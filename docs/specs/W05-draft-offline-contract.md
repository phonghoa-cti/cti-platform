# Hợp đồng bản nháp ngoại tuyến X01 → W05

Trạng thái: hợp đồng cho dữ liệu **đã chạy cục bộ**, chưa phải API HTTP đang hoạt động. Phiên bản dữ liệu hiện
tại là `1.0`; `extractor/phonghoa_extractor/drafts.py` tạo payload và
`extractor/phonghoa_extractor/store.py` kiểm/lưu payload.

Mục tiêu của tài liệu này là để người làm W05 đọc đúng dữ liệu hiện có mà không làm mất bằng chứng, cảnh báo
hoặc nguồn. Ba mẫu kết quả `get` thật nằm tại [`extractor/draft/examples/`](../../extractor/draft/examples/README.md).

## Hai hình dạng dữ liệu

- **Draft mới tạo:** đúng các trường của schema 1.0, chưa có `id` và `created_at`; đây là đầu vào của `save`.
- **Draft đã lưu:** toàn bộ payload ban đầu không đổi, cộng `id` và `created_at` do store tạo; đây là dữ liệu W05
  cần đọc. Không đưa hai trường này trở lại lệnh `save`.

### Trường cấp draft

| Trường | Kiểu / nullable | Có ở draft mới | Có ở draft đã lưu | Ai tạo | Ý nghĩa hiện tại |
|---|---|---:|---:|---|---|
| `id` | integer dương, không null | — | ✓ | Store | Khóa bản ghi cục bộ; mỗi lần lưu tạo ID mới. |
| `created_at` | string ISO 8601 có múi giờ, không null | — | ✓ | Store | Thời điểm lưu UTC, ví dụ `...+00:00`. |
| `schema_version` | string, không null | ✓ | ✓ | Builder | Hiện chỉ nhận `"1.0"`. |
| `status` | string, không null | ✓ | ✓ | Builder | Hiện chỉ nhận `"pending"`; đây là trạng thái **draft**. |
| `source` | object, không null | ✓ | ✓ | Builder | Tên nguồn và hash của text được lưu; xem bảng dưới. |
| `language` | `"vi" \| "en"`, không null | ✓ | ✓ | Builder/người gọi | Ngôn ngữ khai báo của text. Store không tự nhận diện. |
| `tlp` | string, không null | ✓ | ✓ | Builder/người gọi | `TLP:CLEAR`, `TLP:GREEN`, `TLP:AMBER`, `TLP:AMBER+STRICT` hoặc `TLP:RED`; là metadata, không cấp quyền gửi cloud. |
| `text` | string, không null | ✓ | ✓ | Người gọi/builder | Nguyên văn dùng để tạo hash và tính span; có thể rỗng. |
| `items` | array, không null | ✓ | ✓ | Builder | Danh sách mục trích; hiện builder C1 chỉ tạo IOC. |
| `injection_warning` | boolean, không null | ✓ | ✓ | Bộ quét | Có phát hiện dấu hiệu chèn lệnh; `false` không chứng minh text an toàn. |
| `findings` | array, không null | ✓ | ✓ | Bộ quét | Chi tiết quy tắc cảnh báo; có thể rỗng. |
| `model` | string không rỗng | ✓ | ✓ | Builder | Hiện là `regex-C1`; tên này không chứng minh có LLM. |
| `cost_tokens` | integer ≥ 0 | ✓ | ✓ | Builder | C1 hiện là `0`. |

### `source`

| Trường | Kiểu / nullable | Ai tạo | Ý nghĩa |
|---|---|---|---|
| `source.name` | string không rỗng | Người gọi/builder | Nhãn/tên nguồn để hiển thị; chưa phải URL hay định danh tin cậy. |
| `source.sha256` | 64 ký tự hex thường | Builder | SHA-256 của `text.encode("utf-8")` thực sự lưu. Không hứa là hash byte file gốc trước khi giải mã/trích text. |

### Mỗi phần tử `items`

| Trường | Kiểu / nullable | Ai tạo | Ý nghĩa hiện tại |
|---|---|---|---|
| `kind` | string, không null | Grounding/builder | Builder hiện tạo `"ioc"`. Store chưa giới hạn mọi giá trị string khác. |
| `type` | string, không null | Grounding/builder | Với IOC kept, phải khớp loại của `value` sau chuẩn hóa. |
| `value` | string, không null | Grounding/builder | Giá trị IOC chuẩn hóa; không dùng thay cho quote nguyên văn. |
| `span` | `[start, end]` hoặc `null` | Grounding/builder | Khoảng code point Python `[start,end)` trên đúng `text`. `null` nghĩa không có liên kết tô sáng. |
| `evidence` | string, không null | Grounding/builder | Phải bằng `text[start:end]` khi `span` khác null; có thể rỗng cho item rejected. |
| `keep` | boolean, không null | Grounding/builder | Gợi ý chọn ban đầu. `true` **không** có nghĩa con người đã duyệt. |
| `warning` | string hoặc `null` | Grounding/builder/fixture | Lý do/cảnh báo để người duyệt hiểu trạng thái. |
| `status` | string, không null | Grounding/builder | Trạng thái **item** như `ok`, `allowlist`, `bia`; khác `draft.status`. |

### Mỗi phần tử `findings`

| Trường | Kiểu / nullable | Ai tạo | Ý nghĩa |
|---|---|---|---|
| `paragraph` | integer ≥ 1 | Bộ quét | Đoạn chứa dấu hiệu theo quy ước hiện tại của scanner. |
| `rule` | string, không null | Bộ quét | Mã quy tắc phát hiện. |
| `excerpt` | string, không null | Bộ quét | Trích đoạn để giải thích; luôn render dạng text. |

