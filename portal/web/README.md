# Portal web — W05 preview

Lát cắt cục bộ để xem hàng đợi ba bản nháp tổng hợp X01. Đây không phải luồng duyệt thật: không có đăng nhập,
không gửi request ghi và không nối OpenCTI.

## Chạy cục bộ

Yêu cầu Node.js 22.12 trở lên (đã kiểm với Node.js 24.22.1).

```powershell
npm ci
npm run dev -- --port 3002
```

Mở `http://localhost:3002/duyet`; `/` tự chuyển tới route này.

## Kiểm tra

```powershell
npm test
npm run typecheck
npm run lint
npm run build
```

Dữ liệu trong `data/fixtures/` là bản sao có chủ đích của ba fixture tổng hợp tại
`extractor/draft/examples/`. Adapter `data/draft-adapter.ts` kiểm hình dạng tối thiểu và ID trước khi giao cho UI.
