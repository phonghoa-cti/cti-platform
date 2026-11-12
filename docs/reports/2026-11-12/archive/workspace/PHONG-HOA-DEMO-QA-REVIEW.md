# QA Security review — gói chuẩn bị demo F01

Ngày review: 10/11/2026
Reviewer: CTI QA Security
Base đối chiếu: `7775fee8c456f15dca3e7202b9265f29b0a5f103`
Snapshot bất biến được review: `e169aed479eedc9edec5eb5369c57fc776e66947`

## Kết luận

**FAIL — chưa đủ để bắt đầu lượt thử lab theo đúng hướng dẫn hiện tại.** Hai lỗi tài liệu có thể làm lượt lab dừng ở boot/import hoặc bỏ qua ranh giới duyệt của analyst:

1. Mẫu môi trường chỉ bắt giá trị không rỗng, nhưng không chỉ định/kiểm các định dạng bắt buộc của OpenCTI và connector.
2. Trình tự nhập STIX nhảy từ upload sang kiểm object, bỏ qua workbench review + validation trước khi dữ liệu vào knowledge base.

Đây là kết luận về **độ sẵn sàng chuẩn bị thử lab**, không phải quyền merge/deploy. Không có phát hiện chặn mới trong cấu trúc Compose, scope/type/default của hai connector hoặc cấu trúc STIX sau khi đối chiếu nguồn đúng release. Lỗi heap đã biết (`ES 4g/4g`, `Node 3072/3g`) bị loại khỏi kết luận theo brief vì Engineer đang sửa riêng.

## Phát hiện cần sửa

### QA-01 — HIGH — Giá trị sai định dạng vẫn qua `docker compose config` rồi có thể làm platform/connector không khởi động

- **Trạng thái:** FAIL.
- **Bằng chứng tại snapshot:**
  - `deploy/demo/.env.example:7-24` để trống các biến nhưng không nêu schema/định dạng.
  - `deploy/demo/README.md:35-40` chỉ nói điền secret/tài khoản và dùng `${VAR:?message}`.
  - `${VAR:?message}` trong `deploy/demo/compose.yml:88-92` và hai overlay chỉ chứng minh biến không rỗng, không chứng minh giá trị hợp lệ.
- **Đối chiếu nguồn:**
  - Hướng dẫn cài đặt OpenCTI chính thức cảnh báo `OPENCTI_ADMIN_TOKEN` phải là UUID hợp lệ, nếu không container không start; ví dụ chính thức tạo token bằng UUID và `OPENCTI_ENCRYPTION_KEY` bằng `openssl rand -base64 32`: <https://docs.opencti.io/latest/deployment/installation/>.
  - Breaking changes OpenCTI 7 yêu cầu khóa mã hóa ngẫu nhiên, ít nhất 32 byte và Base64: <https://docs.opencti.io/latest/deployment/breaking-changes/>.
  - Upstream Compose tại ref đã chọn ghi connector ID là UUIDv4: <https://github.com/OpenCTI-Platform/docker/blob/60285adb360e3823a334333ae4744255d8ac1821/docker-compose.yml#L236-L246>.
  - Source connector đúng commit mô tả `connector.id` là UUID v4; `OPENCTI_TOKEN` là token API của user đại diện connector: <https://github.com/OpenCTI-Platform/connectors/blob/d50686be6f64eb2e91ac38b23c45d0460a210435/internal-import-file/import-file-stix/src/connector/settings.py> và <https://github.com/OpenCTI-Platform/connectors/blob/d50686be6f64eb2e91ac38b23c45d0460a210435/external-import/mitre/__metadata__/CONNECTOR_CONFIG_DOC.md>.
