# X01 gold-pilot-v1 — kiểm tra mức sẵn sàng gán nhãn

## Mục tiêu

Lát cắt ngoại tuyến này kiểm inventory đúng 5 record, tối đa hai annotation/record, quyền lưu raw được khai
báo, evidence IOC theo token và TTP active trong catalog ATT&CK đã ghim. Kết quả chỉ cho biết hồ sơ có sẵn
sàng adjudication (hòa giải nhãn) hay chưa; không chứng minh corpus gold hoặc chất lượng model.

## Đầu vào

Dataset có `manifest.json`, `records/`, `annotations/`, `raw/`; chỉ cho phép `.gitignore` và hai thư mục rỗng
`adjudications/`, `suggestions/`. Tổng tối đa 22 file/8 MiB; JSON 256 KiB, raw 512 KiB. Mọi JSON dùng schema
đóng, UTF-8 strict, không BOM, duplicate key, non-finite number hoặc ép kiểu. File symlink, junction, hardlink,
orphan và nested directory bị từ chối.

Manifest và record dùng `schema_version=gold-pilot-v1`. Record chỉ nhận TLP:CLEAR/GREEN, ngày lịch hợp lệ,
HTTPS không userinfo, raw normalized LF và pin ATT&CK khớp. `prohibited` luôn INVALID; `unknown` bắt buộc
`link-only`. `translation_of` chỉ trỏ original cùng `duplicate_group`, không chain/cycle.

Annotation có 0–2 file, annotator khác nhau. Evidence dùng code-point span trên raw normalized LF và SHA-256
substring. IOC phải normalize về đúng type/value khai báo; TTP phải active trong Enterprise catalog. Semantic
TTP luôn `unverified`.

## Trạng thái và report

Record reason theo thứ tự: `NEEDS_RIGHTS`, `NEEDS_LOCAL_RAW`, `NEEDS_SECOND_ANNOTATION`. Dataset reason là
`RECORDS_NOT_READY`, rồi `NO_FINDINGS_ONLY` khi cả năm record đủ hồ sơ nhưng hai union đều rỗng. Agreement là
Jaccard của attacker IOC triple và exact ATT&CK ID; record thiếu điều kiện là `unavailable`.

Report `gold-pilot-readiness-v1` là JSON compact, sort key, LF cuối và không chứa raw, quote, IOC, URL,
publisher, annotator, path hoặc timestamp. Fingerprint bao gồm hash byte gốc của mọi file dataset hợp lệ.

## CLI và writer

`check_gold_pilot.py` bắt buộc bốn cờ dataset/snapshot/pin/report. READY exit 0; NOT_READY/INVALID exit 2;
I/O exit 1. Writer no-clobber dùng temp cùng parent, fsync và hard-link làm commit point; không ghi đè hoặc ghi
vào/alias input. Cleanup lỗi sau commit chỉ cảnh báo vì report đã publish.

## Ngoài phạm vi

Không gọi model/mạng/cloud, không ghi DB/OpenCTI, không xác minh quyền thật, độc lập annotator, semantic TTP,
gold/model/RAG quality, hostile mutation, crash/power-loss, lab hay production.
