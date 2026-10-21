---
name: stix-connector
description: Mẫu chuẩn để viết một connector thu thập nguồn threat intel mới (feed CSV/JSON/RSS/API) và đẩy dữ liệu STIX 2.1 vào OpenCTI. Dùng khi người dùng yêu cầu thêm một nguồn dữ liệu, feed, hoặc trang tin bảo mật mới.
---

# Viết connector mới cho Phong Hỏa

## Trước khi code
1. Đọc tài liệu nguồn: định dạng, giới hạn request, điều khoản sử dụng, giấy phép dữ liệu. Ghi vào `connectors/<ten>/SOURCE.md`.
2. Tải 1–2 mẫu dữ liệu thật, lưu vào `connectors/<ten>/tests/fixtures/` (đã cắt nhỏ, không chứa dữ liệu cá nhân).
3. Xác định: loại IOC, TLP mặc định, độ tin cậy nguồn (A–F), chu kỳ lấy dữ liệu.
4. Tham khảo cách parse có sẵn: tài liệu feeds của IntelMQ, connector chính thức trong repo `OpenCTI-Platform/connectors`.

## Cấu trúc thư mục
```
connectors/<ten>/
├── SOURCE.md          # mô tả nguồn, giấy phép, giới hạn
├── src/
│   ├── fetch.py       # chỉ tải dữ liệu (có timeout, retry, cache)
│   ├── parse.py       # dữ liệu thô -> list[dict] chuẩn hóa (hàm thuần, dễ test)
│   ├── to_stix.py     # dict -> stix2 objects (Indicator, Observable, Relationship)
│   └── main.py        # vòng lặp: fetch -> parse -> to_stix -> gửi OpenCTI (pycti)
├── tests/
│   ├── fixtures/
│   ├── test_parse.py
│   └── test_to_stix.py
├── Dockerfile
└── config.example.yml
```

## Quy tắc
- `parse.py` và `to_stix.py` không gọi mạng → test chỉ dùng fixtures.
- Chuẩn hóa IOC và gắn TLP/điểm theo skill `cti-thesis-conventions`.
- ID STIX phải ổn định (deterministic), ví dụ `pycti.Indicator.generate_id(pattern)`, để chạy lại không sinh trùng.
- Tôn trọng rate limit: đọc header `Retry-After`; khi gặp 429 thì backoff theo cấp số nhân, tối đa 5 lần.
- Log: số bản ghi tải về, số hợp lệ, số bị loại (và lý do), thời gian chạy.
- Văn bản dài (bài báo, báo cáo) không tự trích IOC ở connector: gửi sang `extractor/` qua hàng đợi.
- Container giới hạn RAM (`mem_limit: 256m`) vì máy chủ chỉ có 16 GB.

## Định nghĩa "xong"
- [ ] Test parse và to_stix xanh; có ít nhất một test với dữ liệu lỗi hoặc thiếu trường.
- [ ] Chạy thật vào OpenCTI lab, thấy object trên giao diện, có nhãn TLP và nguồn.
- [ ] Chạy lại lần hai không sinh bản ghi trùng.
- [ ] Đã cập nhật bảng nguồn trong Wiki và `docs/PROGRESS.md`.
