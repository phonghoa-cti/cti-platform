# Kết quả chuẩn bị demo F01

Ngày: 10/11/2026

## Kết luận

**PASS — hoàn tất chuẩn bị ngoại tuyến.** Gói `deploy/demo/` độc lập đã có cấu hình lõi, hai connector bật
riêng, 8 image ghim tag + digest, biến secret bắt buộc, fixture STIX 2.1 tổng hợp và hướng dẫn nghiệm thu.

**UNVERIFIED — chưa chạy lab.** Chưa pull image, boot service, kiểm health, nhập bundle, chạy MITRE, đo RAM/queue
hoặc kiểm chống trùng. Chưa có OTX chạy thật nên **chưa đạt #10**.

## Git và phạm vi

- Checkout: `$WORKSPACE\cti-platform-start`
- Nhánh: `feat/f01-demo-preparation-20261110`
- Base: `7775fee8c456f15dca3e7202b9265f29b0a5f103`
- Commit cấu hình: `d0cbe866753e7e2c1c533bf9439a5f03b6030b49`
- Commit fixture/tài liệu: `e169aed479eedc9edec5eb5369c57fc776e66947`
- Commit chừa dự phòng bộ nhớ: `13d91f7ce0497e4bc96b1af223088ef8b4d3301b`
- Commit xử lý QA-01–03: `9cf935cddcb9f84bd8045cbd62f228121041d1a6`
- Diff ròng: 13 file, 912 dòng thêm, 15 dòng xóa.

Không sửa logic sản phẩm, spec, CI hay deploy cũ. Không push, PR, merge hoặc deploy.

## Artifact

- `deploy/demo/compose.yml`: 6 service lõi; chỉ OpenCTI publish ở `127.0.0.1`.
- Elasticsearch: container 4 GiB, heap JVM mặc định/mẫu 2 GiB; OpenCTI: container 3 GiB,
  Node.js old-space 2048 MiB. Đây là cấu hình ứng viên chưa đo trên lab.
- `deploy/demo/compose.mitre.yml`: MITRE bật riêng, token riêng, giới hạn 256 MB.
- `deploy/demo/compose.import.yml`: ImportFileStix bật riêng, token riêng, giới hạn 256 MB.
- `deploy/demo/images.lock.json`: LTS `7.260811.0-lts.2`, 8 image và manifest `linux/amd64`.
- `deploy/demo/.env.example`: secret để trống và bắt buộc; không chứa secret thật.
- `deploy/demo/validate_compose_config.py`: nhận JSON render qua stdin, kiểm UUIDv4/Base64/tách token mà không
  in dữ liệu đầu vào; core không yêu cầu connector.
- `deploy/demo/fixtures/demo-bundle.json`: 7 object, 1 relationship, dữ liệu tổng hợp dùng `.example` và TEST-NET-2.
- `deploy/demo/README.md`: trình tự review → lõi → MITRE → nhập mẫu → đo → OTX ở lượt sau.

## Kiểm chứng đã chạy

| Kiểm tra | Kết quả | Exit |
|---|---:|---:|
| Compose standalone v5.7.0, checksum khớp | PASS | 0 |
| Thiếu secret bắt buộc | Từ chối đúng kỳ vọng | 1 |
| Compose lõi / MITRE / ImportFileStix `config --quiet` | PASS cả 3 | 0 |
| Render bộ nhớ: Elasticsearch 4 GiB/heap 2 GiB; OpenCTI 3 GiB/old-space 2048 MiB | PASS cấu hình | 0 |
| Preflight JSON lõi / MITRE / ImportFileStix | PASS: 6+0 / 6+1 / 6+1 service+connector | 0 |
| Test preflight dương/âm và không lộ sentinel | 13 passed | 0 |
| Ruff check / format cho script và test mới | PASS; 2 file formatted | 0 / 0 |
| Policy render: 8/8 image khớp lock, không `latest`, chỉ loopback | PASS | 0 |
| STIX 2.1 strict + refs | Valid | 0 |
| Negative pattern hỏng | Bị từ chối | 2 |
| Negative relationship ref hỏng | Bị từ chối | 2 |
| Link tương đối | 0 link hỏng | 0 |
| `git diff --check` | PASS | 0 |
| `pytest -ra` | 61 passed | 0 |
| Ruff check / format check | PASS; 70 file formatted | 0 / 0 |

Fixture SHA-256: `aa2cdb91575d2cf8b56a16ac48e1b1d7147a5512698b6c1ffc525ea937336195`.

## Xử lý review QA

- **QA-01:** tài liệu nêu admin token UUIDv4, encryption key Base64 giải mã tối thiểu 32 byte, connector ID
  UUIDv4 riêng và API token do OpenCTI cấp, không ép UUID. Preflight từ chối dữ liệu sai mà không in input.
- **QA-02:** giữ mặc định `app.validation_mode="draft"` tại ref OpenCTI đã chọn. Quy trình ghi upload → chạy
  ImportFileStix thủ công khi `AUTO=false` → chờ work → analyst review/phê duyệt bản nháp → kiểm knowledge base;
  ghi người duyệt, work ID và trạng thái trước/sau, không bypass.
- **QA-03:** tiêu chí provenance khớp fixture/STIX: marking ở object hỗ trợ; `created_by_ref` ở
  indicator/relationship/report; external reference ở report; IPv4/domain truy nguyên qua report và relationship.

Đây là xử lý cấu hình/tài liệu ngoại tuyến, không phải bằng chứng boot, import hoặc quyền UI thực tế.

## Nguồn/version đã ghi

- OpenCTI commit `957087377304ea548fcd9f83a4ee2b025c855d9b`.
- Connectors commit `d50686be6f64eb2e91ac38b23c45d0460a210435`.
- Cấu trúc Compose upstream commit `60285adb360e3823a334333ae4744255d8ac1821`; chỉ dùng làm nguồn cấu trúc.
- License/reference của từng image nằm trong `images.lock.json`; RabbitMQ config ghi ref và SHA ngay trong file.

## Bằng chứng

Thư mục: `$WORKSPACE\demo-evidence`

- `01-compose-tool.txt`
- `02-registry-manifests.txt`
- `03-compose-validation.txt`
- `04-stix-validation.txt`
- `05-final-checks.txt`
- `06-memory-headroom-validation.txt`
- `07-preflight-and-workflow-validation.txt`

## Giới hạn và bước lab còn lại

1. Xác minh host `linux/amd64`, tài nguyên, `vm.max_map_count` và secret thật bằng kênh an toàn.
2. Pull/boot lõi, kiểm health và đo RSS/CPU/RAM/queue; heap/old-space ứng viên và giới hạn 256 MB cho connector
   đều còn **UNVERIFIED**.
3. Tạo tài khoản/token connector riêng; chạy MITRE rồi ImportFileStix; kiểm provenance/TLP/relationship và nhập lặp.
4. Xác minh capability Upload knowledge files, quyền review/approve đúng mode, work ID và trạng thái draft
   trước/sau trên lab; preflight không chứng minh entropy, quyền hoặc token sử dụng được.
5. Chỉ sau khi có quyền/key và điều khoản phù hợp mới chạy OTX. #10 cần MITRE + OTX quan sát được trên lab.

Hoàn tác phần chuẩn bị bằng revert bốn commit trên; không xóa volume lab nếu chưa có phê duyệt và bản sao lưu.
