# W03-S1 Frontend — F5/F6, giữ các sửa F1–F4

ROOT = `$WORKSPACE`.
Candidate sạch `13b8025274a70ec88dc21dd9ca7f51c68961e881`; cùng tree `ROOT/cti-w03-status-frontend`, thread `a7b74dcb-d309-4b2b-a34e-19b13d145482`. Một Sol medium trực tiếp, không worker/bot con, không reset. Allowlist S1 giữ nguyên; không redesign/đổi dependency/Backend/gateway/RUNS.

Đọc `ROOT/leader-w03-status-review-20261112/RECHECK.md`. Leader đã chạy7probe cũ PASS nhưng3probe mới FAIL, có wire lấy trực tiếp API Backend đã đạt. Không lặp điều tra cũ.

1. F5: sửa parser relation/display theo quyết định RECHECK: frontend bind technology_id+CVE ID, Backend xác thực khóa casefold. Snapshot display cũ khác hoa/thường phải đọc được khi version/dataset đổi; không dùng exact vendor/product equality, cũng không tự thêm Unicode casefold engine/field/dependency. review_required iff saved technology_record_version hoặc dataset_id khác hiện hành. Khi cả hai không đổi mà snapshot khác thì vẫn reject. Giữ strict IDs, tất cả bounds/cross-field/version/history và mutation200only. Dùng actual `casefold-api-wire.json` nguyên bản làm valid control cho status/history.
2. F6: registry pending cần cập nhật và thông báo subscriber hiện hành khi PUT cũ trả conflict hoặc known failure sau close/reopen/A→B→A. Conflict GET context mới, notice đúng, người dùng nhập lại; đúng1PUT, không replay. Không khôi phục stale callback trực tiếp sửa B để giải lock A. Unknown phải giữ behavior đã GREEN. Subscriber của provider khác không bị ảnh hưởng; không GET nhầm relation từ closure cũ.

Kiểm tối thiểu:
- Từ `ROOT/leader-w03-status-review-20261112`: `node_modules/.bin/vitest.cmd run --config vitest.recheck.config.ts --reporter=verbose` =>3/3 GREEN; config cũ `vitest.config.ts` =>7/7 vẫn GREEN. Giữ nguyên probe/config/setup/wire và hash theo `recheck-manifest.json`, không ghi đè RED.
- Regression source cho hai lỗi mới: status/history case-only rename; cùng IDs nhưng snapshot không đổi version/dataset phải reject; wrong IDs reject; close/reopen409 và knownfailure, A→B→A và provider khác. Focused affected tests + typecheck/lint/build/diff-check. Không full151 lặp nếu phần khác không đổi, nhưng giữ tests recovery/ownership liên quan.
- Commit sạch, báo delta từ13b80252, command/exit/count, hash probe không đổi. Output `ROOT/PHONG-HOA-W03-STATUS-FRONTEND-REWORK2-RESULT.md`, evidence `ROOT/w03-status-frontend-rework2-evidence/`, cập nhật report chính. Giữ toàn bộ evidence cũ.
- Không browser/feed/lab/push/PR/merge/deploy. Engineer chuẩn bị HTTP trên tree riêng; không đọc/ghép phần đang sửa của nhau. Chỉ Leader nghiệm thu và nối UI.
