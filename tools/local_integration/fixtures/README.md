# Fixture W03 integration

`w03-cves-synthetic.json` chứa 13 CVE hoàn toàn tổng hợp để kiểm paging, rank, null/0 và thay đổi
snapshot cục bộ. Tên/điểm/ngày không phải dữ liệu CVE thật; URL dùng `example.invalid`. Adapter tính
`dataset_id` từ bytes của file. Harness không gọi feed, CISA, OpenCTI hay Internet.
