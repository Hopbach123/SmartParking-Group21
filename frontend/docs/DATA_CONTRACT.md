# Hợp đồng dữ liệu Smart Parking v1

Đây là đề xuất hợp đồng Frontend để thống nhất với nhóm FastAPI, chưa phải API đang hoạt động. Không triển khai backend trong lượt này.

## Snapshot

```json
{
  "schema_version": "1.0",
  "source": "DEMO",
  "slots": {"P01":"EMPTY","P02":"OCCUPIED","P03":"UNKNOWN","P04":"EMPTY"},
  "gate": "CLOSED",
  "timestamp": "2026-10-18T12:00:00.000Z",
  "events": []
}
```

- slots bắt buộc đúng bốn khóa P01–P04; giá trị EMPTY, OCCUPIED, UNKNOWN.
- gate chỉ OPEN hoặc CLOSED. source hiện là DEMO; source LIVE là hướng mở rộng, chưa được adapter xử lý.
- timestamp là chuỗi ISO 8601 có múi giờ; service xuất UTC Z. UI hiển thị giờ địa phương.
- schema_version hiện chỉ chấp nhận 1.0. validateParkingStatus kiểm tra phần trạng thái, không xác thực toàn bộ events/source; adapter cần kiểm tra sự kiện riêng khi kết nối thật.
- Snapshot, slots và sự kiện của mock service được đóng băng; cập nhật qua hàm service. getParkingStatus trả cùng tham chiếu đến khi dữ liệu thay đổi, tương thích useSyncExternalStore.

## Sự kiện

```json
{"id":"uuid","timestamp":"2026-10-18T12:00:00.000Z","slotId":"P02","type":"IN","previous":"EMPTY","current":"OCCUPIED"}
```

- id duy nhất; lịch sử mới nhất trước. slotId là P01–P04 hoặc GATE cho sự kiện cổng.
- IN: chuyển từ trạng thái khác sang OCCUPIED (kể cả UNKNOWN → OCCUPIED), giữ nguyên hành vi demo hiện có.
- OUT: OCCUPIED → EMPTY. Những thay đổi ô khác là STATUS. Thay đổi cổng là GATE, previous/current dùng OPEN/CLOSED.
- Lặp lại cùng trạng thái không tạo sự kiện hoặc thông báo mới.
- Thống kê entries/exits đếm IN/OUT trong lịch sử phiên; không tương đương số lượt vật lý đã xác thực khi cảm biến từng UNKNOWN.
- RESET xóa lịch sử và bộ đếm, đưa tất cả ô EMPTY, cổng CLOSED, timestamp mới; không tạo sự kiện RESET.
- Không persistence: refresh mở phiên mới. Định nghĩa lịch sử toàn hệ thống và lệnh reset khi chạy thật phải thống nhất với backend, không dùng reset demo để xóa dữ liệu thật.

## Adapter FastAPI dự kiến

1. Giữ subscribe/getParkingStatus làm giao diện store cho React; adapter dùng fetch bất đồng bộ để nhận dữ liệu, kiểm tra rồi thay snapshot và phát thông báo. Không đổi getParkingStatus thành Promise vì useSyncExternalStore cần snapshot đồng bộ.
2. Thống nhất các endpoint dự kiến với backend: GET /api/parking/status, GET /api/parking/events, GET /api/parking/statistics; PATCH /api/parking/slots/{slotId} với {"status":"EMPTY"}; POST /api/parking/gate với {"status":"OPEN"}. Các đường dẫn này chưa tồn tại trong dự án.
3. WebSocket /ws/parking dự kiến gửi snapshot có schema_version; thêm sequence/revision, chống trùng id, bỏ bản tin cũ, reconnect và đồng bộ lại snapshot sau mất mạng.
4. Backend là nguồn xác nhận: gửi lệnh rồi áp dụng trạng thái được xác nhận; phân biệt trạng thái cổng yêu cầu với cảm biến xác nhận khi có phần cứng. Báo lỗi/mất kết nối, không biến lỗi mạng thành EMPTY.
5. Chốt UTC, giới hạn/phân trang lịch sử, mã lỗi, CORS và biến môi trường URL trước khi tích hợp. Không gửi lệnh MQTT từ trình duyệt.


## Giai đoạn 5 — adapter LIVE đã triển khai

Các mục “dự kiến” bên trên được bảo toàn làm lịch sử thiết kế. Contract tích hợp v1 và D01–D08 đã được người dùng duyệt trong hội thoại; file giai đoạn 1 vẫn mang tiêu đề DRAFT cũ, không tự đổi contract.

- `parkingService.js` tiếp tục là mock DEMO, không thay đổi logic.
- `parkingStore.js` chọn service theo `VITE_PARKING_MODE` (DEMO mặc định). `liveParkingService.js` giữ subscribe/getParkingStatus đồng bộ và snapshot bất biến.
- LIVE GET `/api/parking/status`, WS `/ws/parking`. Validate slots, event, gate metadata, health, schema_version, stream_id/revision. Không gọi PATCH slot hoặc RESET.
- Mỗi lần mở/reconnect WS, GET REST rồi áp dụng bản tin WS đã đệm; cùng stream chỉ nhận revision mới hơn. Nếu REST/WS khác stream, reconnect để tránh trộn dataset. Command có revision riêng, không làm mất snapshot cùng revision.
- UI thống kê từ full events của snapshot đang hiển thị; không trộn response statistics/events khác revision. IN/OUT giữ nguyên phân loại do Backend cung cấp, baseline STATUS không tính IN.
- POST `/api/parking/gate` với `{command_id,status,direction}`. UUID do client sinh, direction ENTRY/EXIT bắt buộc, status OPEN/CLOSED. Không thay gate từ trạng thái yêu cầu. Chỉ đồng bộ barrier khi gate_meta.confirmed=true và transport không stale; cổng chưa xác nhận giữ pose cuối và có nhãn rõ.
- PENDING/CONFIRMED/ERROR/TIMEOUT theo contract. GET command khôi phục lệnh bị mất phản hồi. Lưu request chưa giải quyết trong sessionStorage (nếu trình duyệt cho phép); refresh/reconnect chỉ GET, không tự gửi lại. Khi chưa biết kết quả, người dùng có thể retry cùng ID/body; Backend chống trùng.
- Lỗi mạng không đổi slots thành EMPTY, không xóa history, không chuyển DEMO. Gắn stale và reconnect backoff 1–30 giây. HTTP và handshake có timeout 10 giây; poll command 1.5 giây khi cần.
- Không persistence trạng thái frontend LIVE; dữ liệu lấy lại từ SQLite qua REST. Khi sessionStorage bị chặn, vẫn có thể khôi phục pending ID có trong snapshot Backend; không bảo đảm khôi phục ID của request thất lạc trước khi Backend lưu.
- Không thêm dependency. URL REST/WS cấu hình bằng biến Vite; biến được nhúng khi build và phải build/restart lại khi thay.
