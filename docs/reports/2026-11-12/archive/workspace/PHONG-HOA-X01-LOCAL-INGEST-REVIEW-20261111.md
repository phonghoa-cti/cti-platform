# X01 local ingest — review Leader, 11/11/2026

Kết luận: **NEEDS_REWORK R1–R4**, chỉ tài liệu; chưa nghiệm thu để triển khai.

Root: `$WORKSPACE`.

## Đầu vào và quyết định

- Callback nghiên cứu: `fbdd5dc0-d763-40c4-9c6f-ac9c81bf1b70`, thread `db3614d3-ca8d-4b02-b9d6-3f41fc7363f2`.
- Research SHA-256: `61790211855b8298d2c5e28700dd066a50dcfe84bf0e096e1978f869a6fc445b`.
- Implementation brief SHA-256: `a6798d1ef55009c361aed2fb1f6dc20fade3a0a4591aba7a842c560d9ec81bcb`.
- Source kiểm trực tiếp: `cti-x01-gold-pilot`, HEAD `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`, status sạch.
- Giữ phương án B: CLI mới, text/PDF cục bộ, tái dùng `build_regex_draft`, raw hash tách canonical hash, không sửa CLI cũ hoặc C1–C4.
- Giữ canonical text literal như đề xuất: TXT decode UTF-8 strict; PDF nối text từng trang bằng `\n\f\n`; không tự chuẩn hóa newline/NFC/trim. Điều này là hợp đồng mới, không đồng nghĩa byte/hash parity với CLI cũ.
- Không cài dependency, tạo worktree hay chạy parser PDF trong review này. Không thêm OCR, model, network runtime, SQLite, HTTP/UI, lab hoặc phát hành.

## R1 — No-clobber không được bảo đảm

Brief dòng 66 dùng preflight output chưa tồn tại rồi `os.replace`. Một writer bình thường có thể tạo file giữa hai bước và bị ghi đè. Đây là race xuất file thông thường, không cần giả định hostile directory mutation.

