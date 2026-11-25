# Hướng dẫn 02 — Git hằng ngày cho nhóm 3 người

**Mục tiêu:** ba người (và các agent) cùng sửa một repo mà không ghi đè việc của nhau.

**Vì sao:** lỗi phổ biến nhất của nhóm mới không phải code sai, mà là mất code hoặc xung đột khi gộp.

## Vòng làm việc chuẩn (mỗi issue một vòng)
```bash
git switch main && git pull                 # 1. về nhánh main và tải bản mới nhất
git switch -c feat/f01-connector-otx        # 2. tạo nhánh riêng cho issue (đặt tên theo loại/việc)
# ... làm việc, nhờ agent code ...
make test && make lint                      # 3. kiểm tra trước khi lưu
git add -A && git status                    # 4. đánh dấu thay đổi và ĐỌC lại danh sách file
git commit -m "feat(connectors): bat connector OTX"   # 5. lưu kèm mô tả
git push -u origin feat/f01-connector-otx   # 6. gửi lên GitHub, rồi mở Pull Request trên web
```
Sau khi PR được merge:
```bash
git switch main && git pull                 # cập nhật main
git branch -d feat/f01-connector-otx        # xóa nhánh cũ trên máy
```

## Quy ước đặt tên
| Loại | Tiền tố nhánh / commit | Ví dụ |
|---|---|---|
| Tính năng mới | `feat` | `feat/f05-api-tra-cuu` |
| Sửa lỗi | `fix` | `fix/scorer-chia-cho-0` |
| Tài liệu | `docs` | `docs/devlog-w45` |
| Việc lặt vặt, cấu hình | `chore` | `chore/cap-nhat-ruff` |
| Thêm test | `test` | `test/allowlist-ipv6` |

## Khi nhánh của bạn bị cũ so với main
GitHub báo "This branch is out-of-date":
```bash
git switch main && git pull
git switch feat/ten-nhanh
git merge main          # đưa thay đổi mới của main vào nhánh của bạn
```

## Khi gặp xung đột (conflict)
Git sẽ báo file nào xung đột; trong file có đoạn:
```text
<<<<<<< HEAD
phần của bạn
=======
phần từ main
>>>>>>> main
```
1. Mở file, giữ lại nội dung đúng (có thể kết hợp cả hai), xóa 3 dòng đánh dấu.
2. `git add <file>` rồi `git commit`.
3. Không chắc thì hỏi agent: *"Giải thích xung đột trong file X và đề xuất cách gộp, chưa sửa vội."*

## Năm luật vàng
1. Không bao giờ commit thẳng lên `main` (luật bảo vệ nhánh cũng sẽ chặn).
2. Mỗi PR một mục đích, càng nhỏ càng dễ duyệt (dưới khoảng 300 dòng thay đổi).
3. Luôn đọc `git status` trước khi commit, để không lỡ đưa `.env` hay file rác lên.
4. Pull trước khi bắt đầu làm, push trước khi nghỉ.
5. Lỡ commit secret: báo cả nhóm ngay, **đổi key đó** (xóa commit là chưa đủ, vì lịch sử vẫn còn).

## Cứu hộ nhanh
| Tình huống | Lệnh |
|---|---|
| Lỡ sửa linh tinh một file, muốn về như cũ | `git restore <file>` |
| Lỡ `git add` nhầm file | `git restore --staged <file>` |
| Commit nhầm message (chưa push) | `git commit --amend` |
| Xem lịch sử gọn | `git log --oneline --graph -15` |
| Cất tạm thay đổi để chuyển nhánh | `git stash`, sau đó `git stash pop` |

## Học thêm
- **Pull:** tải thay đổi mới từ GitHub về máy và gộp vào nhánh hiện tại.
- **Merge:** gộp lịch sử của hai nhánh làm một.
- **Conflict:** hai người sửa cùng một chỗ, Git không tự quyết được nên hỏi bạn.
- **Staging (`git add`):** "giỏ hàng" chứa những thay đổi sẽ vào commit tiếp theo.
