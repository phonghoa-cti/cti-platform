# Kiểm manifest hai chiều

- Manifest SHA-256: `348a7b8c06d3688bc581accbabd1f659967b29ab133ef6f05e4d1c5763df943b`.
- Tính lại SHA-256 của từng path khai báo: 6/6 entry khớp, `failed=0`.
- So tập file evidence (trừ `MANIFEST*`) cộng report với tập path khai báo: `missing=0`, `extra=0`.
- Kết quả cuối: exit 0.
- Manifest không tự hash chính nó; file này lưu kết quả verify và hash của manifest để tránh vòng phụ thuộc.
