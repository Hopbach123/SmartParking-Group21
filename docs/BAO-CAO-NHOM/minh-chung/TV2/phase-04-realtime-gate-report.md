# Báo cáo giai đoạn 04 — WebSocket & Gate Control

Ngày tổng hợp: 18/10/2026. Workspace đích: F:/HocTap/Nam4/IOT/Project_IOT/SmartParking-Group21.

## 1. Trạng thái bàn giao và phạm vi

**Đã chuẩn bị và kiểm thử code giai đoạn 4; CHƯA áp dụng vào source ở F.** Công cụ chỉ cấp network, không cấp filesystem write cho backend/docs ổ F trong lượt này. Không cố ghi vượt quyền. Bộ cập nhật nằm trong outputs/phase-04, gồm backend/, docs/, manifest source gốc, apply-phase04.ps1 và INSTALL.md. Không có database runtime, .env hoặc .venv của người dùng trong gói.

Người dùng đã xác nhận giai đoạn 3 thấy thay đổi EMPTY→OCCUPIED trong log và thống kê; đây là điều kiện tiếp tục, không phải xác nhận Gate/WS giai đoạn 4.

Người dùng đã chọn **giữ nguyên contract v1** khi được hỏi về mâu thuẫn trong prompt: command_id bắt buộc do client gửi; trạng thái wire là PENDING/CONFIRMED/ERROR/TIMEOUT. SUCCESS/FAILED chỉ là cách gọi kết quả chung, không phải enum mới. Backend không tự điền command_id thiếu. Contract, Device, Frontend, MQTT topic/payload và Scene URL không bị chỉnh.

## 2. WebSocket đã triển khai

Endpoint /ws/parking, nhiều client. Ngay khi kết nối hoặc reconnect gửi full parking.snapshot, khớp REST /api/parking/status. Snapshot và đăng ký client được lấy dưới cùng state lock, tránh khoảng trống subscribe/initial snapshot.

Mỗi commit sau DB phát full snapshot. Thay đổi lệnh cổng phát gate.command trước parking.snapshot cùng revision. Snapshot có stream_id/revision; command message có stream_id/revision top-level theo v1. Client cần theo dõi revision riêng theo loại message và dùng REST để resync hoặc GET command pending sau reconnect. Không triển khai delta/replay làm phát sinh sự kiện xe giả.

Emitter nằm sau commit, được serialize bằng ParkingService RLock chung cho REST và MQTT. Snapshot timestamp là thời gian commit server UTC; event/received_at giữ thời gian nhận server, không lấy thời gian uptime của Device. Client không suy thứ tự từ timestamp thay vì revision.

Giới hạn queue: 64 batch/client, 256 dispatch callback qua thread/event loop. Client chậm bị đóng 1013 để reconnect/resnapshot; schema batch lỗi đóng 1011; send timeout 5 giây. WebSocket là server-push, không cho gửi lệnh OPEN/CLOSE qua socket (1008), tránh bypass Gate REST policy. Browser Origin dùng allowlist hiện có; CLI không Origin được dùng cho kiểm thử local.

Đã phát hiện lỗi cancel chập chờn khi đóng hai client gần nhau trong một lượt test cuối. Đã thay cleanup bằng AnyIO task group và cancel shielding có giới hạn; bổ sung regression 25 vòng mở/đóng cặp client, không còn peer/sender treo trong kiểm thử cuối. Không bỏ qua lỗi bằng cách xóa test.

## 3. Gate Controller đã triển khai

### REST và kiểm tra chính sách

POST /api/parking/gate nhận command_id/status/direction. status OPEN/CLOSED; direction ENTRY/EXIT; CLOSED được map MQTT action CLOSE. GET /api/parking/commands/{command_id} trả record bền vững.

