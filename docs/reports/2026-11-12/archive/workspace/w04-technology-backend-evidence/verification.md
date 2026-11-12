# W04 technology backend — bằng chứng cục bộ

## Môi trường

- CWD: `$WORKSPACE\cti-w04-technology-backend`
- Interpreter: `$WORKSPACE\cti-w02-lookup-api\.venv\Scripts\python.exe`
- `PYTHONPATH`: đúng CWD target ở trên.
- Base: `8a767314b654d39c1ddc2995b7919c44a5b7027a`
- HEAD: `b32fbfe8bb5e72230424ab23d27f8949238dd2a9`

## RED → GREEN

- RED: `python -m pytest portal_api/tests/test_technologies_store.py portal_api/tests/test_technologies_api.py -q`
  - Exit `1`.
  - `2` collection errors đúng nguyên nhân: chưa có `portal_api.technologies` / `TechnologyStore`.
- GREEN focused cuối: cùng hai file test technology.
  - Exit `0`.
  - `47/47` test đạt.

## Cổng regression cuối

Lệnh:

```text
python -m pytest portal_api/tests/test_technologies_store.py portal_api/tests/test_technologies_api.py portal_api/tests/test_assets_api.py portal_api/tests/test_w02_ioc_api.py -q
```

- Exit `0`.
- `148/148`: technology `47`, assets `55`, W02 `46`.
- Output tiến độ: `72 + 72 + 4`, không failure/error.

Kiểm tĩnh trên năm file Python delta:

- `python -m ruff check ...`: exit `0`, `All checks passed!`.
- `python -m ruff format --check ...`: exit `0`, `5 files already formatted`.
- `git diff --check`: exit `0`.
- Collect count độc lập: exit `0`, `TOTAL=148 TECHNOLOGY=47 ASSETS=55 W02=46`.

## Diff và phạm vi

- Commit: `feat: add local technology asset API`.
- Diff base..HEAD: 8 file, `+1412/-0`.
- Chỉ gồm `portal_api/technologies.py`, model/wiring additive, hai test technology, một fixture, spec technology và mục progress riêng.
- Không sửa `assets.py`, `ioc_lookup.py`, auth/settings/core/dependency/gateway/UI/RUNS.
- Tree commit sạch sau commit.

## Mức bằng chứng

PASS cục bộ/in-process với SQLite và JWT tổng hợp. Không kiểm gateway, UI/browser, Cloudflare/JWKS thật, lab,
OpenCTI, W03 matching hoặc production.
