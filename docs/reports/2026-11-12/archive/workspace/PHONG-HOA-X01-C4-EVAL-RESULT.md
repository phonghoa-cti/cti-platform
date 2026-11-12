# X01-C4-EVAL — kết quả triển khai

Ngày: 11/11/2026

## Kết luận

**PASS** cho contract offline/synthetic được giao, gồm rework R1–R4. C4 có query manifest explicit, preflight
toàn dataset (kể cả report rỗng/JSON lỗi) trước generate, artifact schema 1.2 strict/no-clobber và reporter
C4-only hoặc C3 audit 1.1 + C4. Audit được bind với source/catalog; fallback chỉ nhận hai mã retryable của
adapter. C1–C3 không regress trong các phép so compatibility đã chốt.

Không coi `fake_offline` hoặc synthetic smoke là chất lượng model/C4/RAG/TTP semantic.

## Ref và phạm vi

- Target: `cti-x01-c4-eval`
- Branch: `feat/x01-c4-eval-20261111`
- Base: `654443e6ede6557f0629fc0886ca56fff782b193`
- Commit cuối: `5e0cbf4d40559b4380d29f7a2ea7d6c5b3ed9d35`
- Rework từ `7ece3c3`: đúng 4 file allowlist, `+113/-7`; `git diff --check 7ece3c3..HEAD` exit 0.
- Tổng từ base: 9 file allowlist; không có file ngoài phạm vi.
- Target status: sạch. Source `cti-x01-c4-adapter` vẫn đúng base, status sạch, diff quiet exit 0.

## Đã triển khai

- Manifest UTF-8 strict tối đa 16 KiB, duplicate/BOM/nonfinite/bounds/query validator dùng lại, DTO frozen và
  exact dataset ID map.
- C4 preflight report/metadata/labels toàn bộ trước fixture provider và trước generate đầu tiên; document 1..256,
  report tối đa 1 MiB theo code point và UTF-8 byte.
- Adapter C4 đúng một retrieval/document; lifecycle 1/2/2 call cho success/retry/fallback, audit không gọi provider.
- Artifact 1.2 exact projection, năm limitations cố định, context/catalog/audit/count invariants; không ghi raw
  query/context.
- C4 writer temp + fsync + hardlink no-clobber; output tồn tại/race/alias bị từ chối. Cleanup lỗi sau commit trả
  lỗi nhưng giữ output đã publish; test dọn temp sở hữu riêng.
- Reporter strict nhận C4 đơn hoặc C3 audit 1.1 + C4, kiểm cohort/per-ID provenance và không render dữ liệu nhạy.
- ADR 0009, README, fixture query và PROGRESS đã cập nhật.

## Kiểm chứng thực chạy

| Kiểm tra | Kết quả |
|---|---|
| Probe Leader nguyên bộ | RED exit 1: **14 failed/4 passed**; GREEN exit 0: **18 passed** |
| Probe + 4 file regression bắt buộc | exit 0; **181 passed**, 0 failure/error/skip; JUnit trong evidence |
| Ruff check 4 file Python đổi | exit 0 |
| Ruff format --check | exit 0 |
| `git diff --check 7ece3c3..HEAD` | exit 0 |
| C1 base/HEAD | byte-identical |
| C2/C3 base/HEAD | bằng nhau sau khi chỉ bỏ `evaluator.git_ref` |
| Markdown C1/C2/C3 trên input cố định | byte-identical giữa base reporter và HEAD reporter |
| C4 standalone hai output mới | cả hai exit 0, SHA-256 bằng nhau |
| Reporter C4-only | exit 0 |
| C3 audit 1.1 + C4 reporter | cả evaluator/reporter exit 0 tại cùng HEAD |

Final demo SHA-256:

- `final-c4-a.json`: `23972a91ab9d8a82093a8726acd58a038c985d1f71d80d6e18f53dfe6cef2f3f`
- `final-c4-b.json`: `23972a91ab9d8a82093a8726acd58a038c985d1f71d80d6e18f53dfe6cef2f3f`
- `final-c3-audit.json`: `104e25d9842979530df9a3ae95568faea24a30eafd3a3fe891f6e6d366b9aa39`
- `final-c4-report.md`: `e84c2dd3e8b35e9d4bbddda7fa82566ec041039f418c51131ec8cbe37c5b3fe7`
- `final-c3-c4-report.md`: `8e41c16ce1ceac6def5bd79e60a7c3701be87fcd448307e2a5e4010a493d2605`

## Findings đã xử lý

1. Preflight ban đầu dựng provider trước khi đọc document cuối; test recorder bắt được và đã đổi thứ tự.
2. Writer ban đầu chỉ kiểm structural limits; đã thêm strict schema validation trước publish.
3. Strict validator import chạy trong pytest nhưng hỏng ở CLI direct vì runtime path khác; đã tái hiện, sửa và chạy
   lại toàn bộ 291 test.
4. R1: audit C4 nay bắt buộc khớp source SHA và catalog kind/version/SHA trước render/publish.
5. R2: fallback C4 chỉ nhận `provider_error` và `invalid_response`; mã terminal/không biết bị từ chối.
6. R3: JSON integer quá dài/recursion ở metadata hoặc labels C4 được đổi thành lỗi an toàn một dòng, không traceback.
7. R4: report rỗng bị chặn trong preflight trước khi load provider hoặc gọi generate.

## Evidence

Evidence rework: `x01-c4-eval-evidence\rework-r1-r4\` gồm probe RED/GREEN, pytest log/JUnit, compatibility
artifacts, demo JSON/Markdown, verification log và SHA-256 manifest.

`SHA256SUMS.txt` đã đối chiếu 22/22 file; manifest SHA-256:
`fab8d3329ab228558701b73be1f3060666203fec8a52f6b867adbf16704a397f`.

## UNVERIFIED / ngoài phạm vi

- Model/provider thật, model-only quality, retrieval/semantic/multilingual quality, TTP precision/recall/F1.
- Corpus thật được hai người gán nhãn, prompt-injection benchmark, token/chi phí/độ trễ.
- Cloud, W05/SQLite, OpenCTI, lab, production, crash durability và hostile directory mutation.

## Học thêm

- **Preflight**: kiểm toàn bộ input trước side effect đầu tiên để lỗi document cuối không tạo một phần kết quả.
- **No-clobber**: chỉ tạo file mới và từ chối ghi đè, kể cả khi có race giữa hai tiến trình.
- **Cohort**: nhóm artifact chỉ được so sánh khi dataset, fixture, evaluator và provenance liên quan khớp nhau.
