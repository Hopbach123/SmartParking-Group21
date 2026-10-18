# NỘI DUNG BÁO CÁO ĐỒ ÁN — SMART PARKING GROUP 21

**BỘ GIÁO DỤC VÀ ĐÀO TẠO**  
**[TÊN TRƯỜNG / KHOA — BỔ SUNG]**  
**BÁO CÁO ĐỒ ÁN MÔN LẬP TRÌNH IoT**  
**ĐỀ TÀI 21: HỆ THỐNG ĐỖ XE THÔNG MINH (SMART PARKING)**

| Thành viên | MSSV | Phụ trách |
|---|---|---|
| Huỳnh Đổ Hoàng Nguyên | 2001230582 | Device (TV1) |
| Bạch Ngọc Hợp | 2001230279 | Backend (TV2 — bổ sung sau) |
| Bùi Tấn Phước | 2001230696 | Frontend (TV3) |

Giảng viên: [BỔ SUNG]. Lớp/Học kỳ/Năm học: [BỔ SUNG].  
TP. Hồ Chí Minh, năm 2026.

> Tài liệu cung cấp nội dung để đưa vào báo cáo theo khung của nhóm. Điền phần Device và Frontend từ source, tài liệu và kết quả kiểm thử hiện có; giữ mục Backend để bổ sung sau. Nhóm hiện có ba thành viên, không có thông tin TV4. Ngày tổng hợp: 18/10/2026. Các mục ghi thiết kế hoặc dự kiến không phải kết quả hệ thống đã vận hành end-to-end.

## LỜI MỞ ĐẦU

Quản lý bãi đỗ xe cần cung cấp trạng thái chỗ trống rõ ràng, giúp người vận hành theo dõi sức chứa và xử lý việc xe vào, ra. Trong mô hình thủ công, trạng thái thường được kiểm tra trực tiếp và khó tập trung thành lịch sử hoạt động. Đề tài Smart Parking được lựa chọn nhằm thực hành cách thu nhận trạng thái từ thiết bị, truyền dữ liệu qua mạng và biểu diễn trên giao diện giám sát.

Nhóm thiết kế hệ thống gồm lớp thiết bị ESP32 mô phỏng trên Wokwi, giao tiếp MQTT, lớp xử lý FastAPI dự kiến và Dashboard React kết hợp mô hình Spline 3D. Bốn công tắc mô phỏng tình trạng bốn ô đỗ; servo biểu diễn thanh chắn. Dashboard cung cấp trạng thái, sức chứa, lịch sử và thống kê để quan sát quá trình vận hành.

Ở thời điểm báo cáo, source Device và Frontend đã được tổ chức trong workspace chung. Frontend đã được kiểm thử bằng dữ liệu giả lập; Device có firmware và sơ đồ, nhưng chưa có bằng chứng chạy Wokwi/MQTT trực tiếp trong lượt xác minh hiện tại. Backend chưa được triển khai. Vì vậy, kết quả được trình bày theo từng module, không coi thay đổi trên giao diện demo là dữ liệu cảm biến thật.

Báo cáo gồm năm chương: tổng quan và cơ sở lý thuyết; phân tích và thiết kế; triển khai; kiểm thử và đánh giá; kết luận và hướng phát triển.

# CHƯƠNG 1. TỔNG QUAN ĐỀ TÀI VÀ CƠ SỞ LÝ THUYẾT

## 1.1. Đặt vấn đề

Bài toán đặt ra là xác định tình trạng từng ô và tổng hợp thành trạng thái chung của bãi. Người vận hành cần biết số ô có xe, số ô còn trống và dữ liệu nào chưa xác định, đồng thời theo dõi lệnh đóng/mở cổng. Việc trực quan hóa giúp đối chiếu dữ liệu số với bố trí ô đỗ, hỗ trợ trình diễn và phát hiện sai lệch trạng thái.

## 1.2. Mục tiêu của đề tài

Mục tiêu tổng quát là xây dựng mô hình thực hành giám sát bãi đỗ xe ứng dụng IoT. Các mục tiêu cụ thể gồm thu nhận bốn trạng thái ô đỗ, trao đổi dữ liệu bằng MQTT, biểu diễn xe và màu ô trên Dashboard 3D, cảnh báo FULL và theo dõi lịch sử/thống kê. Luồng liên thông qua FastAPI và lưu trữ SQLite là mục tiêu tích hợp tiếp theo, chưa hoàn thành.

Tiêu chí kiểm chứng hiện tại là tính nhất quán giữa trạng thái mock, KPI, lịch sử và thống kê; khả năng hiển thị và điều khiển mô hình; tính hợp lệ của cấu hình Device. Chưa đặt kết quả định lượng về độ trễ đầu cuối vì chưa có phép đo hệ thống tích hợp.

