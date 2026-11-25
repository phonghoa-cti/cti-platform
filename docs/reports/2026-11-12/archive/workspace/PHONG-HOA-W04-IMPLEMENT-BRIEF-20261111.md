# W04 — quyết định Leader và brief Backend cục bộ

Task: `W04-ASSETS-IMPLEMENT`. Owner duy nhất: CTI Backend, Sol medium, không giao tiếp worker khác.
Root: `$WORKSPACE`.

## Nghiệm thu nghiên cứu có hiệu chỉnh

Leader đã đọc `PHONG-HOA-W04-ASSETS-RESEARCH-20261111.md`, SHA256 `d1af31d21adea22a2cb88d1aeb36f3532fb33fcb8dfa32edc4a63e4a30df18cd`, đối chiếu mã W02/core trên `aeff542a20ecc6fe436a0884801fdd69ab0435f6`, AGENTS và PROGRESS. PR #1/#46 vẫn mở khi kiểm GitHub 11/11; không chọn lại main/PR làm baseline. Chấp nhận hướng tái dùng lõi và làm domain/CIDR trước. Những điểm dưới thay phần tương ứng trong nghiên cứu, không xem nghiên cứu ban đầu là hợp đồng nguyên trạng đã đạt.

- **Hợp đồng W02 thực tế khác đề xuất:** `portal_api/schemas.py` và `portal/web/data/ioc-lookup-http.ts:209` đang cấm `asset_match.matched=true` trong `allowlisted/not_found`. Leader chạy phép thử bằng schema hiện tại: đúng là từ chối. Việc mở hai trạng thái là mở rộng ngữ nghĩa có chủ đích, cần bước Frontend sau; không được báo tương thích trọn luồng chỉ vì tên field giữ nguyên. `toLookupState` của client cũng bỏ thông tin asset ở not_found.
- **SQLite:** ví dụ inline `UNIQUE(...) WHERE ...` trong báo cáo không chạy được. Leader kiểm SQLite in-memory: ví dụ cũ bị từ chối, `CREATE UNIQUE INDEX ... ON assets(type, canonical_value) WHERE deleted_at IS NULL` chạy được. Dùng index riêng. Nguồn: https://www.sqlite.org/partialindex.html .
- **IDNA:** codec Python hiện dùng RFC 3490, không phải IDNA2008/RFC 5891. Giữ canonical của core để tránh lệch khóa; không thêm package/chuyển thuật toán trong lát cắt. Nguồn chính thức: https://docs.python.org/3.12/library/codecs.html#module-encodings.idna .
- **Không cần bảng manual tương lai:** default/injected Allowlist hiện có là nguồn độc lập, asset rules được suy ra từ active assets. Chứng minh xóa asset không xóa default/injected rule trùng giá trị. Hoãn persistent manual CRUD/schema, không xây phần chưa dùng.
- **W02 IP riêng:** core/W02 từ chối IP không public trước lookup. Giữ nguyên chính sách này; store có thể giữ CIDR nội bộ nhưng không tuyên bố W02 đã tra được private IP. Dùng IP public tổng hợp không gọi mạng trong kiểm W02.

Phép thử Leader exit 0 sau khi chỉ định đúng source paths root/core/extractor với interpreter `cti-w02-lookup-api/.venv/Scripts/python.exe`; lần đầu thiếu extractor path nên lỗi import, không tính pass. Không sửa sản phẩm, không ghi DB lên đĩa, không chạy lại suite cũ. Đây là kiểm hợp đồng/DDL, chưa là runtime W04.

## Chọn phạm vi

Ba hướng đã cân nhắc: làm cả bốn loại W04 sẽ kéo technology/W03/CSV; làm UI trước khi có hợp đồng làm tăng sửa lại; chọn lõi domain/CIDR và API trước vì dùng được thuật toán hiện có và có luồng kiểm cụ thể. Đây là lựa chọn kỹ thuật Leader trong phạm vi tiếp tục được giao.

