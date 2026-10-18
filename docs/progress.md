# Tiến độ và bàn giao tổ chức workspace

Ngày 18/10/2026. DONE = có bằng chứng cho đúng phạm vi ghi; PARTIAL = đã triển khai nhưng chưa kiểm thử đủ; BLOCKED = lỗi cản trở; TODO = chưa thực hiện. Không suy đoán phần trăm.

## Thành viên

| Thành viên | Module/hạng mục | Trạng thái | Bằng chứng và giới hạn |
|---|---|---|---|
| Huỳnh Đổ Hoàng Nguyên | Firmware, sơ đồ, thư viện, Wokwi link | PARTIAL | Có đủ bốn file; JSON parse đạt, 6 parts/11 connections; chưa biên dịch hoặc chạy Wokwi trong lượt này |
| Bạch Ngọc Hợp | Backend FastAPI/MQTT/SQLite/REST/WS | TODO | Chưa có source; chỉ chuẩn bị backend/README.md |
| Bùi Tấn Phước | Frontend DEMO | DONE trong phạm vi đã xác nhận | Người dùng xác nhận 5 tình huống xe/màu/FULL/barrier/history-statistics; báo cáo tự động trước có UNKNOWN/RESET/refresh/Console/DOM responsive |
| Bùi Tấn Phước | Kiểm tra bản sao Frontend | DONE | npm test 5/5 PASS; npm run build PASS 21.38 giây; không cài hoặc nâng dependencies |
| Nhóm | QA trực quan responsive và UNKNOWN/reset 3D | PARTIAL | Giữ giới hạn theo báo cáo Frontend, không coi DOM là kiểm chứng hình ảnh WebGL |
| Nhóm | Tổ chức monorepo và kiểm tra sao chép | DONE | Manifest SHA-256, số file và dung lượng khớp; source gốc giữ nguyên |
| Nhóm | Tích hợp end-to-end | TODO | Chưa có Backend, chưa nối MQTT vào React |

Báo cáo TV1 hiện có nói đã kiểm tra tĩnh 10/10 nhưng script minh chứng không được cung cấp trong Device. Đây là ghi nhận từ tài liệu, không phải kết quả chạy lại trong lượt này.

## Source gốc và bản sao

| Source | Đường dẫn gốc | Đích | Xác minh lúc sao chép |
|---|---|---|---|
| Device | C:/Users/Admin/Documents/Codex/2026-10-18/SmartParking | device/ | 4/4 file, 12.383 byte, SHA-256 khớp toàn bộ |
| Frontend | ../smart-parking-dashboard-fixed (cùng thư mục outputs với monorepo) | frontend/ | 9.358/9.358 file, 155.367.396 byte, SHA-256 khớp toàn bộ |
| Backend | Chưa cung cấp | backend/ | Chỉ README mới |

Thư mục đích không tồn tại khi bắt đầu: không có file xung đột, không ghi đè source cũ. Robocopy dùng sao chép, không cut/move/delete. Bao gồm cả node_modules và dist sẵn có. Manifest đo trước khi thêm Device README và trước build. Build tạo lại dist; vì vậy hash dist sau build có thể khác, là đầu ra sinh lại. Sau build kiểm tra lại 23 file gốc ngoài node_modules/dist, có 0 sai lệch. Xem copy-summary.json, copy-checksums.csv, validation.log.

Không git init, commit hoặc push. Không thay đổi React component, parkingService, firmware, MQTT topics/payload hay Scene URL. Không npm install hoặc nâng dependency trong lượt tổ chức.

## Tài liệu Frontend được bảo toàn nguyên byte

Giữ nguyên vị trí frontend/docs/ và tên thực tế từ source:

- audit-after.json
- audit-before.json
- build-validation.log
- DATA_CONTRACT.md
- Rp-Tv1.md
- Rp-Tv3_CongNgheSuDung_TienDO.md
- Smart-Parking-Report.md
- test-validation.log

Không di chuyển Rp-Tv1.md mặc dù là tài liệu TV1. Không đổi tên báo cáo theo tên cũ trong lịch sử chat. README Frontend cũng giữ nguyên, kể cả chỗ nhắc đường dẫn báo cáo cũ; báo cáo hiện có thực tế là Rp-Tv3_CongNgheSuDung_TienDO.md.

## File/tài liệu mới

README.md, .gitignore, device/README.md, backend/README.md; docs/architecture.md, mqtt-contract.md, api-contract.md, integration-plan.md, progress.md; copy-checksums.csv, copy-summary.json, validation.log, frontend-test.log, frontend-build.log.

## Cây thư mục thực tế rút gọn

```text
SmartParking-Group21/
├── device/
│   ├── sketch.ino
│   ├── diagram.json
│   ├── libraries.txt
│   ├── wokwi-project.txt
│   └── README.md                 # bổ sung, source không có tests/
├── backend/
│   └── README.md                 # chưa có code
├── frontend/
│   ├── src/
│   ├── docs/                     # nguyên trạng 8 file
│   ├── tests/parkingService.test.js
│   ├── package.json
│   ├── package-lock.json
│   ├── vite.config.js
│   ├── index.html
│   ├── README.md
│   ├── node_modules/             # đã có, không cài lại
│   └── dist/                     # đã build kiểm tra lại
├── docs/                         # tài liệu chung và log mới
├── .gitignore
└── README.md
```

## Chưa có hoặc cần xử lý tiếp

- Device không có tests/verify_static.py được tài liệu nhắc tới; không tạo script thay thế. Device README được bổ sung, không ghi đè file gốc.
- Không có public/ trong Frontend gốc; không tạo thư mục giả. Không có source Backend; không tạo API giả.
- Build Frontend vẫn có cảnh báo chunk trên 500 kB; không tối ưu hoặc sửa logic ngoài phạm vi tổ chức.
- Chốt direction ENTRY/EXIT, chuyển CLOSE/CLOSED và OPENED/OPEN, received_at UTC, timeout UNKNOWN, command_id/ACK và thống kê khi reconnect trước viết Backend.
- TV1 cung cấp kiểm thử chạy Wokwi/MQTT và script còn thiếu; TV2 triển khai Backend theo contract thống nhất; TV3 sau đó thêm adapter REST/WS, giữ mock để demo.
- Sau khi chốt dùng monorepo, mở SmartParking-Group21 trong IDE và chạy tại frontend/. Các source gốc vẫn được giữ nhưng không tự đồng bộ; tránh sửa đồng thời hai bản.
