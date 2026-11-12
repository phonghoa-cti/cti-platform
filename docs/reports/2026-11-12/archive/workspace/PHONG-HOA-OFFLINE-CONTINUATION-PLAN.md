# Phong Hỏa — tiếp tục luồng bản nháp ngoại tuyến

Ngày: 10/11/2026. Người dùng yêu cầu tiếp tục dự án, không dừng sau mỗi lát cắt, và để máy lab sau.
Leader tự điều phối các bước dưới đây; một Engineer sửa checkout. Kết quả từng bước phải được nghiệm thu trước bước kế.
Không tự merge, deploy, chi tiền, đổi quyền, dùng secret hoặc gửi dữ liệu thật ra ngoài.

**Sửa điều phối 10/11 23:15:** kế hoạch này chỉ theo dõi mốc ngoại tuyến, không phải mục tiêu toàn dự án. Mốc đạt tại e83bb3f không kết thúc yêu cầu “tiếp tục dự án”. Sổ tổng hiện hành là `PHONG-HOA-RUNS.json`, quy trình tại mục 11 working agreement. Sau nghiệm thu, Leader nối nghiên cứu/triển khai phần tiếp theo trong phạm vi đã cho phép; không đợi người dùng nhắc.

## Đích gần nhất
Văn bản cục bộ → trích IOC → bằng chứng đúng vị trí → bản nháp pending → lưu và đọc lại cục bộ.
Đây là phần của X01 và hợp đồng drafts; không phải hoàn thành AI/portal/OpenCTI.

## Trình tự tiếp tục
1. Làm ngay: sửa grounding và tạo bản nháp JSON bằng quy tắc có sẵn.
2. Sau nghiệm thu bước1, Leader tự giao bước lưu/đọc bản nháp pending bằng SQLite, test tồn tại sau mở lại, lỗi/rollback và ID; chuẩn bị brief dựa trên source đã có.
3. Tiếp tục kiểm thử vòng tạo→lưu→đọc, chuẩn bị hợp đồng tích hợp W05. UI thuộc Antigravity; không tự dựng thay.
4. Lab, mô hình cloud, dataset người gán nhãn, phê duyệt và xuất vào OpenCTI là các mốc riêng. Không giả lập rồi báo hoàn thành.
Chỉ đưa việc về cho người dùng khi thiếu điều họ thực sự phải cung cấp hoặc cần quyết định vượt phạm vi. Không dừng chỉ vì một commit đã xong.

## Bước1: bản nháp IOC có bằng chứng

**Goal:** CLI chạy cục bộ từ .txt sang JSON pending; mọi IOC được giữ có trích dẫn nguyên văn và vị trí khớp nguồn.
**Spec:** docs/specs/X01-ai-extractor.md; docs/specs/api-portal.md phần drafts; PHONG-HOA-INITIAL-RESEARCH.md.
**Base:** c858990f372c0557e0ee3da8b1a8475149d77af4.
**Checkout:** cti-platform-start cùng thư mục kế hoạch; tạo nhánh feat/x01-evidence-draft-20261110, giữ nguyên nhánh C1.
**Công nghệ:** Python3.12, stdlib, phonghoa_core/phonghoa_extractor; không thêm dịch vụ hoặc dependency nếu không cần.

### Nghiên cứu và lỗi đã tái hiện
- X01 yêu cầu evidence khớp văn bản gốc; API dự kiến span=[start,end].
- grounding.py hiện chỉ dùng _squash(value) in _squash(source), không kiểm raw.evidence; _dedupe lower() cả URL/email.
- Leader đã chạy3ca tại base: thiếu quote, quote bịa, và evil.example khi nguồn chỉ có not-evil.example đều keep=True, status=ok, span=None.
- Đây là bằng chứng cần sửa logic, không phải yêu cầu thay regex C1 để nâng điểm.
- Python3.12 re.Match.span trả vị trí ký tự: https://docs.python.org/3.12/library/re.html#match-objects.
- SQLite dùng ở bước2: https://docs.python.org/3.12/library/sqlite3.html#transaction-control.
- Reuse normalize/refang/allowlist/injection hiện có. So với bỏ grounding hoặc đưa thẳng qua LLM, kiểm xác định bằng mã đáp ứng bằng chứng và không cần dữ liệu cloud.

