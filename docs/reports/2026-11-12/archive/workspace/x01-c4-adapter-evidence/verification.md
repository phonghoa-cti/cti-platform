# Verification tại HEAD

- Base: `d97f96362edcd92e87fc69cfa20a563109cec550`.
- HEAD: `e5e6751c7c1b35cc22e96c8765be2ee4f2f2a521`.
- Branch: `feat/x01-c4-adapter-20261111`.
- Commit count base..HEAD: `1`.
- Source `cti-x01-c4-retrieval`: exact base, branch `feat/x01-c4-retrieval-20261111`, clean.
- Target: clean.

## Commands và exit

1. Scoped pytest 9 files, `-X utf8 -B`, cache disabled, `PYTHONPATH=target/extractor;target/core`: exit `0`; `428 passed in 36.94s`; skipped `0`. JUnit: `scoped-tests-head.xml`.
2. `python.exe -X utf8 -B -m ruff check` trên 4 Python files: exit `0`, `All checks passed!`.
3. `python.exe -X utf8 -B -m ruff format --check` trên 4 Python files: exit `0`, `4 files already formatted`.
4. `git diff --check d97f963...HEAD`: exit `0`.
5. `compare_c2_c3.py source target`: exit `0`; cả 6 full artifacts success/retry-success/fallback của C2/C3 byte-equivalent theo canonical JSON.
6. `demo_c4.py`: exit `0`; wrapper 1 retrieval gián tiếp qua request context, provider calls `1`, recorded context SHA khớp, public audit dùng cùng report và trả quote `matched`.

## Diff

`7 files changed, 524 insertions(+), 11 deletions(-)`; đúng 7 allowlist files, không dependency/asset/retriever/catalog/CLI/evaluator/reporter thay đổi.

## Self-review

PASS: error order base/TLP/retrieval/provider; exact source UTF-8 bounds; retriever owns bounds/query/catalog/record/budget; one immutable request reused; retry/fallback/terminal lifecycle; zero-match provenance; source/context separation; exact semantic keys; C4 public audit; C2/C3 compatibility.

UNVERIFIED: model thật, model quality, prompt-injection resilience, semantic/multilingual TTP, corpus hai người gán nhãn, evaluator/reporter C4, OpenCTI, lab và production.
