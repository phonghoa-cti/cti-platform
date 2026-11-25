# X01-TTP-AUDIT — nghiệm thu nghiên cứu và giao triển khai

Ngày 11/11/2026. **PASS tài liệu sau rework R1–R3; implementation chưa chạy.**

## Bằng chứng nghiệm thu

Leader đọc toàn bộ hai tài liệu đã sửa và đối chiếu review `PHONG-HOA-X01-TTP-AUDIT-RESEARCH-REVIEW-20261111.md`.
Request nghiên cứu gốc `4352741d-a087-4a25-b1e1-4c05b6b3cd1e`; request rework `fbd3ec8a-cd3f-44bc-9a8c-015955f1b74c`; thread `d6aabc06-ecb9-4f74-96d1-d2a82d66701a`.

| Điểm | Đã kiểm trong tài liệu sửa |
|---|---|
| R1 | Research:39–59, Brief:24–37: projection cụ thể, SHA-256 của source kiểm trước mọi return, mode/flag/fallback, không coi hash là chứng thực nguồn |
| R2 | Research:55–59,85–87, Brief:35–37,54: lỗi cấu trúc raise toàn call; string rỗng là content result; validate mixed list trước lọc; giữ item_index; catalog loader boundary |
| R3 | Research:63–103, Brief:39–79: frozen/scalar/tuple; quote chồng nhau; precedence và test matrix; C2/C3 public path và eval_cli regression |

Hash thực đọc:
- `PHONG-HOA-X01-TTP-AUDIT-RESEARCH.md`: `35B8FE7C5EF144CE659FB3C922C603F7346F3B0B127E791999B3D19C667944CF`.
- `PHONG-HOA-X01-TTP-AUDIT-IMPLEMENTATION-BRIEF.md`: `16BFF397C5EC30127BFC49F2BA42E8DBCA17A57F13FA5131A33ADD3A90F221FD`.

Git nguồn thực kiểm: branch `feat/x01-attack-official-20261111`, HEAD `4001441edcf5414df0f06c34352f6c5d3e2a2bd5`; status --porcelain rỗng; diff --check exit 0. Chưa có target worktree hoặc target branch tại thời điểm kiểm. Không lặp test bộ catalog đã accepted; lượt này là review tài liệu, không có bằng chứng code audit.

## Việc được giao

Owner: **một CTI AI Agent / Sol medium**, không giao bot khác. Đọc hai tài liệu đã nghiệm thu; thực hiện contract/TDD/acceptance trong implementation brief, với chốt nhỏ bên dưới.

Root: `$WORKSPACE`.
Source readonly: `<root>\cti-x01-attack-official`.
Base chính xác: `4001441edcf5414df0f06c34352f6c5d3e2a2bd5`.
Tree mới: `<root>\cti-x01-ttp-audit`.
Branch mới: `feat/x01-ttp-audit-20261111`.
Interpreter: `<root>\cti-platform-start\.venv\Scripts\python.exe`.
Ruff: `<root>\cti-platform-start\.venv\Scripts\ruff.exe`.

Đây là phần việc offline đã được giao trong vòng tiếp tục; không cần xin lại duyệt cho việc tạo tree, sửa file theo scope và commit cục bộ. Đọc AGENTS/PROGRESS/X01 spec/ADR0004 trong đúng base. Giải thích ngắn mục tiêu/tái sử dụng/lệnh kiểm, theo tinh thần học trong lúc làm. Nếu xuất hiện sửa ngoài scope, ghi phát hiện cụ thể thay vì tự mở rộng.

File scope:
- Thêm `extractor/phonghoa_extractor/ttp_audit.py`.
- Thêm `extractor/tests/test_ttp_audit.py`.
- `extractor/phonghoa_extractor/__init__.py` chỉ khi cần export public.
- Cập nhật `docs/PROGRESS.md`.
- Thêm ADR ngắn `docs/adr/0005-x01-offline-technique-audit.md` theo template nếu chưa có tên này, để ghi quyết định source binding/projection/quote-only/fail-closed theo yêu cầu AGENTS. Không ghi đè ADR đã tồn tại; báo nếu xung đột. Đây là tài liệu cho đúng lát cắt, không đổi thiết kế khác.

Chốt thực hiện:
1. Containers đầu vào kiểm là native exact dict/list; schema_version/config/result_mode/destination/kind/hash và semantic strings kiểm exact str trước membership/regex/encode. Boolean kiểm is True/False. List/dict/null/bool/number sai kiểu phải về error code đã định nghĩa, không TypeError/KeyError rò marker.
2. Source length check trước encode và UTF-8 byte bound như brief. Semantic value/evidence cũng kiểm length trước encode khi đã vượt 8192 code points, rồi strict UTF-8 byte bound; không tạo bản encode lớn không cần thiết.
3. Có thể giữ source bytes đã encode một lần để hash. “No filesystem/DB/network” áp dụng lời gọi audit; setup synthetic catalog và chạy pytest vẫn được đọc fixture và dùng temp riêng cho test.
4. Preserve mọi file cũ. Không sửa loader/adapter/grounding/evidence/evaluator/CLI/dependency/fixture official/spec cũ. Không tự tái kiểm official 166/full suite lớn vì code đó không đổi.
5. TDD RED → GREEN cho module mới, rồi chạy đúng regression list trong brief; Ruff check/format mọi file Python thực đổi; git diff --check và tự review diff. Demo public ScriptedProvider → adapter C2/C3 → audit có bằng chứng calls không tăng, source/config/catalog provenance và semantic unverified/eligible false. Test sửa input có nhãn fault injection, không gọi là output thật của adapter.

## Bàn giao và giới hạn

Commit local Conventional Commit sau kiểm đạt; giữ tree/branch để Leader nghiệm thu, không merge/push/PR/deploy. Evidence ở `<root>\x01-ttp-audit-evidence\`; report `<root>\PHONG-HOA-X01-TTP-AUDIT-RESULT.md`. Ghi exact base/HEAD/branch/file diff, source/worktree status trước-sau, command/cwd/import path/interpreter/exit/pass/skip, RED/GREEN, demo và manifest hash. Báo limitations trung thực; không coi self-review là review độc lập.

Không model/network/cloud/secret/asset download/package install/DB thật/listener/API/UI/W05/OpenCTI/lab/production, không sửa RUNS/review/research docs/Leader evidence. Không benchmark F1/semantic truth hoặc gọi audit là C4/RAG.

Leader đã xem một lần các cuộc đang mở: không Leader khác đang xử lý Phong Hỏa, AI Agent idle; không giao trùng. Lịch tiếp tục vẫn enabled (09:20:52 ICT), kỳ kế 09:26; giữ vì dự án chưa hoàn tất. Sau kết quả code: Leader review exact diff/tests, sửa finding nếu có; sau accepted mới chọn bước X01 kế trong phạm vi đã giao.
