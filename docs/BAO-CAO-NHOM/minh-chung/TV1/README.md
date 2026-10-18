# Device — Huỳnh Đổ Hoàng Nguyên

Bốn file nguồn từ SmartParking được sao chép nguyên trạng; README này bổ sung sau đối chiếu SHA-256.

sketch.ino: firmware ESP32, bốn công tắc và SG90; diagram.json: sơ đồ Wokwi; libraries.txt: PubSubClient, ESP32Servo, ArduinoJson; wokwi-project.txt: link mô phỏng.

Mở https://wokwi.com/projects/478203397293414401, đối chiếu ba file sketch/diagram/libraries rồi bấm Play, đọc Serial Monitor 115200. LOW tại GPIO13/14/27/26 là có xe; servo PWM GPIO18. Topics/payload xem ../docs/mqtt-contract.md.

Chưa biên dịch hoặc chạy Wokwi trong lượt tổ chức. Source gốc không có tests/verify_static.py dù báo cáo TV1 nhắc tới. Không tạo test giả hoặc tuyên bố chạy lại 10/10 mục. Báo cáo TV1 được giữ tại ../frontend/docs/Rp-Tv1.md, không di chuyển.
