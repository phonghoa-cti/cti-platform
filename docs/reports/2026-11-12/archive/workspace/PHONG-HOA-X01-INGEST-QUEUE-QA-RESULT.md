# Kết quả QA độc lập X01-INGEST-QUEUE

Ngày 11/11/2026. Target chỉ đọc: `cti-x01-ingest-queue` tại HEAD
`db36ec01b765dfd515c1d0ef13642a693b777172`, base
`cf9e6094f3e32f2e7e21c629ebc1ea5d628d376b`.

## Kết luận

**FAIL — chưa đủ điều kiện nối browser.** Hai test ingest mới đều đạt `26/26`, nhưng probe độc lập tái hiện một
lỗi hợp đồng đầu vào: ký tự điều khiển Unicode trong `display_name/source.name` vẫn được import và lưu. Không có
lỗi HIGH/CRITICAL trong phạm vi đã kiểm; finding này là **MEDIUM** vì tên nguồn là dữ liệu không tin cậy sẽ đi tới
reader/UI và có thể làm sai ranh giới dòng hoặc hiển thị/log downstream.

Không tuyên bố browser, OpenCTI, lab hoặc production đã đạt; các phần đó không chạy.

## Finding

### F1 — MEDIUM — bộ lọc tên nguồn bỏ sót Unicode control

- **Tiêu chí:** implementation brief dòng 43 yêu cầu `display_name` là UTF-8 không chứa control hoặc slash.
- **Source:** `extractor/phonghoa_extractor/ingest_queue.py:218-223`; điều kiện chỉ chặn code point `<32` và
  `U+007F`, nên bỏ sót C1 controls `U+0080..U+009F`. Đường gọi tại `:234` chấp nhận kết quả đó.
- **Tái hiện:** `probe_risks.py` tạo envelope synthetic có cả `input.display_name` và `draft.source.name` là
  `bad<U+0085>name.txt`, rồi gọi `save_ingested_envelope(..., created_by_subject="creator-control")`.
- **Mong đợi:** `IngestEnvelopeError(code="invalid_input_metadata")`, không thêm draft/provenance.
- **Thực tế:** trả `result="imported"`, tạo `draft_id=2`; DB `control-display-name.sqlite` lưu nguyên `U+0085`.
- **Bằng chứng:** `probe-risks.log`, exit `1`; DB synthetic `control-display-name.sqlite`.
- **Sửa tối thiểu:** đổi `_valid_name` để từ chối mọi ký tự không in được/control (ví dụ kiểm
  `char.isprintable()` cùng cấm `/` và `\`), và thêm regression cho ít nhất `U+0085`/`U+009F`; xác nhận DB không
  đổi khi bị từ chối. Không sửa implementation trong lượt QA này.

## Ma trận kiểm tra

| Kiểm tra | Trạng thái | Bằng chứng |
|---|---|---|
| Exact HEAD/base, target sạch trước/sau | PASS | `source-state.txt`; HEAD không đổi, status rỗng |
| Hai test ingest mới | PASS | `targeted-tests.log`: 26 passed, exit 0 |
| Migration race và rollback | PASS trong tập chạy | Test mới gồm hai migrator; probe DDL lỗi giữ `user_version=2` và schema cũ |
| Draft + provenance nguyên tử | PASS trong tập chạy | Test mới chứng minh provenance insert/commit failure không để orphan |
| Dedupe cùng creator / conflict creator khác | PASS trong tập chạy | Test library + CLI, gồm race hai writer/process |
| Creator nhập không tự approve | PASS | Probe giữ row `pending, version=0, decided_by=null` |
| Reader v2/v3 và provenance không ghi | PASS trong tập chạy | Test mới v2/v3; probe byte DB trước/sau provenance read giống nhau |
| Malformed JSON, UTF-8, depth, cycle | PASS trong tập chạy | Test mới phủ duplicate key, nonfinite, surrogate, depth, recursive mapping |
| Path samefile/UNC/ancestor reparse | PASS trong tập chạy | Test samefile; probe UNC và junction ancestor trả lỗi đóng |
| `display_name` không control | FAIL | F1: `U+0085` được import/lưu |
| Hostile TOCTOU/mapped drive/network isolation | UNVERIFIED | Ngoài phạm vi; path guard không phải hard sandbox |
| Full 553/UI/build | UNVERIFIED trong QA này | Không lặp theo brief; số 553 chỉ là báo cáo Backend |
| Browser/model/network/OpenCTI/lab/production | UNVERIFIED | Không chạy, không listener/cloud/secret |

## Lệnh và giới hạn

1. Python target 3.12.13 với `-B`, `PYTHONDONTWRITEBYTECODE=1`, pytest cache tắt và basetemp ngoài source:
   hai file ingest, `26 passed`, exit `0`.
2. Probe rủi ro `probe_risks.py`: 5 PASS, 1 FAIL, exit `1` có chủ ý khi có finding.
3. Không chạy demo `--rerun-owned`, full suite 553, regression UI/build hoặc browser.
4. Một lệnh cleanup thư mục pytest tạm bị môi trường từ chối ở bước tạo process; không đổi quyền hoặc vượt chặn.
   Thư mục này chỉ thuộc evidence QA và không tác động source.

## Không sửa source

Target giữ nguyên HEAD và `git status --short` rỗng trước/sau. Hai source W05/producer vẫn đúng SHA và sạch.
QA chỉ tạo báo cáo này cùng `x01-ingest-queue-qa-evidence/`; không sửa index/branch/RUNS/evidence Backend, không
push/PR/merge/deploy.
