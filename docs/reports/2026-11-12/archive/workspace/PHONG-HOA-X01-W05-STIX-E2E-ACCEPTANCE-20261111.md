# X01 → W05 → STIX E2E — nghiệm thu Leader 11/11/2026

**ACCEPTED local CLI + HTTP** tại `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.
Request `d59f1c34-e0cf-4a20-bee1-e1b1a1dddd73`, thread `9707cfe2-9db4-431b-a255-7949df39f535`.

## Phạm vi và mã
- Tree `cti-x01-w05-stix-e2e`, branch `feat/x01-w05-stix-e2e-20261111`, base `ed829a0344b2d3d4392fae933e41a9c44fdcd853`.
- Leader kiểm HEAD, Git sạch và diff đúng 7 file +588/-1. Source `cti-w05-stix-offline` giữ nguyên base và sạch.
- Đọc toàn bộ diff CLI/store, runner, matrix, tests và docs. Không có thay đổi core/schema/API/UI/gateway/exporter/dependency/lock.
- Optional creator CLI đi qua validation core, giữ legacy; đây là metadata khai báo cục bộ, không phải xác thực. Seed thật qua hai subprocess; HTTP selection/approve và STIX CLI dùng cùng DB/draft. Không payload seed tự dựng.
- Không phát hiện finding cần sửa trong phạm vi diff hiện tại. Không suy diễn thành audit bảo mật toàn repo.

## Bằng chứng Leader vừa chạy
| Kiểm tra | Kết quả | Exit |
|---|---:|---:|
| Store CLI + runner + STIX CLI, đúng HEAD | 54 passed, 18.31s | 0 |
| Ma trận CLI→HTTP→STIX | 59 checks | 0 |
| Selection regression | 113 checks / 10 scenarios | 0 |
| Ruff check | All checks passed | 0 |
| Ruff format | 5 files already formatted | 0 |
| git diff --check base..HEAD | không lỗi | 0 |

Log mới: `x01-w05-stix-e2e-evidence/leader-review/verification.log` và `selection-regression.log`.
Manifest worker 7/7 hash khớp. Log worker là bản tóm tắt/chuẩn hóa; số 54/59/113 trên được xác nhận bằng lượt chạy mới của Leader, không chỉ dựa báo cáo.

Run mới:
- Source SHA256 `e73038e5d68d0aee0757bf72cd8a404b3f55a94ef9d6c519f5e0c3fb1292a655`.
- Bundle SHA256 `09f67d792143be7459b799fa07bd2b71f88913269a5b4edca4813b09c78f505a`, 4 object. Khác bundle của run worker do timestamp/audit được tạo mới; identical re-export trong cùng run vẫn giữ bytes/mtime.
- Pending DB before/after `06558d9adc1848655345160504fd091b6191cefca133e6f71c4aff605111360b`.
- Approved DB before/after `73a9420d521ea89626f6cd34595e0f34699748269814c329dba00809ca1b827f`.
- Matrix kiểm source/Unicode/TLP, selection [0,1]→[1], review 0→1→2, final audit/provenance, chỉ domain được chọn, payload không đổi, pending bị chặn và output khác không bị ghi đè.
- PASS chỉ sau gateway process kết thúc, API thread dừng, gateway port bind được lại và temp root bị xóa. Targeted có lỗi seed/start và exception giữa run để kiểm cleanup.
- Không lặp full500/UI/build/browser. TDD Task1/2 có RED do worker báo cáo; không có raw RED trong gói này nên lịch sử RED không được Leader xác minh độc lập. Matrix được thêm sau GREEN: ghi rõ sai lệch quy trình, không yêu cầu dựng RED hồi tố hoặc giả bằng chứng.

## Trạng thái dự án và việc kế
Bằng chứng mới chỉ là fixture tổng hợp cục bộ qua CLI/HTTP. Browser cùng draft, OpenCTI import/workbench, danh tính tổ chức thật, Cloudflare/JWKS/HTTPS thật, model/dataset thật, network share/crash, lab/production vẫn chưa xác minh. Không push/PR/merge/deploy. Không đánh dấu W05 hoặc dự án hoàn tất.

Đã đối chiếu X01/W05/PROGRESS và kế hoạch team. Nhánh AI độc lập còn ở `8694fa7244d181f421bb2733ded7bf9ae218ea93`, sạch; adapter chỉ kiểm định dạng mã technique và giữ semantic items chưa đủ điều kiện dùng. Chưa có loader ATT&CK trong core/extractor đã kiểm. Nghiên cứu AI trước đã nêu phương án loader snapshot nhưng chưa có brief chi tiết; tìm lịch sử “C4 ATT&CK” không có kết quả.

Việc nhỏ hữu ích tiếp theo: CTI Research đối chiếu cách kiểm mã kỹ thuật ATT&CK từ snapshot cục bộ, lập brief nền tảng cho C4 mà không gọi model hoặc tự nhận đã làm RAG/chất lượng TTP. Dự án active; lab và viewport vẫn blocked theo sổ. Lịch dự phòng còn enabled chu kỳ30 phút, lượt07:26 hoàn tất NOTHING NEW; không đổi lịch.
