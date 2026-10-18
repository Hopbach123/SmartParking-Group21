# SMART PARKING – DEVICE V4 (Hoàng Nguyên)

**Hướng dẫn thực hành cho người mới – Wokwi + MQTT Viewer trên MacBook M3**  
Mô hình: 1 ESP32, 4 công tắc P01–P04, 1 servo SG90; dữ liệu trao đổi qua MQTT.  
**Trạng thái xác minh:** đã kiểm tra tĩnh 10/10 mục (`tests/verify_static.py`); **chưa thực sự biên dịch trên Wokwi hoặc kiểm thử mạng/servo với broker trực tiếp**. Chỉ đánh dấu bài test PASS khi chính bạn quan sát kết quả.

## 1. Tạo/mở Wokwi

1. Mở https://wokwi.com/projects/new/esp32 hoặc dự án Wokwi sẵn có, đăng nhập để lưu dự án.
2. Tab `sketch.ino`: chọn tất cả (Cmd+A) và dán nội dung file `sketch.ino` trong thư mục này.
3. Tab `diagram.json`: nếu bạn đã hoàn thành bước 2 và mạch đúng thì **giữ nguyên**; nếu chưa, thay bằng nội dung file `diagram.json` trong thư mục này.
4. File `libraries.txt`: đảm bảo mỗi thư viện nằm trên một dòng: `PubSubClient`, `ESP32Servo`, `ArduinoJson`. Trên giao diện Wokwi, dùng Library Manager để thêm nếu cần.
5. Bấm **Play (▶)**, mở **Serial Monitor** ở phía dưới. Đợi báo Wi-Fi và MQTT kết nối; lần đầu có thể chậm hơn.
6. Nếu có lỗi `Compilation error`, xem dòng báo lỗi **đầu tiên**, kiểm tra phiên bản thư viện, gửi log để sửa trước khi test tiếp.

### Bảng đấu nối

| Bộ phận | Chân của linh kiện | ESP32 |
|---|---|---|
| P01 | switch chân giữa 2; chân 1 nối GND | GPIO13; GND |
| P02 | switch chân giữa 2; chân 1 nối GND | GPIO14; GND |
| P03 | switch chân giữa 2; chân 1 nối GND | GPIO27; GND |
| P04 | switch chân giữa 2; chân 1 nối GND | GPIO26; GND |
| SG90 | PWM | GPIO18 |
| SG90 | V+ | 5V |
| SG90 | GND | GND |

Firmware đọc `INPUT_PULLUP`: chân GPIO về GND = `occupied:true`, ngược lại = `false`. Nếu cảm biến liên tục báo có xe dù công tắc ở vị trí trống, kiểm tra hướng công tắc và dây GND.

## 2. Cài MQTT Viewer trên macOS M3

1. Vào https://mqttviewer.app/download/mac/ và chọn **Download Apple Silicon**; M3 dùng Apple Silicon, không tải bản Intel.
2. Mở ZIP đã tải, kéo **MQTT Viewer** vào **Applications**, sau đó mở ứng dụng.
3. Chọn **Add Connection** (hoặc kết nối mới) và nhập:

| Trường | Giá trị |
|---|---|
| Name | `SmartParking-Group21` |
| Host | `broker.hivemq.com` |
| Port | `1883` |
| Protocol | `MQTT/TCP` (không dùng WebSocket cho ứng dụng desktop) |
| MQTT version | `3.1.1` |
| Client ID | `smartparking-nguyen-viewer` (khác ID ESP32) |
| TLS/SSL | Tắt cho thử nghiệm cổng 1883 |
| Username / Password | Để trống |
| Subscriptions | `smartparking/group21/#` |

4. Bấm **Connect** và kiểm tra trạng thái đã kết nối. Nếu có nút **Save**, bấm để lưu.
5. Với MQTT Viewer, thông điệp được xem trong **List/topic tree**. Muốn xem nhiều gói tin, chọn topic và kiểm tra lịch sử.

**Quan trọng:** Đây là broker **công cộng**. Dùng dữ liệu giả, không đưa thông tin nhạy cảm. Người khác có thể xem/gửi trên các topic công khai. Topic `smartparking/group21` có nguy cơ trùng với người khác; nếu đổi phải đồng bộ cả firmware, MQTT Viewer và Backend. Không kết nối cả hai client bằng cùng Client ID.

## 3. Các topic MQTT

