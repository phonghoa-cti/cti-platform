# Kiểm chứng của lần công bố GitHub

Ngày 12/11/2026, giờ Việt Nam. Đây là kiểm tra tính đầy đủ/an toàn của bản công bố, không phải nghiệm thu lại toàn bộ tính năng.

## Đã kiểm trước công bố

- Đọc working agreement, quy trình điều phối và AGENTS trên nhánh tích hợp; tái dùng nghiên cứu GitHub Flow và hồ sơ kỹ thuật hiện có.
- Đối chiếu các cuộc đang mở: các cuộc đã liệt kê ở trạng thái idle. Không dựa vào `dispatched` trong sổ để tuyên bố đang có worker chạy.
- Đọc trực tiếp GitHub: repo `phonghoa-cti/cti-platform` công khai, nhánh mặc định `main`; PR #1/#46 còn mở với các SHA đã ghi trong báo cáo.
- `git worktree list --porcelain` và `git status --porcelain`: 42 working tree nguồn sạch. 52 ref dự án được chốt bằng SHA; không có thay đổi chưa commit phải tự động gom vào.
- `git ls-remote --heads origin`: trước công bố chỉ có `main`, `feat/cap-nhat-bo-khoi-dong`, `feat/x01-nen-tang`. SHA được lưu trong git-snapshot.json.
- HEAD W03-S1 là `f5d2315e94b7f83e44360a04b67902cb5b0ba4bd`; diff từ `867bdcae` chỉ `docs/PROGRESS.md`. Không suy commit tài liệu thành nghiệm thu sản phẩm mới.
- 413 tài liệu nguồn được sao chụp, thay đường dẫn máy bằng ký hiệu portable; manifest giữ SHA-256 của bản gốc và bản công bố. 89 task và 133 commit được ghi thành danh mục.

## Quét thông tin nhạy cảm

Dùng Gitleaks **8.30.1**, tải từ release chính thức và đối chiếu checksum công bố. SHA-256 gói Windows: `d29144deff3a68aa93ced33dddf84b7fdc26070add4aa0f4513094c8332afc4e`.

Lệnh quét lịch sử nguồn: `gitleaks git cti-platform-start --log-opts="--branches --not --remotes=origin" --redact=100 --report-format json`. Quét 133 commit, khoảng 4.54 MB diff. Lần đầu exit 1 với một cảnh báo generic-api-key tại commit `7ece3c3a47541c40e7baa430792d631bc22c623d`, `extractor/eval/report.py:102`.

Đọc đúng dòng lịch sử cho thấy đó là phép hợp tập tên trường: `C4_ROOT_KEYS = C23_ROOT_10_KEYS | {"query_manifest_sha256", "ttp_audit"}`. Đây là cảnh báo sai, không phải credential. Chỉ bỏ qua đúng fingerprint này trong file phục vụ lượt quét cục bộ, không đổi cấu hình quét của repo hoặc CI. Quét lại cùng phạm vi: **exit 0, không có phát hiện còn lại**. Gitleaks là kiểm theo quy tắc, không phải chứng minh tuyệt đối không có dữ liệu nhạy cảm.

Kết quả quét archive, xác minh hash/liên kết và đối chiếu remote sau push được ghi ở phần kết quả công bố bổ sung. Log chi tiết của thao tác công bố được giữ trong thư mục `github-publish-20261112` của workspace Leader.

Archive đã được quét riêng khoảng 2.86 MB. Ba cảnh báo được đọc kiểm: câu trích phép hợp tập tên trường ở tài liệu này, SHA nguồn API trong báo cáo W02 và cùng SHA đó trong sổ việc. Cả ba là nội dung mã/định danh Git, không phải credential; bỏ qua đúng ba fingerprint trong cấu hình tạm của lượt quét. Quét lại: **exit 0, không còn phát hiện**. Không sửa báo cáo gốc hoặc nới quy tắc của repo để che cảnh báo.

Bộ kiểm sổ hiện hành chạy read-only cho kết quả `YIELD` với hai task `W03-STATUS-INTEGRATION` và `W03-STATUS-S2-NEXT`, exit 0. Đây chỉ là bằng chứng trạng thái sổ hợp lệ, không xác nhận có worker đang chạy.

## Phân biệt bằng chứng

Các test tính năng trong báo cáo tổng hợp là bằng chứng lịch sử có dẫn hồ sơ/SHA. Lượt này không chạy lại full suite Python/Frontend/browser, không gọi feed/model thật hoặc khởi động lab. Các raw log/ảnh/database chưa được commit không được tự động tải lên kho công khai; báo cáo, hash và chỉ dẫn gốc giúp tìm lại chúng tại máy làm việc.

## Kiểm tra toàn vẹn và push mã

- Kiểm lại **413/413 hash tài liệu công bố và 413/413 nguồn gốc**, **438 liên kết nội bộ**, **52 SHA nhánh**, **42 working tree nguồn sạch**: exit 0. Source hash không bị thay đổi. Các bản công bố chuẩn hóa LF và khoảng trắng cuối dòng, hash công bố được tính sau chuẩn hóa.
- Bản sao 3 file công cụ điều phối có [manifest riêng](workflow-manifest.json); đây là script/test đã có, không triển khai thuật toán mới.
- Dry-run `git push --atomic --porcelain origin <SHA>:refs/heads/<branch> ...`: 52 ref, exit 0.
- Push thật cùng 52 ref, không force, không xóa ref: exit 0. `git ls-remote --heads origin` sau push xác nhận **52/52 SHA khớp**; `main` và hai nhánh PR cũ vẫn giữ nguyên SHA. [Biên nhận đối chiếu remote](code-push-verified.json).
- Nhánh hồ sơ là `docs/current-results-20261112`, được commit/push riêng sau khi lưu biên nhận 52 nhánh mã. Liên kết GitHub của nhánh hồ sơ là điểm vào cho lần công bố này; không mở PR hoặc thay nhánh mặc định.
- `git diff --cached --check`: exit 0. Diff công bố gồm 432 file: hồ sơ quá trình, tiến độ, devlog và quy tắc LF cho archive; không đổi source/runtime sản phẩm. Lần quét archive cuối khoảng 2.87 MB, exit 0 sau các cảnh báo sai đã phân loại.