## 1.3. Đối tượng, phạm vi và giới hạn

Mô hình có bốn ô P01–P04, một ESP32, bốn công tắc và một servo SG90 trên Wokwi. Frontend chạy trên trình duyệt bằng React/Vite, có mô hình Spline đã xuất. Chưa triển khai nhận dạng biển số, thanh toán, đặt chỗ, ứng dụng di động hoặc cảm biến thật. Mock data chỉ phục vụ demo, không lưu qua refresh.

## 1.4. IoT và kiến trúc nhiều lớp

Thiết kế chia thành lớp thiết bị, truyền thông, xử lý và ứng dụng. Device đọc tín hiệu và nhận lệnh; MQTT chuyển bản tin; Backend dự kiến chuẩn hóa/lưu dữ liệu; Frontend hiển thị cho người dùng. Việc phân lớp giúp tách giao diện khỏi giao thức thiết bị và giữ ranh giới công việc giữa các thành viên.

## 1.5. Nguyên lý phát hiện ô đỗ

Trong mô phỏng, công tắc thay cho cảm biến phát hiện xe. Firmware dùng INPUT_PULLUP: tín hiệu LOW tương ứng có xe, ngược lại là trống. Công tắc không đo khoảng cách và không chứng minh độ chính xác của cảm biến vật lý. Việc chọn cảm biến thật và hiệu chỉnh là công việc phát triển sau.

## 1.6. ESP32, servo và Wokwi

ESP32 thực hiện đọc GPIO, kết nối Wi-Fi và xử lý MQTT. Servo nhận tín hiệu điều khiển tại GPIO18, được firmware đặt 0° khi đóng và 90° khi mở. Wokwi cung cấp môi trường mô phỏng mạch, source và thư viện; kết quả mô phỏng không thay thế việc kiểm chứng cấp nguồn, cơ khí hoặc nhiễu của mô hình thật.

## 1.7. MQTT và Publish/Subscribe

Firmware trao đổi bản tin qua topic với broker được cấu hình là broker.hivemq.com:1883. Thiết bị publish trạng thái bốn ô, heartbeat và phản hồi cổng; subscribe topic lệnh. Theo source, subscribe lệnh yêu cầu QoS 1, các lệnh publish hiện dùng QoS 0 và không retained. Đây là cấu hình được đọc từ mã, chưa phải kết quả đo truyền tin trực tiếp.

## 1.8. REST API, WebSocket và SQLite

[CHƯA THỰC HIỆN — TV2 bổ sung cơ sở lý thuyết, lựa chọn công nghệ và đối chiếu triển khai sau khi có Backend.]

## 1.9. Dashboard và trực quan hóa 3D

Dashboard tổng hợp thông tin vận hành thành KPI, thẻ ô đỗ, bảng sự kiện và biểu đồ. Spline là công cụ biểu diễn scene 3D; Runtime nhận dữ liệu từ React để thay đổi xe, màu và góc quay. Mô hình 3D là lớp hiển thị, không phải nguồn phát hiện xe.

## 1.10. Tổng kết chương

Các thành phần được lựa chọn phù hợp mô hình thực hành bốn ô. Cần phân biệt dữ liệu GPIO, bản tin MQTT và trạng thái mock; các lớp chỉ trở thành hệ thống liên thông sau khi Backend và adapter được triển khai, kiểm thử.

# CHƯƠNG 2. PHÂN TÍCH YÊU CẦU VÀ THIẾT KẾ HỆ THỐNG

## 2.1. Tác nhân sử dụng

Người giám sát xem trạng thái bãi, người vận hành thực hiện thao tác cổng, Device phát dữ liệu ô đỗ. Trong bản demo, thao tác trên giao diện tạo trạng thái giả lập để kiểm tra tính nhất quán; chưa có đăng nhập hoặc phân quyền thực tế.

## 2.2. Yêu cầu chức năng

| Mã | Chức năng | Kết quả hiện tại |
|---|---|---|
| FR01 | Theo dõi bốn ô | Đã có ở Frontend mock; Device có logic đọc công tắc |
| FR02 | MQTT → Backend → Dashboard | Chưa thực hiện end-to-end |
| FR03 | Cảnh báo FULL | Frontend demo đã được người dùng xác nhận |
| FR04 | Điều khiển cổng | Frontend 3D được xác nhận; Device có code lệnh/ACK, chưa xác minh vận hành |
| FR05 | Lịch sử/thống kê | Đã có trong phiên Frontend, chưa lưu database |
| FR06 | Mô hình 3D | Đã chạy scene và các thao tác người dùng xác nhận |

