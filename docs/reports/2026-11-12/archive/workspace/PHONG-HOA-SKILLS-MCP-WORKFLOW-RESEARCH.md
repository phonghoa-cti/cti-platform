# Nghiên cứu skill MCP và workflow cho Phong Hỏa

Ngày đối chiếu: 10/11/2026. Phạm vi: chọn công cụ và cách làm cho team phát triển và trợ lý trong sản phẩm. Kết quả là khuyến nghị có nguồn; chưa cài skill, thêm dịch vụ, sửa repo hay thử trên lab.

**Khuyến nghị của Leader:** dùng quy trình đang có làm trục chính, tận dụng hai skill riêng của repo sau khi sửa quy tắc chia sẻ dữ liệu, chỉ chọn một số skill phát triển cần thiết. Giữ kết nối GitHub đã dùng được; bổ sung công cụ đọc tài liệu hoặc kiểm thử khi có nhu cầu thật. Với trợ lý Phong Hỏa, so sánh MCP chính thức của OpenCTI với lớp công cụ nghiệp vụ hẹp trong spec A01 trước khi chọn cách xây.

## 1. Phân biệt ba phần

- **Skill:** hướng dẫn thực hiện một loại việc, có thể kèm tài liệu và script. Có skill không đồng nghĩa đã có quyền truy cập hoặc phần mềm phụ thuộc.
- **MCP:** giao thức giúp AI gọi công cụ và lấy dữ liệu từ một dịch vụ. Quyền phải được giới hạn bằng tài khoản và mã kiểm soát thực tế.
- **Workflow:** thứ tự công việc, người phụ trách, đầu ra và điều kiện chuyển bước.