- ID ASCII 1–80 ký tự không khoảng trắng; body tổng quát được schema validate, field dư và thiếu ID trả 422 theo error envelope v1.
- Kiểm tra idempotency trước health: cùng ID/cùng status/direction trả record cũ, không publish lại. Cùng ID nhưng body khác → 409 COMMAND_ID_CONFLICT.
- Chỉ một PENDING cho Device, có lock và partial unique index. ID mới khi bận → 409 GATE_BUSY.
- Broker/subscription và Device phải sẵn sàng; publisher kiểm tra heartbeat còn hạn, kết nối Paho còn connected trước publish.
- OPEN ENTRY khi bốn OCCUPIED → 409 PARKING_FULL, không publish. Baseline thiếu tin cậy hoặc có UNKNOWN → từ chối; không tính UNKNOWN là free.
- OPEN EXIT không chặn chỉ vì FULL/baseline ô chưa đủ; vẫn cần MQTT/Device online và command slot rảnh. CLOSE không tự động vì FULL, không có auto-close.

### Vòng đời command

PENDING được commit SQLite trước publish, sau đó WS phát PENDING và snapshot. 202 chỉ nghĩa chấp nhận lệnh/publish, không phải servo đã quay.

Payload MQTT vẫn command_id/action/direction, topic smartparking/group21/gate/command, retained=false. Giai đoạn này dùng **QoS0**, tránh cơ chế Paho tự publish lại QoS1 khi reconnect. Contract v1 mô tả QoS1 là đề xuất, không phải trường payload bắt buộc; lựa chọn triển khai ưu tiên yêu cầu không auto-republish lệnh có tác động. Không tuyên bố exactly-once hoặc đảm bảo không rơi lệnh.

ACK được parser giai đoạn 3 kiểm tra Device/topic/retained/types; Controller đối chiếu command_id và target:

| Tình huống | Record / snapshot |
|---|---|
| Publish được chấp nhận | Vẫn PENDING, chưa confirmed |
| OPENED đúng lệnh OPEN | CONFIRMED, gate OPEN, confirmed flag true |
| CLOSED đúng lệnh CLOSED | CONFIRMED, gate CLOSED |
| Device ERROR | ERROR / DEVICE_ERROR, không gán CLOSED giả |
| ACK sai target | ERROR / ACK_TARGET_MISMATCH |
| ID lạ, ACK terminal/trùng/muộn | Lưu audit, không cập nhật command/gate |
| Publish lỗi hoặc exception | ERROR / PUBLISH_FAILED, REST 503; không khẳng định lệnh chắc chắn chưa tới Device |
| Quá 5 giây không có ACK hợp lệ | TIMEOUT / ACK_TIMEOUT, không tự retry |
| Backend restart còn PENDING | TIMEOUT / BACKEND_RESTART, không resend |
| Mất broker/heartbeat | Thu hồi gate_meta.confirmed; lệnh pending chờ timeout, không báo success giả |

ACK đến sau TIMEOUT được audit nhưng không đổi record thành CONFIRMED hoặc tự nhận đó là trạng thái gate hiện tại. Đây là cách xử lý thận trọng trong lựa chọn v1 cho phép không áp dụng late ACK. Reconnect không có đường tự gửi lại OPEN.

CONFIRMED/gate_meta.confirmed là xác nhận phần mềm firmware, **không phải chứng cứ quan sát servo**. Lần đầu trạng thái gate chưa biết không ghi chuyển động CLOSED→OPEN giả trong history. GATE event chỉ ghi khi hai trạng thái OPEN/CLOSED trước/sau đã được xác nhận và khác nhau; metadata/snapshot vẫn phát khi lần đầu được xác nhận.

## 4. SQLite migration và bảo toàn

Schema v2 mở parking_events nhận slotId GATE/type GATE cùng OPEN/CLOSED, giữ các sự kiện ô đỗ cũ. Thêm gate_state lưu last-known/confirmed_at và gate_ack_audit lưu phản hồi/received_at/outcome. gate_commands giữ fields/enums v1, thêm partial unique index một PENDING.

