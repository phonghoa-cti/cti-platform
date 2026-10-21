# Hướng dẫn 01 — Làm việc với opencode và agy trong repo

**Mục tiêu:** mỗi bạn chạy được opencode (agent chính) và agy (agent phụ) trong repo `cti-platform`, giao việc theo đúng quy trình spec → test → code → review.

**Vì sao:** nhóm làm chủ yếu bằng AI agent. Dùng đúng cách thì agent viết code có test và giải thích; dùng sai thì agent sinh code rối mà không ai hiểu.

## Phương án đặt agent ở đâu

| Cách | Ưu | Nhược |
|---|---|---|
| **WSL2 trên laptop (khuyến nghị)** | Tài liệu opencode khuyến nghị; lệnh Linux giống hệt máy chủ | Phải bật WSL2 một lần |
| Chạy thẳng trên Windows | Không cần cài thêm | Lệnh khác máy chủ, hay vướng đường dẫn |
| Chạy trên máy Ubuntu qua SSH | Gần OpenCTI | Máy i3 vừa chạy OpenCTI vừa chạy agent sẽ chậm |

## Bước 1 — Bật WSL2 (một lần)
Mở PowerShell **với quyền Administrator**:
```powershell
wsl --install -d Ubuntu     # cài WSL2 kèm Ubuntu; khởi động lại máy khi được yêu cầu
```
Mở ứng dụng "Ubuntu" từ menu Start, đặt tên đăng nhập và mật khẩu. Từ đây gọi là **terminal WSL**.

Trong terminal WSL:
```bash
sudo apt update && sudo apt install -y git python3-pip   # cài git và pip trong WSL
git config --global user.name "Tên Của Bạn"
git config --global user.email "email@github"
mkdir -p ~/code && cd ~/code
git clone https://github.com/<org>/cti-platform.git        # tải repo về WSL (thay <org>)
cd cti-platform
```
Lưu ý: làm việc trong `~/code` của WSL sẽ nhanh hơn nhiều so với `/mnt/d/...` (ổ Windows).

## Bước 2 — Cài opencode và kết nối gói Go
```bash
curl -fsSL https://opencode.ai/install | bash   # cài opencode (lệnh chính thức)
opencode                                         # mở giao diện opencode trong thư mục repo
```
Trong opencode:
1. Gõ `/connect`, chọn **opencode**, mở opencode.ai/auth để lấy key của tài khoản có gói Go, rồi dán vào.
2. Gõ `/models` để chọn model. Gợi ý: model mạnh (bản Pro/Max) khi lập kế hoạch và review; model Flash cho việc lặp lại như sửa lint hay viết test đơn giản.
3. **Không** chạy `/init` — repo đã có `AGENTS.md`, chạy lại sẽ ghi đè.

## Bước 3 — Dùng 3 agent của nhóm
Repo có sẵn 3 agent trong `.opencode/agents/`:

| Agent | Loại | Gọi thế nào | Dùng khi |
|---|---|---|---|
| planner | primary | Bấm **Tab** để chuyển | Bắt đầu một issue: hỏi ngược, viết spec, chia task |
| implementer | primary | Bấm **Tab** để chuyển | Có spec rồi: viết test, code, commit |
| reviewer | subagent | Gõ `@reviewer` trong tin nhắn | Trước khi mở PR: soát theo spec và an toàn |

Lệnh hữu ích: `/undo` hoàn tác thay đổi gần nhất của agent (gõ nhiều lần để lùi tiếp), `/redo` làm lại.

## Bước 4 — Cài agy (Antigravity CLI)
```bash
curl -fsSL https://antigravity.google/cli/install.sh | bash   # cài agy trong WSL
agy --version                                                 # kiểm tra đã cài
cd ~/code/cti-platform && agy                                 # mở agy trong repo
```
Lần đầu: chọn **Google OAuth**, đăng nhập tài khoản có gói Google AI Pro, dán mã xác nhận, chọn **Yes, I trust this folder**.

Giữ chế độ quyền mặc định `request-review` (agy hỏi trước khi chạy lệnh hoặc ghi file) — đổi trong `/config`. **Không** dùng cờ `--dangerously-skip-permissions`.

Nếu agy có vẻ không đọc `AGENTS.md`, luôn mở đầu bằng: *"Đọc AGENTS.md và docs/PROGRESS.md trước, làm theo chế độ học."*

## Bước 5 — Chạy hai agent song song mà không giẫm chân nhau
Dùng **git worktree**: một repo, nhiều thư mục làm việc, mỗi thư mục một nhánh.
```bash
cd ~/code/cti-platform
git worktree add ../cti-review main      # tạo thư mục ../cti-review đang ở nhánh main
```
- opencode làm việc trong `~/code/cti-platform` (nhánh tính năng).
- agy review trong `~/code/cti-review`: `git fetch && git switch <nhánh-cần-review>` rồi nhờ agy soát.

## Mẫu câu giao việc (copy và sửa)
- **Bắt đầu tính năng (planner):** *"Đọc issue #12 và docs/specs/F01-thu-thap-feed.md. Hỏi tôi những gì còn mơ hồ, rồi chia thành các task ≤ 2 giờ, mỗi task có cách kiểm tra."*
- **Làm một task (implementer):** *"Làm task 1 trong spec F01. Viết test trước, chạy cho thấy test fail, rồi mới code. Giải thích từng bước cho người mới."*
- **Review (agy hoặc @reviewer):** *"Review diff của nhánh này so với main theo docs/specs/F01 và AGENTS.md mục 5. Phân loại CHẶN / NÊN SỬA / GỢI Ý."*
- **Khi bí:** *"Dừng lại. Tóm tắt: mục tiêu, đã thử gì, lỗi chính xác là gì, 2 giả thuyết nguyên nhân."*
- **Hết quota giữa chừng:** *"Viết tóm tắt bàn giao vào docs/PROGRESS.md: đang làm gì, file nào đang dở, bước tiếp theo."* Sau đó mở agent kia và bảo nó đọc PROGRESS.md.

## Kiểm tra là xong
- `opencode` mở được trong repo, bấm Tab thấy planner/implementer.
- `agy` mở được trong repo, `/help` hiện danh sách lệnh.
- Nhờ implementer chạy `make test` → thấy `47 passed`.

## Học thêm
- **Agent primary và subagent:** primary là agent bạn trò chuyện trực tiếp; subagent là "trợ lý của agent", được gọi cho một việc hẹp như review.
- **WSL2:** một máy Linux thật chạy bên trong Windows, dùng chung ổ đĩa và mạng.
- **Git worktree:** nhiều thư mục làm việc cho cùng một repo, mỗi thư mục một nhánh. Hai agent làm song song không sửa đè file của nhau.
- **Quyền của agent (permission):** quy định agent được tự làm gì, phải hỏi gì. Quyền càng rộng thì càng nhanh nhưng càng dễ gây hỏng.
