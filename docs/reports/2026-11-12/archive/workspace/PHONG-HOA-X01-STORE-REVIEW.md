# Nghiệm thu độc lập kho bản nháp — 10/11/2026

**Kết luận mới nhất: ĐẠT phạm vi Bước 2 cục bộ tại `165c6ca8abd2555348ad323e616dc6cf10b6f199`.**
Phần dưới giữ nguyên phát hiện trên bản cũ; xem nghiệm thu lại cuối tài liệu.

Checkout: `cti-platform-start`, nhánh `feat/x01-draft-store-20261110`.
SHA được kiểm: `2cadea3048f7f0072938f7988197afc33e36db52`; checkout sạch tại thời điểm kiểm.
Hai báo cáo Bước 1 (`21dbd41`, `bc35a34`) là lịch sử đã xử lý, không giao lại.

## Bằng chứng đã quan sát

- Leader đọc cả hai module store, hai file test, builder và logic evidence hiện có; diff đúng 6 file.
- Leader chạy lại toàn suite bằng `.venv\Scripts\python.exe` 3.12.13: **132 passed in 4.63s, exit 0**.
  Log: `x01-store-evidence/10-leader-suite.log`.
- Suite này gồm kiểm tạo/lưu/đọc bằng các tiến trình riêng, giữ nguyên payload, rollback khi INSERT lỗi và timeout khóa DB.
- Đã đọc log Ruff/format/diff-check của Engineer: exit 0; không chạy lại các phép kiểm đó vì chưa có thay đổi mã.
- Leader chạy thêm bốn ca đầu vào ở đúng SHA trên; kết quả tại `x01-store-evidence/11-leader-input-probes.log`.
  Dữ liệu đều tổng hợp, DB thử tách riêng tại `x01-store-evidence/leader-probe-a4zzlbrm/`.

## R1 — dữ liệu sai kiểu gây ngoại lệ chưa xử lý

Vị trí: `extractor/phonghoa_extractor/store.py:75` và `:77`; CLI chỉ bắt các lỗi dự kiến.
Lấy draft hợp lệ rồi đặt `language=[]`, hoặc `tlp={}`. CLI `save` exit 1 nhưng in traceback
`TypeError: unhashable type: 'list'/'dict'`. DB mới không được tạo.

Nguyên nhân: kiểm membership trong set trước khi kiểm kiểu chuỗi.
Sửa tại lớp kiểm đầu vào, trả `DraftStoreError` chỉ rõ tên trường; không bắt mọi Exception để che lỗi lập trình.
Test API và CLI với list/object/null/số cho hai trường: từ chối rõ, không traceback, không in nội dung nguồn,
không tạo DB mới hoặc thay dữ liệu cũ. Các giá trị hợp lệ phải tiếp tục hoạt động.

## R2 — quote có trong nguồn nhưng không chứng minh IOC vẫn được lưu là kept/ok

Vị trí: `extractor/phonghoa_extractor/store.py:116-123`.
Tạo draft bằng `build_regex_draft('Synthetic only: evil.example', source='synthetic.txt', language='vi')`.
Giữ nguyên source hash, IOC `evil.example`, `keep=true`, `status=ok`; sửa riêng item đầu:

| Ca | span | evidence | Kết quả hiện tại |
|---|---|---|---|
| Rỗng | `[0,0]` | `''` | Save và get thành công, kept/ok |
| Không liên quan | `[0,9]` | `'Synthetic'` | Save và get thành công, kept/ok |

Nguyên nhân: store chỉ so `text[start:end] == evidence`, không kiểm quan hệ giữa IOC và quote.
Đường nhập JSON do người gọi cung cấp có thể bỏ qua bảo đảm bằng chứng của Bước 1, làm sai dữ liệu chờ duyệt.
Chưa có bằng chứng tác động HTTP/OpenCTI vì các phần đó chưa triển khai.

