# BÁO CÁO TỔNG HỢP CÔNG VIỆC CẢ BA THÀNH VIÊN

**BỘ GIÁO DỤC VÀ ĐÀO TẠO — [TÊN TRƯỜNG / KHOA: CHƯA CUNG CẤP]**

**ĐỒ ÁN MÔN LẬP TRÌNH IoT — ĐỀ TÀI 21: HỆ THỐNG ĐỖ XE THÔNG MINH**

Nhóm 21. Ngày tổng hợp: **19/10/2026**. Giảng viên, lớp, học kỳ: **cần nhóm bổ sung**. Không tự đặt tên trường, giảng viên hoặc kết quả kiểm thử.

| Thành viên | MSSV theo khung người dùng cung cấp | Phụ trách |
|---|---|---|
| Huỳnh Đổ Hoàng Nguyên | 2001230582 | TV1 — Device/ESP32/Wokwi/MQTT/servo |
| Bạch Ngọc Hợp | 2001230279 | TV2 — FastAPI/SQLite/MQTT Subscriber/REST/WS/Gate |
| Bùi Tấn Phước | 2001230696 | TV3 — React/Vite/Spline/DEMO/LIVE/UI và kiểm thử Frontend |

## Cách đọc và nguồn dữ liệu

Đây là báo cáo công việc chung, tổ chức theo năm chương để nhóm lấy nội dung vào khung đồ án. Công việc chi tiết nằm ở ba báo cáo cá nhân và bảng thống kê 45 nhóm công việc. Khung đầy đủ người dùng cung cấp được giữ tại `minh-chung/CHUNG/KHUNG_BAO_CAO_NGUOI_DUNG.txt`; các phần lý thuyết, ảnh/video cuối kỳ và thông tin học phần chưa có nguồn vẫn cần nhóm hoàn thiện trước khi nộp.

Nguồn dùng để tổng hợp: source hiện có tại SmartParking-Group21 trên ổ F; các báo cáo Phase 2–5 và log gốc; báo cáo Device/Frontend trước đó; log/screenshot và xác nhận của người dùng trong hội thoại. Phân công phản ánh module theo tài liệu nhóm, không phải kết quả audit tác giả từng commit. Không có timesheet hoặc dữ liệu để tự tính số giờ/phần trăm đóng góp.

### Quy ước đánh giá

| Thuật ngữ | Ý nghĩa |
|---|---|
| Đã triển khai | Đã có code/tài liệu tương ứng; chưa tự đồng nghĩa mọi runtime/E2E đã đạt |
| Triển khai một phần | Có phần đã áp dụng và phần còn ở gói sửa hoặc chưa nghiệm thu |
| PASS tự động | Có log tests/build thực tế, ghi đúng phạm vi fixture/unit/API/WS |
| Người dùng xác nhận | Có phát biểu/log/ảnh từ người dùng, tách khỏi phép thử mới do agent chạy |
| NOT VERIFIED | Chưa có bằng chứng đủ cho ca kiểm thử hoặc môi trường cụ thể |

## CHƯƠNG 1. TỔNG QUAN, MỤC TIÊU VÀ PHẠM VI

### 1.1. Bài toán và mục tiêu

Nhóm xây dựng mô hình giám sát bãi xe bốn ô P01–P04, hiển thị còn chỗ/đầy/chưa xác định, theo dõi lịch sử, điều khiển barrier và trực quan trạng thái bằng mô hình 3D. Hệ thống nhằm minh họa luồng IoT từ thiết bị qua mạng tới ứng dụng, không chỉ trình diễn giao diện với dữ liệu giả.

Mục tiêu kỹ thuật gồm: thu nhận boolean occupied từ công tắc; chuẩn hóa EMPTY/OCCUPIED/UNKNOWN; lưu dữ liệu và sự kiện; truyền snapshot nhất quán qua REST/WebSocket; gửi lệnh cổng có ID và xác nhận; giữ DEMO độc lập và LIVE dùng Backend.

### 1.2. Đối tượng, phạm vi và giới hạn

