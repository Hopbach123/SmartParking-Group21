# API contract dự kiến — chưa triển khai

Nguồn: ../frontend/docs/DATA_CONTRACT.md, giữ nguyên tài liệu gốc. Đây là đề xuất để TV2 và TV3 thống nhất, không phải API đang chạy.

| Endpoint dự kiến | Mục đích |
|---|---|
| GET /api/parking/status | Snapshot bốn ô và cổng |
| GET /api/parking/events | Lịch sử, cần chốt phân trang |
| GET /api/parking/statistics | Thống kê từ cùng lịch sử |
| PATCH /api/parking/slots/{slotId} | {"status":"EMPTY"}, chỉ cần cho chế độ mô phỏng có kiểm soát |
| POST /api/parking/gate | {"status":"OPEN"}, cần bổ sung direction/command_id trong thiết kế tích hợp |
| WS /ws/parking | Snapshot/thay đổi có version, sequence/revision cần thống nhất |

Snapshot Frontend hiện có schema_version 1.0, source DEMO, slots P01–P04 nhận EMPTY/OCCUPIED/UNKNOWN, gate OPEN/CLOSED, timestamp ISO có múi giờ, events. Source LIVE là đề xuất, chưa có adapter. Sự kiện dùng id,timestamp,slotId,type,previous,current. Thống kê entries/exits theo IN/OUT.

Không đổi action CLOSE của MQTT thành CLOSED trên đường gửi; adapter phải ánh xạ rõ UI CLOSED → action CLOSE, ACK OPENED → UI OPEN. API cổng hiện chỉ là đề xuất, chưa mang đủ direction bắt buộc ở firmware. Cần chốt request body trước viết Backend.

Cần thống nhất: mã lỗi, CORS, base URL môi trường, ACK timeout/pending/error, revision, reconnect, schema validation toàn bộ events, UTC, reset demo và dữ liệu thật. Không dùng reset Frontend để xóa SQLite.
