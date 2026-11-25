# PHONG HỎA W03 — Frontend QA độc lập

## Kết luận

**FAIL — chưa đủ điều kiện accepted/nối tích hợp.** Candidate đúng SHA và focused suite hiện có đạt, nhưng probe độc lập tái hiện ba cạnh chưa được khóa: hai lỗi ranh giới summary/request ownership và một lỗi toàn vẹn DTO.

- Base: `273196e2d23b36172d57cc61b289522786d61b2a`
- Candidate/HEAD đã kiểm: `5c968c74cc53c5798bcf8adaf8695dacfd86ffd4`
- Branch: `feat/w03-read-frontend-20261112`
- Source: chỉ đọc; HEAD/branch/index/worktree không bị QA sửa.
- Phạm vi kết luận: source inspection + Vitest component/parser/provider ngoại tuyến. Không phải bằng chứng browser hoặc tích hợp.

## Phát hiện

### F1 — FAIL, MEDIUM: summary nhận và hiển thị metadata tài sản qua `notice`

- Vị trí: `portal/web/data/cves-http.ts:174-197`, đặc biệt dòng 196; sink hiển thị an toàn nhưng không đúng ranh giới tại `portal/web/components/cve-app.tsx:296-302`.
- Tác động: response `view=summary` có thể nhét tên/phiên bản tài sản vào trường envelope `notice`; parser chấp nhận và UI hiển thị. Điều này trái contract “summary không lộ metadata tài sản qua envelope”. React vẫn escape HTML nên đây không phải DOM XSS, nhưng là rò dữ liệu/vi phạm phân quyền hiển thị.
- Tái hiện: `PROBE-F1` đặt `notice = "Tài sản nội bộ: secret.example — FortiOS 7.2.1"` trong DTO summary hợp lệ còn lại.
- Expected: parser từ chối vì notice của W03-R là chuỗi contract cố định, không phải dữ liệu server tự do.
- Actual: `parseCveResponse()` không throw; probe fail tại assertion “must reject”. Dòng 196 chỉ kiểm kiểu/độ dài/control character và dòng 301 render nguyên văn.
- Sửa tối thiểu: so sánh `notice` với literal W03-R đã chốt (hoặc không lấy notice từ wire và dùng copy cục bộ cố định); thêm regression summary với notice chứa asset metadata.

### F2 — FAIL, LOW: parser nhận CVE và technology match trùng

- Vị trí: `portal/web/data/cves-http.ts:112-165,200-210`; render dùng `cveId`/`technologyId` làm React key tại `portal/web/components/cve-app.tsx` (detail row/list).
- Tác động: DTO không đúng contract có hai item cùng CVE và match trùng ID vẫn qua parser; UI có key trùng, selection theo `cveId` mơ hồ và có thể trình bày trùng/khác dữ liệu cho analyst.
- Tái hiện: `PROBE-F2` gửi hai item `CVE-2026-1001`, item thứ hai có hai `technology_id=41`.
- Expected: parser từ chối danh tính CVE trùng và danh sách match không tăng duy nhất.
- Actual: parser không throw; probe fail. Parser hiện chỉ map từng item/match, không kiểm uniqueness/order liên-item.
- Sửa tối thiểu: sau parse, kiểm `cveId` duy nhất; trong detail item kiểm `technologyId` tăng nghiêm ngặt/duy nhất; thêm regression cho duplicate CVE/match.

### F3 — FAIL, MEDIUM: đổi provider sang context summary vẫn gọi Technology API từ `view=detail` cũ

- Vị trí: `portal/web/components/cve-app.tsx:144-201`.
- Tác động: khi `provider` và `technologyProvider` đổi, effect reset context chỉ xóa response trong `queueMicrotask` (dòng 171-181), trong khi effect technology nhìn thấy response detail cũ và gọi `technologyProvider.list()` ngay (dòng 189-201). Context mới chưa xác định là detail vẫn phát một request tài sản; trái yêu cầu summary không gọi Technology API.
- Tái hiện: `PROBE-F3` render detail, rerender với provider mới đang chờ trả summary và Technology provider mới.
- Expected: `summaryTechnologyList` có 0 call cho đến khi response context mới xác nhận detail.
- Actual: có 1 call ngay sau rerender; probe fail với `expected vi.fn() to not be called ... actually called 1 times`.
- Sửa tối thiểu: gắn response với generation/provider owner và chỉ chạy effect technology khi response thuộc generation hiện tại; hoặc xóa response đồng bộ trong layout/reducer transition trước khi effect technology được phép chạy. Thêm regression provider detail → pending summary, đồng thời đổi Technology provider.

## PASS trong phạm vi component

- **PASS:** focused W03 hiện có: 2 file, 39/39 test, exit 0.
- **PASS:** HTTP CVE adapter gửi đúng một GET, `cache: no-store`, không body/retry ngầm trong test hiện có; 409 chỉ tải từ đầu sau thao tác người dùng.
- **PASS:** body JSON được đọc bounded 1 MiB; malformed/status-code không khớp map thành unavailable trong focused tests.
- **PASS:** scan ba file W03 runtime không thấy `dangerouslySetInnerHTML`, `.innerHTML`, `eval`, `new Function` hoặc method ghi; `rg` exit 1 nghĩa không có match. Route thật import `CveHttpClient`; route mẫu riêng import `CveSampleClient`, không thấy fixture fallback trong route thật.
- **PASS:** chuỗi `<script>` trong title được render thành text trong test hiện có; advisory bắt buộc HTTPS/không credentials và link có `noopener noreferrer`.
- **PASS:** source sau QA vẫn HEAD candidate, branch đúng, `git status --short` rỗng và `git diff --check BASE..HEAD` exit 0.

## UNVERIFIED có chủ ý

- Browser thật, focus/keyboard thực tế, layout desktop/mobile 360 px và console/network browser.
- API Backend W03, gateway same-origin, JWT/role thật, SQLite/TechnologyStore và wire Backend candidate.
- Cloudflare/JWKS/HTTPS, feed CISA/OpenCTI, freshness/terms, lab và production.
- Full 344-test suite, typecheck/lint/build không chạy lại trong QA này theo brief; các con số đó vẫn là evidence của Frontend, không phải bằng chứng QA mới.

## Lệnh và bằng chứng

Chi tiết tại `w03-frontend-qa-evidence/QA-COMMANDS-AND-RESULTS.md` và probe `w03-frontend-qa-evidence/w03-qa-probe.test.tsx`.
