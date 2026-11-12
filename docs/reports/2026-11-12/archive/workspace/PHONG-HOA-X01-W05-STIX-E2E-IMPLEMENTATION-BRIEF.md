# X01 → W05 → STIX E2E Offline Implementation Plan

> **Cho worker triển khai:** làm tuần tự theo TDD trong một worktree mới; không giao tiếp cho bot khác. Đây là brief implementation tự đủ, không phải bằng chứng test đã chạy.

**Mục tiêu:** Chứng minh một file text UTF-8 synthetic đi qua extractor C1 CLI thật → store CLI/SQLite → selection và approve qua HTTP gateway/API v1 → STIX export CLI trên cùng draft/DB, chỉ chứa IOC còn được chọn.

**Kiến trúc:** Tái dùng `LocalRun` làm chủ temp/JWT/API/gateway/process. Một scenario `stix-e2e` seed bằng ba CLI subprocess hữu hạn và một script ma trận điều phối HTTP + kiểm SQLite/bundle trước cleanup. Không mở rộng API/UI, không thêm importer/outbox/framework/dependency.

**Tech stack:** Python 3.12, `subprocess.run`, SQLite, httpx, FastAPI/uvicorn, Node gateway hiện có, STIX exporter hiện có.

**Spec:** `PHONG-HOA-X01-W05-STIX-E2E-NEXT-BRIEF.md`; `docs/specs/X01-ai-extractor.md`; `docs/specs/W05-duyet.md`; `docs/specs/W05-draft-offline-contract.md`; research đi kèm `PHONG-HOA-X01-W05-STIX-E2E-RESEARCH.md`.

## Exact base và worktree mới

- Source base readonly hiện tại: `cti-w05-stix-offline`, branch `feat/w05-stix-offline-20261111`, HEAD **`ed829a0344b2d3d4392fae933e41a9c44fdcd853`**; phải xác nhận source vẫn sạch và đúng SHA trước tạo tree.
- Worktree đề xuất, chưa tạo: `$WORKSPACE\cti-x01-w05-stix-e2e`.
- Branch đề xuất: `feat/x01-w05-stix-e2e-20261111`, tạo **từ exact HEAD trên**, không từ `main`.
- Một writer/working tree. Không sửa source tree, tree cũ, `PHONG-HOA-RUNS.json`, acceptance/review/result/evidence cũ.

## Ràng buộc toàn cục

- Không browser trong ma trận mới; review đi qua HTTP thật đến gateway/API v1. Bằng chứng browser selection đã được nghiệm thu riêng và không được nhập nhằng thành cùng-run browser E2E.
- Không tạo payload JSON bằng tay và không gọi `build_regex_draft()`/`save_draft()` trực tiếp để seed draft E2E. Phải gọi `extractor/draft/run.py`, rồi `extractor/draft/store.py save` bằng `sys.executable` và argv list, `shell=False`.
- Không thêm/chỉnh dependency hoặc lock. Không đổi store schema/migration, core mapping, API route/schema/auth, gateway allowlist/body cap, UI, exporter semantics, OpenCTI compose.
- Không gọi Internet, model, feed, OpenCTI, lab, cloud hoặc dữ liệu thật. Không ghi token/JWT/private key/reviewer subject/raw source vào evidence.
- Input synthetic duy nhất: `Cảnh báo thử nghiệm 😀 ghi nhận evil-one.example và evil-two.example.\n`, UTF-8, `language=vi`, `TLP:GREEN`; không sửa payload/source sau khi extractor tạo.
- Export phải hoàn tất và được kiểm **trước** `LocalRun.close()` xóa temp DB. Chỉ xóa file/temp/process do run sở hữu.

## File scope khóa

