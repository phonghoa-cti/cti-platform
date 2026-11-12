# W05 local integration — ACCEPTED LOCAL; R1–R4 CLOSED

**Cập nhật 03:06 ngày 11/11/2026:** nghiệm thu phạm vi tích hợp cục bộ tại `d94afb1e24929f64f82a921cd29307be175fb04e`. R1–R4 đã đóng; Leader vừa chạy 14 ca runner/restart/cleanup, tất cả đạt, exit 0. Chi tiết nghiệm thu cuối ở cuối tài liệu; các kết luận chưa đạt phía dưới là lịch sử tại ref cũ.

Leader review ngày 11/11/2026, khoảng 02:44 giờ Việt Nam. Ref được kiểm: `12ad2767a5a0ed46cc89ba529ff7d7d878e88fb4`, branch `feat/w05-local-integration-20261111`.

## Kết luận lịch sử tại 12ad276

Chưa nghiệm thu toàn bộ harness. Luồng thành công có bằng chứng tốt, nhưng ba lỗi xử lý thất bại dưới đây được Leader tái hiện bằng bốn ca kiểm độc lập. Không coi các số PASS trước đó là đã bao phủ lỗi giữa chừng.

## Đã xác minh

- HEAD đúng, working tree sạch; `git diff --check` exit 0.
- Snapshot `portal/web` có tree hash `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`; diff với UI `a791a3f2be19b4c1593f82706c47b5dca97ab51a` rỗng.
- Report SHA256 `93d4002cd44c330ceb7531a9918e43bf1982a06698af5f2709e17e0ead77dbe7`, manifest `c3e770c1c522e9d120c176e2a3d1bcc9f7790b0246abc7c9406f786ca3a9ef2a`, lock `c4cff04044acd2d95064f38d27e57307d6c6a10893e4152beebee3a9bc9b5374` đều khớp. 7/7 artifact trong manifest khớp hash.
- Đọc XML: 385 tests, 0 failure/error/skip. Đọc log HTTP 56 check/7 scenario, Node 3, UI 52 và typecheck/lint/build exit 0. Đây là bằng chứng worker; Leader không chạy lại toàn bộ các suite này.
- Leader chạy mới settings + runner: **22/22 đạt, exit 0**, `local-integration-evidence/leader-settings-runner.log`.
- Leader xem hai ảnh: trạng thái rejected với queue còn 2; trạng thái approved kèm lỗi tải lại và nút quyết định bị khóa. Không suy ảnh thành kiểm browser độc lập hay bằng chứng audit của cùng lần chụp.
- Sau probe và kiểm runner: 0 process phù hợp đường dẫn harness/probe, 0 thư mục tạm `w05-local-*` tại thời điểm đọc; `leader-cleanup-readback.json`. Không xóa hay dừng tiến trình của người khác.

## R1 — P2: request target lỗi làm gateway thoát

Vị trí: `tools/local_integration/gateway.mjs:76`.

`new URL()` nằm ngoài vùng bắt lỗi trong async request handler. Gửi request target `http://[` tới gateway loopback với Host hợp lệ làm phát sinh `ERR_INVALID_URL`, child gateway exit **1**. Các request hợp lệ tiếp theo mất dịch vụ.

Bằng chứng: ca R1 trong `local-integration-evidence/leader_gateway_probe.mjs`; `leader-gateway-red.log`: `childExit=1`, `invalidUrlError=true`. Probe chỉ mở và dừng các child tổng hợp do chính nó tạo.

Sửa: bắt lỗi parse/validate target tại biên request, trả lỗi 400 gọn với no-store, không tiết lộ exception. Không để request riêng làm thoát process. Thêm regression kiểm response lỗi và request hợp lệ kế tiếp vẫn hoạt động.

## R2 — P2: timeout sau response headers bỏ treo downstream

Vị trí: `tools/local_integration/gateway.mjs:89–97`.

Biến `finished` được đặt true khi nhận headers, trước khi nhận hết response. Nếu upstream gửi headers rồi ngừng body, timeout hủy upstream nhưng handler error bị bỏ qua do `finished=true`; đường pipe không đóng downstream đúng hạn.

Bằng chứng: ca R2 đặt timeout 60 ms, upstream flush headers rồi đứng; client vẫn không end/abort/error sau **600 ms**, `outcome=deadline`, gateway còn sống. Cả hai ca Node probe fail, exit 1.

