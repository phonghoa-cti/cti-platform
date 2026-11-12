# X01-C4-RETRIEVAL-IMPLEMENT — quyết định giao triển khai

Ngày 11/11/2026. Leader nghiệm thu **nghiên cứu/hợp đồng sau R1–R4**, chưa nghiệm thu code hoặc C4. Tiếp tục ngay một worker CTI AI Agent, Sol medium, không giao tiếp cho bot khác.

Root Leader: `$WORKSPACE`.

## Nguồn và phạm vi đã chốt

- Source chỉ đọc: `root\cti-x01-eval-report`, HEAD `d35f58dfa8de03827480e78d62153a75cc78365b`, branch `feat/x01-eval-report-20261111`.
- Tạo worktree mới `root\cti-x01-c4-retrieval`, branch `feat/x01-c4-retrieval-20261111`, đúng base trên. Leader đã kiểm target/branch chưa tồn tại; worker kiểm lại trước tạo, không reset/xóa nếu bất ngờ có sẵn.
- Research sau Leader sửa ví dụ escape: `PHONG-HOA-X01-C4-RETRIEVAL-RESEARCH.md`, SHA-256 `01A015A31FD4DA21705ACCD38E594D0730F0BB8B337EE32199BAC117A42150EE`.
- Brief: `PHONG-HOA-X01-C4-RETRIEVAL-IMPLEMENTATION-BRIEF.md`, SHA-256 `3584CF7C517149BE47AFFBC46D5AB3E24AFEB6B45AB96D241EA9A2EFFA5FDCC8`.
- Áp dụng brief và các điểm chốt dưới đây; nếu khác nhau, quyết định Leader này ưu tiên. Source AGENTS/spec X01/PROGRESS/ADR vẫn áp dụng. Việc triển khai cục bộ này đã nằm trong phạm vi được giao, không cần hỏi lại người dùng.

## Điểm chốt để triển khai nhất quán

1. Regex chính xác là `re.findall(r"[^\W_]+", normalized, flags=re.UNICODE)`; search view nối field bằng ký tự newline `"\n"`, không phải chuỗi backslash+n. Leader sửa lỗi double escape trong research và kiểm 6 ví dụ Python độc lập (ID, full-width, Việt NFC/NFD, token quá ngắn/dài, emoji/CRLF, newline), exit 0. Đây chỉ là kiểm ví dụ contract, không phải test sản phẩm.
2. Description thêm optional ở cuối TechniqueRecord. Chỉ validate/project description của phiên bản canonical được chọn; missing/empty -> None, present non-string (kể cả null), surrogate hoặc >32 KiB -> `AttackCatalogError("invalid_attack_pattern")`. Không dùng description từ bản cũ làm fallback; giữ nguyên kiểm duplicate/conflict/lifecycle/graph hiện có. Không sửa pinned fixtures/hash hoặc output của lookup.
3. `RetrievalResult.results` chứa đúng prefix candidate thực sự được đưa vào `context`, cùng thứ tự; không kèm item bị budget loại. Chỉ item đầu có thể bị cắt snippet. Lấy prefix dài nhất theo code point mà **serialized whole envelope** vẫn vừa, `snippet_truncated=true`; raw result.description giữ nguyên. None -> snippet rỗng, truncated=false. Metadata không vừa trả `context_budget_exceeded`. Cả zero-match envelope cũng phải đo; không biến hết budget thành zero-match. Trường semantics/eligibility cố định trên mọi kết quả.
4. Catalog là input nội bộ từ loader, không phải ranh giới chứng thực nguồn. Guard exact AttackCatalog/SnapshotPin và mapping kiểu dict hoặc MappingProxyType; tái dùng validation pin hiện có trong attack_catalog (không đọc file) và chuyển lỗi thành `invalid_catalog`. Kiểm projection mỗi entry trước ranking: key external ID khớp record và grammar hiện có; exact TechniqueRecord; name/modified/ID, bool lifecycle/subtechnique, tuple parent IDs đúng kiểu/grammar, description None hoặc string đúng bound/UTF-8. Dùng invariant scalar hiện có; lỗi record -> `invalid_record` code-only. Không viết parser STIX hay engine canonical/graph thứ hai: graph/lifecycle source vẫn do public loader quyết định. Test malformed input và no mutation; không dùng object tự dựng làm bằng chứng hash/source đã được xác minh.
5. Official asset local đã có: `root\x01-attack-real-research-evidence\enterprise-attack-20.1.json`, SHA-256 `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`, 55,277,605 bytes. Set env đúng đường này cho acceptance, chạy official tests không skip. Không cần đổi fixture thiếu-env từ skip thành fail cho mọi môi trường chung; yêu cầu không-skip áp dụng lượt nghiệm thu này. Được thêm kiểm description vào test official trong scope.
6. Demo official dùng public loader, query English cho match và ID/tie/zero-match phù hợp; không buộc tiếng Việt có match trong dữ liệu English. Unicode Việt–Anh được kiểm bằng **fixture tổng hợp mới qua loader** ở test retrieval; không gọi đó là multilingual recall. Demo rerun deterministic, source hash trước/sau, context byte bound, raw description bất biến. Không thêm model/provider, dependency, network, database, API/UI hoặc C4 CLI.

## Hoàn thành task

Scope đúng bảy nhóm file của brief: catalog, retrieval mới, catalog tests, retrieval tests mới, official tests, một ADR, PROGRESS. Báo cáo/evidence ngoài repo đúng đường brief. Worker tự viết test RED → code GREEN → scoped regression/lint/format/diff-check → tự review → commit cục bộ, giữ worktree sạch; không push/PR/merge/deploy. Lưu exact command/exit/count, base/HEAD/diff, nguồn/input hash, manifest.

Trả `root\PHONG-HOA-X01-C4-RETRIEVAL-RESULT.md` và `root\x01-c4-retrieval-evidence\`. Leader sẽ kiểm độc lập trước chấp nhận và chọn bước kế. UNVERIFIED: implementation hiện chưa có, semantic/TTP quality, model/C4 integration, corpus thật, runtime/lab/production.

## Bằng chứng nghiệm thu research

Callback rework `6a434ac9-1461-475c-8eed-799ca401a572`: hai hash đầu vào khớp báo cáo (research trước sửa escape `9A91E543BA0AE3A9EEC6DD86BC61EE6406280EAC77BC860C782A951E4D1A81DA`). R1 optional description/official asset; R2 public JSON context/budget overflow; R3 tokenizer/trust/semantics; R4 scope/checks/evidence đều được chốt trong tài liệu cùng bổ sung Leader ở trên. Source đúng HEAD, status sạch; chỉ đọc code/kiểm ví dụ, chưa chạy test implementation. Threads kiểm lúc 11:22 ICT: không có Leader khác đang xử lý và AI Agent idle. Automation tiếp tục vẫn enabled; giữ vì project active.
