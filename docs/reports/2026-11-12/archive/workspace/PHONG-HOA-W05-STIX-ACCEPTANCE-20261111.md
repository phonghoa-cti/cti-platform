# W05-STIX — nghiệm thu cục bộ sau R1/R2, 11/11/2026

**ACCEPTED local** request `9b18b466-b161-4614-813a-98675731cf5f`, HEAD `ed829a0344b2d3d4392fae933e41a9c44fdcd853`, branch `feat/w05-stix-offline-20261111`.
Tree: `$WORKSPACE\cti-w05-stix-offline`. Rework từ dbec016: 5 file, +133/-7. Không merge/push/deploy.

## Quyết định và kiểm chứng
- Đọc toàn bộ diff sửa: R1 type guard TLP trước set lookup, chuyển UTC overflow thành lỗi nghiệp vụ; R2 bảo vệ lexical và resolved input/sidecar. Alias tĩnh hợp lệ vẫn đọc được khi output là bundle riêng.
- Leader chạy lại probe nguyên trạng: **14 passed in 1.06s, exit 0** trên HEAD hiện tại.
  Lệnh: `.venv/Scripts/python.exe -X utf8 -B -m pytest -o addopts='' -q -p no:cacheprovider ../w05-stix-evidence/leader-review/test_stix_review.py`.
  Log mới: `w05-stix-evidence/leader-review/probe-green.log`.
  Probe SHA256 `8ED38838B86F546826808DC820A7A9EF795526AE94B5E9277B70F3EFEAD80BDA`; RED log cũ hash không đổi.
- Đọc regression repo thêm và raw evidence: RED 20 fail/8 pass; GREEN 28 pass; toàn hai file STIX **77 pass**, exit 0, gồm validator/race/CLI. Đây là log Backend đã đọc kiểm, không gọi là Leader chạy lại 77.
- Manifest tổng **16/16** và manifest raw rework **31/31** hash khớp. Raw command/stdout/stderr/exit có thật. Ruff check/format và diff-check exit 0; stderr diff-check chỉ cảnh báo line ending trước commit, không phải lỗi kiểm.
- Leader kiểm git diff --check exit0; implementation clean đúng SHA. Source integration d3cbaa60740cb99d4d46a6cb093bc44aba8a20d2 clean. Scope không đổi store/core/API/UI/gateway/dependencies/locks.
- Không chạy lại full500; đó là kết quả trước rework do Backend báo cáo, không bằng chứng mới. Không lặp UI/build/browser vì UI không đổi.

R1 và R2 trong PHONG-HOA-W05-STIX-CODE-REVIEW-20261111.md được đóng. Không phát hiện vấn đề mới trong diff sửa tập trung.
Xuất STIX cục bộ đã đủ tiêu chí lát cắt: approved final audit, selection, cấu trúc/ID/provenance, không ghi đè, config/path boundary, validator offline.

## Giới hạn và việc tiếp
Chưa xác minh OpenCTI import/workbench, danh tính tổ chức thật, Cloudflare/JWKS/HTTPS thật, network share/crash/power-loss/hostile directory mutation, lab hay production. Không coi bundle STIX chuẩn là đã ghi vào OpenCTI.
Dự án vẫn active. Spec X01 yêu cầu văn bản → draft → W05; spec W05 yêu cầu duyệt → Report/OpenCTI. Phần lab tiếp tục để sau. Việc kế nhỏ nhất: đối chiếu và lập brief kiểm cùng một luồng **văn bản tổng hợp qua extractor C1 thật → SQLite → UI/API duyệt → CLI export STIX**, tái dùng harness đã có. Hiện chưa có bằng chứng ghép toàn chuỗi này; không tạo thêm importer/outbox/HTTP export trước khi cần.
Tìm lịch sử riêng “STIX end-to-end” chưa thấy kết quả; đã đọc W05/X01/PROGRESS và kế hoạch phân công, không lặp nghiên cứu STIX đã chốt.
Đã xem các cuộc một lần: không có Leader khác chạy, Backend idle. Lịch dự phòng còn enabled chu kỳ30 phút; lượt06:56 hoàn tất NOTHING NEW, không suy diễn thành kiểm chứng phục hồi bỏ dở. Giữ lịch, không đóng dự án.
