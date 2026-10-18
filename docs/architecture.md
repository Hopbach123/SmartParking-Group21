# Kiến trúc SmartParking Group 21 — hiện tại

Cập nhật tài liệu ngày 19/10/2026. Bản mô tả cũ được giữ tại [LUU-TRU/ke-hoach-cu/architecture.md](LUU-TRU/ke-hoach-cu/architecture.md).

```text
TV1: ESP32/Wokwi → MQTT Broker → TV2: FastAPI → SQLite
                                           ↓ REST / WebSocket
                                      TV3: React → Spline 3D

React Gate API → FastAPI → MQTT gate/command → ESP32/servo
React/Spline ← WebSocket ← FastAPI ← MQTT gate/status ACK
```

| Module | Hiện trạng |
|---|---|
| device/ | Firmware ESP32, bốn công tắc, SG90; slot/heartbeat/Will, reconnect, command/ACK; gửi lại bốn trạng thái theo heartbeat |
| backend/ | FastAPI/SQLite, strict MQTT subscriber, health/baseline, REST/WS và Gate Controller; một worker MVP |
| frontend/ | React/Vite, Spline, KPI/history/chart, DEMO độc lập và LIVE REST/WS adapter |
| docs/BAO-CAO-NHOM/ | Báo cáo tổng hợp và phần việc cả ba thành viên, hướng dẫn setup, bằng chứng theo module |

Backend đã có source; mô tả “chưa triển khai Backend” trong báo cáo giai đoạn cũ không phải hiện trạng. Tuy vậy có source không đồng nghĩa mọi ca E2E đã có biên bản PASS. Người dùng đã xác nhận test được sau các điều chỉnh; mức xác nhận từng ca được ghi riêng trong báo cáo nhóm.

## Quy tắc dữ liệu

- Slot EMPTY/OCCUPIED/UNKNOWN; UNKNOWN không tính available, FULL khi đủ bốn OCCUPIED.
- LIVE cần heartbeat hợp lệ và baseline bốn ô. Mất broker/Will/heartbeat timeout thu hồi trust, giữ last-known/history; không giả EMPTY để che lỗi.
- Snapshot có source/schema_version/UTC/stream_id/revision; full events để thống kê cùng phạm vi. Reconnect lấy lại snapshot, không replay mock để tăng lượt xe.
- Gate OPEN/CLOSED và gate_meta.confirmed tách trạng thái last-known khỏi xác nhận. PENDING/CONFIRMED/ERROR/TIMEOUT theo command_id; không tự lặp OPEN sau timeout/restart.
- ENTRY OPEN bị chặn khi FULL hoặc không đáng tin; EXIT không bị chặn chỉ vì FULL nhưng vẫn cần kết nối/không busy.
- ACK firmware không phải cảm biến góc; một servo và công tắc là mô hình mô phỏng, chưa có chống kẹt thực tế.

## DEMO và LIVE

DEMO dùng mock service, reset/refresh tạo phiên mới; LIVE nhận REST/WS và dữ liệu cảm biến, ô chỉ đọc, không RESET database. Cổng và công tắc ô là hai chức năng riêng. Barrier Spline được cố định Y/+90° theo yêu cầu, chỉ cập nhật khi LIVE có xác nhận hợp lệ.

Scene giữ `https://prod.spline.design/NNU0y3In1BxfOzsL/scene.splinecode`. Broker hiện tại broker.hivemq.com:1883; giữ MQTT contract. Public broker/QoS0 và Wokwi có thể có lỗi kết nối/độ trễ; snapshot định kỳ giúp phục hồi trạng thái cuối, không bảo đảm phục hồi mọi lượt xe đã mất.

Xem [API](api-contract.md), [integration contract](integration-contract-v1.md), [báo cáo nhóm](BAO-CAO-NHOM/README.md) và [hướng dẫn chạy](BAO-CAO-NHOM/05_HUONG_DAN_SETUP_VA_CHAY_A_Z.md).
