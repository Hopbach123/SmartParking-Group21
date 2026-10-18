# Báo cáo giai đoạn 02 — FastAPI Backend Core

Ngày: 18/10/2026. Workspace: F:/HocTap/Nam4/IOT/Project_IOT/SmartParking-Group21.

## 1. Phê duyệt và phạm vi

Người dùng xác nhận trực tiếp: **“Duyệt contract v1, D01–D08; triển khai giai đoạn 2”** trước khi viết Backend. Nội dung contract v1 và các tài liệu giai đoạn 1 không bị thay đổi trong lượt này; tiêu đề DRAFT ở tài liệu cũ là trạng thái lịch sử trước xác nhận, không phải suy đoán đã duyệt từ phía BE. Ghi nhận phê duyệt tại báo cáo này.

Đã triển khai Python FastAPI, SQLite, Parking Service, REST đọc và unit/API tests. Không sửa Device/Frontend, không MQTT, WebSocket, điều khiển cổng, không triển khai giai đoạn 3. Không có dữ liệu ESP32 thực trong tests hay smoke test.

## 2. Cấu trúc bàn giao

```text
backend/
  app/
    __init__.py
    main.py                 app factory, lifespan, CORS, error handling
    config.py               cấu hình theo backend/.env hoặc biến môi trường
    database.py             schema SQLite version 1, transactions
    models/__init__.py      enum trạng thái, danh sách bốn ô
    schemas/__init__.py     Pydantic response models
    routers/
      __init__.py
      parking.py            REST đọc
    services/
      __init__.py
      parking.py            transitions, history, KPI và statistics
  tests/
    __init__.py
    test_core.py
  .env.example
  .gitignore
  pytest.ini
  requirements.txt          direct dependencies đã pin theo bản kiểm thử
  requirements-lock.txt     đầy đủ resolved dependencies
  README.md                 thay README placeholder bằng hướng dẫn Backend Core
  .venv/                    môi trường riêng, không đưa vào Git
```

Công cụ kiểm thử HTTP tạm nằm ngoài source trong thư mục work của phiên; log và HTTP response được lưu trong docs dự án. Không tạo thêm bản sao Backend ở ổ C.

## 3. SQLite và quy tắc nghiệp vụ

Ba bảng: parking_slots, parking_events, gate_commands. Có CHECK enums/slot IDs, khóa chính, UNIQUE event ID và command ID, khóa ngoại event→slot; user_version=1. gate_commands mới là schema lưu trữ, chưa có service lệnh/ACK hoặc endpoint thực thi.

Fresh DB seed đúng bốn ô UNKNOWN, không seed xe hoặc lịch sử giả. Database mặc định backend/data/smartparking.sqlite3. Đường dẫn được tính từ vị trí app/config.py; đường dẫn tương đối trong SMART_PARKING_DB_PATH cũng được giải theo backend/, không theo cwd.

Luật LIVE của service:

- EMPTY→OCCUPIED: IN; OCCUPIED→EMPTY: OUT; UNKNOWN→known hoặc thay đổi khác: STATUS, không tăng lượt xe.
- State không đổi trong cùng session: không event, không thay revision/timestamp.
- UNKNOWN không tính free. FULL khi occupied=4; AVAILABLE khi free>0; nếu không free và chưa đủ occupied thì UNKNOWN.
- Timestamp server UTC có Z; lịch sử mới nhất trước theo sequence DB. Lượt IN/OUT/by_slot lấy từ cùng events, scope DATABASE_LIFETIME.
- Giao dịch ghi dùng BEGIN IMMEDIATE và lock một process; nếu ghi thất bại cả event/state rollback, revision cũng không tăng. Parameter binding, không nối input vào SQL.
- Revision phản ánh commit trong service session hiện tại; stream_id mới sau restart. Chỉ hỗ trợ một Backend worker.

### Phục hồi sau restart và độ tin cậy

SQLite giữ last-known status, timestamp, events và thống kê. Khi service session mới bắt đầu, API trả slot UNKNOWN cho dữ liệu từ session cũ đến khi có xác nhận mới. Điều này bảo toàn dữ liệu nhưng không coi last-known là dữ liệu cảm biến còn đáng tin sau restart. Nhận lại cùng last-known tái xác nhận session mà không thêm event/lượt xe trùng.

Vì không triển khai MQTT ở giai đoạn 2, chỉ fixture trong tests gọi update_slot để xác minh logic; runtime không tự tạo dữ liệu hoặc online. Snapshot dùng source LIVE theo model Backend v1, nhưng connection luôn DISCONNECTED/UNKNOWN/synchronized=false. Đây là mô tả nguồn store, không phải bằng chứng tích hợp ESP32.

Gate luôn CLOSED placeholder với gate_meta.confirmed=false và không có lệnh pending; không được hiểu là cổng vật lý đã đóng. Trạng thái nhận ACK sẽ được làm trong giai đoạn khác.

## 4. REST đã thực hiện

| API | Trả về | Kết quả |
|---|---|---|
| GET /health | status/database ok, phase BACKEND_CORE, MQTT/WS disabled | PASS |
| GET /api/parking/status | Snapshot v1 có schema_version/source/slots/gate_meta/connection/events/stream_id/revision/timestamp | PASS |
| GET /api/parking/events | schema_version/stream_id/revision/events | PASS |
| GET /api/parking/statistics | scope/entries/exits/by_slot và metadata | PASS |
| GET /api/parking/slots | Danh sách slot và trạng thái | PASS |
| GET /api/parking/summary | total/occupied/free/unknown/status/full | PASS |
| GET /openapi.json | Schema OpenAPI tự sinh | PASS |

Ba API status/events/statistics giữ hình dạng v1. Health, slots và summary là view đọc bổ sung theo nhiệm vụ giai đoạn 2; không thay thế contract. by_slot là map slot→số IN; scope=DATABASE_LIFETIME.

