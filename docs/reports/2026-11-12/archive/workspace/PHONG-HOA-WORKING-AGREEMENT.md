# Cách làm việc của team Phong Hỏa

Bản 3, ngày 10/11/2026. Repo: https://github.com/phonghoa-cti/cti-platform.

Quyết định mới của người dùng: **Codex làm giao diện, không chờ Antigravity; máy ảo/lab để sau**. Bảng phân công mới và phạm vi chạy song song tại `PHONG-HOA-PARALLEL-PLAN.md` được ưu tiên hơn các mục thiết lập/handoff lịch sử bên dưới. CTI Backend, CTI AI Agent và CTI Frontend đã được cấu hình Codex/Sol medium; Engineer giữ hạ tầng/tích hợp. Mỗi người sửa một working tree riêng, không dồn mọi phần vào một Engineer.

Cập nhật 23:15: mục 11 là quy trình tiếp tục dự án theo yêu cầu hiện hành. Các nhận định “chưa được phép triển khai” ở phần thiết lập ban đầu là lịch sử tại lúc thiết lập, không phủ định yêu cầu triển khai/tiếp tục về sau của người dùng.

Mục tiêu là giúp bạn vừa học vừa hoàn thành Phong Hỏa, nền tảng thông tin về mối đe dọa mạng cho doanh nghiệp vừa và nhỏ Việt Nam. Mỗi đầu việc bắt đầu bằng tìm hiểu cái đã có, sau đó mới chọn cách làm và triển khai. Leader là đầu mối duy nhất; các thành viên AI hỗ trợ bạn, không thay thế vai trò của nhóm sinh viên hoặc người duyệt nghiệp vụ.

Bạn đã giao Leader tự tổ chức team và cách làm. Các mặc định dưới đây do Leader chọn, có thể điều chỉnh khi bạn phản hồi; không phải các quyết định sản phẩm đã được bạn duyệt riêng.

## 1. Team và trách nhiệm

| Thành viên | Model đã cấu hình | Chịu trách nhiệm | Khi tham gia |
|---|---|---|---|
| Leader | GPT-6 Astra | Làm rõ mục tiêu, ưu tiên, định hướng kỹ thuật, chia việc, review và báo cáo | Mọi đầu việc |
| CTI Research | GPT-5.6 Terra, medium | Tìm giải pháp, bài nghiên cứu và chia sẻ gốc; đánh giá tái sử dụng | Khi bắt đầu đầu việc hoặc cần cập nhật bằng chứng |
| CTI Engineer | GPT-5.6 Sol, medium | Hạ tầng, connector, tích hợp và công cụ điều phối | Khi nghiên cứu, spec và phạm vi đã đủ |
| CTI Backend | GPT-5.6 Sol, medium | Lõi duyệt, Web API, danh tính và quyền | Tree backend riêng |
| CTI AI Agent | GPT-5.6 Sol, medium | X01 extractor, đánh giá và A01 trợ lý | Nghiên cứu/lát cắt AI độc lập |
| CTI Frontend | GPT-5.6 Sol, medium | Giao diện web theo DESIGN và hợp đồng dữ liệu | Tree frontend riêng |
| CTI QA Security | GPT-5.6 Sol, medium | Kiểm thử độc lập, quyền truy cập, dữ liệu CTI, hành vi AI | Thay đổi có rủi ro hoặc trước mốc demo |
| Antigravity | Không còn là điều kiện triển khai | Phân công cũ được người dùng thay bằng Codex | Không chờ hoặc giao giả |

Team Phong Hỏa cùng ba chuyên viên đã được áp dụng; Leader là Chief. Antigravity không được tạo giả bằng model khác. Một Engineer sửa một working tree tại một thời điểm. Không giao cùng một việc cho nhiều bot để lấy số lượng. Chỉ nâng Sol lên high khi có lý do về độ phức tạp hoặc vướng mắc cụ thể; worker không tự giao việc tiếp.

Ba cách tổ chức đã cân nhắc: Leader làm hết ít tốn điều phối nhưng dễ bỏ sót; Leader cùng ba vai trò trên phân công rõ và chỉ gọi khi cần; chia ngay theo mọi module tạo nhiều người chưa có việc. Leader chọn cách thứ hai. Việc nhỏ ít rủi ro do Leader review, không bắt buộc gọi QA.

## 2. Bạn và Leader phối hợp thế nào

