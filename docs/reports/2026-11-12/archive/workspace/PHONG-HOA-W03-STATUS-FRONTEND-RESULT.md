# W03-S1 Frontend — kết quả triển khai

## Kết quả

PASS cục bộ cho phạm vi Frontend W03-S1 sau rework F1–F6. Commit sạch `2448b8600f9eff2c3e42b6742e220b46980f4ff4` trên branch `feat/w03-status-frontend-20261112`, base/merge-base đúng `7ff6eb3af21d8de65836bfbf707396ae5690de0b`.

- Thêm parser/provider HTTP status riêng, strict wire và response cap 1 MiB; GET/PUT/history dùng same-origin, không tự chèn JWT/actor/role/Origin và không retry PUT.
- Thêm `CveStatusPanel` trong chi tiết một CVE/công nghệ: status, note bắt buộc, context/version, review-required, history phân trang explicit.
- Summary không render/call status; route mẫu dùng memory provider tổng hợp, không HTTP mutation.
- Chặn double-submit và giữ pending/unknown theo provider+relation qua đóng/mở; known commit và unknown outcome chỉ GET đối soát, 409 tải context mới và bắt nhập lại, không replay/merge PUT.
- Note được React render dạng text; panel có loading/error/empty, focus/keyboard tự nhiên và CSS responsive theo token SOC console hiện có.

## RED → GREEN

1. Parser/provider RED: import `@/data/cve-status` không tồn tại; GREEN: 15 test rồi mở rộng thành 19 test parser/provider.
2. Panel RED: import `@/components/cve-status-panel` không tồn tại; GREEN: 7 test component.
3. Integration RED: không có nút `Mở trạng thái Fortinet FortiOS`; GREEN: hồi quy `cve-app` đạt.
4. Recovery RED bổ sung: note control vẫn phát fetch, pending bị mất khi đóng/mở, PUT 503 bị phân loại sai và conflict giữ pending; GREEN bằng validator trước fetch, registry theo provider+relation và mapping mutation riêng.

## Kiểm chứng cuối

Chạy tại `portal/web`:

| Lệnh | Exit | Kết quả |
|---|---:|---|
| Leader probe nguyên bản | 0 | 1 file, 7/7 pass; probe hash không đổi |
| Leader recheck probe nguyên bản | 0 | 1 file, 3/3 pass; probe/wire hash không đổi |
| `npm test -- --run tests/cve-status.test.ts tests/cve-status-panel.test.tsx tests/cve-app.test.tsx tests/cves-http.test.ts tests/technologies-http.test.ts tests/technology-panel.test.tsx` | 0 | 6 file, 151/151 test pass |
| `npm run typecheck` | 0 | không lỗi TypeScript |
| `npm run lint` | 0 | không lỗi/cảnh báo ESLint |
| `npm run build` | 0 | Next.js build thành công, 11/11 trang tĩnh |
| `git diff --check 7ff6eb3..HEAD` | 0 | sạch whitespace |
| allowlist check | 0 | 15 file đổi, 0 file ngoài allowlist |
| `git status --porcelain=v1` | 0 | không có output, tree sạch |

Diff: 15 file, `+953/-6`. Rework2 từ candidate `13b80252` đúng 4 file allowlist, `+69/-13`. Không đổi dependency, backend, ledger, route W03-R, CVE DTO/list/ranking/filter.

## Giới hạn

Đây là bằng chứng unit/component/build cục bộ với fixture tổng hợp do Frontend tự tạo. Chưa kiểm browser thật, chưa nối Backend/API/gateway chung, chưa chứng minh auth/Origin runtime, SQLite, lab, mobile thiết bị thật hoặc production. Không push/PR/merge/deploy.
