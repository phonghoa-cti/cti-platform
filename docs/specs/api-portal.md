# Hợp đồng API của portal (`portal-api`, FastAPI)

**Vì sao cần file này:** frontend và backend do hai người (hai agent) làm song song. Chốt trước hình dạng dữ liệu thì
frontend dùng dữ liệu giả theo đúng hợp đồng, backend làm thật, ghép lại là chạy. Đổi hợp đồng phải sửa file này trước (qua PR).

Quy ước: tiền tố `/api`; JSON; thời gian dạng ISO 8601 có múi giờ; lỗi trả `{"error": {"code": "...", "message": "câu tiếng Việt"}}`.

## 1. Xác thực
- Sau Cloudflare Access: backend đọc email từ header `Cf-Access-Authenticated-User-Email`, tra vai trò trong bảng `users` (SQLite).
- Gọi từ máy (firewall, script): header `X-API-Key`; key gắn với một vai trò.
- Phát triển trên máy: `DEV_USER_EMAIL=analyst@dev.local` (chỉ bật khi `ENV=dev`).
- Email không có trong bảng → 403 "Tài khoản chưa được cấp quyền".

## 2. Ma trận quyền
| Endpoint | Lãnh đạo | IT | Analyst | Admin |
|---|---|---|---|---|
| GET /me, /overview | ✓ | ✓ | ✓ | ✓ |
| GET /ioc, POST /ioc/batch | — | ✓ (chỉ TLP CLEAR/GREEN) | ✓ | ✓ |
| POST /ioc/false-positive | — | — | ✓ | ✓ |
| GET /cves | ✓ (tóm tắt) | ✓ | ✓ | ✓ |
| PATCH /cves/{id}/status | — | ✓ | ✓ | ✓ |
| /assets (mọi phương thức) | — | ✓ | ✓ | ✓ |
| POST /actions (đề xuất) | — | ✓ | ✓ | ✓ |
| GET /actions, POST /actions/{id}/decision | — | — | ✓ | ✓ |
| /drafts (mọi phương thức) | — | — | ✓ | ✓ |
| GET /blocklist.txt | API key loại "export" | | | |

## 3. Endpoint

### GET /api/me
```json
{"email": "an@congty.vn", "role": "it", "language": "vi"}
```

### GET /api/overview?days=30
```json
{
  "threat_level": {"level": "medium", "reason": "2 IOC liên quan tài sản trong 7 ngày"},
  "kpis": {
    "new_iocs_24h": {"value": 1248, "change_pct": 12.0},
    "asset_related_iocs_7d": {"value": 2, "change_pct": null},
    "kev_cves_affecting": {"value": 1, "change_pct": null},
    "wazuh_alerts_7d": {"value": 3, "change_pct": -25.0}
  },
  "attention": [
    {"severity": "high", "kind": "cve", "title": "CVE-xxxx-yyyy ảnh hưởng FortiOS", "link": "/lo-hong?cve=CVE-xxxx-yyyy", "id": "att-1"}
  ],
  "trend": [{"date": "2026-11-01", "ipv4": 120, "domain": 80, "url": 200, "hash": 40}],
  "top_techniques": [{"id": "T1566.001", "name_vi": "Lừa đảo kèm tệp đính kèm", "count": 14}],
  "top_threats": [{"name": "Tên họ mã độc", "type": "malware", "count": 9}],
  "generated_at": "2026-11-10T07:00:00+07:00"
}
```

