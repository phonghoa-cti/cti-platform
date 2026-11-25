# AI-EVAL R1 — RED/GREEN

- Review base: `4b74fbb15bfe02fc499ada3ffe05f5dfa34f9120`
- Fixed commit: `8694fa7244d181f421bb2733ded7bf9ae218ea93`
- Branch: `feat/x01-eval-c2c3-offline-20261111`
- Diff R1: 2 file, 49 insertions, 1 deletion.

## RED

Command (cwd tree AI, Python từ venv dùng chung):

```text
python -m pytest extractor/tests/test_eval_cli.py -q -k "label_role"
```

Exit `1`. Có 4 lỗi đúng mục tiêu: `role=[]` và `role={}` ở cả C2/C3 sinh traceback `TypeError`;
14 ca còn lại đạt. Output sentinel `keep-me` vẫn được giữ.

## GREEN

Cùng lệnh trên exit `0`, `18/18` đạt sau khi kiểm `isinstance(role, str)` trước membership.

## Kiểm chứng hậu commit

| Kiểm tra | Exit | Kết quả |
|---|---:|---|
| `pytest test_evaluate.py test_eval_cli.py -q --junitxml=.../r1-targeted.xml` | 0 | 43/43 đạt |
| `ruff check extractor/eval/run.py extractor/tests/test_eval_cli.py` | 0 | All checks passed |
| `ruff format --check ...` | 0 | 2 file đã format |
| `git diff --check 4b74fbb..HEAD` | 0 | Không lỗi whitespace |
| Demo C1 6 tài liệu | 0 | Byte-identical baseline |

C1 SHA-256: `8e4a1e6afbb2029ed521fcc87190e77aa337f4671bf4117fc5ce7d8682029b9f`.

R1 chỉ dùng fixture tổng hợp và provider `fake_offline`. Model/provider thật và corpus CTI được hai người gán
nhãn độc lập vẫn **UNVERIFIED**.
