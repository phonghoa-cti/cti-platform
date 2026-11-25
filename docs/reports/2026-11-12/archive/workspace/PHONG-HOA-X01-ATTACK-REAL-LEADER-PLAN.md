# X01-ATTACK-REAL — nghiệm thu nghiên cứu và kế hoạch triển khai

Ngày 11/11/2026. Leader. Nghiên cứu request `2ac04017-e6fe-4e5f-8662-4ca9659a3a07` được chấp nhận trong phạm vi dữ liệu/brief, kèm quyết định giới hạn bên dưới. Chưa nghiệm thu `load_catalog()` với dữ liệu MITRE thật.

## Kết quả review có bằng chứng

- Source `cti-x01-attack-offline` giữ HEAD `4e894c37df3ad53c16022909ae6df113dd89aa04`, status sạch.
- Hai tài liệu khớp SHA-256 báo về: research `899F9D9208A93F127EFBF147307C6C946A927BA58F2A6D0DE844471D901555FE`; brief `DA85D9B56567D0A9A67B79E74C2CCACE3BA760449D021B086A096111493184D7`.
- Leader kiểm 5/5 hash trong manifest. Snapshot 55,277,605 bytes; SHA-256 `539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5`; Git blob SHA-1 `4acfc94abd56693ca590ccab493c087deaa7cfb5`.
- Leader chạy `leader-x01-attack-real-review/inventory_policy.py` bằng Python 3.12 của dự án, exit 0. Output `leader-x01-attack-real-review/inventory-policy.json`: 26,699 objects, 867 patterns, 706 active, 481 subtechnique edges; không phát hiện vi phạm các field/timestamp/boolean/reference/graph/domain/ID uniqueness đã đối chiếu. Metadata collection ghi Enterprise ATT&CK 20.1. Đây là inventory riêng, không import/bypass loader, không đổi bytes; không phải test compatibility sản phẩm và không đại diện validator STIX đầy đủ.
- Đã đọc trang release chính thức https://github.com/mitre-attack/attack-stix-data/releases/tag/v20.1 : release 05/11, liên kết commit `f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7`. Đã đối chiếu LICENSE từ URL raw cùng commit. Trang tag API và trang commit chi tiết không mở được qua công cụ web; không nhận là kiểm chữ ký tag/commit.
- LICENSE nguyên văn được lưu; riêng tệp NOTICE chưa xác minh. Không diễn giải lại giấy phép như tư vấn pháp lý.

Giới hạn phát hiện khi đọc script tải: `HttpClient.Timeout` với `ResponseHeadersRead` chưa chứng minh hạn 60 giây cho toàn bộ vòng đọc body đồng bộ. Tệp đã tải xong và hash hợp lệ nên không cần tải lại; script đó không được nghiệm thu để tái sử dụng làm downloader. Lát cắt tiếp không chạy/sửa script tải hay thêm mạng.

## Quyết định kỹ thuật

Chọn mở nhánh official nhỏ nhất trong loader stdlib hiện có; không thêm `stix2` hoặc TAXII. **Chỉ nhận đúng một bộ pin Enterprise v20.1 đã kiểm** trong đợt này, thay cho chấp nhận mọi metadata có hình thức URL giống MITRE. Đây là policy Phong Hỏa, không phải yêu cầu chung của STIX. Lợi ích: không gán nhãn official cho tệp bất kỳ chỉ vì caller tự đặt URL/hash. Đổi lại: thêm release khác cần review bộ pin mới.

Pin hợp lệ có đúng 7 trường sau; type string chính xác, không ép kiểu/strip/lowercase. Sai bất kỳ trường hoặc kiểu => `invalid_pin` trước mọi I/O. Giữ các ràng buộc `max_bytes` cũ. Synthetic giữ nguyên contract cũ.

```json
{
  "kind": "official",
  "version": "20.1",
  "sha256": "539a843a7b53ed9749740b2123dddae3726b1a4831841c32aca740b011b910b5",
  "source_url": "https://raw.githubusercontent.com/mitre-attack/attack-stix-data/f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7/enterprise-attack/enterprise-attack-20.1.json",
  "release_tag": "v20.1",
  "commit": "f59b03ecf828579d5f9e93683ce25b7e2e5fd9d7",
  "provenance": "mitre-attack-stix-data"
}
```

`kind` quyết định nhánh sau kiểm pin, không dựa custom field của tệp. Với pin official đã xác minh, root cần bundle/objects/member shape hiện có, không cần `x_phonghoa_provenance`. Synthetic vẫn bắt buộc root provenance cũ. Không thêm synthetic provenance vào MITRE bytes, không bỏ record khó hoặc giảm điều kiện lifecycle/graph. Không thay lookup semantics: `semantic_status="unverified"`, `operational_draft_eligible=false`.

## Giao một worker triển khai

Owner: CTI AI Agent, Sol medium theo cấu hình hiện hành; không giao tiếp agent/bot khác. Leader review riêng sau báo cáo.

Root tuyệt đối: `$WORKSPACE`.

