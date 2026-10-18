# Giai đoạn 5 — Frontend LIVE integration

Ngày thực hiện: 18/10/2026 (Asia/Saigon). Trạng thái: **đã triển khai và kiểm thử tại bản staging; chờ áp dụng vào F và nghiệm thu Wokwi end-to-end**.

## Phạm vi và contract

Workspace đích: `F:\HocTap\Nam4\IOT\Project_IOT\SmartParking-Group21`. Bản cập nhật tại `outputs/phase-05/frontend`. Công cụ cấp quyền không trả quyền ghi F trong lượt này; chưa thay source F. Có script áp dụng với đối chiếu SHA-256 và sao lưu.

Đã đọc DATA_CONTRACT.md, integration-contract-v1.md và schema/routes Backend thực tế. Contract v1, D01–D08 đã được người dùng duyệt trong hội thoại; giữ nguyên client command_id, ENTRY/EXIT bắt buộc, PENDING/CONFIRMED/ERROR/TIMEOUT. Tiêu đề DRAFT trong tài liệu giai đoạn 1 là thông tin cũ, không tự sửa contract.

## Thực hiện

- Giữ nguyên mock `parkingService.js`, các trang Tổng quan/Quản lý ô đỗ/Lịch sử/Thống kê và cách dùng useSyncExternalStore. Adapter mới xuất snapshot đồng bộ, bất biến và subscribe như service cũ.
- Chọn DEMO/LIVE bằng VITE_PARKING_MODE. DEMO mặc định, không gọi REST/WS, các thao tác mô phỏng và RESET tiếp tục hoạt động. Không tự chuyển DEMO khi LIVE lỗi.
- LIVE lấy full snapshot REST và WS `/ws/parking`; validate schema, slots, events, metadata và connection. Nhận revision mới trong cùng stream, dữ liệu stream mới thay dataset; không trộn REST/WS khác phiên. Buffer WS trong lúc GET, không để initial WS cũ ghi đè REST mới.
- Reconnect backoff 1–30s; HTTP/handshake timeout 10s; cảnh báo stale và giữ last-known/history. Reconnect lấy lại REST. Metadata trạng thái mạng tách khỏi dữ liệu server.
- KPI/FULL/history/chart tính cùng full snapshot. Không phát lại event vào mock nên refresh/reconnect không tăng lượt xe. Baseline STATUS không đếm IN.
- LIVE khóa ô đỗ, ẩn RESET và UNKNOWN mô phỏng; hiển thị MQTT/device/baseline. Cổng chưa xác nhận có nhãn riêng; không gọi placeholder CLOSED là trạng thái thật.
- Gate API gửi UUID + status + direction; không đổi barrier theo nút bấm/PENDING. Theo dõi ACK qua WS và GET command, hỗ trợ TIMEOUT/ERROR, không tự phát lại. Retry có chủ đích dùng đúng ID/body. Poll khi cần 1.5s. Request chưa rõ kết quả lưu sessionStorage nếu được phép để khôi phục sau refresh; không lưu snapshot thành nguồn dữ liệu chính.
- Scene URL và tên object giữ nguyên. OCCUPIED hiện xe và màu ô hiện có, EMPTY ẩn xe/màu xanh, UNKNOWN màu xám. Giữ trục/chiều/góc quay cũ, không chọn mặc định mới; cổng chưa xác nhận/stale giữ pose cuối, đồng thời UI báo chưa xác nhận. Không chứng minh servo đã quay bằng ACK.
- `.env.example` có URL REST/WS, không có IP máy cá nhân. Không thêm/nâng dependency; package.json/package-lock.json không đổi.

## Kết quả kiểm thử