Các endpoint gate/command, PATCH slot và WebSocket trong kế hoạch tổng thể chưa triển khai. Không trả thành công giả cho thao tác cổng; không expose route ghi fixture. Không sửa contract MQTT hoặc Scene URL.

Các GET riêng có thể khác revision nếu có commit xen kẽ; consumer cần lấy /status để có snapshot nguyên khối. Schema validation và OpenAPI được kiểm tra bằng HTTP client.

## 5. Kết quả kiểm thử thực tế

Môi trường: Python 3.11 trong backend/.venv; FastAPI 0.145.0, Pydantic 2.14.1, Uvicorn 0.54.0, pytest 9.1.1, httpx 0.28.1. Phiên bản đầy đủ trong requirements-lock.txt.

Lệnh:

```powershell
.venv\Scripts\python.exe -m pytest -q --junitxml=../docs/phase-02-pytest.xml
.venv\Scripts\python.exe -m pip check
```

**24 passed, 0 failed, 1 warning; 2.48 giây.** pip check: No broken requirements found. Python compileall cho app/tests thành công.

| Nhóm kiểm thử | Phương pháp / bằng chứng | Kết quả |
|---|---|---|
| Khởi tạo DB | Idempotent, đúng ba bảng/bốn ô, version schema | PASS |
| Trạng thái và UTC | EMPTY→OCCUPIED→EMPTY, history/status/timestamp | PASS |
| Không trùng | Cập nhật giống nhau không đổi snapshot; 24 cập nhật đồng thời chỉ một IN | PASS |
| FULL / UNKNOWN | Bốn OCCUPIED, chuyển UNKNOWN không tăng free, AVAILABLE khi có EMPTY | PASS |
| UNKNOWN→known | STATUS, không tăng IN/OUT | PASS |
| Invalid input | Slot/status ngoài contract, không mutation | PASS |
| SQLite constraints/rollback | Chặn FREE; trigger lỗi fixture rollback event+state+revision | PASS |
| Restart | App/service mới trên DB cũ giữ history/last-known/totals; API UNKNOWN đến xác nhận mới | PASS |
| Response schemas | Sáu REST response validate Pydantic | PASS |
| Consistency | Snapshot/events/statistics cùng revision khi không có commit xen kẽ | PASS |
| CORS | Origin allowlist được trả header, origin ngoài không được trả header | PASS |
| Đường dẫn SQLite | Đổi cwd không đổi db path tương đối | PASS |

### Kiểm tra tiến trình server thật

Đã khởi động Uvicorn thật bằng app-dir tuyệt đối, cwd ở ngoài backend, host 127.0.0.1, port 18021. Dùng HTTP client gọi health, status, slots, summary, events, statistics và OpenAPI: **7/7 HTTP 200**. Fresh DB kiểm tra unknown=4, free=0, gate chưa confirmed. Không nạp sample xe, không gửi MQTT. Server đã dừng sau test; smoke DB tạm đã được dọn.

Không coi HTTP/TestClient hoặc fixture là tích hợp Device. Không chạy test mạng MQTT/Wokwi, không mở WebSocket, không chỉnh Frontend để gọi REST.

## 6. Log và kiểm tra bảo toàn

- docs/phase-02-pytest.log: kết quả pytest.
- docs/phase-02-pytest.xml: JUnit machine-readable.
- docs/phase-02-http-smoke.json: HTTP response từ server thật.
- docs/phase-02-uvicorn.log: startup và request log.
- docs/phase-02-protected-checksums.json: SHA-256 trước/sau cho 5 file Device và 5 file frontend/src, **10/10 không thay đổi**. Không ghi bất kỳ file frontend/ nào; package/config Frontend cũng không bị chỉnh bởi nhiệm vụ.

## 7. Vấn đề và giới hạn còn lại

1. Starlette TestClient phát một cảnh báo deprecation về httpx, đề nghị httpx2 ở phiên bản tương lai. Tests hiện PASS; không tắt cảnh báo hoặc coi là lỗi ứng dụng. Không đổi stack chỉ để che cảnh báo.
2. Chưa MQTT/WS, stale timer, gate commands/ACK, FULL policy execution, auth hoặc live adapter. Các quyết định D01–D08 đã duyệt nhưng phần liên quan các giai đoạn sau chưa được triển khai.
3. SQLite schema version 1 chỉ phục vụ khởi tạo hiện tại; migration nâng schema sau này cần bổ sung. Không nhận file DB của ứng dụng khác làm đầu vào.
4. Lịch sử full dataset chưa pagination và chỉ phù hợp MVP demo. Một process/worker; không chạy nhiều workers với session/revision độc lập.
5. Phục hồi last-known không đồng nghĩa giữ trạng thái công khai tin cậy qua restart. Khôi phục snapshot LIVE cần tín hiệu mới theo contract; giai đoạn này không có consumer thực.
6. Chưa đánh giá bảo mật dependency bằng scanner riêng; pip check chỉ chứng minh tương thích requirements, không chứng minh không có lỗ hổng.

## 8. Chạy local

```powershell
cd "F:\HocTap\Nam4\IOT\Project_IOT\SmartParking-Group21\backend"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Mở http://127.0.0.1:8000/docs. Khi chuyển máy, tạo lại venv và cài requirements-lock.txt như README; không chép venv. Không cần activate. .env.example có DB path/origins, không có credentials.

## 9. Điểm dừng

Backend Core giai đoạn 2 hoàn thành trong phạm vi SQLite/service/REST đã kiểm thử. Chưa tích hợp hệ thống thật. Dừng sau báo cáo này; không tự chuyển giai đoạn 3, không commit/push trong lượt này.
