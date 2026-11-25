# W05-STIX evidence — 11/11/2026

Phạm vi: dữ liệu tổng hợp, local Windows/NTFS, không network listener, OpenCTI, lab, Cloudflare, LLM hay dữ
liệu thật. Base `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`; commit
`ed829a0344b2d3d4392fae933e41a9c44fdcd853`.

## Rework R1/R2

- Regression repo RED: 20 fail/8 pass, exit 1; GREEN: 28 pass, exit 0.
- Probe Leader nguyên trạng: 14 pass, exit 0; probe SHA-256
  `8ED38838B86F546826808DC820A7A9EF795526AE94B5E9277B70F3EFEAD80BDA` không đổi.
- Hai file STIX cuối: 77 pass, exit 0; gồm validator, race Windows, no-clobber và CLI safe JSON.
- Ruff check, Ruff format check và `git diff --check`: exit 0.
- Alias file/directory của DB và config vẫn dùng được cho output bundle thường; tên lexical/resolved và ba sidecar
  `-wal`, `-shm`, `-journal` đều bị chặn làm output, DB/config giữ nguyên hash.
- Raw command/stdout/stderr/exit nằm trong `rework-r1-r2/`. Full Python 500 là lượt trước rework và không chạy lại.

## TDD đã quan sát

| Nhóm | RED | GREEN |
|---|---|---|
| API mới | Import `phonghoa_extractor.stix_export` thiếu, collection exit 2 | Targeted cuối 53 test, exit 0 |
| Mapping/ID/CLI | Lượt implementation đầu còn 9 failure, exit 1 | Tám IOC/TLP/provenance/CLI qua trong targeted cuối |
| Validator | 4 failure, exit 1: marking literal thiếu `name`, giả định exit code sai | 3 negative + MUST/ref + strict-except-103 qua |
| Review hardening | 7 failure, exit 1: audit cũ, ancestor reparse, race alias, scalar validation, safe error | 7 test focus qua, exit 0 |
| Audit ID | Negative audit ID chưa bị từ chối, 1 failure, exit 1 | Test focus qua, exit 0 |

## Lệnh và kết quả

- Baseline sau khi sync `requirements-api.lock`: `.venv\Scripts\python.exe -m pytest -q` → exit 0.
- STIX targeted: hai file `test_stix_export*.py` → 53 test, exit 0.
- Selection/review regression → 71 test, exit 0.
- Store/queue/CLI regression → 127 test, exit 0.
- Full Python cuối: `.venv\Scripts\python.exe -m pytest -q` → 500 test, exit 0.
- Ruff changed Python: `ruff check ...` → exit 0; `ruff format --check ...` → exit 0.
- `git diff --cached --check` trước commit → exit 0.
- Windows race focus (same bytes, different bytes, protected alias) → 3 test, exit 0.
- `stix2-validator` package metadata → `3.3.2`; executable `--help` → exit 0.
- Demo validator `--version 2.1 --enforce-refs` → exit 0.
- Demo validator `--strict --disable 103` cùng schema/ref → exit 0.
- Plain strict → exit 2 và chỉ có ba check `{103}` cho Bundle/Identity/Report UUIDv5.
- `git diff base -- requirements-api.in requirements-api.lock portal/web/package-lock.json` → exit 0.

## Demo deterministic

`demo_w05_stix.py` tạo hai IOC, lưu selection `[1]`, reviewer khác author approve, export và re-export cùng
snapshot. `demo-summary.json` quan sát chỉ có `beta.evil.example`, object count 4, bytes/mtime không đổi khi
re-export. Negative case dùng draft pending; DB và output hash không đổi sau lỗi. `demo.sqlite` và config đều là
synthetic, không dùng làm bằng chứng production.

## Giới hạn

PASS này chỉ chứng minh converter/read snapshot/publisher/validator cục bộ. Chưa kiểm import/workbench OpenCTI,
mapping reviewer-author thật, filesystem network, crash/power-loss, người có quyền đổi directory đồng thời,
Cloudflare, lab, deploy hay production. Validator PASS không chứng minh sharing authority hoặc CTI correctness.