Đích: người IT/Analyst thêm/sửa/xóa domain và CIDR; lookup xác định tài sản từ cùng DB, audit có người thao tác, quyền bị kiểm phía API. Chỉ demo cục bộ với dữ liệu tổng hợp, một tổ chức dùng chung DB. Không có chặn thật, không gọi đây là an toàn, không suy TLP:CLEAR hiện hữu thành quyền xuất dữ liệu doanh nghiệp ra ngoài.

## Working tree và file được sửa

- Nguồn chỉ đọc: `cti-w02-local-integration` HEAD `aeff542a20ecc6fe436a0884801fdd69ab0435f6`, trạng thái sạch khi Leader kiểm.
- Tạo tree riêng `cti-w04-assets-local`, branch `feat/w04-assets-local-20261111` từ đúng SHA trên. Nếu đích đã có, kiểm owner/HEAD/dirty trước, không reset/xóa/ghi đè.
- Đọc AGENTS.md, docs/PROGRESS.md, W04-tai-san.md, nghiên cứu và brief này. Brief này ưu tiên khi có mâu thuẫn với nghiên cứu.
- Allowlist: `portal_api/assets.py` mới; phần nối nhỏ trong `portal_api/app.py`, `schemas.py`, `ioc_lookup.py`; `portal_api/tests/test_assets_api.py` mới, có thể thêm test_assets_store.py/test_assets_matcher.py; bổ sung `portal_api/tests/test_w02_ioc_api.py`; `docs/specs/W04-assets-local-contract.md` mới và `docs/PROGRESS.md`.
- Không sửa core, auth/settings/service W05, frontend, lock/dependency/deploy, RUNS hay cây nguồn. File ngoài allowlist cần báo Leader kèm lý do.

## Hợp đồng triển khai

1. Giữ route/body/status/error assets đã đề xuất trong nghiên cứu: GET/POST/PUT/DELETE `/api/assets`, domain/ip_range, version chống ghi đè; actor lấy từ principal đã xác minh. Auth/role trước body/query/DB; `leader`/không được cấp role bị 403; giả header/claim không cấp quyền. Mutation yêu cầu Origin hợp lệ như W05; lỗi và success đều no-store/Vary. Body đọc streaming tối đa 8 KiB, excess 413, sai input 422, duplicate/stale409, missing404; strict IDs/versions 1..2^53-1, bool/float không phải int; query lặp/extra bị từ chối. Không echo raw input/SQL/path/token.
2. Create/update/delete và audit trước/sau canonical là một write transaction; rollback đầy đủ. SQLite timeout hữu hạn theo cấu hình hiện có; partial unique index đúng cú pháp. Dedupe domain/CIDR canonical active, soft-delete hoặc delete+audit rõ ràng. Ghi migration khởi tạo idempotent cho DB demo riêng; không tự migrate DB đang dùng chung.
3. Domain input chỉ hostname, không scheme/path/port/wildcard/email. Kiểm cấu trúc trước normalize để refang hoặc dấu câu bị cắt không vô tình nhận input sai. Dùng core cho canonical, domain cuối một dot được hỗ trợ. Chấp nhận domain chuẩn tối đa 253 ký tự canonical; AssetMatch dùng loại tên riêng tối đa 253, không nới các tên source/related vốn 128. CIDR bắt buộc chuỗi có `/`, strict network address, IPv4/IPv6 tách biệt; không fallback thành domain. Nguồn: https://docs.python.org/3.12/library/ipaddress.html .
4. Một snapshot read cung cấp active assets, matched names và rules cho một lookup; không singleton mutable/cache cũ. Match domain equality hoặc hậu tố `.` + domain; IP theo network cùng family; URL/email lấy hostname/domain; URL có path/query vẫn asset-match nhưng giữ luật allowlist core chỉ homepage. Hash không asset-match. Tối đa 100 matched names, không silently truncate; vượt giới hạn/DB hỏng trả unavailable. GET list tối đa 1000 active items; vượt trả lỗi hữu hạn có tài liệu, không trả partial giả đầy đủ. Chưa triển khai pagination.
5. Thêm tham số tùy chọn `asset_store` vào `create_app`/LookupService: mặc định `None` giữ nguyên ứng dụng W02 đã nghiệm thu, không tự mở DB hoặc bật W04. Khi được inject store trong demo/test, assets routes hoạt động và lookup có ngữ nghĩa mới. Khi chưa cấu hình store, assets routes sau auth trả `503 assets_unavailable`. Auth vẫn chạy trước mọi access DB; khởi tạo store/schema tường minh ngoài request trong fixture.
6. Khi bật asset_store: W02 giữ fields và các invariant khác, chỉ mở asset_match cho allowlisted/not_found và bound tên asset nói trên. Allowlisted vẫn score0, no source/related; not_found vẫn score null, no source/related. Khi found có asset match, gộp với asset facts đã qua TLP filter, dedupe ổn định, tính score nhất quán theo tập visible cuối cùng; không lộ hidden facts. Nếu chỉ local asset và lookup record không visible, chỉ trả asset local được phép thấy. Assets không tự biến unknown thành found. Store failure ở `/api/ioc` giữ `503 lookup_unavailable` để không phá error contract; assets routes dùng `assets_unavailable`. Default/injected allowlist cũ vẫn hiệu lực và không bị sửa/xóa theo asset.
7. Xuất 3 response fixture tổng hợp hợp lệ (allowlisted+asset, not_found+asset từ URL path, found+asset), kèm mẫu lỗi vào thư mục evidence. Đây là đầu vào bước Frontend tiếp theo; chưa nối client cũ vào chế độ W04 hoặc tuyên bố UI hoạt động.

