# X01 → W05 → STIX E2E — kết quả triển khai

Ngày 11/11/2026. **PASS local CLI + HTTP** cho một fixture synthetic UTF-8/Unicode đi qua extractor CLI →
store CLI → gateway/API v1 selection `[1]` + approve → STIX CLI trên cùng draft/DB trước cleanup.

## Git và phạm vi

- Worktree: `cti-x01-w05-stix-e2e`.
- Branch: `feat/x01-w05-stix-e2e-20261111`.
- Exact base: `ed829a0344b2d3d4392fae933e41a9c44fdcd853`.
- HEAD: `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.
- Diff base→HEAD: 7 file, `+588/-1`; đúng file scope đã khóa.
- Source readonly `cti-w05-stix-offline` vẫn branch `feat/w05-stix-offline-20261111`, đúng base và sạch.
- Implementation tree sạch sau commit. Không push/PR/merge/deploy.

Sáu commit cục bộ:

1. `1a93533` — `feat(extractor): accept draft creator in store CLI`
2. `1a90662` — `test(integration): seed STIX flow through CLIs`
3. `93ace83` — `test(integration): verify CLI HTTP STIX flow`
4. `d873364` — `docs(integration): document offline STIX E2E`
5. `71b8309` — `test(integration): report export window hashes`
6. `cf9e609` — `docs(integration): remove trailing blank line`

## Đã triển khai

- `store.py save` có optional `--created-by-subject`, giữ stdout và caller không truyền option; core hiện có xử lý
  validation. Metadata này không được coi là danh tính đã xác thực.
- Scenario `stix-e2e` tạo exact UTF-8 LF/no-BOM input, gọi hai seed CLI bằng argv list, `shell=False`, timeout
  10 giây và parse chặt stdout store; child error/timeout/malformed output fail closed, cleanup temp owned.
- Ma trận 120 giây dùng HTTP gateway/API v1 thật để bỏ một IOC, lưu selection và approve; exporter CLI chạy
  sau review trên cùng DB. Pending fail closed; successful export chỉ chứa selected subset; provenance nối đúng
  source hash/final audit/selection; output identical idempotent và existing different không bị ghi đè.
- DB/sidecar được hash theo hai cửa sổ export riêng: pending và approved. Hash trước/sau từng cửa sổ bằng nhau;
  không so vượt qua selection/approve vì đó là thay đổi DB hợp lệ.
- PASS chỉ được in sau khi gateway process, API thread và listener owned đã dừng, temp root đã xóa.

## TDD và kiểm chứng cuối

| Cổng | Kết quả mới trên HEAD | Exit |
|---|---:|---:|
| Targeted store CLI + runner + STIX CLI | 54 passed | 0 |
| Ma trận CLI→HTTP→STIX | 59 checks | 0 |
| Selection matrix regression | 113 checks / 10 scenarios | 0 |
| Ruff check | All checks passed | 0 |
| Ruff format check | 5 files already formatted | 0 |
| `git diff --check` | sạch | 0 |

TDD quan sát: Task 1 RED 3 ca vì option chưa có rồi GREEN 28; Task 2 RED 4 ca vì scenario chưa có rồi GREEN.
Task 3 là executable acceptance matrix được thêm sau Task 2 nên lần chạy đầy đủ đầu tiên PASS; không bịa một RED
riêng cho script. Lượt pre-final đầu bị giữ là FAIL tổng vì Ruff exit 1 dù test xanh; sau sửa cơ học, toàn bộ cổng
trên được chạy lại và cùng exit 0. Self-review tiếp đó bắt được một dòng trắng cuối file qua
`git diff --check base..HEAD`; đã sửa tại `cf9e609` và chạy lại toàn bộ cổng. Không chạy full 500, UI build hoặc
browser vì ngoài phạm vi thay đổi.

## Hash và evidence

- Source SHA-256: `E73038E5D68D0AEE0757BF72CD8A404B3F55A94EF9D6C519F5E0C3FB1292A655`.
- Bundle SHA-256 của run cuối: `E25B57E6B8440C3940823F398F1A4587C311968EBF70210AFAB9C5387C8F9D8E`.
- Evidence: `x01-w05-stix-e2e-evidence`.
- Manifest: `x01-w05-stix-e2e-evidence/SHA256SUMS.txt`.
- Manifest SHA-256: `F929A674A9D0B184EE5DC214102A9B239696AE9C34414FBEAE6596B45808E0C3`.
- Manifest đã kiểm độc lập: 7/7 entry khớp, 0 sai.

Evidence không chứa raw source/draft/DB/bundle/JWT/private key/subject. Command nội bộ có creator synthetic được
ghi bằng nhãn `<REDACTED_SYNTHETIC_SUBJECT>`.

## Giới hạn

PASS này chỉ chứng minh **local CLI + HTTP gateway/API + SQLite + STIX file** trên fixture synthetic. Chưa chứng
minh browser cùng draft, OpenCTI import/workbench, reviewer-to-Identity thật, Cloudflare/JWKS/HTTPS thật, chất
lượng/metrics X01 C2–C4, dữ liệu thật, network share/crash, lab, deploy hoặc production. Nghiên cứu và validator
không phải bằng chứng đã ingest OpenCTI.

## Hoàn tác

Trên branch này, hoàn tác bằng `git revert --no-commit ed829a0344b2d3d4392fae933e41a9c44fdcd853..cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`
rồi review và commit revert; không dùng `reset --hard` và không xóa evidence cũ.

## Học thêm

- **Cửa sổ bất biến:** chỉ so hash trong khoảng không có write hợp lệ, tránh báo giả rằng selection/approve làm hỏng DB.
- **Fail closed:** output hoặc trạng thái không chắc chắn bị từ chối thay vì đoán và tiếp tục export.
- **Owned cleanup:** mỗi run chỉ dừng/xóa process, listener và temp do chính nó tạo.
