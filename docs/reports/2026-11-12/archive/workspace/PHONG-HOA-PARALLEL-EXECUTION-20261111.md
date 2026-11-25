# Phân công thực thi song song — 11/11/2026

Root: `$WORKSPACE`.

Mục tiêu giữ nguyên: tài liệu TXT/PDF → hàng chờ → chọn/duyệt → STIX; đồng thời phát triển tra cứu IOC W02 theo thiết kế hiện có. Đây là điều chỉnh phân công theo yêu cầu làm song song, không mở rộng sang phát hành/lab/model thật.

## Bằng chứng và lựa chọn

- Đã xem threads và đội hiện có trước ghi sổ. Lượt Frontend `240e11ed-9c7b-4c7f-b288-1f5b90d2ee20` đã cancelled vì yêu cầu cha bị dừng; tree có sửa dở. Nối lại đúng thread/branch, không tạo người thay hoặc reset.
- QA `b3127421-f492-4763-875b-72be4543f54f` đã completed, kết luận FAIL tại importer `db36ec01b765dfd515c1d0ef13642a693b777172`. Leader đọc source và tái hiện độc lập U+0085 được import thành draft 2 trên DB tổng hợp riêng. Chưa nghiệm thu importer.
- Research `217d52c9-6759-425a-b55f-7a9c686c007a` đã completed; brief W02 hash `93dab3d51d5e62e63711f6dc7fbd6b05a5c039c38f62e6e667b3ac2b34da84df`. Đọc và chốt bổ sung bên dưới, không giao nghiên cứu lại.
- Tái dùng brief demo đã được chấp nhận ở mức chuẩn bị. Chọn cho Engineer viết phần điều khiển demo trong tree riêng ngay; việc chạy nghiệm thu browser vẫn phải đợi importer đã sửa được chấp nhận. Không bắt Engineer chờ để viết mã không chồng lấn; không dùng kết quả trên importer cũ để báo luồng hoàn thành.

## Một người — một phạm vi

| Owner | Task | Phạm vi ghi | Điều kiện nối |
|---|---|---|---|
| Backend / Sol medium | X01-INGEST-QUEUE-IMPLEMENT, sửa F1 | Tree `cti-x01-ingest-queue`, chỉ file bên dưới | Leader kiểm F1 và dữ liệu không bị ghi khi lỗi |
| Frontend / Sol medium | W02-LOOKUP-VIEW, nối lại R1/R2 | Tree `cti-w02-lookup-ui`, allowlist review hiện có | 7 probe Leader + kiểm web đạt; API nối ở bước sau |
| Engineer / Sol medium | X01-INGEST-BROWSER-HARNESS | Tree mới `cti-x01-ingest-browser-prep`, chỉ `tools/local_integration` đã chỉ định | Chuẩn bị code/kiểm offline; chưa được chạy nghiệm thu browser |
| Backend, sau F1 | W02-LOOKUP-API-IMPLEMENT | Tree mới `cti-w02-lookup-api` từ W05 ổn định | Chỉ giao sau Backend trả F1; không hai việc đồng thời cho cùng người |
| QA | Kiểm lại phần sửa rủi ro khi có SHA ổn định | Evidence riêng, source chỉ đọc | Không sửa tree tác giả, không chạy lại toàn bộ mặc định |
| Leader | Hợp đồng chung, nghiệm thu, chọn bước tích hợp | Sổ tổng/kế hoạch/bằng chứng riêng | Không tự merge/deploy |

Research đã có đầu ra; AI Agent không thay người gán nhãn hay gọi model thật. Chưa thêm thành viên vì ba phạm vi triển khai hiện đã có chủ sở hữu, điểm chờ kế tiếp là nghiệm thu đầu vào.

## Backend — sửa F1 đúng phạm vi

Tiếp tục thread `b90466c0-6172-4dc5-b9b8-b106cecea3f9`, branch `feat/x01-ingest-queue-20261111`, HEAD `db36ec01b765dfd515c1d0ef13642a693b777172`; không tạo lại tree. Đọc `PHONG-HOA-X01-INGEST-QUEUE-QA-RESULT.md`, brief và AGENTS hiện có.