- Source chỉ đọc: `<root>\cti-x01-attack-offline`, exact base `4e894c37df3ad53c16022909ae6df113dd89aa04`.
- Tạo worktree riêng `<root>\cti-x01-attack-official`, branch `feat/x01-attack-official-20261111` từ exact base. Nếu đã tồn tại, kiểm owner/HEAD/status rồi báo khác biệt; không reset/xóa/chiếm tree khác.
- Interpreter dùng chung chỉ đọc: `<root>\cti-platform-start\.venv\Scripts\python.exe`; Ruff cùng Scripts. Không cài package hoặc đổi venv; chạy với cwd tree mới, kiểm import module nằm tree mới.
- Asset chỉ đọc: `<root>\x01-attack-real-research-evidence\enterprise-attack-20.1.json` và `MITRE-LICENSE.txt`. Không tải thêm, không sửa/copy snapshot 55 MB vào repo.
- Đọc AGENTS.md, docs/PROGRESS.md, spec X01, ADR0004 trên base; nghiên cứu/brief mới và kế hoạch này. Kế hoạch này chốt phần pin/tree/tests còn mở của brief; phạm vi code đã được giao, không cần chờ người dùng duyệt lại.

File code/doc được sửa trong tree mới:

1. `extractor/phonghoa_extractor/attack_catalog.py`.
2. `extractor/tests/test_attack_catalog.py`; được thêm `extractor/tests/test_attack_catalog_official.py` nếu giúp tách kiểm asset thật.
3. `extractor/tests/fixtures/attack_official/` chỉ metadata JSON pin, README và LICENSE.txt nguyên văn, không snapshot hay tệp thực thi.
4. `docs/adr/0004-x01-restricted-attack-catalog.md` cập nhật trạng thái theo quyết định một release; `docs/PROGRESS.md` ghi đúng bằng chứng/giới hạn.

Không đổi adapter/eval/grounding/store/API/UI/W05/lock/dependencies, RUNS, probe hoặc evidence Leader, các worktree/nguồn cũ. Không mạng, model, secret, lab, listener, DB, push/PR/merge/deploy.

## TDD và kiểm chứng cần chạy

- Test trước code: RED positive official load trên bytes thật ở base; không nhận các test vốn đã từ chối official pin là bằng chứng RED cho tính năng. Ghi command/exit/summary thật.
- Test invalid pin theo từng field: missing/None/list/dict/bool/number, metadata khác, hash uppercase, mutable branch URL, repo/domain/path/version khác, query/fragment/credentials/percent-escape. Chứng minh từ chối trước `_read_snapshot`, không traceback/echo marker; không cần tạo hàng loạt kiểm trùng lặp không thêm giá trị.
- Giữ 104 regression catalog cũ. Synthetic metadata và root provenance không nới lỏng; bảo toàn bool-vs-number, JSON duplicate, timestamp, lifecycle, parent và immutable records.
- Real asset dùng path cấu hình trong test/evidence, không hardcode đường dẫn máy vào mã sản phẩm. Các test cần asset có thể skip rõ ràng khi không cung cấp; **lượt nghiệm thu phải cung cấp path và thực chạy, không skip các ca asset thật**. Dùng fixture module-scope nếu cần tránh parse 55 MB nhiều lần không có ích.
- GREEN qua public `load_catalog`: đủ 867 record, 706 active, 161 inactive; 497 subtechnique; `T1001` active, `T1001.001` active với parent `(T1001,)`, `T1002` inactive, `T0000` unknown, malformed input not_checked. Mọi kết quả vẫn unverified/eligible false; mapping bất biến.
- Real pin + file bytes bị sửa => `snapshot_hash_mismatch`; bounded read dưới size thực => `snapshot_too_large`; I/O taxonomy cũ. Dùng bản tạm thuộc test, giữ nguyên asset nguồn. Official root không cần custom provenance được chứng minh bằng file thật, không giả hash official cho fixture nhỏ.
- Test no-egress khi load/lookup bằng chặn các socket connection entry points trong phạm vi test, kết hợp kiểm diff không thêm HTTP/TAXII/downloader. Đây là kiểm đường code này, không tuyên bố toàn OS bị cô lập mạng.
- Run targeted catalog suite, Ruff check/format, `git diff --check`; không lặp full122/fullsuite/UI/build vì các module khác không đổi. Tất cả artifact từ exact HEAD cuối; kiểm source vẫn base và sạch, implementation commit cục bộ Conventional Commit và tree sạch.

Lệnh pytest cốt lõi (giải thích: chạy các ca catalog trong tree mới; bật path asset theo cách test đã tài liệu hóa):

```powershell
& '..\cti-platform-start\.venv\Scripts\python.exe' -X utf8 -B -m pytest -o addopts='' -p no:cacheprovider extractor/tests/test_attack_catalog.py extractor/tests/test_attack_catalog_official.py -q
```

Nếu gộp test vào file cũ thì bỏ tên file mới khỏi command. Ghi chính xác cách cung cấp asset và số passed/skipped; không che missing asset thành PASS compatibility.

## Đầu ra

- `<root>\PHONG-HOA-X01-ATTACK-REAL-RESULT.md`.
- `<root>\x01-attack-real-evidence\`: RED/GREEN logs, command/cwd/interpreter/exit, demo public API, source/base/HEAD/diffstat, SHA256 manifest. Không lưu lại snapshot lớn; tham chiếu hash/path asset có sẵn, kèm license nhỏ nếu cần.
- Report trả base/HEAD/branch/tree sạch, test counts, mã nguồn/path import đúng tree, dữ liệu nguyên bytes/hash trước-sau, giới hạn và hướng tiếp theo. Inventory nghiên cứu tách khỏi test sản phẩm.

Vẫn UNVERIFIED sau lát cắt: release khác, chữ ký tag/commit, semantics TTP/corpus/model thật, C4/RAG/adapter wiring, OpenCTI/lab/production. Sau nghiệm thu, Leader chọn nghiên cứu cách nối catalog vào kiểm tra TTP ngoại tuyến theo spec; không tự gọi model hoặc mở quyền ghi.
