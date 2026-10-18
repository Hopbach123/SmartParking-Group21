# Kế hoạch tích hợp

## Luồng

ESP32/Wokwi → MQTT → FastAPI/SQLite → REST/WebSocket → React/Spline. Chiều ngược lại cho cổng: UI → FastAPI → MQTT → Device → ACK → FastAPI → UI.

## Contract và khác biệt

Topics và payload chính xác nằm trong mqtt-contract.md; snapshot Frontend trong ../frontend/docs/DATA_CONTRACT.md; API dự kiến trong api-contract.md.

| Device | Frontend hiện tại | Xử lý dự kiến tại Backend/adapter |
|---|---|---|
| occupied true/false, slot_id | OCCUPIED/EMPTY/UNKNOWN, khóa P01–P04 | Ánh xạ boolean; UNKNOWN theo timeout/chưa nhận dữ liệu, không giả EMPTY |
| Không có UTC, có uptime_ms trong heartbeat | timestamp ISO có múi giờ | Gắn received_at UTC, không coi uptime là thời gian tuyệt đối |
| action OPEN/CLOSE | gate OPEN/CLOSED | CLOSED yêu cầu → CLOSE; ACK OPENED → OPEN, CLOSED → CLOSED |
| direction ENTRY/EXIT bắt buộc | UI chưa có direction | Nhóm thống nhất direction trên API/UI trước tích hợp; không tự giả định |
| ACK có command_id và ERROR | mock cập nhật ngay | pending/confirmed/error, đối chiếu ID, timeout; không coi gửi lệnh là thành công |
| QoS 0 publish, không retained | snapshot ban đầu EMPTY | Chờ dữ liệu, xử lý mất bản tin, reconnect và stale; cần thống nhất chiến lược |
| MQTT có slot_id/device_id | lịch sử dùng slotId | Adapter đổi tên trường có kiểm soát, giữ payload MQTT nguyên trạng |
| Reconnect có gửi lại trạng thái | IN/OUT theo chuyển trạng thái mock | Không ghi thêm sự kiện khi nhận lại cùng trạng thái; chốt UNKNOWN→OCCUPIED có tính IN không |

## Thứ tự công việc

1. TV1 chạy Wokwi và lưu bằng chứng sensor, FULL, command/ACK, duplicate, busy, reconnect. Hiện source mới được kiểm tra tĩnh.
2. Ba thành viên chốt contract đã ghi, direction, timeout, timestamp, thống kê và revision.
3. TV2 triển khai MQTT subscriber và lưu SQLite theo contract; thêm REST snapshot/events/statistics, command và WebSocket. Chưa làm ở nhiệm vụ này.
4. TV3 thay mock bằng adapter store; giữ getParkingStatus đồng bộ cho useSyncExternalStore, fetch/WS cập nhật store; không đưa MQTT vào trình duyệt.
5. Chạy kiểm thử tích hợp, lưu log theo module và bằng chứng chung trong docs.

## Checklist end-to-end — chưa kiểm thử

- [ ] Công tắc P01–P04 → đúng MQTT slot_id/boolean → snapshot API → xe và màu 3D.
- [ ] Bốn ô có xe → available=0/FULL, history/statistics nhất quán.
- [ ] Mất heartbeat → UNKNOWN theo chính sách đã chốt; không tính là chỗ trống.
- [ ] OPEN/CLOSE với ENTRY/EXIT → đúng command_id → ACK → UI xác nhận.
- [ ] Busy, payload lỗi, ACK timeout, duplicate/reconnect không làm sai cổng hoặc đếm trùng.
- [ ] Refresh/reconnect Frontend nhận lại snapshot backend, không reset dữ liệu thật.
- [ ] Mất broker/backend/WS hiển thị lỗi và phục hồi; có sequence chống bản tin cũ.

Không thực thi MQTT, không gửi lệnh servo, không triển khai Backend trong lượt tổ chức.
