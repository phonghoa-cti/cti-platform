# Brief triển khai — W05-B: quyết định cục bộ và audit cho draft SQLite

**Leader quyết định 10/11/2026:** chọn phương án B. Phần bổ sung cuối brief chốt các điểm còn tùy chọn và được ưu tiên khi khác đề xuất bên dưới. Brief sẵn cho bước triển khai kế, chưa phải xác nhận Engineer đã được giao W05.

**Phân công mới cùng ngày:** CTI Backend là người triển khai, trên `cti-w05-backend` cùng thư mục cha với brief, branch `feat/w05-local-review-20261110`, đã tạo từ e83bb3f. Không sửa `cti-platform-start`. Interpreter dùng đường dẫn tuyệt đối `cti-platform-start/.venv/Scripts/python.exe` nhưng cwd/PYTHONPATH phải ở tree backend (`pytest.ini` đã đặt core/extractor theo cwd). Leader đã chạy baseline mới: 236 passed, exit 0 trên tree backend. Không cần chạy lại baseline chưa thay đổi. Guard điều phối không phải dependency mã W05; được triển khai W05 song song với việc Engineer sửa guard. Việc UI do CTI Frontend riêng; không viết UI trong task này. Các chỉ dẫn cũ tạo branch trong `cti-platform-start` được thay bằng tree/branch đã chuẩn bị ở đây.

## Mục tiêu và người dùng

**Mục tiêu:** một Analyst/Admin đã được caller tin cậy biểu diễn bằng `Actor` có thể duyệt cục bộ hoặc từ chối một draft SQLite `pending` đúng một lần; kết quả state và audit cùng thành công hoặc cùng rollback.
**Người dùng hiện tại:** Engineer viết lõi Python offline và test; chưa có người dùng portal/UI.
**Không làm:** HTTP/FastAPI, Cloudflare Access/JWT/API key, UI, Antigravity, OpenCTI/STIX import, LLM, cloud, lab, secret, push/PR/merge/deploy.

## Base và hiện trạng bắt buộc xác minh trước khi sửa

- Repo/branch/base: `cti-platform-start`, `feat/x01-draft-queue-20261110`, base `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`.
- Chạy `git rev-parse HEAD` và `git status --short --branch`; nếu khác base hoặc có sửa đổi ngoài task, giữ nguyên và báo Leader trước khi sửa. Không checkout/reset.
- Đọc lại: `AGENTS.md`, `docs/PROGRESS.md`, `docs/specs/W05-duyet.md`, `docs/specs/W05-draft-offline-contract.md`, `docs/specs/api-portal.md`, `extractor/phonghoa_extractor/store.py`, `extractor/tests/test_store.py`, `extractor/tests/test_queue.py`.
- Nghiên cứu quyết định: `PHONG-HOA-W05-NEXT-RESEARCH.md` (10/11/2026). OpenCTI là tham chiếu lifecycle, **không** là dependency/API cho task này.

## Quyết định kỹ thuật phải giữ

1. Payload draft 1.0 (`payload_json`, `schema_version`, payload `status="pending"`) là evidence bất biến. Không sửa payload, không ghi `approved` vào payload `status`, không cập nhật `source.sha256`, `text`, item/evidence/findings.
2. State review độc lập: `review_status ∈ {pending, approved, rejected}`, `review_version` tăng từ 0 lên 1 đúng lúc quyết định. “approved” hiển thị/ghi chú là **đã duyệt cục bộ, chưa nhập OpenCTI**.
3. Danh tính trong core là `Actor(subject: str, roles: frozenset[str])`, `subject` opaque non-empty. Chỉ role `analyst`/`admin`; không tự duyệt nếu `created_by_subject` biết và trùng subject. Đây là policy testable, không có nghĩa client đã xác thực.
4. Legacy pending 1.0: `created_by_subject=NULL`, `review_status=pending`, `review_version=0`. Không approve draft có creator unknown; reject với lý do được phép. Không tự backfill/gán email/tên.
5. `reject` bắt buộc reason string non-empty sau trim; approve không tạo OpenCTI outbox hay gọi mạng. Cùng `draft_id` và `expected_version`, quyết định lặp hoặc stale phải lỗi conflict và không thay state/audit.
6. Bật `PRAGMA foreign_keys=ON` trên mọi connection ghi **trước** `BEGIN`; `BEGIN IMMEDIATE` → validate row/policy/version → update conditional + insert audit → commit. Bất kỳ lỗi nào rollback cả hai.
7. Audit chỉ giữ metadata review (draft id, action, timestamp UTC ISO 8601 timezone, actor subject, version, before/after state, reason khi reject); **không** copy text/evidence/findings/payload nguyên văn vào audit. Ghi rõ đây chưa phải audit chống sửa file DB.

