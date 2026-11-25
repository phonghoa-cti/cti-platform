# W05-STIX-IMPLEMENT — kết quả CTI Backend, 11/11/2026

## Kết luận

**PASS cục bộ** cho lát cắt converter final approved audit → một bundle STIX 2.1 ngoại tuyến. Không sidecar
manifest, không Indicator/Pattern/ObservedData, không ghi/migrate DB, không network/OpenCTI/outbox.

- Worktree: `cti-w05-stix-offline`
- Branch: `feat/w05-stix-offline-20261111`
- Base: `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`
- Commit: `ed829a0344b2d3d4392fae933e41a9c44fdcd853`
- Diff từ base: 12 file, `+2403/-2`; riêng rework R1/R2: 5 file, `+133/-7`.
- Source `cti-w05-selection-integration`: vẫn ở exact base và sạch.
- Worktree implementation sau commit: sạch.

## Đã triển khai

- Getter read-only mở `BEGIN` trước schema/data; kiểm schema v2, payload/review, author khác reviewer, đúng một
  final approve audit, toàn bộ selection events, canonical indices/hash và selection eligible không rỗng.
- Snapshot thêm `decided_by_subject` nội bộ `repr=False`; artifact/stdout không chứa subject hay subject hash.
- Bundle canonical có marking literal, exporter Identity, tám loại SCO và Report chứa provenance canonical trong
  `external_references`. SCO dùng namespace chuẩn OASIS; SDO/Bundle dùng ba child namespace UUIDv5 riêng.
- Publisher temp cùng parent + flush/fsync + `os.link`; existing identical idempotent, existing khác fail;
  bảo vệ tên lexical và resolved của DB/config cùng sidecar, hardlink/symlink/reparse và tái kiểm alias sau race.
- CLI stdout success exact ba field; business error chỉ trả mã JSON an toàn một dòng. Argparse giữ exit 0/2 cho
  help/usage.
- Rework R1 ánh xạ TLP sai kiểu và timestamp tràn UTC về `StixExportError`; CLI không còn traceback/path nội bộ.
- Rework R2 vẫn cho đọc alias tĩnh hợp lệ nhưng từ chối dùng DB/config hoặc sidecar ở đích resolved làm output.
- Pin test-only `stix2-validator==3.3.2` ở root input/lock có hash transitive; runtime không thêm STIX SDK.
- ADR, contract, progress, hướng dẫn CLI và config synthetic đã cập nhật; app locks/UI byte-identical.

## Bằng chứng kiểm

- TDD RED→GREEN: API missing; 9 failure implementation; 4 failure validator; 7 failure review hardening; 1
  failure audit ID; tất cả đã có test xanh tương ứng.
- Rework regression RED: 20 fail/8 pass, exit 1; GREEN: 28 pass, exit 0.
- Probe Leader nguyên trạng: 14 pass, exit 0; SHA-256
  `8ED38838B86F546826808DC820A7A9EF795526AE94B5E9277B70F3EFEAD80BDA` không đổi.
- STIX targeted cuối: 77 test, exit 0, gồm validator 3.3.2, race Windows, publication và CLI.
- Selection/review: 71 test, exit 0.
- Store/queue/CLI: 127 test, exit 0.
- Full Python: 500 test, exit 0.
- Ruff check: exit 0; Ruff format check: exit 0; cached diff-check: exit 0.
- Windows race focus: 3 test, exit 0.
- Validator package `3.3.2`, executable help exit 0; MUST/schema/ref exit 0; strict-except-103 exit 0; plain
  strict exit 2 và chỉ báo check 103 cho ba UUIDv5 SDO/Bundle.
- Demo: chỉ SCO đã chọn; re-export cùng summary/hash và mtime; negative pending giữ DB/output không đổi; validator
  hai profile exit 0. Bundle SHA-256 `B5BB9296F2D1A9CFCE2BE7F5744B4FAB96CE78A4F110A79BC7FF86B975150D45`.
- Lock STIX SHA-256 `238F57B7670077A7F2C546DFEFC24C61F4E84E45371FC848DF5669928E23DC9A`.
- Evidence: `w05-stix-evidence/README.md`, `demo-summary.json`, `demo-bundle.json`, `manifest-sha256.txt`.
- Raw rework: `w05-stix-evidence/rework-r1-r2/` có command, stdout/stderr, exit và hash.

Full Python 500 test là kết quả trước rework tại commit `dbec016`; không chạy lại vì phạm vi rework chỉ exporter,
hai file STIX đã bao phủ validator/race/CLI. Không dùng con số lịch sử đó làm bằng chứng rework mới.

## Giới hạn đúng trạng thái

Chưa kiểm OpenCTI/import/workbench, reviewer-author mapping với danh tính thật, network share, crash/power-loss,
đối thủ có quyền đổi directory đồng thời, Cloudflare, lab, deploy hoặc production. Kết quả nghiên cứu và
validator không được coi là bằng chứng ingestion/production. Lát cắt này không đóng toàn dự án Phong Hỏa.
