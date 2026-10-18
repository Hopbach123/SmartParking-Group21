# Nghiệm thu Frontend LIVE — Phase 5

## Chuẩn bị

1. Áp dụng bundle theo INSTALL.md. Backend Phase 4 đang chạy một worker tại cổng 8000; không thêm fixture vào Backend chính.
2. Trong frontend, chép `.env.example` thành `.env.local` nếu chưa có. Đặt VITE_PARKING_MODE=LIVE, REST URL `http://localhost:8000`, WS URL `ws://localhost:8000/ws/parking` cho kiểm thử cùng máy. Đây là ví dụ, thay bằng hostname triển khai nếu cần.
3. Chạy `npm test`, `npm run build`, `npm run dev -- --port 5173 --strictPort`. Mở URL Vite hiển thị. Backend CORS cần cho đúng origin; HTTPS cần WSS.
4. Mở Wokwi hiện có, chạy mô phỏng. Chờ Device ONLINE, MQTT CONNECTED, baseline đủ bốn ô. Nếu chỉ có heartbeat mà slots còn UNKNOWN, restart Wokwi để gửi snapshot.

## Checklist (ghi PASS/FAIL và log/ảnh thực tế)

| Thao tác | Kỳ vọng |
|---|---|
| DEMO với Backend tắt | UI vẫn chạy; P01 toggle, UNKNOWN, RESET; refresh về phiên demo mới |
| LIVE đang Device OFFLINE | Slots UNKNOWN; 0 còn trống, không có nút RESET/UNKNOWN mô phỏng; cổng chưa xác nhận |
| Wokwi P01 EMPTY→OCCUPIED→EMPTY | Card và KPI đổi; Spline Car_P01 hiện/ẩn, ô đổi màu; history IN/OUT tăng đúng |
| Lặp P02–P04 | Cập nhật đúng từng ID, không ảnh hưởng ô khác |
| Cả bốn OCCUPIED | Còn trống 0, FULL; ENTRY OPEN bị Backend từ chối PARKING_FULL |
| FULL, EXIT OPEN | Không bị chặn chỉ vì FULL; phải Device online và không có lệnh pending |
| Chọn direction rồi OPEN/CLOSE | UUID mới, trạng thái PENDING rồi CONFIRMED hoặc lỗi; gate chỉ đổi sau ACK hợp lệ; quan sát servo riêng |
| Spline barrier | Chọn đúng trục/chiều đã kiểm thử trước đó, không đoán trục mới; OPENED/CLOSED theo ACK mới được xoay |
| Refresh LIVE | Lịch sử/bộ đếm giữ từ SQLite; không tăng IN do baseline; không tự gửi lại lệnh |
| Stop Backend rồi start lại | Banner stale/reconnect; giữ last-known/history; kết nối lại lấy REST, stream mới, không POST lại command |
| Mất thiết bị | Heartbeat timeout/Will → UNKNOWN và gate chưa xác nhận; history giữ |
| Hai cửa sổ trình duyệt | Cùng trạng thái từ Backend; không nhân đôi sự kiện |
| Desktop/tablet | Các tab, cards, direction và gate buttons đọc/bấm được, không tràn ngang; kiểm tra 1440×900, 1024×768, 768×1024 |
| Console | Không có lỗi runtime/CORS/WS; ghi nguyên lỗi nếu có |

Không publish payload giả vào broker LIVE để đánh dấu PASS. ACK firmware không thay thế quan sát servo. Nếu test FULL/UNKNOWN bị từ chối, đó là hành vi cần xác nhận, không bỏ kiểm tra Backend để mở cổng.