Bạn có thể nói tự nhiên: “Tôi muốn tra cứu một domain và hiểu vì sao nó nguy hiểm”, “Giải thích phần này”, “Cho tôi xem demo”, “Đổi ưu tiên sang phần đề cương”, hoặc “Tạm dừng”. Không cần viết prompt dài hay giao việc riêng cho từng bot.

Leader chuyển ý tưởng thành mục tiêu quan sát được, tiêu chí đạt và đầu việc nhỏ. Trước khi làm, Leader báo ngắn: mục tiêu, lý do, phát hiện từ research, phương án khuyến nghị, bước tiếp theo và cách kiểm tra. Có lựa chọn thực sự thì nêu tối đa 2–3 phương án cùng đánh đổi; không tạo lựa chọn giả cho thao tác thông thường.

Leader tự quyết các chi tiết kỹ thuật có thể đảo ngược trong phạm vi đã giao. Khi thiếu thông tin làm thay đổi sản phẩm, Leader tìm trong repo và trao đổi trước rồi chỉ hỏi một điều quan trọng nhất. Bạn quyết định đối tượng sử dụng, mục tiêu học tập, ưu tiên và chấp nhận trải nghiệm thực tế. Không biến mọi bước nhỏ thành một lần xin phép.

Một yêu cầu triển khai đã rõ cho phép thực hiện và kiểm chứng trong phạm vi đó. Chỉ xin thêm quyền khi phạm vi hoặc hậu quả chưa được cho phép: chi tiền, dùng tài khoản cần đăng nhập, gửi thông tin ra ngoài, thay đổi quyền truy cập, merge, phát hành hoặc thao tác phá hủy. Đề nghị duyệt phải kèm kết quả cụ thể để xem; không xin duyệt một kế hoạch mơ hồ. Nếu đã được cho phép trong cuộc trao đổi thì không hỏi lại.

Thiết lập team hiện tại chưa phải yêu cầu triển khai tất cả backlog. Chưa sửa mã nguồn, push, merge, bật bảo vệ nhánh hoặc triển khai lab trong lần thiết lập này.

## 3. Chu trình cho mỗi đầu việc

**Mục tiêu → Nghiên cứu → Chọn giải pháp → Mô tả và tiêu chí đạt → Triển khai nhỏ → Kiểm chứng → Demo và ghi nhận.**

1. **Mục tiêu:** một người dùng làm được việc gì; việc gì chưa làm trong lượt này.
2. **Nghiên cứu:** đọc hiện trạng, issue và PR trước; tìm tài liệu chính thức, dự án có mã nguồn, nghiên cứu gốc và trải nghiệm triển khai có thể kiểm chứng.
3. **Chọn giải pháp:** dùng sẵn, điều chỉnh hay tự xây. Ghi lý do, chi phí tích hợp, giới hạn và điều chưa biết. Tự xây phải nêu khoảng trống hoặc mục tiêu học tập cụ thể.
4. **Mô tả:** spec là mô tả hành vi và tiêu chí đạt; ADR là ghi chép một quyết định kỹ thuật cùng lý do. Tận dụng tài liệu trong repo, không tạo bản mâu thuẫn.
5. **Triển khai:** một lát cắt nhỏ, một owner, một nhánh/working tree riêng. Giữ nguyên sửa đổi có trước. Không tự kéo thêm việc “tiện thể”.
6. **Kiểm chứng:** kiểm tra đúng phần thay đổi; bảo mật và tích hợp cần tình huống thất bại, sai quyền và dữ liệu không hợp lệ. Phân biệt test cục bộ với hoạt động trên lab.
7. **Bàn giao:** kết quả, bằng chứng, giới hạn, cách thử, điều cần bạn quyết định và 2–4 khái niệm học thêm khi có giá trị. Cập nhật tiến độ trong phạm vi task được giao.

Nghiên cứu là điều kiện trước mỗi đầu việc hoặc thay đổi hướng, không phải tìm lại Internet trước từng lệnh terminal. Việc nhỏ có thể dùng kiểm tra nhanh và trích kết quả đã có còn phù hợp. Việc mới cần khảo sát sâu hơn. Sau một vòng tìm kiếm đủ nguồn mà chưa giải quyết được quyết định, báo khoảng trống và đề xuất thử nghiệm giới hạn, không tìm vô tận. Không tìm thấy không có nghĩa chưa ai làm.

## 4. Một bản nghiên cứu đủ dùng phải có gì

