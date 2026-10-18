# SmartParking — Group 21

**Tài liệu hiện hành:** [Mục lục docs](docs/README.md) · [Báo cáo chung ba thành viên](docs/BAO-CAO-NHOM/README.md) · [Hướng dẫn setup A–Z](docs/BAO-CAO-NHOM/05_HUONG_DAN_SETUP_VA_CHAY_A_Z.md). Phần mô tả tổ chức ban đầu bên dưới có thông tin lịch sử; trạng thái mới xem các tài liệu hiện hành.


Đề tài 21: bãi đỗ xe thông minh. Workspace monorepo được tổ chức bằng sao chép source hiện có; bản gốc được giữ nguyên. Không đổi logic ứng dụng, MQTT topics/payload hoặc Scene URL, không cài/nâng dependencies trong lượt tổ chức.

## Thành viên

| Thành viên | Phụ trách | Module |
|---|---|---|
| Huỳnh Đổ Hoàng Nguyên | ESP32/Wokwi, cảm biến công tắc, SG90, MQTT và đấu nối | device/ |
| Bạch Ngọc Hợp | FastAPI, MQTT Subscriber, SQLite, REST, WebSocket và tích hợp (dự kiến) | backend/ |
| Bùi Tấn Phước | React/Vite, Dashboard, Spline, KPI, lịch sử, thống kê, mock và kiểm thử | frontend/ |

## Kiến trúc dự kiến

```text
ESP32/Wokwi → MQTT Broker → FastAPI → REST/WebSocket → React Dashboard → Spline 3D
                              ↕
                            SQLite
```

Backend chưa có source, do đó luồng trên chưa kết nối end-to-end. Frontend hiện dùng DEMO.

## Cấu trúc thực tế

```text
SmartParking-Group21/
  device/        sketch.ino, diagram.json, libraries.txt, wokwi-project.txt, README.md
  backend/       README.md (chưa có source)
  frontend/      src/, tests/, docs/, package.json, package-lock.json,
                 vite.config.js, index.html, README.md, node_modules/, dist/
  docs/          architecture.md, mqtt-contract.md, api-contract.md,
                 integration-plan.md, progress.md,
                 copy-checksums.csv, copy-summary.json, validation.log
  .gitignore
  README.md
```

Các file bổ sung trong module được bảo toàn dù không liệt kê ở cây rút gọn. node_modules và dist được sao chép vì có sẵn, nhưng được loại khỏi Git. Không tạo tests Device giả khi source chưa có.

## Chạy Device

Mở dự án ghi trong device/wokwi-project.txt: https://wokwi.com/projects/478203397293414401. Đối chiếu sketch.ino, diagram.json, libraries.txt của device/ rồi chạy mô phỏng và kiểm tra Serial Monitor. Xem device/README.md. Lượt này chỉ xác minh JSON và source, không biên dịch hoặc chạy Wokwi.

## Chạy Frontend

```powershell
cd frontend
npm test
npm run dev -- --force
```

Mở URL Terminal hiển thị. Production: npm run build, npm run preview. Dependencies đã được sao chép từ bản đang có; không cài lại trong nhiệm vụ này. Khi clone sang máy chưa có node_modules, cần tự chuẩn bị dependencies theo package-lock.json trước khi chạy.

## Tích hợp và giới hạn

Đọc docs/LUU-TRU/ke-hoach-cu/integration-plan.md và frontend/docs/DATA_CONTRACT.md. Không đổi contract MQTT hiện có; Backend sẽ chuyển occupied boolean sang enum, OPENED sang OPEN, thêm thời gian UTC và xác nhận lệnh bằng command_id.

Các API trong docs là đề xuất, chưa được triển khai. Frontend vẫn chạy mock, reset/refresh xóa dữ liệu phiên. Không coi kiểm thử tĩnh Device là chạy Wokwi thành công. Không có commit, push hoặc git init trong nhiệm vụ này.
