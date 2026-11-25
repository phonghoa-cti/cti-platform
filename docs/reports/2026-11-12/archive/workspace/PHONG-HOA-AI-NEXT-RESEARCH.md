# AI-NEXT — nghiên cứu bước AI/agent có thể làm trước lab

Ngày đối chiếu: 10/11/2026 (Asia/Saigon)
Repo chỉ đọc: `cti-platform-start`
Ref đã kiểm: `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`
Trạng thái checkout khi nghiên cứu: sạch; không sửa repo, không chạy test/model, không gọi lab/VM/cloud.

## 1. Kết luận

**Chọn lát cắt A: adapter phản hồi LLM trung lập nhà cung cấp, có provider giả lập, kiểm schema, TLP và
evidence cho C2/C3.**

Đây là bước nhỏ nhất vừa chạy được hoàn toàn ngoại tuyến, vừa đi thẳng từ baseline C1 sang phần AI còn thiếu:

- C2 giữ đầu ra model thô chỉ để đo, có cờ `operational_draft_eligible=false`; không được đưa IOC chưa grounded
  (chưa đối chiếu với nguồn) vào draft vận hành.
- C3 dùng lại `ground_iocs` để đối chiếu evidence/span và loại mục bịa trước khi tạo kết quả đủ điều kiện nối
  sang draft.
- Provider giả lập trả các phản hồi tổng hợp đã định trước; không cần key, không chọn hãng/model, không gửi dữ
  liệu ra ngoài và không giả vờ đã đo chất lượng model thật.
- Adapter tách hợp đồng nội bộ khỏi cú pháp riêng của từng API. Khi người dùng chọn provider sau này, chỉ thêm
  lớp chuyển đổi và kiểm lại schema/provider, không viết lại grounding hoặc evaluator.

Không chọn FastMCP/Hermes ở bước này vì `mcp-server/` đang trống và portal-api/auth chưa chạy; dựng công cụ agent
ngay sẽ chủ yếu kiểm khung giả lập, chưa giải quyết khoảng trống C2/C3 của X01. Không chọn bộ TTP trước vì nhãn
TTP thật và corpus hai người gán nhãn chưa có; phần chấm tập hợp đã tồn tại nhưng chưa có đầu vào chất lượng để
cho số đo có ý nghĩa.

## 2. Câu hỏi và phạm vi

**Câu hỏi:** trong ba lát cắt A/B/C, việc nào tạo được đầu ra quan sát được trước lab, độc lập với W05 đang làm,
tái sử dụng code hiện có nhiều nhất và mở đường ngắn nhất tới AI/agent thật mà không vượt ranh giới dữ liệu?

Đã đọc đúng ref: `AGENTS.md`, `docs/PROGRESS.md`, `X01-ai-extractor.md`, `A01-tro-ly-hermes.md`,
`F08-phan-quyen-tlp.md`, `api-portal.md`, code extractor/eval/evidence/drafts, test liên quan và `mcp-server/`.
Đã kế thừa `PHONG-HOA-SKILLS-MCP-WORKFLOW-RESEARCH.md` cùng các kết quả X01 C1/draft/store/queue/QA. Không
đọc secret, không gọi model thật và không coi báo cáo cũ là bằng chứng runtime hiện tại.

## 3. Hiện trạng trên ref `e83bb3f`

