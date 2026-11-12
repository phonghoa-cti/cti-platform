# W05 — nghiên cứu snapshot approved → STIX ngoại tuyến (R1–R6)

Ngày kiểm: 11/11/2026 ICT. Đây là nghiên cứu/brief, không phải implementation hay test PASS.

## Hiện trạng đúng ref

Nguồn chỉ đọc: `cti-w05-selection-integration`, branch `feat/w05-selection-integration-20261111`, HEAD `d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2`; `git status --short` rỗng trước rework. Store v2 có payload immutable, review/audit, selection audit và helper canonical. `draft_audit` final ghi `selected_indices_json`/`selected_sha256` cùng approve. Đây là **nguồn quyền export duy nhất**: không lấy `items.keep`, selection client hay current selection pointer sau approved.

`source.sha256` là hash UTF-8 text theo W05 contract; payload integrity là kiểm/giải mã payload + metadata SQLite; `selected_sha256` là hash JSON canonical indices. Ba giá trị khác nhau và không chống quản trị viên có quyền sửa DB.

## Phương án và quyết định

| Cách | Kết luận |
|---|---|
| Converter CLI read-only → bundle file | **Chọn**: tái dùng store/core/fixture, test offline, không secret/network. |
| Outbox durable | Hoãn: thêm schema/write/retry/retention/quyền. |
| ImportFileStix/OpenCTI | Hoãn task riêng: cần lab, token, workbench, connector/policy/dedup. |

## Nguồn chính thức (truy cập 11/11/2026)

| Nguồn | Áp dụng |
|---|---|
| [OASIS STIX 2.1](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html), §§2.9,3.4,4.5,6,7.2.1.4,8 | Bundle là container; SCO ID deterministic chuẩn; SDO/Bundle UUIDv5 là ngoại lệ SHOULD cho v4; Identity/marking refs phải đúng literal. |
| [FIRST TLP 2.0](https://www.first.org/tlp/) | CLEAR/GREEN/AMBER/RED/AMBER+STRICT; TLP không tự cấp quyền export/upload. |
| [OpenCTI import files](https://docs.opencti.io/7.260512.0/usage/import-files/) | ImportFileStix/workbench là pha sau converter. |
| [OASIS validator](https://github.com/oasis-open/cti-stix-validator), [best practices](https://stix2-validator.readthedocs.io/en/latest/best-practices.html) | Validator non-normative; check 103 liên quan UUID. Release/CLI `3.3.2` chưa xác minh lượt này. |

## Profile artifact đã chốt

### Snapshot read-only

`get_approved_export_snapshot()` mở SQLite URI `mode=ro`, **`BEGIN` trước mọi PRAGMA/schema/data read cần nhất quán**, kiểm `user_version=2`, `_validate_current_schema()`, decode `drafts`, và đúng một `draft_audit` approve final. Verify review version/time/actor, canonical indices/hash, indices subset eligible và selection version/event. Mọi mismatch, v1/legacy, pending/rejected, missing/duplicate final audit, empty selection hoặc corrupt DB đều fail closed; không migrate/ghi DB.

### Tám IOC, không suy diễn intelligence

Tạo **Report + SCO + exporter Identity + standard marking-definition**. Không Indicator, Pattern, Observed Data, relationship. Report `object_refs` gồm SCO + Identity; provenance final audit nằm manifest ngoài STIX, không raw subject/email.

| Core `IocType` (`ioc.py:17-25`) | SCO |
|---|---|
| ipv4, ipv6 | `ipv4-addr:value`, `ipv6-addr:value` |
| domain, url, email | `domain-name:value`, `url:value`, `email-addr:value` |
| md5, sha1, sha256 | `file:hashes.'MD5'`, `'SHA-1'`, `'SHA-256'` |

`sha512`, kind không IOC/type lạ: fail. Dedup `(type, normalized value)`, first final index wins. Không raw text/evidence/findings/reviewer subject/reason/secret.

### TLP và identity

Standard marking: `spec_version:2.1`, `created:2017-01-20T00:00:00.000Z`, `definition_type:"tlp"`, definition lower-case. IDs (prefix `marking-definition--`): WHITE `613f2e26-407d-48c7-9eca-b8e91df99dc9`, GREEN `34098fce-860f-48ae-8e50-ebd3cc5e41da`, AMBER `f88d31f6-486f-44da-b317-01333bde0b82`, RED `5e57c739-391a-4eb3-b6be-7d15ca92d5ed`. Mark Identity/SCO/Report.

CLEAR → WHITE only with manifest `source_tlp:"TLP:CLEAR"`, `stix_tlp:"TLP:WHITE"`; GREEN/AMBER/RED one-to-one; AMBER+STRICT reject. Artifact local không cấp quyền share/import.

Exporter config tin cậy qua `--exporter-config PATH`, schema exactly `{ "schema_version":"1", "id_namespace_uuid":"…", "name":"…", "identity_class":"organization", "created":"…", "tlp":"…" }`. Validate trước DB; identity ID includes canonical full-config hash. Đây không phải reviewer author; manifest chỉ giữ `reviewer_subject_sha256` + audit ID để OpenCTI future map nội bộ.

### IDs, times, validator profile

SCO IDs: OASIS SCO algorithm, canonical JSON ID-contributing properties + OASIS SCO UUIDv5 namespace. SDO Report/Bundle dùng project UUIDv5 namespaces riêng; Identity namespace thứ ba + config hash. Name includes export schema version, payload canonical SHA, `source.sha256`, draft/audit ID, final selection SHA, IOC type/value, marking ID, exporter config hash. Report/Bundle time = `decided_at`; Identity created = config; marking created = standard.

UUIDv5 SDO/Bundle là explicit OASIS SHOULD exception, không MUST failure. Profile validator sau implementation: MUST/schema/ref đầy đủ; profile riêng **“strict except 103”** chỉ sau khi xác minh release `3.3.2`/CLI/option. Test riêng UUID version/namespace/SCO properties/collision. Không gọi đó là strict nguyên vẹn.

### Publish

Build/validate bytes in memory. Target absent → atomic non-clobber publish; existing identical → success no write; existing different → error untouched. No force/replace. Guard DB và `-wal/-shm/-journal`, samefile/hardlink/symlink alias/directory. Temp same parent, exclusive creation, flush/fsync, cleanup owned temp. Windows race cần exclusive-create primitive/test concurrency; no delete other temp. Network/reparse/crash durability unverified; hỗ trợ local writable NTFS trước.

## Reuse/gap và giới hạn

Reuse store helpers, `phonghoa_core.ioc`, fixture conventions, candidate pin `stix2-validator==3.3.2`. Add final-audit getter, serializer/config/publisher/tests; test requirements input/lock hashes after implementation. Chưa cài/chạy validator/test, xác minh release/hash, OpenCTI/lab, Windows race/crash. Validator PASS không chứng minh CTI correctness, sharing authority hay OpenCTI import.
