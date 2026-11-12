# X01-GOLD-PILOT-IMPLEMENT — kết quả sau rework R1–R5

## PASS

- Target: `cti-x01-gold-pilot`.
- Branch: `feat/x01-gold-pilot-readiness-20261111`.
- Base/source: `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`; source sạch, không đổi.
- Commit ban đầu: `9d278cfc1f9cbc2b6236b06c8e1c7541d7e7aed5`.
- Commit rework: `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`.
- Rework diff: 3 file, `+233/-39`; target sạch.

## R1–R5

- R1: mọi enum/hash được kiểm đúng kiểu trước membership/hash; JSON list/dict trả mã lỗi đóng.
- R2: URL parse lỗi, userinfo rỗng và control/DEL trả `invalid_record`; CLI JSON sạch, không traceback.
- R3: kiểm reparse trên mọi lexical ancestor trước resolve/open cho dataset, pin, snapshot và output.
- R4: enumeration streaming dừng tại cap; fingerprint kiểm size và map lỗi I/O thành `io_failure`.
- R5: manifest evidence loại đúng chính nó theo full path, kiểm đủ file/hash/size hai chiều và chứa các
  `demo/*/dataset/manifest.json`.

## RED→GREEN và kiểm chứng

- Probe Leader nguyên trạng: `26 failed / 1 passed`, exit 1 → `27 passed`, exit 0.
- Regression repo: sau khi thêm test trước `25 failed / 9 passed`, exit 1 → `34 passed`, exit 0.
- Ruff check/format ba file Python: exit 0.
- Diff-check `9d278cf..HEAD` và `5e0cbf4..HEAD`: exit 0.
- Writer no-clobber/post-link cleanup test: exit 0.
- Demo: READY `0/0`, NOT_READY `2`, INVALID `2`; JSON sạch, INVALID không tạo report.
- Hai report READY byte-identical; hash input trước/sau không đổi.
- Không chạy lại 349 regression cũ vì C1–C4/catalog không đổi, đúng brief Leader.

Probe Leader giữ SHA-256 `e472ff28687beca7341b06e63a9ba86768d3be17db70ad3404f3e8b56c4c02c6`.
Evidence mới: `x01-gold-pilot-evidence/rework-r1-r5/`.

## Giới hạn

Test reparse ancestor bằng fault injection đã đạt 8 ca tổng cộng giữa repo/probe Leader. Thử junction Windows
thật bị chính sách máy chặn trước khi tiến trình khởi chạy; không giả PASS và không tạo/xóa junction.

UNVERIFIED: quyền raw corpus thật; hai annotator thật/độc lập; adjudication; semantic TTP; corpus gold;
model/RAG quality; chữ ký catalog release; hostile mutation; crash/power-loss; cloud/lab/OpenCTI/production.

Đây là kết quả worker để Leader nghiệm thu độc lập, không tự coi là nghiệm thu/merge/phát hành.