Đối tượng sử dụng là người giám sát/vận hành mô hình. Device là ESP32 mô phỏng trên Wokwi, bốn slide switches thay cảm biến và một servo SG90. Không có OCR biển số, thanh toán, đặt chỗ, ứng dụng di động, hai cổng vật lý riêng hoặc cảm biến chống kẹt trong phạm vi source đang báo cáo.

Không gọi công tắc Wokwi là phép đo từ cảm biến vật lý. ACK firmware không phải phép đo góc servo. Không khẳng định độ trễ/SLA hoặc độ ổn định production khi chưa có phương pháp đo và dữ liệu.

### 1.3. Cơ sở công nghệ gắn với phần việc

| Lớp | Công nghệ | Lý do trong triển khai hiện tại |
|---|---|---|
| Thiết bị | ESP32/Arduino, WiFi, PubSubClient, ESP32Servo, ArduinoJson, Wokwi | Đọc bốn ô, điều khiển servo, publish/subscribe JSON MQTT |
| Truyền thông | MQTT 3.1.1 qua broker.hivemq.com:1883 | Tách publisher/subscriber cho Device và Backend |
| Xử lý/lưu trữ | Python/FastAPI/Pydantic/SQLite/Paho | Validate, state/history/KPI, lệnh cổng, API và realtime |
| Ứng dụng | React/Vite/Spline/Recharts/Lucide | Các tab Dashboard, dữ liệu realtime, xe/màu/barrier và thống kê |
| Kiểm thử | pytest/HTTPX/TestClient/websockets/Node test runner | Kiểm tra domain, API, WS, mock store và LIVE adapter |

Môi trường từng kiểm thử: Python 3.11, Node.js 24.18.0, Vite 6.4.4; dependency cụ thể lấy theo lockfiles. Không suy mọi phiên bản mới hơn đã tương thích hoặc đã được kiểm thử.

## CHƯƠNG 2. THIẾT KẾ VÀ PHÂN CÔNG HỆ THỐNG

### 2.1. Kiến trúc và ranh giới trách nhiệm

```text
TV1: ESP32/Wokwi → MQTT Broker → TV2: FastAPI → SQLite
                                           ↓ REST / WebSocket
                                      TV3: React → Spline 3D

React OPEN/CLOSE → Gate API → MQTT gate/command → ESP32/servo
React/Spline ← WS/REST ← FastAPI ← MQTT gate/status ACK
```

TV1 cung cấp trạng thái và ACK. TV2 là nguồn xác nhận dữ liệu, quy tắc bãi và lưu trữ. TV3 không tự sửa trạng thái cảm biến LIVE hoặc bỏ qua FULL ở Backend. Công tắc ô đỗ và nút điều khiển cổng là hai thao tác khác nhau; gạt công tắc không tự mở barrier.

### 2.2. Yêu cầu chức năng và hiện trạng

| Mã | Chức năng | Hiện trạng triển khai | Mức xác nhận |
|---|---|---|---|
| FR01 | Theo dõi P01–P04 | Có Device publish, Backend store và card UI | Có log Device/Backend và xác nhận người dùng |
| FR02 | MQTT → Dashboard | Có subscriber, REST/WS, LIVE adapter | Có kiểm thử từng chặng; chưa có biên bản mọi E2E |
| FR03 | FULL/UNKNOWN | Có trong Backend và UI, UNKNOWN không tính free | Automated tests PASS và FULL DEMO đã được người dùng xác nhận |
| FR04 | Gate ENTRY/EXIT | Có API/ID/policy/MQTT/ACK và UI | Unit/fixture PASS, từng gặp ACK muộn; cần tách nghiệm thu servo |
| FR05 | Lịch sử/thống kê | Có SQLite và giao diện | Có tests và xác nhận người dùng thấy log/thống kê |
| FR06 | Mô hình 3D | Xe/màu/scene và barrier Y/+90° | Có xác nhận các tình huống DEMO, scene load; giới hạn QA trực quan ghi riêng |
| FR07 | Mất kết nối/reconnect | Có health/UNKNOWN/baseline/resync | Automated PASS; mạng/broker công cộng còn có lỗi thực tế |
| FR08 | DEMO/LIVE | Có hai service và cấu hình | DEMO độc lập, LIVE đã có source tại F |

### 2.3. Phần cứng và MQTT

