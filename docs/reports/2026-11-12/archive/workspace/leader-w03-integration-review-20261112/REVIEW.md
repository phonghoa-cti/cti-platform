# W03 tích hợp — review 12/11/2026
Candidate93962d9ec771c49855c213e6332be0632e33debd sạch. **CHƯA NGHIỆM THU TOÀN LUỒNG**.

## Bằng chứng đã đối chiếu
- 42/42 manifest hash khớp; manifest9b17ed1ff8a9a85db30f096c3d1d1525acb28f589b74bb4b356c1591908a2922.
- Backend portal_api đúng abcd14da; frontend sản phẩm đúng f650f04d, chỉ thêm wire test. Không nghiệm thu lại B1/B2 cũ.
- Đọc diff gateway/runner/helper/matrix; ảnh thật7tệp final-browser, metadataHEAD93962d9.
- Trace Leader một CVE GET200, không Technology API; recovery503→200; snapshot PUT200→GET409→GET200.
- SQL đối chiếu trực tiếp schema/rows/version của6SQLite snapshots: Leader và recovery hoàn toàn bất biến; snapshot chỉ2bảng technology đổi và audit+1, đúng PUT. sql-review.json.
- Ảnh thể hiện0/null, notice/source mẫu, summary,409 và503 rồi thành công. Cleanup states stopped/portclosed/tempremoved được lưu. Không chạy lại browser.
- Worker103HTTP/112Python/58Frontend/51W04/build/lint được giữ dưới dạng báo cáo; chưa chạy lại các suite ấy.

## R1 HIGH — bỏ Chỉ KEV lại loại KEV
CveHttpProvider luôn gửi kev=String(query.kev). UI checkboxfalse nghĩa bỏ lọc, Sample provider đã dùng !query.kev||item.kev, nhưng HTTPfalse nghĩa loạiKEV theo contractBackend.
Ảnh final-browser-snapshot/01-detail-zero.png: bỏ chọn mà chỉ13CVE,0KEV trong dataset16CVE có3KEV.
Probe Leader kev-checkbox-probe.test.ts:1FAIL/2PASS exit1, đúngassert has(kev)true thayfalse. Fileprobe đã sửa Content-Type chuẩn trước lần kết luận; lần thử thiếu header trước đó không dùng kết luận.
Sửa ownerFrontend tại tree riêngf650f04d. HTTPunchecked bỏ parameterkev; checked giữkev=true. Không đổi Backend semantics hoặc relabel checkbox để che lỗi.

## R2 MEDIUM — kiểm wire phụ thuộc file ngoài và false PASS
Không có W03_WIRE_DIR: chạy vitest run tests/cves-wire-integration.test.ts trên candidate,5FAIL/2PASS exit1. Hai case503 vẫn PASS vì lỗi đọc fixture nằm trong fetcher rồi bị adapter map unavailable, chưa hề kiểm wire API. wire-default-red.log.
Cần fixtures API portable/được lưu trong repo kèm provenance; vẫn hỗ trợ override wire mới. Load/validate fixtures trước adapter/catch; paththiếu/JSONhỏng phải thất bại setup, không báoPASS503.
Bổ sung kiểm near-cap qua boundedHTTPprovider thay vì chỉ gọiparse; bổ sung POST/DELETE Technology làmthaymatches trên cùngDB (matrix hiện chỉ PUT).

## Điều phối
Frontend sửaR1 trên cti-w03-read-frontend; Engineer sửaR2/bằng chứng trên cti-w03-read-integration. Không viết chéo tree. Leader chỉ nối commitFrontend sau nghiệm thu; Engineer không chờ/poll/bot khác.
Hai input cũ vẫn giữ lịch sử accepted; integration chưaaccepted vì lỗi mới. Mobile/livefeed/OpenCTI/lab/production UNVERIFIED; chưa nối scope mới.
