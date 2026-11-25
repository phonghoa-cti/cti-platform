# Brief triển khai AI-NEXT — adapter LLM C2/C3 ngoại tuyến

## 1. Mục tiêu và trạng thái

Triển khai một adapter phản hồi LLM trung lập nhà cung cấp, dùng provider giả lập để chạy C2/C3 hoàn toàn
ngoại tuyến. Adapter kiểm envelope/schema/TLP trước khi xử lý; C2 chỉ tạo artifact đánh giá thô, C3 dùng lại
grounding/evidence để loại IOC bịa. Không gọi model thật, không cần key, không ghi SQLite và không nối W05.

Đây là brief để tạo working tree AI riêng **sau khi Leader giao**; chưa phải bằng chứng implementation.

## 2. Base, owner và ranh giới Git

- Repo: `cti-platform-start`
- Base bắt buộc: `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`
- Owner: CTI AI Agent, Sol medium, một người/một tree.
- Working tree đề xuất tạo sau: `cti-platform-ai-llm-adapter`
- Nhánh đề xuất: `feat/x01-llm-adapter-offline-20261110`
- Không sửa tree Backend/Frontend/Leader; không push, PR, merge hoặc deploy.
- Trước khi sửa: xác nhận `git rev-parse HEAD` đúng base và `git status --porcelain=v1` sạch hoặc ghi rõ thay đổi
  có trước. Bảo toàn mọi thay đổi có trước.

## 3. Phạm vi

### Trong phạm vi

1. Schema nội bộ X01 response v1.0 và validator hẹp bằng Python stdlib.
2. `LLMProvider` protocol và `ProviderResponse` envelope trung lập provider.
3. `ScriptedProvider` đọc chuỗi phản hồi tổng hợp trong bộ nhớ/fixture, có thể trả thành công, lỗi, refusal,
   incomplete hoặc chuỗi phản hồi cho hai lần gọi.
4. Egress policy mặc định deny cloud và quyết định rõ cho provider `fake_offline` (`egress=false`).
5. Orchestrator C2/C3:
   - C2: giữ payload schema-valid để đo, không grounding, không đủ điều kiện draft vận hành.
   - C3: gọi `ground_iocs`; giữ cả item bị loại cùng status để audit/eval; chỉ item `keep=true` được tính đủ
     điều kiện nối draft.
6. Retry đúng một lần khi provider error có thể retry hoặc response không hợp schema; sau đó fallback C1 regex
   với lỗi có cấu trúc, không traceback/raw CTI.
7. CLI/demo offline đọc `.txt` và fixture JSON tổng hợp, ghi một artifact JSON.
8. Test TDD offline cho success, lỗi, TLP, evidence và rò dữ liệu.

### Ngoài phạm vi

- SDK/provider/model thật, API key, đăng nhập, cloud LLM, model local lớn, lab/VM.
- Chọn OpenAI/Gemini/OpenRouter/Ollama hoặc model cụ thể; đo token/giá/latency thật.
- `store.py`, `draft/store.py`, queue, SQLite, portal, HTTP/auth, W05, OpenCTI, deploy.
- FastMCP, Hermes, Telegram, cron, tool agent, approve/reject/block/delete/shell.
- TTP RAG/C4, loader ATT&CK, actor/malware grounding hoàn chỉnh.
- Corpus thật, đánh giá hai người gán nhãn hoặc tuyên bố chất lượng model/injection.

## 4. File được phép sửa

Tên có thể điều chỉnh nhỏ nếu repo convention yêu cầu, nhưng không mở rộng thư mục.

| File | Việc |
|---|---|
| `extractor/phonghoa_extractor/llm_adapter.py` | Protocol/envelope, schema validator, policy, C2/C3 orchestration và lỗi typed. |
| `extractor/llm/run.py` | CLI offline; chỉ file/text/fixture/output cục bộ. |
| `extractor/llm/README.md` | Cách chạy, trạng thái mock và giới hạn. |
| `extractor/llm/fixtures/c2c3-response.json` | Phản hồi tổng hợp gồm một IOC grounded và một IOC bịa. |
| `extractor/tests/test_llm_adapter.py` | Unit test protocol/schema/policy/C2/C3/retry/fallback. |
| `extractor/tests/test_llm_cli.py` | Test CLI/demo, exit code, atomic output và không rò dữ liệu. |
| `docs/prompts/extractor-v1.md` | Prompt versioned dạng dữ liệu, chỉ nếu file chưa có; không phụ thuộc provider. |
| `docs/PROGRESS.md` | Cập nhật đúng trạng thái mock/offline sau khi test đạt. |

