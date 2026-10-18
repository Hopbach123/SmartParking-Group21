# Báo cáo giai đoạn 03 — MQTT Device → FastAPI → SQLite

Ngày 18/10/2026. Workspace: F:/HocTap/Nam4/IOT/Project_IOT/SmartParking-Group21.

## 1. Phạm vi và điều kiện

Giai đoạn 2 đã có 24 test PASS và HTTP smoke test; regression được chạy lại trong bộ 74 test giai đoạn này. Contract v1 D01–D08 đã được người dùng duyệt trực tiếp trước giai đoạn 2; bản contract gốc không bị thay đổi ở giai đoạn này.

Người dùng cung cấp bằng chứng thủ công Device↔MQTTX: bốn ô publish, OPEN/CLOSE được Device nhận và có gate/status, đôi lúc MQTT timeout/reconnect. Báo cáo này không coi các bằng chứng đó là kiểm thử Device→Backend; kết quả Backend mới được tách riêng dưới đây.

Đã thực hiện MQTT Subscriber, quản lý FastAPI lifespan, schema inbound strict, SQLite/service cập nhật, trạng thái health và watchdog. Không sửa Device/Frontend, không đổi topic/payload/Scene URL, không Gate Controller, không WebSocket, không publish dữ liệu giả vào LIVE. Không commit/push trong lượt này.

## 2. MQTT contract được đối chiếu

Đọc device/sketch.ino và docs/integration-contract-v1.md. Broker giữ nguyên broker.hivemq.com:1883, MQTT 3.1.1 TCP. Device esp32-01. Backend dùng client ID ngẫu nhiên riêng smartparking-group21-backend-..., không trùng client ID ESP32.

Subscribe đúng sáu topic, yêu cầu QoS1; dữ liệu Device publish hiện QoS0 và không retained:

| Topic | Vai trò ở Backend |
|---|---|
| smartparking/group21/slots/P01/state | Validate P01, boolean → trạng thái, ghi service/SQLite |
| smartparking/group21/slots/P02/state | Tương tự P02 |
| smartparking/group21/slots/P03/state | Tương tự P03 |
| smartparking/group21/slots/P04/state | Tương tự P04 |
| smartparking/group21/device/status | Online heartbeat, uptime_ms; Will offline |
| smartparking/group21/gate/status | Validate và ghi log quan sát, không áp dụng ACK |

Không subscribe gate/command, không gọi publish application. Dạng payload giữ nguyên:

```json
{"device_id":"esp32-01","slot_id":"P01","occupied":true}
```
```json
{"device_id":"esp32-01","status":"online","uptime_ms":30000}
```
```json
{"device_id":"esp32-01","status":"offline"}
```
```json
{"device_id":"esp32-01","command_id":"cmd-open-001","status":"OPENED"}
```

Gate status nhận OPENED/CLOSED/ERROR, chỉ log. Gate snapshot vẫn placeholder CLOSED với confirmed=false; không ghi gate_commands và không giả cổng đã được xác nhận.

## 3. Luồng triển khai và xử lý lỗi

```text
Paho callbacks (network thread)
    → bounded queue + epoch + received_at UTC + monotonic time
    → một ingest worker
    → strict parse/validate
    → ParkingService (RLock/transaction)
    → SQLite
    → REST đọc cùng store
```

Callback không ghi DB. Queue tối đa 1000; message cũ qua epoch reconnect bị bỏ; message chờ quá timeout bị bỏ. Queue overflow hoặc lỗi worker được log và thu hồi baseline, không tạo dữ liệu phục hồi giả. Worker tiếp tục xử lý sau lỗi.

Strict validation kiểm tra exact topic allowlist, slot_id khớp topic, device_id, boolean thật, heartbeat uint32, gate enums/ID. JSON hỏng, duplicate keys, NaN/Infinity, invalid UTF-8, fields dư, sai kiểu, payload trên 1024 byte và retained payload bị từ chối mà không sửa trạng thái. Retained bị từ chối vì Device hiện phát non-retained; tránh dùng dữ liệu tồn đọng do publisher khác.

received_at UTC được chụp lúc callback nhận message, ghi vào parking_slots cho packet hợp lệ. Event timestamp là thời gian nhận phía Backend, không giả thời gian cảm biến đo. Duplicate state vẫn touch received_at nhưng không thêm event; revision có thể tăng cho commit metadata.

## 4. Vòng đời, reconnect và timeout

