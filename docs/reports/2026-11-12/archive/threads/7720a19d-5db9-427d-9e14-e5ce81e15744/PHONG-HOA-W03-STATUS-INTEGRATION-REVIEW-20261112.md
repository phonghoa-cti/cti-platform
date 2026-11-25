# W03-S1 — review tích hợp và bổ sung bằng chứng
Ngày 12/11/2026. Task W03-STATUS-INTEGRATION vẫn chưa accepted toàn bộ; đây là rework có tiêu chí cụ thể, không phải thử lại lỗi stalled.

## Ref và phần Leader đã đối chiếu
- Tree: $WORKSPACE/cti-w03-status-integration
- HEAD a2c4ffa245297a8714b0023bf4e4bb248869dc36; status sạch. Base prep 65e31980ac01910b825951676bae428ca3bf1742.
- git diff --check base..HEAD exit 0. So với Frontend accepted 2448b8600f9eff2c3e42b6742e220b46980f4ff4, toàn portal/web chỉ khác tests/cve-status-wire-capture.test.ts. Không suy parity từ thư mục src không tồn tại.
- Đọc diff hai commit mới 7be19ca/a2c4ffa: mở scenario/helper SQL counts, capture sáu response thật và gate parser. Không phát hiện thay đổi product UI mới.
- Báo cáo worker: $THREADS/484d57b0-1cb9-4264-b24a-54cecff6e454/PHONG-HOA-W03-STATUS-INTEGRATION-RESULT.md
- Evidence gốc: cùng thư mục cha, w03-status-integration-evidence/recovery-20261112. Manifest 69/69 khớp; SHA256 f6a4543e041c4fdabde40e7827aaf41bf3f99a13580016a1c39b5d4696715066.
- Leader mở ảnh known-recovered.png và unknown-reconciled.jpg: trạng thái cuối v1 hiện đúng; known có notice đã lưu, unknown không tự báo save thành công.
- Leader mở SQLite bằng mode=ro và đọc trace cho cả năm scenario: regular 2 PUT/2 audit/1 record; known PUT200 + GET503,503,200, 1 audit; unknown PUT503 + GET503,200 sau tải lại trang, 1 audit; conflict PUT200 rồi PUT409 vẫn 1 audit; smoke 0 status/audit.
- State của năm helper đều ghi stopped/port_closed/temp_removed. Đây là đối chiếu tệp cleanup; lượt Leader này chưa tái kiểm PID/port do state cuối không lưu các định danh đó.
- Log worker có 6 helper tests, 150 HTTP assertions, 4 wire tests và 58 component/provider tests. Leader đọc log, không chạy lại các suite đã đạt.
- Không nghiệm thu lại Backend, Frontend, prep hoặc các accepted_results trước.

## E1 — dữ liệu biên qua API thật còn thiếu
Brief gốc mục 1 yêu cầu giới hạn note/actor/context và history lớn hợp lệ. Capture hiện dùng note ngắn, identity/context seed ngắn và history đúng một item; test còn assert length=1. Chưa có bằng chứng API thật và parser/provider UI tương thích ở biên.

Một Engineer Sol medium trực tiếp bổ sung capture + fixture/gate trong allowlist cũ:
- Lấy giới hạn từ contract/code hiện tại (note 1000; vendor 128, product 256, software_version 128; history limit tối đa 100; actor theo validator thật). Không đổi giới hạn.
- Capture status/history thực với chuỗi sát giới hạn, Unicode hợp lệ và ngày do API trả, trang history đủ 100 item cùng next_cursor nếu có. Seed dữ liệu tổng hợp qua API/store hợp lệ trong DB test riêng; không fake envelope bằng viết tay.
- Cho production parser/provider đọc response đó. Bao gồm thiếu/hỏng fixture fail khi required=1; truyền thư mục hiện hữu nhưng thiếu file hoặc JSON lỗi, không chỉ kiểm thiếu env.
- Chỉ focused capture/wire tests và Ruff/format/diff tương ứng; không lặp full matrix, build hoặc auth suite nếu không đổi product/build.
- Nếu thấy product defect, dừng sửa ngoài allowlist và trả repro tối thiểu; không tự sửa Backend/Frontend.

