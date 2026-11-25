# X01 local ingest — nghiệm thu nghiên cứu

Ngày: 11/11/2026. **PASS tài liệu sau R1–R4 và các quyết định triển khai của Leader**, không phải PASS implementation.

- Request đã kiểm: `43f87b3c-05b9-4deb-a1a8-a2d3891af726`.
- Research: `PHONG-HOA-X01-LOCAL-INGEST-RESEARCH.md`, SHA-256 `09c845f62cab64bf5babdeae8dd2ce5c8144cef902744344ec09417b57d2f237`.
- Brief: `PHONG-HOA-X01-LOCAL-INGEST-IMPLEMENTATION-BRIEF.md`, SHA-256 `38a4dab5b53122ea94166afc6c86faebc2abe48227a2722b878b7105962e5462`.
- Source kiểm trực tiếp: `cti-x01-gold-pilot`, HEAD `1fc3986e0c3baef1f99e6c3497cda84148cb9cb0`, status sạch; target `cti-x01-ingest-local` chưa tồn tại.

| Finding | Kết quả review |
|---|---|
| R1 | Đã đổi sang hard-link no-clobber, không replace fallback; có race/winner/input preservation và cleanup trong acceptance. |
| R2 | Có caps exact, một PDF child, timeout/reap/result bounds, lỗi hữu hạn và giới hạn RAM/network rõ. Leader bổ sung snapshot đầu vào, read capped và xử lý lỗi nền trong plan. |
| R3 | Có canonical literal riêng, phân biệt newline legacy, kiểm no-text trước join, page range rỗng/separator. |
| R4 | Có exact file scope, dependency pin/hash, target interpreter và checks/evidence. Leader chốt bootstrap, ADR theo AGENTS và quyền commit local trong plan; không mở PR/phát hành. |

Leader mở trực tiếp [PyPI metadata 7.0.1](https://pypi.org/pypi/pypdf/7.0.1/json): version, BSD-3-Clause, Python >=3.10 và hai distribution hash khớp tài liệu. Wheel `pypdf-7.0.1-py3-none-any.whl`, 416136 bytes, SHA-256 `6131b764b046282357037309e7ef2a1b7679d4a5c53eed3db2bfbf7c673ddc2b`; chưa tải hoặc cài. Metadata có `yanked=false`, `vulnerabilities=[]` tại lần đọc; không suy thành bảo đảm không có lỗ hổng.

Không chạy lại test sản phẩm vì chỉ tài liệu thay đổi. Probe race/newline/empty-join từ review trước vẫn là bằng chứng cho lý do sửa contract, không là bằng chứng PDF implementation. Chưa kiểm bytes package, parser/runtime, hard memory isolation, PDF thật hoặc chất lượng dữ liệu.

Bước tiếp được giao theo `PHONG-HOA-X01-LOCAL-INGEST-LEADER-PLAN.md`: CTI AI Agent/Sol medium triển khai riêng, một người một tree, kiểm thử fixture tổng hợp và bàn giao để Leader kiểm độc lập. Danh sách cuộc đã xem: chỉ cuộc Leader hiện tại đang chạy; không có worker ingest cần tránh trùng. Lịch tự tiếp tục vẫn enabled, lần gần nhất kết thúc NOTHING NEW; không coi lịch/receipt là worker sống.
