# W03-S1 — chuẩn bị gateway/HTTP độc lập với Frontend

ROOT = `$WORKSPACE`.
CTI Engineer, một Sol medium trực tiếp, không worker/bot con. Mục tiêu hữu ích độc lập: API status/history qua gateway cục bộ, cùng SQLite với W04, có kiểm quyền/transaction/recovery; chưa ghép UI. Tái dùng nghiên cứu S1 và harness W03/W04 đã nghiệm thu, không nghiên cứu lại kiến trúc.

## Input/tree/phạm vi

- Backend đã được Leader nghiệm thu cục bộ tại `4f7100cf83e57b1cb30a12472ed71a0cd985a413` trong `ROOT/cti-w03-status-backend`; xem `ROOT/leader-w03-status-review-20261112/RECHECK.md`.
- Tạo `ROOT/cti-w03-status-integration`, branch `feat/w03-status-integration-20261112`, từ đúng Backend SHA. Giữ edits/owner nếu tree đã có, không reset. Không sửa source tree khác; một writer trên target.
- Frontend `13b80252` còn F5/F6, **chưa được cherry-pick**. Không viết UI/component/provider/test frontend trong prep này. Khi hai input đạt Leader sẽ giao ghép tiếp cùng tree/thread; không tự giao người khác.
- Đọc AGENTS.md, PROGRESS, `ROOT/PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md`, `docs/specs/W03-status-local-contract.md`, `tools/local_integration/README.md` đúng ref. Quyền làm local đã có, không xin duyệt lại đa file trong phạm vi.
- Allowlist chỉ `tools/local_integration/**`, `docs/PROGRESS.md`, `docs/specs/W03-status-local-contract.md` phần hướng dẫn tích hợp, output/evidence bên dưới. Không đổi portal_api/core/auth/frontend/deps/lockfile/RUNS. Nếu cần sửa product thì trả lỗi/repro/minimalfix, không tự nới.

## Thực hiện

1. Gateway allowlist chính xác status GET/PUT và status-history GET dưới `/api/cves/{cve_id}/technologies/{id}/...`; query giữ nguyên. Chặn method/path gần đúng, không mở proxy chung. Giữ GET `/api/cves` và các route cũ như trước. Giữ JWT server-side, loại client-supplied JWT, không lộ token/key trong URL/log/evidence. Body PUT status cap16KiB riêng (gateway mặc định8KiB không được vô tình siết contract); không đổi cap các luồng khác. API vẫn xử lý auth/Origin/media/JSON/body theo contract.
2. Runner opt-in S1 inject CveStatusStore cùng SQLite path W04/CveReadPort. Explicit bootstrap migration+seed ngoài request, dữ liệu synthetic có nhãn. Scenario cũ không bật status tự động. Đọc harness hiện có, giữ interpreter/cwd/PYTHONPATH đúng target.
3. Thêm fault hữu hạn cho status: response PUT bị thay503 **sau khi upstream đã commit**, và GET đối soát fail N lần hữu hạn rồi200. Chỉ fault đúng relation/route, không vô tình chặn W04/summary. Trace sanitized method/path/status và SQL snapshot, không lưu body chứa token. Chuẩn bị helper bounded nếu cần giai đoạn UI sau; không mở browser lượt này.
4. HTTP matrix qua socket gateway/API thật, không mock response thay cho backend mutation. Test valid control PUT JSON có escaped Unicode/whitespace khiến body >8KiB nhưng <=16KiB và hợp lệ; >16KiB413 không ghi. Fixture thiếu/hỏng phải preflight fail trước assertion, không skip thànhPASS.

## Acceptance mới (không lặp toàn lịch sử)

- IT/analyst/admin/mixed được GET/PUT/history; leader-only403 và không ghi; thiếuJWT401; clientJWT không nâng quyền. Origin/media/body/strict bool/fraction/duplicatekeys; no-store/Vary; route/method allowlist.
- Unset GET không tạo row; PUT200 tạo đúng statusv1+audit1; updatev2+audit2, history paging; stale status/context409 giữ SQL, replay request cũ không ghi. Kiểm first-write concurrency nếu harness bổ sung, không lặp whole backend377.
- W04 sửa software version/note/display bằng API thật => review_required; old expected409/no-write; human xác nhận trên currentcontext mới ghi. Case-only vendor/product rename giữ snapshot/history. Đổi identity/xóa-tạo lại không kế thừa. Dataset snapshot đổi (synthetic controlled) đúng409/review semantics. Historycursor cũ sau mutation409; bắt đầu lại200.
- Fault known-commit PUT200 → GET503→503→200 và unknown PUT503(aftercommit) → GET503→200: mỗi case đúng1PUT, đúng1status/1audit (seed baseline ghi rõ), retry chỉGET. Không dùng GET200 để khẳng định client đã biết PUT thành công; chứng cứ commit từ SQL/trace server.
- SQL snapshot schema/rows/versions/audits trước/sau GET và failures không đổi. Tách mutation W04/setup có chủ ý khỏi GET read-only. Lỗi schema/DB hỏng không tự migration/seed trong request.
- Targeted gateway/runner/new matrix, Ruff/format/diff-check, W03-R/W04 smoke cần thiết vì sửa harness. Không frontend typecheck/build/browser/fullsuite lúc chưa ghép UI.
- Cleanup mọi tài nguyên sở hữu: process/port/temp root; ghi evidence trước cleanup, command foreground bounded không sleep-loop/poll CI. Không chạy browser/VM/lab/live feed/OpenCTI/Cloudflare/JWKS/HTTPS thật.

## Bàn giao

Commit sạch, base/finalSHA/diff allowlist, command/exit/assertion counts, scenario/trace/SQL trước-sau, cleanup, manifest hashes. Output `ROOT/PHONG-HOA-W03-STATUS-INTEGRATION-PREP-RESULT.md`, `ROOT/w03-status-integration-prep-evidence/`. Không push/PR/merge/deploy hoặc đổi quyền. PASS chỉ prep HTTP cục bộ; UI/mobile/live/lab/production UNVERIFIED. Trả kết quả để Leader kiểm và giao nối UI đúng lúc.