## 2.3. Yêu cầu phi chức năng

Dữ liệu trên UI cần nhất quán, lỗi scene không làm mất toàn bộ Dashboard, bố cục sử dụng được trên desktop/tablet và cấu hình dễ tái lập. Mất mạng, dữ liệu cũ, reconnect và độ trễ MQTT đầu cuối cần được kiểm thử khi tích hợp; hiện chưa có số đo để khẳng định chất lượng các phần này.

## 2.4. Phạm vi MVP và mở rộng

MVP hiện tập trung bốn ô, cảnh báo FULL, cổng, sự kiện, thống kê và biểu diễn 3D. Giai đoạn tiếp theo nối Backend và Device. Nhận dạng biển số, thanh toán và tăng quy mô nằm ngoài phần đã triển khai.

## 2.5. Kiến trúc tổng thể

```text
ESP32/Wokwi → MQTT Broker → FastAPI → REST/WebSocket → React Dashboard → Spline 3D
                              ↕
                            SQLite
```

Sơ đồ trên là kiến trúc đích. Hiện Frontend lấy dữ liệu từ parkingService mock, chưa nhận MQTT qua FastAPI.

## 2.6. Phần cứng và kết nối

| Bộ phận | ESP32 | Quy ước |
|---|---|---|
| P01 | GPIO13 | Công tắc chân giữa 2 tới GPIO; chân 1 tới GND |
| P02 | GPIO14 | INPUT_PULLUP, LOW = có xe |
| P03 | GPIO27 | INPUT_PULLUP, LOW = có xe |
| P04 | GPIO26 | INPUT_PULLUP, LOW = có xe |
| SG90 PWM | GPIO18 | Góc đóng 0°, mở 90° theo source |
| SG90 nguồn | 5V và GND | Theo diagram.json mô phỏng |

Sơ đồ hiện có 6 parts và 11 connections, JSON hợp lệ. [CHÈN HÌNH 2.1: ảnh diagram Wokwi từ dự án của nhóm; chưa có ảnh minh chứng mới trong tài liệu này.]

## 2.7. Luồng dữ liệu và MQTT

| Topic | Hướng |
|---|---|
| smartparking/group21/slots/P01/state | Device publish |
| smartparking/group21/slots/P02/state | Device publish |
| smartparking/group21/slots/P03/state | Device publish |
| smartparking/group21/slots/P04/state | Device publish |
| smartparking/group21/device/status | Device publish heartbeat/Will |
| smartparking/group21/gate/command | Device subscribe |
| smartparking/group21/gate/status | Device publish ACK |

Payload slot hiện có:

```json
{"device_id":"esp32-01","slot_id":"P01","occupied":true}
```

Payload lệnh:

```json
{"command_id":"report-demo-001","action":"OPEN","direction":"ENTRY"}
```

Payload phản hồi:

```json
{"device_id":"esp32-01","command_id":"report-demo-001","status":"OPENED"}
```

Các action hợp lệ là OPEN/CLOSE, direction ENTRY/EXIT. Firmware debounce 400 ms, heartbeat 10 giây, thử kết nối lại theo khoảng 5 giây. Khi reconnect, bốn ô được đánh dấu gửi lại. Payload Device chưa có UTC; Backend dự kiến bổ sung received_at. Xem mqtt-contract.md để có đầy đủ điều kiện xử lý.

## 2.8. Thiết kế Backend và API/WebSocket

[CHƯA THỰC HIỆN — bổ sung sau. Các endpoint trong api-contract.md hiện chỉ là đề xuất, không đưa thành API đã triển khai.]

## 2.9. Thiết kế cơ sở dữ liệu

[CHƯA THỰC HIỆN — bổ sung schema/ERD theo Backend thực tế sau.]

## 2.10. Dashboard và mô hình 3D

Giao diện có bốn trang Tổng quan, Quản lý ô đỗ, Lịch sử hoạt động và Báo cáo thống kê. KPI phản ánh tổng bốn ô, số có xe, còn trống và trạng thái bãi. UNKNOWN không được tính là ô còn trống. Khi cả bốn OCCUPIED, trạng thái là FULL; khi có EMPTY, trạng thái AVAILABLE; nếu không có EMPTY nhưng còn UNKNOWN, trạng thái UNKNOWN.

| Trạng thái | Xe trong scene | Màu yêu cầu |
|---|---|---|
| EMPTY | Ẩn | Xanh |
| OCCUPIED | Hiện | Màu chiếm dụng; người dùng mô tả đỏ, mapping hiện tại dùng #f97316 |
| UNKNOWN | Ẩn | Xám; còn cần xác nhận trực quan riêng |