| Topic | Ai gửi | Ai nhận | Công dụng |
|---|---|---|---|
| `smartparking/group21/slots/P01/state` | ESP32 | MQTT Viewer/Backend | Trạng thái P01 |
| `smartparking/group21/slots/P02/state` | ESP32 | MQTT Viewer/Backend | Trạng thái P02 |
| `smartparking/group21/slots/P03/state` | ESP32 | MQTT Viewer/Backend | Trạng thái P03 |
| `smartparking/group21/slots/P04/state` | ESP32 | MQTT Viewer/Backend | Trạng thái P04 |
| `smartparking/group21/device/status` | ESP32 | MQTT Viewer/Backend | Heartbeat / Will offline |
| `smartparking/group21/gate/command` | MQTT Viewer/Backend | ESP32 | Lệnh OPEN/CLOSE |
| `smartparking/group21/gate/status` | ESP32 | MQTT Viewer/Backend | Phản hồi OPENED/CLOSED/ERROR |

### Dữ liệu mẫu

**Slot (ESP32 publish):**
```json
{"device_id":"esp32-01","slot_id":"P01","occupied":true}
```
**Heartbeat:**
```json
{"device_id":"esp32-01","status":"online","uptime_ms":30000}
```
**Lệnh mở cổng (gửi từ MQTT Viewer):**
```json
{"command_id":"test-open-001","action":"OPEN","direction":"ENTRY"}
```
**Lệnh đóng cổng:**
```json
{"command_id":"test-close-002","action":"CLOSE","direction":"ENTRY"}
```
**Phản hồi từ ESP32:**
```json
{"device_id":"esp32-01","command_id":"test-open-001","status":"OPENED"}
```

## 4. Chạy demo nhanh từ đầu đến cuối

**A – ESP32 gửi trạng thái:**
1. Mở MQTT Viewer, Connect, subscribe `smartparking/group21/#`.
2. Bấm Play trên Wokwi. Chờ log `[MQTT] CONNECTED`, `[MQTT] SUBSCRIBE OK`, bốn dòng `[SLOT P01]` ... `[SLOT P04]` và `[HEARTBEAT]`.
3. Gạt công tắc P01 về GND và giữ hơn 0,4 giây; Wokwi in `[SENSOR] P01 -> CO XE`.
4. Trong MQTT Viewer chọn `slots/P01/state`, phải thấy JSON `"occupied":true`. Gạt về trống, phải thấy `false`.
5. Gạt cả P01–P04 sang có xe, Wokwi dự kiến ghi `[PARKING] Busy=4 Free=0 FULL`.

**B – Điều khiển cổng:**
1. Trong MQTT Viewer mở mục **Publish**.
2. Topic gửi: `smartparking/group21/gate/command`.
3. Payload: `{"command_id":"test-open-001","action":"OPEN","direction":"ENTRY"}`.
4. Đặt **Retain = OFF**, QoS 0 cho bài thử; bấm Publish.
5. Trở về Wokwi: servo hướng 90°; log có `[GATE] OPENED` và `[GATE STATUS]`.
6. Trong MQTT Viewer chọn `smartparking/group21/gate/status`, đối chiếu `command_id=test-open-001`, `status=OPENED`.
7. Gửi `{"command_id":"test-close-002","action":"CLOSE","direction":"ENTRY"}` rồi kiểm tra servo về 0° và phản hồi `CLOSED`.
8. **Luôn dùng command_id mới cho thao tác mới**, trừ bài test gửi lặp có chủ đích.

## 5. Test nâng cao từng chức năng

| Mã | Thao tác | Kết quả cần nhìn thấy |
|---|---|---|
| T01 | Khởi động Wokwi | Wi-Fi & MQTT connected, subscribe OK, 4 trạng thái ban đầu |
| T02 | Chuyển P01 sang có xe và về trống | MQTT nhận true, sau đó false |
| T03 | Cả 4 công tắc về có xe | Busy=4 Free=0 FULL |
| T04 | Gửi OPEN `command_id` mới | Servo 90°, `gate/status=OPENED` |
| T05 | Gửi CLOSE `command_id` mới | Servo 0°, `gate/status=CLOSED` |
| T06 | Gửi action `FLY` có `command_id` | Không di chuyển servo, `gate/status=ERROR` |
| T07 | Gửi lại `command_id` của lệnh đã hoàn thành gần nhất | Nhận lại phản hồi trước đó, không di chuyển servo lần nữa |
| T08 | Đợi 30 giây trong khi online | Khoảng 3 heartbeat, `uptime_ms` tăng |
| T09 | Stop / Play Wokwi | ESP32 khởi động lại và gửi lại trạng thái bốn ô sau khi reconnect |
| T10 | Giả lập mất MQTT trong lúc firmware chạy | Khi kết nối lại, tự subscribe, heartbeat và gửi lại 4 ô |

**Cách test T10 an toàn:** tại đầu hàm `void loop()` thêm tạm:
```cpp
static bool disconnectedOnce = false;
if (!disconnectedOnce && millis() > 30000 && mqtt.connected()) {
  disconnectedOnce = true;
  Serial.println("[TEST] Force MQTT disconnect");
  mqtt.disconnect();
}
```
Bấm Stop/Play, chờ đủ 30 giây, quan sát `[TEST]` rồi `[MQTT] CONNECTED` và 4 dòng SLOT mới. **Xóa đoạn test** khi hoàn thành.

