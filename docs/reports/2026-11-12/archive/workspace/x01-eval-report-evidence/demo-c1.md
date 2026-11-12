# Báo cáo đánh giá X01

> **SYNTHETIC SMOKE — không phải chất lượng model hoặc corpus thật.**

## Provenance

| Config | Schema | Documents | Dataset SHA-256 | Input SHA-256 |
|---|---:|---:|---|---|
| C1 | 1.0 | 6 | `43fe0cab40d669fa0d2622349fcc9d34e05f2072c21939eeea4da49a08654557` | `8d4c217f95fb8a2b35dc4b8596a8d4d60e86501c61daf7d778f0529675cdfd76` |

- C1: evaluator/provider/fixture không có trong schema C1.

## IOC aggregate

| Config | Documents | TP | FP | FN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| C1 | 6 | 7 | 3 | 1 | 0.700000 | 0.875000 | 0.777778 |

C3: grounded model candidates + regex; not model-only.

## Result modes

| Config | Mode | TP | FP | FN | Precision | Recall | F1 |
|---|---|---:|---:|---:|---:|---:|---:|

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

## Giới hạn

- Chỉ là smoke tổng hợp với provider giả lập; chưa đo model hoặc corpus thật.
- C3 trộn candidate model với regex trước grounding, nên không phải metric model-only.
- TTP chỉ có consistency counts; semantic TTP, C4/RAG, W05, OpenCTI, lab và production chưa được xác minh.

---
Định dạng: `phonghoa-x01-eval-report/1`.
