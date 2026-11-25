# Kết quả BƯỚC 1 — bản nháp IOC có bằng chứng

Ngày kiểm chứng: 10/11/2026. Trạng thái: **PASS cục bộ** trên nhánh
`feat/x01-evidence-draft-20261110`; không push, PR, merge hoặc deploy.

## Git và phạm vi

- Base: `c858990f372c0557e0ee3da8b1a8475149d77af4`.
- Commit tính năng: `21dbd41e691180c33f3d4bc7e439b82910fcd99a`.
- Commit sửa lỗi nghiệm thu: `bc35a34c5470748db3cf0b6becb933958cfeb06f`
  (`fix: validate IOC evidence on source boundaries`).
- Checkout sau commit sạch; nhánh đi trước base đúng 2 commit.
- Diff cộng dồn: 9 file, 665 dòng thêm, 22 dòng xóa.
- Hoàn tác cục bộ nếu cần: `git revert bc35a34c5470748db3cf0b6becb933958cfeb06f 21dbd41e691180c33f3d4bc7e439b82910fcd99a`
  trên một nhánh thử; chưa thực hiện lệnh hoàn tác này.

## Đã làm

- `extractor/phonghoa_extractor/evidence.py`: tìm IOC theo loại trên nguyên văn, giữ offset Unicode `[start,end)`;
  so sánh qua `normalize` hiện có nên domain/hash không phân biệt hoa thường theo chuẩn, nhưng URL path/query và
  email local part vẫn phân biệt hoa thường. Biên token được kiểm trên toàn source, không phải trên quote đã cắt;
  nếu occurrence đầu nằm trong token lớn hơn thì chọn occurrence hợp lệ về sau.
- `extractor/phonghoa_extractor/grounding.py`: evidence bắt buộc phải là quote nguyên văn có đúng IOC với biên
  token; loại evidence thiếu/bịa/sai loại; duplicate có bằng chứng hợp lệ thay duplicate invalid; allowlist vẫn
  được giữ trong draft với `keep=false` và lý do.
- `extractor/phonghoa_extractor/drafts.py`: thêm `build_regex_draft`, tạo `status=pending`, SHA-256 nguồn,
  `TLP:AMBER` mặc định, `model=regex-C1`, `cost_tokens=0`, items, span/evidence và kết quả quét injection. URL
  `hxxps://evil(.)…`, scheme `ftp://…` được giữ ngang khả năng core; kết quả extract không tìm được quote trở
  thành item rejected có lý do thay vì biến mất.
- `extractor/draft/run.py` và README: CLI `.txt` UTF-8 sang JSON; lỗi file thiếu, đuôi sai, language/TLP sai không
  tạo kết quả hợp lệ.
- `docs/PROGRESS.md`: ghi đúng giới hạn BƯỚC 1.

## Bằng chứng kiểm thử

| Kiểm tra | Kết quả thật |
|---|---|
| Baseline trước sửa | 81 test, exit 0 |
| 3 lỗi grounding trên base | 3 fail, exit 1; module path trỏ bản sao base `c858990…` |
| Cùng 3 test trên working tree | 3 pass, exit 0 |
| 8 test lỗi boundary/parity trên `21dbd41…` | fail, exit 1; module path trỏ đúng bản sao commit |
| Cùng 8 test trên working tree | pass, exit 0, Python 3.12.13 |
| Toàn bộ pytest cuối | 115 passed trong 5,31 giây, exit 0, Python 3.12.13 |
| `ruff check .` | All checks passed, exit 0 |
| `ruff format --check .` | 81 file đã định dạng, exit 0, chạy qua Python 3.12.13 |
| `git diff --check` | exit 0 |
| C1 regression | 6 báo cáo, exit 0; JSON byte-identical kết quả cũ, cùng SHA-256 `8D4C217F…FD76` |
| Demo draft thật | exit 0; `pending`, 5 items, 3 kept, 2 findings; URL HTTP defang và FTP có mặt; mọi span có `text[span]==evidence` |

Log ban đầu: `x01-draft-evidence/01-base-red.log` đến `06-sample-validation.log`. Log nghiệm thu/sửa lỗi:
`08-leader-py312-tests.log` đến `16-py312-demo-validation.log`; RED→GREEN mới nằm tại
`11-boundary-parity-red.log` và `12-boundary-parity-green.log`. Các thư mục `*-base-repro/` chỉ là bản sao mã
commit dùng chứng minh RED, không chứa dữ liệu thật hoặc secret. Kết quả C1 cuối ở `x01-draft-evidence/c1-regression.json`.

Mẫu thật: `PHONG-HOA-X01-DRAFT-SAMPLE.json`, SHA-256
`537B544412BC78474DDAB3605AFAB2F8D4A1B20149405CC2EC1516DDDB853EB8`.

## Giới hạn và phần chưa xác minh

- **Python 3.12 đã xác minh cục bộ:** `.venv\Scripts\python.exe` là Python 3.12.13; pytest, Ruff, C1 và CLI demo
  cuối đều chạy bằng executable này. Chưa kiểm Python 3.12 trên lab hay CI.
- Chưa lưu/đọc SQLite; đó là BƯỚC 2 riêng.
- Chưa chạy lab, OpenCTI, portal, model cloud, URL/PDF hoặc dữ liệu thật.
- Đây không phải hoàn thành toàn X01; chưa đánh giá TTP, attacker/victim/benign, precision/recall trên dataset
  hai người gán nhãn hoặc chất lượng ngữ nghĩa.
- `injection_warning` chỉ là cảnh báo theo mẫu; không chứng minh chống được mọi prompt injection và không có
  hành động tự động nào được thực thi.

## Học thêm

- **Grounding** là bước buộc kết quả trích xuất quay lại bằng chứng thật trong nguồn, thay vì tin chuỗi do model trả.
- **Half-open span `[start,end)`** lấy ký tự từ `start` đến trước `end`, nên `text[start:end]` tái tạo đúng quote.
- **RED→GREEN** là test trước tiên phải bắt được lỗi, sau đó mới sửa để test chuyển sang đạt.
- **Allowlist** là danh sách hạ tầng hợp pháp mặc định bỏ chọn, nhưng vẫn giữ dấu vết để analyst biết vì sao.