Tên mapping là Slot_P01–Slot_P04 và Car_P01–Car_P04; cổng dùng Gate_Barrier. Không đổi tên hoặc Scene URL. [CHÈN HÌNH 2.2: ảnh Dashboard thực tế.]

## 2.11. Xe vào/ra và barrier

Ở demo, bấm ô để chuyển có xe/trống, hoặc chọn UNKNOWN; thao tác cập nhật store, UI và Runtime. OPEN/CLOSE cập nhật trạng thái và góc barrier theo trục/chiều được chọn. Góc ban đầu được lưu để đóng trở lại.

Firmware Device nhận action/direction và điều khiển một servo. Source chưa có quy tắc chặn ENTRY khi FULL hoặc tự suy ra xe qua cổng; direction được kiểm tra nhưng không phải cơ chế phát hiện xe. Không tuyên bố TC ENTRY khi FULL đã đạt. Chính sách này cần nhóm thống nhất và triển khai/kiểm thử khi có Backend.

## 2.12. Bảo mật và xử lý lỗi

Firmware kiểm tra JSON và trường lệnh, giới hạn độ dài command_id, có xử lý busy, phản hồi ERROR và nhận lại lệnh hoàn tất gần nhất. Cơ chế này chưa phải lưu idempotency lâu dài. Broker hiện công cộng, không xác thực/TLS trong cấu hình; chỉ phù hợp demo, không coi là thiết kế bảo mật hoàn chỉnh.

Frontend có Error Boundary cho scene, thông báo tải/lỗi và kiểm tra dữ liệu trạng thái. Đợt audit đã lưu cho kết quả 0 vulnerabilities sau nâng Vite; kết quả đó thuộc thời điểm đã kiểm tra, không phải cam kết không có mọi rủi ro.

## 2.13. Phân công và kế hoạch tích hợp

TV1 phụ trách Device; TV2 phụ trách Backend; TV3 phụ trách Frontend. Workspace chia device/, backend/, frontend/ và docs/ chung. Chưa có thao tác git init/commit/push trong đợt tổ chức. Trước tích hợp cần chốt boolean → enum, slot_id → slotId, CLOSE/CLOSED, OPENED/OPEN, direction, timeout UNKNOWN và chống trùng sự kiện.

## 2.14. Tổng kết chương

Thiết kế Device và Frontend đã có source tương ứng. Phần trung gian xử lý dữ liệu và luật vận hành chưa được hiện thực. Các contract chung giúp nhóm xác định khác biệt trước triển khai Backend, không thay đổi payload hiện tại.

# CHƯƠNG 3. TRIỂN KHAI VÀ XÂY DỰNG HỆ THỐNG

## 3.1. Môi trường và cấu trúc dự án

Frontend sử dụng React/React DOM 18, JSX, Vite 6.4.4, plugin React 4, Spline React 4, Runtime 2.0.93, Recharts 2, Lucide React và CSS. Node.js dùng trong lượt kiểm thử trước là 24.18.0. Phiên bản khóa đọc từ frontend/package-lock.json; khoảng ^ trong package.json không phải phiên bản cài chính xác.

Device sử dụng Arduino/C++, WiFi, PubSubClient, ESP32Servo và ArduinoJson. libraries.txt chưa khóa phiên bản; cần ghi lại phiên bản thực tế khi chạy Wokwi, không suy đoán.

```text
SmartParking-Group21/
  device/       firmware, sơ đồ, thư viện, link Wokwi
  backend/      README — chưa có source
  frontend/     src, tests, docs, cấu hình React/Vite
  docs/         tài liệu chung, contracts, logs và manifest checksum
```

## 3.2. Triển khai ESP32 trên Wokwi

Firmware khởi tạo Serial 115200, cấu hình bốn GPIO INPUT_PULLUP và đọc trạng thái ban đầu. Trong vòng lặp, tín hiệu thay đổi được lấy mẫu, chỉ cập nhật occupied khi giữ ổn định qua khoảng debounce. Khi trạng thái đổi, slotDirty được bật để gửi MQTT. diagram.json và libraries.txt đã được cung cấp cùng sketch.ino.

Đây là mô tả triển khai từ mã nguồn, chưa phải xác nhận mô phỏng đã chạy. Dự án ghi trong wokwi-project.txt: https://wokwi.com/projects/478203397293414401. [BỔ SUNG ảnh chạy và log biên dịch khi TV1 thực hiện.]

