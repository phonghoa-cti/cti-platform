# PHONG HỎA — QA độc lập X01 ingest browser harness

Ngày 11/11/2026. Phạm vi: `X01-INGEST-BROWSER-HARNESS-QA`.

## Kết luận

**FAIL cổng hậu kiểm.** Snapshot `970a130452eb69bae3cd3793eab5a527b3d382d5` chưa đủ tin cậy để dùng `verify_browser_outcome()` làm bằng chứng cho ma trận browser cuối: có hai ca thay đổi tính toàn vẹn/định danh vẫn trả `PASS`, và bộ kiểm bundle chưa chứng minh đầy đủ yêu cầu không lộ evidence/tên nguồn.

- Phần chuẩn bị/offline: seed/import/duplicate/export và cleanup mục tiêu có bằng chứng cục bộ; không đồng nghĩa harness hậu kiểm đạt.
- Browser/end-to-end: **UNVERIFIED**; không mở browser hoặc demo listener trong lượt QA.
- OpenCTI/lab/cloud/model/production: **UNVERIFIED**.
- F1 importer cũ trên base không được ghi thành finding mới; bản sửa nằm ở tree khác và chưa ghép vào snapshot này.

## Ref và phạm vi bất biến

- Source chỉ đọc: `cti-x01-ingest-browser-prep`.
- Base: `db36ec01b765dfd515c1d0ef13642a693b777172`.
- HEAD/branch trước và sau: `970a130452eb69bae3cd3793eab5a527b3d382d5`, `feat/x01-ingest-browser-prep-20261111`.
- `git status --porcelain=v1`: rỗng trước/sau.
- Diff đúng 5 file; SHA-256 từng file nằm trong `x01-ingest-browser-harness-qa-evidence/refs-and-source-hashes.log` và không đổi sau probe.
- Dispatch đã đối chiếu SHA-256 `57ae0d0d77ba31504f1ed7a4b01ffb06170edcc85d272c09732525b263e3a690`.
- Chỉ ghi report này và `x01-ingest-browser-harness-qa-evidence/`; không sửa source/index/branch/RUNS/plan/evidence Engineer.

## Finding 1 — HIGH — envelope đổi nhưng hậu kiểm vẫn PASS

- **File:line:** `tools/local_integration/tests/run_ingest_browser_stix.py:65-74`.
- **Tình huống lỗi:** sau seed/approve, đổi một trường hợp lệ trong envelope (`input.display_name`) nhưng giữ nguyên `draft.source.sha256` và source file.
- **Repro:** chạy `probe_postcheck.py`; ca `envelope_display_name_changed`.
- **Lệnh/exit:** `.venv\Scripts\python.exe -X utf8 -B ..\x01-ingest-browser-harness-qa-evidence\probe_postcheck.py`; exit `0`; tổng `14` ca, `5` ca được verifier chấp nhận.
- **Expected:** verifier từ chối vì envelope trên đĩa không còn là envelope đã seed/import.
- **Actual:** `verify_browser_outcome()` trả `status=PASS`, STIX `4` object.
- **Nguyên nhân:** code so `provenance.envelope_sha256` với giá trị đã giữ trong `seed`, nhưng không tính lại canonical SHA-256 của envelope hiện tại; kiểm envelope trực tiếp chỉ nhìn `draft.source.sha256`.
- **Ảnh hưởng:** một artifact đầu vào đã bị thay đổi có thể được báo là cùng phiên ingest đã kiểm chứng.
- **Sửa tối thiểu:** dùng cùng hàm canonical digest của importer để tính lại toàn envelope trong hậu kiểm; so với cả `seed.envelope_sha256` và provenance. Thêm regression đổi một trường hợp lệ ngoài source hash và yêu cầu FAIL.

## Finding 2 — HIGH — định danh người lưu/duyệt có thể đổi đồng bộ và vẫn PASS

- **File:line:** `tools/local_integration/tests/run_ingest_browser_stix.py:41-63`; helper thiếu trường tại `tools/local_integration/tests/run_stix_e2e.py:50-68`; JWT browser mặc định là `admin-sub` tại `tools/local_integration/runner.py:336-375`.
- **Tình huống lỗi:** sau thao tác hợp lệ, đổi đồng bộ `drafts.decided_by_subject`, `draft_audit.actor_subject` và `draft_selection_audit.actor_subject` thành `other-reviewer-sub`.
- **Repro:** `probe_postcheck.py`, ca `all_review_actors_changed_to_other_reviewer`.
- **Expected:** verifier từ chối vì DB không còn ghi nhận subject mà phiên browser của harness phát hành (`admin-sub`).
- **Actual:** `PASS`, STIX `4` object. Ca chỉ đổi một phía final audit bị exporter từ chối, nhưng đổi đồng bộ ba phía vượt qua hậu kiểm.
- **Nguyên nhân:** `database_state()` chỉ trả payload/status/version, số lượng selection audit và năm trường final audit; không trả hoặc so actor. `verify_browser_outcome()` cũng hardcode kiểm chuỗi subject trong bundle thay vì xác minh subject thao tác trong DB.
- **Ảnh hưởng:** harness không chứng minh đúng người đã lưu/duyệt, làm yếu bằng chứng phân quyền và self-approve denial.
- **Sửa tối thiểu:** truyền `expected_actor_subject` vào verifier; đọc và so `drafts.decided_by_subject`, final-audit actor, toàn bộ selection-audit actor/action/version với subject browser kỳ vọng. Không hardcode `admin-sub` trong kiểm bundle.

## Finding 3 — MEDIUM — kiểm bundle thiếu điều kiện âm về evidence/tên nguồn

