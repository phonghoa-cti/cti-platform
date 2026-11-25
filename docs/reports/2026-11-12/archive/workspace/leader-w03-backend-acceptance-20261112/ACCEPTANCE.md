# Nghiệm thu Backend W03 B1/B2 — 12/11/2026

PASS cục bộ tại abcd14dacca361791b17719632d2ce38557d6baf; đóng B1/B2, chưa nghiệm thu tích hợp/browser.

## Đối chiếu và kiểm mới của Leader
- Base rework a49486caf39942019259e41514457bdb85498347; HEAD đúng, git status sạch.
- Đọc delta 4 file +219/-9, đúng allowlist: cves.py, test_cves_api.py, contract và PROGRESS. Không đổi store/auth/app/shared hay Frontend.
- B1 dùng cùng connection SQLite URI mode=ro, BEGIN đọc, kiểm schema/index/marker rồi SELECT bounded LIMIT1001 và validate rows, rollback/close. Test từng defect riêng, valid controls và SQL snapshot trước/sau.
- B2 bắt lỗi hostname/port, authority sai/whitespace/backslash/escape; giữ URL/IPv6 hợp lệ. Không DNS/network.
- Chạy mới 59 tests W03 + nguyên 3 QA probes: **62 passed in 2.69s, exit0**. Log tests.log và tests.xml tại thư mục này.
- Probe QA SHA256 giữ nguyên D17F27A8E50CE9AF17D343BE3B7A4FD229E925B34FB3BBCA7D74E5E6476DDD20.
- Kiểm thêm suffix sau bracket IPv6: **4 passed in 0.77s, exit0**, hai malformed503 và hai valid200, SQL snapshot không đổi. test_bracket_authority.py, bracket-tests.log/xml.
- HEAD/status/diff-check sau chạy vẫn đúng/sạch. Hai thử import trực tiếp ban đầu thiếu PYTHONPATH core/extractor; đó là lỗi lệnh kiểm, không phải lỗi sản phẩm; phép kiểm kết luận dùng pytest.ini đúng . core extractor.

## Lệnh tái chạy
Cwd ROOT/cti-w03-read-backend, Python .venv/Scripts/python.exe.
```text
python -X utf8 -B -m pytest -c pytest.ini --rootdir . -o addopts='' -p no:cacheprovider portal_api/tests/test_cves_api.py <original-QA-probe> -q --junitxml ../leader-w03-backend-acceptance-20261112/tests.xml
python -X utf8 -B -m pytest -c pytest.ini --rootdir . -o addopts='' -p no:cacheprovider ../leader-w03-backend-acceptance-20261112/test_bracket_authority.py -q --junitxml ../leader-w03-backend-acceptance-20261112/bracket-tests.xml
```
Original-QA-probe:
$THREADS/4431b864-0d00-4d10-93c9-a10bcad43317/w03-backend-qa-evidence/test_w03_backend_qa_probes.py

## Bằng chứng kế thừa và giới hạn
Đã đọc report và w03-backend-rework-evidence/03-final-checks.log: Ruff check/format exit0, RED12fail47pass và QA RED3fail được worker báo; không gọi là Leader đã chạy RED/lint. Không chạy lại345 tests vì shared không đổi.
Frontend f650f04de8f08238e13e2630f974e9f30ef838b5 đã accepted qua51+3 kiểm tươi ở lượt trước; không chạy lặp.

Hai input đủ điều kiện giao W03-READ-INTEGRATION ở tree riêng. Gateway/browser/mobile/feed/OpenCTI/Cloudflare/JWKS/HTTPS/lab/production chưa được chứng minh. Cả dự án vẫn active.
