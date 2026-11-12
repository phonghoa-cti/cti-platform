# X01-ATTACK-REAL — kết quả triển khai official v20.1

Ngày 11/11/2026. Kết quả: **PASS trong phạm vi loader ngoại tuyến**.

## Commit và phạm vi

- Worktree: `cti-x01-attack-official`; branch `feat/x01-attack-official-20261111`.
- Base: `4e894c37df3ad53c16022909ae6df113dd89aa04`.
- Commit cục bộ sạch: `4001441edcf5414df0f06c34352f6c5d3e2a2bd5` — `feat: load pinned official ATT&CK catalog`.
- Diff: 7 file, +293/-16. Không push/PR/merge/deploy.
- Chỉ sửa loader, test/fixture metadata+LICENSE, ADR0004 và PROGRESS theo plan. Không sửa adapter/eval/grounding/store/API/UI/W05/dependency/RUNS/probe/evidence Leader.

## Hành vi đã triển khai

- `load_catalog()` chỉ nhận chính xác bộ pin Enterprise ATT&CK v20.1 đã chốt; sai/missing/khác kiểu/thêm metadata bị `invalid_pin` trước I/O.
- Root official không cần `x_phonghoa_provenance`; synthetic vẫn giữ provenance và toàn bộ strict JSON/lifecycle/graph policy cũ.
- Asset được đọc local, giới hạn size và hash trước decode/parse; không thêm HTTP, TAXII, downloader hoặc dependency.
- Lookup giữ `semantic_status="unverified"` và `operational_draft_eligible=false`.

## RED → GREEN và kiểm chứng

- RED positive asset thật: exit 1, `load_catalog -> _validate_pin -> invalid_pin`; 1 failed trong 0,08 giây.
- GREEN official: exit 0, 62 passed trong 0,76 giây.
- Final từ exact HEAD: exit 0, 166 passed trong 2,49 giây = 104 regression cũ + 62 official; asset path được cấp, không skip.
- Public loader trả 867 record: 706 active, 161 inactive; 497 sub-technique. Các lookup T1001/T1001.001/T1002/T0000/malformed đạt contract.
- Ruff check exit 0; Ruff format check exit 0; `git diff --check BASE..HEAD` exit 0.
- No-egress test chặn ba điểm vào socket trong đường load/lookup; diff code không thêm client mạng. Đây không phải tuyên bố cô lập toàn hệ điều hành.

Log: `x01-attack-real-evidence/00-red.txt`, `01-green.txt`, `02-final-verification.txt`.

## Asset, license và bảo toàn nguồn

- Asset ngoài repo, chỉ đọc: `x01-attack-real-research-evidence/enterprise-attack-20.1.json`.
- 55.277.605 byte; SHA-256 `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`.
- LICENSE fixture có cùng SHA-256 với evidence gốc: `738144f7fb054722a4ef9d3367c51710341dc12fc574c6ac3a41daaaecd8bf5e`.
- Source `cti-x01-attack-offline` vẫn HEAD `4e894c37df3ad53c16022909ae6df113dd89aa04`, status sạch. Implementation status sạch.
- Import kiểm bằng interpreter dùng chung nhưng cwd tree mới; module trỏ đúng `cti-x01-attack-official\extractor\phonghoa_extractor\attack_catalog.py`.

Inventory nghiên cứu 26.699 object là bằng chứng riêng, không được dùng thay product test. Bằng chứng compatibility ở đây là ca asset thật gọi public `load_catalog`.

## UNVERIFIED / ngoài phạm vi

- Release ATT&CK khác; chữ ký cryptographic của tag/commit; tệp NOTICE riêng.
- Độ đúng ngữ nghĩa TTP, corpus hai người gán nhãn, model thật, C4/RAG và adapter wiring.
- OpenCTI, W05, UI, lab, runtime và production.
- Không gọi model/cloud, không chạy lab/VM, không đọc secret, không DB/listener/network, không push/PR/merge/deploy.

## Học thêm

- **Pin bất biến:** bộ metadata cố định buộc loader chỉ tin đúng release đã review, không tin URL có vẻ giống MITRE.
- **Fail-closed:** dữ liệu mơ hồ hoặc sai contract bị từ chối thay vì đoán và tiếp tục.
- **Compatibility test:** kiểm public API với bytes thật; khác inventory chỉ đếm và khảo sát cấu trúc dữ liệu.