### Files/giao diện
- Sửa extractor/phonghoa_extractor/grounding.py và test_grounding.py.
- Có thể thêm evidence.py nếu cần logic tìm vị trí nguyên văn; tránh nhân bản normalize/refang.
- Thêm drafts.py với hàm build_regex_draft(text, source, language, tlp) trả dict.
- Thêm extractor/draft/run.py và README: --input <txt> --output <json> --language vi|en --tlp <label>.
- Dùng extract_iocs hiện có, scan dấu hiệu injection, ground_iocs và Allowlist. Không thêm model.
- Source có tên và SHA256; model=regex-C1, cost_tokens=0, status=pending; default TLP:AMBER, label không biết phải lỗi.
- Items tối thiểu kind,type,value,span,evidence,keep,warning; rejected item có lý do và không bịa span. Có injection_warning và findings.
- TLP chỉ là metadata trong lượt offline, không là phép gửi cloud. Không đổi quy tắc GREEN trong spec để cho phép cloud.
- Chuẩn span: chỉ số ký tự Python Unicode, [start,end), theo nguyên văn input. Source slice phải bằng evidence của mục giữ. Ghi rõ frontend JS cần chuyển đổi khi tích hợp.
- Evidence chứa full IOC token tương đương sau normalize/refang; không chấp nhận giá trị con trong hostname/hash/IP dài hơn, không bỏ phân biệt hoa thường URL path/query và email local.
- Nếu raw_items từ nguồn giả lập thiếu evidence hoặc quote không ở nguồn/không chứa IOC thì keep=False, lý do rõ; CLI regex tự tạo quote từ nguồn rồi kiểm.
- Dedupe theo loại+giá trị đã normalize; mục invalid xuất hiện trước không được làm mất mục valid sau cùng giá trị.
- Allowlist mặc định bỏ chọn, có lý do. Không tự suy diễn attacker/victim/benign cho kết quả regex.
- Không nhận URL/PDF, không mở HTTP, không gửi LLM, không ghi OpenCTI/SQLite ở bước1.

### Kiểm chứng bắt buộc
- [ ] Test trước cho3lỗi tái hiện; giữ ca hợp lệ defang/email/URL/IP/hash và allowlist.
- [ ] Test span ở văn bản Việt, emoji, xuống dòng, nhiều lần xuất hiện, chuỗi defang co độ dài; không dùng offset chuỗi đã normalize cho nguyên bản.
- [ ] Test quote có trong nguồn nhưng trỏ IOC khác; substring domain/IP/hash; URL path hoa thường; evidence thiếu/sai kiểu phải bị từ chối sạch.
- [ ] Test duplicate invalid trước/valid sau; Unicode và nội dung chèn lệnh chỉ là dữ liệu, không chạy theo.
- [ ] CLI input trống ra draft pending rỗng, thiếu file/TLP sai báo lỗi; không claim đánh giá ngữ nghĩa hay hoàn tất chặn injection.
- [ ] Chạy pytest phù hợp và toàn bộ nếu thay grounding/core tác động baseline; Ruff/diff-check; chạy demo thật với mẫu tổng hợp an toàn.
- [ ] C1 CLI vẫn chạy; nếu điểm đổi phải giải thích, không đổi nhãn để che lỗi.
- [ ] Local commit sạch; cập nhật PROGRESS, tài liệu cách chạy; ghi rõ kết quả local khác runtime/lab.