## 3.3. Wi-Fi và MQTT

Firmware dùng Wi-Fi Wokwi-GUEST, broker.hivemq.com cổng 1883. Các hàm reconnect kiểm tra thời gian thử lại, cấu hình Will offline và subscribe lệnh cổng. Sau kết nối, firmware gửi heartbeat và đặt lại cờ gửi trạng thái bốn ô. Khi publish không thành công, cờ ô chưa được xóa để tiếp tục thử.

Chưa có log mạng trực tiếp được xác minh trong lượt này; không đưa chuỗi log mẫu trong source thành bằng chứng kết nối thành công.

## 3.4. Servo/barrier Device

Firmware kiểm tra command_id, action và direction trước khi điều khiển. Khi nhận lệnh hợp lệ, servo được đặt góc mục tiêu và đánh dấu gateMoving. Sau 700 ms, phần mềm cập nhật OPENED/CLOSED và xếp phản hồi. Lệnh mới trong khi bận bị từ chối; lệnh trùng lệnh hoàn tất gần nhất được phản hồi lại.

Không có cảm biến đo góc hoặc xe qua barrier, nên ACK là trạng thái phần mềm sau thời gian chờ, không phải xác nhận cơ khí thực tế. [BỔ SUNG minh chứng Wokwi khi có.]

## 3.5. FastAPI MQTT Subscriber

[CHƯA THỰC HIỆN — TV2 bổ sung sau.]

## 3.6. SQLite và quản lý trạng thái Backend

[CHƯA THỰC HIỆN — TV2 bổ sung sau.]

## 3.7. REST API và WebSocket

[CHƯA THỰC HIỆN — bổ sung endpoint, Swagger và bản tin thực tế sau.]

## 3.8. React Dashboard

UI được xây dựng theo component React với trạng thái dùng chung từ parkingService. Service cung cấp getParkingStatus, getParkingEvents, getParkingStatistics, updateSlotStatus, updateGateStatus, subscribe và reset. React nhận thay đổi qua useSyncExternalStore; snapshot có tham chiếu ổn định đến khi có cập nhật.

Các snapshot được đóng băng để tránh sửa ngoài service. Hợp đồng có schema_version 1.0, source DEMO, slots, gate, timestamp và events. Validator kiểm tra phần trạng thái; chưa xác thực đầy đủ mọi trường sự kiện cho dữ liệu mạng. Timestamp xuất UTC ISO và hiển thị giờ địa phương.

Lịch sử lưu id, timestamp, slotId, type, previous và current. IN được ghi khi chuyển sang OCCUPIED, OUT khi OCCUPIED → EMPTY; các thay đổi ô khác là STATUS. UNKNOWN → OCCUPIED hiện tính IN theo hành vi demo, cần chốt lại nếu dùng cho thống kê xe vật lý. Cập nhật trùng trạng thái không tạo sự kiện. Thống kê và biểu đồ dùng cùng lịch sử, không dùng số ngẫu nhiên độc lập.

## 3.9. Spline 3D

Scene được nhúng qua @splinetool/react-spline, Runtime instance lưu bằng useRef. Khi tải, chương trình kiểm tra tên đối tượng; đồng bộ dùng visibility cho xe, color cho ô và rotation cho cổng. Scene URL giữ nguyên:

```text
https://prod.spline.design/NNU0y3In1BxfOzsL/scene.splinecode
```

Scene được giữ mount khi chuyển trang. Error Boundary giữ phần Dashboard hoạt động nếu 3D lỗi. Trong quá trình phát triển đã sửa cấu hình React/Vite, trạng thái báo lỗi và nâng Runtime; kiểm thử sau đó tải được đủ 12/12 đối tượng. Không tuyên bố mọi lỗi trước đây còn đang tái hiện sau xác nhận chạy thành công.

## 3.10. Tích hợp ba lớp

[CHƯA THỰC HIỆN — chưa có Backend, chưa có bằng chứng MQTT → Dashboard end-to-end.]

## 3.11. Cài đặt và vận hành demo

Tại thư mục gốc dự án:

```powershell
cd frontend
npm test
npm run dev -- --force
```

Mở URL Terminal hiển thị. Để kiểm tra production, chạy npm run build rồi npm run preview. Bản workspace hiện có dependencies; trên máy mới chưa có node_modules, chuẩn bị dependencies theo lockfile, ví dụ npm ci. Không cần chạy Backend cho demo mock.

Kịch bản demo: đổi trạng thái từng ô; đưa cả bốn OCCUPIED để xem FULL; thử UNKNOWN; mở/đóng cổng theo cấu hình trục đã xác minh; xem lịch sử và biểu đồ; RESET; refresh. Demo Device chạy riêng trên Wokwi, chưa kết nối với Dashboard.

