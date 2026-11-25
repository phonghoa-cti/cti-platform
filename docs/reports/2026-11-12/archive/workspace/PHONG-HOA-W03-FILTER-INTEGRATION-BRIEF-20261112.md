# W03 — ghép R1 và kiểm bộ lọc trên browser
ROOT = $WORKSPACE

Một CTI Engineer Sol medium trực tiếp, không worker con/bot khác. Cùng thread024d0127-8ec0-48ac-bd81-cbe0d65ff053 và tree ROOT/cti-w03-read-integration.
Đọc ROOT/leader-w03-rework-acceptance-20261112/ACCEPTANCE.md. R2 ở9579d1657145769718fde96c4918fe5cd4d80f63 đã đạt độc lập; Frontend R1 ở7ff62711f4304aefda9a6fc640d05039fd0cd9af đã đạt53+3kiểm. Không làm lại hoặc sửa source tree Frontend.

1. Xác nhận integration HEAD9579d165 sạch, giữ edits nếu xuất hiện. Cherry-pick **chỉ7ff62711f4304aefda9a6fc640d05039fd0cd9af** vào tree này. Conflict PROGRESS giữ cả hai nội dung. Không cherry-pick lại hai commit frontend cũ. Không merge main/PR/push/deploy.
2. Chứng minh runtime Frontend giống7ff62711, Backend giốngabcd14da, wire tests R2 vẫn nguyên. Chạy focused W03app/http/wire trên final tree một lần (dự kiến53+10), build để phục vụ browser đúng code mới. Nguyên3probe Leader dùng config gốc trỏ integration phảiGREEN, giữhash.
3. Chỉ một browser run w03-it với công cụ OpenMausBot, viewport thật. Trên /lo-hong: mặc định Chỉ KEV checked thấy3CVE/3KEV; bỏ chọn thấy16CVE/3KEV, cả3KEV vẫn ởđầu; trang1→2 đủ16ID không lặp, không bỏ; bật lại thấy3. Kiểm một filter q hoặc technology trong trạng thái unchecked rồi bỏ filter vẫn16 để xác nhận query semantics. Không sửa label đểche hànhvi.
4. Evidence mới ROOT/w03-filter-integration-evidence/: screenshot/text của3→16→3 vàpaging, trace methods/status, trả ID hoặc summary API đểđối chiếu nếu tool hỗ trợ an toàn; không ghiJWT. Source vẫn synthetic và notice version nguyên. SQLite trước/sau W03 chỉ đọc giống nhau; không thêm mutation để kiểm checkbox.
5. Chạy trên SHA cuối, lưu metadata/head/build và cleanup stopped/portclosed/tempremoved. Nếu docs/evidence-only commit sau run thì chỉ ra diff, không tự gọi browser chạy trên SHA chưa tồn tại. Không sửa/xóa42artifact gốc hoặc14artifact R2.
6. Tái dùng các kiểm120HTTP và browser summary/409/503 trước, vì runtime mới chỉ querymapping. Không chạy lại full112/356 hay ba browser faults. Không mở rộng UI/design/API/deps. Nếu gặp lỗi khác, báo repro, không tự đổi scope.
7. Update docs/PROGRESS một đoạn đúng mức bằng chứng. Output ROOT/PHONG-HOA-W03-FILTER-INTEGRATION-RESULT.md, clean finalSHA/base/delta và manifest. Báo R1/R2 đã ghép cùng kết quả mới và giới hạn chưa kiểm.
Mobile/live feed/OpenCTI/Cloudflare/JWKS/lab/production vẫn UNVERIFIED. Không triển khai môi trường thật. Trả kết quả về Leader để nghiệm thu cuối.