DB v1 được backup trước migration vào <database>.before-phase04.bak; migration rename/copy/recreate event table trong transaction, giữ sequence/id/data. Không xóa DB để khởi tạo lại. Migration idempotent được kiểm thử. Trạng thái last-known được giữ, confirmed flag bị thu hồi khi restart để tránh giả dữ liệu còn tin cậy.

Không chạy migration trên DB runtime ở F trong lượt này. Migration sẽ xảy ra khi người dùng áp dụng source và khởi động app mới. Dừng app cũ trước, không chạy hai phiên Backend trên cùng DB.

## 5. Kết quả automated tests

**103 passed, 0 failed, 1 warning trong 13.96 giây** ở lượt cuối. Bao gồm 74 ca regression giai đoạn 2–3 và 29 ca giai đoạn 4 (tính parameterization). Tests chạy trong venv riêng của vùng staging, database tạm, fake MQTT và clock; không publish fixture tới broker LIVE.

| Hạng mục | Kết quả |
|---|---|
| OPEN/PENDING không coi publish là thành công servo | PASS |
| ACK OPENED/CLOSED đúng ID và target | PASS (mock MQTT) |
| FULL chặn ENTRY, EXIT vẫn được chấp nhận | PASS |
| UNKNOWN/baseline không tin cậy chặn ENTRY | PASS |
| Broker/device offline không báo thành công | PASS |
| Publish fail/exception, DB PENDING trước publish | PASS |
| ID duplicate/concurrent chỉ một publish, conflict/busy | PASS |
| ACK sai ID/target, ERROR, trùng/muộn | PASS |
| Timeout 5s, restart PENDING không resend | PASS |
| MQTT publish đúng topic/payload/retain và ACK qua ingest worker | PASS (fake client) |
| Reconnect không auto OPEN lại | PASS (fake client) |
| Hai WS client nhận cùng snapshot | PASS |
| Command trước snapshot cùng revision | PASS |
| Reconnect initial snapshot/REST khớp | PASS |
| WS timeout, origin, lệnh inbound bị chặn | PASS |
| Client chậm/batch lỗi được ngắt để resync | PASS |
| 25 vòng đóng/mở hai client, không peer treo | PASS |
| Migration v1→v2 giữ events, backup và chạy lại | PASS |
| Timestamp commit tách delayed received_at | PASS |
| Timeout config 0/âm/NaN/Infinity bị từ chối | PASS |

pip check: No broken requirements found. Cảnh báo cũ Starlette TestClient/httpx deprecation vẫn còn, không bị tắt để che kết quả.

Lệnh kiểm thử sau áp dụng:

```powershell
.venv\Scripts\python.exe -m pytest -q
```

## 6. HTTP/WebSocket transport thật

Đã chạy Uvicorn thật ở localhost:18024 trên DB tạm và hai client websockets thật. Không dùng MQTT broker trong smoke này; publisher và ACK là fixtures cục bộ được ghi rõ.

Kết quả:

- Hai client nhận initial snapshot giống nhau, revision 5.
- Thay đổi ô qua fixture nhận cùng snapshot revision 6.
- POST Gate API HTTP 202/PENDING, gate.command trước snapshot revision 7.
- Fixture ACK → CONFIRMED và gate OPEN, cùng revision 8, hai client giống nhau.
- GET /status khớp dữ liệu WS.
- Retry cùng ID → HTTP 200, không publish fixture lần hai.
- Client reconnect → snapshot khớp REST.
- Server/lifespan dừng sạch.

Nguồn bằng chứng: phase-04-http-ws-smoke.json và .log. Đây là kiểm thử transport thật với dữ liệu fixture, không phải ESP32/servo thật.

## 7. Manual integration — NOT VERIFIED

