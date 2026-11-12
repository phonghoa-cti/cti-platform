# X01-C4 adapter rework R1 — verification

Ngày chạy: 11/11/2026. Python duy nhất: `cti-platform-start/.venv/Scripts/python.exe`, mọi lệnh Python dùng `-X utf8 -B`; pytest tắt cache bằng `-p no:cacheprovider -o addopts=`. `PYTHONPATH` là `target/core;target/extractor`.

| Bước | Lệnh rút gọn | Exit | Kết quả |
|---|---|---:|---|
| RED regression | `pytest ... test_llm_adapter.py -k invalid_utf8_response_metadata` | 1 | 12 failed, 71 deselected; đúng `UnicodeEncodeError` |
| GREEN regression | cùng lệnh sau sửa | 0 | 12 passed, 71 deselected |
| Probe Leader | `pytest ... x01-c4-adapter-leader-review/test_c4_response_metadata.py` | 0 | 12 passed |
| Adapter + audit | `pytest ... test_llm_adapter.py test_ttp_audit.py` | 0 | 138 passed |
| CLI + evaluator | từ target: `pytest ... test_llm_cli.py test_eval_cli.py` | 0 | 73 passed |
| C2/C3 compare | `compare_c2_c3.py source target` | 0 | 6/6 artifact bằng nhau |
| Ruff | `ruff format`, `ruff check`, `ruff format --check` trên 2 file đổi | 0/0/0 | sạch |
| Diff check | base→HEAD và pre-R1→HEAD | 0/0 | sạch |

Probe SHA-256 trước/sau: `52DC1FBA95B55D365B34489DA7F4C62887566283BE5A06E776EC98681DDD6792` (không đổi).

Target HEAD `654443e6ede6557f0629fc0886ca56fff782b193`, source `d97f96362edcd92e87fc69cfa20a563109cec550`; cả hai `status --porcelain` rỗng khi ghi bằng chứng Git. Diff R1 chỉ gồm `extractor/phonghoa_extractor/llm_adapter.py` và `extractor/tests/test_llm_adapter.py`, `+31/-1`.

Self-review: fix chỉ bắt `UnicodeEncodeError` ngay tại phép mã hóa metadata; không thay terminal refusal/incomplete/non-retryable error, không bắt exception rộng quanh pipeline, không đưa raw metadata vào exception/result. Test gây lỗi nếu bỏ catch, đổi mã lỗi, retry một lần, thay request object hoặc làm lộ marker.

UNVERIFIED: model/provider thật, corpus hai người gán nhãn, semantic TTP/RAG, evaluator/reporter C4, OpenCTI, lab và production.
