# TV3 — Bùi Tấn Phước

**MSSV:** 2001230696. **Phụ trách:** Frontend / React / Spline / adapter LIVE.

## Phạm vi và công nghệ

React 18, JavaScript JSX, Vite 6.4.4, Spline Runtime 2.0.93, Recharts, Lucide, CSS, Fetch, WebSocket, Node test runner.

Phân công lấy từ tài liệu nhóm. Nội dung bên dưới đối chiếu source và báo cáo, không phải audit tác giả từng commit hoặc thống kê số giờ làm.

## Bảng công việc thực tế

| Mã | Công việc | Nội dung đã làm | Trạng thái triển khai | Bằng chứng / giới hạn |
|---|---|---|---|---|
| TV3-01 | Giao diện và tab | Tổng quan, quản lý ô, lịch sử, thống kê; điều hướng trong Dashboard. | Đã triển khai | Source App.jsx và xác nhận người dùng trước |
| TV3-02 | KPI/FULL/UNKNOWN | Total/occupied/available/unknown; UNKNOWN không tính free, FULL khi đủ 4 xe. | Đã triển khai | DEMO tests và UI đã xác nhận |
| TV3-03 | Mock DEMO | Service độc lập, click ô/UNKNOWN/RESET, refresh mở phiên mới. | Đã triển khai | 5 tests mock PASS, không phụ thuộc Backend |
| TV3-04 | Store/contract | Snapshot bất biến và ổn định, subscribe/useSyncExternalStore, schema 1.0 và UTC. | Đã triển khai | Tests validator/immutability PASS |
| TV3-05 | History/chart | Bảng IN/OUT/STATUS/GATE, bộ đếm và Recharts theo cùng events. | Đã triển khai | Người dùng xác nhận cập nhật theo thao tác |
| TV3-06 | Scene loading/diagnostics | Scene URL giữ nguyên; 12 object checks, error boundary, loading/error rõ. | Đã triển khai | Scene 12/12 trong bằng chứng Phase 5 |
| TV3-07 | Đồng bộ xe/màu | Car_P01–P04 hiện/ẩn; Slot EMPTY/OCCUPIED/UNKNOWN theo dữ liệu. | Đã triển khai | 5 tình huống DEMO do người dùng xác nhận; không suy mọi vật liệu đã QA |
| TV3-08 | Barrier trục Y | Cố định Y, mở góc gốc +90°, đóng khôi phục gốc; không cộng dồn góc. | Đã triển khai | Source App.jsx đã có; không coi ACK là bằng chứng cơ khí |
| TV3-09 | Mode và env | Giữ DEMO/LIVE, cấu hình REST/WS URL bằng Vite env; LIVE khóa mô phỏng/reset. | Đã triển khai | parkingStore.js/.env.example và UI LIVE |
| TV3-10 | Adapter REST | GET full snapshot, validate data, thay store mà không replay mock events. | Đã triển khai | Tests LIVE và đọc Backend thật ở Phase 5 |
| TV3-11 | Realtime/reconnect | WS envelopes, revision riêng theo loại, stream đổi, stale/backoff/REST resync. | Đã triển khai | Tests đảo/trùng revision và command/snapshot cùng revision |
| TV3-12 | Gate UI | ENTRY/EXIT bắt buộc; UUID, POST Gate API, pending/error/timeout, GET recovery và retry có chủ đích. | Đã triển khai | Tests fixture; servo thực tế chưa đủ biên bản E2E |
| TV3-13 | Refresh và dữ liệu | LIVE refresh lấy lại DB snapshot; history/totals không reset như DEMO, request giữ sessionStorage nếu được phép. | Đã triển khai | Browser refresh/fixture test đã có bằng chứng |
| TV3-14 | Sửa lỗi pending/404 | Đã áp dụng phân biệt DEVICE_UNAVAILABLE và chặn offline; bản dừng polling 404 đã chuẩn bị nhưng chưa có trong source F lúc kiểm tra. | Triển khai một phần | Rà source F xác nhận 503 có, nhánh if(error.http===404) chưa có |
| TV3-15 | Tests/build/audit/docs | 5 tests DEMO đầu; 21 tests trong Phase 5, build DEMO/LIVE và audit online; tài liệu setup và tổng hợp. | Đã triển khai | Không cộng các lần regression thành số tests độc lập; QA tablet còn giới hạn |

## Minh chứng gốc

- [Rp-Tv3_CongNgheSuDung_TienDO.md](minh-chung/TV3/Rp-Tv3_CongNgheSuDung_TienDO.md)
- [phase-05-frontend-live-report.md](minh-chung/TV3/phase-05-frontend-live-report.md)
- [phase-05-tests.log](minh-chung/TV3/phase-05-tests.log)
- [phase-05-build-live.log](minh-chung/TV3/phase-05-build-live.log)

## Công việc phối hợp và ranh giới

Phối hợp TV2 về contract và ACK; phối hợp TV1 quan sát Wokwi/3D. Snapshot định kỳ là thay đổi firmware phối hợp, không phải Frontend giả dữ liệu.

## Chưa kết luận hoàn thành tuyệt đối

Đã triển khai không đồng nghĩa mọi tình huống E2E đã PASS. Người dùng đã xác nhận test được sau điều chỉnh, nhưng chưa có bảng nghiệm thu đầy đủ từng ca, số đo độ trễ/SLA, bằng chứng phần cứng thật hoặc fresh clone trên máy khác. Xem [báo cáo tổng hợp](00_BAO_CAO_TONG_HOP_NHOM.md) và [bảng công việc](04_THONG_KE_CONG_VIEC.md).