## Bất biến và giới hạn schema hiện tại

1. `source.sha256` phải đúng SHA-256 UTF-8 của `text`; store từ chối payload không khớp.
2. Khi `span` khác null, `text[start:end] == evidence`. IOC `keep=true` còn phải nằm nguyên token trong chính
   span đó sau chuẩn hóa và đúng `type`.
3. Item rejected có thể có `span=null`, `evidence=""`, `keep=false`; W05 không tạo liên kết tô sáng cho item này.
4. Hiện store chỉ nhận draft `pending`; chưa có chuyển trạng thái, cập nhật hay ghi đè.
5. Builder C1 hiện chỉ tạo IOC. Ví dụ API cũ có `ttp|malware|actor` là hướng tương lai, không phải dữ liệu đã chạy.
6. Ngoài kiểm tra quan hệ type/value/span cho `kind=ioc` được giữ, store chưa giới hạn đầy đủ tập
   `kind`/`item.status` của dữ liệu tự khai. Biên API tương lai phải có allowlist schema và từ chối loại/trạng
   thái chưa hỗ trợ trước khi đưa dữ liệu cho W05.
7. `tlp` và `injection_warning` chỉ là dữ liệu hiển thị/kiểm soát; chúng không phải phép gửi cloud và cũng không
   chứng minh nội dung an toàn.

## Unicode và span

Python 3.12 đếm `str` theo Unicode code point. Span không phải offset byte và cũng không phải vị trí ký tự hiển
thị (grapheme): một chữ ghép có thể gồm nhiều code point. Không normalize, refang hoặc trim `text` trước khi cắt.

Mẫu `01-regular.json` có emoji đứng trước IOC và evidence `[0,58)`. Python lấy quote bằng:

```python
quote = text[start:end]
```

JavaScript dùng chỉ số UTF-16 cho `slice`, nên với span code point phải dùng:

```js
const quote = Array.from(text).slice(start, end).join("");
```

Nếu API/frontend sau này chọn offset UTF-16, cần một bước chuyển đổi được đặc tả và test riêng; không được đổi
ngầm ý nghĩa span 1.0.

## Hàng đợi pending ngoại tuyến

API Python dự kiến cho lát cắt này:

```python
list_drafts(db_path, *, limit=20, before_id=None, timeout=5.0)
```

Hàm chỉ đọc các draft có trạng thái cột SQLite là `pending`, sắp xếp `id DESC` và trả:

```json
{
  "items": [
    {
      "id": 5,
      "created_at": "2026-11-10T15:18:49.564135+00:00",
      "status": "pending",
      "source": {"name": "synthetic.txt", "sha256": "..."},
      "language": "vi",
      "tlp": "TLP:AMBER",
      "item_count": 1,
      "injection_warning": false
    }
  ],
  "next_before_id": 5
}
```

- Summary không chứa `text`, `items`, `evidence`, `findings` hoặc excerpt nguồn.
- `limit` là integer thật trong `[1,100]`; `before_id` là null hoặc integer dương trong miền SQLite.
- Trang sau dùng `id < before_id`, không dùng OFFSET. Cursor không cần trùng một ID đang tồn tại.
- `next_before_id` là ID cuối trang khi còn ít nhất một dòng phía sau; hết dữ liệu hoặc trang rỗng trả null.
- Insert mới giữa hai lần đọc không làm lặp/mất ID cũ ở các trang tiếp theo; tải lại trang đầu mới thấy ID mới.
  Đây không phải snapshot chung qua nhiều lần đọc.
- Lệnh list dùng SQLite `mode=ro`, timeout hữu hạn, không tạo DB/table và không chuyển trạng thái.
- CLI ghi JSON summary ra file riêng; output trùng/equivalent/samefile với DB phải bị từ chối.

## Khoảng trống trước khi W05 chạy thật

| Phần | Hiện tại | Cần có trước tích hợp |
|---|---|---|
| Liệt kê/lọc/phân trang | Có API/CLI ngoại tuyến theo cursor ID; chưa có HTTP | Endpoint pending có quyền, giới hạn và metadata phân trang. |
| Đọc chi tiết | Chỉ có CLI/API Python `get_draft` | Endpoint đọc một draft, lỗi 404/422 rõ và payload giữ đủ trường. |
| Xác thực/quyền | Chưa có | Danh tính phải do backend xác minh; chỉ Analyst/Admin, không tin header email do client tự gửi. |
| Schema ở biên API | Store chưa siết mọi `kind/status` | Từ chối loại/trạng thái chưa hỗ trợ và trường thừa/thiếu trước khi render. |
| Sửa/lưu nháp | Chưa có update | Quy tắc optimistic concurrency hoặc phiên bản, audit before/after. |
| Duyệt/từ chối | Chưa có | Chuyển trạng thái có transaction, lý do từ chối và chống tự duyệt. |
| Người đề xuất/người duyệt | Chưa lưu | Định danh, vai trò, thời gian và quy tắc hai người khi cần. |
| Đo sửa đổi | Chưa có | Số mục gốc/bỏ/thêm/sửa để đánh giá extractor. |
| OpenCTI | Chưa nối | Chỉ ghi sau quyết định hợp lệ; lưu ID/kết quả/lỗi và cho phép retry an toàn. |
| Offset frontend | Chỉ code point Python | Dùng `Array.from` hoặc chuyển đổi có test với emoji/chữ ghép. |

Các endpoint trong [`api-portal.md`](api-portal.md) vẫn là đề xuất. Hoàn thành tài liệu này không chứng minh W05,
HTTP, xác thực, phê duyệt hoặc OpenCTI đã hoạt động.
