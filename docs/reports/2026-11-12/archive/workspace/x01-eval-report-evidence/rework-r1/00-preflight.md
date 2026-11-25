# X01-EVAL-REPORT R1 — preflight

- Review: `PHONG-HOA-X01-EVAL-REPORT-REVIEW-20261111.md`
- Target base trước rework: `b765b8602785cee98b697f4c6319c7f17447741c`
- Branch: `feat/x01-eval-report-20261111`
- Source read-only: `984bd2136872f4c5fba4118e33cf02b5ca615f2d`, sạch trước/sau.
- Leader probe SHA-256 trước/sau: `62C8FA1205A908103ED5A572E0C086B08A8CD5549E956E346CC7034395E2D8E7`.
- Review được xác minh trên code: `_validate_ttp_top` so dict trực tiếp, trong khi Python coi
  `True == 1 == 1.0` và `False == 0 == 0.0`.

Phạm vi rework chỉ `extractor/eval/report.py` và `extractor/tests/test_eval_report.py`; không sửa probe,
review, producer, evidence cũ hoặc RUNS.
