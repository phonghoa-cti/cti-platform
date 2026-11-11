# Fixture local ingest

Tất cả file trong thư mục này là dữ liệu tổng hợp, không chứa CTI thật, secret
hoặc mẫu gold. PDF chỉ dùng lớp text tối thiểu để kiểm hợp đồng cục bộ; chúng
không chứng minh độ an toàn parser, chất lượng trích PDF thật, OCR hay sandbox.

- `text-crlf.txt`: giữ nguyên CRLF, CR, LF và marker NUL tổng hợp.
- `text-bom.txt`: giữ nguyên BOM UTF-8 trong canonical text.
- `text-vi-emoji.txt`: Unicode tiếng Việt và emoji.
- `two-text-pages.pdf`: hai trang text.
- `blank-middle-page.pdf`: ba trang, trang giữa rỗng.
- `all-whitespace-pages.pdf`: chỉ whitespace, phải bị từ chối.
- `encrypted.pdf`: fixture mã hóa, chỉ để xác nhận từ chối; runtime không giải mã.
- `malformed.pdf`: có magic PDF nhưng cấu trúc sai.

Các PDF hợp lệ có marker NUL tổng hợp sau EOF để Git nhận diện là binary; marker
không nằm trong lớp text mà parser trả về.