### Bàn giao
- PHONG-HOA-X01-DRAFT-RESULT.md: SHA, files, lệnh, exit/test, hạn chế.
- PHONG-HOA-X01-DRAFT-SAMPLE.json: bản nháp thật từ CLI, không secret hoặc tài liệu hạn chế.
- x01-draft-evidence/: log testcase/demo.
Leader nghiệm thu rồi tiếp tục bước2 ở trên, không đợi người dùng nhắc tiếp.

## Nghiệm thu Bước 1 — 10/11/2026

- Đã kiểm diff và checkout sạch tại `bc35a34c5470748db3cf0b6becb933958cfeb06f`.
- Leader chạy lại toàn suite bằng `.venv\Scripts\python.exe` 3.12.13: **115 passed, exit 0**.
- Log: `x01-draft-evidence/17-leader-final-py312.log`. Các test sửa lỗi đã phủ quote cắt trong token lớn hơn, occurrence hợp lệ về sau, URL defang/FTP, IPv6 và giữ mục rejected khi không tìm được quote.
- Đã đọc log Ruff, C1 so SHA và demo; các phép kiểm đó đạt. Chấp nhận phạm vi Bước 1 cục bộ. Chưa nghiệm thu toàn X01, UI, lab hoặc hiệu quả trên báo cáo thật.

## Bước 2 — lưu và đọc bản nháp pending bằng SQLite

**Task ID:** X01-DRAFT-STORE. **Owner:** CTI Engineer, Sol medium, một người sửa checkout.
**Base đã nghiệm thu:** `bc35a34c5470748db3cf0b6becb933958cfeb06f`.
**Nhánh mới:** `feat/x01-draft-store-20261110`, tạo trên checkout hiện có sau khi kiểm sạch; giữ nhánh Bước 1.

### Cơ sở và lựa chọn

X01 bước 8 và `docs/specs/api-portal.md` đã chọn SQLite cho hàng chờ bản nháp. Repo chưa có lớp lưu trữ portal để tái sử dụng; giữ hàm `build_regex_draft` thuần và thêm lớp lưu trữ riêng. So với nhiều file JSON, SQLite có transaction và khóa chính; thêm ORM/PostgreSQL hiện không cần thiết cho lát cắt cục bộ này.

