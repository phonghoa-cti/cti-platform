# W03-STATUS-FRONTEND-QA — PASS cục bộ

Ngày kiểm: 12/11/2026. Kết luận: **PASS cục bộ** cho candidate Frontend `2448b8600f9eff2c3e42b6742e220b46980f4ff4`; không phát hiện finding mới trong phạm vi F5/F6 và bảy probe hồi quy. Đây chưa phải nghiệm thu browser, tích hợp gateway/Backend, lab hoặc production.

## Ref, delta và bất biến target

- Target: `cti-w03-status-frontend`; HEAD đầu và cuối đều là `2448b8600f9eff2c3e42b6742e220b46980f4ff4`; `git status --porcelain=v1` đầu/cuối đều rỗng.
- Base rework2: `13b8025274a70ec88dc21dd9ca7f51c68961e881`; base chức năng: `7ff6eb3af21d8de65836bfbf707396ae5690de0b`.
- Delta đúng bốn file cho phép, `+69/-13`: `portal/web/components/cve-status-panel.tsx`, `portal/web/data/cve-status-http.ts`, `portal/web/tests/cve-status-panel.test.tsx`, `portal/web/tests/cve-status.test.ts`.
- `git diff --check 13b80252..HEAD`: exit `0`.
- Không sửa target, Backend accepted, tree Engineer, `PHONG-HOA-RUNS.json`, probe/evidence cũ hoặc báo cáo cũ. Chỉ tạo báo cáo và evidence dưới thư mục OUT được giao.

## Probe độc lập mới

| Kiểm | Lệnh từ `leader-w03-status-review-20261112` | Exit | Kết quả |
|---|---|---:|---:|
| F5/F6 | `.\node_modules\.bin\vitest.cmd run --config vitest.recheck.config.ts --reporter=verbose` | 0 | 3/3 PASS |
| Hồi quy cũ | `.\node_modules\.bin\vitest.cmd run --config vitest.config.ts --reporter=verbose` | 0 | 7/7 PASS |

Hai lượt chỉ có cảnh báo Vite config-loader/oxc-esbuild đã có, không làm test fail. Log đầy đủ theo test name, command, cwd, exit và count nằm trong `w03-status-frontend-qa-evidence/qa-probe-3.log` và `qa-probe-7.log`.

## Hash và provenance

- `casefold-api-wire.json`: `c76c5429d80a5eb0ea8cd9faf47f75c96321939c843142d948684c6770b92d32`, khớp manifest và không đổi trước/sau.
- `frontend-recheck.test.tsx`: `37b47a4d457949d76995d9c5436839b5f5a37ebb58152d8486a941ca6231d879`; `vitest.recheck.config.ts`: `ce62d7bc3d927e6781af7ef62d63cb000c0c421a568a3701e4d499a9febfbdf6`.
- `frontend-probes.test.tsx`: `a5169c29a4b2ecef2da289482008f29a511119c2133908e38380ebbac8d60368`; `vitest.config.ts`: `8105331b8cf3374759cdbf0bd3e7b40df32ec69cde4b4558bf84c468ae7577f5`.
- Cả 9/9 mục trong `leader-w03-status-review-20261112/recheck-manifest.json` khớp SHA-256 ghi sẵn. Bảng trước/sau và hash bốn source nằm trong `w03-status-frontend-qa-evidence/hashes.json`.

## Đánh giá theo tiêu chí

1. **PASS — F5 snapshot/relation.** `portal/web/data/cve-status-http.ts:59-67` bind relation bằng `technologyId+cveId`; snapshot display/software chỉ được khác khi `technologyRecordVersion` hoặc `datasetId` khác. `portal/web/data/cve-status-http.ts:76-82` tính `review_required` đúng khi và chỉ khi version/dataset khác. Wrong relation vẫn bị từ chối ở parser và HTTP binding (`:68-69`, `:158-169`). Probe API wire thật cho status/history case-only đều PASS; test source tại `portal/web/tests/cve-status.test.ts:74-87` phủ wrong ID, snapshot cũ hợp lệ và display drift khi snapshot không đổi.
2. **PASS — F6 registry subscriber.** Registry tách theo object provider bằng `WeakMap` và theo relation key (`portal/web/components/cve-status-panel.tsx:14-31`). Conflict/known failure xóa lock rồi thông báo subscriber hiện hành đúng provider+relation (`:30-31`, `:72-82`, `:104-113`); callback chỉ sửa UI khi owner hiện tại còn khớp (`:50-58`, `:73`). Close/reopen conflict probe PASS, giữ đúng một PUT và GET lại context để nhập lại.
3. **PASS — A→B→A và provider khác qua review source/test.** Test source `portal/web/tests/cve-status-panel.test.tsx:109-130` phủ known failure sau A→B→A; `:186-203` phủ conflict/unknown/unavailable từ provider cũ không làm sai provider mới. Cơ chế provider+relation key không phát broadcast sang B/provider khác. Không cần thêm probe ngoài brief vì code path và regression đã có trực tiếp.
4. **PASS — pending/unknown, không replay PUT.** Submit bị khóa khi `saving|pending|unknown` (`portal/web/components/cve-status-panel.tsx:92-95`, `:130-153`). Unknown chỉ được giải sau GET thành công (`:54-66`); không có nhánh tự gọi lại `save`. Probe cũ xác nhận unknown+GET lỗi vẫn khóa và callback cũ không ghi đè relation mới.
5. **PASS — dữ liệu không tin cậy trong phạm vi parser/UI.** Parser giữ object/key/schema/bounds/timestamp strict (`portal/web/data/cve-status-http.ts:14-56`, `:76-107`), nội dung note hiển thị bằng React text node (`portal/web/components/cve-status-panel.tsx:149`, `:160`), không có sink HTML mới trong delta.

## Findings và giới hạn

- Findings mới: **không có** trong phạm vi kiểm này.
- **UNVERIFIED:** browser thật; Frontend ghép gateway/Backend accepted; HTTP runtime cùng DB; mobile; feed/OpenCTI; Cloudflare/JWKS/HTTPS; lab; production; dữ liệu thật.
- Không lặp full suite, typecheck, lint hoặc build theo brief vì 3+7 probe và review delta không tạo nghi vấn mới. Các kết quả 97/97, typecheck/lint/build trong evidence ứng viên chỉ là bằng chứng worker trước đó, không được trình bày như lượt QA này tự chạy.

## Học thêm

- **Snapshot** là ảnh chụp dữ liệu tại một phiên bản; snapshot cũ chỉ hợp lệ khi hệ thống đánh dấu cần người xem lại.
- **Subscriber** là phần giao diện đăng ký nhận thay đổi trạng thái dùng chung; phải ràng buộc đúng provider và quan hệ để callback cũ không làm sai màn hình mới.
- **Unknown outcome** là trường hợp chưa biết mutation đã ghi hay chưa; an toàn nhất là chỉ GET đối soát và không tự phát lại PUT.
