# Leader kiểm nghiên cứu tích hợp và chốt triển khai

Request `2428ed61-6ff7-4719-b401-ca4be09441c5`: hai file khớp hash báo cáo, nghiên cứu `102cef2dbf43423100e522953593de45863e9bea392ff64995343c2bb22eef6a`, brief `17b0024ac139edffe812dd3c99de86d82db840fb7bde963e958362b693c23f57`. Leader đọc toàn bộ và đối chiếu settings/app/auth, dependency lock, UI manifest cùng Git history tại exact refs. Hai tree nguồn sạch.

## Chấp nhận có phần chốt của Leader

Chọn phương án C: harness loopback riêng, JWT ký tổng hợp xác minh thật, SQLite tạm. Cho phép Uvicorn0.54.0 minimal vào venv/lock của tree riêng và factory HTTP test-only có regression bảo vệ production HTTPS. Leader xác nhận Python3.12.13, uvicorn/hypercorn đều chưa có; đây là dependency cần bổ sung cục bộ, không blocker cần người dùng thao tác.

Sửa điểm quan trọng trong brief: Backend02b0efe chưa có portal/web; bốn commit UI cuối không bao gồm previewbe364bd/clipboard9b10223. Thay bằng nhập nguyên snapshot portal/web từa791a3f vào tree mới, không merge/cherry-pick, không sửa tree nguồn. Git treehash UI `9f9ae6d46030dd5ab45f3cbf283f0df90f2035db`. Các quyết định và acceptance bổ sung nằm ở `PHONG-HOA-LOCAL-INTEGRATION-LEADER-PLAN.md`; không triển khai theo bốn commit cũ.

Đã đối chiếu nguồn chính thức [FastAPI](https://fastapi.tiangolo.com/deployment/manually/), [PyPI Uvicorn0.54.0](https://pypi.org/project/uvicorn/0.54.0/), [MDN Origin](https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Origin) và [Cloudflare JWT](https://developers.cloudflare.com/cloudflare-one/access-controls/applications/http-apps/authorization-cookie/validating-json/). Chọn phương án là quyết định kỹ thuật của Leader; nguồn chỉ hỗ trợ cơ chế, chưa chứng minh harness chạy được.

**ACCEPTED nghiên cứu với kế hoạch bổ sung**, không phải accepted implementation. Không chạy test sản phẩm trong lượt đọc nghiên cứu. Một lệnh đọc đường đoán portal_api/demo.py không tìm thấy; dữ liệu runtime và module auth/settings được kiểm trực tiếp, không suy lỗi đường dẫn này là lỗi sản phẩm.

Đã xem threads một lần: Engineer idle, không Leader khác đang xử lý. Lịch dự phòng kiểm lúc02:13:35 giờ Việt Nam: enabled=true, lần tiếp02:26:14; lượt gần nhất01:56 ra NOTHING NEW. Giữ lịch; dự án active và phục hồi việc bỏ dở vẫn UNVERIFIED. Nhiệm vụ tiếp là W05-LOCAL-INTEGRATION-IMPLEMENT trên tree riêng do Engineer sở hữu; receipt thực ghi sau khi giao.

## Receipt triển khai

Engineer đã nhận request `8598e68d-2407-4dbb-885c-31c8cc604680`, thread `dca33bbe-a84c-4f7b-bc31-bb9525c40e78`, outcome queued. Đã đọc lại sổ: research accepted với Leader plan, implementation dispatched. Guard YIELD exit0 và hash ledger trước/sau giống nhau. Không gọi queued là running, không polling; chờ callback có kết quả thật để nghiệm thu.
