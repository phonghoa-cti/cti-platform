# W05-SELECTION-UI-NEXT — nghiên cứu và brief nối giao diện lựa chọn

Owner CTI Research. Chỉ đọc và viết hai tài liệu, không sửa sản phẩm/giao bot khác. Dùng nghiên cứu còn phù hợp; tối đa hai cách quản lý thao tác lưu, không khảo sát lại framework/JWT/LLM hoặc thiết kế lại portal.

Root: `$WORKSPACE`.

## Nguồn thật phải đọc

- Tree `<root>\cti-w05-selection-api`, HEAD **812dae1ffbdc8e8866342cc075d925fdc99ef12d**, branch feat/w05-selection-api-20261111, đã nghiệm thu trong `PHONG-HOA-W05-SELECTION-API-REVIEW-20261111.md`. Kiểm ref/status trước đọc, không reset. Đọc AGENTS.md, docs/PROGRESS.md, spec W05, docs/design/DESIGN.md nếu có, docs/specs/api-portal.md và W05-draft-offline-contract.md.
- API source là `portal_api/schemas.py`, app.py/service.py và tests; nghiên cứu/plan Selection API tại root là bối cảnh, source ref trên là hợp đồng thực tế. Bốn thao tác `/api/v1/drafts`; selection view không draft_id; decision có snapshot; body max65536 byte, selection input max1024, strict JS safe integers, errors401/403/404/409/413/415/422/503.
- UI ngay trong tree đó: `portal/web/data/api-client.ts`, `components/draft-review-app.tsx`, `components/draft-review.tsx`, types/fixtures/messages và tests. Tìm file bằng rg, giữ thiết kế/VI-EN/Unicode code point/defang/clipboard/sample đã có. UI cũ có exact parser, khóa chống double-submit, bỏ response detail cũ, giữ quyết định đã ghi khi refresh lỗi/queue rỗng, chọn lại cùng ID không làm mất detail. Không hồi quy các phần này.
- Đọc `tools/local_integration/gateway.mjs`/README liên quan chỉ để xác định phần còn thiếu cho browser v1; không sửa harness. Không báo browser end-to-end khi gateway chưa hỗ trợ path mới.
- Tìm nguồn chính thức React về state/forms/race hoặc MDN về fetch/abort, chỉ những điểm cần thiết cho quyết định. Ghi link/ngày đọc, phân biệt suy luận với code/test thực chạy.

## Những điểm brief phải chốt

1. Luồng nhỏ nhất: load detail → chỉnh selected_indices riêng → lưu lựa chọn → quyết định theo version đã lưu. So lưu rõ ràng bằng nút với autosave, khuyến nghị **nút Lưu lựa chọn** cho lát cắt này để tách rõ thay đổi chưa ghi và quyết định. Không tự nối save→approve nếu chưa có contract/test đầy đủ. Dùng màn/component hiện có, không tạo dashboard/design mới.
2. Tách `items.keep` gốc, snapshot selection đã lưu và lựa chọn người dùng chưa lưu. Không thay payload hoặc giả keep. Chỉ checkbox của IOC eligible được chỉnh; giữ nguyên allowlist/bịa/loại không hỗ trợ. Counts từ đâu, label và thông báo VI/EN phải rõ. Chốt hành vi empty selection, no-op, limit1024 trong khi read có thể trả nhiều hơn, version ceiling và quyền từ backend.
3. Khi dirty (đã sửa nhưng chưa lưu), nút quyết định phải không duyệt snapshot khác điều đang hiện. Chốt lưu/hủy thay đổi, chuyển draft/pagination/reload khi dirty, khóa lúc POST và lỗi. Không âm thầm mất chỉnh sửa hoặc tự gửi thay người dùng; chọn cách đơn giản và giải thích.
4. Save response mới hợp lệ, POST thành công nhưng refresh fail, response lỗi/mất mạng sau POST chưa rõ đã ghi, 409 conflict, 401/403/413/422/503: state nào giữ, lúc nào cho tải lại, lúc nào mở nút. Không tự retry POST, không overwrite draft B bằng response draft A. Phân biệt đã lưu với chưa xác định; lỗi transport không chứng minh DB chưa ghi.
5. Parser v1 exact/safe; kiểm review+selection versions, sorted/unique indices/subset eligible, hash format và response/request association phù hợp. Không tự nhận response sai draft/version là thành công. Reuse helper cũ khi đúng; cập nhật fixture/demo/test theo shape thật, không giữ fallback legacy làm bỏ mất selection.
6. `/duyet/mau` tiếp tục có nhãn mẫu và không POST; `/duyet` dùng v1, không fallback mẫu khi lỗi. Không đưa JWT/identity/role tự khai vào frontend. Không thay backend/gateway/settings/dependency trong task UI.
7. Brief triển khai cho **CTI Frontend/Sol medium** trên worktree mới đề xuất `<root>\cti-w05-selection-ui`, branch `feat/w05-selection-ui-20261111`, base 812dae1 ở trên. Không tạo tree trong nghiên cứu. Scope cụ thể `portal/web` code/tests/docs liên quan + PROGRESS. Nếu phải đổi shared type thì chỉ rõ sample và legacy behavior nào bị ảnh hưởng.
8. Acceptance matrix có ca đúng/biên/lỗi/race/dirty navigation, saved-vs-unsaved decision, committed save refresh failure, unknown POST outcome, stale detail, duplicate action, sample không gọi API, Unicode/clipboard/defang/VI-EN regression. Unit/component fetch giả lập + typecheck/lint/build là bằng chứng UI cục bộ; browser cùng API/gateway là bước Engineer sau đó, không đánh đồng. Không viết lại backend tests hay chạy browser 404 để gọi đó là tích hợp thành công.

## Hai đầu ra duy nhất

- `<root>\PHONG-HOA-W05-SELECTION-UI-RESEARCH.md`: nguồn đã đọc, so hai cách/chọn, state/flow/error decisions, reuse và điều còn chưa biết.
- `<root>\PHONG-HOA-W05-SELECTION-UI-IMPLEMENTATION-BRIEF.md`: tự đủ ref/tree/scope, state transitions, API examples chính xác, copy/flow VI-EN, tiêu chí và lệnh kiểm phù hợp, handoff Engineer sau UI accepted.

Không sửa code/RUNS/report/plan cũ; không chạy implementation/tests sản phẩm, cài dependency, mở listener/browser, dùng secret/cloud/lab/model/OpenCTI, push/PR/merge/deploy. Báo hash hai file và ref/status nguồn. Leader kiểm rồi mới giao Frontend triển khai; nghiên cứu không được báo thành UI đã chạy.
