# Nghiệm thu và phân công tiếp — ingest / W02

Ngày 11/11/2026. Leader đã xem các cuộc đang mở một lần trước ghi sổ/giao việc. W02 Frontend vẫn giữ nguyên request `e3c34ab6-e71a-4e7c-b9e6-80538d42707e`, thread `0ab8095a-ac5a-49ca-be0d-b3d67988e6c8`; không giao lại hoặc sửa tree đang viết.

Root: `$WORKSPACE`.

## 1. Importer: nhận bàn giao, chưa nghiệm thu mã

- Leader kiểm trực tiếp `cti-x01-ingest-queue`: HEAD `db36ec01b765dfd515c1d0ef13642a693b777172`, status sạch; diff từ `cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`: 12 file, +1315/-55, đúng danh sách cho phép.
- Hai source giữ đúng ref và sạch: W05 `cti-x01-w05-stix-e2e@cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`; producer `cti-x01-ingest-local@8a16758601647fb3dbf935abecc2435f3b7a3fb6`.
- Leader kiểm manifest `x01-ingest-queue-evidence/MANIFEST.sha256`: hash `f03b73538009e6d9c9873730c0723dd40f0dd8fc08840d7c33d81ccbd5742f87`, 11/11 khớp, không thiếu/thừa (loại manifest và báo cáo kiểm manifest khỏi inventory).
- Báo cáo 553 test là kết quả Backend; `commands.md` là bảng tóm tắt, chưa có raw log test trong manifest. Leader chưa chạy test mã và chưa dùng số 553 làm xác nhận độc lập.
- Giao QA Security rà soát độc lập ở đúng HEAD trước nối browser. Không yêu cầu chạy lại full suite; ưu tiên chỗ rủi ro và bằng chứng còn thiếu.

## 2. X01-INGEST-QUEUE-QA — phạm vi độc lập

Owner CTI QA Security, GPT-5.6 Sol medium, một worker, không giao bot/agent khác. Target chỉ đọc `<root>\cti-x01-ingest-queue`, base/HEAD ở trên. Đọc AGENTS, `PHONG-HOA-X01-INGEST-QUEUE-LEADER-PLAN.md`, implementation brief, report và diff; không đánh giá lại toàn dự án.

Kiểm tập trung migration v2→v3 và hai migrator; rollback từng giai đoạn/atomic draft+provenance; duplicate cùng/khác creator và chặn tự duyệt; reader v2/v3 không ghi, snapshot/provenance; dữ liệu JSON sai kiểu/Unicode/depth/cycle và path local/ancestor/UNC. Đối chiếu điều kiện rõ trong Leader plan với test thực tế, phân biệt lỗi sản phẩm và thiếu bằng chứng; không mở rộng sang hostile filesystem, hard sandbox, model hay lab.

Chạy hai test ingest mới ở exact HEAD, ghi raw output/exit/count. Thêm probe độc lập nhỏ cho nhánh rủi ro chưa được test chứng minh; tận dụng helper hiện có và dữ liệu synthetic, không viết test chỉ lặp implementation. Các assertion phải kiểm DB/output hoặc lỗi công khai. Nếu cần kiểm regression, chọn nhóm bị ảnh hưởng, không lặp full553/UI/build.

