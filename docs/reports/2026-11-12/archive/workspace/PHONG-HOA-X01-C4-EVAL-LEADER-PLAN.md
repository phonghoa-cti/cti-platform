# X01-C4-EVAL — nghiệm thu contract và giao triển khai

Ngày 11/11/2026. Leader chấp nhận phương án A sau rework request `ee870262-acd2-4f88-8ddc-21b2e91a6e6a`, với các chốt cụ thể bên dưới. Không cần thêm vòng nghiên cứu. Đây là nghiệm thu tài liệu, chưa nghiệm thu implementation/test C4.

## Bằng chứng đã kiểm

Root tuyệt đối: `$WORKSPACE`.

- Đã đọc toàn bộ research và brief đã sửa; SHA-256 lần lượt `E9441ED40CEE2E112C3A669F4D443632BB570E848703AFF01141886ADF5C2027` và `68EE38D3C86F749B588636D3AD364BF2F1E87C7BC9854ECDCF67EF9F2CD7BA92`.
- Source `root\cti-x01-c4-adapter` vẫn tại `654443e6ede6557f0629fc0886ca56fff782b193`, status porcelain rỗng và diff quiet exit 0. Base giữ nguyên, không fetch/pull hoặc chuyển nhánh source.
- Đã đối chiếu mã producer/reporter trong review trước; kiểm lại giới hạn reporter hiện hành, AGENTS.md và interpreter trong lượt này: Python 3.12.13, pytest 9.2.0, Ruff import được. Không chạy test sản phẩm trong lượt nghiệm thu tài liệu.
- Target `root\cti-x01-c4-eval` và branch `feat/x01-c4-eval-20261111` chưa tồn tại lúc kiểm. Các thread liên quan idle; không có worker C4 evaluator trùng.

| Review | Kết luận |
|---|---|
| R1 | Đủ năm nhãn TLP cho fake_offline; literal prediction_basis đúng; C4 1.2 đơn hoặc C3 audit 1.1+C4; compatibility cũ rõ. |
| R2 | API/immutable DTO cụ thể; reuse query validator; preflight toàn dataset trước generate; report/hash/newline và terminal calls phân biệt. |
| R3 | C4 no-clobber riêng; schema/context/audit/cohort invariants đã chốt; old writer không đổi. Các chi tiết nhỏ cuối cùng được cố định dưới đây. |
| R4 | Exact target/base/branch, allowlist, interpreter, checks và evidence đủ giao một worker. |

## Chốt bổ sung để triển khai trực tiếp

1. Nguồn contract là `PHONG-HOA-X01-C4-EVAL-RESEARCH.md` và `PHONG-HOA-X01-C4-EVAL-IMPLEMENTATION-BRIEF.md` tại hai hash trên; tài liệu này ưu tiên khi có khác biệt nhỏ. Read AGENTS.md, docs/PROGRESS.md, X01 spec và ADR 0008 trên target. Phạm vi triển khai offline nhiều file đã được người dùng giao tiếp tục; không dừng xin lại phép giữa TDD, kiểm thử và commit cục bộ.
2. `limitations` C4 là đúng năm chuỗi theo thứ tự dưới đây; không chấp nhận paraphrase từ input. C1–C3 giữ nguyên constants/rendering.

```json
[
  "Synthetic fixtures and fake_offline provider only; no real model quality claim.",
  "C4 adapter merges model candidates with regex extraction before grounding; scores are not model-only.",
  "Semantic TTP, malware, and actor items are not evaluated.",
  "Retrieval completion and context transmission do not prove model knowledge use or quality.",
  "TTP audit reports source, quote, and catalog consistency only; semantic TTP remains unverified."
]
```