## File được phép sửa

| File | Thay đổi dự kiến |
|---|---|
| `extractor/phonghoa_extractor/store.py` | Migration có version, types/errors API review, schema SQLite, read/list metadata review, transaction decision+audit. Giữ API save/get/list hiện hữu tương thích tối đa. |
| `extractor/tests/test_review.py` | Test-first cho migration, policy, transition, optimistic concurrency, atomic audit/rollback và legacy. |
| `extractor/tests/test_store.py` | Chỉ điều chỉnh assertion bị thay đổi có chủ ý bởi metadata review; giữ nguyên test integrity cũ. |
| `extractor/tests/test_queue.py` | Chỉ điều chỉnh/viết thêm để chứng minh list chỉ pending-review và summary không lộ report content. |
| `docs/specs/W05-draft-offline-contract.md` | Cập nhật hợp đồng metadata review/migration/semantic “duyệt cục bộ”; không gọi nó là HTTP/OpenCTI. |
| `docs/specs/api-portal.md` | Chỉ sửa phần đề xuất W05 để phân biệt local core với endpoint tương lai và auth production. |
| `docs/PROGRESS.md` | Ghi đúng phần đã kiểm và khoảng trống HTTP/auth/UI/OpenCTI còn lại. |

Không tạo portal, connector, migration framework tổng quát, dependency cloud hay file `.env`. Nếu cần đổi file ngoài bảng, dừng và báo Leader lý do.

## Giao diện lõi đề xuất

Tên chính xác có thể điều chỉnh cho phù hợp style repo, nhưng phải giữ hành vi:

```python
@dataclass(frozen=True)
class Actor:
    subject: str
    roles: frozenset[str]

def decide_draft(
    db_path: str | Path,
    draft_id: int,
    *,
    actor: Actor,
    decision: Literal["approve", "reject"],
    expected_version: int,
    reason: str | None = None,
    timeout: float = 5.0,
) -> DraftReviewResult: ...
```

- Có thể mở rộng `save_draft(..., created_by_subject: str | None = None)` theo cách backward-compatible để draft mới có authorship. Không đổi payload 1.0. Nếu không kịp nối tác giả lúc save, báo rõ chứ không phát minh creator.
- `get_draft()` trả payload cũ cộng một object metadata có tên không đụng key payload, ví dụ `review`; `list_drafts()` summary thêm `review_status` và `review_version`. Cập nhật contract/test đồng thời.
- `DraftStoreError` phải cho người gọi phân biệt ít nhất: invalid input/policy/unknown draft/conflict/SQLite error qua message hoặc subclass/code ổn định; không lộ `payload_json` hay text lỗi.

## Migration tối thiểu

1. Dò `PRAGMA user_version`. Với DB mới, tạo schema đã có review fields/tables; với DB cũ version 0, migrate trong một transaction.
2. Thêm metadata review vào `drafts` (hoặc một bảng one-to-one có FK) và bảng `draft_audit`; có unique/FK/index cần thiết. Thiết kế phải biểu diễn tối đa một quyết định cuối cho một draft.
3. Backfill tất cả row cũ thành legacy nêu trên. `payload_json` byte/nội dung logic và ID/created_at/source hash phải giữ nguyên.
4. Chỉ set `user_version` sau DDL/backfill thành công. Lần mở/migrate thứ hai không đổi records/audit.
5. Không xóa DB, không scan/sửa `.env` hay database ngoài `tmp_path` của test.

## Acceptance criteria và kiểm lỗi bắt buộc

