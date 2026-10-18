# API/Realtime hiện có — SmartParking v1

Đối chiếu source Backend hiện tại; cập nhật tài liệu 19/10/2026. Bản API đề xuất cũ lưu tại [LUU-TRU/ke-hoach-cu/api-contract.md](LUU-TRU/ke-hoach-cu/api-contract.md). Các quy tắc wire vẫn theo [integration contract v1](integration-contract-v1.md), không đổi bằng lượt dọn tài liệu này.

Base URL cấu hình bằng env. Ví dụ cùng máy: http://127.0.0.1:8000. Swagger `/docs`, schema `/openapi.json`; GET `/` không phải Dashboard.

| Method/path | Mục đích / response |
|---|---|
| GET /health | Health DB và cờ MQTT/WS |
| GET /api/parking/status | Full snapshot: slots/gate/gate_meta/connection/events/schema_version/source/timestamp/stream_id/revision |
| GET /api/parking/slots | Danh sách P01–P04 và status |
| GET /api/parking/summary | total/occupied/free/unknown/status/full và metadata |
| GET /api/parking/events | Full events và metadata |
| GET /api/parking/statistics | entries/exits/by_slot, scope DATABASE_LIFETIME và metadata |
| POST /api/parking/gate | Nhận ý định cổng có ID/direction, kiểm tra policy, lưu command/publish |
| GET /api/parking/commands/{command_id} | Tra bản ghi PENDING/CONFIRMED/ERROR/TIMEOUT; 404 nếu chưa có |
| WS /ws/parking | parking.snapshot và gate.command; không nhận command từ client qua WS |

**Không có PATCH slot hoặc API RESET dữ liệu LIVE trong v1.** Các đề xuất PATCH trong tài liệu cũ không phải endpoint được triển khai. Thao tác giả lập/reset chỉ ở DEMO.

## Gate request

```json
{"command_id":"client-uuid-001","status":"OPEN","direction":"ENTRY"}
```

Status OPEN/CLOSED; direction ENTRY/EXIT bắt buộc, không ánh xạ từ trục/chiều Spline. Client sinh ID cho ý định mới; retry cùng ID/cùng body không republish. ID trùng khác body bị từ chối. Backend map CLOSED→MQTT CLOSE; ACK OPENED→gate OPEN.

| HTTP | Ý nghĩa |
|---|---|
| 202 | Đã nhận/lưu PENDING, chưa phải xác nhận servo |
| 200 | Trả record đã terminal khi retry cùng ID/body |
| 409 | FULL/unsynchronized/unavailable/busy hoặc ID conflict theo error code |
| 503 | Device/MQTT chưa sẵn sàng hoặc publish lỗi; kiểm tra error code và tra record khi kết quả truyền chưa rõ |
| 422 | Body/schema không hợp lệ |
| 404 | Command chưa có hoặc đường dẫn không tồn tại |

Error envelope `{ "error": { "code": "...", "message": "...", "command_id": "..." } }`. DEVICE_UNAVAILABLE có thể bị từ chối trước lưu command; PUBLISH_FAILED xảy ra sau khi có record. Không coi mọi 503 là cùng một tình huống.

Command record gồm command_id/requested_status/direction/state/created_at/completed_at/error_code. ENTRY OPEN cần dữ liệu đáng tin và còn ô trống; EXIT không bị chặn chỉ vì FULL. Không auto-close vì FULL. ACK đúng ID/target mới xác nhận; timeout và late ACK không tự biến thành thành công.

## WebSocket và nhất quán dữ liệu

Kết nối/reconnect nhận full snapshot. Mỗi commit có revision tăng trong cùng stream; Backend restart đổi stream. `gate.command` có thể trước `parking.snapshot` cùng revision nên client theo dõi riêng loại message, không bỏ snapshot vì đã nhận command cùng revision.

Frontend LIVE dùng snapshot nguyên khối để KPI/history/chart cùng dữ liệu, REST resync khi reconnect và GET command khi cần. Các GET riêng có thể khác revision nếu có cập nhật xen giữa. Không ghép tùy ý totals của revision này với history revision khác.

WS/REST dùng CORS/Origin allowlist. Ví dụ dev http://127.0.0.1:5173 hoặc http://localhost:5173; preview http://127.0.0.1:4173. HTTPS cần WSS. Không mở wildcard để che lỗi origin.

Các ngưỡng timeout runtime theo backend/.env; cấu hình demo đã dùng ACK15s, heartbeat30s. Chỉ thay thời gian chờ không bảo đảm kết nối public broker ổn định. Xem [hướng dẫn setup](BAO-CAO-NHOM/05_HUONG_DAN_SETUP_VA_CHAY_A_Z.md) và [báo cáo nhóm](BAO-CAO-NHOM/00_BAO_CAO_TONG_HOP_NHOM.md).