- Lỗi ở `_valid_name`, `extractor/phonghoa_extractor/ingest_queue.py`: chỉ chặn C0/DEL, bỏ lọt C1. Sửa nhỏ nhất là cấm toàn bộ Unicode category `Cc`, giữ cấm `/` và `\`. Không dùng `isprintable()` để vô tình cấm thêm các dấu cách hợp lệ; UTF-8/surrogate vẫn theo validator hiện có. Không hứa xử lý mọi lừa đảo hiển thị.
- Nguồn xác minh: [Python unicodedata.category](https://docs.python.org/3/library/unicodedata.html#unicodedata.category), [str.isprintable](https://docs.python.org/3/library/stdtypes.html#str.isprintable); nghiên cứu còn lại tái dùng QA/brief đã có.
- Cho phép sửa `extractor/phonghoa_extractor/ingest_queue.py`, `extractor/tests/test_ingest_queue.py`, `extractor/tests/test_ingest_queue_cli.py`, `docs/PROGRESS.md` mục task; report cũ và evidence mới `x01-ingest-queue-evidence/rework-f1/`. Không sửa store/migration/schema/producer/API/UI hoặc evidence QA.
- RED→GREEN: U+0085/U+009F (nên phủ C0/C1 đầy đủ), library và CLI trả lỗi đóng; DB bytes/count/provenance/version không đổi. Tên tiếng Việt, khoảng trắng và emoji hợp lệ vẫn nhập được. Test mới không được sửa probe QA cũ để biến FAIL thành PASS.
- Chạy hai test ingest, kiểm hồi quy liên quan nếu sửa lan, Ruff check/format và diff-check. Không lặp full 553 hay browser/build vì thay đổi nhỏ này. Raw command/exit/count, HEAD/diff/status, hash evidence và commit local sạch. Không sửa mã khi chưa giữ sửa đổi có sẵn.

## Frontend — nối lại đúng việc bị dừng

Thread `0ab8095a-ac5a-49ca-be0d-b3d67988e6c8`, tree `cti-w02-lookup-ui`, HEAD `d5a3aa4eda20491937da3ab4b4e29198f9563c7c`. Đã có sửa dở trong hai file sản phẩm, test và PROGRESS; đọc diff rồi hoàn tất, không reset. Theo nguyên `PHONG-HOA-W02-LOOKUP-UI-REVIEW-20261111.md`: own-key fixture, callback clipboard không cập nhật kết quả mới, probe 7/7, các kiểm web đã chỉ định. Không đổi thiết kế hoặc chờ API để sửa hai lỗi này.

## Engineer — code demo tách riêng, giữ gate nghiệm thu

Đây là triển khai phần điều khiển demo, thay thế điều kiện phải chờ trước mọi hoạt động viết mã trong brief chuẩn bị; giữ nguyên điều kiện importer đạt trước nghiệm thu browser.

- Tạo `cti-x01-ingest-browser-prep`, branch `feat/x01-ingest-browser-prep-20261111` từ commit bất biến `db36ec01b765dfd515c1d0ef13642a693b777172`. Tạo tree qua repo W05 `cti-x01-w05-stix-e2e`; không đọc HEAD đang đổi hoặc sửa working tree Backend. Nếu target/branch đã có người sửa thì báo, không reset.
- Đọc `PHONG-HOA-X01-INGEST-BROWSER-INTEGRATION-BRIEF.md` và phần browser-prep của `PHONG-HOA-INGEST-W02-REVIEW-20261111.md`. Producer chỉ đọc tại `cti-x01-ingest-local@8a16758601647fb3dbf935abecc2435f3b7a3fb6`.
- Viết khả năng seed bằng producer/importer CLI và hậu kiểm cùng SQLite, tái dùng LocalRun và helpers. Không sao chép parser hoặc sửa importer. Hợp đồng CLI, creator, provenance/schema v3 giữ nguyên. Kiểm số IOC thực của TXT/PDF trước chọn, không mặc định thứ tự.
- Allowlist: `tools/local_integration/runner.py`, `tools/local_integration/tests/test_runner.py`, `tools/local_integration/tests/run_stix_e2e.py`, mới `tools/local_integration/tests/run_ingest_browser_stix.py`, helper mới nếu cần dưới `tools/local_integration/tests/ingest_*`, `tools/local_integration/README.md`, `docs/PROGRESS.md` mục task. Không sửa portal/API/extractor/core/config/dependency/lock/RUNS.
- Giai đoạn này dùng unit/in-process và CLI với dữ liệu tổng hợp, không mở browser/listener phục vụ demo. Có thể test seed/postcheck riêng không gọi LocalRun.start; mock vòng đời nếu cần. Test runner hiện có nếu cần loopback thì dùng port tự cấp, DB/process/temp riêng và cleanup; không chạm port 3012. Không cài hoặc điều khiển trình duyệt khác. Có cleanup/EOF/timeout hữu hạn cho lượt browser tương lai; không đợi trong lệnh.
- Chạy test runner và test helper mới, Ruff check/format trên phần đổi, diff-check. Report `PHONG-HOA-X01-INGEST-BROWSER-HARNESS-RESULT.md`, evidence `x01-ingest-browser-harness-evidence/`, commit local. Nêu rõ base chứa F1 chưa sửa và browser/end-to-end vẫn UNVERIFIED.
- Trả kết quả để Leader chọn cách đưa patch điều khiển demo lên importer đã nghiệm thu. Không tự cherry-pick/merge hoặc chạy browser khi thấy Backend có commit mới. Bước tích hợp cuối có brief/SHA riêng sau khi hai đầu đạt.

## W02 — chốt bổ sung contract, sẵn sàng cho Backend sau F1

Brief Research ở hash trên được chấp nhận ở mức thiết kế, kèm các điểm rõ hơn dưới đây; chưa có API hay kiểm runtime.

- DTO `Source` trả ra gồm đúng `name, first_seen, last_seen, tlp` theo fixture; không lộ source_id/reliability/metadata nội bộ. Found phải có ít nhất một source visible. Score.parts chỉ null ở allowlisted; not_found score null.
- Record có `record_tlp` ngoài quyền người dùng phải trả not_found như record vắng mặt, trước xử lý nested facts; không hạ nhãn record bằng cách lấy nhãn nguồn thấp hơn. Record hợp lệ trong quyền có mixed nested facts thì lọc facts ngoài quyền trước score/serialization. Chỉ DTO sai schema/type/unknown TLP trả 503; sự có mặt của facts bị ẩn hợp lệ không phải lỗi 503.
- Dedupe nguồn theo source_id sau lọc; duplicate visible mâu thuẫn trả 503, không chọn tùy ý. Mốc as_of là mốc công khai/fixture cố định, độc lập với dữ liệu ẩn; nếu adapter không bảo đảm điều đó thì dùng mốc do service cung cấp. Mutation test giữ cùng query/time phải chứng minh dữ liệu ẩn không đổi bất kỳ response IT nào.
- Thông báo cố định cho auth/role/invalid/private/unavailable theo bảng hữu hạn trong code; không echo exception. Các mã, thứ tự auth→role→query và headers giữ nguyên brief.
- W02 API không phụ thuộc mã importer mới: exact base vẫn `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`, tree/allowlist theo brief Research. Chỉ đợi Backend rảnh; chưa có dispatch thì ghi planned.

## Kết thúc lượt phân công

Ghi receipt thật vào RUNS, giữ lịch sử request và thread. Kết quả trước mới là evidence, không dùng trạng thái queued để nói đang chạy. Leader chỉ kiểm phần mới/rủi ro, không lặp toàn suite; lỗi cùng nguyên nhân tối đa hai lần. Không push/PR/merge/deploy, secret, mạng/model/cloud/lab hoặc dữ liệu hạn chế. Dự án còn active, giữ hai lịch tiếp tục hiện có.
