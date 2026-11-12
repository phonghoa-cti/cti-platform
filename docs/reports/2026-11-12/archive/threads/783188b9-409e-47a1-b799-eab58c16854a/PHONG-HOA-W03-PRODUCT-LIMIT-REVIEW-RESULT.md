# W03-PRODUCT-LIMIT-REVIEW — kết luận 128/256

**Phạm vi:** chỉ đọc `d09929311b4b6447aac8b2ec6adac5999beda25d` (12/11/2026 06:38 +07) và các báo cáo đã có. Không sửa mã, chạy test, ghi DB/cache hoặc kiểm runtime.

## Kết luận cho Leader

Nên **thống nhất `product` thành 1..256 Unicode code point ở W04 Technology, W03 dataset/read và W03 status**, giữ `vendor` 1..128 và `software_version` 1..128. Con số 128 của product trong dataset không xuất phát từ CPE/CVE/OpenCTI: nguồn CPE chỉ mô tả các thành phần vendor/product/version và tách Naming khỏi Name Matching; không đặt cap 128. Đây là một lựa chọn cục bộ cũ, nay mâu thuẫn với W04 (cả contract, store, status context và parser đều đã nhận 256).

`product` dài 256 hiện là **fixture hợp lệ theo contract W04 nhưng không hợp lệ theo contract dataset W03**. Vì W03 status phải validate toàn bộ dataset trước khi trả relation, capture `PUT technology=200` rồi `GET status=503` là hành vi fail-closed đúng với contract W03 hiện hành, không phải bằng chứng loader tự nó sai. Nhưng nó là khoảng trống chức năng của luồng W04→W03: một technology hợp lệ không thể có relation/status cho đến khi hai contract được thống nhất. Không hạ gate để ghi PASS.

| Đối chiếu đã kiểm | Bằng chứng tại ref ghim | Ý nghĩa |
|---|---|---|
| W04 Technology | `docs/specs/W04-technology-local-contract.md:33-37`; `portal_api/technologies.py:436-442` | vendor 128, product 256, version 128; Python `len` đếm code point và từ chối Cc/Cf/Cs. |
| W03 dataset/read | `docs/specs/W03-read-local-contract.md:25-38`; `portal_api/cves.py:322-332,518-534` | affected vendor/product đều 128; lỗi dataset thành `cves_unavailable`/503 trước bất kỳ kết quả nào. |
| W03 status + UI parser | `portal_api/cves_status.py:529-548,688-699`; `portal/web/data/cve-status-http.ts:26-32,54-56` | context/API/parser đã nhận product 256; parser dùng `Array.from`, tức code point, không phải UTF-16 code unit. |
| Capture hiện tại | `tools/local_integration/tests/capture_w03_status_wire.py:121-159`; `wire-fixtures/product-256-repro.json` | Gate cố ý đòi loader lỗi và status 503; phải đổi sau khi sửa contract, không xóa. |

Nguồn ngoài đã đối chiếu trong nghiên cứu W04: [NIST IR 7695](https://nvlpubs.nist.gov/nistpubs/Legacy/IR/nistir7695.pdf) và [MITRE CPE specification](https://cpe.mitre.org/specification/) chứng minh mô hình vendor/product/version, **không** chứng minh cap 128/256. [CVE CPE Applicability Guide v1.3](https://www.cve.org/Resources/Roles/Cnas/CPEinCVERecordsGuide.pdf) cho thấy matching/version range là lớp khác; không thêm range/CPE/alias vào sửa lỗi giới hạn này.

## Cách sửa nhỏ nhất và allowlist đề xuất

**Khuyến nghị:** chỉ nâng W03 *affected product* từ 128 lên 256 để khớp W04; giữ exact `casefold` match, các cap fixture 4 MiB/1.000 candidate/20 products, response 1 MiB, cursor 1.024 ASCII, history page ≤100, status PUT 16 KiB và technology mutation 8 KiB. Không thay pagination, body cap, rank, version assessment, status/audit, gateway hay UI flow. Các cap body vẫn đủ cho một product 256 (kể cả UTF-8 nhiều byte), nhưng phải kiểm bằng body thực tế chứ không suy từ số ký tự.

Allowlist code/doc/test cho một task Backend+integration hẹp:

- `portal_api/cves.py` — `_product(..., 256)`; dùng cùng quy tắc trim + Cc/Cf/Cs như Technology.
- `docs/specs/W03-read-local-contract.md` — affected product 256; ghi rõ code point.
- `portal_api/tests/test_cves_api.py` — boundary dataset 256/257 thay cho test 129 fail-closed.
- `tools/local_integration/tests/capture_w03_status_wire.py` và fixture evidence tương ứng — đổi gate `product 256` từ “loader lỗi + status 503” sang “dataset hợp lệ + GET status 200 và context/match product 256”; bổ sung product 257 vẫn loader lỗi + 503.
- `portal_api/cves_status.py`, `portal/web/data/cve-status-http.ts`, `portal/web/data/cves-http.ts` **chỉ sửa nếu** kiểm tra cho thấy control-char/trim không đồng nhất; hiện chúng đã có cap 256. Không mở rộng file ngoài danh sách này.

Rủi ro tương thích thấp: producer dataset synthetic dài 129..256 trước đây bị từ chối 503, sau thay đổi sẽ được nhận; đó là thay đổi có chủ ý đã được W04 contract cho phép. Consumer W03 UI đã parse 256 nên không cần “nới gate” ở frontend. Rủi ro còn lại là khác nhau về control character: `cves.py`/Technology từ chối Cc/Cf/Cs, còn `_visible` của status trong ref chỉ Cc/Cs. Nên đồng bộ **Cf** tại boundary status và cả parser nếu regex chưa bao phủ Cf; không tự chuẩn hóa NFKC hay alias vì sẽ đổi identity match.

## Ca kiểm bắt buộc trước khi Leader chấp nhận

| Ca | Kỳ vọng |
|---|---|
| vendor 128 / 129 | 128 nhận ở Technology, dataset và status context; 129 bị từ chối đúng boundary, không ghi status/audit. |
| product 128 / 129 | Cả hai nhận (sau đổi product dataset=256); chứng minh loại bỏ legacy cap 128. |
| product 256 / 257 | 256 qua Technology → dataset → exact match → status GET/PUT hợp lệ; 257 bị W04 và dataset từ chối fail-closed, status 503 khi dataset hỏng, không mutation. |
| Unicode | Dùng ký tự astral (ví dụ `😀`) để chứng minh Python `len` và JS `Array.from` cùng đếm code point; Cc/Cf/Cs, whitespace đầu/cuối bị từ chối nhất quán. Không dùng `.length` JS làm oracle. |
| Body/pagination | Product 256 UTF-8 4-byte với request dưới/qua 8 KiB (technology) và 16 KiB (status); giữ response W03 ≤1 MiB, cursor 1.024 ASCII, history limit 100 và không đổi query/page semantics. |
| Capture/gate | Capture cũ phải đổi expectation 503→200 **chỉ cho fixture dataset 256 hợp lệ**; giữ ca 257 để chứng minh 503. Khẳng định context product 256, match, `review_required`/status shape và mutation/audit count riêng; không chỉ kiểm HTTP code. |

**Chưa xác minh:** không có test mới, browser/runtime/gateway/lab/production, feed/CPE/NVD/OpenCTI thật. Khuyến nghị là điều chỉnh contract và brief code; chưa phải thay đổi đã triển khai.