| File | Thay đổi được phép |
|---|---|
| `extractor/draft/store.py` | Thêm `save --created-by-subject`; truyền nguyên giá trị vào `save_draft`. Không đổi stdout success hiện có. |
| `extractor/tests/test_store_cli.py` | TDD cho subject synthetic được lưu và input subject lỗi fail trước write; giữ backward compatibility khi option vắng. |
| `tools/local_integration/runner.py` | Thêm scenario `stix-e2e`; helper CLI hữu hạn; tạo input/draft/config/output trong owned temp; expose path/draft ID cần cho matrix. Không đổi fixture scenario cũ. |
| `tools/local_integration/tests/test_runner.py` | TDD: scenario seed từ CLI, source/hash/Unicode/TLP/creator đúng; lifecycle/cleanup mới; scenario cũ không đổi. |
| `tools/local_integration/tests/run_stix_e2e.py` (mới) | Một ma trận tự chạy HTTP selection/approve, CLI export và invariant/hashes. |
| `tools/local_integration/README.md` hoặc README hiện hành tương ứng | Một lệnh chạy, mô tả CLI+HTTP, giới hạn không browser/OpenCTI. |
| `docs/PROGRESS.md` | Cập nhật đúng trạng thái local và phần UNVERIFIED; không ghi “W05 hoàn tất”. |

Không thêm ADR: đây là ghép các quyết định đã có, không tạo kiến trúc mới. Nếu implementation phát hiện phải sửa ngoài bảng, dừng tại blocker cụ thể và báo Leader; không tự mở scope.

## Interfaces phải giữ

```python
# extractor/draft/store.py CLI
store.py save --db PATH --input PATH [--created-by-subject SUBJECT] [--timeout SECONDS]
# stdout thành công giữ nguyên: {"id": INT, "status": "pending"}\n

# tools/local_integration/runner.py
LocalRun("stix-e2e", duration_seconds=30, start_ui=False)
# sau start:
run.selection_draft_id: int
run.source_path: Path
run.draft_json_path: Path
run.exporter_config_path: Path
run.bundle_path: Path
```

Nếu muốn tên thuộc tính khác, phải chốt nhất quán trong `runner.py`, `test_runner.py` và `run_stix_e2e.py`; không dùng private field mới từ matrix.

## Review focus

- CLI child timeout/nonzero/malformed stdout: start fail closed, không khởi động listener còn lại và cleanup owned temp.
- Unicode/hash/span: hash theo exact UTF-8 bytes, span theo Python string; không dùng newline/platform transform để tính lại khác nguồn.
- `created_by_subject`: vắng option giữ hành vi cũ; option synthetic hợp lệ được lưu; chuỗi rỗng/whitespace/quá dài hoặc sai kiểu không tạo DB row.
- Artifact phải xuất trước cleanup; exception ở HTTP/export vẫn chạy `__exit__` và dọn PID/listener/temp.
- Evidence chỉ summary/hash/count/path tương đối; không raw input, JWT/key hoặc subject.

---

### Task 1: CLI store nhận subject tạo draft

**Files:**
- Modify: `extractor/draft/store.py`
- Modify: `extractor/tests/test_store_cli.py`

**Produces:** CLI seed có thể tạo draft với `created_by_subject="e2e-author-sub"` mà không gọi library trực tiếp.

- [ ] **RED:** thêm `test_cli_save_accepts_created_by_subject_for_reviewable_draft`; chạy CLI `run.py`, rồi `store.py save --created-by-subject e2e-author-sub`; `get_draft(...)["review"]["created_by_subject"] == "e2e-author-sub"`. Thêm ca whitespace/subject không hợp lệ trả exit `1`, không traceback, không tạo row.
- [ ] Chạy: `.venv\Scripts\python.exe -X utf8 -B -m pytest -o addopts='' -q -p no:cacheprovider extractor/tests/test_store_cli.py`; expected RED vì option chưa tồn tại/subject chưa truyền.
- [ ] **GREEN:** thêm option chỉ cho subcommand `save`; gọi `save_draft(args.db, draft, created_by_subject=args.created_by_subject, timeout=args.timeout)`. Không thay JSON stdout, không log subject.
- [ ] Chạy lại file test; expected tất cả PASS, exit `0`.

### Task 2: Scenario seed bằng hai CLI thật và cleanup đúng ownership

**Files:**
- Modify: `tools/local_integration/runner.py`
- Modify: `tools/local_integration/tests/test_runner.py`

**Consumes:** CLI Task 1.

**Produces:** `LocalRun("stix-e2e")` có đúng một draft E2E từ file, cùng DB dùng cho API/export.

