# X01-INGEST-BROWSER-INTEGRATION — brief chuẩn bị

Ngày 11/11/2026. **Chỉ chuẩn bị; importer và demo tích hợp cùng lượt qua browser chưa được chạy.**

## Mục tiêu và base

- Sau khi `X01-INGEST-QUEUE-IMPLEMENT` được Leader nghiệm thu, chứng minh một file TXT hoặc PDF synthetic đi qua: producer CLI → importer CLI → UI W05 chọn/lưu/duyệt bằng **trình duyệt tích hợp** → STIX, trên cùng một SQLite.
- Base triển khai: commit importer đã được nghiệm thu (SHA hiện chưa có, không đoán); target dự kiến `<root>\cti-x01-ingest-browser-integration`, branch `feat/x01-ingest-browser-integration-20261111`.
- Source chỉ đọc, phải giữ sạch: `cti-x01-w05-stix-e2e@cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`; `cti-x01-ingest-local@8a16758601647fb3dbf935abecc2435f3b7a3fb6`.
- Không chép parser/model sang target, không sửa hai source, không thêm dependency/automation browser, không Internet/cloud/lab/OpenCTI/push/merge/deploy.

## Phần đã chứng minh và phần chưa chứng minh

- Đã chạy ở source W05: `tools/local_integration/tests/run_stix_e2e.py` tạo draft bằng hai CLI cũ, review qua HTTP và xuất STIX trên một DB; `LocalRun` quản lý JWT/API/gateway/UI/temp/cleanup.
- Đã chạy ở producer: `extractor/ingest/run.py::main/_build_envelope/_publish_envelope` dùng `local_ingest.py::ingest_local_file` để tạo envelope TXT/PDF có raw/canonical hashes và page ranges.
- Đề xuất mới: thay seed `draft/run.py` + `draft/store.py save` bằng producer CLI + importer CLI mới, rồi thao tác UI thật trong cùng `LocalRun`; việc này **chưa chạy**, không kế thừa PASS cũ.

## Điểm tái sử dụng chính xác

- `tools/local_integration/runner.py::LocalRun`, `_run_seed_cli`, `_save_stix_e2e_fixture`, `start`, `close`: giữ vòng đời và `db_path`; đổi seed theo tham số input/creator/fault, không tạo runner thứ hai.
- `tools/local_integration/gateway.mjs` và `local_settings.py::make_local_settings`: dùng nguyên gateway same-origin/JWT; chỉ dùng fault refresh đã có.
- `tools/local_integration/tests/run_stix_e2e.py::file_inventory`, `database_state`, `run_export`, `assert_port_released`: tái dùng kiểm read-only/audit/export/cleanup; tách helper nếu cần, không sao chép logic.
- `portal/web/components/draft-review-app.tsx` và `draft-review.tsx`: không đổi; browser dùng checkbox `Lựa chọn duyệt: <IOC>`, nút `Lưu lựa chọn`, `Duyệt bản nháp`, `Thử lại`.
- Producer chỉ gọi CLI `<producer>\extractor\ingest\run.py`; fixtures đọc rồi copy vào temp: TXT từ `E2E_SOURCE_BYTES`, PDF từ `<producer>\extractor\tests\fixtures\two-text-pages.pdf`.
- Importer gọi CLI mới `<target>\extractor\ingest_queue\run.py`; provenance đọc bằng `get_ingest_provenance`; STIX dùng `extractor/draft/stix_export.py export-approved`/`export_approved` hiện có.

## Lát cắt triển khai nhỏ nhất

1. Preflight xác nhận target đúng commit importer đã nghiệm thu, producer đúng SHA, cả hai source sạch; dùng Python 3.12.13 trong từng checkout, không dùng PATH Python.
2. Mở rộng `LocalRun("ingest-browser-stix", start_ui=True)` nhận `input_path`, `producer_root`, `created_by_subject`; copy input synthetic vào `temp_root`, không sửa fixture nguồn.
3. `_save_ingest_browser_fixture`: producer CLI ghi `envelope.json`; importer CLI nhập envelope vào `self.db_path`; parse stdout hữu hạn để lấy đúng một `draft_id`; retry cùng creator phải trả duplicate cùng ID.
4. Script E2E in URL/draft ID/hash summary, giữ `LocalRun` tối đa 300 giây và chờ một dòng stdin. Mở URL bằng trình duyệt tích hợp; không dùng Playwright/CDP/script click khác.
5. Browser mở đúng draft, bỏ IOC thứ nhất, lưu, duyệt bằng subject khác creator; fault refresh thì bấm `Thử lại`, không POST lại quyết định.
6. Khi browser xong, gửi newline cho chính process E2E; nó đọc cùng DB/provenance/audit, chạy STIX CLI, ghi summary không chứa raw text/subject; `LocalRun.close` dừng đúng process và xóa temp.

