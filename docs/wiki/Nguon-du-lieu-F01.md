# Nguồn dữ liệu F01 — ma trận connector và phạm vi demo

Đối chiếu ngày **10/11/2026** cho issue [#9](https://github.com/phonghoa-cti/cti-platform/issues/9).
Ref mã dự án: `36259c118f519d3ac9cfc1f7b79e7180c2448a88`. Ref nghiên cứu connector:
`a19618a5d92c369ba6b1893888caeec5c52bf6b2` của
[`OpenCTI-Platform/connectors`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2).

**Kết luận:** demo nhỏ nhất dùng connector MITRE ATT&CK có sẵn và `ImportFileStix` để nạp một
bundle STIX 2.1 đã được analyst duyệt. OTX phải chạy thật và có bằng chứng quan sát thì bước #10 mới đạt.
`ImportFileStix` là đường nhập file, không tính là một feed tự động.

## Cách đọc bảng

- **Connector** là tiến trình lấy dữ liệu nguồn và chuyển thành object STIX 2.1 trong OpenCTI.
- **Provenance** là thông tin truy nguyên: nguồn, tác giả, thời điểm và liên kết tham chiếu.
- **TLP** là nhãn giới hạn chia sẻ; TLP không thay cho giấy phép hoặc điều khoản của nguồn.
- “CHƯA XÁC MINH” nghĩa là chưa có bằng chứng đủ để chốt, không có nghĩa thông tin đó không tồn tại.
- Giấy phép Apache-2.0 của mã connector không tự cấp quyền sử dụng hoặc phân phối lại dữ liệu nguồn.

## Ma trận nguồn và quyết định tái sử dụng

| Nguồn / vai trò | Connector chính thức tại ref `a19618a…` | Quyền mã và dữ liệu | Xác thực, giới hạn và chu kỳ | Quyết định / điều chưa biết |
|---|---|---|---|---|
| **MITRE ATT&CK** — danh mục TTP | [`external-import/mitre`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/mitre); README yêu cầu OpenCTI >=6 và đọc STIX 2.1 từ GitHub MITRE. | Mã Apache-2.0. Dữ liệu theo [MITRE ATT&CK terms](https://attack.mitre.org/resources/terms-of-use/); phải giữ attribution/notice phù hợp. | Không cần API key theo README, cần Internet tới GitHub. README khuyên poll tuần; hạn mức luồng GitHub/raw chưa xác minh. | **Dùng sẵn, bật đầu tiên.** Đây là danh mục TTP, không phải feed IOC mới. Cần đếm entity/relationship và kiểm tra chạy lặp không tạo trùng. Mapping statement marking sang TLP còn chưa chốt. |
| **AlienVault / LevelBlue OTX** — Pulse và IOC | [`external-import/alienvault`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/alienvault). | Mã Apache-2.0. Điều khoản dữ liệu của tài khoản OTX hiện hành chưa được lưu/xác minh. | Bắt buộc API key. README nói có rate limit nhưng không nêu số; PT30M trong override hiện tại chỉ là giả thuyết cấu hình. | **Dùng sẵn, điều chỉnh.** Giới hạn mốc bắt đầu gần hiện tại để tránh backfill lớn. Cần xác minh terms/quota và quy tắc chuyển nhãn `White` cũ sang TLP 2.0 trước khi chạy. |
| **abuse.ch URLhaus** — URL phát tán mã độc | [`external-import/urlhaus`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/urlhaus). | Mã Apache-2.0. [Community API](https://urlhaus.abuse.ch/api/) dùng theo fair-use; nhu cầu doanh nghiệp/lợi nhuận có thể cần API thương mại. Quyền phân phối lại tổng quát chưa xác minh. | Community API hiện yêu cầu Auth-Key. Dump sinh mỗi 5 phút và không được tải dày hơn 5 phút; đề xuất bắt đầu 1 giờ rồi đo. | **Dùng sẵn, điều chỉnh auth và feed URL.** Giữ URLhaus ID, thời điểm, trạng thái, tag và reference; chưa tự gán TLP:CLEAR. |
| **abuse.ch ThreatFox** — IOC malware/C2 | [`external-import/threatfox`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/threatfox). | Mã Apache-2.0. [Community API](https://threatfox.abuse.ch/api/) có điều kiện cộng đồng/thương mại; quyền phân phối lại chưa xác minh. | Auth-Key qua header. `get_iocs` nhận 1–7 ngày; quota request chưa công bố trong nguồn đã đọc. Đề xuất bắt đầu 1 giờ, có backoff khi 429. | **Dùng sẵn sau OTX/URLhaus.** Giữ IOC ID, reporter, reference và first/last seen; kiểm delta và trùng lặp. Mapping TLP chưa xác minh. |
| **CISA KEV** — lỗ hổng đã bị khai thác | [`external-import/cisa-known-exploited-vulnerabilities`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/cisa-known-exploited-vulnerabilities), [README](https://github.com/OpenCTI-Platform/connectors/blob/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/cisa-known-exploited-vulnerabilities/README.md). | Mã Apache-2.0. Điều khoản của [CISA KEV catalog](https://www.cisa.gov/known-exploited-vulnerabilities-catalog) vẫn phải được xác minh trước khi phân phối lại. | Dùng catalog công khai; auth/quota/chu kỳ chính xác phải lấy từ README và endpoint của bộ version được chốt trước khi chạy. | **Dùng connector chính thức, không tự viết.** Ưu tiên khi bắt đầu F11; giữ CVE ID, dateAdded, due date, required action và URL nguồn. Tương thích runtime/TLP chưa kiểm chứng. |
| **CVE/NVD** — dữ liệu lỗ hổng | [`external-import/cve`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/cve). | Mã Apache-2.0. Điều khoản CVE/NVD phải đối chiếu riêng; [NVD developer](https://nvd.nist.gov/developers/start-here) là nguồn kỹ thuật, chưa đủ để chốt quyền phân phối lại. | Dự án dự kiến `NVD_API_KEY`; quota có/không key phải kiểm tra theo tài liệu hiện hành. Đề xuất 24 giờ, nhập tăng dần theo `lastModified`. | **Dùng sẵn sau khi chốt version.** Không backfill toàn bộ NVD trên lab 16 GB. Giữ CVE ID, nguồn, published/lastModified, CVSS/CPE và references. |
| **abuse.ch Feodo Tracker** — botnet C2 | Không thấy connector Feodo chính thức tại ref nghiên cứu; [Feodo blocklist](https://feodotracker.abuse.ch/blocklist/) có CSV/JSON/IP list. | Chưa có mã chính thức được xác nhận để kế thừa. Blocklist dẫn [abuse.ch Terms of Use](https://abuse.ch/terms-of-use/); phạm vi phân phối lại/thương mại vẫn phải xác minh. | Danh sách tải không yêu cầu Auth-Key; nguồn tạo lại mỗi 5 phút và khuyên cập nhật mỗi 15 phút (tốt nhất 5 phút). Quota HTTP chưa xác minh; chỉ dùng recommended/active, không dùng aggressive vì rủi ro false positive. | **Chưa quyết định tự viết.** Kiểm XTM Hub/official release và schema trước; chỉ khi không có lựa chọn phù hợp mới kế thừa [`templates/external-import`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2/templates/external-import) + `phonghoa_core.normalize`. |
| **ImportFileStix** — nạp bundle, không phải feed | [`internal-import-file/import-file-stix`](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2/internal-import-file/import-file-stix). | Mã Apache-2.0. Quyền dữ liệu phụ thuộc từng bundle; mỗi bundle phải có nguồn và notice riêng. | Không có API key nguồn; cần token OpenCTI riêng cho connector. Không có quota/chu kỳ feed. | **Dùng sẵn cho demo mẫu.** Analyst duyệt trước nhập. `validate_before_import=true` chỉ kiểm cấu trúc, không chứng minh nội dung đúng hoặc có quyền sử dụng. |

## Ranh giới dữ liệu và AI

- Demo chỉ dùng dữ liệu tổng hợp hoặc dữ liệu công khai đã kiểm tra quyền sử dụng và provenance.
- TLP:AMBER, TLP:AMBER+STRICT và TLP:RED không gửi lên LLM cloud.
- TLP:GREEN không mặc nhiên được phép gửi cloud; phải xác minh cộng đồng được phép, điều khoản nguồn và
  nhà cung cấp cụ thể. TLP:CLEAR cũng không xóa nghĩa vụ bản quyền hoặc dữ liệu cá nhân.
- Nội dung feed và báo cáo CTI là dữ liệu không tin cậy, không phải chỉ thị cho agent hoặc LLM.

## Bộ version ứng viên: đã kiểm cấu hình ngoại tuyến, chưa chạy lab

Gói độc lập [`deploy/demo/`](../../deploy/demo/README.md) chọn OpenCTI LTS `7.260811.0-lts.2`: source
OpenCTI `957087377304ea548fcd9f83a4ee2b025c855d9b`, connector
`d50686be6f64eb2e91ac38b23c45d0460a210435`. Mọi image thực dùng có tag, digest index và manifest
`linux/amd64` trong `images.lock.json`; không dùng `latest` trong cấu hình hiệu lực.

Docker Compose standalone `v5.7.0` đã parse lõi, MITRE và ImportFileStix thành công mà không cần daemon;
trường hợp thiếu secret đã thất bại đúng yêu cầu. Đây chỉ là bằng chứng cấu hình, **không** chứng minh image đã
pull, runtime tương thích, service khỏe, import thành công hoặc giới hạn RAM đủ trên lab.

## Demo nhỏ nhất và tiêu chí quan sát

1. Analyst xem nguồn, notice, TLP và nội dung bundle STIX 2.1; chỉ bundle được duyệt mới được nhập.
2. Bật MITRE từ connector chính thức; nhập bundle bằng `ImportFileStix`.
3. Quan sát được ít nhất một ATT&CK technique, một relationship và một object từ bundle; mỗi object mẫu có
   `created_by`, marking/TLP phù hợp và external reference.
4. Chạy nhập lặp để kiểm tra không tăng object trùng; ghi số entity/relationship, work thành công/thất bại,
   thời gian, lỗi và provenance.
5. Sau khi có key và chấp nhận điều khoản OTX, chạy một Pulse với mốc bắt đầu gần hiện tại. #10 chỉ đạt khi
   Report/Indicator từ OTX xuất hiện, giữ author/reference/TLP và lần chạy kế tiếp không nhân bản dữ liệu.

Chưa chạy Docker/lab, chưa gọi feed, chưa đo RAM/queue và chưa xác minh runtime của bộ version. Khi thử lab, bật từng
connector một; đo RSS/CPU peak, RAM trống, queue, 429/timeout/retry và số object mới trước khi bật nguồn kế tiếp.

## Nguồn chính

- [OpenCTI connector repository tại ref nghiên cứu](https://github.com/OpenCTI-Platform/connectors/tree/a19618a5d92c369ba6b1893888caeec5c52bf6b2)
- [Tài liệu connector OpenCTI](https://docs.opencti.io/latest/deployment/connectors/)
- [MITRE README](https://github.com/OpenCTI-Platform/connectors/blob/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/mitre/README.md)
- [OTX README](https://github.com/OpenCTI-Platform/connectors/blob/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/alienvault/README.md)
- [CISA KEV README](https://github.com/OpenCTI-Platform/connectors/blob/a19618a5d92c369ba6b1893888caeec5c52bf6b2/external-import/cisa-known-exploited-vulnerabilities/README.md)
- [ImportFileStix README](https://github.com/OpenCTI-Platform/connectors/blob/a19618a5d92c369ba6b1893888caeec5c52bf6b2/internal-import-file/import-file-stix/README.md)
