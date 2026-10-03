# 🍃 LEAF_AI — Nền Tảng AI Chẩn Đoán Bệnh Cây Trồng (Cà Chua)

> **Slogan:** Sức khỏe cây trồng công nghệ AI — Phát hiện Bệnh cây trồng, Nâng cao chất lượng đầu ra.  
> **Mục tiêu:** Đồng hành cùng nhà nông, bảo vệ mùa màng Việt Nam theo chuẩn quản lý dịch hại tổng hợp (IPM - FAO).

---

## 🏗️ Cấu Trúc Dự Án (All-in-One Repo — Vercel & Hugging Face Ready)

Toàn bộ dự án được tổ chức trong 1 repository duy nhất, phân tách trách nhiệm rõ ràng, sẵn sàng deploy lên **Vercel** cho toàn bộ Web App (Frontend + Backend API) và **Hugging Face** cho AI Model Service:

```text
leafAI/
├── api/
│   └── index.py               # Vercel Serverless Function entrypoint (@vercel/python WSGI app)
├── vercel.json                # Cấu hình routing & build chuẩn hóa cho Vercel
├── requirements.txt           # Danh mục dependencies tối ưu, siêu nhẹ cho Vercel (< 40MB)
│
├── frontend/                  # Web Frontend Single-Page App (HTML5 + CSS3 + Vanilla JS ES)
│   ├── assets/
│   │   ├── css/style.css      # Giao diện nông nghiệp hiện đại, sạch sẽ, glassmorphism, responsive
│   │   ├── js/
│   │   │   ├── api.js         # REST API Client (Auth, Diagnose, History, Chat, Supabase)
│   │   │   ├── camera.js      # Chụp ảnh trực tiếp từ camera vườn hoặc kéo thả
│   │   │   ├── canvas_render.js # Vẽ Bounding Box & hiển thị bản đồ nhiệt Grad-CAM
│   │   │   ├── core.js        # Layout dùng chung, Auth Modal (Login/Signup), Drawer di động
│   │   │   └── disease_data.js # Tri thức 6 bệnh lá cà chua chuẩn hóa
│   │   └── samples/           # Ảnh mẫu lá bệnh thực tế (Úa sớm, Sương mai, Đốm vi khuẩn...)
│   ├── index.html             # Trang chủ giới thiệu
│   ├── scan.html              # Chẩn đoán lá (YOLOv8 + ResNet-18 Grad-CAM)
│   ├── library.html           # Thư viện bệnh
│   ├── handbook.html          # Cẩm nang IPM (FAO)
│   ├── history.html           # Nhật ký đồng ruộng (đồng bộ máy chủ & xuất CSV)
│   └── assistant.html         # Trợ lý kỹ sư BVTV AI (Google Gemini)
│
├── backend/                   # Python Django REST Backend
│   ├── dermai/                # Settings, URLs, WSGI
│   ├── Dermal/                # REST API Views, Authentication, Database Models, Knowledge Base
│   ├── db.sqlite3             # CSDL hạt giống (tự động sao chép sang /tmp/ khi chạy trên Vercel)
│   └── manage.py              # CLI quản trị Django
│
├── hf_space_leaf_ai/          # Hugging Face Space AI Server (FastAPI + PyTorch + CUDA)
│   ├── app.py                 # FastAPI AI Engine với ResNet-18 + Grad-CAM Heatmap
│   ├── tomato_model.pt        # Trọng số mô hình Deep Learning đã train
│   └── Dockerfile             # Container runtime cho Hugging Face Space
│
└── training/                  # Kịch bản thu thập dữ liệu & huấn luyện mô hình
    ├── train.py               # Script fine-tuning ResNet-18 trên Kaggle PlantVillage
    └── upload_to_hf.py        # Tự động đẩy weights lên Hugging Face Model Hub
```

---

## 🚀 Triển Khai Lên Vercel (Frontend + Backend trong 1 Click)

Dự án đã được cấu hình trọn gói bằng `vercel.json` và `api/index.py`.

### 1. Triển khai bằng Vercel CLI
```bash
npm install -g vercel
vercel
```

### 2. Triển khai qua GitHub
1. Đẩy mã nguồn lên GitHub:
   ```bash
   git add .
   git commit -m "feat: complete LEAF_AI with Vercel deployment & Grad-CAM"
   git push origin main
   ```
2. Mở [Vercel Dashboard](https://vercel.com/new) -> Chọn repository `leafAI`.
3. Trong phần **Environment Variables**, thêm các biến môi trường:
   - `SECRET_KEY`: Khóa bảo mật Django (tùy chọn)
   - `GEMINI_API_KEY`: API Key trợ lý ảo Google Gemini
   - `AI_SERVER_URL`: URL endpoint Hugging Face Space (`https://your-user-leaf-ai.hf.space`)
   - `DATABASE_URL`: URL PostgreSQL nếu muốn dùng Supabase/Neon (mặc định dùng SQLite trong `/tmp`)
4. Bấm **Deploy**. Vercel sẽ tự động build frontend static và backend serverless function!

---

## 💻 Chạy Cục Bộ (Local Development)

### 1. Khởi động AI Server (Tùy chọn nếu muốn chạy Grad-CAM cục bộ)
```bash
cd hf_space_leaf_ai
python -m uvicorn app:app --host 127.0.0.1 --port 8001
```

### 2. Khởi động Django REST Backend
```bash
cd backend
.venv\Scripts\activate      # Windows
python manage.py runserver 127.0.0.1:8000
```

### 3. Mở Frontend
Mở trực tiếp file `frontend/index.html` trên trình duyệt hoặc chạy qua máy chủ tĩnh:
```bash
python -m http.server 3000 --directory frontend
```
Truy cập: `http://localhost:3000/`

---

## 🌟 Các Tính Năng Nổi Bật

1. **Chẩn đoán lá đa mô hình**:
   - Khoanh vùng Bounding Box nhận diện vết bệnh.
   - **Explainable AI (XAI)**: Tích hợp bản đồ nhiệt **Grad-CAM** làm nổi bật các đặc trưng điểm ảnh mà mô hình chú ý khi phân loại bệnh.
   - Hỗ trợ chuyển đổi mượt mà giữa chế độ "Hộp khoanh vùng" và "Bản đồ nhiệt Grad-CAM".
2. **Cảnh báo đồng nhiễm (Co-infection)**: Nhận diện và xếp hạng khi một lá nhiễm từ 2 bệnh trở lên cùng lúc.
3. **Hệ thống xác thực người dùng**:
   - Đăng ký, đăng nhập bảo mật qua REST API.
   - Modal Auth trực quan, cập nhật trạng thái ngay lập tức trên Header và Mobile Menu.
4. **Nhật ký đồng ruộng (Lịch sử quét)**:
   - Tự động lưu trữ lịch sử chẩn đoán vào CSDL.
   - Đồng bộ hóa đa nền tảng, cho phép xóa từng bản ghi hoặc xuất file báo cáo CSV.
5. **Trợ lý kỹ sư Nông nghiệp AI**:
   - Tích hợp Google Gemini với kho tri thức chuyên sâu về 6 bệnh lá cà chua và quy trình IPM (FAO).
