# W02 local integration — RED → GREEN

## Route và nhãn nguồn

- RED: `npm test -- --run tests/ioc-lookup.test.tsx` → exit `1`; `1 failed, 33 passed` vì route mode vẫn hiện nhãn fixture cũ.
- GREEN mục tiêu: cùng lệnh → exit `0`; `34 passed`.
- GREEN hồi quy cuối: `npm test` → exit `0`; `9 files, 178 tests passed`.

## Gateway exact `/api/ioc` và chống header giả

- RED: `node --test tools/local_integration/tests/test_gateway.mjs` → exit `1`; `9 passed, 1 failed`, expected `200`, actual `404` cho `/api/ioc`.
- GREEN: cùng lệnh → exit `0`; `10 passed`.

## LocalRun và fixture W02

- RED: `.venv\Scripts\python.exe -X utf8 -B -m pytest tools/local_integration/tests/test_runner.py -q` → exit `1`; sáu scenario W02 bị từ chối và route mặc định qua gateway trả `404`.
- GREEN mục tiêu: `-k "w02 or ttl"` → exit `0`; `8 passed`.
- GREEN hồi quy cuối: toàn file runner → exit `0`; `25 passed`.

Mỗi RED thất bại vì điểm nối chưa có, không phải vì assertion/mocking sai. Implementation tối thiểu sau RED gồm route client wrapper, một exact allowlist gateway và fixture/role scenario trong LocalRun.
