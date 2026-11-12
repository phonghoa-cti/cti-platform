# X01 ATT&CK thật — implementation brief

Trạng thái: sẵn sàng giao **một** worker CTI AI Agent/Sol medium sau review Leader. Đây là compatibility offline tối thiểu; không mở C4/RAG/adapter/model/W05/OpenCTI/UI/lab.

## Mục tiêu và base

Từ base `4e894c37df3ad53c16022909ae6df113dd89aa04`, tạo worktree/branch mới (đề xuất `feat/x01-attack-official-20261111`) và làm cho `load_catalog()` đọc được snapshot MITRE Enterprise v20.1 nguyên bytes từ local path với official pin, đồng thời giữ toàn bộ synthetic test/hành vi cũ.

Source đang có: `$WORKSPACE\cti-x01-attack-offline`. Dùng interpreter `$WORKSPACE\cti-platform-start\.venv\Scripts\python.exe`; không cài dependency.

## Pin/asset canonical

| Trường | Giá trị bắt buộc |
|---|---|
| `kind` | `official` |
| `provenance` | `mitre-attack-stix-data` |
| `version` | `20.1` |
| `sha256` | `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5` |
| `source_url` | `https://raw.githubusercontent.com/mitre-attack/attack-stix-data/f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7/enterprise-attack/enterprise-attack-20.1.json` |
| `release_tag` | `v20.1` |
| `commit` | `f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7` |
| file | 55,277,605 bytes, `enterprise-attack-20.1.json` |

Worker chỉ nhận asset qua path offline do người vận hành cung cấp; **không thêm HTTP/TAXII/download CLI, không lookup mạng**. Không commit 55 MB snapshot vào repo trừ khi Leader có quyết định riêng về artifact storage/licensing. Phân phối asset phải kèm LICENSE.txt nguyên văn từ cùng commit; `NOTICE` file riêng chưa xác minh nên không tuyên bố có.

## File scope và thay đổi nhỏ nhất

- Sửa `extractor/phonghoa_extractor/attack_catalog.py` và `extractor/tests/test_attack_catalog.py`.
- Thêm fixture metadata/pin nhỏ và README/manifest cho asset ngoài repo nếu cần; cập nhật một ADR hoặc `docs/PROGRESS.md` theo AGENTS. Không sửa adapter/eval/grounding/store, lock/dependency, RUNS hay code UI/API.

Mở rộng `_validate_pin` theo discriminated union, trước mọi I/O:

1. Synthetic: giữ đúng contract hiện tại — generator/provenance fixture và `source_url`/tag/commit `None`.
2. Official: exact `kind`/provenance; ASCII/control-free bounds; SHA lowercase 64 hex; URL HTTPS đúng `raw.githubusercontent.com/mitre-attack/attack-stix-data/<40-commit>/...`; tag `v` + version; commit lowercase 40 hex và phải khớp commit trong URL. Missing/sai kiểu/metadata mismatch => `invalid_pin` trước file I/O.
3. `_validate_bundle`: branch theo validated pin. Với official chỉ cần STIX bundle + `objects`; không thêm/sửa `x_phonghoa_provenance`. Với synthetic giữ check root provenance cũ.

Giữ `_read_snapshot`: binary read `max_bytes+1`, hash bytes exact trước UTF-8/JSON; default bound 64 MiB. Error taxonomy cũ, immutable mappings, strict bool-vs-number JSON equality, timestamp precision, canonical lifecycle và graph không được yếu đi. Chỉ ghi chú/document official branch; không tự bỏ unknown/malformed record để pass.

## Test matrix / acceptance

1. RED trước code: valid official pin + real asset hiện phải `invalid_pin`; metadata official sai từng field thất bại **trước I/O** (marker path); synthetic regression vẫn pass.
2. GREEN: real asset + pin canonical tạo catalog; assert lookup `T1001` active, `T1001.001` active/subtechnique có parent, một ID inventory inactive (ví dụ `T1002`) inactive, ID syntax-valid không có unknown, invalid syntax not_checked. Chỉ đây là product compatibility evidence.
3. Check actual hash mismatch, > bound (không cần tạo 64MiB fixture; inject/bounded local fixture), official root không có custom provenance accepted, synthetic root thiếu provenance rejected, duplicate/parent/lifecycle regressions 104 test hiện có còn xanh.
4. Assert no network through design (không import HTTP client/no new dependencies); asset supplied local. Verify full source branch diff does not add `requests`, `taxii`, `stix2` or downloader.
5. Run targeted pytest + ruff check/format on changed Python. Check `git diff --check BASE..HEAD`, `git status --short`, source/base SHA. Report tests/exit fresh, asset SHA/byte count, license artifact path and manifest.

Suggested commands (run only from new worktree):

```powershell
& '..\cti-platform-start\.venv\Scripts\python.exe' -X utf8 -B -m pytest -o addopts='' -p no:cacheprovider extractor/tests/test_attack_catalog.py -q
& '..\cti-platform-start\.venv\Scripts\ruff.exe' check extractor/phonghoa_extractor/attack_catalog.py extractor/tests/test_attack_catalog.py
& '..\cti-platform-start\.venv\Scripts\ruff.exe' format --check extractor/phonghoa_extractor/attack_catalog.py extractor/tests/test_attack_catalog.py
git diff --check 4e894c37df3ad53c16022909ae6df113dd89aa04..HEAD
git status --short
```

## Bằng chứng phải trả / UNVERIFIED

Trả commit/branch/base, diffstat, commands/exit/test count, exact downloaded asset byte+SHA, pin metadata, license/NOTICE disposition and an inventory clearly labeled separate from test. Do not claim semantic correctness of a TTP because code exists in catalog; all lookup result must remain `semantic_status="unverified"`, `operational_draft_eligible=false`.

Chưa được kiểm chứng sau bước code: C4/RAG wiring, model/corpus/TTP accuracy, W05/OpenCTI/UI/lab/production, release-tag cryptographic verification and snapshot updates beyond v20.1.