Leader đã chạy probe stdlib với Python 3.12 của dự án, temp riêng: preflight absent → writer B tạo output → writer A gọi replace. Kết quả `replace_overwrites_intervening_writer=true`, exit 0; temp được dọn. [Python 3.12 os.replace](https://docs.python.org/3.12/library/os.html#os.replace) xác nhận hành vi thay file có sẵn.

Sửa hai tài liệu: publish no-clobber bằng primitive không thay target tồn tại, tái dùng cách `os.link` temp cùng parent đã có tại `extractor/eval/report.py:933` và `phonghoa_extractor/gold_pilot.py:741`; không fallback sang replace. Giữ nguyên input và winner bytes/mtime khi race. Chốt lỗi nếu filesystem không hỗ trợ, alias lexical/resolved/hardlink, parent không hợp lệ và cleanup temp. Test race có đồng bộ/hook, không sleep. Không mở chế độ overwrite trong lát này.

## R2 — Bounds và lifecycle PDF chưa thành hợp đồng thực thi

Brief dòng 32 để implementer tự chọn mọi cap; dòng 91 cấm subprocess nhưng dòng 97 cần child timeout. Chưa xác định thao tác nào chạy trong child, cách dừng/reap, lỗi child và giới hạn dữ liệu trả về. Raw size/page/text cap không phải hard memory cap: [pypdf extraction](https://pypdf.readthedocs.io/en/stable/user/extract-text.html) nêu parser phải xử lý toàn content stream và có thể dùng nhiều RAM.

Chốt trong hai tài liệu:

- Default hữu hạn: raw tối đa 8 MiB, 50 trang, 100.000 code point/trang, 1.000.000 code point tổng (kể cả separator), wall timeout 15 giây cho toàn PDF child, dữ liệu kết quả child tối đa 16 MiB. Validation kiểu chính xác, không coi bool là int; không nhận cấu hình cap từ file input. Nếu cho caller giảm cap, phải chốt min/max và không cho vượt hard maximum này.
- Toàn bộ PdfReader/đếm trang/extract chạy trong đúng một Python child thuộc lượt chạy. TXT không cần child. Cấm converter ngoài, cho phép child Python được chỉ định; không mâu thuẫn với acceptance.
- Parent timeout bao phủ khởi tạo/parse; terminate/kill rồi reap có giới hạn; mọi nhánh lỗi phải dọn tài nguyên do lượt tạo. Nêu cách truyền dữ liệu có bounds; không capture stdout/stderr vô hạn hoặc đưa warning/parser exception/raw text/path ra CLI.
- Error enum và thứ tự lỗi đóng: input/type/size/decode, dependency, parse/encryption/pages/text/timeout/child failure, publication. Bổ sung lỗi I/O/missing dependency/child result sai cấu trúc cụ thể; không trả exception thô. Không dùng mã resource-limit để khẳng định hard RAM đã được áp dụng khi chưa có cơ chế đo/chặn.
- Nêu rõ child timeout/size cap không phải OS sandbox hoặc hard memory/network isolation. Hard RAM trên Windows vẫn UNVERIFIED nếu chưa có cơ chế được nghiên cứu/kiểm. Lát triển khai chỉ dùng fixture tổng hợp; không nhận PDF đối kháng để thử exhaustion.

## R3 — Canonical compatibility và trang không trích được chữ

Brief dòng 34, 87, 91 chưa đủ chính xác. Probe cùng input CRLF/CR chứng minh CLI cũ `read_text(encoding='utf-8')` đổi newline thành LF, còn phương án mới decode bytes giữ CRLF/CR. Đây không phải lỗi nếu công bố rõ, nhưng không được gọi là cùng-input parity.

Probe hai trang `['', '']` cho thấy sau nối separator chuỗi vẫn nonempty. Vì vậy kiểm rỗng sau join không phát hiện PDF không có text. Không thể suy ra chắc chắn image-only từ text rỗng.

Sửa contract: kiểm có code point không-whitespace trong text các trang **trước join**; không có thì lỗi `pdf_no_extractable_text`, không khẳng định image-only. `.strip()` chỉ dùng cho kiểm điều kiện, không sửa canonical output. PDF có trang không text nhưng trang khác có text được giữ thứ tự/range rỗng; separator nằm ngoài range trang; text trích được không chứng minh nội dung PDF đầy đủ. Chốt 0 trang, whitespace-only, một trang trống giữa hai trang text, type/Unicode bất thường của parser. Thêm fixture/test tương ứng.

Tách acceptance: (a) CLI/API C1 cũ không đổi; (b) CLI mới giữ canonical literal, raw/canonical hash và span đúng cả CRLF, CR, LF, BOM, emoji; (c) PDF page ranges half-open, non-overlap, đúng separator, không phải tọa độ/byte PDF. `draft.text/source.name/source.sha256` đã đối chiếu đúng chữ ký source, không cần sửa shape C1.

## R4 — Pin, scope, môi trường và bàn giao chưa tự đủ

Brief dòng 70–79, 99–118 vẫn để manifest/lock và interpreter mơ hồ, trong khi cho phép child/fixture/README/provenance nhưng không liệt kê file tương ứng. Có chỉ dẫn tạo PR dù phạm vi không cho phép PR. Nghiên cứu chưa pin hash chính thức; chưa được coi là dependency đã kiểm.

Chỉ sửa hai tài liệu hiện có: chọn exact release pypdf được xác minh từ metadata chính thức (7.0.1 nếu còn khớp), ghi URL/version/Python/license và distribution hash lấy từ metadata; chưa cài/tải wheel. Phân biệt hash metadata đã đối chiếu với kiểm bytes package chưa chạy. Nêu manifest/lock mới cụ thể trong extractor, không sửa core dependency. Bổ sung allowlist đủ child helper nếu dùng, fixture/README, dependency record, ADR/PROGRESS nếu cần; mọi tên file cố định trước giao code.

Chốt bootstrap môi trường target riêng, interpreter tuyệt đối có thể dùng/được tạo; không dùng PATH mơ hồ hay cài vào source readonly. Nêu lệnh test mới + hồi quy C1 cần thiết, Ruff check **và format-check**, diff/scope/HEAD/status, demo TXT/PDF synthetic, deterministic output, race/timeout/cleanup, hash input bất biến; giữ giới hạn không chạy full suite không liên quan. Chốt output báo cáo `PHONG-HOA-X01-LOCAL-INGEST-RESULT.md` và evidence `x01-local-ingest-evidence/` tại root, manifest/commands/exit/count. Không coi các lệnh đề xuất là đã chạy.

## Bằng chứng và ranh giới

- Đã đọc hai tài liệu, source API/writer/CLI liên quan; đối chiếu Python và pypdf chính thức ngày 11/11/2026.
- Probe stdlib exit 0: race replace ghi đè; literal/newline khác legacy; hai trang rỗng join thành chuỗi nonempty. Đây là kiểm giả định trong brief, không phải test implementation PDF.
- Chưa có local-ingest implementation, dependency install, parse PDF, corpus thật hoặc chứng minh resource isolation.
- Đã xem danh sách cuộc đang mở: chỉ Leader tại cuộc này đang chạy; không có worker khác cần tránh trùng. Tự tiếp tục Phong Hỏa còn bật; không coi lịch hoặc receipt là bằng chứng worker đang chạy.
- Research chỉ được sửa hai output của nhiệm vụ gốc, giữ source/RUNS/review nguyên trạng; tự làm trực tiếp, không giao tiếp. Trả bảng R1–R4, hash output và HEAD/status trước/sau. Leader sẽ kiểm rồi mới giao implementation.