**Cấm sửa:** `extractor/phonghoa_extractor/store.py`, toàn bộ `extractor/draft/`, `portal/`, `deploy/`,
`mcp-server/`, `workflow/`, SQLite/schema W05 và `PHONG-HOA-RUNS.json`.

## 5. Thiết kế tối thiểu

### 5.1 Interface provider

Không để provider trả thẳng draft. Interface logic đề xuất:

```python
class LLMProvider(Protocol):
    name: str
    destination: Literal["fake_offline", "local", "cloud"]
    egress: bool

    def generate(self, request: ProviderRequest) -> ProviderResponse: ...
```

`ProviderRequest` chỉ gồm prompt version, schema version, language, TLP và text. `ProviderResponse` gồm:

```text
status: completed | refusal | incomplete | error
payload: object | None
model_id: string (fake dùng scripted-v1)
usage: object | None (fake là null; không bịa token)
retryable: bool
error_code: string | None
```

Không log `text`, prompt đầy đủ, raw payload hoặc key. Exception bên ngoài được quy về mã lỗi ổn định.

### 5.2 Schema nội bộ `x01-extraction-response/1.0`

Root là object có đúng bốn khóa, không nhận khóa lạ:

```json
{
  "iocs": [
    {
      "type": "domain|ipv4|ipv6|url|email|md5|sha1|sha256",
      "value": "chuỗi không rỗng",
      "role": "attacker|victim|benign",
      "evidence": "quote nguyên văn không rỗng"
    }
  ],
  "techniques": [{"id": "T1566.002", "evidence": "quote nguyên văn"}],
  "malware": [{"name": "...", "evidence": "quote nguyên văn"}],
  "actors": [{"name": "...", "evidence": "quote nguyên văn"}]
}
```

Validator phải từ chối: root/list sai kiểu, thiếu/thừa khóa, item sai kiểu, field thiếu/thừa, bool dùng như số,
enum sai, chuỗi rỗng và số lượng/kích thước vượt giới hạn. Giới hạn ban đầu đề xuất: raw provider response tối đa
1 MiB, mỗi danh sách tối đa 500 item, mỗi field tối đa 8 KiB. Các giới hạn là bảo vệ độ bền, không phải số đo
model; test biên và ghi trong README.

Không tự sửa tên field, không ép số thành chuỗi, không bỏ im field lạ. Schema provider thật về sau được sinh/ánh
xạ từ hợp đồng này; vẫn phải validate lần nữa sau nhận.

### 5.3 TLP/egress policy

Policy chạy **trước** `provider.generate`:

| Điều kiện | Kết quả |
|---|---|
| `destination=fake_offline`, `egress=false` | Cho phép fixture tổng hợp ở mọi TLP; artifact ghi `egress=false`. |
| `destination=cloud` ở task này | Từ chối `egress_not_configured` trước khi provider được gọi. |
| Cloud + AMBER/AMBER+STRICT/RED (tương lai) | Luôn từ chối. |
| Cloud + GREEN (tương lai) | Mặc định từ chối; cần quyết định chia sẻ chứng minh đích thuộc community được phép. |
| Cloud + CLEAR (tương lai) | Mặc định từ chối tới khi có quyền nguồn/giấy phép và provider/destination được duyệt. |

TLP hợp lệ: `TLP:CLEAR`, `TLP:GREEN`, `TLP:AMBER`, `TLP:AMBER+STRICT`, `TLP:RED`; canonicalize tương tự
`drafts.py` nhưng không sửa file đó. Nếu tránh lặp nhỏ này cần refactor thì để task riêng, không mở scope.

Test dùng spy provider để chứng minh provider call count bằng 0 khi policy từ chối. Không nhận một cờ CLI kiểu
`--allow-cloud` vì người chạy không được vô tình biến nó thành phê duyệt chia sẻ.

### 5.4 C2 và C3

**C2**

1. Policy -> provider -> envelope -> schema.
2. Giữ payload schema-valid, kể cả IOC không có trong nguồn, để evaluator đo FP/hallucination.
3. Artifact bắt buộc:

```json
{
  "config": "C2",
  "purpose": "evaluation-only",
  "operational_draft_eligible": false,
  "provider": {"name": "scripted", "model_id": "scripted-v1", "egress": false}
}
```

Không import/call store hoặc draft CLI. Test monkeypatch/spies phải chứng minh không có write path.

**C3**

1. Cùng policy/envelope/schema như C2.
2. Chuyển `iocs` sang `ground_iocs(payload["iocs"], source_text)`.
3. Serialize `kind/type/value/evidence/span/keep/status/warning`; bảo toàn item bị loại để audit.
4. `operational_draft_eligible=true` chỉ khi run completed hoặc fallback C1 và mọi item `keep=true` đều có
   exact span. Cờ này chỉ nói artifact đủ điều kiện cho bước tích hợp sau, **không ghi draft**.
