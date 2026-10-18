# BÁO CÁO CÔNG NGHỆ VÀ TIẾN ĐỘ SMART PARKING

Cập nhật: 18/10/2026. Source làm việc: smart-parking-dashboard-fixed trên ổ C. Không triển khai Backend.

## Công nghệ

React/React DOM 18, JavaScript JSX và ES Modules, Vite 6.4.4 (đã nâng từ 5), plugin React 4, Spline React 4 và Runtime 2.0.93, Recharts 2, Lucide React, CSS media queries. Node.js dùng trong kiểm thử: 24.18.0. Phiên bản khóa chi tiết nằm trong package-lock.json.

## Kết quả người dùng trực tiếp xác nhận

Năm tình huống sau là bằng chứng kiểm thử người dùng, không gắn nhãn tự động:

| Tình huống | Kết quả |
|---|---|
| P01 rời ô | PASS: xe 3D ẩn, ô đổi xanh |
| P02 vào ô | PASS: xe 3D hiện, ô đổi đỏ |
| Bốn ô OCCUPIED | PASS: còn trống = 0, cảnh báo FULL |
| Barrier OPEN/CLOSE | PASS: xoay đúng theo kiểm thử của người dùng |
| Lịch sử và thống kê | PASS: cập nhật theo thao tác |

Không xây dựng lại các chức năng trên. Lỗi node cũ không còn được coi là lỗi đang tái hiện: người dùng đã xác nhận 3D hoạt động, và kiểm thử production dưới đây tải scene thành công.

## Kết quả kiểm thử trong lượt này

Bản production được phục vụ tại localhost:4173 bằng Vite preview sau build.

| Hạng mục | Phương pháp và kết quả |
|---|---|
| UNKNOWN | PASS ở logic và UI: P01 Không xác định; available 4 → 3, unknown = 1; lịch sử EMPTY → UNKNOWN, thống kê IN/OUT không tăng |
| UNKNOWN toàn bãi | PASS unit test: bốn UNKNOWN cho trạng thái bãi UNKNOWN, không tính là ô trống |
| RESET | PASS unit test và UI: bốn EMPTY, cổng CLOSED, lịch sử rỗng, IN/OUT = 0 |
| Refresh có dữ liệu thay đổi | PASS trình duyệt: đặt P01 UNKNOWN, reload, P01 về EMPTY, scene tải lại, 12/12 đối tượng |
| Scene load/reload | PASS trình duyệt production: Scene loaded và 12/12 đối tượng sau reload |
| Console | PASS trong phiên kiểm thử: dev.logs ở mức error/warn trả mảng rỗng sau UNKNOWN, RESET, chuyển trang, refresh; không bảo đảm mọi trình duyệt đều không có lỗi |
| Desktop 1440×900 | PASS kiểm tra DOM bố cục: scrollWidth 1425 ≤ innerWidth 1440 |
| Tablet 768×1024 | PASS kiểm tra DOM: scrollWidth 753 ≤ 768, workspace chuyển một cột khoảng 498px, trang Quản lý ô đỗ hiển thị |
| Chất lượng hình ảnh responsive | PARTIAL: ảnh desktop từ công cụ bị cắt/không khớp vùng nhìn; chụp full-page tablet thất bại. Không tuyên bố QA trực quan hoàn toàn |
| Hợp đồng dữ liệu | PASS unit test: JSON roundtrip, version, bốn ô, trạng thái hợp lệ, timestamp có múi giờ, chặn ID không hợp lệ và sửa snapshot trực tiếp |
| Regression logic | PASS: entry/exit, FULL, cập nhật trùng không thêm sự kiện, bộ đếm nhất quán |
| Production build | PASS: Vite 6.4.4, build 20.11 giây; xem build-validation.log |
| npm audit | PASS ở thời điểm rà soát: 0 vulnerabilities; trước đó 2. Xem audit-before.json và audit-after.json |

Unit tests: 5/5 PASS, 0 fail, chạy bằng npm test, log tại test-validation.log.

Không dùng phép đọc DOM để khẳng định riêng màu vật liệu WebGL hoặc pivot. UNKNOWN/RESET đã kiểm thử trạng thái và UI; màu xám/ẩn xe UNKNOWN và reset chuyển động 3D vẫn cần quan sát trực tiếp để xác nhận đầy đủ.

## Thay đổi trong lượt này

| File | Nội dung |
|---|---|
| src/services/parkingService.js | Chuẩn hóa contract 1.0, constants trạng thái, timestamp, validator, summarizeParking, snapshot immutable; giữ hành vi demo và interface hiện có |
| tests/parkingService.test.js | Năm nhóm kiểm thử UNKNOWN, RESET, phiên mới, contract, regression |
| package.json | Thêm npm test, mặc định dev localhost, nâng Vite 6.4.4 |
| package-lock.json | Khóa dependency sau nâng Vite/esbuild |
| docs/DATA_CONTRACT.md | Snapshot, sự kiện, quy tắc đếm/reset và hướng adapter FastAPI |
| docs/BAO_CAO_CONG_NGHE_VA_TIEN_DO.md | Báo cáo hiện tại, phân biệt nguồn kiểm thử |
| docs/audit-before.json, audit-after.json | Bằng chứng audit trước/sau |
| docs/build-validation.log, test-validation.log | Bằng chứng build và unit test |

Không sửa App.jsx, scene, tên object hoặc thuật toán xoay barrier trong lượt này. dist/ là đầu ra build được tạo lại.

## Vấn đề còn tồn tại

- Bundle Spline lớn, build còn cảnh báo chunk trên 500 kB; chưa tối ưu lại phần đã chạy ổn.
- Recharts 2 thuộc dòng cũ; chưa nâng major vì chưa cần thay đổi biểu đồ đã hoạt động. npm audit không báo lỗ hổng không đồng nghĩa không có mọi rủi ro.
- npm install báo không xóa được một thư mục esbuild cũ do file exe đang được dùng (EPERM); install và build vẫn thành công. Không dừng các tiến trình của người dùng để ép xóa.
- Cần QA trực quan tablet/desktop, màu xám và ẩn xe UNKNOWN, reset 3D. Không có ảnh bằng chứng đáng tin từ công cụ trong lượt này.
- Trục/chiều barrier chọn trong phiên; refresh về chưa chọn trục. Người dùng đã kiểm thử xoay đúng, nhưng chưa cung cấp trục/chiều để cố định cấu hình. Không đoán hoặc thay đổi thiết lập này.
- Dữ liệu demo không lưu qua refresh; history chưa phân trang. Không backend, MQTT, database, authentication.

## Hướng tích hợp FastAPI

Xem DATA_CONTRACT.md. Giữ store đồng bộ cho React, thêm adapter fetch/WebSocket; kiểm tra schema trước khi cập nhật, backend xác nhận lệnh cổng, xử lý mất kết nối, thứ tự bản tin và trùng sự kiện. Các endpoint trong tài liệu là đề xuất, chưa gọi API giả. Cần thống nhất cách thống kê khi UNKNOWN và phân biệt trạng thái cổng yêu cầu/thực tế trước khi nối cảm biến.

## Chạy và kiểm tra lại

```powershell
npm install
npm test
npm run build
npm run dev -- --force
```

Mở URL Terminal in ra. Sau nâng Vite cần dừng dev server cũ và chạy lại. Không cần chuyển sang thư mục docs để chạy.

README.md và báo cáo cũ Smart-Parking-Report.md ngoài thư mục dự án cũng được cập nhật để dẫn tới báo cáo hiện hành này.
