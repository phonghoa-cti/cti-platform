# Tuần 1 (21/10 – 27/10/2026): việc cần làm

## Cả nhóm (buổi họp đầu, khoảng 90 phút)
- [ ] Chốt tên dự án và tên organization; kiểm tra tên trên GitHub và tên miền.
- [ ] Mỗi người nhận vai: Web & Red team / Hạ tầng & Dữ liệu / AI & Agent.
- [ ] Chốt kênh liên lạc (Zalo/Discord) và lịch: lên kế hoạch thứ Hai, demo nội bộ thứ Sáu.
- [ ] Tạo organization, repo `cti-platform`, giải nén bộ khởi động này vào repo, bật Projects, Wiki, Discussions.
- [ ] Bật bảo vệ nhánh `main` (PR + CI + 1 người duyệt), bật secret scanning.

## Hạ tầng & Dữ liệu
- [ ] Cài Docker trên máy Ubuntu, đặt `vm.max_map_count=1048575`.
- [ ] Chạy OpenCTI bằng docker-compose chính thức, `ELASTIC_MEMORY_SIZE=4G`; ghi RAM thực tế vào devlog.
- [ ] Bật thử connector MITRE ATT&CK và AlienVault OTX.

## AI & Agent
- [ ] Cài skill theo `.agents/skills/README.md` (đọc SKILL.md trước khi cài).
- [ ] Tạo notebook NotebookLM: STIX 2.1 intro, NIST SP 800-150, docs OpenCTI, 4 paper LLM-CTI.
- [ ] Chạy Gemini Deep Research với prompt trong `docs/prompts/deep-research.md`; lưu vào `docs/research/`.

## Web & Red team
- [ ] Khám phá giao diện OpenCTI (trang demo công khai hoặc bản lab), chụp màn hình các màn chính.
- [ ] Phác thảo 3 màn trang SME: Tổng quan, Tra cứu IOC, Lỗ hổng ảnh hưởng.
- [ ] Liệt kê ý tưởng chiến dịch giả lập cho lab (phishing domain, C2 bằng MITRE Caldera).

## Cuối tuần
- [ ] Viết devlog tuần đầu tiên theo TEMPLATE.md.
- [ ] Bản nháp đề cương (dựa trên tài liệu khung) gửi cả nhóm đọc.

## Bổ sung (bản cập nhật 22/10)
- [ ] Đưa bản cập nhật này lên GitHub bằng Pull Request đầu tiên (xem hướng dẫn trong chat).
- [ ] Chạy thử `python scripts/create_issues.py --repo <org>/cti-platform`, đọc kỹ, rồi chạy lại với `--apply`.
- [ ] Đưa `docs/wiki/Home.md` và `docs/wiki/Tu-dien-CTI.md` lên tab Wiki.
- [ ] Cả nhóm đọc và sửa bản nháp đề cương, điền tên, MSSV, giảng viên.
