# ADR 0016 — Xuất STIX 2.1 ngoại tuyến từ final approve audit

- Ngày: 11/11/2026
- Trạng thái: Đã chấp nhận

## Bối cảnh

W05 đã có payload bất biến, selection audit và final approve audit trong SQLite v2. Lát cắt này cần tạo artifact
STIX có thể kiểm độc lập mà chưa nối token, outbox hay OpenCTI. Ba lớp phải giữ riêng: payload extractor, quyết
định duyệt cục bộ và ingestion OpenCTI tương lai.

## Các phương án

1. Converter CLI chỉ đọc, xuất một bundle local.
2. Outbox SQLite có retry/retention.
3. Gọi ImportFileStix/OpenCTI trực tiếp.

## Quyết định

Chọn phương án 1. Getter mở SQLite `mode=ro`, `BEGIN` trước schema/data và chỉ chấp nhận final approve audit
nhất quán. Bundle gồm standard marking, exporter Identity, tám SCO hỗ trợ và Report; provenance hash/metadata
nằm trong `Report.external_references`, không có sidecar hay danh tính reviewer.

SCO dùng UUIDv5 chuẩn OASIS. Identity, Report và Bundle dùng ba child namespace UUIDv5 deterministic riêng;
đây là ngoại lệ có chủ ý với khuyến nghị UUIDv4 cho SDO/Bundle. Validator chạy profile MUST/schema/ref và
`strict --disable 103`; plain strict phải chỉ báo check 103.

Publish local dùng temp hoàn chỉnh cùng parent và hardlink `os.link(temp, output)`: không replace, không truncate,
không ghi đè. Existing byte-identical là idempotent; existing khác bytes là lỗi. DB/sidecars/config và alias bị
từ chối.

## Hệ quả (tốt / xấu / cách giảm thiểu)

- Tốt: deterministic, một artifact tự chứa provenance, test offline và không cần secret/runtime STIX SDK.
- Tốt: final audit là nguồn quyền duy nhất; reviewer subject chỉ tồn tại nội bộ trong snapshot `repr=False`.
- Xấu: không có retry/outbox và chưa biết OpenCTI thật sẽ xử lý bundle thế nào; dành cho task/lab riêng.
- Xấu: atomic no-clobber chỉ được kiểm trên local NTFS trong thư mục caller tin cậy; network share, crash/power
  loss và kẻ có quyền đổi directory đồng thời chưa được cam kết.
- Giảm thiểu: pin validator 3.3.2 có lock hash, test negative schema/marking/ref, test race cùng/khác bytes và
  ghi rõ profile `strict except 103` thay vì gọi strict PASS.
