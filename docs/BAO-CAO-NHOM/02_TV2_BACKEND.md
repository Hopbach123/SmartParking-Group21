# TV2 — Bạch Ngọc Hợp

**MSSV:** 2001230279. **Phụ trách:** Backend / tích hợp MQTT / SQLite / REST / WebSocket.

## Phạm vi và công nghệ

Python 3.11, FastAPI, Pydantic, SQLite stdlib, Paho MQTT, Uvicorn, AnyIO, pytest, HTTPX, websockets.

Phân công lấy từ tài liệu nhóm. Nội dung bên dưới đối chiếu source và báo cáo, không phải audit tác giả từng commit hoặc thống kê số giờ làm.

## Bảng công việc thực tế

| Mã | Công việc | Nội dung đã làm | Trạng thái triển khai | Bằng chứng / giới hạn |
|---|---|---|---|---|
| TV2-01 | Audit và contract | Đối chiếu Device/Frontend, lập mapping, v1 và kế hoạch triển khai; contract do người dùng duyệt D01–D08. | Đã triển khai | integration-audit/contract; không tự nhận Backend có quyền phê duyệt |
| TV2-02 | App và cấu hình | App factory/lifespan, env, DB path theo backend/, CORS allowlist và lifecycle services. | Đã triển khai | app/main.py, config.py; tests đường dẫn và CORS |
| TV2-03 | SQLite schema | parking_slots, parking_events, gate_commands, gate_state, gate_ack_audit; seed 4 UNKNOWN. | Đã triển khai | database.py và core tests |
| TV2-04 | Migration/backup | Nâng v1→v2 có backup, giữ dữ liệu/history/sequence, migration transaction. | Đã triển khai | Test migration Phase 4 PASS |
| TV2-05 | State/KPI | EMPTY/OCCUPIED/UNKNOWN, available không tính UNKNOWN, FULL chỉ khi 4 OCCUPIED. | Đã triển khai | Core tests PASS |
| TV2-06 | Event/dedup | IN EMPTY→OCCUPIED; OUT OCCUPIED→EMPTY; baseline STATUS; không event trùng do replay. | Đã triển khai | Core/MQTT tests PASS |
| TV2-07 | Statistics/UTC | Bộ đếm từ full history, timestamp UTC server, phân biệt thời điểm nhận và commit snapshot. | Đã triển khai | Tests schema/consistency/timestamp PASS |
| TV2-08 | REST đọc | Health, status, slots, summary, events và statistics; response v1 và OpenAPI. | Đã triển khai | TestClient và HTTP smoke gốc |
| TV2-09 | Parser MQTT strict | Validate topic/device/slot mismatch, JSON boolean thật, retained/oversize/malformed reject. | Đã triển khai | 50 MQTT tests trong bộ Phase 3 |
| TV2-10 | Subscriber/queue | Paho lifecycle, callback→bounded queue→worker, epoch chống packet cũ, overflow thu hồi trust. | Đã triển khai | MQTT tests; runtime broker còn lỗi ngoài fixture |
| TV2-11 | Health/heartbeat | ONLINE/OFFLINE/UNKNOWN, heartbeat timeout 30s, Will và invalidate slot/gate trust. | Đã triển khai | Tests timeout/Will PASS; log runtime có các trạng thái |
| TV2-12 | Reconnect/baseline | Resubscribe, chờ baseline mới đủ 4 ô, giữ last-known và không nhân bản lượt xe. | Đã triển khai | Tests reconnect/dedup PASS; phụ thuộc Device republish |
| TV2-13 | WebSocket fanout | Initial full snapshot, nhiều client, bounded queues/send timeout, cleanup kết nối. | Đã triển khai | Hai-client, reconnect và 25 vòng đóng/mở test PASS |
| TV2-14 | Revision/stream | stream mới sau restart; command trước snapshot cùng revision, REST nguồn resync. | Đã triển khai | Tests thứ tự/schema và HTTP/WS fixture |
| TV2-15 | Gate request/persistence | Client command_id bắt buộc; persist PENDING trước publish, fingerprint/idempotency, một in-flight. | Đã triển khai | Tests duplicate/concurrency/conflict PASS |
| TV2-16 | Gate policy/publish | FULL/không đáng tin chặn ENTRY OPEN; EXIT không chặn chỉ vì FULL; MQTT QoS0/non-retained. | Đã triển khai | Tests FULL/UNKNOWN/EXIT/offline/publish fail PASS |
| TV2-17 | ACK/audit/timeout/restart | Match ID/target, CONFIRMED/ERROR/TIMEOUT, late ACK audit, không tự resend sau restart; env demo ACK=15s. | Đã triển khai | Có ACK thực đến muộn và TIMEOUT; unit PASS không thay servo E2E |
| TV2-18 | Tests và hướng dẫn | 24 core + 50 MQTT + 29 realtime/gate = 103 tests ở Phase 4; lockfile, env mẫu, README. | Đã triển khai | Log 103 PASS/1 warning; chưa có security audit Python đầy đủ |

## Minh chứng gốc

- [phase-02-backend-core-report.md](minh-chung/TV2/phase-02-backend-core-report.md)
- [phase-03-mqtt-report.md](minh-chung/TV2/phase-03-mqtt-report.md)
- [phase-04-realtime-gate-report.md](minh-chung/TV2/phase-04-realtime-gate-report.md)
- [phase-04-pytest.log](minh-chung/TV2/phase-04-pytest.log)

## Công việc phối hợp và ranh giới

Phối hợp TV1 về trạng thái/heartbeat/gate, phối hợp TV3 về snapshot/command/WS. Không sửa UI để bỏ qua FULL hoặc coi publish là thành công vật lý.

## Chưa kết luận hoàn thành tuyệt đối

Đã triển khai không đồng nghĩa mọi tình huống E2E đã PASS. Người dùng đã xác nhận test được sau điều chỉnh, nhưng chưa có bảng nghiệm thu đầy đủ từng ca, số đo độ trễ/SLA, bằng chứng phần cứng thật hoặc fresh clone trên máy khác. Xem [báo cáo tổng hợp](00_BAO_CAO_TONG_HOP_NHOM.md) và [bảng công việc](04_THONG_KE_CONG_VIEC.md).
