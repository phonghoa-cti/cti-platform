# F04 — Chấm điểm, decay và allowlist

- Vai: Hạ tầng & Dữ liệu (code) + AI & Agent (review công thức) · Mốc: v0.5 · Trạng thái: Nháp

## Mục tiêu
Mỗi Indicator trong OpenCTI có điểm 0–100 được tính lại mỗi giờ theo công thức của nhóm, kèm lời giải thích.

## Cách làm
Viết dịch vụ nhỏ `scorer/` chạy theo lịch:
1. Đọc Indicator thay đổi gần đây qua `pycti`.
2. Tính điểm bằng `phonghoa_core.scoring.score()`; kiểm tra `Allowlist`.
3. Ghi điểm vào trường `x_opencti_score`; ghi lý do vào một Note gắn với Indicator.
4. Điểm < 20 hoặc nằm trong allowlist → đánh dấu không xuất ra blocklist.

## Tiêu chí chấp nhận
- [ ] Có test cho phần chuyển dữ liệu OpenCTI → `ScoreInput` (dùng fixtures JSON).
- [ ] 8.8.8.8 hoặc IP Google xuất hiện trong feed → điểm 0, có lý do "allowlist".
- [ ] Analyst đánh dấu báo nhầm (nhãn `false-positive`) → độ tin cậy nguồn giảm theo `penalize_false_positive`.
- [ ] Chạy ổn định 3 ngày, mỗi lần < 5 phút.

## Câu hỏi mở
Lưu độ tin cậy từng nguồn ở đâu: file YAML trong repo (đơn giản) hay trường tùy chỉnh trong OpenCTI? Đề xuất: YAML trước.
