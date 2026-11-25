# X01-ATTACK — Leader review implementation R1/R2

Ngày 11/11/2026. Kết luận: **NEEDS_REWORK**, chưa nghiệm thu X01-ATTACK-IMPLEMENT.

## Đối tượng và bằng chứng

- Request đã trả: 25e1b0bd-7b30-4763-acd0-153a93555191.
- Thread giữ nguyên: 9f96a7bd-dc43-42c5-8406-9c04903eeb3e; owner CTI AI Agent, Sol medium theo cấu hình hiện có.
- Tree: `$WORKSPACE\cti-x01-attack-offline`.
- Branch feat/x01-attack-offline-20261111; base 8694fa7244d181f421bb2733ded7bf9ae218ea93; reviewed HEAD **a5663b12d37bcec6a75b639409096fe4943192fd**.
- Đã đọc code mới, tests và hợp đồng Leader; diff 8 file +1252/-1 đúng scope; Git tree sạch; diff-check base..HEAD exit 0. Source tree vẫn sạch tại base.
- Manifest đối chiếu **29/29 khớp** (28 evidence files và báo cáo); đọc log regression 122 pass, không chạy lại regression trong review này.
- Leader chạy mới catalog: **89 passed**, exit 0, 1.53s.
- Probe độc lập: **9 failed / 4 passed**, exit 1, 0.58s. Đây là lỗi chưa được bộ test hiện có phát hiện.
- Probe: `$WORKSPACE\leader-x01-attack-review\test_attack_catalog_leader_r1.py`.
- Probe SHA256 **688B06F844B0DAA96E902AB73A9737517D0D2975D04C850965F3C54C5BC9CC35**.
- Log Leader: `leader-x01-attack-review/catalog-current-head.log`, `leader-x01-attack-review/probe-red.log`.

## R1 — equality Python làm mất xung đột kiểu JSON (mức vừa, phải sửa)

Vị trí: `extractor/phonghoa_extractor/attack_catalog.py:355-358`, _select_version.

Hai object cùng STIX id/cùng modified, chỉ khác field phụ dạng lồng nhau `{"nested":[true]}` và `{"nested":[1]}`, bị coi là exact duplicate vì Python `True == 1`. Tương tự false/0. Loader chấp nhận snapshot trái quy tắc “toàn bộ object JSON bằng nhau về cấu trúc”; đáng lẽ phải duplicate_conflict. Field không dùng để tạo record vẫn phải được so theo hợp đồng, không được bỏ qua.

Probe tái hiện 8/8 tổ hợp: attack-pattern/relationship × true/1 hoặc false/0 × hai thứ tự object. 4 ca đối chứng duplicate thật với thứ tự key khác vẫn đạt.

Sửa nhỏ nhất: so toàn bộ JSON theo kiểu JSON, đệ quy object/list, bỏ qua thứ tự key, phân biệt boolean với number ở mọi độ sâu. Không stringify/coerce thành chuỗi chung hoặc bỏ field; xử lý Decimal của parser đúng, không đổi hợp đồng numeric chỉ để sửa bool. Cùng thời điểm khác payload phải duplicate_conflict cho cả record và relationship; exact duplicate thật tiếp tục collapse. Giữ quy tắc timestamp precision/lifecycle hiện có.

## R2 — đường dẫn NUL làm thoát lỗi nội bộ (mức vừa, phải sửa)

Vị trí: `extractor/phonghoa_extractor/attack_catalog.py:155-164`, _read_snapshot.

`load_catalog(Path("private-review-marker\u0000.json"), valid_synthetic_pin)` trên Windows/Python 3.12 trả ValueError("embedded null character"), không phải AttackCatalogError. Code chỉ bắt OSError nên input đường dẫn không hợp lệ vượt cơ chế mã lỗi an toàn.

Sửa ở biên file I/O bằng validation hoặc bắt lỗi đường dẫn cụ thể phù hợp; trả **snapshot_io_error**, str/repr chỉ chứa mã. Không bọc toàn bộ loader bằng catch-all; giữ missing path → snapshot_not_found, pin invalid phải bị từ chối trước I/O. Thêm regression vào repo.

## Scope rework và nghiệm thu

Tái dùng nghiên cứu, brief và PHONG-HOA-X01-ATTACK-LEADER-PLAN.md; đây là sửa hai lỗi trong hợp đồng đã giao, không cần mở nghiên cứu mới.

Chỉ sửa attack_catalog.py, test_attack_catalog.py và docs/PROGRESS.md để ghi tiến độ. Cập nhật PHONG-HOA-X01-ATTACK-RESULT.md và evidence trong x01-attack-evidence/rework-r1-r2 (giữ evidence cũ). Không sửa probe/log/review/plan/RUNS của Leader; không sửa fixture/ADR/README nếu không có nhu cầu trực tiếp từ R1/R2. Nếu phát hiện cần phạm vi khác, báo lý do cụ thể. Một worker, không giao bot/subagent khác.

Các bước:
1. Xác nhận HEAD/tree trước sửa; chạy nguyên probe Leader để có RED mới. Thêm regression repo rồi RED trước code.
2. Sửa R1/R2 nhỏ nhất; GREEN probe **13/13**, toàn bộ catalog suite và regression liên quan nếu thực sự đụng phần khác. Vì adapter/eval/grounding không đổi, không cần lặp 122 hoặc full suite/UI/browser.
3. Ruff check/format file Python đổi; git diff --check a5663b12d37bcec6a75b639409096fe4943192fd..HEAD và working tree. Import vẫn chỉ đúng source tree.
4. Commit cục bộ sạch; báo base/HEAD/diff, raw command/exit/count, probe hash không đổi, manifest; tự review các nhánh lỗi và trả Leader.

Lệnh probe, cwd workspace Leader:
~~~powershell
& '.\cti-platform-start\.venv\Scripts\python.exe' -X utf8 -B -m pytest -o addopts='' -p no:cacheprovider leader-x01-attack-review/test_attack_catalog_leader_r1.py -q --tb=short
~~~

Lệnh catalog, cwd tree triển khai:
~~~powershell
& '..\cti-platform-start\.venv\Scripts\python.exe' -X utf8 -B -m pytest -o addopts='' -p no:cacheprovider extractor/tests/test_attack_catalog.py -q
~~~

Không đổi shared venv/dependency/lock, không mạng, model, secret, dữ liệu thật, lab, push/PR/merge/deploy. Sau sửa vẫn chỉ là catalog fixture tổng hợp; MITRE thật, semantic TTP, C4/RAG, W05/OpenCTI/lab/production chưa kiểm chứng.

Leader giữ task mở đến khi nghiệm thu sửa lỗi, sau đó mới nối bước kế.
