# F02 — Chuẩn hóa và khử trùng lặp

- Vai: Hạ tầng & Dữ liệu · Mốc: v0.1 · Trạng thái: Nháp

## Mục tiêu
Cùng một IOC từ nhiều nguồn chỉ là một object trong OpenCTI, với danh sách nguồn đã báo nó.

## Bối cảnh
OpenCTI tự gộp object có cùng ID STIX. Vì vậy chỉ cần: (1) chuẩn hóa giá trị trước khi tạo ID;
(2) dùng ID "xác định" (deterministic) — cùng giá trị luôn ra cùng ID.

## Tiêu chí chấp nhận
- [ ] Mọi connector tự viết gọi `phonghoa_core.normalize()` trước khi tạo object.
- [ ] Chạy connector hai lần liên tiếp: số object không tăng.
- [ ] Thử nghiệm: đưa `EVIL.com.`, `evil[.]com`, `evil.com` qua 3 nguồn giả → chỉ 1 object, 3 nguồn.
- [ ] Ghi tỉ lệ trùng lặp đo được (số bản ghi vào / số object) vào devlog — số liệu cho chương 4.

## Task
1. Viết test cho bước tạo ID STIX dùng `pycti` (không gọi mạng).
2. Thêm thử nghiệm 3 nguồn giả vào `connectors/_experiments/dedup/`.
