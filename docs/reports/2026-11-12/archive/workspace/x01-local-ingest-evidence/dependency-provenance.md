# Dependency provenance

- Python: 3.12.13; pip: 25.0.1.
- pytest: 9.2.0; ruff: 0.17.4.
- pypdf: 7.0.1; BSD-3-Clause; Requires-Python >=3.10.
- Official metadata: `https://pypi.org/pypi/pypdf/7.0.1/json`, kiểm
  11/11/2026; trường `vulnerabilities` là mảng rỗng tại thời điểm kiểm.
- Wheel local: `wheelhouse/pypdf-7.0.1-py3-none-any.whl`, 416136 byte,
  SHA-256 `6131b764b046282357037309e7ef2a1b7679d4a5c53eed3db2bfbf7c673ddc2b`.
- Download dùng only-binary/no-deps/require-hashes; install dùng
  no-index/find-links/only-binary/no-deps/require-hashes vào target `.venv`.
- Sdist chỉ có hash metadata trong lock, không tải/cài.

PyPI advisory metadata rỗng không phải bảo đảm CVE-free. Wheel/hash/install
không chứng minh parser an toàn với PDF đối kháng.