## 3.12. Tổng kết chương

Device có source và cấu hình mô phỏng; Frontend hoạt động độc lập với mock và scene Spline. Backend và luồng tích hợp còn để sau. Mã nguồn đã được gom bằng sao chép, giữ nguyên bản gốc và kiểm tra checksum.

# CHƯƠNG 4. KIỂM THỬ, KẾT QUẢ VÀ ĐÁNH GIÁ

## 4.1. Phương pháp kiểm thử

Phân biệt ba nguồn bằng chứng: kiểm thử người dùng trên giao diện/3D; kiểm thử tự động service, trình duyệt và build đã ghi nhận; kiểm tra tĩnh Device. Chưa thực hiện kiểm thử tích hợp MQTT/FastAPI/SQLite. Không chuyển các kịch bản kỳ vọng thành PASS nếu chưa chạy.

## 4.2. Kịch bản chức năng đã có kết quả

| ID | Thao tác/điều kiện | Kết quả thực tế | Nguồn |
|---|---|---|---|
| FE01 | P01 có xe → trống | Xe ẩn, ô xanh | Người dùng xác nhận |
| FE02 | P02 trống → có xe | Xe hiện, ô màu chiếm dụng | Người dùng xác nhận |
| FE03 | Bốn ô OCCUPIED | Available = 0, FULL | Người dùng xác nhận |
| FE04 | OPEN/CLOSE trên mô hình | Barrier xoay đúng | Người dùng xác nhận |
| FE05 | Tạo thao tác demo | History/statistics cập nhật | Người dùng xác nhận |
| FE06 | P01 EMPTY → UNKNOWN | Available 4 → 3, unknown = 1, STATUS; IN/OUT không tăng | Kiểm thử tự động đã ghi nhận |
| FE07 | RESET sau thay đổi | Bốn EMPTY, CLOSED, history rỗng, bộ đếm 0 | Unit test và UI đã ghi nhận |
| FE08 | UNKNOWN rồi refresh | P01 về EMPTY; scene tải lại, đủ 12/12 | Kiểm thử trình duyệt đã ghi nhận |
| FE09 | Kiểm thử service | 5/5 PASS | Log mới trong docs/frontend-test.log |
| FE10 | Production build bản monorepo | Thành công, 21.38 giây | docs/frontend-build.log |

Bằng chứng FE06–FE08 thuộc lượt kiểm thử Frontend trước khi sao chép monorepo; lượt tổ chức chạy lại unit/build và checksum, không chạy lại toàn bộ trình duyệt.

## 4.3. Kiểm thử MQTT

[CHƯA THỰC HIỆN TRONG LƯỢT XÁC MINH — cần log Device/broker, biến đổi công tắc, đối chiếu topic/payload và phương pháp đo độ trễ.]

Báo cáo TV1 có nhắc kiểm tra tĩnh 10/10 bằng tests/verify_static.py, nhưng script không có trong source được cung cấp. Chỉ ghi nhận nội dung tài liệu đó, không coi là bộ test đã chạy lại.

## 4.4. API, cơ sở dữ liệu và WebSocket

[CHƯA THỰC HIỆN — bổ sung khi Backend được triển khai.]

## 4.5. Dashboard và 3D

Các thao tác xe và FULL đã có xác nhận người dùng. Trình duyệt production từng tải thành công 12/12 đối tượng; Console được đọc ở mức error/warn trả mảng rỗng trong các thao tác đã kiểm tra. Desktop 1440×900 và tablet 768×1024 không tràn ngang theo DOM; workspace tablet chuyển một cột.

Kiểm tra DOM không chứng minh chất lượng ảnh WebGL. Màu xám/ẩn xe UNKNOWN và reset chuyển động 3D còn cần quan sát riêng. Công cụ chụp ảnh kiểm thử trước gặp hạn chế, chưa có bộ ảnh responsive đáng tin để đưa vào báo cáo cuối kỳ.

## 4.6. Cổng và tình huống bãi đầy

| Kịch bản | Trạng thái |
|---|---|
| Cổng 3D OPEN/CLOSE trong demo | Đã được người dùng xác nhận |
| ENTRY khi FULL bị từ chối | Chưa triển khai/xác minh luật liên thông |
| EXIT khi FULL vẫn được phép | Chưa kiểm thử end-to-end |
| Servo Device nhận lệnh và trả ACK | Có code; chưa có kết quả chạy trực tiếp được xác minh |

Không suy từ FULL hiển thị đúng sang kết luận cổng tự chặn ENTRY đúng.