- Lifespan khởi tạo service và MQTT, chạy connect_async/loop_start, dừng client/worker khi shutdown. Connect timeout 5s, reconnect backoff 1–30s.
- Sau mỗi connect đăng ký lại sáu topic. Chỉ báo mqtt CONNECTED khi SUBACK đủ và không bị broker từ chối. Subscribe lỗi hoặc thiếu SUBACK được retry sau 5s trên kết nối hiện tại.
- Broker không truy cập được không làm REST ngừng khởi động; API phản ánh DISCONNECTED.
- Device ONLINE chỉ từ heartbeat hợp lệ. synchronized khi đã có bốn slot tin cậy, heartbeat ONLINE và subscription CONNECTED.
- Mất broker → mqtt DISCONNECTED, device UNKNOWN, public slots UNKNOWN. Will offline hoặc quá 30s không heartbeat → device OFFLINE, slots UNKNOWN.
- Không timeout riêng từng ô vì Device không publish định kỳ ô đứng yên. Heartbeat đều vẫn giữ slot không đổi.
- Online trở lại không tự phục hồi baseline. Cần nhận đủ slot. Nếu Backend khởi động giữa lúc Device đang online, có thể phải restart/reconnect Wokwi sau subscribe để Device republish.
- Uptime giảm có thể là restart hoặc uint32 wrap; code invalidates baseline thận trọng, không khẳng định chắc chắn reboot. Chờ republish, có thể cần reconnect Device.
- Dữ liệu last-known/history giữ trong DB khi mất tin cậy; thu hồi session_id để REST UNKNOWN. Health transition không ghi thêm parking_events.
- Replay cùng last-known sau reconnect không tạo sự kiện hoặc lượt xe trùng. Giá trị khác khi baseline chưa tin cậy là STATUS, không IN/OUT. Trong phiên tin cậy, EMPTY→OCCUPIED là IN, OCCUPIED→EMPTY là OUT.

## 5. Automated tests — PASS

Lệnh trong backend/:

```powershell
.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/phase-03-pytest.xml
.venv\Scripts\python.exe -m pip check
```

**74 passed, 0 failed, 1 warning trong 11.22 giây.** Gồm 24 test giai đoạn 2 và 50 ca MQTT/validation/lifespan mới (tính cả parameterized cases). pip check: No broken requirements found. compileall cho app/tests đạt.

| Nhóm | Kết quả xác minh |
|---|---|
| Mock messages P01–P04 | Mapping boolean, service và SQLite đúng; UTC normalization |
| JSON/UTF-8/size/type | Từ chối input sai, không mutation |
| Topic/mismatch/device | Từ chối topic ngoài allowlist, P01/P02 mismatch, device_id sai |
| Duplicate | Không tạo event trùng, received_at vẫn được cập nhật |
| Reconnect snapshot | Thu hồi trust, resubscribe, cùng last-known không nhân history/IN/OUT |
| Baseline mới khác | STATUS thay vì đếm vehicle entry khi chưa tin cậy |
| Heartbeat timeout | Fake clock vượt 30s → OFFLINE/UNKNOWN, không xóa last-known |
| Heartbeat còn sống | Slot đứng yên hơn 120s vẫn hợp lệ, không timeout sai từng ô |
| Will/uptime | Offline/uptime giảm invalidates baseline |
| Gate status | Validate/log, không update gate hoặc gate_commands, không publish |
| Thread/lifespan | Callback→worker→DB→REST, shutdown không để worker sống |
| Broker/subscription failures | Fake connect fail, SUBACK reject/mất, subscribe lỗi, retry |
| Queue/epoch | Overflow invalidates, packet epoch cũ không khôi phục trạng thái |
| REST health | Connection schema nhận trạng thái thật; MQTT enabled, WS disabled |
| Regression Core | Khởi tạo DB, FULL, UNKNOWN, persistence/restart/constraints/concurrency/rollback vẫn đạt |

Toàn bộ tests dùng fake client, fake clock và DB tạm; không dùng fixture làm bằng chứng ESP32, không gửi fixture lên broker.

Cảnh báo còn lại: Starlette TestClient deprecates httpx; có từ giai đoạn 2, không tắt cảnh báo để che kết quả. Không phải lỗi MQTT runtime.

## 6. Live broker probe — CONNECT/SUBSCRIBE VERIFIED, WOKWI NOT VERIFIED

Đã chạy FastAPI/Uvicorn thật cổng 18023 trên DB tạm, dùng MQTT client thật chỉ đọc, broker.hivemq.com:1883. Probe quan sát 19 lần REST trong khoảng 18s, không publish.

Log lần kiểm tra cuối:

- 22:39:19: server và subscriber khởi động.
- 22:39:26: kết nối broker, gửi subscribe sáu topic.
- 22:39:27: SUBACK thành công, subscription ready.
- 22:39:37: shutdown kết thúc sạch, cả FastAPI lifespan và MQTT worker dừng.

Kết quả: observed_connected=true; ingest_accepted=0; ingest_rejected=0. Không có thông điệp Device trong cửa sổ quan sát. REST trả UNKNOWN đúng khi chưa có baseline, DB không chứa sample xe do test giả lập. Probe dùng DB tạm và không sửa DB runtime mặc định.

