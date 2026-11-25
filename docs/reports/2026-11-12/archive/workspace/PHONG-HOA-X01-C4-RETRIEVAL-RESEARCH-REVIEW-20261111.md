# X01-C4-RETRIEVAL-NEXT — Leader review R1–R4

Ngày 11/11/2026. **NEEDS_REWORK contract**, chưa giao implementation. Giữ phương án B: component lexical offline, tái dùng canonical loader, chưa nối generator/C4 CLI.

## Bằng chứng đã đối chiếu

- Source `cti-x01-eval-report` HEAD `d35f58dfa8de03827480e78d62153a75cc78365b`; status sạch trước/sau, các lệnh đọc exit 0.
- Research đầu vào SHA-256 `C2A817471510298F59D70C76F94C9E82AD76B93EEBE17516EBF3EFFA61790521`.
- Implementation brief đầu vào SHA-256 `64CD55B8E07FFC1D8717A923B721F82606D6305527C6B0CA8A975DA3AD975300`.
- Đọc `attack_catalog.py:17,28,40,305,475,500` và test builder `test_attack_catalog.py:25`. Builder hợp lệ hiện tại không có description; loader hiện tại không yêu cầu trường này. Dataclass AttackCatalog/TechniqueRecord có constructor công khai.
- Inventory chỉ đọc bằng Python 3.12.13 từ asset local `x01-attack-real-research-evidence/enterprise-attack-20.1.json`: 55,277,605 bytes; SHA-256 `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`; 867 Enterprise attack-pattern, 706 active; cả 867 đều có description string không rỗng; max description 4,680 UTF-8 bytes. Đây là inventory JSON, không phải test loader/retriever mới.
- Đã đọc nguồn chính thức: [MITRE Data & Tools](https://attack.mitre.org/resources/attack-data-and-tools/), [MITRE USAGE](https://github.com/mitre-attack/attack-stix-data/blob/master/USAGE.md), [Lewis et al.](https://arxiv.org/abs/2005.11401), [Sentence Transformers semantic search](https://www.sbert.net/examples/sentence_transformer/applications/semantic-search/README.html). Các nguồn hỗ trợ dùng dữ liệu local/versioned và phân biệt retrieval/generation; không chứng minh công thức overlap tự chọn có chất lượng TTP tốt. Một lần mở trang tokenization Stanford bị timeout; không dùng làm bằng chứng đã đọc.
- Chưa có implementation mới để chạy test. Các finding sau là mâu thuẫn/thiếu trong contract, không báo thành test sản phẩm thất bại.

## R1 — giữ tương thích catalog và kiểm bản MITRE đang dùng

Brief:24 vừa cấm sửa fixture/pin vừa cho phép sửa fixture/hash; :64 bắt mọi description không rỗng, trong khi builder hợp lệ đang thiếu trường này. :96 lại cấm chạy asset official dù đang sửa loader đã được nghiệm thu với asset đó.

Quyết định sửa: bổ sung description **optional** ở cuối TechniqueRecord với default `None` để giữ constructor cũ; lấy từ đúng phiên bản canonical, không đọc STIX bằng parser thứ hai. Missing/empty được biểu diễn `None`, vẫn tìm theo ID/name; không bịa mô tả. Chốt chính xác policy cho present wrong type, surrogate, over-bound và finite error tại seam canonical; thêm regression, không sửa fixture/pin cũ chỉ để làm yêu cầu mới qua test. Giữ duplicate/lifecycle/parent policy và lookup output trước đây.

Bound 32 KiB đủ cho asset đã kiểm, nhưng không được gọi là bảo đảm cho các release khác. Cho phép fixture tổng hợp **mới trong test mới**; giữ asset official và các hash/pin cũ bất biến. Bổ sung `test_attack_catalog_official.py` vào regression với `PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT` trỏ đúng asset local nói trên; không tải lại, không skip rồi nhận PASS. Demo positive phải đi qua public `load_catalog`, không dựng thẳng AttackCatalog làm bằng chứng provenance.

## R2 — budget phải áp lên context mà caller thật sự nhận

Brief:68 giao serializer cho implementer tự chọn, nhưng public API không trả context hay công bố hàm serialize. Research nói cắt từng context, brief chỉ cắt item đầu. Nếu name hợp lệ dài 256 ký tự ASCII, riêng name đã dùng hết budget 256, chưa tính ID/provenance; cắt description không thể giải quyết. Provenance official cũng có URL/hash/commit dài.

Chốt một representation công khai và chính xác: schema/field order, JSON escaping, encoding, separators và phần nào tính trong budget. Trả chính context string/bytes đã đo (hoặc public serializer có signature và invariant rõ). Raw canonical description trong RetrievedTechnique không bị đổi thành snippet; nếu cắt context, dùng trường snippet riêng cùng cờ truncation ngoài dữ liệu MITRE. Query không được chèn vào knowledge context.

Giữ thuật toán đơn giản: xét theo rank, whole item nếu vừa; nếu cắt item đầu thì chỉ cắt snippet, không cắt ID/provenance/name; khi metadata bắt buộc không vừa, trả lỗi hữu hạn `context_budget_exceeded`, không vượt budget và không giả zero-match. Quy định cả empty context/envelope, item sau không vừa, multibyte và ký tự cần JSON escape. Bổ sung ca min-budget + long name/official provenance, zero-match, exact-fit/one-byte-short, raw record bất biến và measured output byte length.

## R3 — chốt tokenizer, kiểu kết quả và ranh giới tin cậy

Brief:62/66 chưa định nghĩa regex/token field selection, token quá dài bị bỏ hay cắt; do đó hai implementer có thể cho thứ hạng khác nhau. Exact dataclass type không chứng minh đối tượng được tạo bởi loader.

- Ghi regex/quy tắc tách từ chính xác, normalization order, trường được index và delimiter giữa các trường. Chốt xử lý `T1566.002`, dấu gạch/underscore, token 1/65 ký tự và Vietnamese composed/decomposed. Dùng cùng tokenizer cho query/doc; không dịch hay bỏ dấu ngầm. Công thức unique overlap là baseline do dự án chọn, không quy thành thuật toán từ bài RAG. Không cần thêm dependency hoặc đổi sang embeddings.
- Chốt exact fields/types/bounds mà API kiểm và mapping lỗi; ghi rõ catalog là input nội bộ từ loader đã kiểm, Python type không phải chứng nhận nguồn. Validation không biến caller tự dựng object thành nguồn MITRE đã xác thực. Kết quả copy vào scalar/tuple immutable; không hứa deepcopy MappingProxyType nếu chưa có cách phù hợp.
- Đồng bộ description optional với R1. Nếu contract muốn assert semantic/eligibility trên result, thêm field fixed `semantic_status="unverified"`, `operational_draft_eligible=False`; không assert thuộc tính chưa có trong public type. Knowledge không trở thành evidence của báo cáo.

## R4 — brief phải đủ để một worker triển khai không cần đoán

Giữ source/base/target/branch hiện tại. Đồng bộ file scope với các test thực sự cần sửa; không mở rộng sang adapter/evaluator/reporter hay pinned fixtures. Lệnh test phải khớp acceptance matrix, gồm official catalog và reporter regression nếu vẫn yêu cầu reporter trong matrix; dùng đúng tên file đã kiểm. Không chạy full suite ngoài phạm vi.

Ghi rõ đầu ra implementation tương lai tại root Leader:

- `PHONG-HOA-X01-C4-RETRIEVAL-RESULT.md`.
- `x01-c4-retrieval-evidence/` cho RED/GREEN, regression, lint/format/diff-check, demo và manifest SHA-256.

Nêu TDD, scoped self-review, commit cục bộ Conventional Commit, clean source/target, giữ branch/worktree để Leader review; không push/PR/merge/deploy. Demo loader → retrieval → context, kiểm hash asset/input trước/sau, deterministic rerun. Không chạy model/C4 hoặc dùng kết quả lexical làm semantic quality. Bỏ cách viết khiến bước nghiên cứu/triển khai đã được ủy quyền lại phải xin người dùng duyệt; Leader review contract là cổng tiếp theo, còn model thật/lab/phát hành vẫn ngoài phạm vi.

## Yêu cầu trả lại

CTI Research **chỉ sửa đúng hai tài liệu đã giao**, giữ phương án B. Không sửa repo, RUNS hoặc review này; không implementation/test/worktree/commit/download, không giao bot khác. Được đọc source và asset hiện có để chốt contract. Trả mapping R1–R4 tới section/line mới, SHA-256 hai file và source HEAD/status trước/sau. Research vẫn không phải bằng chứng component đã chạy.

Automation tiếp tục đã kiểm lúc 11:12 ICT: enabled, project active, giữ nguyên. Lịch và receipt không chứng minh worker đang chạy hay phục hồi bỏ dở đã được kiểm.