| Đối tượng | Cấu hình |
|---|---|
| P01/P02/P03/P04 | GPIO13/14/27/26, INPUT_PULLUP, LOW=true/có xe |
| SG90 | PWM GPIO18, V+5V và GND; OPEN 90°/CLOSE 0° |
| Debounce | 400ms mô phỏng |
| Heartbeat/snapshot | 10s mô phỏng; snapshot bốn ô gửi lại định kỳ và sau reconnect |
| Broker/device | broker.hivemq.com:1883; esp32-01 |

Topic prefix `smartparking/group21/`: `slots/P01/state` đến P04, `device/status`, `gate/command`, `gate/status`. Slot JSON giữ `{device_id,slot_id,occupied:boolean}`. Gate command giữ `{command_id,action:OPEN/CLOSE,direction:ENTRY/EXIT}`. ACK giữ `{device_id,command_id,status:OPENED/CLOSED/ERROR}`.

Device không gửi UTC; Backend gắn received_at UTC. Firmware publish QoS0/non-retained trong cấu hình hiện có; không bảo đảm không mất gói. Gửi snapshot định kỳ là gửi trạng thái đọc từ GPIO, không phải tạo dữ liệu giả để làm UI trông online.

### 2.4. Backend, dữ liệu và cổng

SQLite schema v2 có parking_slots, parking_events, gate_commands, gate_state và gate_ack_audit. Seed UNKNOWN; last-known/history lưu qua restart. Mất trust làm trạng thái công khai UNKNOWN, không xóa lịch sử hoặc tự coi ô là EMPTY.

REST đọc health/status/slots/summary/events/statistics; Gate POST và GET command. WS gửi full snapshot với schema_version/stream_id/revision, command update trước snapshot cùng revision. Backend một worker trong MVP.

Client command_id bắt buộc, PENDING lưu trước publish. ENTRY OPEN bị chặn khi FULL hoặc chưa tin cậy; EXIT không bị chặn chỉ vì FULL nhưng vẫn cần device/MQTT sẵn sàng, không busy. ACK phải đúng ID/target. ERROR/TIMEOUT không giả CLOSED hoặc success; không tự gửi lại OPEN sau reconnect/restart. Cấu hình demo hiện dùng ACK timeout 15s thay cho ngưỡng 5s mặc định cũ.

### 2.5. Giao diện và tính nhất quán

Frontend có bốn tab, mock DEMO, adapter LIVE và store đồng bộ cho useSyncExternalStore. LIVE nhận full snapshot thay nguyên bộ dữ liệu hợp lệ, không replay từng event vào mock. KPI/chart dùng cùng events của snapshot, tránh trộn revision. Cổng chưa confirmed có nhãn riêng và không xoay 3D như đã được xác nhận.

Contract v1 D01–D08 do người dùng phê duyệt trước khi viết Backend. Tiêu đề DRAFT trong một số tài liệu gốc là trạng thái lịch sử, không có nghĩa Backend tự phê duyệt hoặc được phép đổi wire contract.

## CHƯƠNG 3. TRIỂN KHAI VÀ CÔNG VIỆC TỪNG THÀNH VIÊN

### 3.1. TV1 — Huỳnh Đổ Hoàng Nguyên

Đã có mô hình Wokwi, sơ đồ chân, đọc INPUT_PULLUP/debounce, publish slot/heartbeat/Will, reconnect, nhận OPEN/CLOSE và xử lý servo/ACK/busy/duplicate. Sau các lỗi thực tế, firmware đã có socket timeout 15s và snapshot bốn ô định kỳ để hỗ trợ phục hồi baseline. Chi tiết **12 nhóm việc** tại [báo cáo TV1](01_TV1_DEVICE.md).

Các điều chỉnh này không chứng minh broker/mạng đã ổn định tuyệt đối. Báo cáo Device cũ nói chỉ kiểm tra tĩnh được giữ như lịch sử; log và xác nhận người dùng mới được ghi riêng, không sửa log cũ để thành kết quả mới.

### 3.2. TV2 — Bạch Ngọc Hợp