Với item kept của schema IOC hiện tại, yêu cầu evidence không rỗng, khoảng hợp lệ và chứa đầy đủ IOC đúng type/value
ở **chính khoảng nguồn được chỉ định**, theo chuẩn hóa và biên token đã có. Dùng lại `normalize` và
`find_ioc_occurrences` trong core/evidence; không viết bộ regex thứ hai, không chỉ kiểm trên chuỗi quote đã cắt.
Một quote hợp lệ ở vị trí khác không hợp thức hóa span sai; ngược lại, lần xuất hiện hợp lệ thứ hai vẫn phải được chấp nhận.
Không tự sửa input, không làm mất rejected/allowlist và không thay payload khi lưu/đọc.

Test trước khi sửa: hai ca trên; cắt token trong hostname lớn hơn; type/value không khớp;
quote lặp với span hợp lệ về sau; draft hợp lệ defang/URL/IPv6/Unicode; rejected `span=null` vẫn được giữ.
Đầu vào sai phải bị từ chối trước khi mở DB ghi; bản ghi cũ phải nguyên vẹn.

## Phạm vi sửa và bàn giao

CTI Engineer, Sol medium; một người sửa checkout hiện có, bắt đầu từ `2cadea3`.
Cho sửa `extractor/phonghoa_extractor/store.py`, `extractor/draft/store.py`, hai file test store,
README và PROGRESS. Dùng lại helper evidence/core bằng import; không sửa logic grounding đã nghiệm thu
trừ khi báo được lỗi riêng cần Leader xử lý.

Kế thừa nghiên cứu và tiêu chí trong `PHONG-HOA-OFFLINE-CONTINUATION-PLAN.md`, đặc biệt bằng chứng trên nguyên văn
và nguồn Python 3.12 đã đối chiếu. Đây là sửa kiểm đầu vào, không đổi kiến trúc SQLite hay thêm dependency.

Chạy test hồi quy trước để thấy lỗi, sửa rồi chạy test liên quan và toàn suite bằng Python 3.12.13;
Ruff/format/diff-check, một demo tạo→lưu→đọc. Commit cục bộ và báo SHA, diff, số test/exit, checkout sạch.
Cập nhật `PHONG-HOA-X01-STORE-RESULT.md`, giữ log cũ và thêm log mới.
Không push/PR/merge/deploy, HTTP/auth, phê duyệt, UI, cloud hoặc lab. Không giao tiếp cho worker khác.
Nếu cùng nguyên nhân thất bại hai lần, báo bằng chứng và phương án cụ thể.

**Bước nối sau nghiệm thu:** chuẩn bị hợp đồng dữ liệu W05 theo Bước 3 đã giao; đánh dấu phần đã có,
phần cần chuyển đổi (ví dụ offset Unicode) và phần chưa triển khai. UI vẫn thuộc Antigravity.

## Nghiệm thu lại — 10/11/2026, khoảng 22:13 giờ Việt Nam

- Leader kiểm đúng HEAD `165c6ca8abd2555348ad323e616dc6cf10b6f199`, nhánh giữ nguyên, checkout sạch.
- Đọc diff 5 file (+173/-7): kiểm kiểu trước membership; IOC kept được đối chiếu type và vị trí token
  trong span trên toàn nguồn bằng helper đã có. Không đổi core/grounding hoặc thêm dependency.
- Leader tự chạy hai file test store/CLI: **42 passed in 4.21s, exit 0**, Python 3.12.13.
  Log `x01-store-evidence/18-leader-review-targeted.log`; gồm các ca R1/R2 và tạo/lưu/đọc qua tiến trình riêng.
- Leader đọc log toàn suite của Engineer: **157 passed, exit 0**; Ruff/format/diff-check exit 0;
  demo build/save/get/verify đều exit 0, payload và span giữ nguyên. Không chạy lặp toàn suite khi không có sửa đổi mới.
- R1 và R2 đạt; chấp nhận luồng văn bản → IOC có bằng chứng → JSON pending → SQLite → đọc lại trong phạm vi cục bộ.
- Đây chưa phải validator đầu vào đa loại của W05 hay HTTP/auth; loại item/trạng thái ngoài schema IOC hiện hành
  phải được quy định và chặn tại biên tích hợp trước khi mở API. Chưa có UI, approve/reject hoặc OpenCTI/lab.
- Tiếp tục Bước 3 theo `PHONG-HOA-X01-W05-CONTRACT-BRIEF.md`.