| Quan sát | Bằng chứng trong repo | Ý nghĩa |
|---|---|---|
| C1 regex đã có CLI/evaluator | `extractor/eval/run.py`; `phonghoa_extractor/evaluate.py` | Có thể mở rộng trục `--config C2/C3`, không viết lại Precision/Recall/F1. |
| Grounding IOC đã có | `phonghoa_extractor/grounding.py`; `evidence.py` | Đã kiểm normalize, exact evidence, span, allowlist và đánh dấu `bia`; adapter chỉ cần chuyển payload hợp lệ sang đầu vào này. |
| Draft C1 và kho SQLite đã có | `drafts.py`, `store.py`, `draft/` | Không cần và không nên sửa trong lát cắt adapter; output C3 chỉ dừng ở artifact trung gian. |
| TTP mới có hàm kiểm ID/chấm tập hợp | `ground_techniques`, `score_techniques` | Chưa có loader snapshot ATT&CK/version và dataset thật hai người gán nhãn. |
| Dataset chỉ là 6 mẫu synthetic smoke | `extractor/dataset/synthetic-smoke/`; `GUIDELINE.md` | Chỉ đủ test/demo hợp đồng, không đủ kết luận chất lượng model hay luận văn. |
| C2–C4 chưa được hỗ trợ | `extractor/eval/run.py` trả exit 2 nếu config khác C1 | Đây là khoảng trống trực tiếp nhất của X01. |
| MCP server chưa có implementation | `mcp-server/` chỉ có `.gitkeep` | A01 chưa có lõi tool, test, auth hoặc API thật để nối. |
| Portal draft HTTP/auth/approve còn là đề xuất | `docs/specs/api-portal.md`, mục “Bản nháp AI” | Không được giả định agent có quyền hoặc endpoint đã chạy. |
| Tiến độ tự ghi rõ giới hạn | `docs/PROGRESS.md` | Chưa gọi LLM/feed; chưa có dataset thật hai người gán nhãn; C2–C4 và TTP còn thiếu. |

Các kết quả cũ chứng minh luồng offline C1/draft/store/queue trên dữ liệu tổng hợp, nhưng không chứng minh model,
prompt-injection, HTTP/auth, OpenCTI hoặc lab. Ref hiện tại đã gồm commit sửa validation-on-read và timeout;
nghiên cứu này không chạy lại suite vì brief cấm chạy test/code.

## 4. Nguồn chính thức và khả năng tái sử dụng

### 4.1 Structured output và JSON Schema