| Tiêu chí | Bằng chứng test tối thiểu |
|---|---|
| Cơ sở cũ vẫn đọc/list đúng | Tạo DB theo schema 1.0/legacy, migrate, `get` trả payload/hash/span nguyên vẹn; list còn thấy row pending. |
| Migration an toàn/idempotent | Migration lần hai không đổi metadata/audit; lỗi DDL/backfill bị inject rollback toàn bộ; `user_version` không báo đã nâng nếu thất bại. |
| Quyền policy | `it`, role rỗng, subject rỗng bị từ chối trước write; analyst/admin được; self-approval với creator đã biết bị từ chối; legacy unknown bị chặn approve. Khẳng định trong doc: đây không kiểm JWT/header. |
| Transition + reason | approve/reject từ pending thành công một lần; reject trống/whitespace bị từ chối; approve không gọi network/OpenCTI (test monkeypatch nếu có đường gọi ngoài). |
| Atomicity/audit | Success có đúng 1 audit metadata phù hợp. Inject lỗi `INSERT audit` hoặc commit → state/version/audit không nửa chừng; audit không chứa source text/evidence/findings. |
| Race/stale version | expected version cũ, state khác pending, quyết định lần hai đều conflict và không thêm audit; test hai connection/lock với timeout hữu hạn, không retry loop. |
| Queue/read không rò nội dung | list chỉ review pending, có `review_status`/version cần thiết và không chứa text/items/evidence/findings; get metadata hợp lệ. |
| Regression | Test hiện có `test_store.py`, `test_queue.py`, test mới review đều pass; lint/format theo Makefile/repo nếu môi trường sẵn sàng. |

## Cách thực hiện và báo cáo

1. Viết `test_review.py` đỏ trước, bao phủ từng hàng acceptance. Không chạy Internet/lab.
2. Thêm migration + model/state query nhỏ, rồi transition/audit transaction. Không trộn HTTP/UI.
3. Cập nhật contract/PROGRESS sau khi code/test phản ánh hành vi thật.
4. Chạy test tập trung trước, rồi `make test`, `make lint` và formatter/check phù hợp theo `AGENTS.md`. Báo từng lệnh, exit code, số test, ref/commit và file evidence; nếu một lệnh không chạy, ghi `UNVERIFIED` và lý do.

## Bàn giao và bước sau nghiệm thu

- Đầu ra Engineer: commit, diff, kết quả test/lint thật, migration behavior, contract paths, và danh sách điều **không** chứng minh (HTTP/JWT/UI/OpenCTI/lab).
- QA sau Engineer tập trung: legacy migration, audit rollback, stale/concurrent decision, self-approval, không lộ report content trong audit/list, và xác nhận code không có network/OpenCTI call.
- Khi B được nghiệm thu, lát cắt kế là **API đọc có xác thực thật**: JWT Access xác minh signature/issuer/audience hoặc API-key hash, role lookup server-side, 401/403, rồi handoff UI. Không mở endpoint approve trước khi adapter identity được kiểm.

## Chốt của Leader sau review — ưu tiên hơn phần đề xuất