- **Tình huống lỗi:** sinh viên điền chuỗi ngẫu nhiên không rỗng cho `OPENCTI_ADMIN_TOKEN` hoặc khóa mã hóa, Compose parse exit 0 như bằng chứng hiện có, nhưng platform dừng khi boot. Tương tự, dùng ID không phải UUIDv4 hoặc nhầm ID connector với token user làm connector không đăng ký được.
- **Cách khắc phục tối thiểu:** thêm vào `.env.example`/README định dạng và lệnh tạo giá trị cho lab; phân biệt rõ `CONNECTOR_*_ID` (UUIDv4 riêng, duy nhất) với `CONNECTOR_*_TOKEN` (API token của user connector riêng). Trước pull/boot, chạy một kiểm tra offline từ chối admin token/connector ID không phải UUIDv4 và khóa mã hóa không phải Base64 của ít nhất 32 byte. Không in secret ra log.

### QA-02 — HIGH — Quy trình analyst duyệt → nhập → tra thiếu bước workbench validation

- **Trạng thái:** FAIL.
- **Bằng chứng tại snapshot:**
  - `deploy/demo/compose.import.yml:12-14` đặt `CONNECTOR_VALIDATE_BEFORE_IMPORT=true` và `CONNECTOR_AUTO=false`.
  - `deploy/demo/README.md:74-82` có duyệt file trước upload, sau đó đi thẳng từ upload (bước 5) sang kiểm object đã nhập (bước 6); không có bước analyst xem và validate workbench.
  - `docs/wiki/Nguon-du-lieu-F01.md:54-59` cũng đi từ “bundle được duyệt” sang bật connector/quan sát dữ liệu mà không nêu workbench.
- **Đối chiếu nguồn:**
  - Mã connector đúng commit gọi `send_stix2_bundle`; khi bật validate và không bypass, kết quả là “Generated bundle sent for validation”, chưa phải nhập vào knowledge base: <https://github.com/OpenCTI-Platform/connectors/blob/d50686be6f64eb2e91ac38b23c45d0460a210435/internal-import-file/import-file-stix/src/connector/connector.py>.
  - Tài liệu chính thức mô tả output của file connector nằm trong analyst workbench và chỉ vào knowledge base sau review + validation; user khởi tạo import cần capability `Upload knowledge files`: <https://docs.opencti.io/latest/usage/import-files/>.
- **Tình huống lỗi:** operator upload fixture rồi tìm object ngay; không thấy dữ liệu và kết luận sai rằng connector/import hỏng. Nguy hiểm hơn, checklist hiện có thể được dùng để tuyên bố đã giữ ranh giới duyệt bởi con người dù không ghi bằng chứng ai đã review/validate workbench.
- **Cách khắc phục tối thiểu:** sau upload, ghi rõ cách khởi chạy connector nếu UI không tự chạy với `CONNECTOR_AUTO=false`; chờ work hoàn tất; analyst có đúng capability mở workbench, kiểm object/relationship/marking/provenance, rồi bấm validate; chỉ sau đó mới đếm/tra knowledge base. Ghi người duyệt, trạng thái work và bằng chứng trước/sau; không dùng bypass validation.

### QA-03 — MEDIUM — Tiêu chí provenance trong wiki không khớp fixture và mô hình STIX

- **Trạng thái:** FAIL cho tiêu chí tài liệu; fixture vẫn PASS cấu trúc.
- **Bằng chứng tại snapshot:**
  - `docs/wiki/Nguon-du-lieu-F01.md:56-57` yêu cầu “mỗi object mẫu” có `created_by`, marking/TLP và external reference.
  - `deploy/demo/fixtures/demo-bundle.json:17-46` cho thấy identity và hai SCO (IPv4/domain) không có `created_by_ref` hay `external_references`.
  - `deploy/demo/fixtures/demo-bundle.json:48-68` indicator có `created_by_ref` và marking nhưng không có external reference.
  - Chỉ report tại `deploy/demo/fixtures/demo-bundle.json:86-111` có external reference và chứa các object qua `object_refs`.
- **Tình huống lỗi:** analyst áp checklist theo chữ sẽ phải FAIL một fixture hợp chuẩn, hoặc người chạy demo đánh dấu PASS mà không thực sự đối chiếu từng trường.
- **Cách khắc phục tối thiểu:** đổi tiêu chí thành: mọi object hỗ trợ marking đều có marking phù hợp; indicator/relationship/report có `created_by_ref`; report có external reference mô tả nguồn tổng hợp; SCO được truy nguyên qua report/object refs và relationship. Không thêm trường không hợp lệ vào SCO chỉ để thỏa câu chữ.

