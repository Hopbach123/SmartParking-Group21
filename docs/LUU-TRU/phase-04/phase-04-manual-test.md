# Kiểm thử thủ công giai đoạn 4 — sau khi áp dụng source vào dự án

Chưa có kết quả quan sát servo trực tiếp trong lượt Codex. Các ca dưới đây bắt đầu ở trạng thái NOT VERIFIED; chỉ ghi PASS khi đã chạy và lưu log/ảnh.

## 1. Áp dụng và khởi động

Dừng Backend cũ. Gói phase-04 chưa tự chép vào ổ F do chưa được cấp quyền ghi. Từ PowerShell gọi apply-phase04.ps1 trong thư mục gói với -Apply theo INSTALL.md, rồi:

```powershell
cd "F:\HocTap\Nam4\IOT\Project_IOT\SmartParking-Group21\backend"
.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.venv\Scripts\python.exe -m pytest -q
.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --log-level info
```

DB v1 được sao lưu trước migration v2. Không xóa DB. Chờ subscription ready rồi chạy/restart Wokwi. Kiểm tra /health có websocket_enabled=true và /api/parking/status có CONNECTED, ONLINE, synchronized=true. Nếu source vẫn phase3 thì POST gate chưa tồn tại, không tiếp tục test cổng.

## 2. Mở hai client WebSocket

Hai Terminal riêng, cùng chạy từ backend/:

```powershell
.venv\Scripts\python.exe tools/watch_ws.py
```

Mỗi client nhận parking.snapshot đầu tiên. Gạt công tắc trên Wokwi, đối chiếu slots, stream_id/revision ở hai cửa sổ. Tắt/mở lại một viewer phải nhận full snapshot hiện tại, đối chiếu GET /api/parking/status. Viewer chỉ đọc, không gửi bất kỳ lệnh cổng nào và không sửa Frontend.

## 3. Mở cổng ENTRY hợp lệ

Đảm bảo có ô trống và bốn ô đáng tin cậy. Chạy Terminal thứ ba:

```powershell
$base='http://127.0.0.1:8000'
Invoke-RestMethod "$base/api/parking/summary"
$id=[guid]::NewGuid().ToString()
$body=@{command_id=$id;status='OPEN';direction='ENTRY'} | ConvertTo-Json -Compress
Invoke-RestMethod "$base/api/parking/gate" -Method Post -ContentType 'application/json' -Body $body
```

Kỳ vọng 202/PENDING, log publish một lần, Device nhận đúng command_id/action/direction; nhận gate/status OPENED thì GET record CONFIRMED:

```powershell
Invoke-RestMethod "$base/api/parking/commands/$id"
```

Hai WS client phải thấy gate.command PENDING trước snapshot, rồi CONFIRMED trước snapshot gate OPEN (mỗi cặp cùng revision). Quan sát trực tiếp servo Wokwi và lưu ảnh/video riêng. CONFIRMED chỉ chứng minh ACK firmware, không tự chứng minh góc cơ khí.

## 4. Đóng cổng

```powershell
$closeId=[guid]::NewGuid().ToString()
$closeBody=@{command_id=$closeId;status='CLOSED';direction='EXIT'} | ConvertTo-Json -Compress
Invoke-RestMethod "$base/api/parking/gate" -Method Post -ContentType 'application/json' -Body $closeBody
Invoke-RestMethod "$base/api/parking/commands/$closeId"
```

Kỳ vọng action MQTT CLOSE, ACK CLOSED, state CONFIRMED và snapshot CLOSED. Quan sát servo đóng trực tiếp; ghi log/ảnh.

## 5. Duplicate không thêm tác dụng phụ

Gửi lại chính $body với cùng $id. Nếu đã terminal: 200 và record cũ; nếu còn chờ: 202/PENDING. Không có lần publish/servo execution thứ hai do retry. Cùng ID nhưng status/direction khác: 409 COMMAND_ID_CONFLICT. Một command đang chờ với ID khác: 409 GATE_BUSY.

## 6. FULL / UNKNOWN / EXIT

- Đặt bốn công tắc OCCUPIED, đợi API summary FULL/free=0. OPEN ENTRY với ID mới phải 409 PARKING_FULL, không publish.
- OPEN EXIT vẫn được chấp nhận khi Device online, broker sẵn sàng và không busy, dù FULL. Có một servo duy nhất; ENTRY/EXIT là nhãn nghiệp vụ, không phải hai cổng vật lý riêng.
- Khi baseline chưa đủ tin cậy, OPEN ENTRY bị chặn. EXIT chỉ bỏ điều kiện FULL/baseline ô, không bỏ kiểm tra kết nối/busy.
- Dừng Wokwi hoặc mất broker: không báo thành công giả. Lệnh không thể gửi trả 503; lệnh đã PENDING không nhận ACK sẽ TIMEOUT, không tự OPEN lại khi reconnect.

Ca timeout được tự động kiểm thử bằng fake clock và fake publisher, không sửa firmware hoặc gửi cảm biến giả lên LIVE để tạo test. Muốn xác minh timeout thực cần môi trường kiểm soát được mất ACK; chưa đánh dấu PASS chỉ từ unit test.

## 7. Bảng bằng chứng

| Ca | Trạng thái ban đầu |
|---|---|
| Hai viewer nhận cùng snapshot/thay đổi thật | NOT VERIFIED |
| OPEN ENTRY → OPENED + servo quan sát mở | NOT VERIFIED |
| CLOSED → CLOSED + servo quan sát đóng | NOT VERIFIED |
| FULL chặn ENTRY, EXIT vẫn được xử lý | NOT VERIFIED |
| Duplicate ID không publish/actuate lại | NOT VERIFIED |
| Timeout/broker loss/reconnect thực | NOT VERIFIED |

Lưu command_id, log Backend và Device, REST record, WS stream/revision và ảnh servo. Không coi phản hồi firmware hoặc local fixture smoke là bằng chứng quan sát servo thực.
