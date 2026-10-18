# Smart Parking Dashboard

React + Vite, mock data, Spline 3D. Source cập nhật: smart-parking-dashboard-fixed.

Chạy: npm install, npm run dev. Kiểm thử: npm test. Production: npm run build rồi npm run preview.

Xem docs/BAO_CAO_CONG_NGHE_VA_TIEN_DO.md để biết kết quả người dùng xác nhận và kiểm thử tự động. Hợp đồng chuẩn bị FastAPI tại docs/DATA_CONTRACT.md. Không có backend trong giai đoạn này.


## Phase 5 — DEMO / LIVE

Chép `.env.example` thành `.env.local`. Mặc định DEMO, không gọi Backend. LIVE đặt:

```dotenv
VITE_PARKING_MODE=LIVE
VITE_BACKEND_REST_URL=http://localhost:8000
VITE_BACKEND_WS_URL=ws://localhost:8000/ws/parking
```

Các URL trên là ví dụ localhost, không có IP máy cá nhân trong source. Nếu bỏ URL, dùng cùng origin (cần reverse proxy chuyển REST và WS tới FastAPI). HTTPS cần HTTPS/WSS tương ứng, tránh mixed content.

Chạy `npm test`, `npm run dev -- --port 5173 --strictPort`; build `npm run build` và preview. Khi chuyển mode hoặc URL phải restart Vite; bản production cần build lại. Backend CORS phải cho phép chính xác origin frontend; localhost và 127.0.0.1 là hai origin khác nhau. Không mở wildcard. Cấu hình Backend hiện có cho 127.0.0.1:5173, localhost:5173 và 127.0.0.1:4173.

LIVE chỉ đọc ô đỗ, không RESET/UNKNOWN mô phỏng. Chọn ENTRY/EXIT trước khi gửi lệnh cổng. Chỉ phản hồi firmware tương ứng command_id mới xác nhận gate; cần quan sát servo để nghiệm thu phần cứng. Trục/chiều Spline giữ lựa chọn hiện tại, không tự suy đoán trục.

Xem `docs/DATA_CONTRACT.md` và báo cáo `../docs/LUU-TRU/phase-05/phase-05-frontend-live-report.md`.


## Tài liệu hiện hành

Xem [mục lục docs](../docs/README.md) và [báo cáo chung cả ba thành viên](../docs/BAO-CAO-NHOM/README.md). Các báo cáo Phase là tài liệu lịch sử, nay lưu dưới docs/LUU-TRU/.
