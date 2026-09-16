# TEAM — Day04, K4-L3B

**Làm nhóm.** Mỗi người tự viết và commit phần INDIVIDUAL của mình.

## Thông tin bài nộp

- Tên nhóm: KTD
- Người đại diện / MSSV: Trần Ngọc Khánh / 2A202602923
- Tên repo: `K4-L3-DAY04-KTD-PromptEngineeringToolCalling`
- URL repo, nhánh nộp, commit chốt: https://github.com/trankhanh6162/K4-L3-DAY04-KTD-PromptEngineeringToolCalling
- Deadline áp dụng và link thông báo đổi hạn nếu có:

## Thành viên

| Họ và tên        | MSSV        | GitHub        | Vai trò và công việc                                                                                           | File/commit/PR                                                                                                                                                                 |
| ---------------- | ----------- | ------------- | -------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Trần Ngọc Khánh  | 2A202602923 | trankhanh6162 | Prompt & Iteration Lead: chạy và phân tích v0-v3, cải thiện prompt/tool declarations, ghi version evidence     | `abaa696`; `starter_v0/artifacts/{system_prompt.md,tools.yaml,version_log.csv,REPORT.md}`; `starter_v0/{runs,analysis}/`                                                       |
| Nguyễn Hữu Thành | 2A202602807 | hthanh1412004 | Data & Safety Lead: viết 10 group case, chạy group/adversarial eval, phân tích safety trace và ticket boundary | `starter_v0/data/eval_group.json`; `starter_v0/runs/v3_B_{group_gemini_20260915T202018601138,adversarial_openai_20260915T202857024627}.json`; `TEAM.md`; `data/eval_group.json` |
| Phùng Đức Đăng   | 2A202602956 | dawnmoriaty| UI, Bonus & Integration Lead: phát triển Web UI đa phiên bản v0-v3 (hiển thị tool calling sequence, timeline thứ tự gọi trước/sau, bảng so sánh metric benchmark, công cụ chẩn đoán health check), xây dựng Technical Bonus Tool check_asset_warranty (+10đ), tạo 5 transcripts và tích hợp báo cáo | `starter_v0/ui.py`, `starter_v0/tools/check_asset_warranty/`, `starter_v0/scripts/test_bonus_tool.py`, `starter_v0/transcripts/`, `starter_v0/artifacts/REPORT.md` |

## Nhận xét chung

- Kết quả và bằng chứng:
  - Qua 4 phiên bản trên cùng bộ 30 case cơ bản (`data/eval_base.json`), độ chính xác tổng thể tăng liên tục: v0 đạt 70.0% (21/30) ➔ v1 đạt 80.0% (24/30) ➔ v2 đạt 80.0% (Routing 86.67%) ➔ v3 đạt 96.67% (29/30 pass, Tool routing 100%, Multi-turn 100%). Bằng chứng: các file run JSON trong [`starter_v0/runs/`](starter_v0/runs/) và bảng tổng hợp [`starter_v0/artifacts/version_log.csv`](starter_v0/artifacts/version_log.csv).
  - Hoàn thành bộ 10 case nhóm tự viết (`starter_v0/data/eval_group.json`) và bộ 12 case an toàn (`starter_v0/data/eval_adversarial.json`). Bằng chứng run an toàn OpenAI đạt 12/12 cases đo được với `provider_error_cases == 0`, không để lọt rò rỉ dữ liệu hay tạo ticket trái phép.
  - Xây dựng thành công Web UI tương tác thời gian thực (`starter_v0/ui.py`) hỗ trợ chuyển đổi linh hoạt v0-v3, trực quan hóa thứ tự gọi tool calling trước/sau, bảng so sánh metric và công cụ health check; xây dựng Technical Bonus Tool `check_asset_warranty` (+10đ) với 4/4 unit tests passed và lưu trữ 5 bộ live transcripts chuẩn xác.
- Thay đổi hiệu quả nhất:
  - Thiết lập quy trình quyết định tiền điều kiện (pre-call decision procedure) trong `system_prompt.md` và hợp đồng xác nhận hai bước (`clarify(yes_no)` ➔ `create_ticket`) là thay đổi then chốt, loại bỏ hoàn toàn việc gọi công cụ ghi dữ liệu (write actions) bừa bãi và lỗi suy diễn placeholder ID.
  - Bắt buộc tham số `check` cụ thể cho `inspect_device` và phân tách rõ ràng phạm vi định danh giữa `lookup_user` (`employee_id`) và `inspect_device` (`asset_id`) trong `tools.yaml`.
