# Kiểm manifest hai chiều

- Manifest SHA-256: `f03b73538009e6d9c9873730c0723dd40f0dd8fc08840d7c33d81ccbd5742f87`.
- Đã đọc từng dòng `hash  relative-path`, resolve từ evidence directory, tính lại SHA-256 của file đích và so
  ngược với hash khai báo.
- Kết quả: 11/11 entry `PASS`, `FAILED=0`, exit 0.
- Manifest gồm report ngoài evidence qua path `../PHONG-HOA-X01-INGEST-QUEUE-RESULT.md`; không tự hash chính nó để
  tránh vòng phụ thuộc. File này ghi kết quả verify và SHA-256 của manifest.
