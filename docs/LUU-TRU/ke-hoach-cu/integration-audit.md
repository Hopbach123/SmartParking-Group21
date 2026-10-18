# Integration audit — SmartParking Group 21

Trạng thái: AUDIT HOÀN THÀNH, CONTRACT CHƯA PHÊ DUYỆT. Ngày 18/10/2026.

## Phạm vi và nguồn

Đọc đầy đủ docs/architecture.md, mqtt-contract.md, api-contract.md, integration-plan.md, frontend/docs/DATA_CONTRACT.md tại F:/HocTap/Nam4/IOT/Project_IOT/SmartParking-Group21.

Đối chiếu device/sketch.ino, diagram.json, libraries.txt; frontend/package.json; toàn bộ file JS/JSX trong frontend/src gồm App.jsx, main.jsx, SceneErrorBoundary.jsx, services/parkingService.js. Không có hooks/ hoặc Spline component riêng: hooks và logic scene nằm trong App.jsx. style.css là file CSS còn lại. backend/ chỉ có README.md. Ba tài liệu đầu ra chưa tồn tại khi kiểm tra, không ghi đè tài liệu cũ.

Không sửa source, không cài dependencies, không chạy MQTT hoặc lệnh servo, không triển khai Backend. Đây là audit tĩnh, không thay thế test mạng/hardware. Do chưa có quyền ghi ổ F, bộ tài liệu được giao ngoài source để chép vào docs; chưa tuyên bố đã lưu trong workspace gốc.

## Kiến trúc thực tế

Hai luồng độc lập:

```text
Device code: ESP32 + switches + SG90 ↔ broker.hivemq.com:1883
Frontend: thao tác UI → parkingService RAM → useSyncExternalStore → UI/Spline
Backend: chưa có source; không có cầu nối giữa hai luồng
```

Kiến trúc đích có FastAPI, SQLite, REST/WebSocket chỉ là kế hoạch. Frontend không có fetch/WebSocket, không có adapter LIVE hoặc API hiện hành. Không thể làm Frontend nhận dữ liệu thật chỉ bằng tạo endpoint Backend mà không bổ sung adapter ở giai đoạn sau.

## MQTT và Device đã xác minh từ source

- Wi-Fi Wokwi-GUEST, password rỗng. WiFiClient TCP, broker.hivemq.com:1883, không TLS/username/password trong source.
- device_id esp32-01; client_id smartparking-group21-esp32-01-wokwi.
- Sensor GPIO13/14/27/26 tương ứng P01–P04, INPUT_PULLUP; LOW=true. Servo GPIO18, 0° đóng/90° mở. diagram.json khớp wiring, thư viện PubSubClient, ESP32Servo, ArduinoJson chưa khóa phiên bản.
- Topics/payload chính xác ở integration-contract-v1.md, giữ nguyên.
- debounce 400ms; retry Wi-Fi/MQTT 5000ms; heartbeat 10000ms; gate wait 700ms; keepalive 15s, socket timeout 3s, buffer MQTT 512 byte.
- Publish slot lúc thay đổi và khi reconnect; không gửi định kỳ slot không đổi. Slot/heartbeat/Will/ACK không retained; publish QoS0, subscribe command yêu cầu QoS1.
- Không timestamp UTC hoặc sequence/session trong payload. uptime_ms là millis, có wrap và không xác định duy nhất một boot.
- Command length 1–256 byte, JSON fields string command_id/action/direction; ID không rỗng, strlen ≤80 byte. action OPEN/CLOSE, direction ENTRY/EXIT. Backend nên phát ID ASCII để giới hạn byte rõ ràng.
- Lỗi JSON, thiếu/sai kiểu field, ID sai: chỉ Serial log và return, không ACK. Sai action/direction sau khi ID hợp lệ: queue ERROR. Busy: queue ERROR.
- ACK chỉ có OPENED/CLOSED/ERROR, không có lý do lỗi. ACK phản ánh trạng thái phần mềm sau 700ms, không có cảm biến đo góc.
- Chỉ nhớ lệnh hoàn tất gần nhất trong RAM; không chống trùng bền vững. Một pending ACK duy nhất có thể bị ghi đè bởi phản hồi tiếp theo trước khi publish. Nhận lại ID đang chạy có thể ERROR; ACK hoàn tất sau đó vẫn có thể đến. ID hoàn tất cũ trùng nhưng action khác có thể nhận ACK cũ vì firmware không đối chiếu action.
- Không phát trạng thái gate khi boot/reconnect nếu không có command ACK. Servo về 0° ở setup nhưng Backend không quan sát trực tiếp điều đó. Không có luật cấm ENTRY khi FULL trong firmware; direction hiện được validate/log, không phân thành hai servo.

## Frontend đã xác minh

React/React DOM ^18.3.1, Vite ^6.4.4, plugin React ^4.3.4, react-spline ^4.0.0, Runtime 2.0.93, Recharts ^2.15.0, Lucide ^0.468.0. Đây là version ranges khai báo trừ Runtime cố định, không khẳng định resolved versions của mọi package.

Store snapshot: {schema_version:'1.0',source:'DEMO',slots:{P01..P04},gate:'CLOSED',timestamp:ISO UTC,events:[]}. Slot enums EMPTY/OCCUPIED/UNKNOWN, gate OPEN/CLOSED. Snapshot/slots/events đóng băng, getParkingStatus đồng bộ và tham chiếu ổn định giữa cập nhật. subscribe thông báo sau thay đổi. validateParkingStatus chưa kiểm tra events/source và chỉ kiểm timestamp bằng regex + Date.parse, không phải full schema strict.

