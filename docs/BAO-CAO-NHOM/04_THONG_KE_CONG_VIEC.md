# Thống kê công việc cả ba thành viên

Ngày 19/10/2026. Mỗi dòng là **một nhóm công việc**, không phải giờ làm hoặc tỷ lệ đóng góp. Số lượng nhóm không dùng để đánh giá ai đóng góp nhiều hơn. Phân công theo tài liệu nhóm; chưa đối chiếu tác giả từng commit.

## Tổng hợp theo module

| Thành viên | Nhóm công việc | Đã triển khai theo source | Triển khai một phần | Kết quả kiểm thử / lưu ý |
|---|---|---|---|---|
| Huỳnh Đổ Hoàng Nguyên (TV1) | 12 | 12 | 0 | Có source và log chạy; không đánh đồng tất cả firmware branch đã test thực. |
| Bạch Ngọc Hợp (TV2) | 18 | 18 | 0 | 103 Backend tests PASS tại Phase 4, có cả fixture; E2E riêng. |
| Bùi Tấn Phước (TV3) | 15 | 14 | 1 | Log Phase 5 21 tests PASS; bản sửa 404 chưa áp dụng F. |
| **Tổng** | **45 nhóm** | **44 nhóm** | **1 nhóm** | **Không phải 44/45 ca E2E PASS, không phải % hoàn thành.** |

## Chi tiết 45 nhóm công việc

