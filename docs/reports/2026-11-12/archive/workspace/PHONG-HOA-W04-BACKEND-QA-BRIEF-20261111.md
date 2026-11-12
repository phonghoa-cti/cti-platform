# W04 — kiểm độc lập Backend trước tích hợp

Task `W04-ASSETS-BACKEND-QA`, CTI QA Security / Sol medium trực tiếp, không giao tiếp worker khác.
Root `$WORKSPACE`.

## Mục tiêu và nguồn

Kiểm độc lập phần mới W04 auth/CRUD/audit/snapshot, xác định lỗi cụ thể trước khi Leader nghiệm thu. Frontend đang chạy trên tree riêng, không chờ hoặc chạm tree đó.

- Target chỉ đọc `cti-w04-assets-local`, branch `feat/w04-assets-local-20261111`, base `aeff542a20ecc6fe436a0884801fdd69ab0435f6`, HEAD phải là `bfd3272d968313ed8b6d9c46ef07c730b49c2ebb`, 8 file +1000/-21, tree sạch.
- Yêu cầu chính `PHONG-HOA-W04-IMPLEMENT-BRIEF-20261111.md`; nghiên cứu tham chiếu `PHONG-HOA-W04-ASSETS-RESEARCH-20261111.md`; contract trong target `docs/specs/W04-assets-local-contract.md`. Hiệu chỉnh Leader ưu tiên hơn nghiên cứu.
- Báo cáo worker `PHONG-HOA-W04-ASSETS-RESULT.md`, raw `w04-assets-evidence/`. Full197 tests là trên mốc trước sửa ID error; cuối HEAD có targeted26. Không gọi full suite đó là run mới trên HEAD.
- Leader intake `leader-w04-backend-intake-20261111.json`: HEAD/clean/module-path và3 schema fixtures+1error đã kiểm mới exit0. Không cần lặp fixture-schema chỉ để xác nhận lại; không đồng nghĩa runtime fixture đã xuất đúng hoặc auth/audit an toàn.

## Phạm vi kiểm tập trung

1. Đọc diff source/test đúng SHA; auth/role trước query/body/DB, Origin và streamed body cap, error/header nhất quán, strict id/version (bool/float/large/duplicate query), không mở quyền bằng role/header giả. Kiểm cả exception ngoài happy path.
2. Mỗi mutation+audit atomic, duplicate/optimistic version và concurrent writer đúng; failure rollback cả asset/audit; sửa/xóa chỉ bỏ rule asset, default rule vẫn hiệu lực; audit không thể sửa qua API.
3. Snapshot đọc assets và rules cùng trạng thái, overflow/malformed stored data không cho kết quả partial/allowlist rộng sai. Kiểm canonical domain/IDN/dot/ranh giới và IPv4/IPv6 CIDR; URL path/query vẫn match asset nhưng không được tự allowlist; private IP W02 vẫn theo chính sách cũ.
4. W02 khi opt-in tắt giữ hành vi; khi bật hợp lệ ở allowlisted/not_found/found, score/asset visible nhất quán, hidden-TLP record/fact không bị lộ qua hợp nhất assets. Giới hạn253 chỉ cho asset name; lỗi snapshot là lookup_unavailable. Một tổ chức/demo tổng hợp, không chứng nhận multi-tenant hay production.
5. Tái chạy một lần nhóm cần thiết `portal_api/tests/test_assets_api.py` trên HEAD, rồi chỉ bổ sung probe cho rủi ro thực sự còn thiếu từ review. Không lặp full197, build/frontend hoặc browser. Retain probes và raw log dù phát hiện lỗi. Không đếm đọc code như chạy test.

## Cách chạy và ranh giới ghi

Không sửa/commit target, Backend source, Frontend, RUNS/plan. Chỉ ghi root `PHONG-HOA-W04-BACKEND-QA-RESULT.md` và `w04-assets-qa-evidence/`; DB/probe tạm nằm dưới evidence riêng. Dùng interpreter cụ thể `cti-w02-lookup-api/.venv/Scripts/python.exe`, cwd target, PYTHONPATH target root/core/extractor, `-B` và pytest `-p no:cacheprovider -o addopts='' -q` để log có count và không ghi cache target. Xác nhận executable/module source. Không cài packages, secret/network/browser/lab/push/PR/merge/deploy; không làm pentest ngoài phạm vi in-process synthetic.

Nếu có lỗi: báo severity, file:line, điều kiện tái hiện, expected/actual, lệnh/exit/output và đề xuất sửa nhỏ nhất; không tự sửa. Không giữ độc quyền target sau khi báo xong. Kết luận PASS/FAIL/UNVERIFIED từng nhóm, số test/lệnh/exit, SHA/clean trước-sau, hashes artifact. Nếu đạt, trả rõ đủ/thiếu điều kiện nối Frontend; không gọi W04 toàn luồng hoàn thành.
