# Backend implementation plan — CHƯA TRIỂN KHAI

Ngày 18/10/2026. Điều kiện bắt đầu: người dùng phê duyệt D01–D08 của integration-contract-v1.md. Đây là kế hoạch, không phải code Backend hoặc hướng dẫn chạy server đã tồn tại.

## Phạm vi tối thiểu

FastAPI + MQTT client + SQLite + REST + WebSocket full snapshots. Một process/worker ở MVP để tránh nhiều subscribers, command queues và revisions độc lập. Không sửa firmware hoặc scene; Frontend adapter sẽ là công việc riêng được duyệt.

## Các bước sau phê duyệt

1. Viết schema/fixtures từ contract đã duyệt: slot MQTT strict boolean, ID/topic khớp, command ASCII ≤80 byte, message ≤256 byte, snapshot/events/command/error envelopes. Chốt cấu hình broker, origin CORS, database path, stale/ACK timeout; không hardcode token.
2. Tạo phần config/domain tách khỏi I/O. State machine có baseline UNKNOWN, health broker/device, confirmed gate riêng; không dùng default CLOSED làm bằng chứng cổng đóng. Policy ENTRY/FULL ở Backend, không gán vào firmware hiện có.
3. SQLite migration tối thiểu dự kiến: slot_state(device_id,slot_id,status,received_at,baseline_valid); parking_event(id,device_id,slot_id,type,previous,current,received_at); gate_command(command_id UNIQUE,request_fingerprint,direction,target,state,created_at,completed_at,error_code); gate_state(last_confirmed,confirmed_at,confirmed); metadata/state revision nếu cần. Tên schema cuối phụ thuộc contract duyệt; không tạo database trong giai đoạn 1.
4. MQTT subscriber listen exact topic allowlist, client_id riêng. Callback đưa bản tin vào hàng đợi thread-safe cho một state owner/event loop; không gọi SQLite/WS tùy tiện từ network thread. Validate rồi cập nhật state+event+revision theo transaction, commit trước broadcast. ACK và timeout giải quyết dưới cùng serialization để tránh đua.
5. Bootstrap và reconnect: không giả định broker có retained state. Chưa có bốn slot → synchronized=false. Heartbeat còn sống không chứng minh đã nhận baseline; Backend khởi động giữa lúc Device online có thể phải đợi Device reconnect/restart thủ công. Ghi giới hạn này trong demo, không tự gửi gate command làm probe. Broker loss invalidate trạng thái live nhưng giữ lịch sử.
6. Gate command service: persist PENDING trước publish, một in-flight/device, unique command_id/fingerprint; normalize CLOSED→CLOSE. Chờ ACK khớp, không coi QoS publish là thành công vật lý. ERROR/busy/timeout/late ACK/restart có test riêng. Không retry tự động ngoài contract đã duyệt.
7. REST endpoints đọc đúng transaction snapshot; giữ errors thống nhất kể cả validation 422. Không cung cấp API giả sửa slot hoặc reset dữ liệu thật. Statistics cùng nguồn events, không trộn thời gian/phân trang với biểu đồ Frontend.
8. WS initial/full snapshots có stream_id/revision; subscribers chậm nhận snapshot mới nhất hoặc disconnect có kiểm soát, không tăng RAM vô hạn. Command updates tương quan bằng command_id, có GET fallback. Reconnect full resync, không dùng history replay tạo IN/OUT mới.
9. Adapter Frontend (công việc tiếp theo riêng): giữ subscribe/getParkingStatus sync, xử lý REST/WS async bên ngoài; thêm LIVE mode/direction/pending/error/unknown gate, khóa RESET/mock ở LIVE. Không sửa thuật toán Spline đã chạy tốt nếu không cần. Không đổi màu/Scene URL/topic.

## Kế hoạch kiểm thử dự kiến

| Nhóm | Ca bắt buộc |
|---|---|
| Parser | JSON hỏng, sai kiểu bool/string, ID sai, topic/slot không khớp, command quá dài, status ngoài enum |
| Baseline/UNKNOWN | Boot trước/sau Device, nhận đủ bốn slot, heartbeat không có slot, slot không đổi lâu, heartbeat timeout 30s, Will, broker reconnect |
| Events/statistics | Trùng state, reconnect replay, UNKNOWN→known, FULL/AVAILABLE, không tăng đếm khi bootstrap; cùng phạm vi history và totals |
| Gate | OPEN/CLOSE × ENTRY/EXIT; FULL ENTRY reject; FULL EXIT allowed; busy, ID trùng cùng/khác payload, publish fail, ACK wrong ID/action/device, timeout/late ACK |
| Reliability | Single pending ACK Device có thể bị ghi đè; không retry gate tự động; restart Backend khi command pending; stale ACK sau command mới |
| REST/WS | Initial snapshot, cùng revision, command update cùng revision, GET/WS race, stream restart, CORS đúng origin, client chậm, reconnect |
| E2E | Công tắc → MQTT → DB/REST/WS → UI/Spline, cổng command/ACK, offline/UNKNOWN, refresh không xóa DB |

Unit/integration tests sẽ dùng MQTT/clock/SQLite test doubles trước; thử broker/Wokwi thật chỉ khi được phép và có người quan sát. Không tuyên bố đã chạy các ca này trong giai đoạn audit.

## Deliverables giai đoạn 2 dự kiến

Source Backend, config .env.example không secret, dependency lock đã lựa chọn sau phê duyệt, migration, tests/log, README vận hành và báo cáo đối chiếu contract. Cập nhật tài liệu cũ có kiểm soát sau khi người dùng duyệt v1; không tự thay v1 thành APPROVED.

## Giới hạn phải nêu trong demo

QoS0 mất bản tin có thể mất transition dù heartbeat vẫn ONLINE; không có slot periodic hoặc sequence Device để phục hồi đầy đủ. Gate ACK là xác nhận phần mềm, không phải cảm biến. Public broker không xác thực nguồn. Kiến trúc một servo không có chống kẹt/đếm xe tại cổng. Đây là giới hạn của mô hình học tập, không được giải thích như đã có bảo đảm vận hành thực tế.

## Điểm dừng

GIAI ĐOẠN 1 KẾT THÚC. Chờ người dùng duyệt hoặc sửa D01–D08; không tạo server, database, dependency hoặc sửa Device/Frontend trước xác nhận giai đoạn tiếp theo.
