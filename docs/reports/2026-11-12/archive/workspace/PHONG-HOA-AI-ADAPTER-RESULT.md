# Kết quả AI-IMPLEMENT — adapter LLM C2/C3 ngoại tuyến

## Kết luận

**PASS trong phạm vi mock/offline của brief.** Đã triển khai adapter trung lập provider, provider kịch bản
`fake_offline`, schema/metadata/TLP gate, C2 evaluation-only, C3 grounding, retry một lần rồi regex fallback,
CLI atomic và fixture/demo ngoại tuyến. Không gọi model thật, mạng, key, SQLite, lab, VM hoặc cloud; không nối
store/draft/W05/OpenCTI.

Đây **không** phải bằng chứng chất lượng model, chống prompt injection, TTP/C4, corpus thật hay production-ready.

## Git và phạm vi

- Tree: `cti-platform-ai-llm-adapter`
- Branch: `feat/x01-llm-adapter-offline-20261110`
- Base/merge-base: `e83bb3f5d8e4ec90e1c0ea48268342e3497c9424`
- Commit hiện tại: `ed24bd817de1e4633693d27f47e8e5fc629451ad`
- Commit ban đầu: `2ac8605e4f96e7b888205a5fe302a840ffca72bc` — `feat: add offline C2 C3 LLM adapter`
- Commit rework R1: `ed24bd817de1e4633693d27f47e8e5fc629451ad` — `fix: validate adapter input types before enums`
- Trạng thái sau commit: sạch (`git status --porcelain=v1` không có output).
- Diff từ base: 9 file được brief cho phép, `1084 insertions`, không có deletion. Riêng R1: 2 file,
  `47 insertions`, `3 deletions`; không đổi
  `store.py`, `draft/`, `portal/`, `deploy/`, `mcp-server/`, `workflow/`, SQLite hay `PHONG-HOA-RUNS.json`.
- Không push, PR, merge hoặc deploy.

## Hành vi đã kiểm chứng

- Policy chạy trước `generate`: chỉ `destination=fake_offline` và `egress is False` được phép. `local`,
  `cloud`, `unknown`, metadata sai kiểu và TLP sai đều bị từ chối; spy provider có call count 0.
- Fake offline chấp nhận năm nhãn TLP hợp lệ nhưng luôn ghi `egress=false`; `TLP:GREEN` không mở cloud.
- Response/model/error metadata bị giới hạn; payload/list/field có giới hạn 1 MiB/500/8 KiB; không đưa raw
  response, source text hay exception provider vào artifact/lỗi.
- Refusal/incomplete và provider error non-retryable trả mã ổn định, call count 1. Invalid/retryable/exception
  được gọi tối đa 2 lần rồi fallback regex; artifact ghi rõ `regex_fallback`, không giả thành model success.
- C2 demo giữ 2 IOC (gồm IOC bịa), `operational_draft_eligible=false`.
- C3 demo giữ 1 IOC có exact Unicode span, đánh dấu 1 IOC bịa `keep=false,status=bia`, và giữ semantic item ở
  `unverified_semantic_items` với eligibility false.
- CLI chặn source/response/output trùng hoặc hard link, ghi output atomic, bảo toàn output cũ khi lỗi và không
  mở socket trong test.
- Rework R1: `language`/`config` dạng list, dict, None, bool, int hoặc enum sai đều trả
  `AdapterError(code="invalid_input")` trước provider; 0 provider call, không TypeError và không lộ source marker.

## RED/GREEN và kiểm chứng cuối

Môi trường: Python `3.12.13`, Ruff `0.17.4`, Git `2.55.0.windows.1`. Dùng Python từ
`cti-platform-start\.venv`, cwd/PYTHONPATH là tree AI; không cài/sửa dependency.

| Lệnh/kiểm tra | Exit | Kết quả |
|---|---:|---|
| Baseline `python -m pytest -q` tại base | 0 | 236 test đạt |
| RED khung adapter/CLI | 1 | 44 lỗi như dự kiến trước implementation |
| RED exception provider | 1 | 1 lỗi; raw exception thoát ra trước fix |
| RED fixture raw >1 MiB | 1 | 1 lỗi; output từng được tạo trước fix |
| RED trường artifact tối thiểu | 1 | 3 lỗi; thiếu `warnings`/summary `output` |
| RED R1 `language/config` list/dict | 1 | 4/12 ca lỗi đúng triệu chứng `TypeError`; 8 ca còn lại đã ổn |
| GREEN regression R1 | 0 | 12/12 đạt; lỗi ổn định, 0 provider call, không lộ marker |
| `python -m pytest extractor/tests/test_llm_adapter.py extractor/tests/test_llm_cli.py -q --junitxml=.../targeted.xml` | 0 | 58/58 đạt (46 ca cũ + 12 ca mới); 0 failure/error |
| `python -m pytest -q --junitxml=.../full-suite.xml` | 0 | 282/282 đạt; 0 failure/error |
| `python -m ruff check .` | 0 | All checks passed |
| `python -m ruff format --check .` | 0 | 96 file đã đúng format |
| `git diff --check HEAD` trước commit | 0 | Không lỗi whitespace |
| Demo C2 với `--language vi --tlp TLP:GREEN` | 0 | 2 raw IOC, mock-only, không đủ điều kiện draft |
| Demo C3 với `--language vi --tlp TLP:GREEN` | 0 | 1 kept + 1 rejected, mock-only |

Chi tiết các vòng RED/GREEN ở `ai-adapter-evidence/RED-GREEN.md`. Tự rà diff lần cuối không thấy lỗi còn lại
trong phạm vi; không có reviewer độc lập vì brief yêu cầu tự làm, không giao bot/agent khác.

## Artifact và checksum SHA-256

Thư mục: `ai-adapter-evidence`

| Artifact | Byte | SHA-256 |
|---|---:|---|
| `c2-result.json` | 1296 | `27e053e668505e01b6e8422f1c7d7f5121876b3201f39ac22b63247af1eb31fa` |
| `c3-result.json` | 1541 | `06a250d5161d92187c0b579b934e5d8cc423eaf40283020cb06b7eac2b55a3b9` |
| `targeted.xml` | 8597 | `57ba86d6196d28975ba1004cf4d52dbe57fbce48f5c4cfa5fe726b827ca75fb9` |
| `full-suite.xml` | 39149 | `906961cecc68e7dfd70fc56decc6127f7a3af56b50d21dc5f26d769696bbfa6a` |
| `leader-validation.json` | 1277 | `573da0fa2380699f88f31394a1a170da94545d0ef7ae2e15ede1fffe87d05528` |
| `RED-GREEN.md` | 1255 | `affd78b6ff746ce32f047c88520eee8e86321524b280d0f0d0ea65eae4b41a94` |

Source fixture hash trong cả hai demo:
`71dc8cb5c1afd86d286017ab66fe01821a51c9a759d394d75dcb3767fa833475`.

## Chưa kiểm chứng / task riêng

- Model/provider thật, token/giá/latency, SDK mapping và quyền destination: **UNVERIFIED**.
- Chất lượng C2/C3 trên corpus thật và corpus hai người gán nhãn: **UNVERIFIED**.
- TTP/C4, prompt injection, HTTP/auth/OpenCTI, lab và production: **UNVERIFIED / ngoài scope**.
- Bất kỳ egress thật nào vẫn bị deny; cần task riêng có quyết định provider, quyền dữ liệu và destination.
