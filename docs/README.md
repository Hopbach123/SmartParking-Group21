# Tài liệu SmartParking Group 21

## Các file cần đọc

| Tài liệu | Dùng khi nào? |
|---|---|
| [Báo cáo chung ba thành viên](BAO-CAO-NHOM/README.md) | Xem tổng hợp Device/Backend/Frontend và công việc từng người |
| [Bảng công việc](BAO-CAO-NHOM/04_THONG_KE_CONG_VIEC.md) | Xem 45 nhóm việc, trạng thái và bằng chứng; không phải % đóng góp |
| [Setup và lệnh chạy A–Z](BAO-CAO-NHOM/05_HUONG_DAN_SETUP_VA_CHAY_A_Z.md) | Thành viên clone/cài/chạy và xử lý lỗi |
| [Kiến trúc hiện tại](architecture.md) | Hiểu các module và luồng dữ liệu |
| [API hiện tại](api-contract.md) | Kết nối REST/WebSocket và điều khiển cổng |
| [MQTT contract](mqtt-contract.md) | Đối chiếu topic/payload Device↔Backend |
| [Integration contract v1](integration-contract-v1.md) | Đối chiếu các quy tắc đã được chốt |

## Bố cục gọn

```text
docs/
  README.md
  architecture.md
  api-contract.md
  mqtt-contract.md
  integration-contract-v1.md
  BAO-CAO-NHOM/       Báo cáo chung, báo cáo từng người, setup và minh chứng đã gom
  LUU-TRU/           Các Phase/log/kế hoạch cũ trước khi gom báo cáo
```

`RP-TV3/` nếu đã có từ trước có thể giữ như bộ báo cáo riêng, nhưng điểm đọc chính là BAO-CAO-NHOM. Không dùng báo cáo Phase cũ để suy trạng thái mới: số tests, đường dẫn source hoặc câu “chưa có Backend/LIVE” có thể là thông tin lịch sử.

Các log, XML, JSON, ảnh, checksum và báo cáo nháp đã được **chuyển vào lưu trữ, không xóa**. Mở [mục lục lưu trữ](LUU-TRU/README.md) khi cần đối chiếu. Minh chứng theo thành viên trong BAO-CAO-NHOM không bị thay đổi.

Contract v1 còn tiêu đề DRAFT từ thời điểm lập đề xuất; người dùng đã duyệt D01–D08 trước triển khai Backend. Việc dọn docs không sửa contract hoặc tự phê duyệt thêm tính năng.

Ngày tổ chức lại: 19/10/2026. Chỉ thay tài liệu và đường dẫn, không sửa source, .env, firmware, dependency hoặc Git.