| Mã | Thành viên | Nhóm công việc | Trạng thái | Minh chứng / ghi chú |
|---|---|---|---|---|
| TV1-01 | Huỳnh Đổ Hoàng Nguyên | Mô hình và đấu nối: ESP32, 4 slide switches, servo SG90; diagram.json có 6 parts và 11 connections. | Đã triển khai | Source và sơ đồ hiện có; chưa nghiệm thu phần cứng thật |
| TV1-02 | Huỳnh Đổ Hoàng Nguyên | Ánh xạ GPIO: P01–P04 = 13/14/27/26; servo PWM = 18; V+ 5V và GND. | Đã triển khai | Đối chiếu diagram.json với SENSOR_PINS/SERVO_PIN |
| TV1-03 | Huỳnh Đổ Hoàng Nguyên | Đọc trạng thái ô: INPUT_PULLUP; LOW → occupied=true, còn lại false. | Đã triển khai | Log người dùng có trạng thái P01–P04 |
| TV1-04 | Huỳnh Đổ Hoàng Nguyên | Chống dội công tắc: Debounce 400ms, cập nhật occupied và slotDirty khi giá trị ổn định thay đổi. | Đã triển khai | Log SENSOR P02/P03 do người dùng cung cấp |
| TV1-05 | Huỳnh Đổ Hoàng Nguyên | Kết nối Wi-Fi: Wokwi-GUEST, retry theo RETRY_MS; không block bằng vòng chờ vô hạn trong loop. | Đã triển khai | Có log Wi-Fi CONNECTED; không đo SLA |
| TV1-06 | Huỳnh Đổ Hoàng Nguyên | Publish MQTT ô đỗ: JSON device_id/slot_id/occupied boolean, đúng bốn topic; không retained. | Đã triển khai | Có log SLOT OK; publish OK chưa bảo đảm subscriber đã nhận |
| TV1-07 | Huỳnh Đổ Hoàng Nguyên | Heartbeat và Last Will: Heartbeat online/uptime mỗi 10s mô phỏng; Will offline khi kết nối mất. | Đã triển khai | Backend đã nhận heartbeat và OFFLINE trong log |
| TV1-08 | Huỳnh Đổ Hoàng Nguyên | Reconnect và timeout: Tự thử reconnect, subscribe gate/command, đánh dấu gửi lại bốn ô; socket timeout 3→15s. | Đã triển khai | Source đã cập nhật; kết nối public broker còn chập chờn |
| TV1-09 | Huỳnh Đổ Hoàng Nguyên | Snapshot định kỳ: Sau mỗi heartbeat đánh dấu cả bốn ô dirty, gửi lại trạng thái GPIO hiện tại ở loop kế tiếp. | Đã triển khai | Source đã có; người dùng xác nhận test được sau chỉnh sửa |
| TV1-10 | Huỳnh Đổ Hoàng Nguyên | Điều khiển servo: OPEN đặt 90°, CLOSE 0°; processServo chờ 700ms mô phỏng trước xếp ACK. | Đã triển khai | Log OPEN/OPENED có thật; quan sát cơ khí cuối cùng chưa có biên bản |
| TV1-11 | Huỳnh Đổ Hoàng Nguyên | Validate lệnh: Kiểm tra topic, độ dài, JSON, command_id/action/direction, giới hạn ID 80 ký tự. | Đã triển khai | Đối chiếu source; không tự gọi mọi ca Device là đã chạy |
| TV1-12 | Huỳnh Đổ Hoàng Nguyên | Chống trùng/busy và ACK: Nhớ lệnh hoàn tất gần nhất để re-ACK; busy trả ERROR; gửi gate/status qua hàng chờ ACK. | Đã triển khai | Không phải idempotency bền qua restart; chưa đủ test vật lý từng nhánh |
| TV2-01 | Bạch Ngọc Hợp | Audit và contract: Đối chiếu Device/Frontend, lập mapping, v1 và kế hoạch triển khai; contract do người dùng duyệt D01–D08. | Đã triển khai | integration-audit/contract; không tự nhận Backend có quyền phê duyệt |
| TV2-02 | Bạch Ngọc Hợp | App và cấu hình: App factory/lifespan, env, DB path theo backend/, CORS allowlist và lifecycle services. | Đã triển khai | app/main.py, config.py; tests đường dẫn và CORS |
| TV2-03 | Bạch Ngọc Hợp | SQLite schema: parking_slots, parking_events, gate_commands, gate_state, gate_ack_audit; seed 4 UNKNOWN. | Đã triển khai | database.py và core tests |
| TV2-04 | Bạch Ngọc Hợp | Migration/backup: Nâng v1→v2 có backup, giữ dữ liệu/history/sequence, migration transaction. | Đã triển khai | Test migration Phase 4 PASS |
| TV2-05 | Bạch Ngọc Hợp | State/KPI: EMPTY/OCCUPIED/UNKNOWN, available không tính UNKNOWN, FULL chỉ khi 4 OCCUPIED. | Đã triển khai | Core tests PASS |
| TV2-06 | Bạch Ngọc Hợp | Event/dedup: IN EMPTY→OCCUPIED; OUT OCCUPIED→EMPTY; baseline STATUS; không event trùng do replay. | Đã triển khai | Core/MQTT tests PASS |
| TV2-07 | Bạch Ngọc Hợp | Statistics/UTC: Bộ đếm từ full history, timestamp UTC server, phân biệt thời điểm nhận và commit snapshot. | Đã triển khai | Tests schema/consistency/timestamp PASS |
| TV2-08 | Bạch Ngọc Hợp | REST đọc: Health, status, slots, summary, events và statistics; response v1 và OpenAPI. | Đã triển khai | TestClient và HTTP smoke gốc |
| TV2-09 | Bạch Ngọc Hợp | Parser MQTT strict: Validate topic/device/slot mismatch, JSON boolean thật, retained/oversize/malformed reject. | Đã triển khai | 50 MQTT tests trong bộ Phase 3 |
| TV2-10 | Bạch Ngọc Hợp | Subscriber/queue: Paho lifecycle, callback→bounded queue→worker, epoch chống packet cũ, overflow thu hồi trust. | Đã triển khai | MQTT tests; runtime broker còn lỗi ngoài fixture |
| TV2-11 | Bạch Ngọc Hợp | Health/heartbeat: ONLINE/OFFLINE/UNKNOWN, heartbeat timeout 30s, Will và invalidate slot/gate trust. | Đã triển khai | Tests timeout/Will PASS; log runtime có các trạng thái |
| TV2-12 | Bạch Ngọc Hợp | Reconnect/baseline: Resubscribe, chờ baseline mới đủ 4 ô, giữ last-known và không nhân bản lượt xe. | Đã triển khai | Tests reconnect/dedup PASS; phụ thuộc Device republish |
| TV2-13 | Bạch Ngọc Hợp | WebSocket fanout: Initial full snapshot, nhiều client, bounded queues/send timeout, cleanup kết nối. | Đã triển khai | Hai-client, reconnect và 25 vòng đóng/mở test PASS |
| TV2-14 | Bạch Ngọc Hợp | Revision/stream: stream mới sau restart; command trước snapshot cùng revision, REST nguồn resync. | Đã triển khai | Tests thứ tự/schema và HTTP/WS fixture |
| TV2-15 | Bạch Ngọc Hợp | Gate request/persistence: Client command_id bắt buộc; persist PENDING trước publish, fingerprint/idempotency, một in-flight. | Đã triển khai | Tests duplicate/concurrency/conflict PASS |
| TV2-16 | Bạch Ngọc Hợp | Gate policy/publish: FULL/không đáng tin chặn ENTRY OPEN; EXIT không chặn chỉ vì FULL; MQTT QoS0/non-retained. | Đã triển khai | Tests FULL/UNKNOWN/EXIT/offline/publish fail PASS |
| TV2-17 | Bạch Ngọc Hợp | ACK/audit/timeout/restart: Match ID/target, CONFIRMED/ERROR/TIMEOUT, late ACK audit, không tự resend sau restart; env demo ACK=15s. | Đã triển khai | Có ACK thực đến muộn và TIMEOUT; unit PASS không thay servo E2E |
| TV2-18 | Bạch Ngọc Hợp | Tests và hướng dẫn: 24 core + 50 MQTT + 29 realtime/gate = 103 tests ở Phase 4; lockfile, env mẫu, README. | Đã triển khai | Log 103 PASS/1 warning; chưa có security audit Python đầy đủ |
| TV3-01 | Bùi Tấn Phước | Giao diện và tab: Tổng quan, quản lý ô, lịch sử, thống kê; điều hướng trong Dashboard. | Đã triển khai | Source App.jsx và xác nhận người dùng trước |
| TV3-02 | Bùi Tấn Phước | KPI/FULL/UNKNOWN: Total/occupied/available/unknown; UNKNOWN không tính free, FULL khi đủ 4 xe. | Đã triển khai | DEMO tests và UI đã xác nhận |
| TV3-03 | Bùi Tấn Phước | Mock DEMO: Service độc lập, click ô/UNKNOWN/RESET, refresh mở phiên mới. | Đã triển khai | 5 tests mock PASS, không phụ thuộc Backend |
| TV3-04 | Bùi Tấn Phước | Store/contract: Snapshot bất biến và ổn định, subscribe/useSyncExternalStore, schema 1.0 và UTC. | Đã triển khai | Tests validator/immutability PASS |
| TV3-05 | Bùi Tấn Phước | History/chart: Bảng IN/OUT/STATUS/GATE, bộ đếm và Recharts theo cùng events. | Đã triển khai | Người dùng xác nhận cập nhật theo thao tác |
| TV3-06 | Bùi Tấn Phước | Scene loading/diagnostics: Scene URL giữ nguyên; 12 object checks, error boundary, loading/error rõ. | Đã triển khai | Scene 12/12 trong bằng chứng Phase 5 |
| TV3-07 | Bùi Tấn Phước | Đồng bộ xe/màu: Car_P01–P04 hiện/ẩn; Slot EMPTY/OCCUPIED/UNKNOWN theo dữ liệu. | Đã triển khai | 5 tình huống DEMO do người dùng xác nhận; không suy mọi vật liệu đã QA |
| TV3-08 | Bùi Tấn Phước | Barrier trục Y: Cố định Y, mở góc gốc +90°, đóng khôi phục gốc; không cộng dồn góc. | Đã triển khai | Source App.jsx đã có; không coi ACK là bằng chứng cơ khí |
| TV3-09 | Bùi Tấn Phước | Mode và env: Giữ DEMO/LIVE, cấu hình REST/WS URL bằng Vite env; LIVE khóa mô phỏng/reset. | Đã triển khai | parkingStore.js/.env.example và UI LIVE |
| TV3-10 | Bùi Tấn Phước | Adapter REST: GET full snapshot, validate data, thay store mà không replay mock events. | Đã triển khai | Tests LIVE và đọc Backend thật ở Phase 5 |
| TV3-11 | Bùi Tấn Phước | Realtime/reconnect: WS envelopes, revision riêng theo loại, stream đổi, stale/backoff/REST resync. | Đã triển khai | Tests đảo/trùng revision và command/snapshot cùng revision |
| TV3-12 | Bùi Tấn Phước | Gate UI: ENTRY/EXIT bắt buộc; UUID, POST Gate API, pending/error/timeout, GET recovery và retry có chủ đích. | Đã triển khai | Tests fixture; servo thực tế chưa đủ biên bản E2E |
| TV3-13 | Bùi Tấn Phước | Refresh và dữ liệu: LIVE refresh lấy lại DB snapshot; history/totals không reset như DEMO, request giữ sessionStorage nếu được phép. | Đã triển khai | Browser refresh/fixture test đã có bằng chứng |
| TV3-14 | Bùi Tấn Phước | Sửa lỗi pending/404: Đã áp dụng phân biệt DEVICE_UNAVAILABLE và chặn offline; bản dừng polling 404 đã chuẩn bị nhưng chưa có trong source F lúc kiểm tra. | Triển khai một phần | Rà source F xác nhận 503 có, nhánh if(error.http===404) chưa có |
| TV3-15 | Bùi Tấn Phước | Tests/build/audit/docs: 5 tests DEMO đầu; 21 tests trong Phase 5, build DEMO/LIVE và audit online; tài liệu setup và tổng hợp. | Đã triển khai | Không cộng các lần regression thành số tests độc lập; QA tablet còn giới hạn |