5. Techniques/malware/actors được giữ trong phần `unverified_semantic_items` với
   `operational_draft_eligible=false` cho từng item ở lát cắt này; không giả vờ đã grounding TTP/RAG.

### 5.5 Retry và fallback

- Tối đa 2 provider calls tổng cộng: lần đầu + 1 retry.
- Retry: `provider_error` với `retryable=true` hoặc `invalid_response`.
- Không retry: policy/TLP, refusal, incomplete do giới hạn được khai báo non-retryable, input sai.
- Sau hai response lỗi: chạy C1 regex hiện có trên cùng text, artifact ghi
  `result_mode="regex_fallback"`, `model_items_used=false`, `attempts=2` và mã lỗi tổng quát.
- Không đưa raw response/error/message chứa CTI vào artifact, stderr hoặc test snapshot.
- C2 fallback vẫn `evaluation-only`; không biến fallback thành số đo C2 model.

## 6. CLI và artifact demo

Interface đề xuất:

```powershell
.venv\Scripts\python.exe extractor\llm\run.py `
  --config C3 `
  --input extractor\llm\fixtures\report.txt `
  --response extractor\llm\fixtures\c2c3-response.json `
  --language vi `
  --tlp TLP:AMBER `
  --output <temp>\c3-result.json
```

Fixture `report.txt` có thể được tạo trong test/temp thay vì commit nếu không muốn thêm file thứ tám. Provider
fake không egress nên TLP:AMBER chỉ chứng minh policy phân biệt đích, không phải cho phép AMBER lên cloud.

Artifact tối thiểu:

```text
schema_version, config, purpose, source.sha256, language, tlp,
provider{name,model_id,destination,egress}, prompt_version,
attempts, result_mode, operational_draft_eligible,
iocs/raw_iocs, unverified_semantic_items, warnings, error_codes
```

Không ghi nguyên source text vào artifact adapter. Evidence quote/span trong item C3 là dữ liệu cần review; fixture
chỉ tổng hợp. Output phải ghi atomic (temp cùng thư mục rồi replace); lỗi không tạo/ghi đè output cũ.

Exit code: `0` khi completed hoặc regex fallback có artifact hợp lệ; `1` cho input/provider/policy/schema lỗi không
thể tạo artifact; `2` cho CLI usage. Stdout chỉ summary count/config/mode/output; stderr không chứa source/raw
response.

## 7. Test offline theo TDD

Viết test đỏ trước, sau đó implementation nhỏ nhất làm xanh.

### 7.1 Schema/envelope

1. Nhận đúng payload đủ bốn list, kể cả list rỗng.
2. Từ chối root sai, thiếu/thừa key, field sai kiểu/enum, chuỗi rỗng, item thừa field.
3. Từ chối response >1 MiB, list >500, field >8 KiB mà không in marker nhạy cảm.
4. Refusal/incomplete/error không bị parse như completed payload.

### 7.2 TLP/egress

5. Fake offline được gọi với CLEAR/GREEN/AMBER/AMBER+STRICT/RED và luôn ghi `egress=false`.
6. Cloud fake/spied bị từ chối trước call cho cả năm TLP trong implementation hiện tại.
7. Riêng GREEN chứng minh không có suy luận “GREEN => cloud allowed”.
8. TLP sai kiểu/nhãn bị từ chối trước provider.

### 7.3 C2/C3/evidence

9. C2 giữ IOC bịa trong raw result nhưng `operational_draft_eligible=false` và không import/call store.
10. C3 cùng response: IOC có quote đúng được normalize + span exact; IOC bịa có `keep=false,status=bia`.
11. Evidence invented, substring hostname, declared type sai và non-string bị loại qua code grounding hiện có.
12. Semantic items chưa grounded nằm ở `unverified_semantic_items`, không vào danh sách đủ điều kiện draft.
13. Unicode/emoji: `source[start:end] == evidence` theo code point Python.

### 7.4 Retry/fallback/CLI

14. Invalid response rồi valid: call count 2, dùng lần hai.
15. Hai invalid/retryable error: call count 2, fallback C1, không dùng model item.
16. Refusal non-retryable: call count 1 và kết quả/lỗi đúng contract đã chọn.
17. Input/response/output trùng đường dẫn hoặc hard link bị chặn; output cũ không đổi khi lỗi.
18. CLI demo C2 và C3 qua process riêng; JSON deterministic (trừ timestamp — tốt nhất không thêm timestamp).
19. Marker source/raw response không xuất hiện trong stdout/stderr/exception khi lỗi.
20. Test không mở socket, không đọc env key và không gọi Internet; monkeypatch socket để fail nếu có egress.