## Làm và kiểm

Viết test tái hiện trước (RED), rồi mã đạt GREEN. Test SQLite tạm, RSA/JWT fixture, in-process API, không browser/listener/network/secret. Bao phủ validation/ranh giới domain, CIDR in/out/cross-family, duplicate canonical, stale version/concurrent writes, rollback audit, auth trước DB/body, Origin, body limit, DB lỗi, default allowlist tồn tại sau xóa asset, không nới quyền/TLP, opt-in/off và ba response trên. Giữ kiểm cũ; nếu một expectation asset state phải đổi vì hợp đồng mới, ghi rõ và thay bằng kiểm invariant tương ứng, không xóa probe cho dễ xanh.

Dùng Python của target nếu đã đủ dependencies. Nếu chưa có, được dùng interpreter **cụ thể** `cti-w02-lookup-api/.venv/Scripts/python.exe` chỉ đọc, với cwd target và `PYTHONPATH` trỏ target root/core/extractor; in executable, phiên bản và đường dẫn module thực tế để chứng minh chạy mã target. Không dùng PATH, không cài vào env nguồn, không coi thiếu target .venv là blocker tự động. Cần cài mới thì báo dependency cụ thể.

Chạy nhóm test mới để chứng minh RED→GREEN, sau đó một lần `pytest portal_api/tests -q`, `ruff check portal_api`, `ruff format --check portal_api`, `git diff --check`. Không lặp nhóm test cũ lần nữa nếu suite đã phủ, không mở rộng full repo/browser/lab.

Trả commit cục bộ Conventional Commit, base/HEAD, diff/stat, status sạch, lệnh/exit/count, đường dẫn artifact, PASS/FAIL/UNVERIFIED. Lưu báo cáo root `PHONG-HOA-W04-ASSETS-RESULT.md` và raw evidence root `w04-assets-evidence/`. Không push/PR/merge/deploy; không tự giao tiếp.

## Bước nối do Leader phụ trách

Sau Backend đạt: CTI Frontend cập nhật parser/view W02 theo response fixtures, bảo toàn lỗi/invariant cũ và nhãn “thuộc tài sản” kể cả unknown; sau đó màn quản lý W04 theo thiết kế hiện có và kiểm browser toàn luồng. Chỉ giao khi đúng đầu vào/hợp đồng đã nghiệm thu. Nghiên cứu/W04 API riêng không phải W04 UI hay dự án hoàn thành.
