# X01-GOLD-DATASET-NEXT — chuẩn bị pilot dữ liệu có nguồn

Ngày đối chiếu: 11/11/2026 (Asia/Saigon). Nghiên cứu/brief duy nhất: không tạo target, code, test, commit, corpus raw, model, network asset hay lab. Source chỉ đọc `cti-x01-c4-eval` tại `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`; status sạch trước khi đọc.

## Kết luận

**Giữ phương án 3:** triển khai lát offline `gold-pilot-v1`: validator/readiness report cho inventory 5 record và tối đa hai annotation/record. Nó tái dùng normalizer IOC và ATT&CK catalog đã nghiệm thu, không sửa C1–C4, không tạo gold, không benchmark model. Chỉ sau pilot có raw được phép lưu, hai nhãn người thật và adjudication riêng mới xét scorer semantic/corpus thật.

## Gap và nguồn

| Hiện trạng | Bằng chứng | Gap / tái dùng |
|---|---|---|
| GUIDELINE có raw + source metadata, labels IOC/TTP và pilot hai người. | `extractor/dataset/GUIDELINE.md:5-10,13-35` | Thiếu rights, span/quote, pin, trạng thái thiếu dữ liệu, adjudication. |
| C1 chỉ nhận synthetic smoke. | `extractor/eval/run.py:190-191,281-309` | Bảo vệ C1 khỏi corpus thật; không có readiness corpus. |
| Catalog thật có sẵn. | `attack_catalog.py:17-24,517-567` | Reuse `SnapshotPin`, `load_catalog`, `validate_technique`; không parser STIX thứ hai. |
| TTP audit unverified. | README evaluator/ADR 0009 | `active` chỉ chứng minh ID catalog, không chứng minh semantic. |

[TRAM](https://github.com/center-for-threat-informed-defense/tram), [Data Annotation](https://github.com/center-for-threat-informed-defense/tram/wiki/Data-Annotation) và [Best Practices](https://github.com/center-for-threat-informed-defense/tram/wiki/Data-Annotation-Best-Practices-Guide) phân biệt pilot luyện tập có thể thảo luận với double annotation đo agreement phải độc lập, sau đó adjudication. Apache-2.0 của code TRAM không cấp quyền raw report. [ATT&CK STIX Data](https://github.com/mitre-attack/attack-stix-data) là catalog pin-able, không là corpus/gold. Không tải CTI-Bench/TRAM/raw; public link không là quyền sao chép raw.

## Contract `gold-pilot-v1`

### Inventory và metadata

Root local có đúng `manifest.json`, `records/`, `annotations/`, `raw/`, optional `.gitignore`; `adjudications/`/`suggestions/` chỉ directory rỗng. Không nested directory, reparse/symlink/junction/hardlink/orphan/entry lạ. Max 22 regular files/8 MiB; JSON 256 KiB, raw 512 KiB, gitignore 4 KiB. Bounded read max+1, UTF-8 strict, no BOM/duplicate key/non-finite/recursion, exact types.

Manifest exact keys: `schema_version="gold-pilot-v1"`, `dataset_id` ASCII `[a-z0-9][a-z0-9-]{0,63}`, `purpose="human-annotation-pilot"`, `provenance` (`synthetic-fixture|human-supplied`), `document_count=5`. Report reflects provenance. Synthetic fixture may use only synthetic pin; human-supplied requires official pin. Fixtures are fake, not two people/corpus gold.

Each metadata exact fields: schema/id; `source={url,publisher,published_date,retrieved_at,source_license,storage_right}`; language `vi|en`; TLP CLEAR/GREEN; `raw={present,sha256}`; `duplicate_group`; optional `translation_of`; `split="pilot"`; `attack={version,sha256}`. URL https <=2048, publisher <=256; dates valid YYYY-MM-DD, `published<=retrieved`, no clock. Licences: public-domain|cc-by-4.0|cc-by-sa-4.0|publisher-permission|unknown. Rights: repo-allowed|local-only|link-only|prohibited. Prohibited/TLP outside allowlist INVALID; unknown=>link-only. Link-only=>absent/null/no annotation; local/repo allowed raw absence is NOT_READY.

`translation_of` must point to existing distinct original in same group, no chain/cycle. Duplicate detection is declared-only; pilot has no dev/holdout and makes no leakage claim.

### Annotation, evidence, catalog

0–2 annotations/record named `<id>.<annotator_id>.json`; wrong filename/id, orphan, >2, duplicate annotator INVALID. Missing valid annotation NOT_READY. Two IDs do not prove independence. Annotation exact fields schema/id/annotator_id/annotated_at/`attack_version`/raw_sha256/iocs/ttps/optional no_findings; `annotated_at>=retrieved`; no_findings true iff both lists empty.

Raw canonical form converts CRLF/CR to LF only; reject NUL/lone surrogate. IOC evidence is exact IOC token span (possibly defanged), not sentence: substring must pass `phonghoa_core.ioc.normalize(raw: str) -> Ioc` and equal normalized declared type/value. Do not apply operational allowlist; role is human claim. TTP evidence only validates UTF-8/LF/code-point span/hash; semantic stays unverified. Duplicate evidence within item invalid; overlap between items allowed.

CLI requires snapshot and pin. Pin strict <=16 KiB exact seven-field `SnapshotPin`; reuse DTO, `load_catalog(snapshot,pin)` (64 MiB cap), then `validate_technique`. `attack.version==pin.version`, `attack.sha256==pin.sha256`. Malformed/unknown/inactive TTP INVALID. Parent/sub are distinct, no parent inference. Official current asset support is v20.1 only; do not promise all releases.

### States/fingerprint/boundary

Closed record reasons, sorted: `NEEDS_RIGHTS`, `NEEDS_LOCAL_RAW`, `NEEDS_SECOND_ANNOTATION`, `NO_FINDINGS_ONLY`. Agreement only for raw+rights+catalog+two valid annotations; otherwise unavailable, not 0/both-empty. Eligible records report attacker IOC triple and exact-TTP Jaccard; empty/empty = both_empty ratio null. READY iff all five eligible and at least one union finding; otherwise NOT_READY report/exit 2. No 80% gate.

`dataset_input_sha256` is SHA-256 of compact UTF-8 JSON `[relative_posix_path,sha256(original_file_bytes)]` for all accepted files sorted lexically, no LF. Report also hashes pin bytes/snapshot. It never renders raw, quote, IOC, URL, publisher, annotator, path or exception. PASS later means mechanics only; UNVERIFIED rights, independence, semantic truth, gold, model/RAG, cloud/lab/UI/OpenCTI/production.
