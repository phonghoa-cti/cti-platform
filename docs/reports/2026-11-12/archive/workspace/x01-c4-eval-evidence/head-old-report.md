# Báo cáo đánh giá X01

> **SYNTHETIC SMOKE — không phải chất lượng model hoặc corpus thật.**

## Provenance

| Config | Schema | Documents | Dataset SHA-256 | Input SHA-256 |
|---|---:|---:|---|---|
| C1 | 1.0 | 6 | `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5` | `8e4a1e6afbb2029ed521fcc87190e77aa337f4671bf4117fc5ce7d8682029b9f` |
| C2 | 1.0 | 6 | `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5` | `6b4464d7d2eae311c74e7e0614a97674a15b23a239fc5f8a083d526f970a9920` |
| C3 | 1.0 | 6 | `d42983e6a22eaf84604b8a48e9ce77e74cfa8d3e14ab4a1e8b2644241284e6e5` | `37adcb6668a00cbf0fb593c0644c5c17a03b4809ac2c5bed0ad680fa956795af` |

- C1: evaluator/provider/fixture không có trong schema C1.
- C2/C3 fixture manifest: `47c8ffe484a95d94fb596f4bab431e3a0d100d29302fd2d3e2d6995f56731249`; evaluator `654443e6ede6557f0629fc0886ca56fff782b193` / Python `3.12.13`; provider `fake_offline`, egress `false`.

## IOC aggregate

| Config | Documents | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1 | 6 | 7 | 3 | 1 | 0.700000 | 0.875000 | 0.777778 |
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
| C1 | domain | 2 | 2 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C1 | email | 1 | 1 | 0 | 0.500000 | 1.000000 | 0.666667 |
| C1 | ipv6 | 0 | 0 | 1 | 0.000000 | 0.000000 | 0.000000 |
| C1 | md5 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C1 | sha1 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C1 | sha256 | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
| C1 | url | 1 | 0 | 0 | 1.000000 | 1.000000 | 1.000000 |
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

## Giới hạn

- Chỉ là smoke tổng hợp với provider giả lập; chưa đo model hoặc corpus thật.
- C3 trộn candidate model với regex trước grounding, nên không phải metric model-only.
- TTP chỉ có consistency counts; semantic TTP, C4/RAG, W05, OpenCTI, lab và production chưa được xác minh.

---
Định dạng: `phonghoa-x01-eval-report/1`.
