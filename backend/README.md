# Backend giai đoạn 4 — WebSocket & Gate Controller

Contract v1 được giữ theo lựa chọn người dùng: command_id bắt buộc từ client; trạng thái PENDING/CONFIRMED/ERROR/TIMEOUT. Không dùng SUCCESS/FAILED trên wire, không tự sinh command_id còn thiếu. Client có thể tạo UUID mới cho một ý định mới và dùng lại đúng UUID khi retry cùng ý định.

## Vị trí và áp dụng

Đây là bản Backend chuẩn bị trong gói phase-04, chưa tự chép vào dự án ổ F do phiên chưa được cấp quyền ghi. Không chứa .env, data SQLite hoặc .venv của dự án gốc. apply-phase04.ps1 ở thư mục cha kiểm tra checksum/xung đột, sao lưu file bị thay đổi và chỉ chép backend/docs; không sửa Device/Frontend hoặc xóa source.

Dừng Backend trước khi áp dụng gói. Sau khi source đã ở backend/ của dự án chính:

```powershell
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Máy mới cần python -m venv .venv trước khi cài. Chạy một worker/process. Swagger http://127.0.0.1:8000/docs. DB mặc định backend/data/smartparking.sqlite3, không phụ thuộc cwd; .env hiện có không bị ghi đè. Thêm SMART_PARKING_ACK_TIMEOUT=5 nếu cần, mặc định đã là 5 giây. MQTT, heartbeat, broker/topic và CORS origins giữ cấu hình giai đoạn 3; POST được cho phép trong CORS allowlist.

## Gate API

POST /api/parking/gate:

```json
{"command_id":"client-uuid-001","status":"OPEN","direction":"ENTRY"}
```

status OPEN/CLOSED; direction ENTRY/EXIT, ID ASCII không có khoảng trắng 1–80 ký tự, body fields thừa bị từ chối. Request CLOSED được map sang MQTT action CLOSE. Thiếu ID trả 422, không tạo ngầm. Payload MQTT giữ command_id/action/direction theo firmware, tổng UTF-8 ≤256 byte.

- 202: đã lưu PENDING và chấp nhận publish; chưa có xác nhận servo.
- 200: retry ID cùng body đã terminal, trả record cũ, không publish lại.
- 409: FULL khi OPEN ENTRY; baseline không tin cậy; GATE_BUSY; ID cũ với body khác.
- 503: broker/device không sẵn sàng hoặc publish lỗi; publish lỗi sau khi lưu command được ghi ERROR, có thể GET record theo ID. Không khẳng định chưa từng có byte nào tới Device.
- 422: body không đúng contract; 404 khi GET command không tồn tại.

GET /api/parking/commands/{command_id} trả record gồm command_id,requested_status,direction,state,created_at,completed_at,error_code.

OPEN ENTRY chỉ được nhận khi mqtt CONNECTED, Device ONLINE, đủ baseline đáng tin và còn ô EMPTY; 4 OCCUPIED bị chặn ở Backend. OPEN EXIT không bị chặn chỉ vì FULL hoặc thiếu baseline ô, nhưng vẫn cần Device online, MQTT thực sự sẵn sàng và không có command PENDING. CLOSE không có auto-close vì FULL. Không bypass luật qua WebSocket.

Idempotency kiểm tra trước health: retry cùng ID không tự phát lại sau reconnect/timeout/restart. Một command in-flight cho Device. PENDING được commit trước publish. Publish không retained, dùng QoS0 để tránh cơ chế Paho tự resend QoS1 trên reconnect; contract v1 ghi QoS1 là đề xuất, còn yêu cầu không auto-republish được ưu tiên. Không đảm bảo exactly-once khi mạng lỗi, ACK vẫn là nguồn xác nhận phần mềm.

ACK OPENED/CLOSED phải đúng command_id và target, Device đúng được parser MQTT kiểm tra. ERROR hoặc target mismatch → ERROR; ID lạ, retained, ACK terminal/late không cập nhật cổng. Timeout 5s → TIMEOUT, không tự retry. ACK muộn chỉ lưu audit, không đổi TIMEOUT thành CONFIRMED. Mất broker/heartbeat hoặc lỗi command thu hồi confirmed flag, không giả cổng CLOSED.

CONFIRMED và gate_meta.confirmed là xác nhận firmware, chưa phải bằng chứng servo đã quay quan sát bằng mắt. Gate status quan sát ngoài command do Backend phát sẽ không được áp dụng. Lần ACK đầu tiên xác nhận trạng thái gate nhưng không tạo chuyển động CLOSED→OPEN giả khi trạng thái trước chưa biết. GATE history chỉ ghi khi hai trạng thái OPEN/CLOSED đã xác nhận khác nhau.

## WebSocket

ws://127.0.0.1:8000/ws/parking. Nhiều client, initial full snapshot khi kết nối/reconnect. Client có thể GET /api/parking/status để resync, không dùng replay updateSlotStatus để tạo history giả.

```json
{"type":"parking.snapshot","schema_version":"1.0","data":{"schema_version":"1.0","source":"LIVE","timestamp":"...","slots":{},"gate":"CLOSED","gate_meta":{},"connection":{},"stream_id":"...","revision":1,"events":[]}}
```

Ví dụ trên rút gọn minh họa; payload đầy đủ được validate theo SnapshotMessage. Mỗi commit phát full snapshot. Thay đổi command phát gate.command trước parking.snapshot cùng revision. Theo dõi revision riêng cho từng loại, không loại snapshot chỉ vì đã nhận command cùng revision. stream_id mới sau Backend restart; không so số revision giữa hai stream. Khi reconnect, GET command pending nếu cần khôi phục chi tiết trạng thái lệnh.

Registration và initial snapshot đồng bộ dưới state lock; callbacks từ MQTT/REST được serialize qua cùng lock rồi đưa vào event loop. Queue mỗi client giới hạn 64 batch, cross-thread dispatch giới hạn 256 callback; client chậm bị đóng 1013 để reconnect/resnapshot; batch schema lỗi đóng 1011. Send timeout 5s. Không có xác nhận delivery từ mọi client; REST/SQLite là nguồn để khôi phục.

Origin browser phải thuộc allowlist; CLI không có Origin được phép cho demo local. Không nhận gate commands qua WS (đóng 1008). Chưa authentication trong MVP; dùng localhost. Frontend hiện chưa có adapter, không sửa ở giai đoạn này.

## SQLite migration và restart

Schema v2 giữ parking_slots/gate_commands; mở parking_events nhận GATE, thêm gate_state và gate_ack_audit. Khi mở DB v1, tạo file <db>.before-phase04.bak trước migration; migration trong transaction giữ events cũ và sequence. Không xóa database. File backup do lần nâng đầu tiên tạo được giữ lại.

Gate state last-known được lưu, nhưng restart confirmed=false; command còn PENDING được chuyển TIMEOUT/BACKEND_RESTART, không gửi lại. Parking slots và heartbeat/reconnect giữ luật giai đoạn 3. gate_ack_audit lưu ID/status/received_at/outcome, kể cả ACK lạ/trùng/muộn; audit không tạo lượt xe. Lịch sử full chưa pagination, một process/worker.

## Kiểm thử và giới hạn

Tests dùng temp DB, fake MQTT/clock; real HTTP/WS smoke cũng dùng fixtures cục bộ và không publish MQTT thật. Không coi tests là bằng chứng Wokwi/servo. Xem ../docs/LUU-TRU/phase-04/phase-04-realtime-gate-report.md và ../docs/LUU-TRU/phase-04/phase-04-manual-test.md. Dừng ở giai đoạn 4, không tự chuyển 5.

Tham chiếu API: https://fastapi.tiangolo.com/advanced/websockets/ và https://eclipse.dev/paho/files/paho.mqtt.python/html/client.html.


## Tài liệu hiện hành

Xem [mục lục docs](../docs/README.md) và [báo cáo chung cả ba thành viên](../docs/BAO-CAO-NHOM/README.md). Các báo cáo Phase là tài liệu lịch sử, nay lưu dưới docs/LUU-TRU/.
