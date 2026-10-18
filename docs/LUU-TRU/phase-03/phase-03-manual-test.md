# Kiểm thử thủ công giai đoạn 3 — Wokwi → MQTT → REST/SQLite

**Trạng thái hiện tại: NOT VERIFIED cho luồng điều khiển Wokwi trong lượt triển khai này.** Người dùng đã cung cấp kết quả Device↔MQTTX trước đó; đó chưa phải bằng chứng Device→Backend của giai đoạn 3.

Không publish mẫu bằng MQTTX để giả dữ liệu cảm biến trong chế độ LIVE. Chỉ đổi công tắc thật của mô phỏng Wokwi. Không gửi lệnh cổng trong checklist này.

## 1. Khởi động Backend trước

```powershell
cd "F:\HocTap\Nam4\IOT\Project_IOT\SmartParking-Group21\backend"
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
```

Chờ log `MQTT subscription ready; awaiting heartbeat and four-slot baseline`. Nếu connect fail: kiểm tra DNS/mạng/cổng 1883, giữ log để phân biệt lỗi broker với Device. Không đổi broker/topic nếu chưa thống nhất nhóm.

Mở Terminal thứ hai:

```powershell
$base = 'http://127.0.0.1:8000'
Invoke-RestMethod "$base/health"
Invoke-RestMethod "$base/api/parking/status" | ConvertTo-Json -Depth 8
```

Chưa có Device: slots UNKNOWN, không có mẫu xe tự sinh. mqtt CONNECTED chỉ chứng minh Backend subscribe broker thành công, chưa chứng minh ESP32 online.

## 2. Chạy hoặc restart Wokwi sau subscribe

Dùng dự án https://wokwi.com/projects/478203397293414401 với firmware đã thống nhất. Đợi Wi-Fi/MQTT kết nối và bốn payload khởi tạo. Không sửa source.

```powershell
Invoke-RestMethod "$base/api/parking/status" | ConvertTo-Json -Depth 8
Invoke-RestMethod "$base/api/parking/summary"
```

Kỳ vọng mqtt CONNECTED, device ONLINE và synchronized=true khi đã có đủ bốn ô. Nếu chỉ ONLINE nhưng chưa synchronized: còn thiếu baseline, restart/reconnect Device để republish. Không giả EMPTY cho các ô chưa nhận.

## 3. P01 EMPTY → OCCUPIED → EMPTY

1. Đưa công tắc P01 về trống, giữ trên 400 ms, chờ REST xác nhận EMPTY.
2. Ghi statistics trước thao tác.
3. Gạt P01 sang LOW/có xe, giữ trên 400 ms; kiểm tra REST OCCUPIED, history IN và entries tăng 1 so với trước.
4. Gạt về trống; kiểm tra EMPTY, OUT và exits tăng 1.

```powershell
(Invoke-RestMethod "$base/api/parking/status").slots
Invoke-RestMethod "$base/api/parking/events" | ConvertTo-Json -Depth 8
Invoke-RestMethod "$base/api/parking/statistics" | ConvertTo-Json -Depth 8
```

Baseline UNKNOWN→EMPTY/OCCUPIED không được tính IN/OUT. Thời gian 400 ms là debounce firmware, không phải cam kết độ trễ đầu cuối. Nếu đo độ trễ, ghi phương pháp và số lần thử, không tự điền số đo.

## 4. Kiểm tra P02–P04 và SQLite

Lặp lại từng công tắc; chỉ đúng slot_id trong REST thay đổi. Cả bốn có xe: occupied=4/free=0/FULL. Không thao tác Gate Controller vì chưa triển khai.

Đọc DB ở chế độ read-only theo config thực tế (Terminal đang ở backend/):

```powershell
.venv\Scripts\python.exe -c "import sqlite3; from app.config import Settings; p=Settings.from_env().db_path; c=sqlite3.connect(p.as_uri()+'?mode=ro',uri=True); print(c.execute('SELECT slot_id,status,received_at,session_id FROM parking_slots ORDER BY slot_id').fetchall()); print(c.execute('SELECT type,slot_id,previous,current,timestamp FROM parking_events ORDER BY sequence DESC LIMIT 12').fetchall()); c.close()"
```

received_at/timestamp phải UTC có Z. Khi offline, DB status giữ last-known còn session_id=NULL và REST UNKNOWN — đây là thiết kế, không phải lỗi không cập nhật ô.

## 5. Restart Wokwi / snapshot không nhân đôi

Đặt các ô về trạng thái ổn định (ví dụ cả bốn EMPTY), ghi events count và entries/exits. Restart Wokwi, giữ các công tắc ở cùng trạng thái ban đầu. Đợi ONLINE và đủ baseline. Kỳ vọng không có IN/OUT hoặc event trùng cho cùng last-known. Nếu restart làm công tắc đổi vị trí, có thể có STATUS baseline hợp lệ; không coi đó là duplicate vehicle event.

## 6. Heartbeat timeout

Dừng Wokwi. Nếu có Will offline, REST OFFLINE/UNKNOWN sớm; nếu broker không phát Will ngay, chờ hơn 30 giây từ heartbeat hợp lệ cuối và thêm thời gian xử lý khoảng 0,25 giây. Không cho UNKNOWN thành free. Khởi động lại Wokwi để nhận online và snapshot mới, lịch sử trước vẫn giữ.

Broker loss/reconnect đã có automated tests; kiểm thử thật chỉ thực hiện khi có thể kiểm soát môi trường mà không ngắt công việc khác. Backend phải subscribe lại sáu topic; chờ baseline, không replay thành lượt xe mới.

## 7. Bảng ghi kết quả thực tế

| Ca | Kết quả cần ghi | Trạng thái trước khi người dùng chạy |
|---|---|---|
| P01 EMPTY→OCCUPIED→EMPTY | Log Device/Backend, REST, DB, IN/OUT delta | NOT VERIFIED |
| P02–P04 | Từng slot khớp topic và DB | NOT VERIFIED |
| FULL | Bốn OCCUPIED, free=0 | NOT VERIFIED |
| Wokwi restart | Baseline mới, không đếm trùng | NOT VERIFIED |
| Wokwi dừng/timeout | OFFLINE, UNKNOWN, last-known giữ trong DB | NOT VERIFIED |
| Broker reconnect thật | Resubscribe và baseline | NOT VERIFIED |

Chỉ đổi PASS/FAIL sau quan sát, kèm thời gian/log/ảnh. Không suy ra các ca này PASS từ việc MQTTX từng nhận dữ liệu trước đó, hoặc từ broker connectivity probe.