- [ ] **RED:** test scenario mới yêu cầu input bytes chính xác, draft JSON do CLI tạo, `selection_draft_id` từ stdout store CLI, creator `e2e-author-sub`, `source.sha256 == sha256(source_path.read_bytes())`, text Unicode/TLP GREEN/model C1/two eligible IOC/span đúng. Assert scenario legacy/selection cũ vẫn 4/5 fixture như trước.
- [ ] Thêm RED cho CLI child nonzero/timeout/malformed stdout: `start()` fail, không listener/process/temp owned còn lại. Mock đúng seam helper, không mock logic extractor ở happy test.
- [ ] Chạy: `.venv\Scripts\python.exe -X utf8 -B -m pytest -o addopts='' -q -p no:cacheprovider tools/local_integration/tests/test_runner.py`; expected RED.
- [ ] **GREEN:** scenario `stix-e2e` không tạo bốn fixture legacy; sau `TemporaryDirectory` được cấp, ghi source/config synthetic, dùng `subprocess.run([sys.executable, ...], cwd=ROOT, capture_output=True, text=True, encoding="utf-8", check=False, timeout=10, shell=False)`. Mọi nonzero/timeout/JSON sai thành lỗi start an toàn, không chèn stdout/stderr/raw input vào exception.
- [ ] Khởi động API/gateway sau khi seed thành công; roles/JWT dùng admin synthetic hiện có; không bật UI.
- [ ] Chạy lại targeted runner; expected PASS/exit `0`, rồi chạy `git diff --check`.

### Task 3: Ma trận cùng-run extractor → HTTP review → CLI STIX

**Files:**
- Create: `tools/local_integration/tests/run_stix_e2e.py`

**Consumes:** `LocalRun("stix-e2e")`, API v1, STIX CLI hiện có.

**Produces:** một JSON summary redacted trên stdout; exit `0` chỉ khi toàn bộ invariant đạt.

- [ ] **RED:** viết ma trận trước khi Task 2 GREEN hoàn tất. Trong context run, GET detail qua gateway và assert exact draft/source/hash/text/TLP/model/2 eligible; snapshot `payload_json`, input/draft file hash và inventory hash của DB + `-wal/-shm/-journal`.
- [ ] Gọi STIX CLI khi pending: exit `1`, stdout rỗng, stderr exact JSON safe hiện có, bundle không tồn tại.
- [ ] POST `/selection` với `expected_version=0, selected_indices=[1]`, Origin đúng `run.url`; assert version `1`, one selection audit. POST `/decision` approve với `expected_version=1`; assert review version `2`, final indices/hash; đúng one approve audit. Không gửi subject trong body.
- [ ] Gọi CLI `export-approved` bằng cùng DB/draft/config/output trước close; assert exit `0`, stdout chỉ `draft_id`, `bundle_sha256`, `object_count` và hash khớp bytes.
- [ ] Parse bundle: object types theo thứ tự `marking-definition, identity, domain-name, report`; domain đúng `evil-two.example`; deselected `evil-one.example`, raw Unicode source, evidence và subjects không xuất hiện trong bundle bytes. Report provenance JSON khớp `source_sha256`, `draft_id`, `approved_audit_id`, review `2`, selection `1/[1]/hash`, TLP GREEN.
- [ ] Assert `payload_json`/`items.keep` bất biến; input/draft/DB/sidecar inventory hashes không đổi bởi export. Re-run cùng target: exit `0`, bytes/hash/mtime không đổi. Tạo target phụ owned có bytes khác, export tới đó: exit `1`, bytes/hash/mtime giữ nguyên và không temp mồ côi.
- [ ] Chỉ stdout summary redacted dạng `{"status":"PASS","checks":N,"draft_id":N,"source_sha256":"...","bundle_sha256":"...","object_count":4}`. Không in raw source/IOC/JWT/key/subject/path tuyệt đối.
- [ ] Chạy trực tiếp: `.venv\Scripts\python.exe -X utf8 -B tools/local_integration/tests/run_stix_e2e.py`; expected PASS, exit `0`; sau context, exact temp root không tồn tại và gateway/API PID/listener owned đã dừng.

### Task 4: Regression, tài liệu và evidence