Chạy nhóm liên quan trước, sau đó full suite/lint vì file mới nằm trong package chung.

## 8. Acceptance criteria

| Tiêu chí | PASS khi |
|---|---|
| Đúng base/phạm vi | Diff chỉ ở file cho phép; không đổi store/portal/deploy/mcp/workflow/RUNS. |
| Không egress | Test socket guard đạt; provider fake `egress=false`; không đọc key/env. |
| Schema | Mọi test positive/negative/limits đạt; refusal/incomplete không lọt như payload. |
| TLP | Cloud spy có 0 call; GREEN mặc định deny; AMBER/RED không có đường cloud. |
| C2 | Giữ raw hallucination để đo, luôn evaluation-only, không có write/draft path. |
| C3 | IOC grounded có exact quote/span; hallucination/type/evidence sai bị loại bằng code hiện có. |
| Retry/fallback | Tối đa hai calls; lỗi lần hai chuyển C1; artifact nói rõ fallback, không giả C2/C3 model success. |
| Demo | Hai lệnh C2/C3 offline exit đúng, artifact JSON parse được và source hash tái hiện được. |
| Không rò dữ liệu | Marker tổng hợp không xuất hiện trong stderr/stdout/error artifact. |
| Regression | Targeted tests, full `pytest`, Ruff check/format và `git diff --check` exit 0. |

Không được ghi PASS chất lượng model, prompt injection, TTP, corpus, HTTP/auth/OpenCTI/lab. Mock PASS chỉ chứng minh
hợp đồng và kiểm soát code offline.

## 9. Lệnh kiểm chứng phải báo

Giải thích: các lệnh dưới chạy test adapter/CLI, toàn suite, lint/format và kiểm whitespace diff trên đúng tree.

```powershell
.venv\Scripts\python.exe -m pytest extractor\tests\test_llm_adapter.py extractor\tests\test_llm_cli.py -q
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\ruff.exe check .
.venv\Scripts\ruff.exe format --check .
git diff --check
git status --short
git rev-parse HEAD
```

Bàn giao phải ghi từng lệnh, exit code, số test, Python/Ruff version, base/commit/SHA, `git status`, diffstat và
đường dẫn artifact demo. Nếu thiếu executable/dependency, báo UNVERIFIED; không tự cài dependency hoặc gọi cloud.

## 10. Dependency

**Không thêm dependency** ở lát cắt này: dùng `dataclasses`, `typing.Protocol`, `json`, `hashlib`, `pathlib` và
code repo. Validator hẹp dễ review hơn việc thêm framework chỉ để kiểm một schema cố định.

Khi triển khai B sau này mới đánh giá ghim FastMCP theo phiên bản tương thích Hermes/MCP. Khi thêm provider thật,
mới quyết định SDK/Pydantic/jsonschema dựa trên provider được người dùng chọn; phải ghi version/license và test
schema mapping. Không sao chép SDK hoặc tự viết client HTTP nếu SDK chính thức đáp ứng.

## 11. Bước nối thật sau lát cắt này

1. Leader nghiệm thu diff, test và hai artifact C2/C3 mock; xác nhận chỉ là mock.
2. Nhóm chọn provider/model và destination theo chi phí, điều khoản, dữ liệu và tài nguyên; không suy từ brief.
3. Thêm **một** provider adapter thật trong task riêng; test bằng synthetic response trước, sau đó smoke có quyền
   với dữ liệu được phép. Không gửi TLP:GREEN nếu chưa chứng minh community/destination.
4. Mở rộng eval runner để C2/C3 dùng adapter; corpus thật phải theo GUIDELINE và có giai đoạn hai người gán độc
   lập. Báo model/prompt/schema/dataset hash, token/cost/latency từ run thật.
5. Chỉ sau khi C3 grounding ổn định mới nối artifact đủ điều kiện sang draft contract/W05; quyền ghi/duyệt do
   backend cưỡng chế, agent không có approve/delete/block.
6. TTP/C4 là task riêng: ghim snapshot ATT&CK chính thức, provenance và nhãn TTP thật trước khi báo F1.

## 12. Demo được phép tuyên bố

“Provider giả lập trả một IOC có bằng chứng và một IOC bịa. C2 giữ cả hai để đánh giá và không cho vào draft;
C3 dùng code grounding hiện có, giữ IOC có exact span và đánh dấu IOC bịa bị loại. TLP:GREEN vẫn không mở cloud;
toàn bộ demo không mạng, không key, không model thật.”

Không được đổi câu này thành “AI extractor đã đạt chất lượng”, “chống prompt injection”, “Hermes đã chạy”,
“TLP an toàn” hoặc “sẵn sàng production”.
