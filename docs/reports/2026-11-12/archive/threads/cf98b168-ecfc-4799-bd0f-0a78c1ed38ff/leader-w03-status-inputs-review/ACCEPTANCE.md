# W03-S1 — nghiệm thu Frontend và yêu cầu sửa prep R1

Ngày 12/11/2026, Leader. Phạm vi là cục bộ; chưa ghép UI/browser, chưa lab/production.

## Frontend và QA: ACCEPTED_LOCAL

Candidate 2448b8600f9eff2c3e42b6742e220b46980f4ff4; delta từ13b8025274a70ec88dc21dd9ca7f51c68961e881 đúng4file +69/-13. HEAD/status sạch đã kiểm lại. Leader đã đọc delta ở lượt giao QA, đọc lại registry/read/submit và đối chiếu kết luận QA.

- QA request4f08b204-42d0-445d-ba0d-67fad30c6063 trả report PHONG-HOA-W03-STATUS-FRONTEND-QA-RESULT.md:3probe mới+7probe cũ đạt, exit0. Đây là lượt QA chạy.
- Leader chạy mới nguyên3probe F5/F6 bằng vitest.recheck.config.ts:3PASS, exit0; log leader-w03-status-inputs-review/frontend-recheck.log. Không lặp7probe hoặc full suite/build.
- Leader xác nhận9mục manifest gốc,8input QA và4source hash đều khớp. Bằng chứng: leader-w03-status-inputs-review/hash-checks.json.
- F5/F6 đóng trong phạm vi parser/provider/component: snapshot đổi hoa/thường hợp lệ; conflict sau remount giải pending và chỉGETđối soát, không replayPUT. A→B→A/provider khác được review source/test và dùng kết quả QA.
- Nghiệm thu cả báo cáo QA và input Frontend tại SHA trên. Backend4f7100cf giữ accepted từ lượt trước, không kiểm lại.
- Không nâng bằng chứng này thành browser/runtime toàn luồng.

## HTTP prep: REWORK_REQUIRED_R1

Candidate32b5c068c4d6da5a0abb00906c619f92f13b9177; delta8file +641/-7 từ4f7100cf, đúng allowlist; tree sạch và diff-check exit0.30/30 artifact của SHA256SUMS.txt khớp. Các số144HTTP/98Python/16gateway/W03-R120/W0451 là báo cáo+artifact Engineer, không phải Leader chạy lại và không đủ đóng R1.

R1 mức medium, ảnh hưởng độ tin cậy phép kiểm recovery: bộ đếm lỗi GET status dùng chung mọi quan hệ và cả status-history. Brief prep đã yêu cầu fault chỉ đúng relation/route. Request khác có thể tiêu thụ lỗi dự kiến của quan hệ vừa ghi, khiến case recovery đổi ý nghĩa hoặc thành falsePASS.

Leader chạy node --test leader-w03-status-inputs-review/fault-scope-probe.mjs:0PASS/2FAIL assertion, exit1. Probe độc lập chỉ kiểm gateway thật với upstream tổng hợp; không giả đây là API/SQLite/browser thật.

- Known commit: PUT A200, GET B503, GET A/history503, GET A/status200→200→200. Cần B/history200 và A/status503→503→200.
- Unknown outcome: PUT A503, GET B503 rồi GET A/status200→200. Cần B/history200 và A/status503→200.
- Source: tools/local_integration/gateway.mjs, statusGetFailuresRemaining và nhánh isStatus GET. Chỉ khóa fault theo exact pathname status của mutation, không áp vào history/quan hệ khác; giữ counters/fault hữu hạn và không tự replay.

Hai log/probe gốc giữ nguyên. Không sửa code sản phẩm hoặc source tree. Giao Engineer rework cùng thread b05471df-3a0c-49c0-b02b-4019e1cf15d4 và tree cti-w03-status-integration; Frontend đã đạt nhưng chưa cherry-pick trước prep được nghiệm thu. Không giao writer khác.

Đã kiểm threads một lần: các worker liên quan idle; cuộc Leader chính đã báo nhường phần này cho lượt tự động. Hai lịch Phong Hỏa vẫn enabled vì mục tiêu tổng còn mở; không tạo/pause lịch.