## 4.7. Lỗi và độ ổn định

Đã có xử lý lỗi scene, kiểm tra dữ liệu service, no-op khi trạng thái không đổi và khởi tạo nhất quán khi refresh. Unit tests kiểm tra UNKNOWN, reset, snapshot bất biến, JSON roundtrip, ID/trạng thái không hợp lệ và regression IN/OUT/FULL.

Các trường hợp mất broker, Wi-Fi, timeout ACK, reconnect WS và dữ liệu MQTT lỗi chưa được kiểm thử toàn hệ thống. Chưa có kết quả thử tải hoặc chạy dài hạn.

## 4.8. Tổng hợp minh chứng

| Minh chứng | Vị trí trong dự án |
|---|---|
| Firmware và sơ đồ | device/sketch.ino, device/diagram.json |
| Topic/payload đọc từ firmware | docs/mqtt-contract.md |
| Báo cáo Device được bảo toàn | frontend/docs/Rp-Tv1.md |
| Báo cáo Frontend được bảo toàn | frontend/docs/Rp-Tv3_CongNgheSuDung_TienDO.md |
| Contract Frontend | frontend/docs/DATA_CONTRACT.md |
| Unit test mới trên bản sao | docs/frontend-test.log |
| Build mới trên bản sao | docs/frontend-build.log |
| JSON/import/checksum sau build | docs/validation.log |
| Manifest sao chép | docs/copy-checksums.csv, docs/copy-summary.json |
| Audit trước/sau đã lưu | frontend/docs/audit-before.json, audit-after.json |

Sao chép xác minh Device 4/4 file, Frontend 9.358/9.358 file, SHA-256 khớp toàn bộ tại thời điểm sao chép. Sau build, 23 file nguồn/tài liệu ngoài node_modules/dist vẫn khớp. Đây là kiểm tra bảo toàn source, không phải bằng chứng phần cứng chạy.

[CHƯA CÓ: link video demo, ảnh minh chứng có chú thích và commit Git để trích dẫn.]

## 4.9. Ưu điểm và hạn chế

Ưu điểm là phân lớp rõ, mock dùng chung cho KPI/lịch sử/thống kê, scene đã đồng bộ theo thao tác kiểm thử và source/tài liệu được giữ nguyên khi gom workspace. Hạn chế là chưa có Backend, chưa có dữ liệu cảm biến thực, chưa kiểm thử end-to-end, không có persistence mock và còn cảnh báo bundle lớn. Broker công cộng chưa phù hợp triển khai thực tế cần kiểm soát truy cập.

## 4.10. Tổng kết chương

Frontend demo có bằng chứng chức năng và kiểm thử logic/build. Device mới được xác minh tĩnh trong phạm vi hiện có. Chưa đủ cơ sở kết luận hệ thống IoT hoàn chỉnh đã vận hành xuyên suốt.

# CHƯƠNG 5. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

## 5.1. Kết quả so với mục tiêu

Nhóm đã có mô hình Device bằng firmware/sơ đồ, Dashboard React và scene Spline điều khiển bằng mock. Frontend đáp ứng các tình huống demo đã xác nhận, có tests và build thành công. Mục tiêu truyền dữ liệu từ ESP32 qua MQTT/FastAPI tới Dashboard và lưu SQLite chưa hoàn thành.

## 5.2. Đóng góp của từng thành viên

| Thành viên | Nội dung hiện có theo phân công | Minh chứng |
|---|---|---|
| TV1 — Huỳnh Đổ Hoàng Nguyên | Firmware, mạch Wokwi, khai báo thư viện, MQTT và servo | device/ và báo cáo TV1; cần bổ sung log chạy |
| TV2 — Bạch Ngọc Hợp | Backend theo kế hoạch | Chưa có source; bổ sung sau |
| TV3 — Bùi Tấn Phước | React/Vite, Spline, mock service, điều hướng, KPI/history/statistics, tests và tài liệu | frontend/, logs và xác nhận người dùng |

Bảng là phân công/hiện trạng module, không thay thế lịch sử đóng góp Git. Chưa có commit để kiểm chứng tác giả từng dòng mã.

## 5.3. Hạn chế còn tồn tại

Chưa kiểm chứng phần cứng thực, Wokwi/MQTT trực tiếp và kết nối toàn hệ thống. Chưa có luật cổng ENTRY/FULL được xác minh. Lựa chọn trục/chiều barrier thuộc phiên, chưa cố định bằng thông số người dùng cung cấp. Frontend demo mất dữ liệu khi refresh; QA trực quan UNKNOWN/reset và tablet chưa đầy đủ.

