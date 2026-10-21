# Skill trong repo

opencode đọc skill từ `.opencode/skills`, `.claude/skills` và `.agents/skills`; Antigravity đọc từ `.agents/skills`.
Đặt mọi skill vào thư mục này để cả hai agent dùng chung. Giữ tối đa 10–15 skill.

## Skill tự viết
| Skill | Dùng khi |
|---|---|
| cti-thesis-conventions | Xử lý IOC, điểm, TLP, viết tài liệu |
| stix-connector | Thêm nguồn dữ liệu mới |

## Skill tải về (đọc kỹ SKILL.md trước khi cài — skill có thể chứa lệnh độc hại)
| Nguồn | Skill nên lấy | Lệnh |
|---|---|---|
| obra/superpowers | brainstorming, writing-plans, test-driven-development, systematic-debugging, requesting-code-review | opencode: bảo agent đọc và làm theo `.opencode/INSTALL.md` trong repo superpowers |
| mattpocock/skills | grill-me, to-spec, handoff, code-review | `npx skills add mattpocock/skills` |
| vercel-labs/skills | find-skills | `npx skills add vercel-labs/skills@find-skills` |
| mukul975/Anthropic-Cybersecurity-Skills (cộng đồng, không thuộc Anthropic) | building-threat-intelligence-platform, building-threat-intelligence-feed-integration, automating-ioc-enrichment, building-ioc-enrichment-pipeline-with-opencti, building-attack-pattern-library-from-cti-reports, analyzing-threat-actor-ttps-with-mitre-attack | `npx skills add https://github.com/mukul975/Anthropic-Cybersecurity-Skills --skill <ten>` |

## Skill cho giao diện (vai Web & Red team)
Luôn đọc `docs/design/DESIGN.md` trước khi làm giao diện.

| Nguồn | Skill | Ghi chú | Lệnh |
|---|---|---|---|
| anthropics/skills | frontend-design | 1,0M lượt cài; hướng dẫn tránh giao diện "template" | `npx skills add anthropics/skills@frontend-design` |
| pbakaus/impeccable | impeccable | ~83,8k sao; có lệnh critique/audit/polish; tự đọc DESIGN.md; 1 trong 3 bộ quét báo Warn | `npx skills add https://github.com/pbakaus/impeccable --skill impeccable` |
| vercel-labs/agent-skills | web-design-guidelines | Soát code giao diện theo hướng dẫn của Vercel (truy cập mạng để lấy quy tắc mới nhất) | `npx skills add https://github.com/vercel-labs/agent-skills --skill web-design-guidelines` |
| shadcn/ui | shadcn | Dùng đúng component shadcn | `npx skills add shadcn/ui@shadcn` |

Cân nhắc thêm: `leonxlnx/taste-skill@design-taste-frontend` (rất phổ biến nhưng 2/3 bộ quét báo Warn — đọc kỹ thư mục scripts trước khi cài).

## Nhật ký chỉnh sửa skill tải về
Ghi lại mỗi lần sửa một skill tải về: tên, ngày, sửa gì, vì sao.

| Skill | Ngày | Thay đổi | Lý do |
|---|---|---|---|
| | | | |