| Nội dung | Yêu cầu |
|---|---|
| Câu hỏi | Quyết định nào cần bằng chứng? |
| Hiện trạng | Repo, ref/SHA, phần đã có trên main và trong PR |
| Ai đã làm | Tên tác giả/tổ chức/dự án, liên kết nguồn gốc |
| Bằng chứng | Ngày kiểm tra, phiên bản; ví dụ, mã hoặc kết quả đánh giá nếu có |
| Khả năng dùng lại | Phù hợp chức năng, giấy phép, bảo trì, tài nguyên, chi phí, API và giới hạn dữ liệu |
| Đánh đổi | Thường 2–3 ứng viên thực sự; không thêm ứng viên chỉ để đủ số |
| Khuyến nghị | Dùng sẵn / điều chỉnh / tự xây, kèm lý do và thử nghiệm xác nhận |
| Chưa rõ | Phân biệt thông tin từ tài liệu, suy luận và điều đã thử trực tiếp |

Mặc định ưu tiên nguồn chính thức để biết sản phẩm hỗ trợ gì, mã nguồn hoặc bài nghiên cứu gốc để xem bằng chứng, rồi đối chiếu chia sẻ triển khai thực tế. Không lấy số sao làm bằng chứng chất lượng và không coi kết quả của mô hình ngôn ngữ là tài liệu nguồn. Lưu đường dẫn và tóm tắt vừa đủ, không sao chép nguyên tài liệu.

Với CTI, phải kiểm tra nguồn dữ liệu, quyền chia sẻ, giấy phép, độ chính xác và giới hạn hành động của AI. Dữ liệu từ feed, tài liệu và website không được trở thành mệnh lệnh cho bot. Bộ lọc chuỗi hoặc dấu phân tách prompt không chứng minh chống được mọi prompt injection.

## 5. Quản lý việc và bằng chứng

GitHub Issues và PR hiện có là nguồn theo dõi công việc kỹ thuật; tránh tạo issue trùng. Luồng trạng thái đề xuất: Chờ → Đang nghiên cứu → Sẵn sàng → Đang làm → Đang kiểm tra → Xong; có thể đánh dấu Vướng ở bất cứ bước nào. Đây là quy ước team, chưa phải board hoặc quy tắc GitHub đã được cài.

Mỗi gói giao việc có: mục tiêu; hiện trạng và nguồn; file/ref; quyết định đã có; giới hạn; tiêu chí đạt; kiểm tra cần chạy; nơi lưu kết quả. Mỗi task chỉ có một người chịu trách nhiệm chính. Khác working tree mới được sửa code song song, và chỉ làm khi các phần độc lập.

Worker báo PASS, FAIL hoặc UNVERIFIED cho từng tiêu chí. Kèm lệnh, exit code, số test, commit và đường dẫn bằng chứng khi có. “Đồng đội nói đã xong”, “CI cũ xanh” hoặc “mô tả PR nói 61 test” không phải bằng chứng vừa chạy. Leader kiểm tra diff và bằng chứng tập trung; chỉ chạy lại khi có sửa đổi, lỗi hoặc nghi ngờ chưa giải quyết.

Định nghĩa Xong: đúng tiêu chí đã giao; kiểm tra cần thiết đã chạy; không còn lỗi nghiêm trọng trong phạm vi; có tài liệu đủ để dùng/duy trì; chỉ rõ những phần chưa kiểm chứng. Xong cục bộ, đã merge, chạy trên lab và đã phát hành là các trạng thái khác nhau.

Không cài lịch họp hay báo cáo tự động khi chưa có nhu cầu cụ thể. Báo tại các mốc có ý nghĩa: phát hiện đổi hướng, vướng mắc cần bạn, kết quả nghiên cứu, bản demo và kết quả kiểm tra. Không để các bot phát báo cáo lặp nhau cho bạn.

## 6. Hiện trạng được kiểm tra ngày 10/11/2026

