# W04 Backend QA độc lập — kết quả

Ngày kiểm: 11/11/2026. Kết luận tổng: **FAIL — chưa đủ điều kiện nghiệm thu Backend hoặc nối Frontend**.

Target chỉ đọc: `cti-w04-assets-local`, branch `feat/w04-assets-local-20261111`, base
`aeff542a20ecc6fe436a0884801fdd69ab0435f6`, HEAD
`bfd3272d968313ed8b6d9c46ef07c730b49c2ebb`. Tree sạch trước và sau QA. QA không sửa hoặc
commit target; chỉ ghi báo cáo và `w04-assets-qa-evidence/` ở root.

## Finding cần sửa

### F1 — HIGH — dữ liệu domain hỏng trong DB có thể mở allowlist quá rộng

- Vị trí: `portal_api/assets.py:150` đọc snapshot nhưng không kiểm lại invariant từng row;
  `portal_api/assets.py:65` dùng trực tiếp giá trị đó để match hậu tố và `portal_api/assets.py:86`
  biến match thành allowlist. Trong khi đường ghi hợp lệ từ API kiểm domain tại
  `portal_api/assets.py:279`.
- Tái hiện: chèn synthetic row `type=domain, canonical_value=com` trực tiếp vào DB demo, rồi tra
  `attacker.com`.
- Mong đợi: snapshot fail-closed, HTTP `503 lookup_unavailable`; không gọi lookup adapter và không
  trả allowlisted.
- Thực tế: HTTP `200`, state `allowlisted`, score `0`, `asset_match.assets=["com"]`; adapter không
  được gọi. Bằng chứng: `06-targeted-probes-utf8-final.txt`, probe
  `malformed_stored_domain`.
- Sửa nhỏ nhất: khi dựng snapshot, kiểm type/value/canonical bằng cùng invariant với đường ghi;
  bất kỳ row sai nào phải làm hỏng toàn snapshot. Thêm hồi quy cho single-label, CIDR hỏng và row
  vượt giới hạn; không bỏ qua row và không trả partial.

### F2 — HIGH — mutation đã commit nhưng API trả 422

- Vị trí: `portal_api/assets.py:300` chỉ kiểm actor không rỗng, không áp giới hạn; create commit tại
  `portal_api/assets.py:166`; sau commit, `portal_api/app.py:323` mới dựng `AssetView`, trong khi
  `portal_api/schemas.py:148` giới hạn `created_by` 512. `portal_api/app.py:326` bắt lỗi response
  validation và đổi thành `invalid_asset`.
- Tái hiện: principal đã xác minh có subject dài 513 ký tự và role `it`, POST một domain hợp lệ.
- Mong đợi: từ chối trước transaction hoặc trả success đúng với mutation đã commit.
- Thực tế: HTTP `422 invalid_asset`, nhưng DB có `1` asset và `1` audit row. Client có thể retry vì
  tưởng request không ghi, tạo unknown outcome. Bằng chứng: `06-targeted-probes-utf8-final.txt`,
  probe `long_verified_subject`.
- Sửa nhỏ nhất: ràng buộc subject/actor trước khi bắt đầu transaction (đồng bộ schema 512), và bảo
  đảm mọi DTO response được dựng/kiểm trước commit hoặc từ dữ liệu đã chắc chắn thỏa schema.

### F3 — MEDIUM — giới hạn tên asset 253 chưa được áp dụng nhất quán

- Vị trí: response cho asset name cho phép 253 tại `portal_api/schemas.py:28` và
  `portal_api/schemas.py:73`, nhưng `portal_api/ioc_lookup.py:327` gọi helper chung giới hạn 128 tại
  `portal_api/ioc_lookup.py:334`.
- Tái hiện: lookup record hợp lệ, visible `AssetFact.name` dài 129.
- Mong đợi: HTTP `200 found`; tên asset có bound riêng tối đa 253, không nới source/related.
- Thực tế: HTTP `503 lookup_unavailable`. Bằng chứng: `06-targeted-probes-utf8-final.txt`, probe
  `asset_name_129`.
- Sửa nhỏ nhất: validator riêng cho `AssetFact.name` với 1..253; giữ source/related ở 128 và thêm
  test biên 128/129/253/254.

### F4 — MEDIUM — lỗi audit integrity bị báo nhầm là duplicate asset

- Vị trí: `portal_api/assets.py:178` và `portal_api/assets.py:220` biến mọi
  `sqlite3.IntegrityError` thành `AssetExists`; API sau đó trả `409 asset_exists` tại
  `portal_api/app.py:260`.
