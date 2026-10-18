# Integration contract v1 — DRAFT / CHƯA PHÊ DUYỆT

Phiên bản đề xuất 1.0, 18/10/2026. Phần MQTT dưới đây là hiện trạng source; REST/WS và chính sách LIVE là ĐỀ XUẤT, chưa có endpoint hoặc consumer hoạt động. Không thay thế tài liệu cũ trước khi được duyệt.

## 1. MQTT hiện hành — giữ nguyên

Broker broker.hivemq.com:1883 TCP; device_id esp32-01. Backend dùng client_id riêng, không dùng ID của Device.

| Topic chính xác | Publisher | Subscriber dự kiến |
|---|---|---|
| smartparking/group21/slots/P01/state | Device | Backend |
| smartparking/group21/slots/P02/state | Device | Backend |
| smartparking/group21/slots/P03/state | Device | Backend |
| smartparking/group21/slots/P04/state | Device | Backend |
| smartparking/group21/device/status | Device | Backend |
| smartparking/group21/gate/command | Backend | Device |
| smartparking/group21/gate/status | Device | Backend |

Slot:
```json
{"device_id":"esp32-01","slot_id":"P01","occupied":true}
```
false tương ứng EMPTY, true OCCUPIED; Device không phát UNKNOWN. Payload phải object, đúng device_id và slot_id khớp topic; occupied là JSON boolean thật. Không suy diễn string/number thành boolean.

Heartbeat:
```json
{"device_id":"esp32-01","status":"online","uptime_ms":30000}
```
Will:
```json
{"device_id":"esp32-01","status":"offline"}
```
Commands:
```json
{"command_id":"cmd-open-001","action":"OPEN","direction":"ENTRY"}
```
```json
{"command_id":"cmd-close-001","action":"CLOSE","direction":"EXIT"}
```
command_id ASCII UUID/ID 1–80 byte, tổng JSON UTF-8 ≤256 byte. action OPEN/CLOSE; direction ENTRY/EXIT. Backend publish retained=false (đề xuất QoS1; ACK publish hiện QoS0, không có exactly-once).

Gate statuses:
```json
{"device_id":"esp32-01","command_id":"cmd-open-001","status":"OPENED"}
```
status OPENED/CLOSED/ERROR; không timestamp, error reason hoặc boot/session id. Không ACK cho một số payload lỗi; mọi command đều cần timeout tại Backend. Chỉ có một servo; ENTRY/EXIT là ý nghĩa nghiệp vụ do Backend kiểm soát.

## 2. State model dự kiến

Giữ core của Frontend; mở rộng metadata, không sửa firmware. Ví dụ JSON hợp lệ của snapshot LIVE **chưa được UI hiện tại xử lý**:

```json
{
  "schema_version":"1.0",
  "source":"LIVE",
  "timestamp":"2026-10-18T12:00:00.000Z",
  "slots":{"P01":"EMPTY","P02":"OCCUPIED","P03":"UNKNOWN","P04":"EMPTY"},
  "gate":"CLOSED",
  "gate_meta":{"confirmed":false,"confirmed_at":null,"pending_command_id":null},
  "connection":{"mqtt":"CONNECTED","device":"ONLINE","synchronized":false},
  "stream_id":"server-session-uuid",
  "revision":1,
  "events":[]
}
```

- Exactly P01–P04; EMPTY/OCCUPIED/UNKNOWN. LIVE boot UNKNOWN tới khi có dữ liệu hợp lệ; không boot EMPTY như DEMO.
- gate vẫn OPEN/CLOSED cho core compatibility; gate_meta.confirmed=false nghĩa là **chưa biết**, giá trị gate khi đó chỉ last-known/placeholder. UI LIVE phải hiển thị chưa xác nhận, không tự gọi CLOSED là trạng thái thật. Adapter chưa tồn tại; đây là thay đổi tối thiểu cần duyệt (D02).
- acknowledged OPENED→OPEN, CLOSED→CLOSED. ERROR/timeout không gán gate về CLOSED. Không nhận ACK sai ID/device/action; ACK mâu thuẫn target được ghi lỗi, không hoàn tất lệnh thành công.
- timestamp UTC ISO là thời gian commit snapshot server, không phải thời gian cảm biến đo. Event timestamp lấy received_at server. Giữ riêng last_received_at trong DB nếu cần, không lấy uptime làm UTC.
- stream_id thay đổi khi Backend restart; revision tăng trên mọi commit state/event/command/health trong cùng stream. Một transaction → một snapshot bất biến.
- mqtt CONNECTED/DISCONNECTED; device ONLINE/OFFLINE/UNKNOWN; synchronized=true chỉ khi đã có baseline bốn ô hợp lệ cho phiên kết nối quan sát được. Không bảo đảm phát hiện mọi reboot vì Device thiếu session id.
- Đề xuất mất broker, Will offline hoặc không có heartbeat hợp lệ >30s: invalidate LIVE slots thành UNKNOWN, confirmed gate=false; lưu last-known riêng. Không timeout từng ô khi heartbeat đang sống. Heartbeat trở lại một mình không đủ khôi phục baseline đã invalidate; chờ Device republish (có thể cần restart/reconnect Device nếu Backend vừa khởi động và slot không đổi). Không tự gửi lệnh cổng để dò trạng thái.