Không sửa source/index/HEAD/branch/RUNS/plan, report/evidence Backend hoặc probe Leader cũ. Chỉ ghi `<root>\PHONG-HOA-X01-INGEST-QUEUE-QA-RESULT.md` và `<root>\x01-ingest-queue-qa-evidence\` (probe/log/DB tổng hợp/manifest nếu cần). Dùng Python target 3.12.13, `-B`, tắt pytest cache; đặt tmp/basetemp trong evidence của QA. Không chạy demo `--rerun-owned` có thể ghi đè artifact Backend.

Mỗi finding: mức độ, file:dòng, đầu vào/tái hiện, mong đợi/thực tế, command/exit/log và sửa tối thiểu. Không tự sửa mã. Báo PASS/FAIL/UNVERIFIED, phạm vi chưa xét, HEAD/status trước-sau và manifest đầu ra. Không network/listener/browser/secret/model/OpenCTI/lab/push/PR/merge/deploy. Mục tiêu là quyết định có đủ điều kiện nối browser, không tuyên bố production-ready.

## 3. Browser prep — chấp nhận ở mức chuẩn bị

Đã đọc brief 78 dòng `PHONG-HOA-X01-INGEST-BROWSER-INTEGRATION-BRIEF.md`, hash `bc2665d8a8b6731950a7f0aaddb95b9072e885a012cff077efc934967736bfe2`. Đã đối chiếu tên LocalRun/helper/fixture với source. Chấp nhận thiết kế nối producer CLI → importer CLI → browser W05 → STIX trên cùng DB, kèm các ràng buộc khi giao triển khai:

1. Chỉ dùng commit importer sau nghiệm thu QA/Leader, không dùng HEAD đang chờ kiểm. Base và cổng chạy được chốt trong brief triển khai riêng; không tranh cổng 3012 hoặc trình duyệt đang do Frontend sử dụng.
2. Producer CLI thật chạy TXT và PDF; kiểm thực tế số lượng/thứ tự IOC trước thao tác chọn, không mặc định `[1]` nếu fixture PDF khác. Source/envelope/provenance/audit/bundle phải được đối chiếu cùng lần chạy.
3. Mỗi tình huống tự duyệt, người khác duyệt, save-refresh lỗi và decision-refresh lỗi có danh tính synthetic/scenario rõ trong harness; không thay auth sản phẩm hoặc giả Origin. Trace phải chứng minh retry chỉ GET và POST không lặp.
4. Script giữ phiên phải có thời hạn 300 giây và cleanup trong finally, xử lý EOF/timeout/lỗi browser. Không gọi chờ blocking dài trong tool; không tự sinh browser automation khác.
5. Chạy đủ TXT/PDF và các ca trong bảng; raw log, snapshot/screenshot và audit là bằng chứng riêng. Chuỗi producer→browser cùng draft chưa được chứng minh bằng kết quả CLI/core hiện có.

Không giao triển khai browser khi importer còn chờ QA; không cần sửa brief chuẩn bị để giả có SHA đã nghiệm thu.

## 4. W02 API research — cần sửa R1–R4

Input: `PHONG-HOA-W02-API-CONTRACT-BRIEF.md`, hash `1510244e8867fc1dc85225bccf9c99acc7b7689a09aed52a97af2454de501728`. Source `cti-x01-w05-stix-e2e@cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b` sạch. Leader đã đọc core normalize/score và factory/auth/settings W05.

**R1 — scope và DTO mẫu:** plan loại đề xuất chặn, brief lại có `recommendation=block`; bỏ field recommendation khỏi lát lookup. JSON success còn key `input` rồi đoạn sau yêu cầu bỏ, không phải fixture response hợp lệ: tách request và response chính xác. Điểm 78/parts không khớp core với một source; tạo ví dụ tổng hợp bằng core hiện có và chốt cách sinh level theo spec nếu có, ghi delta nếu chưa có. Không suy unknown/allowlist thành khẳng định an toàn.

**R2 — TLP trước số liệu tổng hợp:** hiện LookupRecord chứa ScoreInput tính sẵn nhưng không chốt cách loại ảnh hưởng nguồn/tài sản ẩn; chỉ kiểm marking trả về không chứng minh điểm/reason không rò dữ liệu ẩn. Chốt DTO nội bộ đầy đủ cho nguồn, related và asset (types/bounds/TLP), cách dựng ScoreInput chỉ từ phần được phép, quy tắc dedupe/độ tin cậy/thời gian/asset. Thêm kiểm biến đổi dữ liệu bị ẩn không làm thay response IT, kể cả score/reason/marking/count; nested AMBER trong record GREEN phải được xử lý. Không cần xây OpenCTI adapter thật.

**R3 — hook và thứ tự lỗi:** Leader chọn `create_app(..., lookup_port=None, ...)` optional injection; thiếu adapter chỉ làm route W02 trả 503, W05 vẫn hoạt động. Tái dùng verifier và role server-side, không đổi contract W05. Chốt multi-role, auth→role→query→normalize/private-IP→allowlist→lookup/filter/score→serialization; finite message bảng lỗi; response exception phải no-store/Vary. Bound canonical/display phải tính đến defang/IDNA làm chuỗi dài hơn raw; mọi số hữu hạn, bool không là integer. Timeout trong fixture chỉ là adapter ném lỗi; không nhận đó là chứng minh giới hạn thời gian của future network adapter.

**R4 — gói tự đủ:** target `<root>\cti-w02-lookup-api`, branch `feat/w02-lookup-api-20261111`, source/base như trên. Chốt interpreter target, exact allowlist (file mới để DTO/service/fixture/test), report/evidence path, Ruff format-check, targeted+W05 regression và demo in-process. Có thể thêm `docs/specs/W02-lookup-offline-contract.md` để lưu contract mới nhưng không sửa spec cũ/W05/config/lock. Chỉ sửa brief hiện tại <=160 dòng; kiểm JSON fixture bằng stdlib/core được phép, không tạo code/worktree hoặc chạy test implementation.

Leader chốt delta: dùng JWT W05 thay API-key nháp cũ; một GET chỉ đọc; chưa batch/enrichment/false-positive/block/link OpenCTI; not-found score null. Quyền IT CLEAR/GREEN và analyst/admin theo role mapping đã giao là policy portal cục bộ, không suy ra quyền chia sẻ ngoài hệ thống. Chưa nghiệm thu toàn brief cho triển khai trước khi R1–R4 rõ.

## 5. Tiếp tục

Frontend tiếp tục view hiện có; QA kiểm importer; Research sửa đúng brief API. Không giao lại Backend sửa khi chưa có finding. Engineer triển khai luồng browser sau gate importer; W02 API giao Backend sau gate contract, trên tree riêng. Hai lịch tiếp tục đã đọc, còn bật; dự án chưa hoàn tất nên không tạm ngưng.