Tài liệu OpenAI phân biệt rõ lớp hướng dẫn của skill với dữ liệu và hành động do dịch vụ cung cấp. [Nguồn](https://developers.openai.com/plugins/concepts/skills).

## 2. Hiện trạng đã quan sát

| Nơi kiểm tra | Kết quả | Ý nghĩa |
|---|---|---|
| Repo tại head PR #1 `8d9d7df54e90a1811b58a713cfe7ec56072ed0a7` | Có `cti-thesis-conventions`, `stix-connector`, danh mục skill gợi ý, ba vai planner/implementer/reviewer và CI | Có cơ sở để kế thừa; các file ở PR chưa mặc nhiên thuộc main |
| Bot Leader trong OpenMausBot | Chưa có skill nhập riêng và chưa có dịch vụ MCP tự thêm | Không đồng nghĩa không có công cụ: kết nối GitHub và các skill do môi trường Codex cung cấp đang sẵn có |
| Kết nối GitHub | Đã đọc được repo, file và PR ở lượt này | Chưa cần thêm GitHub MCP trùng chức năng |
| Các bot khác | Chưa kiểm tra việc nạp từng skill | Danh mục của Leader không chứng minh mọi bot đã có cùng bộ skill |
| A01 tại PR #1 | Spec nháp dùng Hermes, Telegram, lớp công cụ qua portal-api; bảng hiện có **7 công cụ**, dù issue #38 nói 6 | Cần chốt hợp đồng theo spec/ref, tránh sao chép con số trong tiêu đề issue |

Nguồn repo: [danh mục skill](https://github.com/phonghoa-cti/cti-platform/blob/8d9d7df54e90a1811b58a713cfe7ec56072ed0a7/.agents/skills/README.md), [A01](https://github.com/phonghoa-cti/cti-platform/blob/8d9d7df54e90a1811b58a713cfe7ec56072ed0a7/docs/specs/A01-tro-ly-hermes.md), [CI](https://github.com/phonghoa-cti/cti-platform/blob/8d9d7df54e90a1811b58a713cfe7ec56072ed0a7/.github/workflows/ci.yml).

## 3. Skill nên chọn

| Skill và nguồn gốc | Ai dùng | Khuyến nghị | Điều kiện và giới hạn |
|---|---|---|---|
| `cti-thesis-conventions` của repo | Research, Engineer, QA | Giữ và chỉnh trước khi xử lý dữ liệu thật | Sửa quy tắc TLP ở mục 6; công thức điểm là lựa chọn của dự án, chưa phải mô hình đã được thực nghiệm xác nhận |
| `stix-connector` của repo | Engineer, QA | Giữ | Hữu ích vì tách tải, parse, chuyển STIX và fixture; đối chiếu API/SDK đúng phiên bản, đo RAM thay vì mặc định 256 MB là đủ |
| [`research` của mattpocock](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/research/SKILL.md) | Research | Tham khảo, thích nghi với team | Dùng nguồn gốc và báo cáo có trích dẫn; bản gốc yêu cầu mở agent nền, nên cần gắn với CTI Research sẵn có, tránh tạo agent trùng |
| [`systematic-debugging`](https://github.com/obra/superpowers/blob/main/skills/systematic-debugging/SKILL.md) | Engineer | Tận dụng khi có lỗi | Tái hiện, tìm nguyên nhân, thử một giả thuyết; dùng kiểm tra phù hợp, không ghi secret hoặc dữ liệu nhạy cảm vào log |
| [`test-driven-development`](https://github.com/obra/superpowers/blob/main/skills/test-driven-development/SKILL.md) | Engineer | Dùng cho logic sản phẩm và sửa lỗi | Test hành vi thất bại trước rồi sửa cho đạt; không xóa code có trước hay áp quy trình máy móc lên thay đổi tài liệu nhỏ |
| [`verification-before-completion`](https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md) | Leader, Engineer, QA | Tận dụng khi bàn giao | Bằng chứng phải gắn với bản code được giao; không chạy lại vô ích khi không có thay đổi hoặc nghi ngờ mới |
| [`playwright-cli` của Microsoft](https://github.com/microsoft/playwright-cli/tree/main/skills/playwright-cli) | QA, Engineer | Thử khi portal có luồng chạy được | Đã đọc SKILL.md; ưu tiên test chạy lại được. Trong OpenMausBot vẫn dùng trình duyệt được cấp cho thao tác web, không dùng CLI để vượt quyền hoặc chiếm trình duyệt cá nhân |
| [`web-design-guidelines` của Vercel](https://github.com/vercel-labs/agent-skills/blob/main/skills/web-design-guidelines/SKILL.md) | Antigravity; QA soát khả năng sử dụng | Để giai đoạn portal | Skill tải quy tắc mới từ mạng; ghi lại ref/ngày của quy tắc dùng để kết quả review tái hiện được. Chưa thay thế tiêu chí UI riêng của Phong Hỏa |

Superpowers đã nằm trong danh mục skill của môi trường Leader hiện tại; không cần cài lại toàn bộ chỉ để có các mục trên. Việc nhập cho bot cụ thể vẫn cần kiểm tra khả năng nạp và gọi đúng skill.

Đã đối chiếu mức sử dụng trên [skills.sh](https://skills.sh/) để tìm ứng viên: `research` khoảng 789,1 nghìn lượt cài; `systematic-debugging` 327,3 nghìn; TDD 275,4 nghìn; verification 270,9 nghìn; web-design-guidelines 845,5 nghìn. Đây là số hiển thị ngày kiểm tra, không phải bằng chứng an toàn. Metadata GitHub cho biết Superpowers và mattpocock dùng MIT; Playwright CLI dùng Apache-2.0. Với Vercel, chưa xác nhận giấy phép ở cấp skill nên cần kiểm tra trước khi sao chép/phân phối lại.

**Chưa đưa vào bộ mặc định:**

- [`to-spec` của mattpocock](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/engineering/to-spec/SKILL.md) tự xuất bản lên issue tracker và đặt nhãn `ready-for-agent`, đồng thời yêu cầu danh sách user story rất dài. Có ích để tham khảo cấu trúc, nhưng dùng nguyên bản dễ trùng spec và issue hiện có, cũng không hợp cách giao việc gọn của team.
- Bộ `Anthropic-Cybersecurity-Skills` trong README là của **mukul975**, không phải Anthropic. Mẫu OpenCTI đã đọc dùng image `6.4.4`, ví dụ dùng chung token admin và bật làm giàu tự động tới dịch vụ ngoài. Chỉ dùng làm tài liệu tham khảo sau review, chưa cài cả bộ. Metadata repo ghi Apache-2.0; giấy phép không chứng minh cấu hình phù hợp. [Skill đã kiểm tra](https://github.com/mukul975/Anthropic-Cybersecurity-Skills/blob/main/skills/building-ioc-enrichment-pipeline-with-opencti/SKILL.md).
- Không bật thêm bộ thiết kế để Codex thay Antigravity. Antigravity vẫn là bên phụ trách thiết kế khi khả dụng.

## 4. MCP dành cho team phát triển

| Lựa chọn | Giá trị | Quyết định hiện tại | Kiểm tra trước khi dùng |
|---|---|---|---|
| GitHub hiện có | Đọc code, issue, PR và bằng chứng CI | **Dùng hiện có** | Phạm vi repo; hành động ghi phải thuộc nhiệm vụ đã giao |
| [GitHub MCP chính thức](https://github.com/github/github-mcp-server) | Cho môi trường khác chưa có kết nối GitHub | **Chưa thêm bản trùng** | Nếu cần: giới hạn tài khoản vào repo, chế độ chỉ đọc và nhóm công cụ cần thiết; README hỗ trợ `--read-only` và chọn toolsets |
| [Context7 của Upstash](https://github.com/upstash/context7) | Tra tài liệu thư viện theo phiên bản | **Thử khi bắt đầu lập trình** | Gửi câu hỏi kỹ thuật tối thiểu; không gửi báo cáo CTI hoặc secret. Xác minh thư viện/phiên bản thật có trong dữ liệu; không coi kết quả tìm được là tài liệu chính thức nếu chưa đối chiếu |
| [OpenAI Docs MCP](https://developers.openai.com/learn/docs-mcp) | Đọc tài liệu OpenAI | **Chỉ cần khi dùng OpenAI API/SDK hoặc cấu hình liên quan** | Dịch vụ chỉ đọc tài liệu, không gọi API thay người dùng; không cần cài plugin Platform chỉ để đọc docs |
| [Playwright CLI và MCP](https://github.com/microsoft/playwright-cli) | Kiểm thử portal | **Chưa thêm ngay** | Microsoft định hướng CLI + skill cho coding agent; MCP phù hợp thao tác khám phá có trạng thái. Chọn một cách cho nhu cầu, không dùng cả hai mặc định |
| Filesystem, Memory, Sequential Thinking, Docker MCP chung | Có thể bổ sung trong môi trường thiếu chức năng | **Tạm hoãn** | Chưa có khoảng trống đủ cụ thể: team đã có file/shell, ghi nhận chung và cách điều phối |

Context7 hiện hỗ trợ cách dùng CLI + skills hoặc MCP; tài liệu khuyến nghị API key cho hạn mức cao hơn. Không xác minh giá trả phí, hạn mức tài khoản hay chi phí thực tế trong nghiên cứu này, nên chưa chốt ngân sách. Khi cần credential, nhập qua nơi lưu an toàn của ứng dụng, không qua chat. [Nguồn](https://github.com/upstash/context7#installation).

## 5. MCP nằm trong sản phẩm Phong Hỏa

Đây là phần riêng với công cụ phát triển. Trợ lý phục vụ người dùng cuối không được nhận quyền của Leader hay tài khoản GitHub dùng để viết code.

**Phát hiện mới:** OpenCTI công bố MCP tích hợp trong **XTM One Community Edition**. Nó cần XTM One đang chạy, đăng ký OpenCTI và tài khoản liên kết; có cả đọc, tạo, cập nhật và xóa dữ liệu theo quyền người gọi. Chưa thử trên lab hay đo tài nguyên. [Tài liệu chính thức](https://docs.opencti.io/latest/deployment/mcp-server/).

| Phương án | Điểm mạnh | Khoảng trống cần kiểm tra |
|---|---|---|
| MCP chính thức qua XTM One | Kế thừa công cụ và tích hợp OpenCTI | Tài nguyên, phiên bản tương thích, tài khoản; cần chứng minh vai trò chỉ đọc bị chặn ghi/xóa; không mặc định có quy trình đề xuất/duyệt riêng của Phong Hỏa |
| Lớp công cụ nghiệp vụ theo A01 qua portal-api | Phạm vi hẹp: đọc và tạo nháp/đề xuất, có thể gắn quy trình duyệt W05 | Phải tự duy trì, kiểm thử quyền, dữ liệu và lỗi; tránh viết lại việc SDK chính thức đã hỗ trợ |

**Khuyến nghị của Leader:** giữ A01 làm giả thuyết thiết kế, không kết luận phải tự xây toàn bộ. Khi có lab, thử phần tra cứu chỉ đọc của phương án chính thức trước; nếu thiếu quy trình nghiệp vụ thì giữ lớp mỏng qua portal-api. Đây là quyết định cần bằng chứng thử nghiệm, chưa đổi ADR hoặc spec.

Tiêu chí so sánh: cùng bộ dữ liệu mẫu, cùng vai trò, số thao tác cần có, lỗi quyền, phạm vi dữ liệu trả về, độ trễ và RAM. Xác nhận ở phía dịch vụ rằng tài khoản agent không thể duyệt/xóa/chặn; không chỉ giấu nút hoặc viết “không được” trong prompt.

Với `extract_report(url)` cần chặn URL trỏ nội bộ và kiểm tra lại sau chuyển hướng; với đề xuất cần tránh tạo trùng khi thử lại, ghi người tạo/người duyệt và không cho tự duyệt. Nếu dùng OAuth, xác minh token đúng đối tượng nhận, không chuyển tiếp tùy tiện token từ dịch vụ khác. Đây là yêu cầu kiểm thử đề xuất, chưa phải kết quả pentest. [MCP security](https://modelcontextprotocol.io/specification/latest/basic/security_best_practices).

Nhãn `readOnlyHint` chỉ mô tả ý định, không thực thi phân quyền và không chống prompt injection. [Giải thích của dự án MCP](https://blog.modelcontextprotocol.io/posts/2026-03-16-tool-annotations/).

## 6. Ba điểm cần xử lý trước khi dựa vào cấu hình hiện có

**A. Quy tắc TLP cần sửa.** `cti-thesis-conventions/SKILL.md:28` cho phép cả CLEAR và GREEN gửi lên LLM cloud. FIRST giới hạn GREEN trong cộng đồng được phép; không thể suy ra nhà cung cấp AI bất kỳ thuộc cộng đồng đó. Đề xuất: chỉ dùng dữ liệu có quyền chia sẻ với nhà cung cấp cụ thể; khi chưa rõ thì xử lý nội bộ. CLEAR cũng không tự xóa nghĩa vụ bản quyền hoặc ràng buộc dữ liệu khác. Chưa chỉnh file. [File dự án](https://github.com/phonghoa-cti/cti-platform/blob/8d9d7df54e90a1811b58a713cfe7ec56072ed0a7/.agents/skills/cti-thesis-conventions/SKILL.md#L28), [FIRST TLP 2.0](https://www.first.org/tlp/).

**B. Cấu hình OpenCode phải khớp phiên bản chạy thật.** Các file `.opencode/agents/` ở PR #1 dùng `permission` và `temperature`. Tài liệu OpenCode V2 hiện yêu cầu `permissions` dạng danh sách và không dùng các trường cũ đó trong cấu hình V2 mới. Chưa chạy OpenCode hoặc kiểm tra cấu hình hiệu lực trong lượt này; chưa kết luận quyền hiện tại thực thi ra sao. Nếu dùng OpenCode, xác minh executable/version rồi chuyển cấu hình theo đúng phiên bản và thử trên thư mục mẫu. [Ví dụ repo](https://github.com/phonghoa-cti/cti-platform/blob/8d9d7df54e90a1811b58a713cfe7ec56072ed0a7/.opencode/agents/implementer.md#L5), [tài liệu quyền](https://opencode.ai/docs/permissions/), [tài liệu agent](https://opencode.ai/docs/agents/).

**C. Quét secret hiện chưa thể coi là quét lịch sử Git.** CI dùng `gitleaks ... dir /repo`, dù checkout có đầy đủ lịch sử. Gitleaks phân biệt `dir` quét file/thư mục với `git` quét bản vá trong lịch sử. Đề xuất quét phạm vi commit cần thiết, che giá trị nhạy cảm trong log và ghim phiên bản công cụ thay vì `latest`; kiểm tra khả năng tái hiện của pytest/ruff đang cài không ghim phiên bản. Chưa sửa hay chạy CI. [CI dòng 15–30](https://github.com/phonghoa-cti/cti-platform/blob/8d9d7df54e90a1811b58a713cfe7ec56072ed0a7/.github/workflows/ci.yml#L15), [Gitleaks](https://github.com/gitleaks/gitleaks#usage).

## 7. Workflow đề xuất và lựa chọn đã so sánh

| Cách làm | Đánh giá cho Phong Hỏa |
|---|---|
| Quy trình repo + skill chọn theo việc | **Khuyến nghị**: giữ spec, ADR, issue, CI và đội hình đã có; bổ sung phần nghiên cứu và bằng chứng còn thiếu |
| Cài toàn bộ Superpowers và các bộ điều phối tương tự | Nhiều năng lực sẵn có nhưng dễ lặp hỏi đáp, lập kế hoạch, agent và review; chỉ dùng phần cần cho nhiệm vụ |
| [GitHub Spec Kit](https://github.com/github/spec-kit) | Có luồng từ yêu cầu đến kế hoạch/task/code và các phần mở rộng; đáng tham khảo, chưa cần thêm một hệ thống tài liệu song song |

Luồng chuẩn:

1. **Nghiên cứu:** câu hỏi, 2–3 lựa chọn thực sự, nguồn và ref, dùng lại được gì, điều chưa biết, khuyến nghị có lý do. Dừng khi đủ để quyết định; nếu còn thiếu thì đề xuất thử nghiệm có giới hạn.
2. **Spec/ADR:** ghi hành vi, ngoài phạm vi, tiêu chí đạt và ranh giới dữ liệu; cập nhật tài liệu đã có thay vì tạo bản cạnh tranh. Leader chỉ hỏi người dùng điều không thể suy ra mà thay đổi sản phẩm.
3. **Giao việc:** một issue/owner, đúng ref/worktree, nghiên cứu liên quan và kiểm tra phải chạy. Engineer thực hiện; Antigravity sở hữu UI.
4. **Kiểm chứng:** test hành vi và lint; logic CTI dùng fixture; phần quyền có kiểm tra sai vai trò, dữ liệu bị hạn chế và hành động không được phép. QA độc lập cho phần rủi ro hoặc mốc demo.
5. **Demo và báo cáo:** kết quả quan sát được, bằng chứng, giới hạn, cách thử và phần người dùng cần quyết định. CI xanh không chứng minh lab đã chạy; báo cáo agent không thay kiểm tra diff.

Tổ chức tài liệu trong repo khi có yêu cầu triển khai: `docs/research/` cho bằng chứng; `docs/specs/` cho hành vi; `docs/adr/` cho quyết định; `docs/ai-log/` cho cấu hình/thí nghiệm đã lọc dữ liệu nhạy cảm; `docs/PROGRESS.md` cho tiến độ. Không cần thêm hệ quản trị team, lịch tự động hay nền tảng điều phối mới ở giai đoạn này.

## 8. Cách thử skill hoặc công cụ trước khi nhập chính thức

1. Chọn đúng nhu cầu còn thiếu, kiểm tra công cụ đang có để tránh trùng.
2. Ghi chủ sở hữu nguồn, URL, commit/release, giấy phép và file/script phụ thuộc. Đọc cả phần tải thêm hoặc thực thi lệnh; không chỉ đọc mô tả.
3. Thử ở phạm vi riêng với dữ liệu tổng hợp hoặc dữ liệu công khai đủ quyền sử dụng; không để dùng token quản trị theo ví dụ mặc định.
4. Kiểm tra một tình huống thành công, một tình huống từ chối quyền và cách tắt/hoàn tác. Với skill, kiểm tra gọi đúng việc và không tự mở rộng sang publish, tạo bot hoặc cài thêm.
5. Chỉ sau kết quả đạt mới ghim bản đã kiểm tra, ghi bot sử dụng và cách gọi. Khi nâng phiên bản, xem diff và chạy lại phần kiểm tra bị ảnh hưởng.

Các bước tiếp theo hợp lý: sửa/kiểm chứng ba điểm ở mục 6 trong một nhiệm vụ riêng; sau đó thử bộ skill tối thiểu trên một task có spec; chỉ thêm MCP khi task chứng minh cần. Không có bước cài đặt nào đã được thực hiện trong nghiên cứu này.
