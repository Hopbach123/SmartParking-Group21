# Kiến trúc hệ thống

Device: ESP32, bốn công tắc P01–P04, SG90. Firmware hiện kết nối broker.hivemq.com:1883, publish trạng thái/heartbeat và subscribe lệnh cổng.

Backend dự kiến nhận MQTT, gắn received_at UTC, chuẩn hóa trạng thái, lưu SQLite, cung cấp REST/WebSocket. Chưa có code Backend.

Frontend React + Vite hiện dùng parkingService giả lập, hiển thị Spline, KPI, lịch sử và thống kê. Scene giữ nguyên:
https://prod.spline.design/NNU0y3In1BxfOzsL/scene.splinecode

Frontend không điều khiển ESP32 trực tiếp; MQTT đi qua Backend sau này. Luồng điều khiển dự kiến: UI → REST → MQTT command → Device → MQTT ACK → Backend → WebSocket → UI.

Tài liệu riêng giữ tại frontend/docs; tài liệu chung đặt ở docs gốc. Báo cáo Device Rp-Tv1.md đã có trong frontend/docs được giữ nguyên vị trí theo yêu cầu, không chuyển sang module khác.