IN khi trạng thái mới OCCUPIED (kể cả UNKNOWN→OCCUPIED); OUT chỉ OCCUPIED→EMPTY; thay đổi khác STATUS. Gate event dùng slotId GATE, type GATE. Không tạo sự kiện cho trạng thái trùng. IN/OUT được tính từ events, biểu đồ lọc IN theo slotId. UI không đọc API statistics độc lập.

DEMO MODE và mô tả mock được ghi cứng trên UI. UNKNOWN hiện do nút giả lập, không có timeout mạng. FULL nếu 4 OCCUPIED; AVAILABLE khi ít nhất một EMPTY; còn lại UNKNOWN. UNKNOWN ẩn xe, màu #94a3b8; EMPTY ẩn/xanh #22c55e; OCCUPIED hiện/cam #f97316.

RESET thay store về 4 EMPTY/CLOSED, xóa events/thống kê, timestamp mới; không reset page hoặc axis/chiều local. Refresh tạo lại store; axis='' và chiều +1. OPEN không xoay 3D khi chưa chọn axis. Biến direction trong App là chiều xoay ±1, KHÔNG PHẢI direction ENTRY/EXIT của MQTT.

Spline scene không đổi: https://prod.spline.design/NNU0y3In1BxfOzsL/scene.splinecode. App giữ instance useRef, tìm 12 object, đóng bằng rotation gốc. Gate mapping Boolean khiến UNKNOWN/PENDING không được thể hiện đúng nếu nhét vào trường gate. Error Boundary chỉ xử lý scene, không phải mất Backend. onError đang truyền vào Spline không đủ bằng chứng là hook lỗi Runtime hợp lệ; App còn có Error Boundary và timeout 30s.

## Mapping và các khoảng trống

| Device | Backend dự kiến | Frontend hiện có | Vấn đề |
|---|---|---|---|
| occupied boolean + slot_id | chuẩn hóa và timestamp server | slots.P01 enum | Validate topic khớp slot_id, không dùng bool('false') |
| Slot publish khi đổi | giữ last-known nếu heartbeat còn sống | UNKNOWN enum | Timeout theo từng slot đơn thuần sẽ sai |
| online/offline + uptime_ms | health/epoch, không coi uptime là UTC | chưa có health UI | Broker restart có thể mất slot ban đầu vì không retained |
| action CLOSE | lệnh trạng thái CLOSED | gate CLOSED | Cần map CLOSED→CLOSE |
| ACK OPENED | xác nhận OPEN | gate OPEN | Không coi publish thành ACK |
| command direction ENTRY/EXIT | bắt buộc ở API | chỉ OPEN/CLOSE, rotation ±1 | Chưa có direction nghiệp vụ trên UI |
| ACK ERROR / không ACK | command status ERROR/TIMEOUT | chưa pending/error | Không giả CLOSED khi lỗi |
| Boot không gửi gate | confirmed_gate null/unknown | chỉ OPEN/CLOSED | Không thể tương thích trung thực zero-change |
| State replay/reconnect | baseline, chống đếm trùng | UNKNOWN→OCCUPIED là IN | Replaying qua updateSlotStatus đếm xe sai |
| MQTT packet không event id | tạo event id server | history UUID | Không thể tái tạo chính xác chuỗi bị mất QoS0 |
| MQTT dữ liệu thật | LIVE store | hardcoded DEMO + reset mock | Cần adapter/UI tối thiểu ở giai đoạn sau |

## Mâu thuẫn kiến trúc cần chốt

1. Giữ nguyên tuyệt đối Frontend chỉ chạy được DEMO. Ưu tiên giữ layout/Spline/business đã chạy, nhưng LIVE cần adapter và vài chỉ báo/trạng thái mới. Không sửa ở giai đoạn 1.
2. Gate không xác định lúc boot/mất kết nối: đề xuất thêm gate_meta.confirmed=false trong snapshot và UI LIVE tối thiểu; giá trị gate placeholder CLOSED chỉ dùng tương thích hình dạng, không được hiển thị như xác nhận thật. Nếu không chấp nhận metadata/UI, phải mở enum gate UNKNOWN và sửa validator/UI. Không chọn ngầm.
3. Heartbeat timeout phát hiện device offline, không xác nhận từng slot; dropped QoS0 slot có thể stale dù heartbeat sống. Không thể chữa toàn bộ nếu giữ firmware nguyên trạng; định kỳ republish là cải tiến Device cần phê duyệt riêng.
4. ENTRY OPEN khi FULL hoặc thiếu dữ liệu: đề xuất từ chối khi available=0 hoặc health/snapshot chưa tin cậy; EXIT OPEN vẫn cho nếu kết nối và gate command sẵn sàng. Đây không phải chức năng hiện có hay bảo đảm an toàn phần cứng.
5. Không auto-retry gate command sau timeout; ACK đến muộn phải đối chiếu pending/timed-out records, không đổi ERROR thành thành công một cách vô điều kiện. Public broker không xác thực ACK.
6. Đồng bộ history/statistics: đề xuất snapshot đủ events cho quy mô demo, cùng phạm vi lifetime DB; pagination và dataset lớn để sau. Không dùng events trang hiện tại để tính tổng mọi thời gian.

## Kết luận

Nguồn hiện tại đủ để chốt MQTT hiện hành. REST/WS chưa tồn tại và bản v1 đi kèm là DRAFT. Giai đoạn 2 bị chặn bởi phê duyệt contract, không phải do thiếu source audit. Không làm Backend trước khi người dùng chốt các quyết định D01–D08 trong contract.
