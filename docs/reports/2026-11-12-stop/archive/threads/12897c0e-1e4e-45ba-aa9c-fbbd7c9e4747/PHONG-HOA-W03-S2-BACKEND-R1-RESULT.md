# W03-S2 Backend R1 — kết quả

Ngày 12/11/2026. Candidate trước R1: `82f8a6acc8f357645f7105a2cc84b46bf58f4e4f`.
Commit R1: `3e6934037879860c8abb5f6d797381dbe3225633`
(`fix: reject malformed W03 status cursors`). Branch giữ nguyên; tree sạch.

## PASS

- TDD RED 7/7 được quan sát trước sửa: array/dict gây 503, integer được nhận 200, ngày lịch sai trả 409,
  NaN/surrogate gây 503. Log tại `w03-s2-r1-evidence/01-red.txt`.
- Decoder nay kiểm type trước membership/equality; `kev` chỉ nhận exact bool/null, integer không giả bool. JSON
  nonfinite bị chặn khi parse; lỗi canonical UTF-8 được đổi thành lỗi query; ngày được parse thành ngày lịch thật.
  Không sửa generic exception handler nên dependency failure thật vẫn giữ 503.
- GREEN focused: 7/7 pass; từng response là 422 `invalid_cve_status_query`, có no-store/Vary, không gọi dataset
  và không đổi schema/Technology/status/audit.
- Probe Leader chạy lại từ source gốc nhưng redirect output sang evidence mới: control 200; bảy invalid 422,
  `dependency_calls=0`; DB unchanged; 8 pass/0 fail; exit 0.
- Bốn drift tách fixture mới: status-only, dataset-only, Technology-only và UTC-date-only đều trả độc lập 409
  `status_snapshot_changed`, không dựa vào mutation từ case trước.
- S2 + W03-R + W03-S1: 138/138 pass, exit 0. Ruff check/format và diff-check exit 0.
- Fixture wire và contract không đổi schema nên không tạo lại hình thức. `docs/PROGRESS.md` ghi rõ R1.

## Diff

- `portal_api/cves_status_view.py`: validation cursor/canonical/date/type tối thiểu.
- `portal_api/tests/test_cves_status_view_api.py`: 7 regression invalid + 4 drift độc lập.
- `docs/PROGRESS.md`: hai dòng tiến độ R1.
- Delta R1: 3 files, +122/-9.

## Lệnh và raw evidence

- `01-red.txt`: RED exit 1, 7 failed.
- `02-green-focused.txt`: GREEN exit 0, 7 passed.
- `03-regressions.txt`: exit 0, 138 passed.
- `04-probe-command.txt` + `w03-s2-cursor-probe-results.json`: probe exit 0, 8/8.
- `05-quality-git.txt`: Ruff/format/diff-check/SHA/status/diff stat, exit 0.

## Giới hạn / UNVERIFIED

- Theo brief không chạy lại full suite; giới hạn môi trường cũ vẫn là bốn test STIX thiếu
  `stix2-validator==3.3.2`. Không cài hoặc đổi dependency.
- Không gateway/frontend/browser, feed/OpenCTI, Cloudflare/JWKS/HTTPS, lab hay production.
- Không push/PR/merge/deploy; chưa mở phụ thuộc Frontend và chưa tuyên bố toàn W03 hoàn thành.
