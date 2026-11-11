# ADR 0009 — Artifact evaluator và cohort reporter C4 ngoại tuyến

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận cho synthetic/fake_offline

## Bối cảnh

Adapter C4 đã nối retrieval ATT&CK vào request nhưng chưa có artifact evaluator hoặc bảng reporter. Query vẫn do
caller cung cấp, còn C3/C4 cần so sánh trên cùng dataset, response fixture, evaluator và catalog mà không phát tán
raw query/context.

## Phương án

1. Chỉ thêm evaluator: ít mã hơn nhưng chưa có đầu ra đọc được cho chương 4.
2. Thêm evaluator schema 1.2 và reporter C4 trong cùng lát: kiểm được contract và cohort đồng provenance.
3. Chờ corpus gold/model thật: cần cho chất lượng, nhưng không cần để kiểm contract offline.

## Quyết định

Chọn phương án 2. C4 nhận query manifest `explicit-per-document-v1` UTF-8 strict, digest raw bytes và ID khớp
chính xác dataset. Toàn bộ dataset, label, metadata, response fixture và provider được preflight trước generate đầu
tiên. Artifact 1.2 ghi digest/provenance/context metadata, score IOC, source/quote/catalog audit và năm giới hạn cố
định; không ghi raw query hoặc raw context.

C4 publish bằng temp cùng thư mục, `fsync`, rồi `os.link` làm commit point no-clobber. Reporter chấp nhận C4 đơn
hoặc C3 audit 1.1 + C4 1.2 với projection cùng cohort; các cohort C1–C3 cũ giữ nguyên contract và rendering.

## Hệ quả và giới hạn

- Tốt: deterministic, không egress, không đổi adapter/retriever/audit, có provenance và failure boundary rõ.
- Xấu: hardlink phụ thuộc filesystem; cleanup lỗi sau commit trả lỗi nhưng output đã publish vẫn được giữ.
- Chưa xác minh: model/RAG quality, semantic TTP, corpus hai người gán nhãn, injection benchmark, cloud,
  OpenCTI, lab, production, crash durability và hostile directory mutation.
