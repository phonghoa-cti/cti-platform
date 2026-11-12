# X01-C4-RETRIEVAL — nghiệm thu cục bộ sau R1

Ngày 11/11/2026. **PASS cục bộ**, chấp nhận HEAD `d97f96362edcd92e87fc69cfa20a563109cec550` trên branch `feat/x01-c4-retrieval-20261111`.

Root tuyệt đối: `$WORKSPACE`.

## Kết luận và bằng chứng độc lập

- Target `root\cti-x01-c4-retrieval`; source `root\cti-x01-eval-report` giữ HEAD `d35f58dfa8de03827480e78d62153a75cc78365b`. Cả hai sạch sau kiểm.
- Rework từ `4067598c87772dac88af309b01d127f748f369fd`: đúng hai file catalog/test, +30/-3. Leader đọc toàn diff. `_PatternVersion` giữ raw; `_description(item.raw, ...)` chạy khi xây record sau canonical selection. Không đổi retrieval, pin, lookup, graph hoặc lifecycle.
- R1 được đóng: probe Leader đã bắt 10 lỗi trên HEAD cũ, nay **18/18 đạt**. Bản cũ lỗi không chặn bản mới; bản hiện tại lỗi vẫn bị từ chối; missing/empty không kế thừa bản cũ. Oracle byte budget với Unicode/escaping vẫn đạt.
- Fresh command bên dưới chạy ba file regression và probe trong cùng lượt: **229 passed in 3.75s**, exit 0. JUnit: 229 test, 0 failure/error/skip. Gồm 211 test repo + 18 probe Leader.
- Ruff check, Ruff format-check hai file thay đổi và `git diff --check 4067598..HEAD`: exit 0.
- Manifest rework: **24/24** mục khớp hash. Report SHA `00C599B45970336F27705FED0151BAC90FE87DB1E235F66B829146E06132D425`; manifest SHA `DF16B1043A6BDD87221897AED67F35FE39C3337CEBC470670B9D35B6CA25AE44`, khớp callback.
- Probe nguyên trạng SHA `D636C4BA3C2DE1AA14139E11A015CA0B9179D6F9565BC384F704B6787F7409AB`. Không sửa code sản phẩm trong review.

## Lệnh và tệp kiểm

CWD `root\cti-x01-c4-retrieval`; PYTHONPATH gồm `target\extractor;target\core`; `PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT=root\x01-attack-real-research-evidence\enterprise-attack-20.1.json`.

```text
root\cti-platform-start\.venv\Scripts\python.exe -X utf8 -B -m pytest -o addopts= -q -p no:cacheprovider --junitxml=../leader-x01-c4-retrieval-review/04-rework-acceptance.xml extractor/tests/test_attack_catalog.py extractor/tests/test_attack_catalog_official.py extractor/tests/test_attack_retrieval.py ../leader-x01-c4-retrieval-review/test_canonical_description_probe.py
```

Log/XML/exit: `root\leader-x01-c4-retrieval-review\04-rework-acceptance.*`; manifest check `05-rework-manifest.json`; lint/diff/source/target readback `06-rework-final-checks.json`. Review ban đầu `PHONG-HOA-X01-C4-RETRIEVAL-REVIEW-20261111.md` giữ nguyên lịch sử NEEDS_REWORK.

Lệnh đọc tìm file kế tiếp có một lỗi đường dẫn giả định `llm_provider.py` không tồn tại; đã xác nhận `ProviderRequest`, `LLMProvider`, `ScriptedProvider` nằm trong `llm_adapter.py`. Lỗi tìm kiếm không được tính là test thất bại hoặc bằng chứng thiếu module sản phẩm.

Không lặp full 662/scoped 428: đó là số worker chạy trước R1, không phải bằng chứng fresh của lượt nghiệm thu này.

## Phạm vi được chấp nhận và nối việc

Chấp nhận component lexical retrieval và context JSON có provenance/budget, compatibility loader official v20.1 và sửa R1. Chưa chấp nhận chất lượng ngữ nghĩa, full C4 hoặc khả năng model sử dụng context.

Spec `docs/specs/X01-ai-extractor.md` nêu C4 = C3 + RAG ATT&CK; PROGRESS và research hiện có ghi khoảng trống đưa context vào trước generation. Bước đủ điều kiện kế là nghiên cứu/brief **C4 adapter ngoại tuyến** trên đúng HEAD vừa nghiệm thu; giao CTI Research chỉ viết hai tài liệu, chưa cho sửa source. Nghiên cứu phải tái dùng loader/retriever/adapter/audit hiện hữu, giữ các ranh giới bằng chứng và quyền.

Threads kiểm đầu lượt 11:51 ICT: không có Leader khác chạy Phong Hỏa; worker R1 idle và callback đã về. Automation tiếp tục enabled, lần gần nhất 11:26 trả NOTHING NEW; giữ vì dự án active. Chưa chứng minh khả năng khôi phục mọi lần bỏ dở.

UNVERIFIED: multilingual recall/TTP semantics, corpus thật hai người gán nhãn, model/provider thật, C4 generation/evaluator/report integration, OpenCTI/lab/production. Không push/PR/merge/deploy.
