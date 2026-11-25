# W04 Technology — review Leader và yêu cầu sửa

Kết luận ngày 11/11/2026: **FAIL nghiệm thu hai đầu vào; chưa giao tích hợp**. Chỉ các lỗi bên dưới cần sửa; giữ nguyên thiết kế/hợp đồng/phạm vi đã giao.

## Mã và bằng chứng đã đối chiếu

- Backend `b32fbfe8bb5e72230424ab23d27f8949238dd2a9`, tree `cti-w04-technology-backend`, sạch; 8 file +1412/-0.
- Frontend `2419b29656092edcf2bb20b0d7c62a12fa0774c0`, tree `cti-w04-technology-frontend`, sạch; 13 file +1337/-5.
- Cùng base đã nghiệm thu `8a767314b654d39c1ddc2995b7919c44a5b7027a`.
- Fixture Backend khớp SHA256 `f98df16abb8f92d441b56b718f0436f8bfd1b2c10bc1919c588eda156f816cb5`.
- Leader chạy mới 47 test technology sẵn có: đạt. Thêm 8 probe Backend: 6 fail, 2 pass; lệnh tổng exit1.
- Leader chạy 4 probe Frontend cuối: 4 fail đúng hành vi, exit1. Một lần đầu đọc fixture bằng URL bị lỗi hạ tầng test; đã sửa riêng đường dẫn probe và chạy lại, không tính lần đó là bằng chứng lỗi sản phẩm.
- Leader tạo 1000 record qua TechnologyStore thật trên SQLite tạm: đạt, output 1,705,904 byte UTF-8. Parser Frontend nhận đủ 1000, nhưng HTTP adapter từ chối.
- Hai tree sản phẩm vẫn sạch sau review; không sửa source, không nối code, không chạy browser/lab.

Evidence tại `leader-w04-technology-acceptance-20261111/`: `backend-red.log`, `frontend-red.log`, `capacity-generation.log`, `backend-valid-1000.json`, hai probe và cấu hình Vitest.
Báo cáo worker 148 Backend/111 Frontend và build là evidence của worker, không gọi là Leader đã chạy lại toàn bộ.

## B1 — Backend: timestamp trái wire vẫn đọc/ghi (MEDIUM)

`_validate_timestamp` chấp nhận các dạng ISO rộng hơn hợp đồng: `2026-11-11T16:00:00+00:00`, `2026-11-11 16:00:00Z`, `20261111T160000Z`. Leader chèn từng dạng vào created_at của một record trong DB thử:
- GET trả200 dù Frontend strict timestamp sẽ từ chối.
- PUT trả200, thực sự ghi note mới/version2/audit2, trả created_at trái wire.
- Mong đợi503 assets_unavailable, note/version vẫn rỗng/1, audit1.

Sửa nhỏ trong TechnologyStore: kiểm cú pháp đúng YYYY-MM-DDTHH:mm:ss[.fraction]Z và giá trị lịch hợp lệ; mọi timestamp trả ra phải qua cùng validator trước commit. Không tự sửa row hỏng. Giữ dạng chuẩn có/không phần thập phân. Regression GET/PUT (và kiểm DELETE không ghi khi row hỏng), cả created_at/updated_at phù hợp. Không đổi W04 domain/CIDR.

Allowlist rework: technologies.py, hai test technology, PROGRESS nếu cần; docs chỉ khi mô tả chính xác, không đổi wire/fixture. Chạy 8 probe Leader nguyên bản + focused technology; Ruff/format/diff-check. Không cần lặp assets/W02 khi không sửa chúng hoặc app/shared schema.

## F1 — Frontend: giới hạn 1MiB từ chối danh sách hợp lệ (MEDIUM)

1000 record Backend tạo thật, các field đúng bound, tổng1,705,904 byte. parseTechnologyList thành công nhưng createTechnologiesHttpProvider.list() trả unavailable ở cả Content-Length và stream không có header đó.