Đã đối chiếu [tài liệu sqlite3 của Python 3.12](https://docs.python.org/3.12/library/sqlite3.html) ngày 10/11/2026: dữ liệu lưu trên đĩa, không cần tiến trình dịch vụ riêng; dùng placeholder cho giá trị SQL; quản lý commit/rollback và đóng kết nối rõ ràng. Lưu ý context manager transaction không tự đóng connection. Đây là cơ sở triển khai, chưa phải bằng chứng store của dự án đã hoạt động.

### Phạm vi

- Module riêng trong `extractor/phonghoa_extractor/` (ví dụ `store.py`), CLI riêng `extractor/draft/store.py`, tests, README và cập nhật `docs/PROGRESS.md`; bổ sung hợp đồng offline ngắn trong docs khi cần. Chỉ stdlib Python 3.12.
- API nhỏ: lưu một draft pending và trả ID số nguyên dương; lấy draft theo ID, trả lại nguyên nội dung cùng ID và created_at UTC có timezone. ID do kho cấp; không cập nhật/ghi đè draft cũ hoặc tự khử trùng theo nội dung nguồn.
- CLI `save --db <file.sqlite> --input <draft.json>` trả ID và trạng thái; `get --db <file.sqlite> --id <id> --output <json>` ghi lại kết quả. Không đổ toàn văn báo cáo vào log.
- Giữ `source`/SHA, `text`, language, TLP, items, evidence/span, keep/warning/status, findings, model và cost_tokens. Không thay giá trị hoặc thứ tự items khi lưu/đọc.
- Chỉ nhận schema hiện hành và status=pending; từ chối cấu trúc sai, ID/metadata do kho quản lý bị chèn, source hash sai hoặc evidence/span mâu thuẫn. Không tự sửa đầu vào sai thành đúng. Không biến dữ liệu JSON thành câu SQL hay câu lệnh.
- SQL tham số hóa; transaction ghi rõ ràng; giới hạn chờ khóa; đóng connection cả khi lỗi. Đọc DB không tồn tại phải báo lỗi, không tự tạo DB rỗng. DB lỗi không bị xóa hoặc tái tạo âm thầm.
- Đây là kho nội bộ cục bộ: không HTTP, xác thực portal, approve/reject, OpenCTI, cloud, URL/PDF, UI, lab, push/PR/merge/deploy. Không đổi core/evidence đã nghiệm thu trừ khi báo lỗi tái hiện cụ thể.
- Dữ liệu demo chỉ tổng hợp. DB, file journal/WAL và đầu ra thử nằm ngoài repo trong `x01-store-evidence/`; không commit dữ liệu lưu trữ.

### Tiêu chí nghiệm thu

1. Test trước: lưu draft thật từ `build_regex_draft`, đóng mọi connection, mở lại bằng connection mới và đọc đúng toàn bộ dữ liệu; ít nhất một demo save/get qua hai tiến trình CLI riêng.
2. Hai lần lưu tạo ID khác nhau, không ghi đè. Unicode/emoji/xuống dòng, quote và chuỗi giống SQL được giữ nguyên; items kept/rejected/allowlist và cảnh báo không mất.
3. Thiếu ID, ID sai, JSON/schema/status/hash/span sai đều có lỗi rõ, không làm mất bản ghi cũ và không tạo output get sai. Nội dung hợp lệ không bị log lộ ra terminal khi kiểm lỗi.
4. Gây lỗi ghi thực tế trong DB thử để kiểm transaction rollback; bản ghi trước giữ nguyên, lần ghi hợp lệ sau vẫn hoạt động. Kiểm DB bị khóa với timeout ngắn, không vòng retry vô hạn.
5. Dùng đúng `.venv\Scripts\python.exe` 3.12.13 cho tests/CLI/Ruff. Chạy suite phù hợp và toàn suite cuối, diff-check; demo end-to-end text→JSON→save→get, so nội dung và SHA nguồn.
6. Commit cục bộ sạch; báo đúng SHA, file, lệnh/exit, số test, giới hạn. Nếu môi trường khác, nêu path/lệnh lỗi thay vì suy đoán thiếu Python.

**Đầu ra:** `PHONG-HOA-X01-STORE-RESULT.md`, `PHONG-HOA-X01-STORE-SAMPLE.json`, log/DB tổng hợp trong `x01-store-evidence/` ở cùng thư mục kế hoạch.
**Bước nối:** Leader nghiệm thu kho và luồng tạo→lưu→đọc, rồi chuẩn bị hợp đồng tích hợp W05 theo bước 3; không cần người dùng nhắc tiếp.

## Kiểm tra Bước 2 của Leader — 10/11/2026

- Đúng nhánh `feat/x01-draft-store-20261110`, SHA `2cadea3048f7f0072938f7988197afc33e36db52`, checkout sạch.
- Leader chạy lại Python 3.12.13: 132 test đạt, exit 0; gồm tạo/lưu/đọc qua tiến trình riêng, rollback và khóa DB.
- **Chưa nghiệm thu:** kiểm thêm thấy language/TLP sai kiểu gây traceback, và JSON có IOC kept với quote rỗng
  hoặc không liên quan vẫn được lưu. Chi tiết, cách tái hiện và phạm vi sửa: `PHONG-HOA-X01-STORE-REVIEW.md`.
- Bước 3 phụ thuộc bản sửa đạt nghiệm thu. Không giao lại Bước 1; không coi các báo cáo lịch sử là việc mới.

## Nghiệm thu lại Bước 2 và nối Bước 3 — 10/11/2026

- Bước 2 đạt tại `165c6ca8abd2555348ad323e616dc6cf10b6f199`: Leader đọc diff, tự chạy 42 test store/CLI
  đạt trên Python 3.12.13, exit 0; đã đọc log Engineer toàn suite 157 test và demo đạt. Checkout sạch.
- R1/R2 đã xử lý. Chi tiết: `PHONG-HOA-X01-STORE-REVIEW.md`, log `x01-store-evidence/18-leader-review-targeted.log`.
- Bước 3: chuẩn bị hợp đồng dữ liệu và mẫu tích hợp W05; brief `PHONG-HOA-X01-W05-CONTRACT-BRIEF.md`.
  Đây là tài liệu/mẫu đã kiểm offline, không triển khai UI hoặc mở HTTP. Antigravity nhận gói bàn giao khi khả dụng.

## Nghiệm thu Bước 3 và nối hàng chờ cục bộ — 10/11/2026

- SHA `2959eb0540bd708eeae60fedd9d11b13d32b543b`, nhánh `docs/x01-w05-contract-20261110`, checkout sạch.
- Leader đọc 9 file thay đổi: chỉ docs/fixtures, không runtime/tests/dependency; nội dung hợp đồng và handoff đạt phạm vi.
- Leader tự kiểm 3/3 mẫu: hash/span và save→get giữ nguyên payload; exit 0.
  Log `x01-w05-contract-evidence/08-leader-roundtrip.log`.
- Đã đọc log Python/Node kiểm Unicode và 9 liên kết cục bộ đạt; diff-check Leader exit 0.
  Không chạy lặp suite cho docs. Handoff mới chuẩn bị, Antigravity chưa thực thi.
- Hai chỉnh lý tài liệu nhỏ sẽ đi cùng bước tiếp: escape dấu `|` ở ô language và nói rõ giới hạn kind/status
  cũng áp dụng khi đầu vào tự khai kind khác IOC, không chỉ item bị bỏ chọn.
- Bước tiếp đã chọn trong phạm vi tiếp tục ngoại tuyến: `X01-DRAFT-QUEUE`, liệt kê pending có phân trang,
  rồi đọc chi tiết theo ID. Brief `PHONG-HOA-X01-QUEUE-BRIEF.md`. Chưa mở API hoặc phê duyệt/OpenCTI.

## Nghiệm thu chức năng queue và kiểm độc lập toàn luồng — 10/11/2026

- HEAD `d03fa10523b45b94182038b5b46fed8231319e6f`, nhánh `feat/x01-draft-queue-20261110`, checkout sạch.
- Leader đọc diff 7 file, code và test mới; tự chạy 77 test store/queue trên Python 3.12.13:
  **77 passed in 8.17s, exit 0**, log `x01-queue-evidence/13-leader-store-queue.log`.
- Đọc log Engineer toàn suite **192 passed, exit 0**, Ruff/format/diff-check đạt, demo các trang
  [5,4]→[3,2]→[1] khi chèn ID 6; đọc giữ nguyên DB, summary không có toàn văn.
- Đạt phạm vi chức năng X01-DRAFT-QUEUE. Luồng tạo→lưu→liệt kê→đọc đã có kiểm chứng cục bộ.
- Trước mở rộng tích hợp, giao CTI QA Security kiểm độc lập tại SHA trên theo
  `PHONG-HOA-X01-OFFLINE-QA-BRIEF.md`; Engineer chưa được giao sửa tiếp nên SHA giữ nguyên trong lượt review.
- Chưa có HTTP/auth, UI, duyệt/từ chối, OpenCTI/lab; chưa gọi LLM hoặc đánh giá dữ liệu thật.

## Kết quả QA và sửa tính nhất quán của kho — 10/11/2026

- QA độc lập tại `d03fa10523b45b94182038b5b46fed8231319e6f`: NEEDS_FIX. Demo CLI hợp lệ, bằng chứng,
  phân trang và read-only đạt; hai lỗi mới cần sửa nằm ở get thiếu validation và save/get nhận timeout NaN.
- Leader đọc báo cáo, đối chiếu mã và hash artifact, tự tái hiện cả hai trên DB tổng hợp mới;
  log `x01-offline-qa-evidence/05-leader-confirmation.log`. Repo vẫn cùng SHA, sạch.
- Mốc offline chưa chốt sau QA; nghiệm thu chức năng queue trước đó không thay thế kết quả kiểm độc lập này.
- Giao Engineer sửa đúng hai lỗi theo `PHONG-HOA-X01-QA-FIX-BRIEF.md`; sau khi trả kết quả, Leader kiểm diff/test
  và nhờ QA xác nhận lại hai finding trên SHA mới, không mở review rộng hoặc tính năng mới.

## Leader kiểm bản sửa và chuyển QA xác nhận — 10/11/2026

- HEAD `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`, nhánh `feat/x01-draft-queue-20261110`, checkout sạch.
- Đã đọc diff 7 file: dùng chung kiểm tra timeout và giải mã/kiểm tra bản ghi cho get/list; không đổi schema hoặc dependency.
- Leader tự chạy 44 ca hồi quy mới trên Python 3.12.13, exit 0; log `x01-qa-fix-evidence/09-leader-regressions.log`.
- Đã đọc log Engineer toàn suite 236 ca, Ruff/format/diff-check và demo ba fixture đều exit 0. Đây là bằng chứng Engineer, không ghi là Leader chạy lại toàn suite.
- Chưa đóng F1/F2 hoặc chốt mốc offline: chuyển QA kiểm lại đúng hai finding trên SHA mới bằng DB tổng hợp riêng; giữ nguyên kết quả QA cũ.
- Không mở thêm tính năng trong lượt xác nhận này. HTTP/auth, UI, duyệt/từ chối, OpenCTI, dữ liệu thật và lab vẫn ngoài phạm vi đã kiểm.

## Nghiệm thu mốc bản nháp ngoại tuyến — 10/11/2026

- **PASS trong phạm vi mốc ngoại tuyến** tại `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`.
- Đích gần nhất của kế hoạch đã đạt: văn bản → IOC có bằng chứng → bản nháp pending → SQLite → danh sách phân trang → đọc chi tiết. Hợp đồng W05 và gói bàn giao UI đã có; UI chưa được thực thi.
- QA kiểm độc lập 24 tiến trình CLI: 8 lệnh hợp lệ exit 0; 6 ca dữ liệu hỏng và 10 ca timeout không hợp lệ exit 1 đúng kỳ vọng. F1 CLOSED, F2 CLOSED.
- Smoke ba fixture giữ nguyên payload/hash/span; đọc không đổi DB; lỗi không ghi đè output. Báo cáo: `PHONG-HOA-X01-QA-RECHECK-RESULT.md`.
- Leader đã đối chiếu báo cáo, JSON từng lệnh, log kiểm cuối, hash của báo cáo/JSON/DB và HEAD hiện tại; HEAD không đổi, checkout sạch. Không chạy lặp toàn suite hoặc harness khi bằng chứng đã đủ.
- Phân biệt nguồn kiểm chứng: Engineer toàn suite 236 test; Leader trực tiếp 44 regression; QA 24 tiến trình CLI độc lập. Không cộng các số này thành số test duy nhất.
- Các mốc riêng chưa hoàn thành: HTTP/auth/quyền, duyệt/từ chối và audit, UI Antigravity, tích hợp OpenCTI, LLM/TTP, đánh giá dữ liệu thật và lab. Kết quả này không phải hoàn thành toàn X01 hay dự án.
- Không có sửa lỗi còn mở trong phạm vi lần recheck này. Không giao thêm việc chỉ để xác nhận đã nhận báo cáo.