**Manual integration: NOT VERIFIED.** Chưa thực hiện được chuỗi gạt công tắc trên phiên Wokwi có kiểm soát trong lượt này. Kết nối broker thành công không chứng minh P01–P04 từ ESP32 đã qua Backend. Không đánh dấu công tắc/servo/network reconnect thực tế PASS từ unit tests hoặc kết quả MQTTX trước đó.

| Kiểm thử thủ công cần người dùng chạy | Trạng thái |
|---|---|
| P01 EMPTY→OCCUPIED→EMPTY, REST và SQLite thay đổi | NOT VERIFIED |
| P02–P04 mapping thực tế | NOT VERIFIED |
| FULL từ bốn công tắc | NOT VERIFIED |
| Restart Wokwi và snapshot không đếm trùng | NOT VERIFIED |
| Wokwi dừng/heartbeat timeout thực | NOT VERIFIED |
| Broker loss/reconnect thực | NOT VERIFIED |

Hướng dẫn từng bước, REST và SQL đọc-only ở **docs/phase-03-manual-test.md**.

## 7. File thay đổi và thêm mới

| File | Thay đổi |
|---|---|
| backend/app/config.py | MQTT enable/host/port/timeout, validation; explicit Settings tests mặc định offline |
| backend/app/main.py | MQTT lifecycle, cleanup qua lifespan, injectable MQTT factory cho tests |
| backend/app/services/parking.py | Nhận received_at, cập nhật connection/trust/baseline, giữ last-known, không duplicate events |
| backend/app/services/mqtt_subscriber.py | Mới: Paho subscriber, queue/worker, strict ingest, watchdog/reconnect/SUBACK |
| backend/app/schemas/mqtt.py | Mới: inbound schemas, topic constants và JSON parser strict |
| backend/app/schemas/__init__.py | Mở connection enums/bool theo contract, health phase MQTT_SUBSCRIBER |
| backend/app/routers/parking.py | Health phản ánh MQTT enabled; không thêm gate hoặc WS route |
| backend/tests/test_mqtt.py | Mới: automated tests MQTT/health/lifespan |
| backend/requirements.txt | Thêm paho-mqtt==2.1.0 |
| backend/requirements-lock.txt | Snapshot dependencies sau cài client |
| backend/.env.example | Cấu hình MQTT demo và heartbeat timeout |
| backend/README.md | Hướng dẫn chạy MQTT, REST, state semantics và giới hạn |
| docs/phase-03-mqtt-report.md | Báo cáo này |
| docs/phase-03-manual-test.md | Checklist manual và lệnh kiểm tra |
| docs/phase-03-pytest.log/xml | Bằng chứng automated tests |
| docs/phase-03-live-probe.log/json | Bằng chứng broker thật/read-only HTTP probe |
| docs/phase-03-protected-checksums.json | SHA-256 Device/Frontend trước/sau |

Không đổi database.py hoặc schema SQLite version 1; dùng cột session_id/received_at đã có. File test_core.py giai đoạn 2 giữ nguyên. Không ghi đè log/báo cáo giai đoạn 2. SHA-256 xác nhận **24/24 file Device/Frontend ngoài node_modules/dist không thay đổi**. Scene URL nguyên trạng.

## 8. Cách chạy để người dùng kiểm thử

```powershell
cd "F:\HocTap\Nam4\IOT\Project_IOT\SmartParking-Group21\backend"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Chờ subscription ready rồi chạy/restart Wokwi. Đọc http://127.0.0.1:8000/docs hoặc GET /api/parking/status. Không chỉ nhìn /health để kết luận Device online; kiểm tra connection.device và synchronized.

Nếu chạy trên máy khác, tạo venv và cài requirements-lock.txt. Không cần cài SQLite riêng. Xem README cho các biến môi trường; app default MQTT true, còn Settings(path) trong tests mặc định false để tránh kết nối mạng ngoài ý muốn.

## 9. Giới hạn và điểm dừng

Broker công cộng không xác thực nguồn payload; dù device_id khớp vẫn có thể là publisher khác. QoS0 có thể mất transition dù heartbeat ONLINE; không có periodic snapshot/sequence/boot ID nên không thể chữa toàn bộ bằng Backend. Không thay firmware để che giới hạn. Nếu packet bị mất khi baseline cần republish, có thể cần restart/reconnect Wokwi thủ công.

Queue/DB lỗi có log và invalidation; không có hàng đợi bền vững MQTT để khôi phục message đã mất. Full history chỉ phù hợp MVP. Single process/worker. Gate status chỉ quan sát, chưa có command correlation, Gate Controller, ACK timeout execution hay WebSocket.

**Giai đoạn 3 đã bàn giao code và automated tests; manual Device→Backend integration còn NOT VERIFIED. Dừng tại đây, chờ xác nhận trước giai đoạn 4.**
