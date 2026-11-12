# W03-INTEGRATION rework R2 và phần bằng chứng thiếu
ROOT = $WORKSPACE
Một CTI Engineer Sol medium trực tiếp, khôngworkercon/botkhác. Cùng thread024d0127-8ec0-48ac-bd81-cbe0d65ff053 và tree ROOT/cti-w03-read-integration tại93962d9ec771c49855c213e6332be0632e33debd. Khôngreset/sourcechanges.
Đọc ROOT/leader-w03-integration-review-20261112/REVIEW.md và briefintegrationgốc. R1checkbox đang giaoFrontend tree riêng; **không tự sửa adapter/component, không cherry-pick hoặc chờ/poll Frontend**. Trả xong phầnR2 này độc lập; Leader gửi commitR1 vào cùngthread sau nghiệmthu. Toànluồng giữCHƯAĐẠT trước khi R1 ghép và kiểm.

R2 đãtái hiện: với W03_WIRE_DIR khôngđặt, vitest run tests/cves-wire-integration.test.ts cho5FAIL/2PASS; hai503testfalsePASS vì đọcfilelỗi bên trongfetcher rồi bịmapunavailable.
Chọn sửa: ghi wire API thật đãcapture thành fixtureportable trong portal/web/tests/fixtures/w03-integration/**, kèmprovenance/hashes/cách táitạo; defaultresolve từfiletest, không phụ thuộc đườngdẫn máy/ROOT. Giữ W03_WIRE_DIR override để kiểm wire mới nếuđặt.
Load/validate fixtures ngoàiHTTPcatch trước test để missing/JSONhỏng báo lỗiđầu vào, tuyệtđối không tínhhai503PASS. Test điều kiện thiếu/hỏng bằng fixturecopy trongtmp hoặcpreflight riêng, không sửa fixturegốc/evidence đãđạt. Đừng skiptoànbộtest để tránhđỏ.

Bằng chứng cònthiếu:
- near-cap realAPIwire phải đi qua createCvesHttpProvider.list với responseContent-TypeJSON/bytebody thật, cả có/khôngContent-Length hợp lệ; quá1MiB bịreject. Không chỉ parseCveResponse.
- Bổsung matrix W04POST tạoTechnology match mới, rồi DELETE làm mấtmatch trên cùngDB; cursor đổi409 nếuđangphântrang; GET khôngđổi schema/rows/audit. Giữ phân biệt mutationW04cóchủý với W03GET. Matrix trước chỉPUT.
- README phải có lệnh thực chạy đầyđủ --output --evidence-dir và W03_WIRE_DIR optional/default; outputcommand ởreporthiện --evidence... không khớp CLI, sửa cho táitạo được.

Allowed thêm theo briefgốc: testfixture/provenance, cves-wire-integration.test.ts, tools/local_integration tests/matrix/README,docsPROGRESS/report; không productfrontend/backend/deps/ledger.
Chạy focusedwire defaultunset, wire overridepathvalid, thiếu/hỏng failpreflight; matrixmới; Ruff/format/diff. Không lặp full112/356/build/browser cũ vì khôngđổi product. Giữ42artifactcũ nguyên, tạo evidence R2 thưmụcROOT/w03-integration-rework-evidence đểtrace khôngghiđè.
Output ROOT/PHONG-HOA-W03-INTEGRATION-REWORK-RESULT.md, cleanSHA/delta/commands/count và noteR1pending. Không tự gọiPASS toànluồng hoặc tự giao bot. Không push/PR/merge/deploy/feed/lab/secret.