### GET /api/ioc?value=hxxp://evil[.]com
```json
{
  "input": "hxxp://evil[.]com",
  "ioc": {"type": "url", "value": "http://evil.com/", "display": "hxxp://evil[.]com/"},
  "found": true,
  "allowlisted": false,
  "asset_match": {"matched": false, "assets": []},
  "score": {"value": 78, "level": "high", "reason": "Nguồn tin cậy 0.80 × ... = 78 điểm", "parts": {"reliability": 0.8, "confirmation": 0.88, "freshness": 0.96, "asset": 1.0}},
  "recommendation": "block",
  "sources": [{"name": "AlienVault OTX", "first_seen": "2026-10-20T08:00:00+07:00", "link": "https://..."}],
  "related": {"techniques": ["T1566.001"], "malware": [], "actors": []},
  "enrichment": {"country": "NL", "asn": "AS12345", "vt_detections": "12/90"},
  "tlp": "TLP:GREEN",
  "opencti_url": "http://<host>:8080/dashboard/observations/indicators/<id>"
}
```
Lỗi: 422 `invalid_ioc` (không nhận diện được), 422 `private_ip`, 404 không bao giờ dùng (không tìm thấy vẫn trả 200 với `found: false`).

### POST /api/ioc/batch
Body `{"values": ["...", "..."]}` (tối đa 50) → `{"results": [<giống GET /ioc nhưng bỏ enrichment>]}`.

### POST /api/ioc/false-positive
Body `{"value": "...", "note": "Là IP của đối tác"}` → 204. Giảm độ tin cậy nguồn đã báo, ghi nhật ký.

### GET /api/cves?kev=true&status=open&asset=<id>
```json
{"items": [{"id": "CVE-xxxx-yyyy", "title": "...", "kev": true, "kev_due": "2026-12-05", "epss": 0.94, "cvss": 9.8,
            "assets": [{"id": 3, "name": "Fortinet FortiOS 7.2"}], "status": "open", "priority": 1}],
 "summary": {"open": 3, "overdue": 1}}
```
### PATCH /api/cves/{id}/status
Body `{"status": "patching|patched|not_affected|open", "note": "..."}` → 200 item mới.

### /api/assets
- GET `?type=domain|ip_range|technology|keyword` → `{"items": [{"id": 1, "type": "domain", "value": "congty.vn", "note": "", "created_by": "...", "created_at": "..."}]}`
- POST `{"type": "technology", "vendor": "Fortinet", "product": "FortiOS", "version": "7.2"}` → 201
- PUT `/api/assets/{id}`, DELETE `/api/assets/{id}` → 200/204
- POST `/api/assets/import` (CSV) → `{"created": 12, "errors": [{"line": 5, "message": "CIDR không hợp lệ"}]}`

### Hành động chờ duyệt
- POST `/api/actions` `{"kind": "block", "target": "evil.com", "reason": "..."}` → 201 `{"id": 7, "status": "pending"}`
- GET `/api/actions?status=pending`
- POST `/api/actions/{id}/decision` `{"decision": "approve|reject", "note": "..."}` → 200. Người đề xuất không được tự duyệt (403 `self_approval`).

### Bản nháp AI
- GET `/api/drafts?status=pending` · GET `/api/drafts/{id}` → `{"id", "source", "language", "tlp", "text", "items": [{"kind": "ioc|ttp|malware|actor", "type", "value", "span": [start, end], "keep": true, "warning": null}], "injection_warning": false, "model", "cost_tokens"}`
- POST `/api/drafts/{id}/approve` `{"items": [...đã chỉnh...], "tlp": "TLP:GREEN"}` → `{"opencti_report_id": "..."}`
- POST `/api/drafts/{id}/reject` `{"note": "..."}`

### GET /api/blocklist.txt?type=ipv4|domain|url&min_score=60
Văn bản thuần, mỗi dòng một giá trị (không defang), đã loại allowlist. Header `X-Generated-At`.

### GET /api/health
`{"status": "ok", "opencti": "ok", "db": "ok"}` — dùng cho Docker healthcheck.

## 4. Dữ liệu riêng của portal (SQLite)
`users(email, role, language)`, `api_keys(id, hash, role, name, created_at, revoked)`, `assets(...)`,
`cve_status(cve_id, status, note, updated_by, updated_at)`, `actions(...)`, `drafts(...)`,
`audit_log(id, at, actor, action, target, before, after)`, `cache(key, value, expires_at)`.
API key chỉ lưu **mã băm** (hash), không lưu bản rõ.
