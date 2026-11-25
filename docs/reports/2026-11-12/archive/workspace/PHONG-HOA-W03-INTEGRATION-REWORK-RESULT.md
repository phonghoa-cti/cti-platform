# W03-INTEGRATION rework R2 — kết quả

## Trạng thái

**R2 PASS độc lập; toàn luồng vẫn CHƯA ĐẠT vì R1 checkbox KEV đang chờ frontend review và ghép.**

- Base: `93962d9ec771c49855c213e6332be0632e33debd`.
- HEAD sạch: `9579d1657145769718fde96c4918fe5cd4d80f63`.
- Commit: `test: harden W03 integration evidence`.
- Delta: 14 file, `+189/-17`; chỉ test/fixture/provenance, matrix, README và PROGRESS trong allowlist.
- Không sửa component/provider sản phẩm, không cherry-pick hoặc chờ R1, không push/PR/merge/deploy/lab/feed/secret.
- 42 artifact R1 cũ vẫn nguyên vẹn: manifest `9b17ed1f...`, 42/42 hash khớp.

## Wire portable và preflight

Fixture API thật đã capture được lưu ở `portal/web/tests/fixtures/w03-integration/`, kèm nguồn, lệnh tái tạo và
SHA-256. Khi không đặt `W03_WIRE_DIR`, test tự resolve theo vị trí file test; override vẫn dùng được để kiểm capture
mới.

| Trường hợp | Kết quả quan sát |
|---|---|
| Không đặt `W03_WIRE_DIR` | exit 0, **10/10** PASS |
| Override tới `w03-integration-rework-evidence/http-final/wire` | exit 0, **10/10** PASS |
| Override thiếu `summary.json` | exit 1, **0 test chạy**, báo `fixture missing or unreadable` |
| Override có `detail.json` hỏng | exit 1, **0 test chạy**, báo `fixture is not valid JSON` |

Preflight nạp và parse đủ chín fixture trước khi tạo HTTP provider. Vì vậy lỗi đọc fixture không còn bị catch của
adapter đổi thành `unavailable` rồi làm hai test 503 false PASS.

Near-cap `1,027,338` byte được chạy qua `createCvesHttpProvider.list` với cả có và không `Content-Length` hợp lệ.
Hai trường hợp body vượt 1 MiB đều bị adapter từ chối. Tổng wire test tăng từ 7 lên 10.

## W04 create/delete và SQL cùng DB

Lệnh tái chạy:

```powershell
..\cti-w03-read-backend\.venv\Scripts\python.exe -X utf8 -B -m tools.local_integration.tests.run_w03_matrix --output ..\w03-integration-rework-evidence\http-matrix.json --evidence-dir ..\w03-integration-rework-evidence\http-final
```

Kết quả: exit 0, **120/120** kiểm, 8 scenario.

- PUT đổi FortiOS thành NoMatch: matches 16→1, cursor trước mutation trả 409.
- POST tạo FortiOS mới: HTTP 201, matches 1→16; `technology_assets` 2→3, technology audit 3→4.
- DELETE đúng record vừa tạo: HTTP 204, matches 16→1; cursor đang phân trang trả 409, audit 4→5.
- Mỗi GET sau mutation được `assert_get_immutable` chụp SQL trước/sau; schema SHA-256 và `user_version=2` giữ
  nguyên. Chỉ các W04 mutation có chủ ý làm đổi rows/audit.
- Trace thật ghi đúng `PUT /api/assets/technologies/1 200`, `POST /api/assets/technologies 201`,
  `DELETE /api/assets/technologies/3 204` và các CVE GET `200/409`; không có W03 mutation.

## Kiểm tra bổ sung

| Kiểm | Kết quả |
|---|---|
| TypeScript | exit 0 |
| ESLint file wire | exit 0 |
| Ruff check | exit 0 |
| Ruff format check | exit 0 |
| `git diff --check` | exit 0 |

Không lặp browser, full Python 112, frontend 356 hoặc build vì rework không đổi product code và brief yêu cầu giữ
bằng chứng cũ. Browser/mobile/live feed/OpenCTI/Cloudflare/lab/production vẫn giữ nguyên mức **UNVERIFIED**.

## Giải thích cho người mới

Wire fixture là JSON được lưu lại đúng từ API để frontend kiểm tra cấu trúc dữ liệu mà không cần Internet.
Preflight là bước kiểm đầu vào trước test; nếu file thiếu hoặc hỏng, suite dừng ngay thay vì biến lỗi đó thành một
kết quả tưởng như đúng. Cursor 409 báo danh sách đã đổi giữa hai trang, nên client phải tải lại từ đầu. SQL snapshot
chứng minh các request GET chỉ đọc không âm thầm sửa database.

## Hoàn tác

Dùng `git revert 9579d1657145769718fde96c4918fe5cd4d80f63` để hoàn tác R2 mà không phá lịch sử.