## Bất biến và kiểm hash/audit

- Trước browser: SHA-256 byte input không đổi; envelope `raw_sha256` khớp file; `canonical_text_sha256` khớp UTF-8 canonical text; `draft.source.sha256` và API `source.sha256` cùng hash canonical.
- Provenance: `envelope_sha256`, `raw_sha256`, `canonical_text_sha256`, format/page ranges và `draft_id` khớp envelope; retry không tăng số draft/provenance/audit.
- Sau lưu: `draft_selection_audit` có đúng một bản ghi version 1, indices `[1]`, `selected_sha256` khớp response; `payload_json`/`items.keep` và file input/envelope bất biến.
- Sau duyệt: creator tự duyệt nhận 403 và DB bất biến; analyst/admin khác creator tạo đúng một `draft_audit` action `approve`, review version 2, selection version/indices/hash khớp bản lưu.
- STIX: export chỉ đọc DB; bundle SHA khớp stdout, chứa IOC thứ hai nhưng không IOC bị bỏ/raw source/evidence/subject; provenance STIX khớp source hash, draft ID, approved audit ID, review/selection version/hash.

## Allowlist dự kiến

- Sửa: `tools/local_integration/runner.py`, `tools/local_integration/tests/test_runner.py`, `tools/local_integration/README.md`.
- Sửa hoặc tách helper: `tools/local_integration/tests/run_stix_e2e.py`.
- Tạo: `tools/local_integration/tests/run_ingest_browser_stix.py`, `PHONG-HOA-X01-INGEST-BROWSER-INTEGRATION-RESULT.md`; evidence dưới `x01-ingest-browser-integration-evidence/` ngoài target nếu Leader giao.
- Không sửa `portal/**`, `portal_api/**`, importer/store/STIX/producer, dependency/lock, RUNS hay Leader plan; phát hiện cần sửa thì báo blocker bằng file/hàm và dừng mở rộng.

## Ma trận 8 ca cho người không đọc code

| Ca | Thao tác nhìn thấy | Đạt khi |
|---|---|---|
| TXT happy | Nạp TXT, mở URL/draft | Tên nguồn, hai IOC, source hash đúng; một draft/provenance |
| PDF happy | Nạp PDF hai trang | Canonical text/page ranges/hash đúng; UI mở cùng draft |
| Nhập trùng | Chạy importer lại cùng envelope/creator | Báo duplicate cùng ID; counts/audit không đổi |
| Tự duyệt bị chặn | Phiên subject bằng creator bấm duyệt | UI báo không đủ quyền/403; không có decision audit |
| Lựa chọn bỏ | Bỏ IOC đầu, bấm `Lưu lựa chọn` | UI báo đã lưu; reload vẫn chỉ chọn IOC thứ hai |
| Lỗi refresh sau lưu | Fault 503 sau POST lưu | UI nói đã ghi nhưng chưa tải lại; `Thử lại` phục hồi, chỉ một selection audit |
| Lỗi refresh sau duyệt | Fault 503 sau POST duyệt | UI nói quyết định đã ghi; retry chỉ GET, đúng một decision audit |
| Xuất đúng | Chạy export sau duyệt | Bundle/hash/count đúng, chỉ IOC đã chọn và audit/provenance khớp |

## Lệnh kiểm bắt buộc khi triển khai

```powershell
git -C <target> rev-parse HEAD; git -C <target> status --short
git -C <w05-source> rev-parse HEAD; git -C <w05-source> status --short
git -C <producer> rev-parse HEAD; git -C <producer> status --short
<target>\.venv\Scripts\python.exe -m pytest tools/local_integration/tests/test_runner.py -q
<target>\.venv\Scripts\python.exe -X utf8 -B tools/local_integration/tests/run_ingest_browser_stix.py --input-kind txt
# Khi script chờ: mở URL bằng trình duyệt tích hợp, làm đúng ca, rồi gửi newline cho cùng process để hậu kiểm/cleanup.
<target>\.venv\Scripts\python.exe -m ruff check tools/local_integration
<target>\.venv\Scripts\python.exe -m ruff format --check tools/local_integration
git -C <target> diff --check
```

Đầu ra thấy được: URL + draft ID + hash summary; UI có trạng thái lưu/duyệt/retry; JSON verifier có counts/source/selection/audit/bundle hashes; ảnh browser và manifest hash. PASS chỉ khi fresh exit/count và browser cùng run đều có; OpenCTI/lab/production vẫn UNVERIFIED.