Sửa: phân biệt bắt đầu response với hoàn tất response, xử lý stream error/aborted và client disconnect. Trước headers trả 503 no-store; sau headers phải kết thúc bằng đóng kết nối có kiểm soát, không cố ghi lại status và không báo thành công cho body thiếu. Không retry POST. Thêm test headers-then-stall, upstream abort, client abort và bảo đảm gateway còn phục vụ request tiếp.

Nguồn đã đọc: [Node.js HTTP — request lifecycle, timeout và destroy](https://nodejs.org/api/http.html#httprequestoptions-callback). Timeout phát sự kiện; chương trình phải chủ động xử lý việc hủy và trạng thái stream. Kết luận lỗi cụ thể dựa trên probe tại ref trên.

## R3 — P2: một lỗi cleanup bỏ qua tài nguyên còn lại, lần sau không thử lại

Vị trí: `tools/local_integration/runner.py:260–280`.

`close()` đặt `_closed=True` trước khi dừng tài nguyên, rồi gọi terminate/wait/join/cleanup tuần tự không cô lập lỗi. Nếu terminate một child ném lỗi, UI/API/temp chưa được xử lý. Nếu cleanup temp bị khóa file tạm thời trên Windows, mọi lần `close()` tiếp theo đều return ngay.

Bằng chứng fault injection, không tạo process/file thật: `leader_cleanup_probe.py`, `leader-cleanup-red.log`, **2/2 fail, exit 1**. Đã làm rõ mock API thread dừng và cho phép báo lỗi tổng hợp, rồi xác nhận lại cùng hai failure trong `leader-cleanup-confirmed-red.log`, exit 1. Ca đầu `ui.terminate.called=False` sau lỗi terminate gateway; ca sau cleanup chỉ được gọi 1 lần sau hai lần close dù lỗi file chỉ xảy ra lần đầu. Đây không phải bằng chứng rằng lỗi Windows đó đã xảy ra trong lần browser của worker.

Sửa: cleanup best-effort cho từng tài nguyên độc lập, theo dõi tài nguyên chưa đóng để có thể thử lại, không đánh đã đóng hoàn toàn khi còn lỗi. Báo lỗi tổng hợp gọn thay vì che mất thất bại; chỉ xóa DB sau khi API thực sự dừng. Giữ ownership theo handle/PID tạo bởi run, không kill theo port/tên. Kiểm join còn sống, partial startup, TTL và cleanup gọi lặp. Không yêu cầu cơ chế giám sát production hay xử lý cưỡng bức kill của hệ điều hành trong lượt này.

## Phạm vi rework

Engineer/Sol medium, một người sửa đúng tree `cti-w05-local-integration`, bắt đầu từ HEAD trên. Chỉ sửa `tools/local_integration/gateway.mjs`, `runner.py`, tests liên quan; docs ADR/progress nếu cần để khớp hành vi. Không sửa settings/core/store/auth, dependency, UI snapshot, hai tree nguồn, RUNS hoặc tài liệu/probe/log Leader.

TDD: giữ RED của Leader; thêm regression trong repo trước sửa, lưu log RED/GREEN riêng. Không sửa probe để làm xanh. Nếu probe có vấn đề, trả kết quả tái hiện cụ thể cho Leader.

Các kiểm tra cần chạy sau sửa:

1. Hai Node probe Leader và hai Python probe Leader đều xanh; nhóm gateway/runner trong repo gồm các lỗi mới, cleanup ownership, partial start và TTL đạt.
2. Settings + runner regression; HTTP matrix 56 check/7 scenario để kiểm không đổi JWT/Origin/decision/audit. Đọc SQLite vẫn một audit cho mỗi quyết định thành công; POST không tự retry.
3. Ruff/check-format Python thay đổi, `git diff --check`, UI tree hash vẫn bằng `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`.
4. Kiểm dừng sạch child/API/temp sau ca thành công và thất bại, không đụng tài nguyên sentinel. Ghi exit/count và HEAD cuối, commit cục bộ, tree sạch.

Không chạy lại toàn bộ Python385/UI52/build hoặc browser chỉ vì thói quen khi UI/dependency/settings không đổi. Nếu phát hiện thay đổi lan rộng hay regression mới, mở rộng kiểm đúng phạm vi và giải thích. Cập nhật `PHONG-HOA-LOCAL-INTEGRATION-RESULT.md`, thêm evidence có tên rework và manifest riêng; giữ nguyên log/ảnh cũ cùng mọi file `leader*`.

Cloudflare/JWKS thật, HTTPS, dữ liệu thật, lab/OpenCTI/deploy và phục hồi điều phối bỏ dở vẫn UNVERIFIED. Automation dự án được đọc trạng thái trong lượt này, còn bật; lần gần nhất 02:26 trả NOTHING NEW, lần kế 02:56 giờ Việt Nam. Giữ project active và nối việc sau khi nghiệm thu.

## Kiểm rework tại 0a38e9 — R1–R3 đã đóng

- HEAD `0a38e918c5967f6b98f95827ffffa1790de68598`, tree sạch, diff 5 file +300/−21, đúng phạm vi; đọc diff gateway/runner/tests.
- Leader chạy mới Node 2/2 và Python 2/2, exit 0: `leader-gateway-green.log`, `leader-cleanup-green.log`. URL lỗi không làm gateway thoát; timeout sau headers kết thúc request; cleanup tiếp tục và thử lại được.
- Rework manifest 8/8 file khớp; manifest SHA256 `632d96a57ef032b447cad2f8b72d95af8b580f386684303af0428d0637de7bb8`; report SHA256 `5883549b80ba6bb3c6e9d301a5cd8bbd6dfd6920c0fa188e45bc99954c8526a2` khớp.
- Đã đọc log sau commit: gateway7, settings/runner27, HTTP56/7, Ruff/format/diff-check exit0. Không chạy lặp các suite đã có bằng chứng phù hợp.
- UI snapshot vẫn tree `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`, diff với source a791a3f rỗng.

## R4 — P2: mở lại LocalRun đã đóng tạo tài nguyên không còn được cleanup

Vị trí tại ref `0a38e9`: `tools/local_integration/runner.py:185–187`, `:265–268`, `:316–335`.

Cleanup mới đặt `_temporary=None` khi xóa xong, trong khi `start()` chỉ dùng `_temporary is not None` để chặn khởi động lại. Do đó `start → close → start` được cho qua nhưng `_closed` còn true. `close()` kế tiếp và TTL callback đều return ngay, để gateway/API/DB tạm tiếp tục tồn tại. Trước rework, `_temporary` còn giữ handle nên lần start thứ hai bị từ chối; đây là regression do thay vòng đời cleanup, không mở lại R1–R3 đã đóng.

Leader tái hiện với **HTTP stack thật chỉ loopback**, dữ liệu tổng hợp, không UI: `local-integration-evidence/leader_restart_probe.py`. Sau lần close thứ hai: `closed_flag=true`, `gateway_alive=true`, `api_alive=true`, `temporary_exists=true`. Test **1 fail, exit1**, log `leader-restart-red.log`. Phần finally của probe khôi phục khả năng close rồi dừng chính các handle do probe tạo; đọc lại `leader-restart-cleanup-readback.json` xác nhận 0 process/0 temp phù hợp. Không để ca thử lỗi tồn tại sau kiểm.

### Chốt cách sửa và phạm vi R4

Chọn hợp đồng **mỗi instance LocalRun chỉ được bắt đầu một lần**; muốn chạy scenario mới thì tạo instance mới. Không cần hỗ trợ restart hoặc tạo cơ chế tự hồi sinh. Dùng trạng thái vòng đời rõ ràng để chặn mọi lần start lại trước khi cấp tài nguyên: đang chạy, đã close, close trước start, hoặc start trước đã thất bại kể cả khi cleanup còn chờ retry. Không dùng sự tồn tại của temp handle làm trạng thái start. `close()` vẫn phải gọi lặp an toàn và thử lại cleanup chưa xong như R3.

Engineer/Sol medium sửa đúng tree hiện tại từ `0a38e9`. Chỉ `runner.py`, `tests/test_runner.py` và ADR nếu cần; không sửa gateway, UI, settings/dependency, core/store/auth, tree nguồn, RUNS hoặc probe/log/review Leader. Không giao thêm agent/bot.

TDD: thêm regression repo chứng minh normal start-close-start bị từ chối; close-before-start và failed-start không thể tái cấp tài nguyên; cleanup retry vẫn đạt. Chạy probe R4 giữ nguyên, nhóm runner mới/cũ và 4 probe R1–R3 để không phá sửa trước. Kiểm thực tế ít nhất một lần start/close thành công, lỗi partial-start, TTL và sentinel ownership qua runner tests; không cần lặp full385, settings27, HTTP56, UI52/build/browser nếu phạm vi giữ như trên. Ruff/check-format/diff-check, UI treehash giữ nguyên, đọc lại cleanup, commit cục bộ sạch.

Cập nhật report hiện có, ghi evidence trong `local-integration-evidence/rework-r4/` với manifest riêng; giữ log/ảnh cũ và mọi file `leader*`. Nếu phát sinh thay đổi ngoài phạm vi, báo finding trước; không tự mở rộng. R4 là correction cụ thể mới, không phải giao lại R1–R3.

## Nghiệm thu cuối tại d94afb1 — R1–R4 đã đóng

- Đối chiếu request `0257c8a7-d210-496a-b3f6-a2c39011ed96` với HEAD `d94afb1e24929f64f82a921cd29307be175fb04e`, branch `feat/w05-local-integration-20261111`. Diff R4 từ `0a38e9`: 3 file, +78/−2, đúng runner/tests/ADR; đã đọc toàn diff. Tree sạch, diff-check exit 0.
- `LocalRun` chỉ cho start từ trạng thái `new`, chặn tái cấp tài nguyên sau close, close-before-start và failed-start. Cleanup vẫn thử lại từng tài nguyên chưa đóng. Leader chạy mới **14/14 đạt, exit 0**: 11 test runner trong repo, probe restart R4 bất biến và 2 probe cleanup R3 bất biến. Log: `local-integration-evidence/leader-r4-acceptance.log`.
- Report SHA256 `a72f60084de62a6ae8b372977d88eb79775c5e951c7bbfa6ee4c97acfd5fccc0`; manifest R4 SHA256 `b07cf4eb9734478a50e165b4fd3dff5cbab986444ce85ec0095a0b4b5f1bd534`; 5/5 artifact khớp hash. Đọc log worker hậu commit: runner11, restart1, gateway2, cleanup2, Ruff/format/diff-check đều exit 0.
- UI snapshot vẫn tree `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`, diff source UI `a791a3f` rỗng. Không lặp browser/UI/build/HTTP matrix hoặc full Python vì R4 không đổi những phần đó. Kết quả Python385, HTTP56/7 và UI52 trước đây vẫn là bằng chứng ở ref đã ghi, không gán thành lần chạy mới tại d94afb1.
- Sau kiểm, quan sát 03:05:17 giờ Việt Nam: **0 process phù hợp harness/probe, 0 thư mục tạm w05-local-***; `local-integration-evidence/leader-r4-cleanup-readback.json`. Không dừng hoặc xóa tài nguyên ngoài test do Leader tạo.
- Nghiệm thu luồng UI/API/SQLite cục bộ với dữ liệu và JWT tổng hợp, gồm xử lý thất bại đã kiểm; không suy ra Cloudflare/JWKS/HTTPS thật, dữ liệu thật, model thật, OpenCTI hoặc lab đã đạt. Không push/PR/merge/deploy.
- Đã đọc automation và các cuộc mở một lần trong lượt: không có Leader khác đang làm Phong Hỏa. Lịch dự phòng còn bật, lần 02:56 hoàn tất NOTHING NEW, lần kế 03:26 giờ Việt Nam. Chưa chứng minh phục hồi việc bỏ dở; giữ lịch vì dự án còn active.

### Nối việc từ spec

`docs/specs/W05-duyet.md` còn yêu cầu người duyệt thay lựa chọn và lưu nháp. API hiện tại chỉ list/detail/decision; `payload_json` bất biến, `draft_audit` chỉ một quyết định cho mỗi draft. Chọn nghiên cứu **lõi lưu lựa chọn IOC của người duyệt** trước: bỏ chọn/chọn lại mục vốn đủ điều kiện, version và audit nguyên tử; chưa mở rộng thành sửa toàn bộ payload/TLP, thêm IOC, UI mới hoặc OpenCTI. Brief giao Research: `PHONG-HOA-W05-EDIT-NEXT-BRIEF.md`. W05 và dự án tổng vẫn chưa hoàn tất.
