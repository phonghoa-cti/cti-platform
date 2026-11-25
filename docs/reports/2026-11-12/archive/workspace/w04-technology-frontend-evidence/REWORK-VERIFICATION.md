# Evidence rework F1–F3 W04 Technology Frontend

- Base rework: `2419b29656092edcf2bb20b0d7c62a12fa0774c0`.
- HEAD/commit: `cfb612f05f6ae57952362580e35ad59d2aff0a3f`.
- Probe/fixture giữ nguyên; SHA256 đã đối chiếu lần lượt `218118d0f58a523e25e60eba1734da7ed9a1e008ddf93d196cbd31cd9be19a45` và `b0f87acdac467348c5dd2f66447a04923914dde7daeba08752e499dcd2198b78`.

## RED → GREEN

- Probe Leader trên base: exit `1`, **0/4 pass, 4/4 fail** (hai ca list 1.000 DTO, committed notice qua GET retry và unknown lock qua tab).
- F1 regression sau khi thêm test, trước implementation: exit `1`, **35 pass, 3 fail**.
- F2/F3 regression chọn lọc sau khi thêm test, trước implementation: exit `1`, **2 pass, 4 fail, 18 skipped**.
- GREEN cuối: probe Leader exit `0`, **4/4 pass**; focused technology+assets exit `0`, **120/120 pass**.
- Lint trung gian phát hiện ba lỗi `react-hooks/refs` do đồng bộ ref trong render; chuyển sang effect, sau đó lint exit `0`, focused/probe vẫn giữ nguyên GREEN.

## Cổng cuối

| Evidence raw | Exit | Kết quả |
|---|---:|---|
| `rework-probe-green.log` | 0 | 1/1 file, 4/4 probe pass. |
| `rework-focused.log` | 0 | 6/6 file, 120/120 test pass. |
| `rework-typecheck.log` | 0 | Không lỗi TypeScript. |
| `rework-lint.log` | 0 | Không lỗi/cảnh báo ESLint. |
| `rework-build.log` | 0 | Build production thành công, 9/9 trang tĩnh. |
| `rework-diff-check.log` | 0 | Không lỗi whitespace. |

`git status --short` sau commit không có output; worktree sạch. Bằng chứng chỉ là fixture/fetch mock cục bộ; không chứng minh API/gateway/browser/lab/production.