| Hạng mục | Quan sát và ý nghĩa |
|---|---|
| Main | `3ff7daf93469dd13692fd1f7aec83a323e2ebb43`; chủ yếu bộ khung và hướng dẫn, các thư mục chức năng chính có `.gitkeep` |
| Công việc đang mở | 44 issue và 2 PR; con số API 46 gồm cả PR, không phải 46 task riêng |
| PR #1 | Đang mở; head `8d9d7df54e90a1811b58a713cfe7ec56072ed0a7`; API báo 54 file thay đổi; mô tả nêu core, spec và thiết kế |
| PR #46 | Đang mở; head `36259c118f519d3ac9cfc1f7b79e7180c2448a88`; API báo 61 file thay đổi so với main |
| Quan hệ PR | So sánh hai head cho thấy #46 đi trước #1 một commit, không đi sau; phần chênh gồm 10 file, chủ yếu extractor và cấu hình test |
| Kiểm thử | Mô tả PR tự báo 47/61 test đạt; chưa chạy lại, chưa review đầy đủ code, chưa xác minh lab |
| Lịch | PROGRESS cập nhật 21/10/2026; mốc đề cương 03/11 đã qua theo lịch, nhưng chưa biết tình trạng thực tế; hạn nộp ghi 27/02/2027 |
| Thiết kế | Antigravity hiện chưa khả dụng; chưa có handoff được thực thi |

Các ngày, cấu hình lab 16 GB và phạm vi đồ án là thông tin trong repo, cần xác nhận lại khi quyết định dựa vào chúng. Không xem tài liệu cũ là bằng chứng đã triển khai. Đối chiếu PR trước khi chọn điểm xuất phát; không mặc định viết lại vì main còn ít code.

