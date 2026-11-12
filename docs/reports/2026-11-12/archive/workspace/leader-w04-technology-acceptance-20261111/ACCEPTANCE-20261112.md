# Nghiệm thu đầu vào W04 Technology — 12/11/2026

**PASS cục bộ hai đầu vào, đóng B1/F1–F3. Chưa nghiệm thu tích hợp hoặc browser Technology.**

## Ref và phạm vi

| Phần | Request nghiệm thu | HEAD sạch | Delta rework |
|---|---|---|---|
| Backend | 4199b661-2edf-494e-81c5-b7a7e8db1c5e | f4c19d44a33fe588046e0e974af9c18cbf8a1a12 | 2 file +75/-4 so b32fbfe |
| Frontend | 13d5e800-cb40-445d-a3e3-046fcc58e1d9 | cfb612f05f6ae57952362580e35ad59d2aff0a3f | 6 file +221/-20 so2419b29 |

Leader đọc Git/diff mới, đối chiếu báo cáo/raw log và kiểm probe/fixture nguyên bản bằng SHA256. Hai nhánh đều bắt đầu từ accepted8a767314; Backend có b32fbfe→f4c19d4, Frontend có2419b29→cfb612f. Không sửa source trong nghiệm thu.

## Leader chạy mới

- Backend probe nguyên bản: **8/8 pass, exit0**. Ba timestamp trái wire đều503; PUT giữ note rỗng/version1/audit1, không còn commit. Hai dạng Z chuẩn có/không phần thập phân vẫn đọc được.
- Frontend probe nguyên bản: **4/4 pass, exit0**. Danh sách1000 record từ Backend thật (1,705,904byte) đọc được với/không Content-Length; committed notice giữ qua GET lỗi lần2 rồi GET thành công; unknown lock vẫn giữ khi đổi tab và GET đối soát lỗi.
- Test lifecycle mới chọn theo rủi ro: **4/4 pass,20 skipped,exit0**. Create/update/delete giữ committed notice qua lỗi GET; mutation pending qua tab không được GET sớm mở khóa, unknown cần GET thành công sau đó.
- Raw: backend-green-leader.log, frontend-green-leader.log, frontend-lifecycle-green-leader.log trong thư mục này.

Lệnh Backend cwd cti-w04-technology-backend, interpreter cti-w02-lookup-api/.venv/Scripts/python.exe; PYTHONPATH target + target/core + target/extractor:
`python -m pytest ../leader-w04-technology-acceptance-20261111/backend_probes.py -o addopts='' -q -s --tb=short`.
Lệnh Frontend cwd thư mục evidence này:
`node ../cti-w04-technology-frontend/portal/web/node_modules/vitest/vitest.mjs run --config vitest.config.mjs --reporter=verbose`.
Lifecycle cwd cti-w04-technology-frontend/portal/web:
`node node_modules/vitest/vitest.mjs run tests/technology-panel.test.tsx -t 'keeps committed|keeps a pending' --reporter=verbose`.

## Review và evidence kế thừa

- B1: regex ASCII đúng wire trước datetime calendar validation, dùng chung trước trả/ghi; worker bổ sung GET/PUT/DELETE trên cả created_at/updated_at.
- F1: GET list cap hữu hạn18,700,011byte bao phủ1000 DTO và escape Unicode; mutation/error vẫn1MiB. Đã đọc test tối đa Unicode, UTF-16 escape, cap+1, stream khôngheader và count1001; không bỏ timeout/cancel/parser.
- F2/F3: mode tải giữ committed/unknown, component Technology tồn tại qua tab nhưng chỉ render khi active, pending khóa mọi mutation; đổi provider vẫn reset/invalidates context. Test stale/unmount trước còn trong suite.
- Worker Backend69focused+8probe=77 đạt, Ruff/format/diff0; raw log SHA256728ebcb52a977e605150154d594fe619f26816b1c144075634f78643bf783905 đã khớp.
- Worker Frontend120focused, typecheck/lint/build/diff0, build9/9: đã đọc raw build/focused và báo cáo. Không gọi đây là Leader chạy lại120/77.
- Probe SHA Backend3a022eb79f3ca1b1c08bc62ed51d09cb89217bca5629471101f0535d13cf5dcf; Frontend218118d0f58a523e25e60eba1734da7ed9a1e008ddf93d196cbd31cd9be19a45; fixture1000b0f87acdac467348c5dd2f66447a04923914dde7daeba08752e499dcd2198b78: không đổi.

## Quyết định tiếp

Giải phụ thuộc W04-TECHNOLOGY-INTEGRATION. Dùng brief PHONG-HOA-W04-TECHNOLOGY-INTEGRATION-BRIEF-20261112.md; một Engineer Sol medium, tree mới, chỉ ghép các SHA đã đạt và bổ sung wiring/harness. Không lặp nghiệm thu domain/CIDR cũ.

Còn UNVERIFIED: API↔gateway↔UI Technology cùng DB, browser Technology/mobile, Cloudflare/JWKS/HTTPS thật, OpenCTI/W03 matching, lab/production. Dự án còn active; hai lịch nối việc vẫn bật đã đọc lúc00:07, không có monitor mục tiêu đã xong cần dừng.
