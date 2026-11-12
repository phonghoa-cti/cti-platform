# X01-C4 adapter — review độc lập của Leader, 11/11/2026

Kết luận: **NEEDS_REWORK R1**, chưa nghiệm thu task `X01-C4-ADAPTER-IMPLEMENT`.

## Phạm vi và bằng chứng đã đối chiếu

- Báo cáo request `bc0b26ba-5394-4e62-aa4d-a50fdcdc57f6`, thread `c2b66412-c530-4848-b174-05c8abc2923c`.
- Target `cti-x01-c4-adapter`, branch `feat/x01-c4-adapter-20261111`, HEAD `e5e6751c7c1b35cc22e96c8765be2ee4f2f2a521`.
- Base/source `cti-x01-c4-retrieval`: `d97f96362edcd92e87fc69cfa20a563109cec550`.
- Leader xác nhận source/target sạch, diff đúng 7 file `+524/-11`, diff-check exit 0. Không sửa code sản phẩm.
- Đọc research, brief, Leader plan, AGENTS, spec X01 và phần code/test thay đổi. Giữ phương án tách report khỏi knowledge, tái sử dụng retry/fallback.
- Manifest worker: 8/8 khớp; SHA-256 `a16a74a6c66fb04b5e1d0620b05fab991b8e1362f1237e045fc9c194c5b1deb2`.
- JUnit worker tại HEAD: 428 tests, 0 failure/error/skip. Đây là evidence worker đã kiểm hash, **không phải 428 test Leader vừa chạy**.
- Đã đọc code demo và so sánh C2/C3, không chạy lại suite/build không cần thiết. Các báo cáo lịch sử đã accepted không giao/kiểm lại.

## R1 — metadata response sai UTF-8 thoát khỏi vòng retry/fallback (mức quan trọng)

Vị trí: `extractor/phonghoa_extractor/llm_adapter.py:274–277`, `_bounded_metadata()`; caller `_consume_response()` / `_handle_provider_error()`; vòng `_run_provider()` chỉ bắt `_RetryableError` sau khi nhận response.

Tái hiện bằng provider giả lập trả `ProviderResponse(status="completed", model_id="CTI_METADATA_NOT_FOR_LOG_\\ud800", ...)`, hoặc `status="error", error_code` có cùng ký tự surrogate, `retryable=True`. Chuỗi trong probe chứa surrogate thật theo escape Python, không phải sáu ký tự chữ. `value.encode("utf-8")` ném `UnicodeEncodeError` trước kiểm response hữu hạn. Provider chỉ được gọi một lần; response thứ hai không được dùng, không có fallback sau hai response hỏng. Lỗi tồn tại sẵn ở seam dùng chung C2/C3 và được C4 mới kế thừa; không gọi đây là regression mới của C2/C3.

Probe Leader `x01-c4-adapter-leader-review/test_c4_response_metadata.py` gồm 3 config × 2 trường × 2 chế độ recovery/exhaustion. Chạy mới trên HEAD: **12 failed, exit 1**, cùng nguyên nhân `UnicodeEncodeError`.

Lệnh từ root, PYTHONPATH `root/cti-x01-c4-adapter/core;root/cti-x01-c4-adapter/extractor`:

```text
cti-platform-start/.venv/Scripts/python.exe -X utf8 -B -m pytest -p no:cacheprovider -o addopts= -q --tb=short x01-c4-adapter-leader-review/test_c4_response_metadata.py
```

Log: `x01-c4-adapter-leader-review/metadata-probe-red.log`.
Probe SHA-256: `52DC1FBA95B55D365B34489DA7F4C62887566283BE5A06E776EC98681DDD6792`.

## Gói sửa cụ thể

CTI AI Agent / Sol medium, một worker trong target hiện có, không giao tiếp. Tái dùng nghiên cứu/contract đã chốt; sửa nhỏ validation metadata của seam chung để surrogate trả `_RetryableError("invalid_response")`, không chứa raw value. Giữ semantics response hợp lệ và terminal refusal/incomplete/error hiện có; không bắt rộng toàn pipeline để che lỗi lập trình.

- Cho phép sửa `extractor/phonghoa_extractor/llm_adapter.py`, `extractor/tests/test_llm_adapter.py`; `docs/PROGRESS.md` chỉ cập nhật bằng chứng nếu cần.
- Viết regression RED→GREEN trong repo cho model_id/error_code sai UTF-8; giữ nguyên probe/log/review của Leader và source tree.
- Chạy nguyên probe 12 ca; hai file `test_llm_adapter.py` + `test_ttp_audit.py`; vì sửa seam chung, chạy thêm `test_llm_cli.py`, `test_eval_cli.py`; Ruff check/format các Python file đổi và diff-check.
- Chạy lại script `x01-c4-adapter-evidence/compare_c2_c3.py` với source/target để giữ 6 artifact hợp lệ cũ. Không lặp toàn 428/full repo/official asset/UI khi không có failure hay concern mới.
- Sau commit cục bộ: ghi exact SHA/diff/exit/count, hash probe trước/sau, status source/target; cập nhật `PHONG-HOA-X01-C4-ADAPTER-RESULT.md`, thêm evidence `x01-c4-adapter-evidence/rework-r1/` và manifest đã tự kiểm. Giữ evidence cũ, ghi rõ kết quả nào trước/sau rework.
- Không network/model/secret/DB/listener/lab/push/PR/merge/deploy; không sửa RUNS hoặc tài liệu Leader. Nếu blocker cùng nguyên nhân sau hai cách thử, báo đúng bằng chứng.

Đạt khi 12 probe xanh, Unicode metadata không thoát exception thô, retry-success đúng 2 calls, exhaustion đúng fallback 2 calls, request object giữ nguyên và không lộ marker; regression/compatibility đạt, tree sạch.

## Nối việc và giới hạn

Sau R1, Leader nghiệm thu rồi nối nghiên cứu lát evaluator C4 theo next_on_accept hiện có. Chưa mở nghiên cứu phụ thuộc khi R1 chưa đạt. Dự án vẫn active; model quality, semantic TTP, corpus thật, evaluator/reporter C4, OpenCTI/lab/production chưa xác minh.

Đã đối chiếu threads: không có Leader khác đang xử lý; thread adapter idle sau báo cáo. Lịch `79621896-f322-47a8-80d7-072739a2314b` vẫn enabled, 30 phút/startup; lần 12:26 Việt Nam completed/NOTHING NEW, lần kế 12:56. Bằng chứng này chỉ xác nhận lịch chạy, không chứng minh phục hồi việc bỏ dở hoặc Stop hook cưỡng chế.