Chưa gọi Gate API tới Wokwi đang chạy có kiểm soát và chưa quan sát servo trong lượt này. Các mục OPENED/CLOSED thật, servo quay, FULL ENTRY/EXIT thực, timeout/broker reconnect thực đều để NOT VERIFIED.

Không suy từ ACK mô phỏng hoặc xác nhận Device↔MQTTX trước đó rằng servo đã quay. Hướng dẫn sau áp dụng nằm trong phase-04-manual-test.md; tools/watch_ws.py là CLI viewer chỉ đọc, có reconnect, không sửa Frontend hoặc gửi command qua WS.

## 8. File thay đổi / thêm mới trong bộ cập nhật

| File Backend | Nội dung |
|---|---|
| app/database.py | Migration/schema v2 và backup DB v1 |
| app/services/parking.py | Observer sau commit, gate snapshot/event, timestamp commit |
| app/services/gate.py | Mới: policy, idempotency, pending/ACK/timeout/restart/audit |
| app/services/realtime.py | Mới: fanout, bounded queues, validation và resync |
| app/services/mqtt_subscriber.py | Explicit Gate API publish và ACK dispatch, heartbeat check; không auto publish khi reconnect |
| app/routers/realtime_gate.py | Mới: REST Gate/command và WS lifecycle |
| app/routers/parking.py | Health giai đoạn 4 |
| app/schemas/__init__.py | Gate/event/WS schema v1 và metadata |
| app/config.py | ACK timeout 5s, kiểm tra số hữu hạn |
| app/main.py | Gate watchdog/hub/MQTT wiring và error envelopes |
| tests/test_realtime_gate.py | Mới: 29 ca/parameterized cases giai đoạn 4 |
| tests/fixtures/schema-v1.sql | Mới: schema giai đoạn 3 dùng test migration |
| tests/test_core.py, tests/test_mqtt.py | Chỉ cập nhật expectation schema_version DB và POST gate thiếu body từ 404 sang 422 vì route mới |
| tools/watch_ws.py | Mới: CLI viewer chỉ đọc |
| requirements.txt/requirements-lock.txt | Thêm websockets 16.1.1; khai báo AnyIO đang dùng 4.15.1, giữ version dependencies cũ |
| .env.example | SMART_PARKING_ACK_TIMEOUT=5 |
| .gitignore | Bỏ qua thư mục backup source |
| README.md | Vận hành và semantics giai đoạn 4 |

Tài liệu/log mới ở docs/: phase-04-realtime-gate-report.md, phase-04-manual-test.md, phase-04-pytest.log/xml, phase-04-http-ws-smoke.log/json. Gói có INSTALL.md, original-backend-manifest.json và apply-phase04.ps1 để áp dụng có kiểm soát.

## 9. Vấn đề còn lại và bước áp dụng

- **Chưa chép vào F** do quyền ghi chưa được cấp. Bộ cập nhật không thay source/DB runtime. Chạy script ở chế độ mặc định để kiểm tra (read-only); dừng Backend rồi dùng -Apply để chép, cài lockfile và test tại dự án chính. Xem INSTALL.md.
- Manual Wokwi/servo chưa xác minh; chỉ xác nhận firmware khi ACK đúng, không khẳng định cơ khí.
- Public broker không xác thực nguồn; ID/payload matching không thay thế authentication. Chỉ demo local, chưa anti-jam sensor hoặc hai barrier vật lý.
- Publish QoS0 có thể mất lệnh; không auto retry, cần người vận hành quyết định ý định mới sau timeout. Không bảo đảm exactly-once.
- Single process/worker; queue bị giới hạn và client phải reconnect/resync khi chậm. History full chưa pagination.
- Frontend giữ nguyên và chưa có adapter LIVE/WS/Gate API. Giai đoạn 5 sẽ là công việc riêng sau xác nhận.

**Dừng giai đoạn 4 tại bộ cập nhật đã kiểm thử. Chờ áp dụng/kiểm thử thủ công và xác nhận trước giai đoạn 5.**