Nguồn hiện trạng: [README](https://github.com/phonghoa-cti/cti-platform/blob/3ff7daf93469dd13692fd1f7aec83a323e2ebb43/README.md), [AGENTS](https://github.com/phonghoa-cti/cti-platform/blob/3ff7daf93469dd13692fd1f7aec83a323e2ebb43/AGENTS.md), [tiến độ](https://github.com/phonghoa-cti/cti-platform/blob/3ff7daf93469dd13692fd1f7aec83a323e2ebb43/docs/PROGRESS.md), [ADR 0001](https://github.com/phonghoa-cti/cti-platform/blob/3ff7daf93469dd13692fd1f7aec83a323e2ebb43/docs/adr/0001-chon-opencti-lam-loi.md), [issue](https://github.com/phonghoa-cti/cti-platform/issues), [PR #1](https://github.com/phonghoa-cti/cti-platform/pull/1), [PR #46](https://github.com/phonghoa-cti/cti-platform/pull/46), [so sánh hai head](https://github.com/phonghoa-cti/cti-platform/compare/8d9d7df54e90a1811b58a713cfe7ec56072ed0a7...36259c118f519d3ac9cfc1f7b79e7180c2448a88).

## 7. Cách làm đã có để kế thừa

Đã đọc nguồn chính thức ngày 10/11/2026:

| Nguồn | Điều team dùng |
|---|---|
| [GitHub Flow](https://docs.github.com/en/get-started/using-github/github-flow) | Nhánh riêng, thay đổi nhỏ, PR để thảo luận và review trước khi nhập vào nhánh chính |
| [MADR](https://adr.github.io/madr/) | Ghi gọn quyết định kỹ thuật quan trọng, bối cảnh và lý do; tiếp tục dùng thư mục ADR đã có |
| [OpenCTI connectors](https://docs.opencti.io/latest/deployment/connectors/) | Đối chiếu chức năng nạp, làm giàu và xuất dữ liệu có sẵn trước khi viết mới |
| [Mã nguồn connector chính thức](https://github.com/OpenCTI-Platform/connectors) | Có thư viện connector và template để khảo sát; kiểm tra từng component/version trước khi tái sử dụng |

Đây là cơ sở cho cách làm của team. Chưa phải kết luận rằng một connector cụ thể hoặc toàn bộ kiến trúc hiện tại phù hợp lab. Bảng nghiên cứu theo từng module là bước tiếp theo.

## 8. Thứ tự khởi động

1. Research lập bảng đối chiếu những gì OpenCTI và cộng đồng đã làm với backlog Phong Hỏa; đề xuất phạm vi demo đầu tiên có ích và vừa sức.
2. Leader xác định phần nào có thể kế thừa từ PR #1/#46, phần nào cần review hoặc kiểm chứng thêm; chưa mặc định merge.
3. Sau khi có mục tiêu triển khai cụ thể, Engineer kiểm tra baseline trên đúng ref trong môi trường riêng; QA tham gia theo rủi ro.
4. Làm một lát cắt chạy trọn luồng nhỏ nhất, ưu tiên dữ liệu mẫu an toàn và thành phần có sẵn; chỉ tăng phạm vi sau bằng chứng thực tế.

## 9. Mẫu giao việc ngắn

```text
Mục tiêu và người dùng:
Hiện trạng, repo, ref/SHA và file liên quan:
Nghiên cứu đã có và nguồn:
Quyết định, phạm vi và điều chưa làm:
Người phụ trách; working tree được phép sửa:
Tiêu chí đạt và kiểm tra cần chạy:
Nơi lưu kết quả; bằng chứng phải trả:
```

Mẫu báo về bạn: “Kết quả → Bằng chứng → Phần chưa kiểm chứng → Điều cần bạn quyết định (nếu có) → Bước tiếp theo”. Khi cần chạy lệnh, giải thích một câu lệnh đó làm gì; không trút log dài vào hội thoại.

## 10. Brief sẵn dùng cho Antigravity

Trạng thái: chuẩn bị bàn giao, chưa thực thi. Đây là gói định hướng ban đầu; người thiết kế xác minh tài liệu ở đúng ref trước khi bắt đầu.

- **Mục tiêu:** giúp người phụ trách IT tại SME hiểu cảnh báo và bước xử lý tiếp theo, tiếng Việt mặc định, hỗ trợ tiếng Anh theo repo.
- **Luồng cần đối chiếu:** Tổng quan → tra cứu IOC (dấu hiệu như domain/IP/hash) → xem bằng chứng và độ tin cậy; lỗ hổng liên quan tài sản; màn analyst duyệt đề xuất AI. Ưu tiên một luồng đầu tiên sau nghiên cứu, chưa dựng toàn bộ.
- **Màn/tài liệu nguồn:** kiểm tra `docs/design/DESIGN.md`, `docs/specs/W00-portal-tong-the.md`, W01–W05 và `api-portal.md` ở PR #1; đây là các đường dẫn được mô tả trong PR, chưa được Leader review nội dung. Dùng thiết kế sẵn có làm tham chiếu trước khi đề xuất khác.
- **Ràng buộc:** phân biệt dữ liệu mẫu, chưa có dữ liệu, đang tải, lỗi và không đủ quyền; không hiển thị trạng thái “đã chặn” khi chưa có hành động thật; không cho AI tự duyệt; không dùng thông tin nội bộ khó hiểu làm nội dung cho người dùng.
- **Đầu ra:** luồng chính, danh sách màn, mockup có trạng thái rỗng/lỗi/quyền, thành phần dùng lại và brief tích hợp API. Không code giao diện trước khi phạm vi và thiết kế đủ rõ.
- **Tiêu chí:** người mới thực hiện được luồng mục tiêu, thấy nguồn và lý do của cảnh báo, phân biệt đề xuất với hành động đã được duyệt; giao diện theo tài liệu dự án và kiểm tra khả năng sử dụng trên desktop/mobile phù hợp.
- **Vai trò Codex:** làm rõ hợp đồng dữ liệu, phân quyền và tích hợp; không tự thay Antigravity thiết kế trực quan.

## 11. Điều phối theo mục tiêu tổng, không dừng ở task con

Áp dụng cho công việc Phong Hỏa đang được người dùng yêu cầu tiếp tục. Nguồn và phân tích: `PHONG-HOA-ORCHESTRATION-RESEARCH-20261110.md`. Sổ hiện hành: `PHONG-HOA-RUNS.json`; nhật ký lát cắt cũ chỉ là bằng chứng lịch sử. Leader là người duy nhất sửa sổ, đồng đội trả báo cáo vào file được giao.

### Đầu lượt và sau mọi kết quả đồng đội

1. Đọc mục tiêu mẹ và tiêu chí còn thiếu trong sổ, sau đó đọc trạng thái task đang liên quan. Không dùng “đích gần nhất” để thay mục tiêu mẹ. Đã có triển khai được giao thì tiếp tục trong phạm vi đó; báo cáo tự động không hủy yêu cầu của người dùng.
2. Đối chiếu kết quả bằng request ID và SHA; báo cáo lặp của việc đã nghiệm thu không tạo việc mới. `reported` chưa là `accepted`. Review phần mới/rủi ro/bằng chứng thiếu, không chạy lại cả suite theo thói quen.
3. Đạt một task thì cập nhật evidence, giải phụ thuộc và chọn việc kế. Nếu chưa có brief, việc kế là nghiên cứu/lập brief cụ thể do Leader hoặc Research thực hiện, không chờ người dùng nói tiếp tục. Việc kỹ thuật chưa biết không tự động thành blocker cần người dùng.
4. Khi một phần chờ lab/UI/dữ liệu thật, chọn phần độc lập còn làm được. Blocker phải có lý do, người có thể giải và điều kiện mở lại; “xong lát cắt” không phải blocker.

### Trạng thái và giao việc

- `planned`: chưa đủ brief hoặc đang chờ phụ thuộc; `queued`: đủ brief, chờ người nhận.
- `dispatched`: đã có receipt accepted/queued cùng request ID và thread ID; chưa đủ bằng chứng gọi là đang chạy.
- `running`: có quan sát thật; `reported`: đã có kết quả chưa nghiệm thu; `accepted`: đã kiểm đủ phạm vi.
- `blocked`: trở ngại có lý do/chủ sở hữu/điều kiện mở; `failed`: cần chẩn đoán, không phải cớ dừng mục tiêu.
- Một người Sol medium sửa một working tree; Backend, Frontend và AI có thể làm song song trong tree/phạm vi riêng. Research chỉ đọc ghi riêng output. UX/UI do CTI Frontend qua Codex theo yêu cầu mới.
- Receipt thất bại không đổi task thành dispatched. Sửa đúng nguyên nhân; tối đa hai lần cùng nguyên nhân rồi đổi cách. Không polling, không tạo bản sao worker đang sống, không dùng báo cáo tự nhận làm bằng chứng chạy.
- Khi giao thành công, lưu receipt vào sổ rồi nhường lượt cho kết quả tự quay lại. Cơ chế callback có sẵn là người theo dõi công việc; không thêm lịch hỏi trạng thái.

### Cổng trước khi kết thúc lượt

Khi bộ kiểm tra được nghiệm thu, chạy `cti-platform-start\.venv\Scripts\python.exe workflow\check_continuation.py --ledger PHONG-HOA-RUNS.json`.
Trong khi chưa có script, Leader áp dụng bảng dưới bằng tay và ghi quyết định vào sổ; không giả vờ đã có bảo vệ tự động.

| Kết quả | Hành động |
|---|---|
| Có kết quả mới chưa review | Review hoặc giao sửa cụ thể. |
| Có task queued đủ phụ thuộc và người phụ trách rảnh | Giao thật và lưu receipt trước khi nhường lượt. |
| Có task thất bại hoặc mục tiêu đang mở nhưng không có việc tiếp | Chẩn đoán/lập brief tiếp, không tuyên bố xong. |
| Có việc đã được tiếp nhận, callback sẽ trả kết quả | Nhường lượt; báo đã giao, không báo dự án hoàn thành. |
| Mọi phần còn lại thực sự cần người dùng/tài nguyên ngoài phạm vi | Báo đúng blocker và phần đã chuẩn bị; không ghi hoàn thành. |
| Người dùng yêu cầu tạm dừng | Ghi lý do và dừng giao việc mới. |
| Toàn bộ tiêu chí mục tiêu đã được kiểm chứng | Kết thúc mục tiêu và báo kết quả. |

Sổ chỉ là dữ liệu đã ghi, không tự chứng minh tiến trình còn chạy hoặc test đã chạy. Bộ kiểm tra không tự gửi việc, không tự thay quyền, không là Stop hook của OpenMausBot. Không hứa “không bao giờ dừng” khi chưa có cơ chế ứng dụng thực thi.

### Tự tiếp tục khi Leader đã bỏ dở

Theo yêu cầu bổ sung của người dùng lúc 23:22 ngày 10/11/2026, đã tạo lịch `Phong Hỏa — tự tiếp tục việc còn mở`, ID `79621896-f322-47a8-80d7-072739a2314b`, mỗi 30 phút và khi ứng dụng khởi động. Quy tắc đầy đủ tại `PHONG-HOA-AUTONOMOUS-CONTINUATION.md`. Lịch phục hồi công việc khi không có ai đang làm: nghiệm thu kết quả bị bỏ sót, lập brief hoặc giao bước kế. Đây không phải lịch chỉ hỏi bot đã xong chưa; callback vẫn là đường tiếp tục chính. Trước khi sửa sổ/giao việc phải kiểm một lần các cuộc đang mở để tránh trùng với Leader đang hoạt động. Chưa xem cấu hình đã bật là bằng chứng đã chạy được toàn chu kỳ tự nối việc.

### Khi ngữ cảnh thay đổi

Đọc working agreement → sổ tổng → brief/kết quả của task liên quan → Git hiện tại. Chỉ đọc phần cần thiết. Mọi báo cáo cuối về tiến độ phải nói rõ đang nhường lượt có công việc thật hay đang chờ điều kiện nào; không kết bằng lời hứa chưa thực hiện.