**Files:**
- Modify: `tools/local_integration/README.md` hoặc README hiện hành tương ứng
- Modify: `docs/PROGRESS.md`
- Evidence mới ngoài repo: `x01-w05-stix-e2e-evidence/`

- [ ] Chạy targeted, không lặp full suite theo thói quen:
  - `.venv\Scripts\python.exe -X utf8 -B -m pytest -o addopts='' -q -p no:cacheprovider extractor/tests/test_store_cli.py tools/local_integration/tests/test_runner.py extractor/tests/test_stix_export_cli.py`
  - `.venv\Scripts\python.exe -X utf8 -B tools/local_integration/tests/run_stix_e2e.py`
  - `.venv\Scripts\python.exe -X utf8 -B tools/local_integration/tests/run_selection_matrix.py` chỉ vì `runner.py` đổi; expected giữ `113 checks / 10 scenarios` hoặc báo số thực tế nếu suite thay đổi hợp lệ.
  - `.venv\Scripts\ruff.exe check extractor/draft/store.py extractor/tests/test_store_cli.py tools/local_integration/runner.py tools/local_integration/tests/test_runner.py tools/local_integration/tests/run_stix_e2e.py`
  - `.venv\Scripts\ruff.exe format --check` cùng file Python; `git diff --check`.
- [ ] Không chạy browser/UI build nếu UI không đổi. Tái dẫn acceptance browser cũ cho no-replay refresh; không gọi đó là lượt chạy mới.
- [ ] Evidence mới gồm exact commands, stdout/stderr redacted, exit codes, số test/check thật, Git before/after, source HEAD/status, bundle/source/DB-before-after hashes và manifest SHA-256. Không copy bundle/raw source/DB/JWT/key/subject vào evidence.
- [ ] Cập nhật docs: ghi rõ `PASS local CLI+HTTP` nếu và chỉ nếu lệnh mới PASS; giữ `UNVERIFIED browser same-draft/OpenCTI/lab/production`.
- [ ] Commit nhỏ theo Conventional Commits; tree sạch. Không push/PR/merge/deploy.

## Acceptance matrix

| Tiêu chí | Bằng chứng mới bắt buộc | PASS khi |
|---|---|---|
| Source thật | CLI command/exit + source/draft hash | Draft cùng run do `run.py` tạo; không payload tay/in-process seed |
| Store/identity | CLI save/SQLite read | Creator synthetic khác reviewer, không lộ trong artifact/evidence |
| Unicode/hash/TLP | GET detail + bytes/hash/span assertions | Exact UTF-8 hash/text/span; GREEN xuyên suốt source/config/marking/provenance |
| Selected subset | HTTP selection/approve + DB audit | `[0,1] → [1]`, versions `0→1→2`, đúng một selection và approve audit |
| Export | CLI stdout + bundle parse | Cùng draft/DB; chỉ `evil-two.example`; provenance/hash nối final audit |
| Fail closed | Pending + different output | Không output pending; existing different không đổi; không raw traceback/path |
| Read-only/idempotent | Hash inventory/mtime | Source/draft/DB/sidecars không đổi bởi export; identical re-export no write |
| Lifecycle | PID/listener/temp before/after | Chỉ owned resources, export trước cleanup, sau close không còn owned resource |
| Regression | Targeted counts/exits | Store/runner/STIX CLI/selection matrix và Ruff/diff đều exit `0` |

## Giới hạn phải báo nguyên văn khi bàn giao

Kết quả này, nếu PASS, chỉ chứng minh **local CLI + HTTP gateway/API + SQLite + STIX file** trên fixture synthetic. Nó không chứng minh browser cùng draft, OpenCTI import/workbench, reviewer-to-Identity thật, Cloudflare/JWKS/HTTPS thật, X01 quality/metrics C2–C4, dữ liệu thật, network share/crash, lab, deploy hay production. Nghiên cứu và validator không phải bằng chứng đã chạy integration hoặc đã ingest OpenCTI.

## Hoàn tác

- Trước merge: bỏ worktree/branch mới theo quy trình owner sau khi evidence đã bàn giao; không đụng source tree.
- Sau commit local: dùng `git revert <SHA>` trên branch, không `reset --hard` và không xóa evidence cũ.
