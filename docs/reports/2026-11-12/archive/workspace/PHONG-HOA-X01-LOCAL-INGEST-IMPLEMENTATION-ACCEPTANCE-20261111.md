# Nghiệm thu X01 local ingest — 11/11/2026

**PASS cục bộ, đóng R1–R4. Dự án vẫn active.** Leader nghiệm thu request `b7c026d3-a2b5-47dc-92ae-4409e273ecbc` trong thread `d01bc25b-277d-4840-a747-ac19b043c1fa`.

- Target: `cti-x01-ingest-local`, branch `feat/x01-ingest-local-20261111`.
- HEAD đã đọc trực tiếp: `8a16758601647fb3dbf935abecc2435f3b7a3fb6`.
- Source: `cti-x01-gold-pilot`, giữ `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`.
- Hai working tree sạch; `git diff --check` exit 0.

## Bằng chứng độc lập và phạm vi

Leader đã đọc diff R4: chỉ `extractor/phonghoa_extractor/local_ingest.py` và `extractor/tests/test_local_ingest.py`, +66/-1. Input tương đối dưới thư mục làm việc UNC bị từ chối trước stat/read; input tuyệt đối cục bộ vẫn hoạt động. UNC là đường dẫn chia sẻ mạng Windows.

Lệnh mới tại HEAD, cwd target, Python `.venv/Scripts/python.exe`, `PYTHONDONTWRITEBYTECODE=1`:

```text
python -B -m pytest -o addopts= -q -p no:cacheprovider --tb=short ../leader-local-ingest-review/test_ingest_contract.py ../leader-local-ingest-review/test_ingest_unc_cwd.py extractor/tests/test_local_ingest.py extractor/tests/test_ingest_cli.py
81 passed in 4.82s; exit 0
```

Log: `leader-local-ingest-review/r4-green.log`. Gồm 74 test repo và 7 phép kiểm Leader. Hai probe giữ nguyên SHA-256:

- `test_ingest_contract.py`: `a1896975905607b0cb607b7e5a76a2d22256f8828bd9ee003b37b7f7ed0e11e9`.
- `test_ingest_unc_cwd.py`: `3ef10d378663e3557a5f11ab52588398c96b4464e3d80b9ea833d29d799deffa`.

Đối chiếu manifest hai chiều bằng bytes thực: root `x01-local-ingest-evidence` 32/32; `rework-r4` 6/6; thiếu, thừa và sai hash đều 0. Script kiểm lại exit 0. Lần in ledger đầu gặp lỗi encoding console sau các phép kiểm; đã sửa UTF-8 và chạy lại phần kiểm manifest/đọc ledger, không coi exit 1 đó là thành công toàn lệnh.

R1–R3 đã được kiểm độc lập ở HEAD `732685f7f774fee925840cb7d97b894547bfd119`: 113 test đạt, log `leader-local-ingest-review/rework-green.log`. Đây là bằng chứng trước R4, không phải 113 test chạy tại HEAD mới. R4 giữ nguyên parser child, cleanup, CLI và dependency; không cần lặp full C1 hoặc PDF demo.

| Finding | Kết quả nghiệm thu |
|---|---|
| R1 mã lỗi child sai kiểu | Trả lỗi đóng, không TypeError do list/dict. |
| R2 wait/terminate lỗi | Vẫn thử kill/reap; chỉ dọn temp khi xác nhận child đã dừng. |
| R3 ancestor reparse/symlink | Chặn trước đọc leaf; phép kiểm mô phỏng giữ nguyên. |
| R4 relative path dưới UNC cwd | Chặn trước stat/read; 7 probe gốc đều xanh. |

Báo cáo worker có tiêu đề đầu cũ R1–R3; mục R4 và HEAD cuối mới là phần áp dụng cho lần nghiệm thu này. Worker đã ghi riêng TXT relative demo và Ruff; Leader không biến các log đó thành lệnh mình chạy. TXT/PDF fixture và các kiểm trước được giữ theo đúng ref trong báo cáo.

## Giới hạn và việc tiếp

Nghiệm thu nạp TXT/PDF tổng hợp thành envelope có raw hash, canonical text hash và evidence trên canonical text. Chưa lưu envelope vào hàng chờ W05. Không chứng minh mapped drive không có mạng, chống mọi thay đổi filesystem đồng thời, giới hạn RAM/mạng cứng, parser trước PDF đối kháng, OCR, corpus/model thật, lab hoặc production. Không push/PR/merge/deploy.

Việc kế: nghiên cứu cầu nối envelope đã nghiệm thu sang SQLite pending queue, giữ provenance và tương thích W05 hiện có. Không coi việc này hay lịch tự nối là bằng chứng toàn dự án hoàn thành.
