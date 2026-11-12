# AI-EVAL-NEXT — nghiên cứu bước nối đánh giá C2/C3 ngoại tuyến

Owner CTI Research. Nghiên cứu và ghi hai tài liệu, chưa sửa code. Mục tiêu chọn lát cắt nhỏ tái sử dụng evaluator hiện có để so C1/C2/C3 bằng dữ liệu tổng hợp và phản hồi fake đã có. Không biến smoke test thành tuyên bố chất lượng model hoặc luận văn hoàn tất.

Workspace gốc: `$WORKSPACE`.

Đọc nghiên cứu còn phù hợp `PHONG-HOA-AI-NEXT-RESEARCH.md`, `PHONG-HOA-AI-IMPLEMENTATION-BRIEF.md`, `PHONG-HOA-AI-ADAPTER-RESULT.md`. Adapter đã được Leader nghiệm thu phạm vi offline ở SHA `ed24bd817de1e4633693d27f47e8e5fc629451ad`, tree `cti-platform-ai-llm-adapter`, branch `feat/x01-llm-adapter-offline-20261110`. Đọc đúng SHA: AGENTS.md, docs/PROGRESS.md, spec X01 liên quan, extractor/phonghoa_extractor/evaluate.py và llm_adapter.py, extractor/eval/run.py + README.md, extractor/tests/test_evaluate.py + test_eval_cli.py, dataset/GUIDELINE.md và synthetic-smoke. Không cần đọc nhánh API đang rework.

So tối đa 3 cách nối artifact vào evaluator; chọn 1 cách đơn giản, nêu file/hàm tái sử dụng. Đối chiếu nguồn chính thức cho metric/contract khi cần, dùng lại nguồn cũ còn đúng thay nghiên cứu lại toàn đề tài. Chốt cách giữ raw C2 để đếm false positives, dùng keep/evidence C3 để chấm, tách fallback C1 và lỗi/refusal khỏi thành công model, xử lý duplicate/normalization/empty gold/empty prediction/language/TLP. Chốt input/output/provenance/determinism và giới hạn dữ liệu tổng hợp. Không tự đặt mục tiêu chất lượng hoặc giả có corpus hai người gán nhãn; phần đó ghi chưa xác minh.

Chỉ ghi `PHONG-HOA-AI-EVAL-NEXT-RESEARCH.md` và `PHONG-HOA-AI-EVAL-IMPLEMENTATION-BRIEF.md` tại workspace gốc. Brief đủ để giao AI Agent Sol medium: exact base/tree, file scope, CLI/interface nếu cần, acceptance matrix có các ca lỗi quan trọng, demo offline, checks và giới hạn. Nếu thiếu quyết định kỹ thuật có thể đảo ngược thì chọn và giải thích, không hỏi user cho việc thường lệ.

Không sửa repo/RUNS/memory, không test code/implementation, không giao bot khác, không secret/network model/SQLite/cloud/lab/push/merge/deploy. Web nguồn công khai để nghiên cứu được phép. Báo số tiêu chí tài liệu tự kiểm, hash hai file và trạng thái tree; phân biệt nghiên cứu với code đã chạy. Leader sẽ chọn và giao triển khai sau.
