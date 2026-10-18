# SmartParking Group 21 — Hướng dẫn cài đặt và chạy từ A–Z

Ngày cập nhật: **19/10/2026**. Đối tượng: các thành viên nhận source từ GitHub và chạy trên Windows/PowerShell. Không cần cài lại môi trường mỗi lần demo.

## 1. Trạng thái bản hướng dẫn và điều kiện clone

Người dùng đã xác nhận **“oke test được rồi”** sau quá trình sửa lỗi và bổ sung gửi lại baseline. Đây là xác nhận kiểm thử của người dùng trong hội thoại, chưa phải biên bản PASS riêng cho toàn bộ 10 ca E2E hoặc thử trên máy mới.

Repo được cấu hình trong dự án local:

**https://github.com/Hopbach123/SmartParking-Group21.git**

**Điểm cần xử lý trước khi phát hành cho nhóm:** tại lúc viết tài liệu, Backend mới và adapter LIVE đã tồn tại trên máy chủ dự án, nhưng các file `backend/app/main.py`, `backend/requirements-lock.txt`, `backend/.env.example`, `frontend/src/services/liveParkingService.js`, `frontend/.env.example` chưa có trong Git index/HEAD local đã kiểm tra. Chưa kiểm tra trực tiếp phiên bản trên GitHub. Vì vậy không khẳng định clone hiện tại đã có đủ source mới. Chủ repo cần kiểm tra và đưa bản source hoàn chỉnh lên nhánh bàn giao trước khi các thành viên làm theo phần LIVE.

Tài liệu này không tự commit/push, không yêu cầu thành viên dùng các script nằm trên ổ C của máy tác giả. Sau khi repo đủ file, mọi lệnh cài/chạy bên dưới thực hiện ngay trong bản clone của mỗi người.

## 2. Hệ thống gồm những phần nào?

| Phần | Vai trò | Chạy ở đâu? |
|---|---|---|
| Device | ESP32, bốn công tắc mô phỏng cảm biến P01–P04 và servo cổng | Wokwi trên trình duyệt |
| Backend | Nhận MQTT, lưu SQLite, cung cấp REST/WebSocket và xử lý lệnh cổng | Terminal 1, cổng 8000 |
| Frontend | Dashboard React, KPI, lịch sử, thống kê và Spline 3D | Terminal 2, Vite cổng 5173 |
| MQTT broker | Chuyển bản tin giữa ESP32 và Backend | broker.hivemq.com:1883 |
| SQLite | Lưu trạng thái cuối, lịch sử và lệnh | File trên máy chạy Backend |

```text
Công tắc Wokwi → ESP32 → MQTT → FastAPI → SQLite
                                      ↓ REST / WebSocket
                                React Dashboard → Spline

Nút cổng trên Dashboard → FastAPI → MQTT → ESP32/servo
Dashboard/Spline ← WebSocket ← FastAPI ← ACK OPENED/CLOSED
```

Vite là chương trình chạy giao diện React. Uvicorn là chương trình chạy FastAPI. Hai terminal phải tiếp tục chạy trong lúc sử dụng LIVE.

## 3. Cài công cụ trên máy mới

Môi trường đã dùng để kiểm tra dự án: **Python 3.11.9, Node.js 24.18.0 và Windows PowerShell**. Đây là môi trường tham chiếu, không khẳng định mọi phiên bản Python/Node khác đã được kiểm thử.

