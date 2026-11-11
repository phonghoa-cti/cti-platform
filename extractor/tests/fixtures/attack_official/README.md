# Fixture metadata ATT&CK official

Thư mục này chỉ giữ bộ pin đã review và LICENSE nguyên văn của MITRE ATT&CK Enterprise v20.1.
Snapshot `enterprise-attack-20.1.json` không nằm trong repo: đặt biến môi trường
`PHONGHOA_ATTACK_OFFICIAL_SNAPSHOT` trỏ tới tệp local có đúng 55.277.605 byte và SHA-256 trong
`official-pin.json` trước khi chạy `test_attack_catalog_official.py`.

Thiếu biến môi trường thì các ca cần asset thật được đánh dấu skip rõ ràng. Lượt nghiệm thu phải cấp path và
không được coi kết quả skip là bằng chứng tương thích. Loader chỉ đọc tệp local; fixture này không cấp quyền tải
mạng và không xác minh chữ ký cryptographic của tag/commit.

Tệp `LICENSE.txt` được sao nguyên văn từ cùng commit. Tệp NOTICE riêng chưa được xác minh.
