# Bằng chứng RED/GREEN — adapter C2/C3 ngoại tuyến

Ngày chạy: 2026-11-11 (Asia/Saigon). Python 3.12.13, Ruff 0.17.4.

Các vòng TDD đã quan sát trực tiếp trên nhánh `feat/x01-llm-adapter-offline-20261110`:

| Vòng | RED | GREEN |
|---|---|---|
| Khung adapter/CLI | `44 failed`, exit 1: module và CLI chưa tồn tại | `44 passed`, exit 0 |
| Lỗi exception provider bị rò | `1 failed`, exit 1: exception thô thoát ra | `1 passed`, exit 0: quy về `provider_error`, retry rồi fallback |
| Fixture raw vượt 1 MiB | `1 failed`, exit 1: CLI vẫn tạo output | `1 passed`, exit 0: chặn trước khi đọc/tạo output |
| Trường artifact tối thiểu | `3 failed`, exit 1: thiếu `warnings` và `output` trong summary | `3 passed`, exit 0 |
| R1 kiểu dữ liệu `language`/`config` | `4 failed`, exit 1: list/dict thoát `TypeError`; 8 ca còn lại đạt | `12 passed`, exit 0: mọi kiểu/enum sai trả `AdapterError invalid_input`, provider 0 call, không lộ marker |

Kiểm chứng cuối được ghi riêng trong `targeted.xml`, `full-suite.xml`, `c2-result.json`, `c3-result.json`.

Lưu ý: đây là test provider giả lập, không có model thật, mạng, key, SQLite, lab hoặc cloud.
