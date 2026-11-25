# Cleanup và ownership

- Evidence directory được tạo mới riêng cho task; không ghi đè output của người khác.
- Lần rerun chỉ unlink năm path synthetic có parent đúng evidence directory: DB, hai envelope, bundle và summary.
- Sau demo không còn process Python/STIX có executable path thuộc target.
- Không tạo listener/browser/server/background job.
- DB và envelope còn lại trong evidence là artifact synthetic có chủ ý để Leader kiểm lại; không chứa raw CTI thật,
  secret, token hoặc danh tính người dùng thật.
- `.venv` target chỉ là môi trường local ignored; không nằm trong commit/diff.