## 3. Event và thống kê dự kiến

Giữ fields UI đã dùng:
```json
{"id":"event-uuid","timestamp":"2026-10-18T12:00:00.000Z","slotId":"P02","type":"IN","previous":"EMPTY","current":"OCCUPIED"}
```

slotId P01–P04 hoặc GATE; type IN/OUT/STATUS/GATE. Trước/sau của slot dùng slot enums; gate event chỉ tạo khi có chuyển OPEN/CLOSED đã xác nhận. Metadata command/health nằm riêng, không nhét ERROR vào gate enums.

LIVE đề xuất IN chỉ EMPTY→OCCUPIED, OUT chỉ OCCUPIED→EMPTY; UNKNOWN→known là STATUS/baseline, không tăng đếm xe. Khác DEMO hiện tại UNKNOWN→OCCUPIED tính IN; không sửa DEMO. Trạng thái trùng không tạo event; heartbeat chỉ cập nhật health, không tạo IN/OUT. Không biến refresh/reconnect thành xe vào mới. Không thể phục hồi số lượt bị mất khi MQTT QoS0 rơi gói.

MVP đề xuất events là toàn bộ lịch sử trong DB demo, mới nhất trước; entries/exits và per-slot counts đếm cùng tập hợp đó, không reset khi refresh hoặc reconnect. Chưa có pagination trong v1 để giữ thuật toán UI; khi history lớn phải giới hạn đồng bộ có thiết kế mới, không cắt im lặng rồi vẫn gọi thống kê tổng. RESET và nút mô phỏng chỉ DEMO; không có API xóa DB/reset physical state trong LIVE v1.

## 4. REST đề xuất

Base URL cấu hình ngoài source; ví dụ local Backend 127.0.0.1:8000, CORS allowlist chính xác origin dev/preview được chốt, không mở wildcard tùy tiện. Không gọi những URL này trong giai đoạn 1.

| Method/path | Request | Response |
|---|---|---|
| GET /api/parking/status | — | 200 snapshot mục 2 |
| GET /api/parking/events | — | 200 {schema_version,stream_id,revision,events} |
| GET /api/parking/statistics | — | 200 {schema_version,stream_id,revision,scope,entries,exits,by_slot} |
| POST /api/parking/gate | {command_id,status,direction} | 202 command record sau khi chấp nhận, chưa phải ACK |
| GET /api/parking/commands/{command_id} | — | 200 command record, hoặc 404 |

Không cung cấp PATCH slot LIVE trong MVP; endpoint mô phỏng của tài liệu cũ vẫn chưa tồn tại. Giữ API lấy thống kê cho kiểm tra nhưng UI tương lai phải chọn cùng revision; v1 UI có thể giữ tính từ full events snapshot, không trộn ba GET khác revision.

Request gate ví dụ:
```json
{"command_id":"cmd-open-001","status":"OPEN","direction":"ENTRY"}
```
status OPEN/CLOSED được map action OPEN/CLOSE. direction bắt buộc cho cả đóng và mở, không có mặc định ngầm. ID do client sinh cho retry cùng request; một ID với payload khác trả 409. Một Device chỉ một command in-flight.

Command record ví dụ:
```json
{"command_id":"cmd-open-001","requested_status":"OPEN","direction":"ENTRY","state":"PENDING","created_at":"2026-10-18T12:00:00.000Z","completed_at":null,"error_code":null}
```
state PENDING/CONFIRMED/ERROR/TIMEOUT. Persist PENDING trước publish; lỗi publish trả 503 kèm ID, ghi ERROR và không hứa lệnh chưa từng đến Device. ACK timeout đề xuất 5s. Không tự phát lại lệnh có tác động sau timeout/restart; idempotency lookup trả record cũ, không republish. Sau restart, pending chuyển TIMEOUT do không biết chắc đã thực thi. ACK muộn được lưu audit; có thể cập nhật last-known/confirmed gate nếu xác minh không có command mới hơn, nhưng record TIMEOUT không tự đổi CONFIRMED. Quy tắc late ACK cần test trước triển khai.

Đề xuất policy: ENTRY+OPEN bị chặn nếu available=0, hoặc health/baseline chưa tin cậy; EXIT+OPEN vẫn có thể thực hiện khi thiết bị online và command slot rảnh, kể cả parking FULL. CLOSE không tự động vì FULL, không có auto-close. Đây là mô hình demo không có cảm biến chống kẹt; không cam kết an toàn cho barrier thật.