## Kiểm tra theo phạm vi

| Kiểm tra | Kết luận | Bằng chứng |
|---|---|---|
| Đúng ref và 11 file | PASS | `git diff --name-status 7775fee..e169aed`: 11 file đúng brief. Nội dung đọc bằng `git show e169aed:<path>`. |
| Core 6 service, port/network/socket | PASS tĩnh | `compose.yml:3-150`: 6 service; chỉ `127.0.0.1:${OPENCTI_PORT}:8080`; không socket, privileged hoặc host network. Runtime network/health vẫn UNVERIFIED. |
| OpenCTI/worker/health env | PASS tĩnh, trừ QA-01 | Tên biến và healthcheck khớp upstream Compose `60285adb…`; chỉ thiếu kiểm schema secret. |
| MITRE config | PASS tĩnh | `compose.mitre.yml:8-14` khớp source commit: URL/token/ID/name, scope `mitre`, interval 7. `CONNECTOR_TYPE` mặc định `EXTERNAL_IMPORT` trong image Dockerfile đúng commit. |
| ImportFileStix config | PASS tĩnh, trừ QA-02 | scope `application/json,text/xml`, auto false, validate true khớp source commit; `CONNECTOR_TYPE=INTERNAL_IMPORT_FILE` có trong Dockerfile image nên không coi trường vắng ở Compose là lỗi. |
| Token connector tách admin | PASS tĩnh | Hai overlay dùng token riêng; README cấm dùng admin token. Quyền thực tế và capability chưa được kiểm trên lab. |
| Fixture STIX | PASS cấu trúc | Review độc lập: `stix2-validator 3.3.2 --version 2.1 --strict --enforce-refs` exit 0; 7 object, 1 relationship, 0 internal ref thiếu. Tiêu chí wiki sai câu chữ được tách ở QA-03. |
| Image pin/digest | KHÔNG LẶP | Leader đã kiểm registry 8 image; QA chỉ xác nhận Compose dùng tag + digest và lock có 8 entry. Không pull image. |
| Baseline test/lint | KHÔNG LẶP | 61 test/digest registry nằm ngoài review tập trung và đã có evidence trước đó. |
| `git diff --check` | PASS | Chạy cho `7775fee..e169aed`, exit 0. |
| Lab/runtime/#10 | UNVERIFIED | Không pull/boot, không gọi feed, không nhập thật, không đo RAM/queue. OTX/key/terms chưa có; #10 chưa đóng. |

## Phần không xét và ngoại lệ

- Không xét lỗi heap/limit tại snapshot (`ELASTIC_MEMORY_SIZE=4g`, ES cap 4g; Node old-space 3072, cap 3g): đã biết và Engineer đang sửa thành 2g/2g cùng 2048/3g. QA không dùng commit sửa này để thay đổi kết luận về snapshot.
- Không chạy Docker, container, malware, feed, OTX, LLM hoặc lab; không đọc `.env`/secret.
- Không review lại logic product/core/extractor, 61 test, registry digest/architecture hay license ngoài 11 file đã giao.
- Không đánh giá khả năng connector chạy trong 256 MB; vẫn UNVERIFIED đến khi đo lab.
- Không cấp quyền merge, deploy hay thay đổi quyền truy cập.

## Tính bất biến của review

Lúc bắt đầu, checkout ở `e169aed…`; trong lúc review HEAD được tác nhân khác chuyển sang `13d91f7…` (commit heap đã biết). QA không checkout, reset, stage, commit hoặc sửa file trong repo. Mọi nhận xét `file:line` ở trên lấy bằng `git show e169aed:<path>`; báo cáo này chỉ áp dụng cho snapshot `e169aed479eedc9edec5eb5369c57fc776e66947`.
