# Browser tích hợp OpenMausBot — W02 loopback

Ngày kiểm: 11/11/2026, browser tích hợp OpenMausBot, chỉ `127.0.0.1`.

| Scenario | URL cùng run | Quan sát |
|---|---|---|
| `w02-it` | `http://127.0.0.1:64139/tra-cuu` | `evil.example` → `evil[.]example`, TLP:GREEN, score 40, `Synthetic Alpha`, T1566.001; screenshot `browser-found.png`. |
| `w02-it` | cùng URL | `8.8.8.8` → allowlist, 0/100, TLP:CLEAR. |
| `w02-it` | cùng URL | `unknown.example` → “Không tìm thấy không có nghĩa là an toàn”; đổi English giữ đúng cảnh báo và nhãn local synthetic/chưa OpenCTI. |
| `w02-missing-token` | `http://127.0.0.1:54331/tra-cuu` | Hiện “Cần đăng nhập để tra cứu”; browser ghi một GET `/api/ioc` trả 401, không hiện raw server error. |
| `w02-lookup-503` | `http://127.0.0.1:62630/tra-cuu` | Hiện “Tạm thời không thể tra cứu”; browser ghi một GET `/api/ioc` trả 503, không hiện raw server error. |

Nút sao chép được thao tác sau found nhưng browser không cấp quyền clipboard; UI hiện thông báo lỗi an toàn. Vì vậy copy canonical trên browser là `UNVERIFIED`; unit regression về canonical clipboard vẫn PASS.

Browser được đóng. Ba listener trên các port `64139`, `54331`, `62630` đều đã đóng; không còn temp root `w05-local-*`.
