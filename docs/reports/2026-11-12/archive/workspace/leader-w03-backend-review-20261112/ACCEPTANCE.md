# Nghiệm thu báo cáo QA Backend W03 — 12/11/2026

Chấp nhận báo cáo QA request1288c486-dc20-4265-92da-dc462ded45ba. **Không chấp nhận Backend candidate a49486caf39942019259e41514457bdb85498347.**

Leader đọc cves.py/technologies.py và chạy lại nguyên3 QA probes trên đúng candidate bằng .venv Python, PYTHONPATH candidate + core, pytest config/root ghim đúng; bytecode/cache tắt. Kết quả mới3failure assertion,0pass,exit1 trong0,77s. HEAD trước/sau đúng, git status rỗng. Raw probe-run.log/probe-results.xml.

B1: schema thiếu audit/migration/index vẫn200. B2: URL không hostname hoặc hostname có whitespace vẫn200. Tất cả expected503 cves_unavailable. Các assert non-mutation trước status đều qua; probe B1 chỉ so filebytes nên không suy rộng thành bằng chứng không ghi mọi chế độ WAL. B2 so SQL snapshot. Không chứng minh bypass quyền hay khai thác thực tế; đây là vi phạm fail-closed/contract.

Không chạy lại41/345tests hoặc5wire fixtures vì chưa đổi mã, các mục đó vẫn theo bằng chứng QA/Backend. Chỉ chạy3probe thiếu xác minh độc lập; không ghi chúng PASS. QA acceptance khác product acceptance.

Rework chốt tại PHONG-HOA-W03-BACKEND-REWORK-BRIEF-20261112.md. Giữ lượt Frontend b9085460-b667-4605-a7b9-88ef556930f4 đang chạy, không gửi lại. Backend sửa trong thread/tree cũ. W03 gateway/browser/feed/lab/production chưa được nghiệm thu.