Đã có audit/contract, Backend Core, SQLite/migration, state/history/KPI/UTC, REST, strict MQTT parser/subscriber, queue/epoch, heartbeat/baseline/reconnect, WS fanout/ordering, Gate policy/idempotency/ACK/timeout/restart và tests/lockfile/env/README. Chi tiết **18 nhóm việc** tại [báo cáo TV2](02_TV2_BACKEND.md).

24 core + 50 MQTT + 29 realtime/gate là **103 tests** của bộ regression Phase 4. Không cộng kết quả Phase 2 (24), Phase 3 (74) và Phase 4 (103) thành 201 tests riêng vì đó là các lần chạy chồng nhau.

### 3.3. TV3 — Bùi Tấn Phước

Đã có UI/tab/KPI, DEMO, store/contract, lịch sử/chart, scene/diagnostics, đồng bộ xe/màu, barrier cố định Y/+90°, env/mode, REST/WS adapter, command UI/recovery và tests/build/audit/docs. Chi tiết **15 nhóm việc** tại [báo cáo TV3](03_TV3_FRONTEND.md).

Trong nhóm xử lý lỗi adapter, bản DEVICE_UNAVAILABLE/offline guard đã có trong source F. Bản dừng polling 404 đã được chuẩn bị/kiểm thử riêng nhưng khi rà source cho báo cáo này vẫn chưa có nhánh xử lý đó tại F, nên đánh dấu **triển khai một phần**, không ghi hoàn thành toàn bộ.

### 3.4. Công việc phối hợp

Nhóm thống nhất topic/payload, snapshot/command contract và ranh giới DEMO/LIVE; tổ chức workspace; đối chiếu log các lớp; xử lý ACK muộn/baseline; chuẩn bị hướng dẫn clone/setup và báo cáo. Các việc này không tính trùng vào số nhóm công việc cá nhân và không quy tất cả firmware/Backend/Frontend cho một người.

### 3.5. Thống kê triển khai

| Thành viên | Nhóm công việc được liệt kê | Đã triển khai theo source | Triển khai một phần |
|---|---|---|---|
| TV1 | 12 | 12 | 0 |
| TV2 | 18 | 18 | 0 |
| TV3 | 15 | 14 | 1 |
| Tổng | 45 | 44 | 1 |

**Đây là số nhóm công việc được mô tả, không phải tỷ lệ đóng góp, % hoàn thành, số giờ hoặc số ca E2E PASS.** Từng nhóm có mức bằng chứng/giới hạn riêng. Xem [bảng chi tiết](04_THONG_KE_CONG_VIEC.md).

### 3.6. Cài đặt và chạy

Hướng dẫn đầy đủ: [Setup và lệnh chạy A–Z](05_HUONG_DAN_SETUP_VA_CHAY_A_Z.md). Mỗi thành viên cần đúng source/lockfiles, tự tạo venv và cài npm dependencies, tạo env cá nhân; không copy venv/node_modules/DB runtime của máy khác.

Trình tự demo: Backend một worker → Wokwi một phiên → Frontend LIVE. Sau sửa source Device phải chép code mới lên Wokwi online và Stop/Play; file local không tự đồng bộ. Không cần reconnect thủ công sau mỗi lần gạt công tắc.

Từng quan sát source Backend/LIVE chưa được Git theo dõi ở bản local; hướng dẫn clone có bước kiểm tra đủ file. Báo cáo không tự commit/push và chưa chứng minh fresh clone trên máy mới đã đạt.

## CHƯƠNG 4. KIỂM THỬ, BẰNG CHỨNG VÀ ĐÁNH GIÁ

### 4.1. Phương pháp

Tách ba nguồn: (1) source/kiểm tra tĩnh, (2) automated unit/API/WS/fixture và build, (3) log/ảnh/xác nhận người dùng chạy mô phỏng. PASS của nguồn (2) không tự thành PASS vật lý hoặc E2E trên mọi môi trường.

### 4.2. Kết quả đã có