**Chống nhiễu:** firmware chờ trạng thái ổn định ít nhất 400 ms trước khi ghi nhận. Thao tác bằng chuột không phải thiết bị đo độ chính xác thời gian, nên chỉ quan sát dấu hiệu giảm nhấp nháy. **Chặn ENTRY khi bãi FULL:** phải kiểm thử tại Backend, Device không tự từ chối lệnh trực tiếp từ MQTT Viewer.

## 6. Lỗi thường gặp

| Hiện tượng | Kiểm tra / cách xử lý |
|---|---|
| `PubSubClient.h not found` hoặc `ESP32Servo.h not found` | Kiểm tra `libraries.txt`, Library Manager và tên thư viện |
| Không hiện `WIFI CONNECTED` | Kiểm tra `Wokwi-GUEST`, Internet và chạy lại Wokwi; Mac M3 không phải nguyên nhân mặc định |
| `[MQTT] FAILED state=-2/-4` | Kiểm tra host/port và gateway mạng Wokwi; thử lại broker khi lỗi tạm thời |
| MQTT Viewer không Connect | Host `broker.hivemq.com`, port TCP `1883`, SSL tắt; xem **View logs** trong menu kết nối |
| Viewer Connect nhưng không thấy topic | Subscribe `smartparking/group21/#`, thử gạt công tắc hoặc Stop/Play Wokwi |
| Servo không quay | Kiểm tra PWM GPIO18, V+ 5V, GND, thư viện, log `[GATE]`, MQTT command topic |
| Lệnh OPEN không chạy lại | Dùng `command_id` mới vì firmware có cơ chế bỏ lệnh trùng gần nhất |
| Có thông điệp `offline` sau khi bấm Stop | Last Will của MQTT chỉ được broker phát sau khi phát hiện mất kết nối bất thường, có độ trễ |

## 7. Giới hạn kỹ thuật cần nêu trung thực trong báo cáo

- **Chưa có timestamp từ ESP32.** Tài liệu nhóm dùng `timestamp` ISO UTC; Backend nên gắn `received_at` UTC và xác định đây là giờ nhận ở server, không phải thời điểm cảm biến đo.
- MQTT publish ở mức QoS 0; `publish()` trả `true` không phải xác nhận Backend đã nhận/lưu dữ liệu. Khi offline, chỉ trạng thái hiện tại được đồng bộ lại, không có toàn bộ lịch sử thay đổi.
- Các thông điệp SLOT hiện không retained; MQTT Viewer kết nối sau thời điểm publish có thể không thấy snapshot cũ cho đến khi có update hoặc khởi động lại.
- `OPENED/CLOSED` là xác nhận theo logic firmware sau 700 ms, **không phải** phản hồi cảm biến hành trình thật.
- Chống lặp chỉ nhớ **command_id hoàn thành gần nhất** trong RAM; restart hoặc gửi chuỗi lệnh xen kẽ không bảo đảm idempotency toàn bộ.
- Bộ đệm phản hồi gate đang giữ một phản hồi chờ; nếu có nhiều lệnh sai liên tiếp rất nhanh, có thể bị ghi đè. Bản thử này phù hợp cho demo từng lệnh, chưa bảo đảm delivery của hệ thống sản xuất.
- Không sử dụng broker công cộng và kết nối plaintext cho dữ liệu thực tế hoặc môi trường triển khai chính thức.

## 8. Bàn giao cho nhóm và thu thập minh chứng

Chụp `screenshots/01-wokwi-circuit.png`, `02-wifi-mqtt.png`, `03-slots.png`, `04-heartbeat.png`, `05-gate-open.png`, `06-gate-close.png`, `07-reconnect.png` (chỉ lưu những ảnh thực sự chụp). Quay video 1–2 phút: mở Wokwi, gạt P01, gạt cả bốn ô, xem MQTT Viewer, Publish OPEN/CLOSE, cho xem `gate/status`.

Gửi cho Hợp và Phước: đường link dự án Wokwi, `sketch.ino`, `diagram.json`, `libraries.txt`, `README.md`, bảng test, ảnh/video và các topic/payload ở mục 3. Backend cần subscribe `slots/+/state`, `device/status`, `gate/status`, kiểm tra trạng thái bãi trước khi publish `gate/command`.

**Nguồn hướng dẫn chính thức:**
- Wokwi ESP32 Wi-Fi: https://docs.wokwi.com/guides/esp32-wifi
- MQTT Viewer Mac: https://mqttviewer.app/download/mac/
- MQTT Viewer kết nối broker: https://mqttviewer.app/walkthroughs/connect-broker/