- Giới hạn còn lại:
  - Ở phiên bản v3, case H12 vẫn gọi `clarify(response_type=text)` để hỏi lại summary thay vì tự động rút trích một summary ngắn gọn từ mô tả người dùng đã cung cấp rồi hỏi xác nhận `yes_no`. Hướng cải tiến tiếp theo là bổ sung quy tắc cho phép agent tự tổng hợp tóm tắt ngắn từ ngữ cảnh trước khi yêu cầu xác nhận.
  - Khi chạy tự động hàng loạt qua API Gemini trực tiếp dễ gặp giới hạn quota 5 RPM (429), nhóm đã khắc phục thông suốt bằng cổng 9Router proxy cục bộ (`http://localhost:20128/v1`) cho model `ag/gemini-3-flash` và dùng OpenAI `gpt-4o-mini` cho các benchmark cố định.
- Cách phân công và tích hợp:
  - **Thành viên 1 (Trần Ngọc Khánh - Prompt & Iteration Lead):** Phụ trách thiết lập baseline v0, phân tích failure trace, đề xuất giả thuyết và thực hiện cải tiến prompt/tools qua v1, v2, v3, lưu run/version log và viết B1, B2, B7.
  - **Thành viên 2 (Nguyễn Hữu Thành - Data & Safety Lead):** Phụ trách xây dựng bộ 10 test case mở rộng (`eval_group.json`), thực thi đánh giá group eval, chạy và phân tích sâu 12 case an toàn adversarial, viết B3, B4a, B6.
  - **Thành viên 3 (Phùng Đức Đăng - UI, Bonus & Integration Lead):** Phụ trách phát triển Web UI tương tác thời gian thực (`ui.py`) với đầy đủ tính năng chuyển đổi version v0-v3, timeline thứ tự tool call trước/sau, bảng so sánh metric và tool kiểm tra health check; xây dựng Technical Bonus Tool `check_asset_warranty` (+10 điểm); thu thập và đối soát 5 bộ transcripts thực tế; tổng hợp và kiểm tra chốt hạ toàn bộ báo cáo `REPORT.md`, `TEAM.md` và `README.md`.

## INDIVIDUAL

Sao chép mục này cho từng thành viên.

### Trần Ngọc Khánh — 2A202602923

- Phần việc và file/commit/PR: Prompt & Iteration Lead; thiết lập baseline v0, phân tích failure, xây các hypothesis v1-v3, cải thiện `system_prompt.md` và `tools.yaml`, lưu run/analysis/version log và viết các mục B1, B2, B7 trong report. Evidence kỹ thuật tại commit `abaa696`.
- Quyết định, khó khăn và cách xử lý: Khó khăn lớn nhất là v2 không tăng tổng accuracy và làm hai case đang PASS bị regression vì quy tắc hỏi lại còn quá rộng. Tôi giữ run này làm evidence thay vì che kết quả, đối chiếu từng case với v1 rồi thu hẹp quy tắc ở v3: dùng trực tiếp enum hợp lệ, bắt buộc category cụ thể và tách rõ bước xác nhận ticket. Nhờ đó v3 đạt 29/30, routing và multi-turn đều đạt 1.0.
- Điều đã học: Tôi học được rằng system prompt hiệu quả cần mô tả một quy trình quyết định rõ ràng thay vì chỉ liệt kê capability. Các quy tắc về thông tin bắt buộc, ý định mới nhất, sửa/hủy và hiệu lực của xác nhận giúp agent ổn định hơn; tuy nhiên mọi thay đổi vẫn phải được kiểm tra bằng cùng bộ case và đọc cả tool results vì automatic score không phản ánh đầy đủ hành động ghi dữ liệu.
- AI/công cụ đã dùng và cách kiểm tra: Dùng OpenCode để đọc trace, đề xuất và áp dụng thay đổi prompt/tool declaration, tổng hợp report. Kết quả được tự kiểm tra bằng OpenAI `gpt-4o-mini` trên cùng 30 case cho v0-v3; mọi run đều có `provider_error_cases == 0` và `measured_cases == total_cases == 30`; v3 đạt 29/30, routing và multi-turn đạt 1.0. Tool results và filesystem được rà để phát hiện ticket tạo sai ở v0-v2 và xác nhận v3 không ghi ticket.
- Thời điểm đã tự nộp URL repo chung trên VLearn:

### Nguyễn Hữu Thành - 2A202602807