| Hạng mục | Kết quả | Bằng chứng / giới hạn |
|---|---|---|
| Unit/store tests | PASS 21/21 | 5 tests DEMO cũ + 16 LIVE; phase-05-tests.log |
| DEMO UNKNOWN/RESET UI | PASS | Trình duyệt: UNKNOWN P01 → còn trống 3, unknown 1; RESET → trống 4, history 0 |
| DEMO scene | PASS tải | Runtime báo 12/12 object; chưa dùng điều này để thay nghiệm thu toàn bộ chuyển động LIVE |
| Adapter HTTP/WS thật với Backend fixture riêng | PASS | P01 OCCUPIED→EMPTY, history 1 IN/1 OUT, PENDING→ACK CONFIRMED, gate OPEN, ngắt WS/reconnect, tạo lại phiên đọc; không MQTT/ESP32 thật |
| Adapter đọc Backend đang chạy :8000 | PASS | REST+WS, stream/revision hợp lệ, 6 events, entries=1/exits=1; không gửi command |
| LIVE UI với Backend đang chạy | PASS | Trình duyệt hiển thị LIVE CONNECTED, Device OFFLINE, 4 UNKNOWN, gate chưa xác nhận; không có RESET/nút giả lập |
| Refresh LIVE trong trình duyệt | PASS | Tải lại giữ 6 events và 1 IN/1 OUT từ DB; gate không bị xác nhận giả |
| LIVE scene load | PASS tải | Runtime báo 12/12; xem live-dashboard.png |
| Console | PASS phạm vi đã quan sát | Browser dev logs không có error/warn khi kiểm tra DEMO UNKNOWN/RESET và LIVE/refresh |
| Production build DEMO và LIVE | PASS | phase-05-build-demo.log, phase-05-build-live.log; còn warning chunk Spline >500kB |
| Script áp dụng | PASS trên workspace thử riêng | Apply + SHA-256 đạt; chạy lại preflight báo 0 file cần đổi; F chỉ kiểm tra read-only |
| npm audit online | 0 advisory tại thời điểm chạy | phase-05-audit.json; không coi kết quả offline là bằng chứng đầy đủ |
| Wokwi thay P01 → Dashboard/Spline hiện/ẩn xe | NOT VERIFIED trong Phase 5 | Thiết bị đang OFFLINE khi kiểm tra; không phát MQTT giả vào LIVE |
| Gate OPEN/CLOSE → servo thực tế | NOT VERIFIED trong Phase 5 | Fixture không thay thế quan sát servo |
| Tablet/responsive trực quan | NOT VERIFIED | Giữ media queries sẵn có; đã xem layout desktop, chưa giả lập viewport tablet |

Kiểm thử LIVE bao gồm dữ liệu sai, trùng/đảo revision, stream mới, command và snapshot cùng revision, mất mạng không xóa dữ liệu, timeout handshake, không auto POST lại khi reconnect, retry cùng ID, phục hồi request sau refresh và ACK tới trước response POST không làm lùi trạng thái.

## File thay đổi / bổ sung

| File | Vai trò |
|---|---|
| frontend/src/services/liveParkingService.js | Adapter REST/WS, validation, reconnect, command recovery |
| frontend/src/services/parkingStore.js | Chọn mode, cấu hình URL |
| frontend/src/App.jsx | Dùng adapter, nhãn LIVE/health/gate, khóa mô phỏng, ENTRY/EXIT |
| frontend/src/style.css | Banner kết nối, command, disabled state |
| frontend/tests/liveParkingService.test.js | Bộ tests LIVE |
| frontend/.env.example | Cấu hình mẫu |
| frontend/docs/DATA_CONTRACT.md | Thêm phần adapter đã triển khai, giữ nội dung cũ |
| frontend/README.md | Thêm hướng dẫn DEMO/LIVE |
| docs/phase-05-frontend-live-report.md | Báo cáo này |
| docs/phase-05-manual-test.md và log/ảnh Phase 5 | Hướng dẫn nghiệm thu và bằng chứng |

Không sửa firmware, Backend, MQTT contract, Scene URL hoặc mock service. Không commit/push. Source F chưa thay bởi lượt này; script sẽ chỉ cập nhật frontend/docs được liệt kê, không đụng data/.env/node_modules/dist.

## Tồn tại và nghiệm thu

1. Áp dụng bundle vào F rồi chạy tests/build tại đó, cấu hình `.env.local` LIVE và restart Vite. CORS phải đúng origin frontend; nếu Vite tự nhảy port, cấu hình lại allowlist Backend thay vì dùng wildcard.
2. Chạy Wokwi, chờ heartbeat + baseline bốn ô. Có thể phải restart Device sau Backend mới vì firmware không publish định kỳ từng ô. Không sửa Device trong Phase 5.
3. Thực hiện checklist manual: P01, FULL/ENTRY reject/EXIT, ACK/servo, refresh, reconnect, các ô khác, tablet và Console.
4. Lịch sử full lifetime DB chưa pagination theo contract; tăng dần sẽ tốn bộ nhớ. Bundle Spline vẫn lớn. Không xử lý bằng cách cắt history âm thầm.
5. Broker công cộng không có xác thực nguồn ACK, QoS0 có thể mất gói; các giới hạn Phase 4 còn nguyên. Backend chỉ một worker. Frontend không thể phục hồi sự kiện chưa tới Backend.
6. sessionStorage có thể bị chặn. Khi request đã mất và snapshot không có pending ID, UI không tự tạo/phát lại lệnh. Cần kiểm tra command ID/log để biết kết quả; không kết luận lỗi mạng nghĩa là cổng chưa chạy.

Dừng tại Phase 5, chờ người dùng nghiệm thu. Không tuyên bố Wokwi → UI → servo đã đạt chỉ từ automated tests.
