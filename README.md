# 🍃 LEAF_AI — Nền Tảng AI Chẩn Đoán Bệnh Cây Trồng (Cà Chua)

> **Slogan:** Sức khỏe cây trồng công nghệ AI — Phát hiện Bệnh cây trồng, Nâng cao chất lượng đầu ra.  
> **Mục tiêu:** Đồng hành cùng nhà nông, bảo vệ mùa màng Việt Nam theo chuẩn quản lý dịch hại tổng hợp (IPM - FAO).

---

## 🏗️ Cấu Trúc Dự Án (All-in-One Repo — Vercel & Hugging Face Ready)

Toàn bộ dự án được tổ chức trong 1 repository duy nhất, phân tách trách nhiệm rõ ràng, sẵn sàng deploy lên **Vercel** cho toàn bộ Web App (Frontend + Backend API) và **Hugging Face** cho AI Model Service:

```text
leafAI/
├── api/                  # Entry serverless cho Vercel (FastAPI) — Vercel yêu cầu nằm ở gốc
│   └── index.py
├── backend/              # Django: dermai/ (settings), Dermal/ (models, API, tri thức bệnh)
│   ├── supabase/         # Cấu hình + migrations Supabase (chạy CLI trong thư mục backend/)
│   ├── manage.py
│   ├── requirements.txt
│   └── build.sh, Procfile, render.yaml, runtime.txt   # Deploy Render (tùy chọn)
├── frontend/             # Web + PWA đa trang (HTML/CSS/JS thuần)
│   ├── index.html, scan.html, library.html, disease.html,
│   │   handbook.html, history.html, assistant.html, about.html
│   └── assets/           # css/, js/ (core, api, pages/*), images/, samples/
├── ml/                   # Mọi thứ về mô hình AI
│   ├── hf-space/         # AI server cho Hugging Face Space (app.py, Dockerfile, tomato_model.pt)
│   └── training/         # Huấn luyện & đẩy mô hình (train.py, upload_to_hf.py, ...)
├── docs/                 # Tài liệu bàn giao (FE-HANDOFF.md)
├── .github/workflows/    # CI: chạy test Django trong backend/
├── vercel.json           # Routing & build Vercel
├── requirements.txt      # Dependencies cho hàm Python trên Vercel
└── README.md
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
cd ml/hf-space
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