## E2 — ảnh/trình tự trạng thái tạm thời còn thiếu
Ảnh hiện chỉ là trạng thái sau phục hồi. Trace chứng minh không replay, nhưng chưa chứng minh trực tiếp thông báo/khóa form khi đọc lỗi hoặc sau đóng/mở panel. Unknown hiện có GET /lo-hong 304: đó là tải lại trang; không ghi thành đã kiểm đóng/mở panel hoặc A→B→A.

Bổ sung hai lượt nhỏ bằng Browser tab OpenMausBot được cấp, không đổi công cụ hoặc dùng màn hình host:
1. Known: PUT200 rồi hai GET503; chụp notice đã lưu còn hiện trong lỗi đọc, thử lại GET tới200 và ảnh sau. Đóng/mở panel hoặc A→B→A trong recovery một lần; phân biệt hành vi đã kiểm trực tiếp và component tests cũ.
2. Unknown: PUT503 sau upstream commit và GET503; chụp form đang khóa (kèm snapshot disabled/read-only nếu ảnh không rõ), đóng/mở panel hoặc A→B→A trong cùng trang; chỉ GET đối soát tới200. Không dựa vào reload cả trang để thay bằng chứng giữ trạng thái trong app. Trace/SQLite cuối đúng một PUT, một audit. Không tự suy PUT thành công từ GET.
Giữ evidence cũ; run_id/subfolder mới. Ghi lại các bước và nội dung hiện/ẩn ở từng bước, ref browser nếu có, kích thước viewport thật. History409 đã có HTTP/component evidence có thể tái dùng và nêu rõ chưa bấm trên browser; không cần lặp cả suite.
Nếu browser thiếu khả năng cần, trả giới hạn chính xác và phần code/wire hoàn chỉnh, không treo chờ.

## E3 — tài liệu tái chạy và cleanup
- Thêm lệnh đầy đủ capture/wire/env cho người khác chạy trong README integration; báo cáo có cwd, interpreter tuyệt đối, exit/count, không dùng dấu ... thay tham số.
- Cập nhật docs/PROGRESS và mục Giới hạn bằng chứng trong docs/specs/W03-status-local-contract.md theo đúng mức kiểm (chỉ sửa đoạn tiến độ/giới hạn, không sửa contract). Hai tài liệu hiện vẫn ghi chưa ghép UI/chưa browser; không xóa giới hạn mobile/lab/production.
- Evidence lưu PID/port/temp-root thuộc từng lượt trước cleanup, xác nhận chúng đã dừng/đóng/xóa sau cleanup. Không đụng tài nguyên không sở hữu.
- Final HEAD sạch, manifest mới, git diff --check. Chỉ ghi report tiến độ có bằng chứng, không gọi toàn bộ PASS nếu E1/E2 còn thiếu.

## Phạm vi và đầu ra
Giữ thread b05471df-3a0c-49c0-b02b-4019e1cf15d4 và branch/tree hiện có, không cherry-pick lại. Một writer, không worker con, không sửa RUNS hoặc source tree khác.
Tái dùng nghiên cứu và contract S1: ROOT/PHONG-HOA-W03-STATUS-IMPLEMENT-BRIEF-20261112.md (SQLite transactions/isolation, RFC9110 409, OWASP Logging); không nghiên cứu/thiết kế lại. Không push/PR/merge/deploy, deps/lockfile, quyền, lab, feed/cloud/LLM thật, secret hoặc S2.
Đầu ra mới tại thư mục lượt hiện tại:
- $THREADS/7720a19d-5db9-427d-9e14-e5ce81e15744/PHONG-HOA-W03-STATUS-INTEGRATION-EVIDENCE-REWORK-RESULT.md
- $THREADS/7720a19d-5db9-427d-9e14-e5ce81e15744/w03-status-evidence-rework/
Không ghi đè report/evidence cũ ở cuộc khác. Tối đa hai lần cùng lỗi; trả blocker/repro ngay nếu không tiến được. Leader nghiệm thu phần bổ sung rồi chọn bước tiếp, không giao lại phần đã accepted.
