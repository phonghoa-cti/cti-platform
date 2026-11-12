# Nghiên cứu khởi động Phong Hỏa

**Câu hỏi quyết định.** Demo đầu tận dụng OpenCTI thế nào, nạp dữ liệu gì trước, và AI extractor phải được chứng minh bằng gì? Kiểm tra ngày **10/11/2026**; chỉ đọc nguồn công khai/PR, không chạy lab hay test.

## Hiện trạng đã quan sát

`main` tại `3ff7daf93469dd13692fd1f7aec83a323e2ebb43` chủ yếu là khung. PR #1 (head `8d9d7df…`) có core/spec/thiết kế; PR #46 (head `36259c…`) kế thừa #1 và thêm extractor (`grounding`, `injection`, `evaluate`, X01/dataset). Mô tả PR tự khai báo 61 test, **chưa được chạy lại và chưa là bằng chứng lab**. Xem [PR #46](https://github.com/phonghoa-cti/cti-platform/pull/46); đây không phải kết luận có thể merge.

## Nguồn gốc và khả năng kế thừa

| Nguồn đã kiểm tra | Đã có gì | Dùng lại / điều chỉnh | Giới hạn cần giữ |
|---|---|---|---|
| [OpenCTI connectors](https://github.com/OpenCTI-Platform/connectors) (`master` `593c25a`, Apache-2.0) | Kho connector chính thức; MITRE và ImportFileStix hiện diện. | Kế thừa image/cấu hình mẫu, không chép/sáng tác connector từ đầu. | Cần chốt tương thích với version OpenCTI thực tế; Apache-2.0 của kho không thay thế điều khoản dữ liệu nguồn. |
| [MITRE connector README](https://github.com/OpenCTI-Platform/connectors/tree/master/external-import/mitre) | Nhập Enterprise/Mobile/ICS ATT&CK và CAPEC, STIX 2.1; yêu cầu OpenCTI >=6 và Internet tới GitHub; import đầu có thể mất vài phút. | **Ưu tiên bật đầu tiên** để có danh mục kỹ thuật, nhóm, malware và quan hệ cho tra cứu. | Không phải feed IOC mới; không suy ra dung lượng/RAM hay thời gian lab từ tài liệu. |
| [ImportFileStix README](https://github.com/OpenCTI-Platform/connectors/tree/master/internal-import-file/import-file-stix) | Nạp STIX 2.1 JSON (và nâng STIX 1.2 XML), có `CONNECTOR_VALIDATE_BEFORE_IMPORT=true`, import theo Report/Case. | Dùng bundle mẫu có nguồn gốc cho demo khép kín. | Validation chỉ kiểm tra bundle, không thay duyệt nghiệp vụ và tài liệu không chứng minh quy trình duyệt bắt buộc. |
| [STIX 2.1 OASIS](https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1-os.html) (OASIS Standard, 10/06/2021) | Chuẩn trao đổi CTI có cấu trúc, machine-readable. | Chốt schema/ID/evidence của extractor và mẫu nạp theo STIX, không tạo định dạng riêng. | Chuẩn là hợp đồng dữ liệu, không là bộ dữ liệu hay bộ đo chất lượng.
| [Điều khoản MITRE ATT&CK](https://attack.mitre.org/resources/terms-of-use/) (2026) | Cho phép dùng nghiên cứu, phát triển, thương mại, miễn phí bản quyền nếu giữ copyright/license. | Lưu nguyên notice khi sao chép/phân phối dữ liệu ATT&CK; ghi đúng tên MITRE ATT&CK lần đầu. | ATT&CK không bao phủ mọi hành vi; không dùng như bằng chứng “an toàn/đủ phòng thủ”. |
| [SoK: Automated TTP Extraction](https://www.usenix.org/conference/usenixsecurity25/presentation/buechel) (USENIX Security 2025) | Tổng hợp >40 công trình; NLP truyền thống có thể hơn embedding/generative trong bối cảnh **TTP** thực tế; thiếu dataset/ontology thống nhất. | So sánh các cách trích TTP trên cùng nhãn/evidence; đặt baseline trước model/RAG. | Không suy ra regex trích IOC tốt hơn LLM, hay chuyển chỉ số sang tập song ngữ Phong Hỏa. |
| [OpenCTI MCP qua XTM One](https://docs.opencti.io/latest/deployment/mcp-server/) (cập nhật 05/07/2026) | MCP Community đọc/tạo/sửa/**xóa** knowledge theo quyền user; cần XTM One, đăng ký OpenCTI, tài khoản tương ứng và API key cá nhân. | Đối chiếu A01 trước khi tự xây; nếu thử thì read-only/ít quyền. | Không quản lý connector/ingestion; thay đổi đi thẳng graph. Chưa có lab/XTM One để xác minh. |
| [FIRST TLP 2.0](https://www.first.org/tlp/) (hiệu lực từ 08/2022) | TLP là ranh giới chia sẻ: GREEN chỉ trong cộng đồng, CLEAR mới không giới hạn; nguồn có thể đặt hạn chế bổ sung. TLP không thay thế license/quy tắc xử lý dữ liệu. | Demo và cloud-LLM chỉ dùng dữ liệu tổng hợp hoặc TLP:CLEAR có quyền sử dụng/provenance kiểm tra được. | Không suy ra “TLP:CLEAR = được gửi cho mọi dịch vụ”; còn điều khoản nguồn, riêng tư và điều khoản nhà cung cấp cần kiểm tra. |

## Kết luận ba quyết định

1. **Demo đầu tiên (kiểm chứng nội bộ): analyst xem/duyệt bundle mẫu → nhập → tra IOC/nguồn/quan hệ/ATT&CK.** Dùng knowledge graph sẵn có: bundle STIX có provenance và MITRE ATT&CK. Analyst review là bước do Phong Hỏa đặt ra trước nhập; validation STIX không thay thế hay chứng minh OpenCTI bắt buộc bước này. Chưa cần portal, dashboard, LLM hay chặn; chưa coi đây là trải nghiệm SME đã chốt. MCP/XTM One là phương án A01 cần đối chiếu sau: có ghi/xóa nên không đưa vào demo hoặc tự xây khi chưa cần.

2. **Nạp dữ liệu: MITRE trước, ImportFileStix cho bộ mẫu kiểm soát; chưa tự viết connector.** MITRE cấp từ điển TTP để đối chiếu X01; ImportFileStix cho đường vào chuẩn và có validation. Sau khi demo này chạy và ghi lại version/tài nguyên, khảo sát một external connector chính thức có điều kiện truy cập rõ (AlienVault cần API key theo [cấu hình chính thức](https://github.com/OpenCTI-Platform/connectors/blob/master/external-import/alienvault/docker-compose.yml)). Chỉ tự viết Feodo/nguồn Việt khi bảng #9 chứng minh không có connector tương thích hoặc thiếu mapping/dữ liệu; khi đó dùng template SDK và đo incremental import/dedup, rate limit, TLP, license. Không suy ra “miễn phí”, nhẹ, hay phù hợp máy 16 GB.

3. **AI extractor: nghiên cứu/đánh giá trước, không chọn LLM trước.** Khóa hướng dẫn gán nhãn, pilot 5 báo cáo do 2 người gán độc lập, tính đồng thuận; sau đó cố định split/nguồn. IOC: so regex/LLM/grounding cùng nhãn IOC, P/R/F1 và tỉ lệ không có evidence. TTP: so các cấu hình trích TTP trên nhãn TTP, kiểm tra evidence ngữ nghĩa; mã ATT&CK tồn tại chỉ là kiểm tra bổ sung. Đo latency/chi phí và 10 mẫu prompt-injection. Output là bản nháp STIX có evidence; người duyệt mới nhập. Quy tắc Phong Hỏa bảo thủ hơn FIRST: **TLP:AMBER/AMBER+STRICT/RED không gửi cloud**; GREEN không mặc nhiên gửi cloud. Demo hiện chỉ dùng dữ liệu tổng hợp hoặc công khai có đủ quyền; dùng GREEN cần quyết định chia sẻ riêng đúng phạm vi cộng đồng/nguồn. Đây là điều kiện đánh giá, không phải bằng chứng chốt hiện có đủ chống injection.

## Ba việc ưu tiên (khớp backlog)

1. **#9 → #10:** lập bảng version/license/auth/rate-limit/TLP cho MITRE, ImportFileStix và một feed, kèm quy tắc dữ liệu được/không được gửi cloud; sau đó chỉ dựng MITRE + bundle STIX mẫu theo checklist quan sát (không bật hàng loạt 5 feed).
2. **#22 (thu hẹp pilot):** hai người gán độc lập 5 báo cáo trước, chốt quy tắc/evidence và đồng thuận rồi mới làm 20+20 của #22/#23.
3. **#24 trước #25/#44:** đo baseline regex cho IOC và khung chấm TTP/evidence riêng trên tập đã khóa; chỉ so sánh LLM/RAG cùng tác vụ sau kiểm tra TLP.

**Bước đầu cụ thể khuyến nghị:** mở #9 với bảng quyết định cho ba thành phần, rồi chuẩn bị bundle STIX 2.1 có nguồn/notice MITRE để analyst duyệt trước nhập và tra cứu ở #10. Báo cáo tooling cùng thư mục đã được đối chiếu cho MCP/TLP; chưa có thay đổi repo/lab.

**Một câu hỏi sản phẩm cần chốt:** Bản demo đầu cần thuyết phục **nhân viên IT SME tra một IOC để biết nên làm gì**, hay **analyst quản lý/duyệt dữ liệu CTI** trước?
