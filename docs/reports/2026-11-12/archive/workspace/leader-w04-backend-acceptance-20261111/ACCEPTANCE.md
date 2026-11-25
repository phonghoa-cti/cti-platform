# Nghiệm thu Backend W04 cục bộ — 11/11/2026

**PASS cục bộ/in-process tại `90b26287eccc416fd7e7e736b0ad37632e0c34b1`.** Bốn finding QA F1–F4 đã đóng trong phạm vi Backend. Chưa nghiệm thu giao diện hoặc tích hợp W04.

## Bằng chứng Leader vừa chạy

- Đúng branch/tree `cti-w04-assets-local`; HEAD trước/sau khớp, `git status --porcelain` rỗng.
- Đã đọc delta từ `5316422ef6091f48edca443f886358a4475d8e04`: 3 file, +40/-15, chỉ assets classifier, regression và PROGRESS. Không đổi schema/fixture/Frontend/W02.
- CWD target; interpreter `cti-w02-lookup-api/.venv/Scripts/python.exe`; PYTHONPATH trỏ target root/core/extractor, PYTHONUTF8=1.
- `python -m pytest portal_api/tests/test_assets_api.py -o addopts= -q --junitxml=<evidence>/assets-tests.xml`: **55 passed in 2.12s**, exit 0; raw `assets-tests.txt`, `assets-tests.xml`. Bao gồm duplicate canonical thật create/update vẫn 409, actor/output/version bounds, rollback, auth và snapshot.
- Probe Leader `leader-w04-rework-acceptance-20261111/f4_unrelated_unique_probe.py` giữ nguyên SHA256 `67D718C3D77C2973E6DE517612B2D120B487835B2F790F0609106220CB061F56`: **2/2 PASS**, exit 0. POST/PUT đều 503 assets_unavailable, asset/audit 1/1, row không đổi. Raw `f4-http-results.json`, `f4-probe.txt`.
- `git diff --check 5316422ef6091f48edca443f886358a4475d8e04 HEAD`: exit 0. SHA, tree và exit được ghi tại `verification.json`.

## Bằng chứng tái sử dụng

- F1–F3 và phần không đổi đã được Leader kiểm trên `5316422e`: assets + W02 99 PASS, bảy probe QA nguyên bản đúng expected, ghi ở `leader-w04-rework-acceptance-20261111/REVIEW.md`. Kết luận FAIL khi đó chỉ còn F4, nay được hai probe độc lập xác nhận đã sửa.
- Đọc worker RED JUnit: 2 test/2 failure/0 error; GREEN assets JUnit: 55/0/0. Raw lint cuối ghi All checks passed, format 13 files already formatted. Đây là bằng chứng worker đã đối chiếu, không nhận là Leader vừa chạy lint.
- Nghiên cứu/hợp đồng/fixture W04 đã được kiểm trước; không nghiên cứu lại hoặc chạy lại full portal/W02 khi delta không chạm chúng.

## Quyết định và giới hạn

Chấp nhận `W04-ASSETS-IMPLEMENT` tại SHA trên, bảo toàn các báo cáo FAIL lịch sử. Classifier chỉ nhận đúng lỗi UNIQUE của `assets.type, assets.canonical_value`; lỗi khác trả unavailable, không lộ chi tiết SQLite. Hành vi này đã kiểm trên runtime SQLite cục bộ; đổi runtime cần giữ kiểm duplicate và unrelated UNIQUE.

Frontend đang chạy trong thread `957c7dec-fe60-4717-acf1-8531e349e4aa`, request `659a5f35-1227-4205-a8dd-7cafc677f9bb`, được giữ nguyên. Bước kế là nghiệm thu Frontend rồi giao CTI Engineer nối hai SHA đã đạt trong tree riêng và kiểm cùng DB. Chưa lấy mã Frontend đang sửa, không tạo người làm trùng.

Hai lịch nối việc đã được đọc và còn enabled; dự án active nên giữ nguyên. Lịch 30 phút trả phần cuối instructions bị cắt; điều kiện bảo toàn việc/tiếp tục/dừng đã được đối chiếu quy trình cục bộ.

**UNVERIFIED:** UI/browser W04, HTTP listener và tích hợp cùng DB, Cloudflare/JWKS/HTTPS thật, OpenCTI, feed/LLM thật, lab/production. Không push/PR/merge/deploy.
