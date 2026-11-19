# Hướng Dẫn Triển Khai Backend Lên Render (Render Deployment Guide)

Dự án đã được cấu hình sẵn 100% để triển khai lên Render theo 2 cách (khuyên dùng **Cách 1 - Blueprint hoặc Docker**):

---

## Cách 1: Tự động qua Docker (Khuyên Dùng - Đơn Giản Nhất)

1. Đăng nhập [https://dashboard.render.com/](https://dashboard.render.com/)
2. Bấm **New +** -> Chọn **Web Service**.
3. Chọn Repository: **`leaf_ai2`**.
4. Cấu hình các mục như sau:
   - **Name**: `leaf-ai-backend` (hoặc tên tùy chọn)
   - **Region**: `Singapore` (tốc độ tối ưu cho người dùng VN)
   - **Environment / Runtime**: **`Docker`**
   - **Dockerfile Path**: `./Dockerfile` (Render tự điền)
   - **Plan**: **`Free`**
5. Các biến môi trường (**Environment Variables**):
   - `APP_ENV`: `production`
   - `FRONTEND_ORIGIN`: `https://hieu0345984559.github.io`
6. Bấm **Deploy Web Service**.

> Render sẽ tự động tải Docker image, cài PyTorch bản CPU siêu nhẹ, nạp model AI và khởi chạy FastAPI.

---

## Cách 2: Triển khai qua Python Runtime (Không dùng Docker)

Nếu bạn chọn **Runtime: Python 3** trên Render:
- **Root Directory**: Để trống (hoặc nhập `backend`)
- **Build Command**: `./render_build.sh` (nếu để trống Root Directory)  
  *Hoặc nếu Root Directory là `backend`:* `./render_build.sh`
- **Start Command**: `python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT` (nếu Root Directory là `backend`)  
  *Hoặc nếu Root Directory để trống:* `sh -c "cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port $PORT"`
- **Environment Variables**:
  - `PYTHON_VERSION`: `3.10.12`
  - `APP_ENV`: `production`
  - `FRONTEND_ORIGIN`: `https://hieu0345984559.github.io`

---

## Kết Nối Với Frontend GitHub Pages
Sau khi Render deploy thành công, bạn sẽ nhận được một đường link dạng:
`https://leaf-ai-backend-xxxx.onrender.com`

Vào GitHub repo `leaf_ai2` -> **Settings** -> **Secrets and variables** -> **Actions** -> tab **Variables**:
- Tạo biến: `VITE_API_BASE_URL`
- Giá trị: `https://leaf-ai-backend-xxxx.onrender.com`
Mỗi khi bạn cập nhật code, Frontend GitHub Pages sẽ tự động liên kết với Backend Render này!
