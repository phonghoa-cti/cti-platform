# Báo cáo đánh giá X01

> **SYNTHETIC SMOKE — không phải chất lượng model hoặc corpus thật.**

## Provenance

| Config | Schema | Documents | Dataset SHA-256 | Input SHA-256 |
|---|---:|---:|---|---|
| C3 | 1.1 | 6 | `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5` | `e0750178ae01420b3eb327697317f42c84b58d78ca0841fb777a691231cbfeb8` |
| C4 | 1.2 | 6 | `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5` | `3ac261f794a5b0dd9a2372de338991ec16ab7a54a1530d5b83948ca7d767d504` |

- C1: evaluator/provider/fixture không có trong schema C1.
- C2/C3 fixture manifest: `47c8ffe484a95d94fb596f4bab431e3a0d100d29302fd2d3e2d6995f56731249`; evaluator `654443e6ede6557f0629fc0886ca56fff782b193` / Python `3.12.13`; provider `fake_offline`, egress `false`.
- ATT&CK catalog: `synthetic` / `synthetic-1` / `05f5af7bcf44f158da47e3645bd44cf193d0fca2b52b4d12a16fee5827c9653f`.
- C4 query manifest: `e36df38f0f44417bb82eb353f66f731739ed6c0283a39247a6f053b3b1886847`; ATT&CK catalog: `synthetic` / `synthetic-1` / `05f5af7bcf44f158da47e3645bd44cf193d0fca2b52b4d12a16fee5827c9653f`.

## IOC aggregate

| Config | Documents | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C3 | 6 | 7 | 3 | 1 | 0.700000 | 0.875000 | 0.777778 |
| C4 | 6 | 7 | 3 | 1 | 0.700000 | 0.875000 | 0.777778 |

C3: grounded model candidates + regex; not model-only.
C4: grounded model candidates + regex; not model-only.

## Result modes

| Config | Mode | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| C3 | model_completed | 6 | 3 | 0 | 0.666667 | 1.000000 | 0.800000 |
| C3 | regex_fallback | 1 | 0 | 1 | 1.000000 | 0.500000 | 0.666667 |
| C4 | model_completed | 6 | 3 | 0 | 0.666667 | 1.000000 | 0.800000 |
| C4 | regex_fallback | 1 | 0 | 1 | 1.000000 | 0.500000 | 0.666667 |

## IOC by type

| Config | Type | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| C3 | domain | 2 | 2 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C3 | email | 1 | 1 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C3 | ipv6 | 0 | 0 | 1 | 0.000000 | 0.000000 | 0.000000 |
| C3 | md5 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C3 | sha1 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C3 | sha256 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C3 | url | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C4 | domain | 2 | 2 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C4 | email | 1 | 1 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C4 | ipv6 | 0 | 0 | 1 | 0.000000 | 0.000000 | 0.000000 |
| C4 | md5 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C4 | sha1 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C4 | sha256 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C4 | url | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |

## TTP consistency counts

> Counts chỉ kiểm tra source/quote/catalog consistency; không phải Precision/Recall/F1 hay semantic truth.

| Config | Technique items | matched | missing | not_found | ambiguous | active | inactive | unknown | not_checked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C3 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| C4 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |

## Giới hạn
- C4 retrieval/context transmission không chứng minh model sử dụng tri thức hay chất lượng.
- C4 TTP audit chỉ kiểm source/quote/catalog; semantic TTP vẫn chưa xác minh.

- Chỉ là smoke tổng hợp với provider giả lập; chưa đo model hoặc corpus thật.
- C3 trộn candidate model với regex trước grounding, nên không phải metric model-only.
- TTP chỉ có consistency counts; semantic TTP, C4/RAG, W05, OpenCTI, lab và production chưa được xác minh.

---
Định dạng: `phonghoa-x01-eval-report/1`.