- **File:line:** `tools/local_integration/tests/run_ingest_browser_stix.py:81-125`, trọng tâm `95-107`.
- **Tình huống lỗi:** probe thay kết quả exporter bằng một bundle vẫn có hash/count/provenance hợp lệ nhưng thêm `x_leaked_source_name` và `x_leaked_selected_evidence`.
- **Repro:** `probe_postcheck.py`, ca `bundle_selected_evidence_and_source_name_leaked`.
- **Expected:** verifier từ chối theo brief: bundle không chứa raw source/evidence/source name/subject.
- **Actual:** `PASS`; verifier chỉ yêu cầu IOC đã chọn có mặt, IOC đã bỏ vắng mặt và hai subject cố định không xuất hiện.
- **Giới hạn bằng chứng:** probe này kiểm năng lực phát hiện regression của verifier; **không khẳng định exporter hiện tại đang lộ dữ liệu**.
- **Sửa tối thiểu:** parse cấu trúc bundle theo allowlist và kiểm vắng mặt source name/evidence/raw text ở mọi field; dùng fixture marker riêng để phân biệt IOC cần có với evidence không được phép có.

## Probe âm tính không thành finding

| Ca | Kết quả | Đánh giá |
|---|---|---|
| Sửa `payload_json` | REJECTED: `Provenance row không hợp lệ` | PASS fail-closed |
| Sửa `provenance.envelope_sha256` | REJECTED | PASS fail-closed |
| Xóa selection audit | REJECTED: count/action sai | PASS fail-closed |
| Xóa final audit | REJECTED | PASS fail-closed |
| Sửa final selected hash | REJECTED: JSON/hash không canonical | PASS fail-closed |
| Sửa final version hoặc chỉ một actor | STIX CLI thất bại | PASS fail-closed |
| Nhiều final audit | Schema chặn bằng `draft_id UNIQUE` tại `store.py:420-435` | Không biến `fetchone()` thành finding trong schema bất biến hiện hành |

`database_state()` dùng `fetchone()` cho final audit chưa phải lỗi độc lập vì schema v3 bảo đảm tối đa một row final audit cho mỗi draft. Ngược lại, selection audit có nhiều row hợp lệ theo version nên chỉ đếm row là chưa đủ để chứng minh nội dung/actor của audit.

## Deadline, EOF và cleanup

- Targeted pytest: `4 passed`, exit `0`:
  - ingest-browser seed vào API và cleanup resource sở hữu;
  - stdin `continue`/EOF/timeout;
  - cleanup tiếp tục sau lỗi child;
  - TTL đóng stack/temp.
- `wait_for_browser_signal()` phân biệt EOF và timeout, thread đọc là daemon (`run_ingest_browser_stix.py:139-156`).
- Browser session dùng `with LocalRun(...)` nên exception EOF/timeout đi qua `close()` (`run_ingest_browser_stix.py:257-295`, `runner.py:593-683`).
- Một lần chạy sơ bộ của probe QA exit `1` vì chính script probe giữ SQLite handle trên Windows; đã sửa probe để đóng handle và chạy fresh lại exit `0`. Source không bị thay đổi; kết quả kết luận chỉ dùng lượt fresh cuối.

## Coverage và cổng nối

| Tiêu chí | Kết luận | Bằng chứng/gap |
|---|---|---|
| Seed producer → importer, duplicate cùng DB | PASS cục bộ | Baseline probe thật qua hai CLI |
| Payload/provenance/hash sai bị từ chối | PASS một phần | Các probe âm tính trên |
| Envelope bất biến | FAIL | Finding 1 |
| Actor/audit đúng phiên browser | FAIL | Finding 2 |
| Bundle không lộ evidence/source name | FAIL năng lực chứng minh | Finding 3 |
| EOF/timeout/owned cleanup | PASS cục bộ | 4 targeted tests, exit 0 |
| Browser TXT same-run | UNVERIFIED | Không chạy browser trong QA |
| Browser PDF | UNVERIFIED/unsupported | `browser-session` chủ động từ chối PDF tại `run_ingest_browser_stix.py:257-261` |
| Self-approve/save-refresh/decision-refresh trong ingest scenario | UNVERIFIED | Chưa có cùng scenario; các scenario W05 cũ không thay thế bằng chứng ingest-browser |

**Quyết định cổng:** chưa nối harness này để tuyên bố ma trận browser đạt. Sửa Finding 1 và 2 trước; bổ sung kiểm âm bundle theo Finding 3 trước khi dùng hậu kiểm làm bằng chứng riêng tư. Sau đó mới ghép importer đã nghiệm thu trên tree tích hợp riêng và chạy ma trận TXT/PDF/self-approve/fault theo brief. QA không merge/cherry-pick/sửa implementation.

## Bằng chứng

- `x01-ingest-browser-harness-qa-evidence/probe-postcheck.log`
- `x01-ingest-browser-harness-qa-evidence/targeted-pytest.log`
- `x01-ingest-browser-harness-qa-evidence/refs-and-source-hashes.log`
- `x01-ingest-browser-harness-qa-evidence/probe_postcheck.py`
- `x01-ingest-browser-harness-qa-evidence/MANIFEST.sha256`

## Học thêm

- **Canonical digest:** hash được tính trên một biểu diễn JSON chuẩn, giúp phát hiện cả thay đổi hợp lệ về cú pháp lẫn nội dung.
- **Audit actor:** danh tính được ghi cùng sự kiện lưu/duyệt; phải khớp phiên đã thực hiện thao tác, không chỉ khớp giữa các bảng.
- **Negative assertion:** kiểm tra điều tuyệt đối không được xuất hiện, ví dụ evidence hoặc tên nguồn trong bundle STIX.
