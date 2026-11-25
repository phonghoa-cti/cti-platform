# Kết quả tích hợp tài liệu F01/#9

Ngày thực hiện: **10/11/2026**
Checkout: `$WORKSPACE\cti-platform-start`
Nhánh: `docs/f01-source-inventory-20261110`
Base: `36259c118f519d3ac9cfc1f7b79e7180c2448a88`
Commit tài liệu: `7775fee8c456f15dca3e7202b9265f29b0a5f103`

## Kết quả

PASS trong phạm vi tài liệu. Chỉ ba file đã thay đổi và được commit cục bộ:

1. `docs/wiki/Nguon-du-lieu-F01.md`: thêm ma trận MITRE, OTX, URLhaus, ThreatFox, CISA KEV,
   CVE/NVD, Feodo và ImportFileStix; tách quyền mã/dữ liệu, auth/giới hạn, quyết định tái sử dụng và
   điều chưa biết.
2. `docs/wiki/Home.md`: thêm liên kết Wiki tương đối tới trang nguồn F01.
3. `docs/PROGRESS.md`: cập nhật ngày, ref/kết quả baseline và phần chưa kiểm chứng trên lab.

CISA KEV được mapping đúng sang connector chính thức
`external-import/cisa-known-exploited-vulnerabilities` tại ref connector
`a19618a5d92c369ba6b1893888caeec5c52bf6b2`; quyết định là dùng sẵn, không tự viết.
Feodo chỉ là phương án tự viết có điều kiện sau khi kiểm tra lại giải pháp phù hợp, chưa triển khai.

Trang wiki ghi rõ:

- ImportFileStix là đường nhập bundle, không tính là feed tự động.
- Analyst duyệt bundle, quyền dữ liệu, provenance và TLP trước khi nhập.
- #10 chỉ đạt khi OTX chạy thật và có object/provenance quan sát được, không trùng ở lần chạy kế tiếp.
- TLP:AMBER, TLP:AMBER+STRICT và TLP:RED không gửi cloud; TLP:GREEN không mặc nhiên được phép.
- Chưa có bộ version OpenCTI/worker/connector đã kiểm chứng; không bịa số hoặc dùng `latest` làm pin.

## Diff và kiểm tra

```text
git diff --cached --check
exit 0

git diff --cached --stat
docs/PROGRESS.md               |  9 ++++--
docs/wiki/Home.md              | 10 +++---
docs/wiki/Nguon-du-lieu-F01.md | 71 ++++++++++++++++++++++++++++++++++++++++++
3 files changed, 84 insertions(+), 6 deletions(-)
```

Kiểm tra Markdown bằng script chỉ đọc:

- Link tương đối và code fence: 0 lỗi.
- Bảng ma trận: 10 dòng (header, separator và 8 nguồn/đường nhập), 0 dòng sai số cột.
- Từ khóa bắt buộc cho 8 nguồn, TLP và điều kiện #10: tìm thấy, exit 0.
- `git diff HEAD^ HEAD --check`: exit 0 sau commit.
- `git status --short --branch`: chỉ hiện nhánh, không có thay đổi chưa commit.

Không chạy lại pytest/Ruff vì thay đổi chỉ là Markdown và baseline cùng base SHA đã được Leader xác minh.

## Giới hạn chưa kiểm chứng

- Chưa có candidate version/tag/digest được Research chốt; trang wiki giữ trạng thái chưa kiểm chứng.
- Chưa chạy Docker/Compose hoặc service; chưa gọi feed/LLM; chưa dùng key; chưa đo RAM, queue, timeout,
  rate limit hoặc tính tương thích runtime.
- Chưa xác minh điều khoản tài khoản OTX và các quyền phân phối dữ liệu còn đánh dấu CHƯA XÁC MINH.
- Không sửa spec, code, CI, TLP skill hoặc deploy; không push, tạo PR, merge, đóng issue hay ghi GitHub.

## Hoàn tác

Commit chỉ chứa tài liệu. Khi cần hoàn tác sau này, tạo commit đảo bằng
`git revert 7775fee8c456f15dca3e7202b9265f29b0a5f103`; không cần xóa lịch sử hoặc reset nhánh.

## Học thêm

- **Data provenance** là bằng chứng giúp truy lại dữ liệu đến nguồn và thời điểm ban đầu.
- **Image digest** định danh chính xác nội dung image, ổn định hơn tag `latest`.
- **ImportFileStix** là đường nhập file do người dùng cung cấp, không phải connector tự kéo feed theo lịch.
