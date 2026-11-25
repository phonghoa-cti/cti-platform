# W05-API-NEXT — chốt bước nối portal với lõi duyệt

Owner CTI Research. Nghiên cứu và viết brief, không sửa repo hoặc chạy implementation. Tự làm, không giao bot khác.

## Mục tiêu

Chọn lát cắt HTTP nhỏ nhất có ích để portal đi từ dữ liệu mẫu tới lõi W05 đã có, với danh tính/quyền kiểm được ngoại tuyến. So tối đa hai cách: đọc có xác thực trước, hoặc đọc + quyết định với auth cùng lượt. Chọn một, giải thích phạm vi và phụ thuộc; không cần người dùng quyết định kỹ thuật có thể đảo ngược.

## Nguồn đúng ref

Workspace cha: `$WORKSPACE`.

- `cti-w05-backend` HEAD `f87b7f51acd51961eb9de26af42cea9d65d9cc9b`: AGENTS, PROGRESS, specs api-portal/W05/F08, store.py và review tests. Có local policy/audit; chưa có HTTP/JWT.
- `cti-portal-web` commit `be364bd87cd87a86b37d83e8a74e1ff3583ea7ec`: adapter/README và contract frontend. Frontend đang rework riêng: đọc bằng `git show <sha>:<path>`, không sửa hoặc lấy working copy thay ref nêu trên.
- Kế thừa PHONG-HOA-W05-NEXT-RESEARCH.md, PHONG-HOA-W05-REVIEW-RESULT.md, PHONG-HOA-LEADER-ACCEPTANCE-20261111.md và PR #1/#46 đang mở; không nghiên cứu lại W05 core.
- Đối chiếu tài liệu chính thức FastAPI dependency/auth testing, Cloudflare Access JWT validation, SQLite và tài liệu web khi cần CORS/CSRF. Ghi URL, phiên bản/date và chưa biết; không tự coi email header là identity đã xác thực.

## Ranh giới thiết kế cần chốt

- Giữ payload draft 1.0 bất biến, review metadata riêng. Không đồng nhất payload.status pending với review.status approved/rejected.
- Danh tính actor lấy từ verified identity, role server-side; không nhận subject/role/email do body hoặc header trần tự khai. Xác định issuer/audience/expiry/signature và subject ổn định; offline dùng khóa/fixture tổng hợp, không cần secret thật.
- Dev mode nếu chọn phải tắt mặc định và không thể vô tình mở trong production. API key xuất blocklist không được dùng quyết định draft.
- Explicit migrate, đọc không ghi; rollback/audit/stale version, lỗi 401/403/404/409/422/503 và dữ liệu không rò qua error/log. Không gửi dữ liệu sang OpenCTI.
- Chốt endpoints/request/response/pagination và cache policy cho dữ liệu CTI, mode phục vụ UI/same-origin hoặc CORS/CSRF; không bật CORS wildcard cùng credential.
- Dependency tối thiểu, version/license và cách test offline. Không mở network listener public, lab/cloud/model thật, không cài dependency hoặc ghi repo ở nhiệm vụ nghiên cứu.

## Đầu ra

Chỉ ghi `PHONG-HOA-W05-API-RESEARCH.md` và `PHONG-HOA-W05-API-IMPLEMENTATION-BRIEF.md` tại workspace cha. Brief tự đủ: base SHA/tree/branch, file được sửa, behavior/contract, decision auth, test positive/negative, lệnh/exit cần báo, demo và bước Frontend nối tiếp. Không ghi RUNS.

Đạt khi Leader có thể giao Backend triển khai mà không phải đoán trust boundary hoặc đổi lại contract. Phân biệt test API in-process, browser và lab; không ghi đã auth thật/tích hợp khi mới là đề xuất.
