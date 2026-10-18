# TV1 — Huỳnh Đổ Hoàng Nguyên

**MSSV:** 2001230582. **Phụ trách:** Device / ESP32 / Wokwi.

## Phạm vi và công nghệ

Arduino C++, ESP32, WiFi, PubSubClient, ESP32Servo, ArduinoJson, Wokwi.

Phân công lấy từ tài liệu nhóm. Nội dung bên dưới đối chiếu source và báo cáo, không phải audit tác giả từng commit hoặc thống kê số giờ làm.

## Bảng công việc thực tế

| Mã | Công việc | Nội dung đã làm | Trạng thái triển khai | Bằng chứng / giới hạn |
|---|---|---|---|---|
| TV1-01 | Mô hình và đấu nối | ESP32, 4 slide switches, servo SG90; diagram.json có 6 parts và 11 connections. | Đã triển khai | Source và sơ đồ hiện có; chưa nghiệm thu phần cứng thật |
| TV1-02 | Ánh xạ GPIO | P01–P04 = 13/14/27/26; servo PWM = 18; V+ 5V và GND. | Đã triển khai | Đối chiếu diagram.json với SENSOR_PINS/SERVO_PIN |
| TV1-03 | Đọc trạng thái ô | INPUT_PULLUP; LOW → occupied=true, còn lại false. | Đã triển khai | Log người dùng có trạng thái P01–P04 |
| TV1-04 | Chống dội công tắc | Debounce 400ms, cập nhật occupied và slotDirty khi giá trị ổn định thay đổi. | Đã triển khai | Log SENSOR P02/P03 do người dùng cung cấp |
| TV1-05 | Kết nối Wi-Fi | Wokwi-GUEST, retry theo RETRY_MS; không block bằng vòng chờ vô hạn trong loop. | Đã triển khai | Có log Wi-Fi CONNECTED; không đo SLA |
| TV1-06 | Publish MQTT ô đỗ | JSON device_id/slot_id/occupied boolean, đúng bốn topic; không retained. | Đã triển khai | Có log SLOT OK; publish OK chưa bảo đảm subscriber đã nhận |
| TV1-07 | Heartbeat và Last Will | Heartbeat online/uptime mỗi 10s mô phỏng; Will offline khi kết nối mất. | Đã triển khai | Backend đã nhận heartbeat và OFFLINE trong log |
| TV1-08 | Reconnect và timeout | Tự thử reconnect, subscribe gate/command, đánh dấu gửi lại bốn ô; socket timeout 3→15s. | Đã triển khai | Source đã cập nhật; kết nối public broker còn chập chờn |
| TV1-09 | Snapshot định kỳ | Sau mỗi heartbeat đánh dấu cả bốn ô dirty, gửi lại trạng thái GPIO hiện tại ở loop kế tiếp. | Đã triển khai | Source đã có; người dùng xác nhận test được sau chỉnh sửa |
| TV1-10 | Điều khiển servo | OPEN đặt 90°, CLOSE 0°; processServo chờ 700ms mô phỏng trước xếp ACK. | Đã triển khai | Log OPEN/OPENED có thật; quan sát cơ khí cuối cùng chưa có biên bản |
| TV1-11 | Validate lệnh | Kiểm tra topic, độ dài, JSON, command_id/action/direction, giới hạn ID 80 ký tự. | Đã triển khai | Đối chiếu source; không tự gọi mọi ca Device là đã chạy |
| TV1-12 | Chống trùng/busy và ACK | Nhớ lệnh hoàn tất gần nhất để re-ACK; busy trả ERROR; gửi gate/status qua hàng chờ ACK. | Đã triển khai | Không phải idempotency bền qua restart; chưa đủ test vật lý từng nhánh |

## Minh chứng gốc

- [Rp-Tv1.md](minh-chung/TV1/Rp-Tv1.md)
- [README.md](minh-chung/TV1/README.md)
- [XAC_NHAN_NGUOI_DUNG.md](minh-chung/CHUNG/XAC_NHAN_NGUOI_DUNG.md)

## Công việc phối hợp và ranh giới

Phối hợp TV2 về topic/payload và ACK, phối hợp TV3 kiểm tra công tắc/servo với Dashboard. Không nhận REST/SQLite hoặc React là phần triển khai Device.

## Chưa kết luận hoàn thành tuyệt đối

Đã triển khai không đồng nghĩa mọi tình huống E2E đã PASS. Người dùng đã xác nhận test được sau điều chỉnh, nhưng chưa có bảng nghiệm thu đầy đủ từng ca, số đo độ trễ/SLA, bằng chứng phần cứng thật hoặc fresh clone trên máy khác. Xem [báo cáo tổng hợp](00_BAO_CAO_TONG_HOP_NHOM.md) và [bảng công việc](04_THONG_KE_CONG_VIEC.md).
