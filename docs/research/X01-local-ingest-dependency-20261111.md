# Dependency X01 local ingest — pypdf 7.0.1

Ngày kiểm: 11/11/2026.

## Nguồn và pin

- Nguồn chính thức: `https://pypi.org/pypi/pypdf/7.0.1/json`.
- Phiên bản: `7.0.1`; `Requires-Python >=3.10`; giấy phép `BSD-3-Clause`.
- Wheel dùng: `pypdf-7.0.1-py3-none-any.whl`, 416.136 byte.
- SHA-256 wheel đã kiểm trên bytes tải về:
  `6131b764b046282357037309e7ef2a1b7679d4a5c53eed3db2bfbf7c673ddc2b`.
- SHA-256 sdist chỉ đối chiếu metadata, không tải/cài:
  `0a78bb99efb41e9088260e9a8e5da134a5cbb9a322014744177bf29b5267ea6d`.

## Cài đặt đã quan sát

Wheel được tải bằng `--only-binary=:all: --no-deps --require-hashes`, sau đó
cài ngoại tuyến từ wheelhouse bằng `--no-index --only-binary=:all: --no-deps
--require-hashes` vào đúng `.venv` của worktree. `pip show pypdf` trả phiên bản
`7.0.1`; không cài extra crypto, converter hoặc dependency hệ thống.

PyPI JSON tại thời điểm kiểm trả mảng `vulnerabilities` rỗng. Đây chỉ là
metadata advisory của PyPI tại thời điểm đó, không phải cam kết không có CVE
hoặc bằng chứng parser an toàn với PDF đối kháng.

Log lệnh, hash và phiên bản thực nằm trong gói evidence bàn giao ngoài repo.
