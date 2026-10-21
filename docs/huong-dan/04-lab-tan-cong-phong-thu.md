# Hướng dẫn 04 — Dựng lab tấn công/phòng thủ trên laptop 32 GB

**Ai làm:** vai Web & Red team (chính) + Hạ tầng & Dữ liệu (phần Wazuh). Hạn: v0.1 (24/11/2026).

**Mục tiêu:** 3 máy ảo trên laptop — Wazuh (SIEM), Windows nạn nhân có Wazuh agent, Kali kẻ tấn công — nối với nhau trong một mạng riêng.

**Vì sao:** đây là sân khấu cho demo Red → Blue: kẻ tấn công dùng hạ tầng giả lập, Phong Hỏa biết hạ tầng đó, Wazuh phát hiện máy nạn nhân liên lạc với nó.

## Phương án phần mềm máy ảo

| Phần mềm | Ưu | Nhược |
|---|---|---|
| **VirtualBox (khuyến nghị bắt đầu)** | Miễn phí; tài liệu Wazuh hướng dẫn trực tiếp cho file OVA | Có thể chậm hơn khi Windows đã bật WSL2/Hyper-V |
| VMware Workstation Pro | Miễn phí cho cá nhân, thường nhanh hơn | Phải tạo tài khoản Broadcom để tải |
| Hyper-V | Có sẵn trong Windows Pro | Không mở trực tiếp file OVA của Wazuh |

Bắt đầu bằng VirtualBox; nếu máy ảo ì ạch thì chuyển sang VMware Workstation Pro.

## Sơ đồ mạng
- Tạo một **NAT Network** tên `phonghoa-lab` (VirtualBox: File → Tools → Network Manager → NAT Networks → Create).
- Gắn cả 3 máy ảo vào `phonghoa-lab`: chúng thấy nhau, ra được Internet, nhưng mạng nhà bạn không thấy chúng.
- Máy chủ Ubuntu (OpenCTI) nằm ở mạng nhà; Wazuh chỉ cần **tải blocklist** từ Phong Hỏa (chiều ra), không cần chiều vào.

## Máy 1 — Wazuh (8 GB RAM, 4 CPU, 50 GB)
1. Tải file `wazuh-<phiên bản>.ova` từ trang "Virtual Machine (OVA)" trong tài liệu chính thức documentation.wazuh.com.
2. VirtualBox: File → Import Appliance → chọn file OVA.
3. Settings → Display → Graphics Controller: chọn **VMSVGA** (tài liệu Wazuh cảnh báo các lựa chọn khác có thể treo màn hình).
4. Settings → Network: Adapter 1 → NAT Network `phonghoa-lab`.
5. Khởi động, đăng nhập `wazuh-user` / `wazuh`, gõ `ip a` để xem IP.
6. Từ trình duyệt laptop vào `https://<IP Wazuh>` (bấm "vẫn tiếp tục" khi trình duyệt cảnh báo chứng chỉ), đăng nhập `admin` / `admin`.
7. **Đổi ngay** mật khẩu `admin` và `wazuh-user` — mọi bản OVA đều dùng chung mật khẩu mặc định này.

Mẹo: muốn mở dashboard Wazuh từ laptop dễ hơn, thêm Port Forwarding trong NAT Network (Host 8443 → Wazuh 443).

## Máy 2 — Windows nạn nhân (4 GB RAM, 2 CPU, 60 GB)
1. Tải bản dùng thử 90 ngày của Windows từ Microsoft Evaluation Center (bản Enterprise evaluation).
2. Tạo máy ảo mới, gắn NAT Network `phonghoa-lab`, cài Windows.
3. Trên dashboard Wazuh: mục **Agents → Deploy new agent** → chọn Windows → copy lệnh PowerShell được sinh ra → chạy trong máy Windows với quyền Administrator.
4. Chụp **snapshot** tên `sach-se` ngay sau khi cài xong, để sau mỗi lần diễn tập quay về trạng thái sạch.

## Máy 3 — Kali kẻ tấn công (4 GB RAM, 2 CPU)
1. Tải bản máy ảo dựng sẵn cho VirtualBox (hoặc VMware) tại kali.org.
2. Import, gắn NAT Network `phonghoa-lab`.
3. (Tháng 12) Cài MITRE Caldera để giả lập chiến dịch theo kỹ thuật ATT&CK.

## Luật an toàn của lab (bắt buộc)
1. Không chạy mã độc thật; chỉ giả lập bằng công cụ dành cho diễn tập (Caldera, script tự viết vô hại).
2. Không tấn công bất kỳ địa chỉ nào ngoài mạng `phonghoa-lab` và tên miền của nhóm.
3. Tên miền "độc hại" trong kịch bản phải là **tên miền do nhóm sở hữu** (ví dụ một subdomain của tên miền nhóm).
4. Tắt máy ảo khi không dùng; snapshot trước mỗi lần thử nghiệm.

## Ngân sách RAM khi diễn tập đầy đủ
Wazuh 8 + Windows 4 + Kali 4 + WSL2 6 = 22 GB, còn khoảng 10 GB cho Windows. Khi chỉ code thì tắt cả 3 máy ảo.

## Kiểm tra là xong
- Dashboard Wazuh hiện agent Windows ở trạng thái **Active**.
- Từ Kali `ping` được máy Windows (có thể cần bật ICMP trong tường lửa Windows).
- Đã chụp snapshot `sach-se` cho Windows và Kali.

## Học thêm
- **SIEM agent:** chương trình nhỏ cài trên máy cần giám sát, gửi log về SIEM.
- **NAT Network:** mạng riêng giữa các máy ảo, ra được Internet nhưng bên ngoài không gọi vào được.
- **Snapshot:** "ảnh chụp" toàn bộ máy ảo, quay về được bất cứ lúc nào.
- **OVA:** máy ảo đóng gói sẵn trong một file, import là dùng được.
