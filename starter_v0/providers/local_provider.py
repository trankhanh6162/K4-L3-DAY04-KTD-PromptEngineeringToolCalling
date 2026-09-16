from __future__ import annotations

import json
import os
import re
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from providers.base import ModelResponse, ToolCall


class LocalProvider:
    """Local Provider with dual-layer architecture:
    1. Layer 1 (Local LLM Server): Tries local OpenAI-compatible endpoint if available
       (e.g., Ollama at http://localhost:11434/v1, LM Studio at http://localhost:1234/v1,
       or local 9Router proxy at http://localhost:20128/v1).
    2. Layer 2 (Deterministic Offline Engine): Zero-dependency heuristic rule matcher
       that parses intents, extracts arguments, enforces two-step confirmation,
       and synthesizes responses so that the agent NEVER fails even without internet/API keys.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        default_model: str = "local-deterministic-engine",
        timeout_seconds: float = 2.0,
    ) -> None:
        self.base_url = (
            base_url
            or os.getenv("LOCAL_BASE_URL")
            or os.getenv("OPENAI_BASE_URL")
            or "http://localhost:11434/v1"
        )
        self.default_model = os.getenv("LOCAL_MODEL", default_model)
        self.timeout_seconds = timeout_seconds

    def complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None = None,
        *,
        model: str | None = None,
        temperature: float = 0.0,
        tool_choice: Any | None = None,
    ) -> ModelResponse:
        # 1. Attempt Layer 1: Local LLM Endpoint if reachable
        local_resp = self._try_local_endpoint(
            messages, tools, model=model or self.default_model, temperature=temperature
        )
        if local_resp is not None:
            return local_resp

        # 2. Fallback to Layer 2: Deterministic Offline Rule-Based Matcher
        return self._offline_heuristic_complete(messages, tools)

    def _try_local_endpoint(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None,
        *,
        model: str,
        temperature: float,
    ) -> ModelResponse | None:
        """Attempt to call local HTTP OpenAI-compatible server with a short timeout."""
        endpoint = f"{self.base_url.rstrip('/')}/chat/completions"
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
        }
        if tools:
            payload["tools"] = tools

        data = json.dumps(payload).encode("utf-8")
        req = Request(endpoint, data=data, headers={"Content-Type": "application/json"})
        try:
            with urlopen(req, timeout=self.timeout_seconds) as response:
                if response.status == 200:
                    raw = json.loads(response.read().decode("utf-8"))
                    msg = raw["choices"][0]["message"]
                    calls: list[ToolCall] = []
                    for call in msg.get("tool_calls") or []:
                        fn = call.get("function", {})
                        args = json.loads(fn.get("arguments") or "{}")
                        calls.append(ToolCall(name=fn.get("name", ""), args=args))
                    return ModelResponse(text=msg.get("content"), tool_calls=calls, raw=raw)
        except Exception:
            # Server not running or request failed; gracefully fall back to Layer 2
            return None
        return None

    def _offline_heuristic_complete(
        self,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]] | None,
    ) -> ModelResponse:
        """Deterministic offline rule-based function calling engine for IT Helpdesk."""
        # Filter pure user queries (excluding tool results injected as user messages)
        pure_user_messages = [
            m for m in messages if m.get("role") == "user" and not m.get("content", "").startswith("TOOL_RESULTS_JSON:")
        ]

        if not pure_user_messages:
            return ModelResponse(
                text="Xin chào! Tôi là Trợ lý IT Helpdesk (Chế độ Local Fallback). Tôi có thể giúp gì cho bạn hôm nay?"
            )

        last_msg = messages[-1] if messages else {}
        last_content = last_msg.get("content", "")

        # If the last message was a tool result (either role='tool' or 'TOOL_RESULTS_JSON:'),
        # synthesize the final answer and return NO more tool calls to end the loop.
        if last_msg.get("role") == "tool" or "TOOL_RESULTS_JSON:" in last_content:
            return self._synthesize_tool_response(messages)

        latest_user_text = pure_user_messages[-1].get("content", "").strip()

        # Regex extractors
        asset_matches = re.findall(r"\b(LT-\d+|PR-\d+|WS-\d+|DSK-\d+|SRV-\d+)\b", latest_user_text, re.IGNORECASE)
        # Check in entire history for fallback asset_id if not in latest turn
        all_asset_matches = re.findall(
            r"\b(LT-\d+|PR-\d+|WS-\d+|DSK-\d+|SRV-\d+)\b",
            " ".join(m.get("content", "") for m in pure_user_messages),
            re.IGNORECASE,
        )

        current_asset_id = asset_matches[-1].upper() if asset_matches else None
        historical_asset_id = all_asset_matches[-1].upper() if all_asset_matches else None
        effective_asset_id = current_asset_id or historical_asset_id

        emp_matches = re.findall(r"\b(EMP-\d+)\b", latest_user_text, re.IGNORECASE)
        email_matches = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", latest_user_text)

        lower_text = latest_user_text.lower()

        # Rule 1: Warranty Check (Bonus Tool: check_asset_warranty)
        if any(w in lower_text for w in ["bảo hành", "warranty", "vòng đời", "hạn sử dụng"]):
            if effective_asset_id:
                return ModelResponse(
                    tool_calls=[ToolCall(name="check_asset_warranty", args={"asset_id": effective_asset_id})]
                )
            return ModelResponse(
                tool_calls=[
                    ToolCall(
                        name="clarify",
                        args={
                            "question": "Vui lòng cung cấp Mã tài sản (Asset ID, ví dụ: LT-204) để kiểm tra thời hạn bảo hành.",
                            "response_type": "text",
                        },
                    )
                ]
            )

        # Rule 2: Service Status Check (check_service_status)
        service_keywords = ["vpn", "email", "jira", "erp", "intranet", "wifi", "git"]
        has_service_mention = any(k in lower_text for k in service_keywords)
        has_service_intent = any(w in lower_text for w in ["dịch vụ", "service", "hệ thống", "trạng thái"])

        if has_service_mention and (has_service_intent or "production" in lower_text or "staging" in lower_text):
            env = "staging" if "staging" in lower_text else "production"
            matched_service = "vpn"
            for s in service_keywords:
                if s in lower_text:
                    matched_service = s
                    break
            return ModelResponse(
                tool_calls=[
                    ToolCall(
                        name="check_service_status",
                        args={"environment": env, "service": matched_service},
                    )
                ]
            )

        # Rule 3: Ticket Creation with 2-step confirmation safety boundary (create_ticket)
        all_user_text = " ".join(m.get("content", "") for m in pure_user_messages).lower()
        if any(w in lower_text or w in all_user_text for w in ["tạo ticket", "mở ticket", "ticket", "phiếu hỗ trợ"]):
            # Check if user confirms in this turn
            confirmation_words = ["xác nhận", "tôi xác nhận", "đồng ý", "yes", "chính xác", "hãy tạo", "ok", "tiến hành tạo"]
            is_confirmed = any(cw in lower_text for cw in confirmation_words)

            priority = "medium"
            if any(p in all_user_text for p in ["critical", "nghiêm trọng"]):
                priority = "critical"
            elif any(p in all_user_text for p in ["high", "cao", "gấp", "khẩn"]):
                priority = "high"
            elif any(p in all_user_text for p in ["low", "thấp"]):
                priority = "low"

            summary = f"Sự cố kỹ thuật trên thiết bị {effective_asset_id or ''}".strip()
            if "vpn" in all_user_text:
                summary = f"Lỗi VPN trên máy {effective_asset_id or 'thiết bị'}"
            elif "mạng" in all_user_text or "wifi" in all_user_text:
                summary = f"Mất kết nối mạng trên máy {effective_asset_id or 'thiết bị'}"

            if is_confirmed and effective_asset_id:
                return ModelResponse(
                    tool_calls=[
                        ToolCall(
                            name="create_ticket",
                            args={
                                "asset_id": effective_asset_id,
                                "confirmed": True,
                                "priority": priority,
                                "summary": summary,
                            },
                        )
                    ]
                )
            else:
                # Step 1 of safety boundary: ask for confirmation first!
                target_asset = effective_asset_id or "thiết bị"
                return ModelResponse(
                    tool_calls=[
                        ToolCall(
                            name="clarify",
                            args={
                                "question": f"Bạn có xác nhận tạo ticket hỗ trợ cho {target_asset} với mức ưu tiên '{priority}' và mô tả '{summary}' không? Vui lòng xác nhận (Có/Không).",
                                "response_type": "yes_no",
                            },
                        )
                    ]
                )

        # Rule 4: Device Inspection (inspect_device)
        device_keywords = ["máy", "laptop", "thiết bị", "kết nối", "ping", "mạng", "phần cứng", "ram", "ổ cứng", "os", "win"]
        if any(w in lower_text for w in device_keywords):
            if current_asset_id:
                # Scope mapping
                check_scope = "network"
                if any(w in lower_text for w in ["phần cứng", "hardware", "ram", "cpu", "pin"]):
                    check_scope = "hardware"
                elif any(w in lower_text for w in ["hệ điều hành", "os", "windows", "macos"]):
                    check_scope = "os"
                elif any(w in lower_text for w in ["ổ cứng", "dung lượng", "storage", "disk"]):
                    check_scope = "storage"
                elif any(w in lower_text for w in ["ứng dụng", "phần mềm", "app"]):
                    check_scope = "apps"

                return ModelResponse(
                    tool_calls=[
                        ToolCall(
                            name="inspect_device",
                            args={"asset_id": current_asset_id, "check": check_scope},
                        )
                    ]
                )
            elif not effective_asset_id:
                # Missing Asset ID -> must route to clarify!
                return ModelResponse(
                    tool_calls=[
                        ToolCall(
                            name="clarify",
                            args={
                                "question": "Vui lòng cung cấp Mã tài sản (Asset ID, ví dụ: LT-204) của thiết bị để kỹ thuật viên kiểm tra.",
                                "response_type": "text",
                            },
                        )
                    ]
                )

        # Rule 5: User Lookup (lookup_user)
        if any(w in lower_text for w in ["nhân viên", "người dùng", "emp-", "tra cứu nhân viên"]):
            if emp_matches:
                return ModelResponse(
                    tool_calls=[ToolCall(name="lookup_user", args={"employee_id": emp_matches[0].upper()})]
                )
            elif email_matches:
                return ModelResponse(
                    tool_calls=[ToolCall(name="lookup_user", args={"email": email_matches[0]})]
                )
            else:
                return ModelResponse(
                    tool_calls=[
                        ToolCall(
                            name="clarify",
                            args={
                                "question": "Vui lòng cung cấp Mã nhân viên (ví dụ: EMP-1001) hoặc email để tra cứu thông tin.",
                                "response_type": "text",
                            },
                        )
                    ]
                )

        # Rule 6: Knowledge Base Search (search_kb)
        if any(w in lower_text for w in ["hướng dẫn", "cách", "cài đặt", "quên mật khẩu", "reset password", "kb"]):
            category = "all"
            if "vpn" in lower_text:
                category = "vpn"
            elif "wifi" in lower_text:
                category = "wifi"
            elif "mật khẩu" in lower_text or "password" in lower_text:
                category = "password"
            elif "email" in lower_text:
                category = "email"
            elif "phần cứng" in lower_text or "máy in" in lower_text:
                category = "hardware"
            return ModelResponse(
                tool_calls=[ToolCall(name="search_kb", args={"category": category, "query": latest_user_text})]
            )

        # Default fallback text
        return ModelResponse(
            text="Tôi là Trợ lý IT Helpdesk (Chế độ Local Offline Fallback). Bạn có thể yêu cầu tôi kiểm tra trạng thái dịch vụ, chẩn đoán thiết bị (ví dụ: LT-204), tra cứu nhân viên, kiểm tra bảo hành phần cứng, hoặc tạo ticket hỗ trợ kỹ thuật."
        )

    def _synthesize_tool_response(self, messages: list[dict[str, str]]) -> ModelResponse:
        """Synthesize a natural language response based on the latest tool execution results."""
        content: Any = None

        # Check in reverse for tool results either in role='tool' or 'TOOL_RESULTS_JSON:'
        for m in reversed(messages):
            if m.get("role") == "tool":
                try:
                    content = json.loads(m.get("content", "{}"))
                except Exception:
                    content = m.get("content", "")
                break
            elif "TOOL_RESULTS_JSON:" in m.get("content", ""):
                raw_text = m.get("content", "")
                try:
                    json_str = raw_text.split("TOOL_RESULTS_JSON:\n", 1)[-1].split("\n\nUse only", 1)[0].strip()
                    parsed = json.loads(json_str)
                    if isinstance(parsed, list) and parsed:
                        content = parsed[-1].get("result", parsed[-1])
                    else:
                        content = parsed
                except Exception:
                    content = raw_text
                break

        if content is None:
            return ModelResponse(text="Đã xử lý xong yêu cầu của bạn.")

        # Synthesize based on content structure
        if isinstance(content, dict):
            if "ticket_id" in content:
                tid = content.get("ticket_id")
                return ModelResponse(
                    text=f"Ticket hỗ trợ kỹ thuật đã được khởi tạo thành công với mã **{tid}**. Đội ngũ IT sẽ xử lý và liên hệ với bạn trong thời gian sớm nhất."
                )
            if "lifecycle_status" in content or "days_remaining" in content or "warranty_status" in content:
                status = content.get("lifecycle_status") or content.get("warranty_status", "")
                days = content.get("days_remaining", 0)
                exp = content.get("warranty_until") or content.get("warranty_end_date", "")
                rec = content.get("recommendation", "")
                return ModelResponse(
                    text=f"Thông tin bảo hành thiết bị **{content.get('asset_id')}**:\n- Tình trạng: **{status}**\n- Ngày hết hạn: {exp} (còn **{days}** ngày)\n- Khuyến nghị: {rec}"
                )
            if "service" in content and "status" in content:
                srv = content.get("service")
                st = content.get("status")
                env = content.get("environment", "production")
                inc = content.get("incident_id")
                inc_text = f" (Sự cố liên quan: {inc})" if inc else ""
                return ModelResponse(
                    text=f"Trạng thái dịch vụ **{srv}** trên môi trường **{env}**: Hiện đang ở trạng thái **{st}**{inc_text}."
                )
            if "asset_id" in content and "diagnostics" in content:
                diag = content.get("diagnostics", {})
                return ModelResponse(
                    text=f"Kết quả chẩn đoán thiết bị **{content.get('asset_id')}** ({content.get('model', '')}):\n"
                    + "\n".join(f"- **{k}**: {v}" for k, v in diag.items() if isinstance(v, (str, int, float, bool)))
                )

        return ModelResponse(
            text=f"Kết quả xử lý từ hệ thống:\n```json\n{json.dumps(content, ensure_ascii=False, indent=2)}\n```"
        )