Leader đã đối chiếu source tại e83bb3f, spec W05, CLI `extractor/draft/store.py` và nguồn gốc [OpenCTI draft](https://docs.opencti.io/latest/usage/draftWorkspaces/), [SQLite transaction](https://sqlite.org/lang_transaction.html), [SQLite foreign key](https://www.sqlite.org/foreignkeys.html). Không coi hành động approve cục bộ là ingestion OpenCTI. Đây là bước lõi được phép tiếp tục ngoại tuyến theo yêu cầu hiện hành, không cần người dùng duyệt lại mỗi file; giữ mọi giới hạn phát hành của brief.

1. **Tác giả mới là bắt buộc triển khai:** thêm `save_draft(..., created_by_subject=None)` tương thích caller cũ. Không được bỏ qua nhánh này vì nếu mọi draft thiếu tác giả thì không có demo approve hợp lệ. Caller tin cậy cung cấp subject; không thêm cờ CLI giả làm đăng nhập. Legacy/null không được approve, reject có lý do vẫn được. Chặn tự approve kể cả admin; reject của chính tác giả được phép nếu role hợp lệ. Không có bypass role cho máy/agent.
2. **Read-only giữ nguyên:** get/list không migration và không ghi DB trong cả schema cũ/mới. Legacy chưa migration được đọc với metadata review mặc định pending/0/creator null, không sửa file. Có hàm migration rõ cho DB đã tồn tại; save là đường ghi có thể chuẩn bị schema mới/migrate trong transaction. `decide_draft` mở DB đã tồn tại và yêu cầu schema review đúng phiên bản; DB cũ phải migrate trước, thiếu DB không tự tạo. Phiên bản tương lai hoặc schema hỏng bị từ chối, không tự sửa.
3. **Payload và trạng thái không lẫn:** payload.status vẫn pending của kết quả trích xuất; `review.status`/version là quyết định cục bộ. get/list/CLI stdout phải nêu rõ trường review khi có quyết định, không chỉ in pending làm người đọc hiểu nhầm. Giữ source/hash/span và payload_json nguyên vẹn. Lệnh get có thể đọc bản đã quyết định; list là hàng đợi chỉ review pending, cursor theo ID như cũ. Metadata review hỏng phải bị get/list từ chối nhất quán.
4. **Phạm vi bổ sung hợp lý:** được sửa `extractor/draft/store.py`, `extractor/tests/test_store_cli.py`, `extractor/tests/test_queue_cli.py`, `extractor/draft/README.md` để phản ánh metadata và kiểm tính tương thích. Được tạo một ADR có tên kết thúc `w05-offline-review.md` theo số còn trống trong docs/adr; không ghi đè ADR cũ. Nếu tách store cho dễ đọc, chỉ được thêm `extractor/phonghoa_extractor/review.py`; tránh vòng import, không nhân đôi validator.
5. **Validation:** ID/version phải là int không bool, trong miền SQLite và version không âm; timeout hữu hạn; Actor/roles/subject/decision/reason đúng kiểu, tránh phép membership gây TypeError. Sai input bị chặn trước kết nối/ghi. Approve chỉ xử lý loại IOC hiện hỗ trợ; item kept với kind không hỗ trợ không được lọt qua validation để được duyệt. Không thêm loại TTP hay chỉnh sửa item trong lát cắt này. Reason chỉ dùng cho reject, approve có reason khác None bị từ chối để hợp đồng rõ.
6. **Transaction và concurrent decision:** audit insert/state/version cùng transaction; lỗi commit phải rollback, không retry vô hạn. Kiểm hai caller cùng expected_version chỉ một thành công và chỉ một audit. Migration lỗi không nâng user_version hay để lại schema nửa chừng; migration lần hai không thay payload/metadata/audit. Test chỉ trên DB tổng hợp riêng; không migrate DB evidence cũ của Leader.
7. **Bằng chứng dễ chạy lại:** có demo Python offline tạo hai subject khác nhau, save draft, approve một draft và reject một draft; dùng tiến trình mới đọc lại state/audit/payload; chứng minh queue chỉ còn pending và read không đổi byte DB. Lưu dưới workspace Leader `w05-review-evidence/`, báo cáo `PHONG-HOA-W05-REVIEW-RESULT.md`. Không cần viết UI hay command approve với actor tự khai.
8. **Git và kiểm:** khi thực sự được giao, tạo branch `feat/w05-local-review-20261110` từ HEAD e83bb3f trên checkout sạch đang được giao; không đụng nhánh/worktree khác. Local commit được phép, không push/PR/merge/deploy. Dùng `.venv/Scripts/python.exe` 3.12.13; `python -m pytest -q` tương đương make test, `python -m ruff check .` và `python -m ruff format --check .` tương đương make lint; chỉ chạy full suite một lần sau test tập trung đạt, không cài make mới chỉ để chạy alias. Giữ đủ assertion integrity cũ; thay đổi contract phải có test hành vi mới, không xóa test để đạt.

Sau B, Leader đối chiếu lại spec W05 và nghiên cứu trước khi chọn lớp tiếp; API xác thực là ứng viên, không mặc định chọn nhà cung cấp danh tính khi chưa có điều kiện thật. Các tiêu chí chỉnh sửa item/đo số sửa, chống agent tự duyệt ở biên xác thực, UI và OpenCTI vẫn còn mở ở mục tiêu tổng.
