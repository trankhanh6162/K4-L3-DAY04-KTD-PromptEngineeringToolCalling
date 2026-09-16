from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from providers.local_provider import LocalProvider
from tools import load_tool_declarations, to_openai_tools

TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"


class TestLocalProvider(unittest.TestCase):
    def setUp(self):
        self.provider = LocalProvider()
        self.tools = to_openai_tools(load_tool_declarations(TOOLS_PATH))

    def test_01_service_status_check(self):
        """Test service status query routes to check_service_status."""
        messages = [
            {"role": "system", "content": "You are an IT Helpdesk assistant."},
            {"role": "user", "content": "Kiểm tra trạng thái dịch vụ VPN production giúp mình."},
        ]
        res = self.provider.complete(messages, self.tools)
        self.assertEqual(len(res.tool_calls), 1)
        call = res.tool_calls[0]
        self.assertEqual(call.name, "check_service_status")
        self.assertEqual(call.args.get("environment"), "production")
        self.assertEqual(call.args.get("service"), "vpn")

    def test_02_missing_id_clarify(self):
        """Test query with missing asset ID routes to clarify(response_type='text')."""
        messages = [
            {"role": "system", "content": "You are an IT Helpdesk assistant."},
            {"role": "user", "content": "Laptop của mình bị mất mạng, kiểm tra giúp mình với."},
        ]
        res = self.provider.complete(messages, self.tools)
        self.assertEqual(len(res.tool_calls), 1)
        call = res.tool_calls[0]
        self.assertEqual(call.name, "clarify")
        self.assertEqual(call.args.get("response_type"), "text")
        self.assertIn("Asset ID", call.args.get("question", ""))

    def test_03_device_inspection(self):
        """Test device query with asset ID routes to inspect_device with scope."""
        messages = [
            {"role": "system", "content": "You are an IT Helpdesk assistant."},
            {"role": "user", "content": "Kiểm tra kết nối của máy LT-204."},
        ]
        res = self.provider.complete(messages, self.tools)
        self.assertEqual(len(res.tool_calls), 1)
        call = res.tool_calls[0]
        self.assertEqual(call.name, "inspect_device")
        self.assertEqual(call.args.get("asset_id"), "LT-204")
        self.assertEqual(call.args.get("check"), "network")

    def test_04_bonus_warranty_tool(self):
        """Test warranty query routes to Technical Bonus Tool check_asset_warranty."""
        messages = [
            {"role": "system", "content": "You are an IT Helpdesk assistant."},
            {"role": "user", "content": "Kiểm tra thời hạn bảo hành và tình trạng vòng đời của thiết bị LT-204."},
        ]
        res = self.provider.complete(messages, self.tools)
        self.assertEqual(len(res.tool_calls), 1)
        call = res.tool_calls[0]
        self.assertEqual(call.name, "check_asset_warranty")
        self.assertEqual(call.args.get("asset_id"), "LT-204")

    def test_05_multiturn_correction(self):
        """Test multi-turn user correction prioritizes the latest asset ID."""
        messages = [
            {"role": "system", "content": "You are an IT Helpdesk assistant."},
            {"role": "user", "content": "Kiểm tra kết nối của máy LT-204."},
            {"role": "assistant", "content": "Đang kiểm tra thiết bị LT-204."},
            {"role": "user", "content": "À nhầm, kiểm tra máy LT-240 giúp mình."},
        ]
        res = self.provider.complete(messages, self.tools)
        self.assertEqual(len(res.tool_calls), 1)
        call = res.tool_calls[0]
        self.assertEqual(call.name, "inspect_device")
        self.assertEqual(call.args.get("asset_id"), "LT-240")

    def test_06_ticket_creation_safety_boundary(self):
        """Test unconfirmed ticket request routes to clarify(response_type='yes_no')."""
        messages = [
            {"role": "system", "content": "You are an IT Helpdesk assistant."},
            {"role": "user", "content": "Tạo ticket mức high cho lỗi VPN trên máy LT-204 giúp mình."},
        ]
        res = self.provider.complete(messages, self.tools)
        self.assertEqual(len(res.tool_calls), 1)
        call = res.tool_calls[0]
        self.assertEqual(call.name, "clarify")
        self.assertEqual(call.args.get("response_type"), "yes_no")

    def test_07_ticket_creation_after_confirmation(self):
        """Test confirmed ticket request routes to create_ticket(confirmed=True)."""
        messages = [
            {"role": "system", "content": "You are an IT Helpdesk assistant."},
            {"role": "user", "content": "Tạo ticket mức high cho lỗi VPN trên máy LT-204 giúp mình."},
            {"role": "assistant", "content": "Bạn có xác nhận tạo ticket hỗ trợ không?"},
            {"role": "user", "content": "Tôi xác nhận tạo ticket cho máy LT-204."},
        ]
        res = self.provider.complete(messages, self.tools)
        self.assertEqual(len(res.tool_calls), 1)
        call = res.tool_calls[0]
        self.assertEqual(call.name, "create_ticket")
        self.assertTrue(call.args.get("confirmed"))
        self.assertEqual(call.args.get("asset_id"), "LT-204")

    def test_08_tool_synthesis(self):
        """Test natural language synthesis after receiving tool results."""
        messages = [
            {"role": "system", "content": "You are an IT Helpdesk assistant."},
            {"role": "user", "content": "Kiểm tra trạng thái dịch vụ VPN production."},
            {"role": "assistant", "content": None},
            {
                "role": "tool",
                "name": "check_service_status",
                "content": json.dumps({"service": "vpn", "environment": "production", "status": "degraded", "incident_id": "INC-1042"}),
            },
        ]
        res = self.provider.complete(messages, self.tools)
        self.assertIsNotNone(res.text)
        self.assertIn("vpn", res.text.lower())
        self.assertIn("degraded", res.text.lower())


if __name__ == "__main__":
    unittest.main()
