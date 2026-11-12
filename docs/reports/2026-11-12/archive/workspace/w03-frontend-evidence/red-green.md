# W03 frontend — RED → GREEN

1. RED contract đầu: `npm test -- --run tests/cves-http.test.ts tests/cve-app.test.tsx` exit 1; Vite không resolve được hai module W03 chưa tồn tại. Đây là failure dự kiến trước production code.
2. GREEN contract: cùng lệnh exit 0, ban đầu 35/35; sau bổ sung fixture, empty/stale technology và accessibility đạt 39/39.
3. RED regression priority: `npm test -- --run tests/cves-http.test.ts` exit 1, nhận `[1,4,7,10]` thay vì `[1,2,3,4]` sau filter fixture.
4. GREEN regression priority: cùng file exit 0, 26/26 sau khi đánh lại priority liên tục trong tập sample đã filter.
5. RED accessibility: test detail focus exit 1 vì focus còn ở nút dòng.
6. GREEN accessibility: test mục tiêu exit 0 sau khi chuyển focus vào detail và trả focus về nút dòng khi đóng.

Các test kiểm strict detail/summary schema, null khác score 0, HTTPS advisory, GET-only/no-store, cap 1 MiB, error mapping, filter/paging/detail, React escaping, 409 reset, stale provider/load/options/unmount và không có mutation/status UI.