3. Dataset C4 không rỗng: document_count **1..256**. Output C4 trước publish phải thỏa giới hạn cấu trúc hiện hữu của reporter (depth 64, object 64 keys, array 512, string 8192) và tổng JSON UTF-8 **<=1,048,576 bytes**. Không tăng global caps hoặc thay producer C1–C3. Serialize C4 deterministic với ensure_ascii=False, indent=2, sort_keys=True và một LF cuối; xác thực bytes/schema trước tạo output cuối. Output quá lớn trả lỗi an toàn, không publish. Python integer phải exact int, bool phải exact bool.
4. `adapter_schema_version` document là `1.0`, config C4, language vi/en, TLP thuộc đúng năm literal CLI đang có. Không yêu cầu ba loại hash khác nhau theo phép so `!=`; chúng đại diện ba loại input khác nhau. Không ghi trường raw query/context. Khi test chống rò dùng marker chỉ xuất hiện trong query/context, không cấm từ tình cờ cũng có trong report/evidence hợp lệ.
5. Writer C4: output tồn tại hoặc race bị từ chối, giữ nguyên bytes; không thêm overwrite. `os.link` thành công là đã publish. Lỗi cleanup sau commit có thể trả exit 1 an toàn nhưng phải giữ output đã publish và ghi rõ tình trạng này trong README/test/evidence; không gọi đó là rollback. Mọi temp còn lại phải có quyền sở hữu xác định và được dọn trước handoff; không xóa output để che lỗi. Không hứa crash durability hay chống hostile directory mutation.
6. DTO raw_sha256 là provenance do parser tính từ bytes input. Evaluator kiểm cấu trúc/digest syntax và mapping, không thể chứng minh digest của DTO tự dựng tương ứng file khi không có raw bytes. Không tuyên bố xác thực nguồn ngoài mức này.

## Phạm vi và cách thực hiện

Một CTI AI Agent, model `gpt-5.6-sol`, reasoning medium, trực tiếp triển khai/kiểm thử, không giao bot hoặc helper khác. Tạo đúng target/branch từ base; một người sửa tree. Nếu target bất ngờ đã tồn tại, inspect trước, không reset/xóa hoặc ghi đè.

Allowlist giữ theo brief: run.py, report.py, eval/README.md; test_eval_cli.py, test_eval_report.py, test_c4_eval_contract.py; fixture mới chỉ `extractor/eval/fixtures/c4/`; docs/PROGRESS.md; docs/adr/0009-c4-evaluator-artifact-and-cohort.md. Không refactor ngoài mục tiêu, sửa dependency, adapter/retrieval/catalog/audit, core/W05/UI, snapshot/fixture cũ hoặc sổ Leader.

Chạy liền mạch: preflight source/target → test RED cho các hành vi mới → code tối thiểu → GREEN và hồi quy → demo → self-review tập trung → commit local → kiểm HEAD/status/manifest. Không cần tất cả test đỏ cùng lúc; mỗi nhóm hành vi phải có RED trước code tương ứng. Không chạy mạng/model thật/secret/lab/listener, không push/PR/merge/deploy.

Interpreter tuyệt đối `root\cti-platform-start\.venv\Scripts\python.exe`; cwd target và PYTHONPATH gồm target/core;target/extractor. Không cài package. Bắt buộc chạy năm test file của brief **và `extractor/tests/test_evaluate.py`** cho C1 scorer/evaluator. Ruff check/format-check đúng các file Python đã đổi, `git diff --check base..HEAD`. Không mở rộng full repo nếu không có lỗi/liên quan mới. Khi so cross-commit C2/C3 chỉ loại evaluator.git_ref; Markdown dùng input artifact cố định. Demo tại HEAD cuối: C4 standalone, C3.1+C4 cùng dataset/fixtures/catalog; lần lặp C4 ghi file đích mới rồi so bytes. Test request recorder chứng minh retrieval một lần/doc và attempts/calls đúng, không gọi model.

Kết quả tại `root\PHONG-HOA-X01-C4-EVAL-RESULT.md`; bằng chứng tại `root\x01-c4-eval-evidence\`, gồm RED/GREEN, JUnit/commands/exit, demo JSON+Markdown, compatibility, source/target refs/status, manifest SHA-256. Giữ worktree/branch cho Leader review, không tự merge. Nêu rõ finding đã xử lý và giới hạn còn lại; self-review không thay nghiệm thu độc lập của Leader.

UNVERIFIED: implementation/tests của lát mới cho đến khi worker thực chạy và Leader đối chiếu; semantic TTP/RAG/model thật, corpus gold, cloud/OpenCTI/lab/production không thuộc lần giao này.
