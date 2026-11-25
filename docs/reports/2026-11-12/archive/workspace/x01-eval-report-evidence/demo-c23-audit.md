# Báo cáo đánh giá X01

> **SYNTHETIC SMOKE — không phải chất lượng model hoặc corpus thật.**

## Provenance

| Config | Schema | Documents | Dataset SHA-256 | Input SHA-256 |
|---|---:|---:|---|---|
| C2 | 1.1 | 6 | `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5` | `fd4a4669040499032e777a41b051826132354bb719b85ec309c5ebd212fb5443` |
| C3 | 1.1 | 6 | `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5` | `4c50357744151bc036225cc14b7ca6abc620e3c5a12df6a6a5528e1dde7ecd1d` |

- C1: evaluator/provider/fixture không có trong schema C1.
- C2/C3 fixture manifest: `5631818b600449cfda95e0d0fb0df25a1337831e4dd5e76b8d628970c2f27be8`; evaluator `984bd2136872f4c5fba4118e33cf02b5ca615f2d` / Python `3.12.13`; provider `fake_offline`, egress `false`.
- ATT&CK catalog: `synthetic` / `synthetic-1` / `05f5af7bcf44f158da47e3645bd44cf193d0fca2b52b4d12a16fee5827c9653f`.

## IOC aggregate

| Config | Documents | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C2 | 6 | 7 | 2 | 1 | 0.777778 | 0.875000 | 0.823529 |
| C3 | 6 | 7 | 3 | 1 | 0.700000 | 0.875000 | 0.777778 |

C3: grounded model candidates + regex; not model-only.

## Result modes

| Config | Mode | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| C2 | model_completed | 6 | 2 | 0 | 0.750000 | 1.000000 | 0.857143 |
| C2 | regex_fallback | 1 | 0 | 1 | 1.000000 | 0.500000 | 0.666667 |
| C3 | model_completed | 6 | 3 | 0 | 0.666667 | 1.000000 | 0.800000 |
| C3 | regex_fallback | 1 | 0 | 1 | 1.000000 | 0.500000 | 0.666667 |

## IOC by type

| Config | Type | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|
| C2 | domain | 2 | 1 | 0 | 0.666667 | 1.000000 | 0.800000 |
| C2 | email | 1 | 1 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C2 | ipv6 | 0 | 0 | 1 | 0.000000 | 0.000000 | 0.000000 |
| C2 | md5 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C2 | sha1 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C2 | sha256 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C2 | url | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C3 | domain | 2 | 2 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C3 | email | 1 | 1 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C3 | ipv6 | 0 | 0 | 1 | 0.000000 | 0.000000 | 0.000000 |
| C3 | md5 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C3 | sha1 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C3 | sha256 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C3 | url | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |

## TTP consistency counts

> Counts chỉ kiểm tra source/quote/catalog consistency; không phải Precision/Recall/F1 hay semantic truth.

| Config | Technique items | matched | missing | not_found | ambiguous | active | inactive | unknown | not_checked |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C2 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| C3 | 1 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |

## Giới hạn

- Chỉ là smoke tổng hợp với provider giả lập; chưa đo model hoặc corpus thật.
- C3 trộn candidate model với regex trước grounding, nên không phải metric model-only.
- TTP chỉ có consistency counts; semantic TTP, C4/RAG, W05, OpenCTI, lab và production chưa được xác minh.

---
Định dạng: `phonghoa-x01-eval-report/1`.