- Tái hiện: trigger synthetic làm INSERT audit abort trong create.
- Mong đợi: rollback toàn bộ và `503 assets_unavailable`; `asset_exists` chỉ dành cho unique active
  canonical.
- Thực tế: rollback đúng (`0` asset, `0` audit) nhưng HTTP `409 asset_exists`. Bằng chứng:
  `06-targeted-probes-utf8-final.txt`, probe `audit_trigger_rollback`.
- Sửa nhỏ nhất: chỉ map constraint unique/index `assets_active_value` sang `AssetExists`; các
  integrity/storage failure khác sang `AssetsUnavailable`, vẫn giữ rollback.

## PASS / FAIL / UNVERIFIED theo nhóm

| Nhóm | Kết luận | Bằng chứng |
|---|---|---|
| Auth, role giả, Origin, body cap, strict ID/query/header | **PASS trong phạm vi targeted** | Test assets 26/26; probe wrong Origin trả 403 trước body/store, private IP trả 422 trước snapshot, số call store bằng 0. Source ordering tại `portal_api/app.py:239`, `:313`, `:333`, `:364`. |
| Atomic mutation, audit, version, concurrent writer | **FAIL** | Concurrent update đúng: một success v2, một conflict, đúng một audit update. Audit failure rollback đúng nhưng sai error F4. Subject dài gây commit rồi trả lỗi F2. |
| Snapshot, matching, allowlist | **FAIL** | Domain boundary, URL path match nhưng không allowlist, IPv4/IPv6, overflow 1001 fail-closed đều đạt; malformed stored domain làm allowlist rộng sai theo F1. |
| W02 TLP/score và bound asset | **FAIL** | 26 tests phủ hidden record vẫn `not_found`, local asset giữ lại, score asset 1.3 và default allowlist sau xóa; bound 129 sai theo F3. |
| W02 khi opt-in tắt, toàn bộ regression portal | **UNVERIFIED trong lượt QA này** | Theo ranh giới brief, không chạy `test_w02_ioc_api.py` riêng và không chạy full 197; chỉ review wiring `asset_store=None`. Không nâng bằng chứng lịch sử thành run mới trên QA. |
| UI/browser/listener, lab, Cloudflare/JWKS/HTTPS thật, OpenCTI, feed/LLM, production | **UNVERIFIED / ngoài phạm vi** | Không chạy theo brief. |

## Lệnh và bằng chứng thực thi

Interpreter:
`cti-w02-lookup-api/.venv/Scripts/python.exe`; Python/module source thực tế nằm trong
`01-runtime-source.txt`. CWD là target; `PYTHONPATH` là target root, `core`, `extractor`; dùng `-B`.

1. Lượt pytest bắt buộc, chạy đúng một lần:
   `python.exe -B -m pytest portal_api/tests/test_assets_api.py -p no:cacheprovider -o addopts= -q`
   → exit `0`, **26 passed in 1.14s**; `02-assets-api-pytest.txt`.
2. Probe đầu `03-targeted-probes.txt` exit `1` do lỗi SQL trong chính harness (8 values/7 columns),
   không dùng làm finding. Probe `04-targeted-probes-final.txt` exit `1` do stdout Windows cp1252
   không encode được tiếng Việt, không dùng làm finding.
3. Lượt probe hoàn chỉnh cuối chạy cùng interpreter/PYTHONPATH với `PYTHONUTF8=1`, exit `0`, JSON
   đầy đủ: 7 probe; 3 đáp ứng expected (concurrency, Origin/private-IP precedence, overflow) và 4
   tái hiện finding F1–F4. Chỉ `06-targeted-probes-utf8-final.txt` được dùng làm bằng chứng finding.

`05-targeted-probes-final.txt` cũng exit 0 sau khi sửa encoding nhưng có tập probe nhỏ hơn; kết luận
cuối chỉ dựa trên run `06` đầy đủ. Không chạy full suite, browser, network hoặc lab. Probe script và
DB synthetic được giữ nguyên trong evidence.

## Trạng thái tích hợp

Không nên nối Frontend vào Backend này như một đầu vào đã nghiệm thu. Fixture/hợp đồng có thể tiếp
tục dùng để chuẩn bị parser độc lập, nhưng acceptance Backend cần sửa F1 và F2 trước; F3/F4 cũng cần
hồi quy và chạy lại targeted assets cùng các probe liên quan. Không tự merge/deploy.

Hash SHA-256 của báo cáo và evidence nằm trong `w04-assets-qa-evidence/08-sha256.txt`; final Git state
nằm trong `07-final-git-state.txt`.