| Nhóm | Kết quả có bằng chứng | Nguồn |
|---|---|---|
| Device static/source | Sơ đồ/GPIO/firmware hiện có; log SENSOR/SLOT/heartbeat/ACK | Báo cáo TV1, source đối chiếu và xác nhận người dùng |
| Backend Core | 24 tests PASS Phase 2, HTTP smoke | minh-chung/TV2/phase-02-* |
| MQTT Backend | Bộ regression 74 tests PASS Phase 3 | minh-chung/TV2/phase-03-* |
| Backend WS/Gate | Bộ regression 103 tests PASS/1 warning Phase 4, HTTP/WS fixture | minh-chung/TV2/phase-04-* |
| Frontend DEMO | 5 tests và các tình huống UI người dùng xác nhận | Báo cáo TV3 cũ, logs tương ứng |
| Frontend LIVE | Log Phase 5 21 tests PASS, build DEMO/LIVE đạt, audit online 0 advisory lúc chạy | minh-chung/TV3/phase-05-* |
| Người dùng sau chỉnh sửa | “oke test được rồi” | XAC_NHAN_NGUOI_DUNG.md; không có chi tiết mọi test case |

Các báo cáo/log được sao chép nguyên byte và có manifest SHA-256. Không chạy lại tests chỉ vì viết hoặc gom báo cáo. Không dùng audit offline để kết luận đầy đủ về bảo mật, không dùng pip check để chứng minh không có lỗ hổng.

### 4.3. Ma trận E2E cần giữ đúng mức xác nhận

| ID | Kịch bản | Bằng chứng hiện có | Kết luận cho nghiệm thu cuối |
|---|---|---|---|
| TC01 | P01 EMPTY→OCCUPIED → UI/3D | Có xác nhận DEMO, log từng chặng LIVE và xác nhận chung sau sửa | Cần bổ sung biên bản/ảnh ca LIVE riêng |
| TC02 | P01 OCCUPIED→EMPTY → history/KPI | Có log/thống kê và xác nhận thao tác trước đó | Chưa tự ghi toàn luồng vật lý PASS mới |
| TC03 | 4/4 OCCUPIED → FULL | DEMO người dùng xác nhận, Backend tests PASS | LIVE end-to-end cần lưu minh chứng riêng |
| TC04 | FULL chặn ENTRY OPEN | Backend automated PASS | Chưa có biên bản thực nghiệm cuối cho ca này |
| TC05 | FULL không chặn EXIT chỉ vì FULL | Backend automated PASS | Cần quan sát Gate API/ACK/servo có kiểm soát |
| TC06 | OPEN/CLOSE hai chiều | Có log firmware OPENED; từng có ACK timeout được đối chiếu | ACK không đủ chứng minh servo/UI/3D đều đã đúng |
| TC07 | Offline/reconnect → UNKNOWN/baseline | Có lỗi runtime, tests và source snapshot định kỳ | Cần nghiệm thu lại độ ổn định và chống đếm trùng |
| TC08 | Refresh LIVE giữ DB history | Có browser/fixture evidence Phase 5 | Chưa chứng minh mọi máy/trình duyệt đều đạt |
| TC09 | Backend restart giữ SQLite | Tests và server fixture PASS | Runtime chính/thiết bị mới cần ghi kết quả nếu đưa vào biên bản cuối |
| TC10 | Invalid MQTT không crash/mutation | Parser/queue/API tests PASS | Chưa có negative test broker có kiểm soát được ghi đầy đủ |

Không gắn nhãn FAIL cho một ca chưa chạy. Khi chưa đủ minh chứng, dùng NOT VERIFIED hoặc ghi phạm vi xác nhận như trên; chỉ đổi PASS sau khi quan sát thực tế đúng tiêu chí.

### 4.4. Các lỗi đã gặp và cách xử lý

- Port 5173 bị chiếm: dừng đúng Vite cũ, chỉ chạy một tiến trình trên cổng cần dùng.
- MQTT timeout/Not authorized/keepalive: log cho thấy có lỗi cả đường Device và Backend tới broker; chưa đủ để quy hoàn toàn cho Wokwi. Không che bằng cách giữ trạng thái tin cậy giả.
- ONLINE thiếu baseline: chỉ có heartbeat chưa đủ bốn ô; bổ sung Device gửi snapshot định kỳ, giữ UNKNOWN tới khi nhận dữ liệu thật.
- ACK đến khoảng 7,8s trong một ca: lệnh đã timeout ở ngưỡng 5s; đổi cấu hình demo ACK15s và dùng ID ý định mới khi cần. ACK muộn vẫn theo policy audit.
- UI pending sau DEVICE_UNAVAILABLE: đã có sửa phân biệt từ chối trước lưu lệnh; vòng polling 404 còn cần áp dụng bản sửa riêng tại F.
- Spline trục/chiều: đã cố định Y/+90° theo yêu cầu, giữ rotation gốc để đóng và tránh cộng dồn.