- Tài liệu OpenAI hiện hành phân biệt JSON mode (chỉ bảo đảm JSON hợp lệ) với Structured Outputs (bám schema),
  nhưng cũng yêu cầu xử lý refusal, output thiếu do giới hạn token và schema chỉ hỗ trợ một tập con. Vì vậy không
  được tin payload chỉ vì provider nói “strict”; ứng dụng vẫn phải kiểm envelope, trạng thái và schema sau khi
  nhận. [OpenAI Structured Outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- Phần dùng lại: hình dạng X01 hiện có (`iocs`, `techniques`, `malware`, `actors`) trở thành **schema nội bộ 1.0**.
  Mỗi provider thật sau này tự ánh xạ schema nội bộ sang tập con nó hỗ trợ.
- Không tự viết: không xây JSON Schema engine tổng quát. Lát cắt đầu chỉ kiểm đúng schema X01 nhỏ bằng stdlib;
  khi thêm provider thật mới quyết định dùng SDK/Pydantic/jsonschema theo dependency và phiên bản đã chọn.

### 4.2 Hermes và MCP

- Hermes có MCP client gốc, hỗ trợ server local stdio hoặc HTTP, lọc tool include/exclude và chỉ nạp tool cần
  thiết. Bản phát hành quan sát ngày 10/11/2026 là `v0.23.1`; repo dùng MIT. Đây là thành phần nên **tái sử dụng
  sau**, không tự viết Telegram/gateway/agent runtime. [Hermes MCP](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/mcp.md),
  [release v0.23.1](https://github.com/NousResearch/hermes-agent/releases/tag/v0.23.1),
  [license](https://github.com/NousResearch/hermes-agent/blob/main/LICENSE)
- FastMCP tài liệu hiện tại nêu bản `4.1.7`, Apache-2.0, hỗ trợ gọi server in-memory để test không mở process
  hay mạng. Đây là ứng viên hợp lý cho lát cắt B sau khi có hợp đồng portal read-only ổn định.
  [FastMCP](https://gofastmcp.com/)
- MCP `readOnlyHint` chỉ là gợi ý không đáng tin nếu server không đáng tin; nó không phải phân quyền và không
  chống prompt injection. Quyền phải được cưỡng chế ở API/token/service, đồng thời toolset không được chứa
  approve/delete/block/shell. [MCP tool annotations](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/)

### 4.3 TLP và ranh giới chia sẻ

- FIRST TLP 2.0 là bản hiện hành; `TLP:GREEN` chỉ cho phép chia sẻ trong community (cộng đồng) xác định, không
  phải kênh công khai. Không thể suy ra một nhà cung cấp cloud bất kỳ thuộc community đó.
  [FIRST TLP 2.0](https://www.first.org/tlp/),
  [TLP use cases](https://www.first.org/tlp/use-cases)
- Do đó nhãn TLP chỉ là một đầu vào của quyết định egress (gửi dữ liệu ra biên). Cloud còn cần: nguồn/giấy phép,
  community được người chia sẻ xác định, điều khoản nhà cung cấp, tài khoản/quyền hiện hành và phê duyệt cho
  đích cụ thể. `TLP:CLEAR` cũng không tự xóa bản quyền hoặc điều khoản nguồn.
- Adapter offline phải mang theo metadata TLP và policy decision, mặc định **deny cloud**. Provider giả lập
  `egress=false` được dùng để test mọi nhãn mà không gửi dữ liệu.

### 4.4 ATT&CK/TTP

- MITRE cung cấp ATT&CK dưới dạng STIX và TAXII chính thức, cùng file theo version. Nếu làm lát cắt C, phải ghim
  snapshot/version và lưu provenance thay vì hard-code danh sách ID hoặc phụ thuộc mạng khi test.
  [MITRE ATT&CK Data & Tools](https://attack.mitre.org/resources/working-with-attack/)
- Code hiện có đã nhận `known_ids: set[str]`, nên phần tái sử dụng rõ. Khoảng trống lớn hơn là corpus và quy
  trình nhãn; không nên tự tạo số F1 TTP từ dữ liệu tổng hợp rồi gọi đó là đánh giá model.

## 5. So sánh tối đa ba lát cắt

Thang 1–5, điểm cao tốt hơn. “Độc lập W05” nghĩa là không cần HTTP/approve/UI đang phát triển.

| Lát cắt | Đầu ra offline quan sát được | Dùng lại ref hiện tại | Độc lập W05 | Tiến tới AI/agent thật | Rủi ro/chi phí hiện tại | Tổng |
|---|---:|---:|---:|---:|---:|---:|
| **A. Adapter LLM C2/C3 + fake provider** | 5 | 5 | 5 | 5 | 4 | **24/25** |
| B. Lõi A01 read-only + fake portal | 4 | 2 | 4 | 4 | 3 | 17/25 |
| C. TTP dataset/eval interface | 4 | 3 | 5 | 3 | 3 | 18/25 |

### A — adapter LLM có schema/TLP/evidence

**Phạm vi hợp lý:** protocol provider nhỏ; schema X01 1.0; fake provider scripted; policy egress; retry tối đa một
lần; lỗi refusal/incomplete/schema/provider; C2 raw chỉ đánh giá; C3 gọi grounding IOC; CLI/demo bằng fixture.

**Tái sử dụng:** `ground_iocs`, evidence span, allowlist, evaluator và quy ước C1/C2/C3.
**Không tự viết:** SDK cloud, model client, JSON Schema engine tổng quát, queue/draft store, prompt-injection
“bảo đảm”, tokenizer/cost provider.
**Giá trị:** làm rõ chính xác ranh giới giữa model không tin cậy và code kiểm chứng; provider thật về sau chỉ là
adapter mới.

### B — lõi công cụ A01 chỉ đọc với fake portal

**Phạm vi khả dĩ:** `lookup_ioc` và `overview` gọi fake transport; role `agent`; lọc TLP CLEAR/GREEN; structured
tool output; test không có tool ghi.
**Ưu:** demo agent/tool sớm; FastMCP hỗ trợ test in-memory.
**Nhược:** portal-api, auth và mcp-server chưa có implementation; nếu chỉ fake sẽ chưa chứng minh quyền backend.
Tool output vẫn là dữ liệu không tin cậy. Việc chỉ gắn `readOnlyHint` hoặc giấu tool không thay kiểm quyền phía
dịch vụ. Chọn B ngay sẽ thêm dependency và hợp đồng dễ đổi trước khi có API thật.

### C — interface dataset/eval TTP

**Phạm vi khả dĩ:** schema nhãn TTP có version/provenance; loader snapshot ATT&CK; scorer micro/per-document;
fixture tổng hợp.
**Ưu:** độc lập portal, quan trọng cho C4/chương 4.
**Nhược:** dataset thật và hai người gán nhãn là đường găng; code scorer đã có. Fixture tổng hợp chỉ kiểm plumbing,
không tạo bằng chứng chất lượng. Hữu ích nhưng chưa đưa model vào pipeline như A.

## 6. Ranh giới bắt buộc cho lựa chọn A

### 6.1 Model response là dữ liệu không tin cậy

Luồng bắt buộc: `provider envelope -> trạng thái -> parse JSON -> kiểm schema nội bộ -> policy -> C2 raw hoặc
C3 grounding -> artifact`. Không gọi hàm/tool/lệnh nêu trong nội dung báo cáo hoặc model output. Không nội suy
field lạ, không giữ value/evidence sai kiểu và không tự sửa JSON mơ hồ.

Structured output giảm lỗi hình dạng nhưng không chứng minh nội dung đúng, không ngăn bịa và không chống mọi
prompt injection. Fake provider chỉ chứng minh code phản ứng đúng với fixture.

### 6.2 C2 không được đi vào draft vận hành

C2 cần giữ cả IOC bịa để đo false positive/hallucination, nhưng artifact phải có:

```json
{"config":"C2","purpose":"evaluation-only","operational_draft_eligible":false}
```

Không gọi `build_regex_draft`, `save_draft` hoặc queue. Chỉ C3 qua schema + grounding mới có thể đánh dấu
`operational_draft_eligible=true`; việc thực sự ghi draft vẫn ở lát cắt tích hợp sau và cần hợp đồng W05.

### 6.3 TLP và quyền gửi cloud

| Đích | Chính sách lát cắt này |
|---|---|
| `fake_offline`, không egress | Cho test fixture tổng hợp với mọi TLP; log `egress=false`. |
| Model local thật | Chưa triển khai; cần quyết định riêng về model, tài nguyên, license và dữ liệu. |
| Cloud, TLP:AMBER/AMBER+STRICT/RED | Cấm. |
| Cloud, TLP:GREEN | Cấm mặc định; chỉ mở khi chứng minh provider thuộc community/đích được phép và có quyết định chia sẻ cụ thể. |
| Cloud, TLP:CLEAR | Vẫn cấm mặc định trong adapter chưa cấu hình; khi tích hợp phải kiểm quyền nguồn/giấy phép, provider và phê duyệt đích cụ thể. |

Không chọn provider, đăng nhập hoặc key trong task. Không ghi raw CTI vào exception/stdout; test dùng marker tổng hợp
và kiểm marker không rò ở lỗi.

### 6.4 Quyền agent

Adapter không phải agent và không có tool. Bước nối A01 sau này chỉ được expose read-only hoặc tạo **đề xuất/nháp**;
không có approve, decision, delete, block, shell hoặc OpenCTI token. Quyền được cưỡng chế ở portal-api, không dựa
vào prompt, tên role hay MCP annotation.

## 7. Lựa chọn, giới hạn chưa biết và điều kiện dừng nghiên cứu

**Lựa chọn:** triển khai A theo `PHONG-HOA-AI-IMPLEMENTATION-BRIEF.md`, không thêm dependency ở lát cắt đầu.

**Chưa biết có chủ đích:** provider/model thật; tập con schema của provider được chọn; giá/latency/token; điều khoản
dữ liệu; community cho từng nguồn TLP:GREEN; model local và tài nguyên; corpus thật/hai người gán nhãn; chất lượng
C2/C3/TTP; mức chống injection; API/auth/lab runtime. Các điểm này không cản adapter offline.

Nghiên cứu dừng ở đây vì đã đủ để chọn một thay đổi nhỏ đảo ngược được. Bước kế là implementation/test/demo
offline; không tiếp tục khảo sát provider hoặc dựng agent cho tới khi có bằng chứng từ lát cắt này và quyết định
riêng của người dùng.