| Công cụ | Cách chuẩn bị |
|---|---|
| Git | Cài Git for Windows từ [trang chính thức](https://git-scm.com/install/windows), giữ tùy chọn dùng Git trong terminal |
| Python | Cài Python 3.11 từ [Python cho Windows](https://www.python.org/downloads/windows/); nếu dùng installer truyền thống, bật Add Python to PATH và Python Launcher khi có tùy chọn |
| Node.js/npm | Cài Node.js nhánh 24 từ [trang Node.js](https://nodejs.org/en/download); npm đi kèm Node |
| Trình duyệt | Có WebGL, truy cập được Wokwi và Spline |
| VS Code | Dùng để mở repo, sửa .env và mở hai terminal; không bắt buộc để chạy lệnh |

Không cần tải SQLite server, Docker, Arduino IDE hoặc cài MQTT broker local để chạy cấu hình demo hiện tại. Firmware được biên dịch trên Wokwi.

Sau khi cài, **đóng và mở terminal mới**, chạy:

```powershell
git --version
py -3.11 --version
node --version
npm --version
```

Nếu `py` không có nhưng `python --version` đúng Python 3.11, thay `py -3.11` bằng `python` trong bước tạo venv. Nếu máy có nhiều Python, dùng đúng executable 3.11; không tạo venv bằng một phiên bản chưa được nhóm kiểm chứng rồi coi lỗi dependency là lỗi ứng dụng.

## 4. Clone và mở đúng thư mục

Mở PowerShell tại thư mục bạn muốn lưu project, sau đó:

```powershell
git clone https://github.com/Hopbach123/SmartParking-Group21.git
cd SmartParking-Group21
```

Nếu muốn mở VS Code và đã có lệnh `code`:

```powershell
code .
```

Không bắt buộc dùng ổ F hoặc đường dẫn giống máy tác giả. Trong hướng dẫn, **thư mục gốc** nghĩa là `SmartParking-Group21` vừa clone, nơi có README.md, device/, backend/, frontend/ và docs/.

Kiểm tra các file quan trọng trước khi cài:

```powershell
Test-Path .\backend\app\main.py
Test-Path .\backend\requirements-lock.txt
Test-Path .\backend\.env.example
Test-Path .\frontend\package-lock.json
Test-Path .\frontend\src\services\liveParkingService.js
Test-Path .\frontend\.env.example
Test-Path .\device\sketch.ino
```

**Tất cả phải là True để chạy đầy đủ LIVE.** Nếu thiếu Backend/LIVE, dừng và hỏi chủ repo về nhánh/commit bàn giao; cài package không thể tạo lại source đang thiếu. Nếu nhóm yêu cầu nhánh khác nhánh mặc định, dùng tên nhánh do nhóm cung cấp, không tự đoán tên.

## 5. Cài Backend — làm một lần trên mỗi bản clone

Từ thư mục gốc:

```powershell
py -3.11 -m venv backend/.venv
.\backend\.venv\Scripts\python.exe -m pip install -r .\backend\requirements-lock.txt
.\backend\.venv\Scripts\python.exe -m pip check
```

Kỳ vọng `pip check` báo `No broken requirements found`. Khi cài package gặp lỗi mạng/PyPI, kiểm tra mạng và chạy lại; không tự nâng toàn bộ dependency để che lỗi. Requirements đã pin phiên bản trong repo.

Hướng dẫn dùng đường dẫn Python của venv trực tiếp nên **không cần activate**, không cần thay PowerShell execution policy. `.venv` chỉ chứa môi trường Python, không phải nơi lưu source. Máy mới tự tạo venv, không copy venv của người khác.

### Tạo cấu hình Backend

Từ thư mục gốc, chỉ copy khi file chưa tồn tại:

```powershell
if (!(Test-Path .\backend\.env)) {
    Copy-Item .\backend\.env.example .\backend\.env
}
```

Mở `backend/.env` và đối chiếu nội dung:

```dotenv
SMART_PARKING_DB_PATH=data/smartparking.sqlite3
SMART_PARKING_CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:4173
SMART_PARKING_MQTT_ENABLED=true
SMART_PARKING_MQTT_HOST=broker.hivemq.com
SMART_PARKING_MQTT_PORT=1883
SMART_PARKING_HEARTBEAT_TIMEOUT=30
SMART_PARKING_ACK_TIMEOUT=15
```

**Lưu ý:** `.env.example` tại thời điểm kiểm tra vẫn ghi ACK timeout=5. Cấu hình demo trên máy tác giả đã đặt **15 giây** để chịu độ trễ ACK từng quan sát được từ Wokwi. Thành viên mới cần sửa dòng này trong `.env`; không nhầm nó với MQTT socket timeout của firmware.

| Biến | Ý nghĩa |
|---|---|
| DB_PATH | Đường dẫn tương đối tính theo backend/, không theo thư mục terminal |
| CORS_ORIGINS | Các origin Frontend được phép gọi API/WS; localhost và 127.0.0.1 là hai origin khác nhau |
| MQTT_ENABLED | true cho LIVE; false để chạy Backend không kết nối broker khi kiểm tra riêng |
| MQTT_HOST/PORT | Phải khớp broker trong firmware |
| HEARTBEAT_TIMEOUT | 30 giây thực phía Backend để đánh dấu thiết bị mất tín hiệu |
| ACK_TIMEOUT | Thời gian chờ ACK lệnh cổng, demo đặt 15 giây thực |

Backend ưu tiên biến môi trường của tiến trình hơn `.env`. Nếu đã đặt biến trong PowerShell hoặc hệ điều hành, kiểm tra chúng khi sửa `.env` không có tác dụng. Không ghi credentials thật vào `.env.example` hoặc Git.

### SQLite được tạo thế nào?

Không cần tự tạo bảng hay tải phần mềm SQLite riêng. Backend khởi tạo file `backend/data/smartparking.sqlite3` và schema khi chạy. Khi chưa có dữ liệu cảm biến đáng tin, bốn ô là UNKNOWN. DB giữ lịch sử sau restart; trạng thái công khai có thể về UNKNOWN tới khi nhận baseline mới.

Không copy database của máy tác giả làm dữ liệu cảm biến mới cho máy khác. Không xóa DB để xử lý lỗi kết nối. Nếu cần sao lưu thủ công, dừng Backend trước rồi copy file DB và lưu ngoài Git.

## 6. Cài Frontend — làm một lần trên mỗi bản clone

Từ thư mục gốc:

```powershell
cd frontend
npm ci
cd ..
```

`npm ci` cài theo package-lock.json; cần mạng để tải dependencies. Không cần cài React/Vite toàn cục và không chép node_modules từ máy khác. Khi dùng lại thư mục cũ, chỉ chạy npm ci khi cần đồng bộ dependencies; không chạy nó trong lúc Vite đang sử dụng thư mục.

### Tạo cấu hình Frontend

Từ thư mục gốc:

```powershell
if (!(Test-Path .\frontend\.env.local)) {
    Copy-Item .\frontend\.env.example .\frontend\.env.local
}
```

Để **LIVE**, nội dung `frontend/.env.local`:

```dotenv
VITE_PARKING_MODE=LIVE
VITE_BACKEND_REST_URL=http://localhost:8000
VITE_BACKEND_WS_URL=ws://localhost:8000/ws/parking
```

Để **DEMO**, đổi dòng mode thành:

```dotenv
VITE_PARKING_MODE=DEMO
```

| Chế độ | Nguồn trạng thái | Thao tác |
|---|---|---|
| DEMO | Mock trong trình duyệt, không cần Backend/Wokwi | Click ô để giả lập, UNKNOWN và RESET; refresh tạo phiên mới |
| LIVE | Snapshot FastAPI REST + WebSocket, cảm biến Wokwi qua MQTT | Ô chỉ đọc; gạt công tắc Wokwi để đổi trạng thái; OPEN/CLOSE gửi qua Backend |

Vite đọc biến khi khởi động/build. **Đổi .env.local phải restart Vite; bản production phải build lại.** Biến VITE_* có trong bundle trình duyệt, không dùng chứa mật khẩu/token. Các URL ví dụ trên là cùng máy, không phải địa chỉ máy cá nhân của thành viên nào.

## 7. Chuẩn bị Device/Wokwi

Mở [dự án Wokwi của nhóm](https://wokwi.com/projects/478203397293414401). Dùng bản sao dự án được nhóm cho phép lưu/sửa; không ghi đè dự án của thành viên khác ngoài phạm vi đã thống nhất.

Đối chiếu ba file trong repo với Wokwi:

| File trong repo | Trong Wokwi |
|---|---|
| device/sketch.ino | Thay nội dung sketch.ino bằng toàn bộ code hiện tại |
| device/diagram.json | Đối chiếu/thay diagram.json để đúng dây nối và linh kiện |
| device/libraries.txt | PubSubClient, ESP32Servo, ArduinoJson |

**Sửa file trên máy không tự đồng bộ lên Wokwi online.** Sau khi dán code, bấm Stop → Play để biên dịch/chạy bản mới. Không cần chạy lệnh npm hay Python cho Device.

| Phần cứng mô phỏng | Cấu hình |
|---|---|
| P01/P02/P03/P04 | GPIO13/14/27/26, INPUT_PULLUP, LOW=true/có xe |
| Servo SG90 | PWM GPIO18, OPEN 90°, CLOSE 0° theo firmware |
| Wi-Fi | Wokwi-GUEST, mật khẩu rỗng trong mô phỏng |
| MQTT | broker.hivemq.com, TCP1883 |
| Device ID | esp32-01 |
| Client ID | smartparking-group21-esp32-01-wokwi |
| Debounce | 400ms thời gian mô phỏng |
| Heartbeat/snapshot | Mỗi 10 giây thời gian mô phỏng; bốn ô cũng gửi khi đổi và khi reconnect |
| MQTT socket timeout | mqtt.setSocketTimeout(15) |

Các topic giữ prefix `smartparking/group21/`: `slots/P01/state` đến P04, `device/status`, `gate/command`, `gate/status`. Không đổi topic/broker ở một phía rồi kỳ vọng hai phía vẫn nhận nhau.

### Khi nhiều thành viên cùng thử

**Chỉ chạy một phiên Wokwi cho Device hiện tại trong một lượt demo chung.** Mỗi bản clone đang dùng cùng client ID/device ID/topic; nhiều mô phỏng đồng thời có thể tranh kết nối và trộn dữ liệu. Dùng DEMO để mỗi người thử UI độc lập; phân ca khi thử LIVE. Nhiều Backend cùng đọc có thể hoạt động nhưng để dễ đối chiếu, mỗi lượt nghiệm thu chỉ dùng một Backend điều khiển.

Nếu cần nhiều thiết bị/bãi thử độc lập đồng thời, nhóm phải thiết kế namespace/device/client ID riêng và cấu hình đồng bộ, không thuộc bước cài đặt hiện tại.

## 8. Chạy hằng ngày — không cài lại

### Terminal 1: Backend

Mở terminal tại thư mục gốc repo:

```powershell
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Giữ terminal này chạy. Không thêm `--workers`, không chạy hai Uvicorn cùng cổng. Trong lúc demo nên dùng lệnh ổn định trên, không cần `--reload`.

Mở:

- Health: http://127.0.0.1:8000/health
- Swagger/API: http://127.0.0.1:8000/docs
- Trạng thái: http://127.0.0.1:8000/api/parking/status

GET `/` trả 404 là bình thường vì Backend không chứa trang Dashboard.

### Wokwi: Device

Sau khi Backend chạy, bấm Play Wokwi và mở Serial Monitor 115200. Kỳ vọng thấy Wi-Fi connected, MQTT CONNECTED, SUBSCRIBE OK, heartbeat và bốn SLOT.

Lúc Backend đã subscribe thành công sẽ có `MQTT subscription ready`. Sau đó cần nhận heartbeat và `MQTT slot received` đủ P01–P04. Nếu lỡ baseline đầu, firmware mới sẽ gửi lại định kỳ; không cần restart chỉ để lấy baseline. Gửi lại định kỳ không tạo event trùng khi trạng thái không đổi.

### Terminal 2: Frontend

Mở **terminal mới tại thư mục gốc repo**, không dùng terminal Backend đang chạy:

```powershell
cd frontend
npm run dev -- --port 5173 --strictPort
```

Mở http://127.0.0.1:5173. Kiểm tra nhãn LIVE MODE hoặc DEMO MODE đúng cấu hình.

LIVE sẵn sàng kiểm thử khi báo:

```text
CONNECTED · MQTT: CONNECTED · Device: ONLINE · Đã có baseline 4 ô
```

CONNECTED đầu tiên chỉ là Dashboard↔Backend. MQTT CONNECTED là Backend↔broker. Device ONLINE chứng minh có heartbeat hợp lệ; cần thêm baseline đủ bốn ô để biết trạng thái bãi.

## 9. Kịch bản demo và kiểm thử chức năng

Không suy kết quả vật lý chỉ từ dòng publish `(OK)`. Đối chiếu Serial Wokwi, log Backend, snapshot API và UI.

| Bước | Thao tác | Kỳ vọng |
|---|---|---|
| 1 | Đợi heartbeat/baseline, scene loaded | Đủ bốn ô; Spline 12/12 objects |
| 2 | Cho P01 EMPTY ổn định, gạt sang OCCUPIED | Car_P01 hiện, ô đổi màu, occupied tăng, available giảm, thêm IN |
| 3 | Gạt P01 về EMPTY | Xe ẩn/ô xanh, available tăng, thêm OUT |
| 4 | Gạt đủ bốn ô OCCUPIED | FULL, available=0; chọn ENTRY rồi OPEN bị Backend từ chối PARKING_FULL |
| 5 | Cho ít nhất một ô EMPTY, chọn ENTRY và OPEN | PENDING → CONFIRMED nếu ACK hợp lệ đúng hạn; quan sát servo Wokwi và barrier 3D |
| 6 | Chọn direction rõ rồi CLOSE | MQTT action CLOSE, ACK CLOSED đúng ID; servo/3D về vị trí đóng |
| 7 | FULL rồi thử OPEN EXIT khi Device online, không busy | Không bị chặn chỉ vì FULL; vẫn cần lệnh/ACK hợp lệ |
| 8 | Refresh Dashboard LIVE | REST khôi phục lịch sử/totals từ SQLite, không tạo lượt IN mới do refresh |
| 9 | Stop Wokwi và chờ phát hiện mất tín hiệu | Device OFFLINE/slots UNKNOWN; lịch sử giữ, UNKNOWN không tính là free |
| 10 | Play Wokwi trở lại | Nhận baseline thật, không tự gửi lại OPEN cũ, không nhân đôi lượt xe do replay cùng trạng thái |

Cổng và công tắc ô đỗ là hai chức năng riêng. Nút OPEN/CLOSE ở Dashboard điều khiển servo; gạt P01–P04 ở Wokwi mô phỏng cảm biến tại ô. Không tự mở cổng khi gạt công tắc ô đỗ.

Trục barrier 3D hiện được cố định **Y, mở +90° so với góc gốc, đóng về góc gốc** theo yêu cầu người dùng. ENTRY/EXIT là hướng nghiệp vụ, không phải chiều quay 3D. LIVE chỉ xoay theo gate đã được xác nhận; CHƯA XÁC NHẬN hoặc stale không được coi là cổng đã đóng/mở thật.

Lệnh dùng command_id riêng, có PENDING/CONFIRMED/ERROR/TIMEOUT. Không tự phát lại sau timeout/restart. Retry cùng ID trả record cũ hoặc được xử lý đúng chính sách idempotency; lệnh TIMEOUT không tự chạy lại chỉ vì nhấn lại cùng ID. Trước một ý định mới cần biết trạng thái thực của servo.

## 10. Chạy tests, build và preview

Từ thư mục gốc, kiểm thử Backend:

```powershell
.\backend\.venv\Scripts\python.exe -m pytest -q .\backend\tests
.\backend\.venv\Scripts\python.exe -m pip check
```

Frontend:

```powershell
cd frontend
npm test
npm run build
npm audit
```

Preview bản production sau khi build:

```powershell
npm run preview -- --host 127.0.0.1 --port 4173 --strictPort
```

Mở http://127.0.0.1:4173. Backend CORS mẫu đã có origin này. Build LIVE vẫn cần Backend/Wokwi để có dữ liệu thật; preview không chạy Backend thay bạn. Thay biến môi trường phải build lại trước preview.

Các bộ tests đã từng chạy PASS: Backend 103 tests; Frontend có số tests tăng theo các bản sửa adapter. Số thực tế trên bản clone phải lấy từ output `npm test`, không bắt buộc một con số cũ. Tests dùng fixtures không thay thế nghiệm thu Wokwi/servo.

Warning bundle Spline >500kB là cảnh báo dung lượng, không tự đồng nghĩa build FAIL. Warning deprecation TestClient/httpx đã được quan sát trong Backend tests; đọc dòng tổng kết PASS/FAIL và lỗi thực tế, không tắt warning để giả kết quả đạt.

## 11. Dừng, chạy lại và cập nhật source

- Dừng Vite: Ctrl+C tại terminal Frontend.
- Dừng Backend: Ctrl+C tại terminal Backend.
- Dừng Device: Stop trên Wokwi.
- Khi chỉ đổi `.env.local`: restart Vite. Khi đổi `backend/.env`: restart Backend. Khi đổi firmware: dán code mới sang Wokwi rồi Stop/Play.
- Không restart thủ công sau mỗi lần gạt công tắc. Firmware tự reconnect khi mạng rớt, nhưng lặp reconnect liên tục vẫn là vấn đề cần chẩn đoán.

Khi nhóm thông báo đã có bản cập nhật GitHub, kiểm tra thay đổi cá nhân trước:

```powershell
git status
git pull --ff-only
```

Nếu có conflict/local edits, dừng để đối chiếu, không dùng reset --hard để ép chạy. Nếu Backend lock thay đổi, chạy lại pip install -r requirements-lock.txt trong venv; nếu package-lock thay đổi, dừng Vite và chạy npm ci. Tự đối chiếu `.env.example` mới với file env cá nhân; không ghi đè toàn bộ env đã cấu hình.

## 12. Xử lý lỗi thường gặp

| Lỗi/hiện tượng | Kiểm tra và xử lý |
|---|---|
| Thiếu backend/app hoặc liveParkingService sau clone | Source bàn giao trên nhánh chưa đầy đủ; hỏi chủ repo, không cài lại dependency để tìm code |
| Không tìm thấy npm/python/git | Cài công cụ và mở terminal mới; kiểm tra PATH/phiên bản |
| PowerShell chặn npm.ps1 | Dùng npm.cmd thay npm, ví dụ `npm.cmd ci`; không cần đổi execution policy để chạy Backend trực tiếp |
| Port 5173 already in use | Tìm terminal Vite cũ và Ctrl+C hoặc dùng lại Dashboard đã mở; chỉ một Vite. Không mở thêm vô hạn hoặc đổi port rồi quên CORS |
| Port 8000 already in use | Backend cũ còn chạy; dừng đúng terminal/tiến trình, không dừng toàn bộ Python trên máy |
| Chưa biết tiến trình chiếm cổng | Chạy `Get-NetTCPConnection -LocalPort 5173 -State Listen`, xem OwningProcess, đối chiếu `Get-Process -Id <PID>`; chỉ dừng tiến trình đã xác định đúng |
| CORS/WS Origin rejected | Dùng 127.0.0.1:5173 hoặc localhost:5173 đúng allowlist. Nếu đổi origin, cập nhật Backend CORS và restart Backend |
| UI vẫn DEMO | Kiểm tra `.env.local`, adapter đã có, mode LIVE và restart Vite |
| CONNECTED nhưng Device OFFLINE | Dashboard đang nối Backend, không chứng minh Device nối broker. Xem heartbeat/Will/timeout và Serial Wokwi |
| ONLINE nhưng chưa có baseline | Backend thiếu một/vài ô trong phiên hiện tại; chờ snapshot định kỳ và kiểm tra `MQTT slot received` đủ bốn ô |
| Gạt công tắc nhưng UI không đổi | Kiểm tra `[SENSOR]` → `[SLOT ... OK]` ở Wokwi → `MQTT slot received` ở BE → snapshot REST → WS/UI để khoanh đúng chặng |
| Wokwi state=-4 | MQTT connection timeout; kiểm tra socket timeout=15, mạng/broker và chỉ một mô phỏng. `(OK)` ở publish không bảo đảm subscriber đã nhận |
| Keep alive timeout/Not authorized | Có thể Backend↔broker cũng đang lỗi. Thu log hai phía, thử MQTTX có kiểm soát; chưa đủ bằng chứng để quy hoàn toàn cho Wokwi hoặc tự đổi credentials/broker |
| MQTT Connecting/CONNECTED lặp | Kết nối đang rớt/reconnect. Snapshot định kỳ không yêu cầu reconnect; kiểm tra mạng và phiên Wokwi trùng client ID |
| Gate PARKING_FULL | ENTRY OPEN bị chặn đúng chính sách khi đủ bốn OCCUPIED; không bỏ Backend check |
| Gate CHƯA XÁC NHẬN/ACK_TIMEOUT | Đối chiếu cùng command_id và thời gian ACK; ACK sau timeout chỉ được audit theo chính sách hiện có, không giả thành công. Kiểm tra ACK timeout trong .env đã là 15 |
| GET commands/{id} lặp 404 | Lệnh có thể chưa được lưu; dùng bản adapter đã sửa dừng polling 404. Không xóa SQLite hoặc tạo nhiều ý định OPEN để thoát UI |
| Servo có ACK nhưng chưa thấy quay | Quan sát servo riêng; ACK là xác nhận phần mềm, không phải cảm biến góc |
| Scene trắng/loading | Kiểm tra WebGL, mạng, scene public và Console; chờ Runtime tải. Không kết luận tên object sai khi scene chưa tải |

## 13. Checklist chủ repo trước khi gửi link clone

Chỉ thực hiện commit/push khi người phụ trách đã cho phép. Hướng dẫn này không tự thực hiện các thao tác đó.

- Đủ source Backend, tests, requirements-lock và `.env.example`.
- Đủ adapter LIVE, UI cố định Y, các bản sửa lỗi đã được thống nhất và tests Frontend.
- Firmware có socket timeout 15 và gửi lại baseline bốn ô theo heartbeat.
- `.env.example` Backend cần được nhóm đồng bộ ACK timeout demo 15 hoặc giữ ghi chú rõ; cấu hình runtime cá nhân không tự đi theo clone.
- Có tài liệu này trong docs/ và link từ README khi nhóm cập nhật README.
- Rà danh sách Git thực tế: `git status --short`, `git ls-files backend/app frontend/src/services backend/requirements-lock.txt backend/.env.example frontend/.env.example`.
- Không đưa node_modules/, dist/, .venv/, .env/.env.local, SQLite, bản backup cấu hình hoặc secrets vào Git. `.gitignore` không tự bỏ các file đã từng tracked.
- Thành viên nhận đúng nhánh/commit đã bàn giao và kiểm tra đủ file trước cài.

## 14. Giới hạn và ghi nhận kiểm thử

Ngày 19/10/2026, người dùng xác nhận đã test được sau các điều chỉnh. Không tự suy ra đã PASS toàn bộ OPEN/CLOSE/FULL/offline/reconnect trên mọi máy; mỗi thành viên cần lưu kết quả thực tế của kịch bản mình chạy.

Broker công cộng và QoS0 có thể mất bản tin; gửi snapshot định kỳ giúp khôi phục trạng thái cuối, không khôi phục được mọi lượt xe đã mất khi offline. Thời gian Wokwi là thời gian mô phỏng, có thể lệch thời gian thực mà Backend dùng cho timeout. Một Backend worker, một servo mô phỏng, chưa có chống kẹt/cảm biến phản hồi góc. History full còn giới hạn quy mô và bundle Spline lớn.

Chưa thử fresh clone trên một máy mới trong lượt viết tài liệu này. Hướng dẫn đã được đối chiếu với source/cấu hình hiện có; bước xác nhận bản GitHub đầy đủ vẫn cần chủ repo thực hiện.

## 15. Bảng lệnh ngắn cho mỗi lần demo

| Thứ tự | Nơi chạy | Lệnh/thao tác |
|---|---|---|
| 1 | Terminal tại backend/ | `.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info` |
| 2 | Wokwi | Play một phiên, chờ heartbeat + bốn ô |
| 3 | Terminal mới tại frontend/ | `npm run dev -- --port 5173 --strictPort` |
| 4 | Trình duyệt | http://127.0.0.1:5173 — LIVE, ONLINE, baseline bốn ô |
| 5 | Wokwi/Dashboard | Gạt công tắc ở Wokwi; điều khiển cổng ở Dashboard |

Các lệnh cài venv/pip/npm chỉ cần làm lần đầu hoặc khi dependency thay đổi. Không cần chạy pytest trước mỗi lần bật server.
