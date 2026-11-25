# TDD và các cổng trung gian

- Task 1 RED: 3 failure đúng nguyên nhân option `--created-by-subject` chưa tồn tại. GREEN: `test_store_cli.py`
  28 passed, exit 0.
- Task 2 RED: 4 failure đúng nguyên nhân scenario `stix-e2e` chưa được phép. GREEN focused: 4 passed; toàn
  `test_runner.py` sau Task 2: 17 passed, exit 0.
- Task 3 thêm executable acceptance matrix sau khi Task 2 đã GREEN nên lần chạy đầy đủ đầu tiên PASS; không bịa
  một RED độc lập cho script. Interface mà matrix dùng đã có RED ở Task 2. Matrix cuối có 59 checks và runner
  cuối có 18 tests.
- Lượt pre-final đầu: targeted pytest 54, E2E 59 và selection 113/10 đều đạt, nhưng overall FAIL vì Ruff check
  và format exit 1. Đã sửa đúng một lint và format hai file; lượt đó không được dùng làm PASS.
- Self-review sau HEAD `71b8309` phát hiện `git diff --check base..HEAD` còn một dòng trắng cuối README mà
  `git diff --check` trên working tree sạch không thấy. Đã sửa tại `cf9e609` và chạy lại toàn bộ cổng.
- Lượt final sau HEAD `cf9e609`: targeted pytest 54, E2E 59, selection 113/10, Ruff check/format và diff-check
  base→HEAD đều exit 0.