## Công việc chung — không tính trùng vào 45 nhóm

| Việc phối hợp | Tình trạng | Ghi chú |
|---|---|---|
| Chốt MQTT/REST/WS contract | Đã có xác nhận người dùng | D01–D08 được duyệt trước Backend Core; tài liệu DRAFT cũ giữ để tra lịch sử |
| Tổ chức monorepo | Đã có workspace | Device/Backend/Frontend/docs, chưa đồng nghĩa GitHub đầy đủ |
| Demo tích hợp và gỡ lỗi | Có log và xác nhận người dùng | Còn thiếu biên bản từng E2E và độ ổn định nhiều phiên |
| Tài liệu báo cáo và setup | Bộ tổng hợp này đã chuẩn bị | Chỉ ghi F khi script tài liệu được áp dụng |
| Bàn giao qua GitHub | Cần kiểm tra/cập nhật | Các source Backend/LIVE từng chưa tracked; không tự commit/push |
| Ảnh/video cuối kỳ và thông tin học phần | Cần bổ sung | Không tạo ảnh giả, số giờ, MSSV hoặc thông tin giảng viên không có nguồn |

## Nhật ký theo mốc công việc

| Mốc | Nội dung | Nguồn kết quả |
|---|---|---|
| Device/MVP ban đầu | ESP32, switch, servo, topic và UI DEMO | Source, Rp-Tv1 và báo cáo TV3 cũ |
| Audit/contract | Mapping và D01–D08 | integration-audit/contract và xác nhận người dùng |
| Phase 2 | Backend Core, SQLite/REST | 24 tests PASS |
| Phase 3 | MQTT/health/baseline | Tổng regression 74 tests PASS, không cộng thêm 24 thành 98 |
| Phase 4 | WS/Gate/ACK/timeout | Tổng regression 103 tests PASS, không cộng 24+74+103 |
| Phase 5 | Frontend LIVE giữ DEMO | Log 21 tests/build DEMO-LIVE, fixture và browser evidence |
| Gỡ lỗi sau tích hợp | ACK 15s, Y/+90°, socket15s, snapshot định kỳ, pending/404 | Phân biệt source đã áp dụng và gói sửa chưa áp dụng |
| 19/10/2026 | Người dùng xác nhận test được, yêu cầu tài liệu chung | Hội thoại, không tự suy PASS mọi ca |

Không có timesheet/nhật ký từng tuần hoặc commit tác giả đầy đủ; không tự dựng lịch làm việc và số giờ.
