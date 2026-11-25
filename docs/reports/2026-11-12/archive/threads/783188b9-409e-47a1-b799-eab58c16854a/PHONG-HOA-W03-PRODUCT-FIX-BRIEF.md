# W03 product256 — Backend local

Một CTI Backend Sol medium trực tiếp, không worker con. Đọc AGENTS, docs/PROGRESS và W03-read/W03-status/W04-technology contracts đúng ref. Nghiên cứu và quyết định tại $THREADS\783188b9-409e-47a1-b799-eab58c16854a\PHONG-HOA-W03-PRODUCT-LIMIT-REVIEW-RESULT.md và PHONG-HOA-W03-NEXT-DECISION.md cùng thư mục.

Base=d09929311b4b6447aac8b2ec6adac5999beda25d. Tạo tree riêng $WORKSPACE\cti-w03-product-boundary, branch fix/w03-product-boundary-20261112 từ object có sẵn ở cti-w03-status-integration; không sửa tree nguồn đang có Engineer. Nếu tree/branch đã tồn tại kiểm ownership và báo thay vì reset.

Allowlist: portal_api/cves.py, portal_api/tests/test_cves_api.py, portal_api/tests/test_cves_status_api.py, docs/specs/W03-read-local-contract.md, docs/PROGRESS.md. Chỉ nâng affected product128→256; vendor128 và mọi policy/cap/auth/audit/rank/pagination giữ nguyên. Không sửa Cf/trim/UI/harness hoặc tự mở rộng allowlist.

Test đỏ→xanh qua API cho product128/129/256 hợp lệ,257 fail-closed; vendor128/129 giữ đúng; Unicode astral đếm code point, controls vẫn bị chặn. Chứng minh relation GET/PUT/history với product256 và một audit, dataset257 không ghi. Chạy hai module pytest liên quan và Ruff/diff cần thiết; không full suite/build/browser. Đọc các test cap/cursor hiện có, chỉ chạy thêm phần liên quan thay đổi; không viết lại tất cả policy.

Commit local sạch; report đầy đủ SHA/diff/lệnh/interpreter/exit/count/red-green tại $THREADS\783188b9-409e-47a1-b799-eab58c16854a\PHONG-HOA-W03-PRODUCT-FIX-RESULT.md và evidence riêng w03-product-fix-evidence. Không sửa RUNS, push/PR/merge/deploy, deps, lab, cloud/feed/LLM thật, secret, quyền/chi tiền. Không nhận toàn integration đạt: capture hiện cố tình kỳ vọng256→503 sẽ được Engineer sửa sau khi đầu vào này đạt review.