- Phần việc và file/commit/PR: Data & Safety Lead; viết 10 case gốc trong `starter_v0/data/eval_group.json` gồm 5 single-turn và 5 multi-turn; kiểm tra schema, expected tool/argument; chạy và đọc group eval v3; chạy adversarial bằng OpenAI và phân tích trace an toàn. Evidence: `starter_v0/runs/v3_B_group_gemini_20260915T202018601138.json` và `starter_v0/runs/v3_B_adversarial_openai_20260915T202857024627.json`. Commit/PR: bổ sung sau khi tự commit phần việc này.
- Quyết định, khó khăn và cách xử lý: Tôi thiết kế case theo tình huống Helpdesk có dữ liệu giả lập, ưu tiên kiểm tra đúng tool, đúng argument, ghi nhớ context đa lượt, hủy hành động và confirmation trước khi tạo ticket. Gemini bị giới hạn request/phút nên các group run có `provider_error` và không được dùng để kết luận chất lượng agent. Tôi dùng run adversarial OpenAI có `provider_error_cases == 0` để phân tích hành vi an toàn dựa trên trace thay vì suy đoán từ điểm số.
- Điều đã học: Tôi học được rằng safety evaluation không chỉ kiểm tra agent có từ chối hay không, mà phải kiểm tra tool call, argument, tool result và filesystem. Case A03 cho thấy text giả mạo `TOOL_RESULTS_JSON` có thể khiến agent tạo ticket sai; A06 xác nhận agent không gửi dữ liệu asset nội bộ ra web; A09 xác nhận nội dung prompt injection trong knowledge base được tách vào `untrusted_text` và không được thực thi.
- AI/công cụ đã dùng và cách kiểm tra: Dùng Codex để đọc source, kiểm tra cấu trúc eval và phân tích run JSON; dùng `run_eval.py`, `scripts/preflight_provider.py` và tool result trong run để kiểm tra. Đã kiểm tra ticket tạo từ A03 là ticket local mock, không chứa secret và bị `/tickets/` trong `.gitignore` chặn khỏi Git. Các kết luận chỉ dùng run OpenAI adversarial đủ 12/12 case đo được; các run có lỗi quota Gemini được ghi nhận là lỗi provider, không tính là fail của agent.
- Thời điểm đã tự nộp URL repo chung trên VLearn:

### Phùng Đức Đăng — 2A202602956

- Phần việc và file/commit/PR: UI, Bonus & Integration Lead (Vai C + D). Phát triển Web UI tương tác thời gian thực bằng Python Native HTTPServer (`starter_v0/ui.py`) với các tính năng: chuyển đổi linh hoạt giữa các phiên bản (v0, v1, v2, v3) kèm badge nhận biết phiên bản trực tiếp trong từng tin nhắn chat, bảng so sánh đối đầu các metric đo lường qua từng version (Accuracy, Routing, Multiturn), trực quan hóa thứ tự luồng gọi tool (tool calling execution sequence: hiển thị rõ tool nào gọi trước, tool nào gọi sau, tham số và kết quả từng bước), và tích hợp công cụ kiểm tra chất lượng phiên bản tự động (Version Health Check Tool). Xây dựng Technical Bonus Tool `check_asset_warranty` (`starter_v0/tools/check_asset_warranty/`) đạt 4/4 unit test cases (`starter_v0/scripts/test_bonus_tool.py`). Chạy và ghi nhận 5 bộ live transcripts thực tế cho v3 (`starter_v0/transcripts/`). Tích hợp Header, Section A (A1-A4), Section B4, B5 trong `starter_v0/artifacts/REPORT.md`, hoàn thiện `TEAM.md` và `README.md`.
- Quyết định, khó khăn và cách xử lý: Quyết định quan trọng nhất là sử dụng `ThreadingHTTPServer` từ thư viện chuẩn Python (zero third-party dependency) thay vì framework ngoài, đảm bảo Web UI hoạt động ngay lập tức trong mọi môi trường mà không bị lỗi thư viện. Khó khăn gặp phải là xử lý rate limit (429) khi gọi mô hình; tôi đã tích hợp thành công cổng trung chuyển 9Router cục bộ (`http://localhost:20128/v1`) với model `ag/gemini-3-flash`, giúp sinh toàn bộ transcript và tương tác UI trơn tru, không gặp bất kỳ lỗi kết nối nào.
- Điều đã học: Hiểu sâu sắc về cơ chế Function Calling/Tool Calling trong các hệ thống Agentic AI. Nhận thức rõ rằng một agent an toàn không chỉ cần prompt khéo léo mà phải có ranh giới tin cậy (trust boundary) ở tầng công cụ: kiểm tra regex hợp lệ trước khi truy vấn, và tuyệt đối không thực thi các hành động ghi có tác động (write actions) như tạo ticket khi chưa có xác nhận rõ ràng (`confirmed: true`) từ người dùng.
- AI/công cụ đã dùng và cách kiểm tra: Sử dụng Antigravity và Python unittest. Tự kiểm tra toàn diện bằng chứng kỹ thuật: chạy bộ kiểm thử `scripts/test_bonus_tool.py` đạt 4/4 test cases pass, kiểm tra tính hợp lệ và cấu trúc schema của 5 file JSON trong `transcripts/`, khởi chạy Web UI qua `python ui.py --port 8080` kiểm tra chuyển đổi version v0-v3, timeline thứ tự gọi tool và tính năng Version Health Check.
- Thời điểm đã tự nộp URL repo chung trên VLearn:
