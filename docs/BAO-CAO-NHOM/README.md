# BÁO CÁO CHUNG SMARTPARKING — NHÓM 21

Thư mục này chứa báo cáo công việc **cả ba thành viên**, không phải riêng TV3. Ngày tổng hợp: 19/10/2026.

## Đọc theo thứ tự

| File | Nội dung |
|---|---|
| [00_BAO_CAO_TONG_HOP_NHOM.md](00_BAO_CAO_TONG_HOP_NHOM.md) | Báo cáo chung theo năm chương; công nghệ, kiến trúc, công việc, kết quả, hạn chế |
| [01_TV1_DEVICE.md](01_TV1_DEVICE.md) | Huỳnh Đổ Hoàng Nguyên — 12 nhóm công việc Device |
| [02_TV2_BACKEND.md](02_TV2_BACKEND.md) | Bạch Ngọc Hợp — 18 nhóm công việc Backend |
| [03_TV3_FRONTEND.md](03_TV3_FRONTEND.md) | Bùi Tấn Phước — 15 nhóm công việc Frontend |
| [04_THONG_KE_CONG_VIEC.md](04_THONG_KE_CONG_VIEC.md) | Ma trận 45 nhóm việc, trạng thái, bằng chứng và công việc phối hợp |
| [05_HUONG_DAN_SETUP_VA_CHAY_A_Z.md](05_HUONG_DAN_SETUP_VA_CHAY_A_Z.md) | Cài đặt, clone, cấu hình, lệnh chạy và lỗi thường gặp |
| [minh-chung/README.md](minh-chung/README.md) | Báo cáo/log/ảnh gốc chia TV1, TV2, TV3 và tài liệu chung |

```text
BAO-CAO-NHOM/
  README.md
  00_BAO_CAO_TONG_HOP_NHOM.md
  01_TV1_DEVICE.md
  02_TV2_BACKEND.md
  03_TV3_FRONTEND.md
  04_THONG_KE_CONG_VIEC.md
  05_HUONG_DAN_SETUP_VA_CHAY_A_Z.md
  minh-chung/
    TV1/
    TV2/
    TV3/
    CHUNG/
    manifest.json
    task-inventory.json
```

**45 nhóm việc không phải 45 tests, số giờ, tỷ lệ đóng góp hoặc 100% nghiệm thu.** Có 44 nhóm đã có triển khai theo source và 1 nhóm Frontend mới triển khai một phần (sửa 503 đã có, dừng polling 404 chưa áp dụng tại F lúc kiểm tra). Mức xác nhận runtime/E2E được ghi riêng.

Báo cáo cũ trong minh-chung giữ nguyên như lịch sử; các câu “chưa có Backend/LIVE” hoặc đường dẫn cũ trong đó không thay thế báo cáo tổng hợp hiện tại. Kết quả Phase 2/3/4 là các lần regression chồng nhau, không cộng tổng số tests giữa các Phase.

Bộ này được chuẩn bị tại outputs/group-reports rồi áp dụng vào docs/BAO-CAO-NHOM bằng script tài liệu. Không tự xóa/di chuyển tài liệu cũ, không sửa ứng dụng, cấu hình hoặc Git. Có thể giữ RP-TV3 làm bộ riêng; dùng thư mục này cho báo cáo chung của nhóm.