### 4.5. Giới hạn kết quả

Chưa đo độ trễ có phương pháp, chưa có timesheet/commit tác giả đầy đủ, chưa có biên bản từng ca E2E cuối và fresh clone trên máy khác. Không tạo ảnh/video hoặc giá trị đo giả. Các ảnh gốc Phase 5 là bằng chứng môi trường staging trước đó, không dùng làm ảnh mới cho mọi máy.

## CHƯƠNG 5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

### 5.1. Kết quả đạt được

Source hiện có đầy đủ ba lớp Device–Backend–Frontend LIVE/DEMO, dữ liệu ô, health/baseline, lưu trữ/history/statistics, realtime và điều khiển cổng có ID/ACK/policy. Đã có các bộ kiểm thử tự động và log chạy thật; người dùng xác nhận test được sau các điều chỉnh. Đây là nền tảng MVP, không phải tuyên bố hệ thống vật lý/production đã nghiệm thu toàn diện.

### 5.2. Đóng góp và tài liệu bàn giao

TV1 triển khai lớp thiết bị và phối hợp tín hiệu; TV2 triển khai xử lý/lưu trữ/API/realtime/lệnh; TV3 triển khai ứng dụng và trực quan dữ liệu. Ba báo cáo cá nhân và ma trận thống kê mô tả cụ thể từng nhóm công việc, không gán phần trăm đóng góp thiếu bằng chứng.

### 5.3. Việc còn lại trước nộp cuối kỳ

1. Áp dụng bản sửa polling 404 còn thiếu ở source F, kiểm thử lại đúng nhánh đó.
2. Lập biên bản từng ca E2E, ảnh/video Wokwi/servo/React cùng ID/thời gian; QA hình ảnh desktop/tablet.
3. Kiểm tra nhánh GitHub có đủ Backend/LIVE/lockfiles/env mẫu và thử clone trên máy thành viên khác. Không đưa .env, DB, dependencies/build/backup vào Git.
4. Bổ sung trường/khoa, giảng viên/lớp/học kỳ, tài liệu tham khảo và chú thích hình/bảng theo mẫu giảng viên.
5. Không tự chuyển xác nhận chung thành 100% PASS, không sửa log cũ hoặc xóa DB để làm số liệu đẹp.

### 5.4. Hướng phát triển

Cảm biến và mô hình vật lý thật, broker riêng/TLS/authentication, Device session/sequence và xác nhận trạng thái tốt hơn, pagination/history quy mô lớn, tối ưu bundle/3D, CI và kiểm thử nhiều môi trường. Các mục này là hướng đề xuất, chưa triển khai trong báo cáo công việc hiện tại.

## PHỤ LỤC VÀ NGUỒN MINH CHỨNG

- [Bảng công việc chi tiết](04_THONG_KE_CONG_VIEC.md).
- [Minh chứng theo thành viên](minh-chung/README.md), kèm manifest SHA-256.
- [Khung báo cáo người dùng cung cấp](minh-chung/CHUNG/KHUNG_BAO_CAO_NGUOI_DUNG.txt).
- [Xác nhận người dùng và phạm vi](minh-chung/CHUNG/XAC_NHAN_NGUOI_DUNG.md).
- Contract, báo cáo Phase và log gốc được lưu trong minh-chung; tên Phase chỉ là lịch sử triển khai, không còn là cách đọc chính của bộ báo cáo này.

Nguồn thư viện/asset và phạm vi hỗ trợ AI cần được nhóm khai báo đúng quy định học phần. Báo cáo/adapter/tests/tài liệu đã có hỗ trợ từ Codex trong hội thoại; không mô tả tất cả là sản phẩm được từng thành viên viết thủ công độc lập hoặc giả lập tác giả commit.
