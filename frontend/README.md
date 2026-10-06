# 🍃 LEAF_AI — Frontend (v2, đa trang)

Giao diện web/PWA nhận diện bệnh trên lá vải thiều Lục Ngạn. Tông xanh diệp lục, chữ **Be Vietnam Pro**, không còn phụ thuộc Bootstrap CSS/JS (chỉ dùng Bootstrap Icons).

## Cấu trúc trang

| File | Nội dung |
|---|---|
| `index.html` | Landing page: hero có demo quét lá vải kèm Grad-CAM, 5 bệnh, quy trình 3 bước, tháp IPM, thông số mô hình |
| `scan.html` | Chẩn đoán: camera / chọn ảnh / ảnh minh họa, ResNet-18 + bản đồ nhiệt Grad-CAM, kết quả, stepper 5 bước |
| `library.html` | Thư viện 5 bệnh, dịch hại lá vải: tìm kiếm không dấu, lọc nấm / tảo, nhện hại / nghiêm trọng |
| `disease.html?id=<id>` | Chi tiết bệnh: triệu chứng 3 giai đoạn, điều kiện, phòng ngừa, phác đồ 3 cấp |
| `handbook.html` | Cẩm nang: 8 nguyên tắc, 7 bước kiểm tra, 10 bước IPM, an toàn BVTV (mục lục bám cuộn) |
| `history.html` | Nhật ký đồng ruộng: thống kê, lọc, xóa, xuất CSV, ảnh thu nhỏ |
| `assistant.html?q=<câu hỏi>` | Trợ lý kỹ sư AI, có trả lời ngoại tuyến từ kho tri thức |
| `about.html` | Giới thiệu dự án, thông số mô hình, nguồn tham khảo |

`id` bệnh: `anthracnose` (thán thư), `downy_blight` (sương mai), `leaf_blight` (cháy lá), `algal_spot` (đốm rong), `erinose` (nhện lông nhung). Tên lớp mô hình cần trả về: `Healthy`, `Anthracnose`, `Downy_blight`, `Leaf_blight`, `Algal_spot`, `Erinose` (các tên gọi khác khai báo trong `aliases` của `disease_data.js`). Nhãn không thuộc danh mục lá vải sẽ không được hiển thị như một chẩn đoán.

## JavaScript

```
assets/js/
├── core.js           # Header/menu/bottom-nav/footer dùng chung, toast, hộp xác nhận, lưu lịch sử, PWA
├── api.js            # REST client có timeout + kiểm tra backend 1 lần; mô phỏng khi backend tắt
├── disease_data.js   # Kho tri thức bệnh lá vải + cẩm nang vườn vải
├── canvas_render.js  # Vẽ ảnh, bounding box, tia quét
├── camera.js         # Camera trước/sau, kéo thả, kiểm tra file ≤ 10MB
└── pages/*.js        # Mỗi trang một file
```

- Mỗi trang khai báo `<body data-page="...">` và nạp `core.js` **ngay sau thẻ `<body>`** để header hiện ngay, không nháy.
- Chẩn đoán chạy song song hiệu ứng quét và gọi API (`Promise.all`), bỏ qua kết quả cũ nếu người dùng đổi ảnh giữa chừng.
- Khi chưa có backend, kết quả gắn cờ `simulated: true` và giao diện hiển thị rõ “chế độ mô phỏng”.
- `three_leaf.js` (lá 3D) không còn dùng trong giao diện mới, giữ lại để tham khảo.

## Chạy

```bash
python -m http.server 3000 --directory frontend
# http://localhost:3000/
```

Backend Django (cổng 8000) được tự phát hiện qua `/health/`. Đổi địa chỉ backend: `localStorage.setItem('leaf_backend_url', 'https://...')`.

Khi chạy qua Django, trang có ở `/app/` (ví dụ `/app/scan.html`).