## 5.4. Hướng phát triển

Ưu tiên chạy kiểm thử Device và lưu bằng chứng; chốt contract và luật nghiệp vụ; triển khai Backend; nối adapter REST/WebSocket; sau đó chạy checklist end-to-end. Các mở rộng cảm biến thật, mô hình vật lý, tăng số ô và bảo mật sẽ xem xét khi MVP liên thông ổn định. Đây là kế hoạch, không phải phần đã hoàn thành.

# TÀI LIỆU THAM KHẢO

Nguồn nội bộ đã dùng để viết báo cáo: source device/, source frontend/, docs/mqtt-contract.md, docs/integration-plan.md, frontend/docs/DATA_CONTRACT.md, hai báo cáo thành viên và log ở Bảng 4.8.

Liên kết tài nguyên dự án do nhóm cung cấp: Wokwi https://wokwi.com/projects/478203397293414401 và Scene URL ghi tại mục 3.9. Các liên kết này là tài nguyên nhóm, không thay thế tài liệu lý thuyết.

[BỔ SUNG SAU: giáo trình và tài liệu chính thức thực sự đã sử dụng, tác giả/tổ chức, tiêu đề, URL và ngày truy cập theo định dạng giảng viên yêu cầu. Không tự tạo tài liệu hoặc ngày truy cập.]

# PHỤ LỤC

## A. Phân công và nhật ký

Tham khảo docs/progress.md. [BỔ SUNG nhật ký theo tuần, ngày thực hiện và xác nhận thành viên.]

## B. MQTT contract

Dùng docs/mqtt-contract.md; giữ nguyên topic và JSON từ firmware. Không thêm timestamp vào mô tả payload hiện tại nếu Device chưa gửi trường đó.

## C. API/WebSocket

[CHƯA THỰC HIỆN — api-contract.md chỉ là đề xuất để TV2 bổ sung sau.]

## D. GPIO và Wokwi

Bảng chân ở mục 2.6, file device/diagram.json và device/wokwi-project.txt. [BỔ SUNG ảnh mạch và phiên bản thư viện khi chạy thực tế.]

## E. Test case và bằng chứng

Dùng bảng mục 4.2, docs/frontend-test.log, docs/frontend-build.log và frontend/tests/parkingService.test.js. [BỔ SUNG ảnh TC và video; không dùng ảnh mẫu thay bằng chứng chạy.]

## F. Nguồn thư viện, asset và hỗ trợ AI

Thư viện được khai báo trong frontend/package.json và device/libraries.txt. Asset Smart_Parking_MVP.glb đã được nhóm cung cấp/import lên Spline trước khi tích hợp; cần bổ sung nguồn tạo, tác giả và quyền sử dụng theo thực tế, chưa có bằng chứng để khẳng định tác quyền.

Trong quá trình làm việc, AI hỗ trợ chỉnh sửa/tổ chức source Frontend, mock service, tests, xử lý lỗi, rà soát dependencies, gom workspace và soạn tài liệu theo yêu cầu. Người dùng trực tiếp kiểm thử năm tình huống UI/3D; các tests và logs tự động được phân biệt trong báo cáo. Nhóm cần rà soát và chịu trách nhiệm nội dung trước khi nộp.

# TIẾN ĐỘ HOÀN THIỆN BẢN BÁO CÁO

| Phần | Trạng thái nội dung | Cần bổ sung |
|---|---|---|
| Chương 1 | Có bản thảo Device/Frontend | Tài liệu lý thuyết chính thức, mục 1.8 |
| Chương 2 Device và UI | Có bản thảo theo source | Ảnh mạch/UI và contract đã chốt |
| Chương 2 Backend/DB | Chưa thực hiện | TV2 bổ sung |
| Chương 3 Device | Có mô tả mã nguồn | Biên dịch, log chạy Wokwi/MQTT |
| Chương 3 Frontend | Có nội dung và kết quả | Ảnh minh chứng được chú thích |
| Chương 3 Backend/tích hợp | Chưa thực hiện | Source và kết quả thực tế |
| Chương 4 | Có kết quả Frontend và kiểm tra tĩnh | E2E, lỗi mạng, QA trực quan |
| Chương 5 | Có đánh giá giai đoạn hiện tại | Cập nhật theo kết quả cuối kỳ |

Khi chuyển sang Word, áp dụng Heading 1/2/3 cho chương/mục, tạo mục lục tự động, thêm danh mục hình/bảng và cập nhật số trang. Không giữ nguyên các nhãn chờ bổ sung trong bản nộp cuối nếu chưa thống nhất với giảng viên.