Sửa cap đọc có chặn hữu hạn và đủ cho mức tối đa contract của technology: 1000 DTO, Unicode code points, JSON escaping và byte UTF-8. Có thể dùng cap riêng cho GET danh sách, giữ cap nhỏ cho mutation/error. Ghi tính toán bound; không bỏ cap, timeout, cancel hoặc validation 1000/1001. Không giảm giới hạn Backend hoặc đổi API để né lỗi. Test cả response có/không Content-Length, Unicode sát bound và vượt cap.

## F2 — Frontend: mất thông báo đã commit khi GET retry lỗi lần nữa (MEDIUM)

POST thành công → GET503 → notice đã lưu; bấm Tải lại danh sách công nghệ → GET503: notice biến thành lỗi dịch vụ chung, mất trạng thái đã lưu. Contract yêu cầu giữ đã lưu và chỉ GET retry.

Giữ notice qua mọi lần GET đang tải/thất bại; khi GET thành công thì thoát trạng thái cần refresh đúng cách. Bao phủ create/update/delete, không tăng mutation count và không cho refresh context cũ ghi notice mới.

## F3 — Frontend: đổi tab xóa trạng thái chưa rõ kết quả ghi (HIGH)

Create trả unknown-mutation → nút Thêm bị khóa đúng; đổi sang Tên miền rồi về Công nghệ → GET đối soát lỗi503 nhưng nút Thêm lại mở. Người dùng có thể gửi lại trong khi lần trước có thể đã ghi.

Giữ trạng thái pending/unknown theo đúng provider/ngữ cảnh ghi qua việc rời/quay lại tab; chỉ mở sau khi không còn mutation pending và GET đối soát thành công. Không để GET thành công quá sớm lúc mutation cũ còn pending mở khóa. Provider mới độc lập không bị khóa nhầm, callback/notice cũ không ghi lên tab/provider mới. Không replay mutation. Không cần thêm persistence qua tải lại toàn trang hay đổi thiết kế.

Allowlist Frontend rework: technology-panel.tsx, assets-app.tsx nếu cần quản lý lifetime; data/technologies-http.ts, tests technology/panel/adapter; messages nếu cần; PROGRESS. Không Backend/gateway/dependency/real route/RUNS hoặc tree khác. Chạy 4 probe Leader nguyên bản, bổ sung regression F1–F3, focused technology+assets, typecheck/lint/build/diff-check.

## Cách chạy probe nguyên bản

Root chung là thư mục chứa báo cáo này. Python đúng môi trường: `cti-w02-lookup-api/.venv/Scripts/python.exe`.

Backend cwd tree Backend; PYTHONPATH gồm tree, tree/core, tree/extractor:
`python -m pytest portal_api/tests/test_technologies_store.py portal_api/tests/test_technologies_api.py ../leader-w04-technology-acceptance-20261111/backend_probes.py -q -s --tb=short`

Frontend cwd `leader-w04-technology-acceptance-20261111`:
`node ../cti-w04-technology-frontend/portal/web/node_modules/vitest/vitest.mjs run --config vitest.config.mjs --reporter=verbose`
node_modules junction trong thư mục probe đã trỏ đúng Frontend. Không sửa probe/config/fixture Leader để đạt test.

SHA256 probe Backend: `3a022eb79f3ca1b1c08bc62ed51d09cb89217bca5629471101f0535d13cf5dcf`.
SHA256 probe Frontend: `218118d0f58a523e25e60eba1734da7ed9a1e008ddf93d196cbd31cd9be19a45`.
SHA256 fixture1000: `b0f87acdac467348c5dd2f66447a04923914dde7daeba08752e499dcd2198b78`.

Mỗi nhóm một Sol medium trực tiếp trên tree hiện tại; không giao tiếp người khác/worker con. Trả final clean SHA, diff so base rework, RED→GREEN counts/exit/raw log, giới hạn chưa kiểm. Cập nhật báo cáo kết quả và evidence riêng đã được giao. Không push/PR/merge/deploy/lab hoặc nhận đã tích hợp.
