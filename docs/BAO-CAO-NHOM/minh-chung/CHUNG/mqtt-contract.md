# MQTT contract hiện có

Nguồn: device/sketch.ino, đọc tĩnh trong lượt tổ chức. Không thay đổi topic hoặc payload. Broker broker.hivemq.com:1883, device_id esp32-01, client_id smartparking-group21-esp32-01-wokwi.

| Topic | Luồng | Dữ liệu |
|---|---|---|
| smartparking/group21/slots/P01/state | Device → Backend | slot_id P01, occupied boolean |
| smartparking/group21/slots/P02/state | Device → Backend | slot_id P02, occupied boolean |
| smartparking/group21/slots/P03/state | Device → Backend | slot_id P03, occupied boolean |
| smartparking/group21/slots/P04/state | Device → Backend | slot_id P04, occupied boolean |
| smartparking/group21/device/status | Device → Backend | heartbeat online hoặc Will offline |
| smartparking/group21/gate/command | Backend → Device | command_id, action, direction |
| smartparking/group21/gate/status | Device → Backend | device_id, command_id, status |

```json
{"device_id":"esp32-01","slot_id":"P01","occupied":true}
```
```json
{"device_id":"esp32-01","status":"online","uptime_ms":30000}
```
Will offline:
```json
{"device_id":"esp32-01","status":"offline"}
```
Lệnh:
```json
{"command_id":"integration-open-001","action":"OPEN","direction":"ENTRY"}
```
action OPEN/CLOSE; direction ENTRY/EXIT; command_id chuỗi không rỗng tối đa 80 ký tự. Payload lệnh tối đa 256 byte theo firmware.

ACK:
```json
{"device_id":"esp32-01","command_id":"integration-open-001","status":"OPENED"}
```
status OPENED/CLOSED/ERROR. Servo chuyển 90°/0°, firmware chờ 700 ms rồi xếp ACK; đây là xác nhận phần mềm, chưa có cảm biến phản hồi góc. Khi đang chuyển động, lệnh mới bị từ chối ERROR. Firmware chỉ nhớ lệnh hoàn tất gần nhất để trả ACK khi trùng, không phải kho idempotency lâu dài.

Sensor INPUT_PULLUP, LOW = occupied true; debounce 400 ms. Heartbeat 10 giây, retry Wi-Fi/MQTT 5 giây. Slot và heartbeat publish retained=false; ACK mặc định không retained. Subscribe lệnh QoS 1, publish PubSubClient hiện QoS 0. Reconnect đánh dấu cả bốn ô cần gửi lại.

Payload không có timestamp tuyệt đối. uptime_ms không phải UTC. Backend dự kiến gắn received_at, định nghĩa timeout UNKNOWN và chống trùng khi reconnect. Broker công cộng chỉ phục vụ demo; tài liệu này không thay đổi cấu hình bảo mật hay broker.
