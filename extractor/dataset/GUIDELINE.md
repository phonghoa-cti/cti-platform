# Hướng dẫn gán nhãn dataset cho AI extractor

**Mục tiêu:** có khoảng 40 báo cáo (một nửa tiếng Việt) được gán nhãn thủ công, làm "đáp án" để chấm điểm
regex và LLM ở chương 4. Gán nhãn sai thì mọi con số trong chương 4 đều sai — nên làm chậm và cẩn thận.

## 1. Chọn báo cáo
- Nguồn: cảnh báo của NCSC/VNCERT, blog bảo mật Việt Nam, báo cáo tiếng Anh từ blog các hãng bảo mật.
- Dài 300–3000 từ, có ít nhất 3 IOC hoặc mô tả hành vi tấn công.
- Lưu: `raw/<id>.txt` (văn bản đã bỏ menu, quảng cáo) + `raw/<id>.meta.json` (`url`, `ngay`, `nguon`, `ngon_ngu`).
- Thư mục `raw/` không commit nếu nội dung có bản quyền; chỉ commit file nhãn và danh sách link.

## 2. Gán nhãn gì
Mỗi báo cáo một file `labels/<id>.json`:
```json
{
  "id": "vn-0001",
  "iocs": [
    {"type": "domain", "value": "hoadon-dientu.top", "role": "attacker"},
    {"type": "ipv4", "value": "45.137.21.9", "role": "attacker"}
  ],
  "ttps": ["T1566.001", "T1204.002"],
  "malware": ["Tên họ mã độc nếu có"],
  "actor": ["Tên nhóm nếu báo cáo nêu"]
}
```

## 3. Quy tắc
1. **Giá trị IOC:** ghi dạng đã chuẩn hóa (chạy `phonghoa_core.normalize`), không defang.
2. **role:** `attacker` (hạ tầng/công cụ của kẻ tấn công), `victim` (của nạn nhân), `benign` (dịch vụ hợp pháp được nhắc đến, ví dụ google.com). Chỉ IOC `attacker` dùng để chấm điểm chính.
3. **Không suy diễn:** chỉ gán IOC xuất hiện trong văn bản. TTP chỉ gán khi văn bản mô tả rõ hành vi.
4. **TTP:** tra mã trên attack.mitre.org; dùng mã con (T1566.001) nếu văn bản đủ chi tiết, không thì mã cha (T1566).
5. **Phân vân:** thêm trường `"ghi_chu"` và đưa ra thảo luận nhóm; không đoán.

## 4. Kiểm tra chất lượng
- 5 báo cáo đầu tiên: 2 người gán độc lập rồi so sánh. Tính tỉ lệ trùng khớp IOC và TTP; nếu < 80%, thống nhất lại quy tắc rồi mới gán tiếp.
- Ghi tỉ lệ đồng thuận vào báo cáo (chương 4) — hội đồng thường hỏi "đáp án do ai làm, tin được không".

## 5. Tiến độ
| Đợt | Số báo cáo | Hạn |
|---|---|---|
| Thử quy tắc | 5 (2 người cùng gán) | 15/12/2026 |
| Đợt 1 | 20 | 22/12/2026 |
| Đợt 2 | 20 | 05/01/2027 |
| Đợt chống prompt injection | 10 bản có chèn câu lệnh ẩn | 20/01/2027 |