Error envelope:
```json
{"error":{"code":"PARKING_FULL","message":"No available slot","command_id":"cmd-open-001"}}
```
422 invalid body (chuẩn hóa cả lỗi validation FastAPI), 409 FULL/busy/ID conflict/unsynchronized, 503 disconnected/publish unavailable, 404 command missing. Retry cùng ID/cùng body trả record cũ (202 nếu PENDING, 200 nếu terminal), không tạo command mới.

## 5. WebSocket đề xuất

Path /ws/parking. Chỉ dùng full snapshot cho v1, không delta:
```json
{"type":"parking.snapshot","schema_version":"1.0","data":{"schema_version":"1.0","source":"LIVE","timestamp":"2026-10-18T12:00:00.000Z","slots":{"P01":"UNKNOWN","P02":"UNKNOWN","P03":"UNKNOWN","P04":"UNKNOWN"},"gate":"CLOSED","gate_meta":{"confirmed":false,"confirmed_at":null,"pending_command_id":null},"connection":{"mqtt":"CONNECTED","device":"UNKNOWN","synchronized":false},"stream_id":"server-session-uuid","revision":0,"events":[]}}
```

Gửi snapshot đầu ngay khi kết nối, sau mỗi transaction gửi bản mới nhất. Đề xuất thêm gate command updates:
```json
{"type":"gate.command","schema_version":"1.0","stream_id":"server-session-uuid","revision":2,"data":{"command_id":"cmd-open-001","requested_status":"OPEN","direction":"ENTRY","state":"PENDING","created_at":"2026-10-18T12:00:00.000Z","completed_at":null,"error_code":null}}
```
Một command update có thể cùng revision với parking.snapshot; adapter theo dõi revision riêng theo loại message, không bỏ snapshot chỉ vì đã nhận command cùng revision. Command GET/REST là nguồn để khôi phục nếu WS mất message. Server gửi snapshot liên quan sau command message; serialize các commit tránh đảo thứ tự.

Client subscribe WS và nhận snapshot trước; nếu dùng GET đồng thời, áp dụng chỉ revision mới hơn trong cùng stream; stream mới yêu cầu thay dataset, không so số revision với stream cũ. Mất WS: hiển thị offline/stale, không phát state EMPTY hay xóa history; reconnect backoff nhận full snapshot. Không phát gate command qua WS trong v1.

Frontend hiện chưa thể tiêu thụ nguyên bản các message này: cần adapter parse/validate envelope.data, thay snapshot và notify, không replay updateSlotStatus từng event; giữ getParkingStatus sync. Cần thêm mode LIVE/DEMO, gate confirmation/pending/error, direction nghiệp vụ, ngăn nút mock/reset ở LIVE. Core Spline, topic, Scene URL giữ nguyên; phần thể hiện gate chưa xác nhận phải tránh vẽ trạng thái như đã xác nhận.

## 6. Quyết định cần người dùng chốt

| ID | Đề xuất cần xác nhận | Tác động |
|---|---|---|
| D01 | Cho phép adapter và UI LIVE tối thiểu ở giai đoạn sau; giữ nguyên DEMO/scene | Không thể tích hợp với Frontend hoàn toàn bất biến |
| D02 | gate OPEN/CLOSED + gate_meta.confirmed; UNKNOWN tại LIVE boot cho slots; không coi placeholder CLOSED là thật | Thay đổi UI nhận biết gate chưa xác định; phương án khác là mở enum gate UNKNOWN |
| D03 | direction ENTRY/EXIT bắt buộc, UI thêm lựa chọn; không ánh xạ từ chiều xoay ±1 | Tránh chọn ngầm hướng nghiệp vụ |
| D04 | ENTRY OPEN chặn FULL hoặc chưa sync, EXIT không chặn theo FULL; command vẫn cần online/not busy | Luật nghiệp vụ hiện chưa có trong firmware/UI |
| D05 | Heartbeat timeout 30s, ACK timeout 5s, không auto-retry gate; chấp nhận giới hạn QoS0/no periodic slot | Nếu cần đảm bảo freshness từng ô phải yêu cầu sửa Device riêng |
| D06 | LIVE UNKNOWN→known là STATUS, chỉ EMPTY→OCCUPIED tính IN; DEMO giữ nguyên | Tránh đếm baseline thành xe vào |
| D07 | REST/WS full snapshots, stream_id/revision, lịch sử lifetime DB demo chưa pagination; không RESET/PATCH slot LIVE | Ranh giới dữ liệu và phạm vi MVP |
| D08 | Giữ broker công cộng hiện có chỉ cho demo tin cậy giới hạn; triển khai Backend một process worker ở MVP | Public ACK không xác thực; nhiều worker sẽ nhân MQTT consumers nếu chưa có coordination |

Chưa quyết định nào được coi là đã duyệt. Kết thúc giai đoạn 1 tại tài liệu này, chờ xác nhận D01–D08 trước lập trình Backend.
