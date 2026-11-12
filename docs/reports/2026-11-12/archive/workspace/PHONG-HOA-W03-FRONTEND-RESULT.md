# PHONG HỎA W03 — Frontend read-only result

## Kết quả

PASS cục bộ cho lát frontend W03-R. Đã thêm `/lo-hong` dùng HTTP provider GET-only và `/lo-hong/mau` dùng provider 12 CVE tổng hợp có nhãn rõ. Không fallback fixture ở route thật.

- Base: `273196e2d23b36172d57cc61b289522786d61b2a`
- Branch: `feat/w03-read-frontend-20261112`
- Commit/HEAD: `5c968c74cc53c5798bcf8adaf8695dacfd86ffd4`
- Commit: `feat(portal): add read-only CVE view`
- Diff: 14 file, `1398 insertions(+), 1 deletion(-)`
- Tree sau commit: sạch

## Phạm vi đã làm

- Typed discriminated parser strict cho `view=detail|summary`; key exact, UTC/date thật, safe integer, finite bounds, nullable invariants, HTTPS advisory và summary không nhận field detail.
- HTTP adapter chỉ gọi một GET same-origin, `cache: no-store`, timeout 10 giây, body UTF-8 bounded 1 MiB; map đúng 401/403/404/422/409/503, network/malformed thành unavailable; không retry/mutation.
- UI mặc định `kev=true`, `limit=10`; filter công nghệ/từ khóa/KEV, previous/next bằng opaque cursor, detail từ row, empty/loading/error states, 409 bỏ chuỗi cũ và chỉ tải từ đầu khi người dùng bấm.
- Summary leader không gọi Technology API, không render filter/metadata tài sản. Detail chỉ tải options W04 sau khi biết `view=detail`.
- Ownership request cho đổi filter/provider/route/unmount; callback cũ không đổi data/loading/options/detail context mới.
- Source/as-of/notice luôn hiện trên response; tooltip KEV/EPSS/CVSS tiếng Việt; null là `Chưa có dữ liệu`; score 0 vẫn hiển thị; link advisory `noopener noreferrer`; React escaping; focus vào detail và trả về nút dòng khi đóng; mobile dùng table scroll + layout một cột.
- Không có status mutation, nhãn đã vá/an toàn hoặc thuật toán rank/match trong HTTP adapter. Sample fixture chỉ lọc/paginate dữ liệu tổng hợp deterministic và đánh priority liên tục theo tập đã lọc.
- Nav W05 hiện có chỉ được thêm link `Lỗ hổng`; `docs/PROGRESS.md` thêm đúng một đoạn W03.

## File thay đổi

Xem `w03-frontend-evidence/manifest.txt`. Tất cả nằm trong allowlist brief; ngoại lệ nav chỉ là một liên kết trong `draft-review-app.tsx`.

## RED → GREEN và kiểm tra

- RED đầu: focused W03 exit 1 vì hai module production chưa tồn tại.
- GREEN cuối focused W03: 2 file, 39/39, exit 0.
- RED regression priority sample: 1 failure đúng `[1,4,7,10]`; GREEN 26/26 sau fix.
- RED accessibility focus: 1 failure đúng focus còn ở row; GREEN test mục tiêu sau fix.
- W04 regression: 3 file, 66/66, exit 0.
- Full suite cuối: 17 file, 344/344, exit 0.
- `npm run typecheck`: exit 0.
- `npm run lint`: exit 0.
- `npm run build`: exit 0; 11/11 static pages, có hai route W03.
- `git diff --check BASE..HEAD`: exit 0.

Một lượt full suite chạy đồng thời với build đã có 1 timeout W04 ở mốc 5 giây (342/343, không assertion fail). Chạy riêng ngay sau đó 343/343 và lần cuối sau mọi sửa đổi 344/344; không sửa test W04.

## Fixture hash

- `w03-detail.json`: `adcc16640ae425fd91955048ff17ddc60a3fb9476421d36531a2f596f40dd309`
- `w03-summary.json`: `fbccb17fca29d4dc00db16a4ce80156acc29a52ed437c36d48e246adaab96994`

## Giới hạn / UNVERIFIED

- Không chạy browser thật theo brief; desktop/mobile rendering và browser interaction chưa được chứng minh trong lượt này.
- Chưa nối API/backend/gateway/JWT/SQLite thật; fixture/parser/component chỉ là bằng chứng synthetic/local.
- Chưa kiểm feed CISA/OpenCTI, freshness/terms, Cloudflare/JWKS/HTTPS, lab hoặc production.
- Không push/PR/merge/deploy và không sửa dependency.
- Engine context Impeccable không có trên máy nên detector tự động không chạy; đã dùng trực tiếp DESIGN.md, tokens và craft-floor hiện có. Không suy diễn điều này thành bằng chứng browser.
