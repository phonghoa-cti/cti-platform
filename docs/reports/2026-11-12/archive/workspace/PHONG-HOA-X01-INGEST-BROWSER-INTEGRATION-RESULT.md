# X01 ingest → browser → STIX — kết quả tích hợp cục bộ

Ngày: 11/11/2026
Nhánh: `feat/x01-ingest-browser-integration-20261111`
Commit: `4655d9aef1b5a6fe2f26d256e4ceb1f1d6ae15cc`
Base rework: `5fd527fc5d9b113ac2725a855f3ac75c9b106762`

## Kết luận

PASS phần R1 còn thiếu. Gateway demo giữ nguyên mode lỗi kéo dài và thêm mode lỗi đúng hai GET sau POST
thành công đầu tiên. Hai Browser run mới đều quan sát hai GET 503, bấm tải lại đúng một lần rồi nhận GET 200
trên cùng port/DB/draft. UI giữ đúng lựa chọn hoặc quyết định đã ghi; verifier đối chiếu audit, provenance,
hash STIX và export read-only. Không có POST replay trong khoảng retry.

Kết quả lịch sử TXT/PDF, duplicate importer, tự duyệt 403 và hai mode lỗi kéo dài nằm tại
`x01-ingest-browser-integration-evidence/RESULT.md`. Evidence R1 mới nằm tại
`x01-ingest-browser-integration-evidence/rework-recovery/`.

## Hai Browser run phục hồi

### Save → 503 → retry → approve

- URL/run: `http://127.0.0.1:60874`, draft `1`, TTL `300` giây.
- Bỏ IOC `0`, lưu; Browser ghi nhận `GET /api/v1/drafts/1 = 503` và
  `GET /api/v1/drafts = 503`.
- UI lỗi vẫn hiện đúng một IOC đã lưu: chỉ IOC `1` (`evil-two.example`).
- Bấm tải lại một lần: cả detail/list trả 200; lỗi biến mất, nút duyệt được mở lại.
- Duyệt thành công; queue về `0`, selected indices `[1]`.
- Request count: `GET=8`, `POST=2`; `selection POST=1`, `decision POST=1`.
- Audit: selection `1`, decision `1`; STIX `object_count=4`, bundle SHA-256
  `21d78d76c01fcc88a4cc4e5ba5e1f933b515cb1d51d15909902c31f6c4b45b35`.
- Exit `0`.

### Decision → 503 → retry

- URL/run: `http://127.0.0.1:51447`, draft `1`, TTL `300` giây.
- UI khởi đầu bằng selection đã seed `[1]`; duyệt một lần.
- Browser ghi nhận `GET /api/v1/drafts/1 = 503` và `GET /api/v1/drafts = 503`.
- Bấm tải lại một lần: cả detail/list trả 200; queue về `0`, trạng thái vẫn `Đã duyệt`.
- Browser tự khởi động lại trong chính thao tác retry; server run/port/DB/draft không đổi và trace của run vẫn
  ghi liên tục POST → hai GET 503 → hai GET 200. Ảnh sau restart xác nhận queue `0` và trạng thái `Đã duyệt`.
- Request count: `GET=6`, `POST=1`; `selection POST=0`, `decision POST=1`.
- Audit: selection `1`, decision `1`; STIX `object_count=4`, bundle SHA-256
  `049a416e8b7a09753d2eb1fb63d93fdac7f35e207090150b9807a3923aba4d93`.
- Exit `0`.

Request trace chỉ ghi `method`, pathname và status; test gateway dùng secret giả trong query/header/body và chứng
minh các giá trị đó không xuất hiện trong trace.

## RED → GREEN và hậu kiểm

- RED gateway: `10 passed, 1 failed`, exit `1`; GET đầu tiên quan sát 200 thay vì 503 vì counter chưa tồn tại.
- RED Python: collection exit `2`; verifier request trace chưa tồn tại.
- GREEN hẹp: gateway `11/11`, Python recovery/plan `11 passed`, đều exit `0`.
- Fresh final: gateway `11/11`; `test_runner.py` `55 passed`; Ruff check `0`; Ruff format check `0`;
  `git diff --check` `0`.
- Không chạy lại full 561, W02 hoặc web build vì không đổi UI/API/store/importer/exporter.

## Cleanup

- Hai browser harness exit `0`; cleanup failure của `LocalRun` sẽ đổi exit thành `1`.
- Listener postcheck chính xác trên port `60874` và `51447`: `0`.
- Process `node.exe`/`python.exe` thuộc target và command gateway/harness: `0`.
- Junction tạm `portal/web/node_modules` và `portal/web/.next`: đã đối chiếu đúng reuse target trước khi gỡ;
  postcheck đều `exists=false`.
- Target Git sạch sau commit.

## Diff và evidence

- Commit: `4655d9aef1b5a6fe2f26d256e4ceb1f1d6ae15cc`.
- Diff: 6 file, `+312/-10`, đúng allowlist:
  `docs/PROGRESS.md`, gateway, runner, harness browser, test gateway, test runner.
- Evidence R1: 10 file được manifest kiểm size/hash; manifest SHA-256
  `ce4fd78790c84a30459bcb1bcf1ff1c9a9d17522bdc08fc43431ae5779585d12`.
- Ảnh gồm hai trạng thái 503, selection phục hồi, save đã duyệt và decision phục hồi.

## Giới hạn

UNVERIFIED: Cloudflare/JWKS/HTTPS thật, OpenCTI, dữ liệu báo cáo thật/model, lab, production và clipboard.
Không push, PR, merge, deploy, cloud, model hoặc lab trong lượt này.
