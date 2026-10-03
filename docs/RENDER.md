# 🚀 Hướng dẫn: Triển khai LEAF_AI lên Render

> **Kiến trúc deploy khuyến nghị cho LEAF_AI:**
>
> | Thành phần | Nơi chạy |
> |---|---|
> | Backend Django (chẩn đoán, chatbot, admin) | **Render** — Web Service (Python) |
> | PostgreSQL | **Neon** — xem [NEON.md](NEON.md) |
> | Ảnh upload (media) | **Cloudinary** — xem [CLOUDINARY.md](CLOUDINARY.md) |
> | Frontend SPA (`frontend/`) + API serverless (`api/index.py`) | **Vercel** (đã cấu hình `vercel.json`) |
>
> Nguồn tham khảo: [Deploy a Django App on Render](https://render.com/docs/deploy-django),
> [Deploy for Free](https://render.com/docs/free), [Blueprint YAML Reference](https://render.com/docs/blueprint-spec).

---

## 0. Điều kiện tiên quyết

Trước khi deploy, bạn cần có:

1. **Repo GitHub** chứa dự án (đã push code LEAF_AI).
2. **Neon PostgreSQL** — connection string pooled ( [NEON.md](NEON.md) ).
3. **Cloudinary credentials** ( [CLOUDINARY.md](CLOUDINARY.md) ).
4. **`GEMINI_API_KEY`** — lấy tại <https://aistudio.google.com/apikey> (thiếu key này app vẫn chạy nhưng chẩn đoán trả trạng thái “Chưa phân tích được ảnh”).
5. File **`backend/.env.example`** → điền thành `backend/.env` khi chạy local (deploy thì khai env trên dashboard, **không** commit `.env`).

> Repo đã có sẵn: `backend/build.sh` (build + migrate + collectstatic),
> `backend/render.yaml` (blueprint), `backend/Procfile`, whitenoise, dj-database-url, psycopg2, gunicorn — **không cần cài gì thêm**.

---

## Cách A — Deploy thủ công bằng Web Service (khuyến nghị, chắc chắn nhất)

### A1. Tạo service

1. Đăng nhập **[render.com](https://render.com)** → **New +** → **Web Service**.
2. **Connect a repository**: chọn GitHub repo LEAF_AI (Render yêu cầu quyền read repo).
3. Cấu hình service:

| Property | Giá trị |
|---|---|
| **Name** | `leaf-ai` |
| **Region** | **Singapore** (cùng vùng Neon để latency thấp) |
| **Runtime** | Python |
| **Branch** | `main` |
| **Root Directory** | `backend` ⚠️ **bắt buộc** (repo đa thư mục — `manage.py` nằm trong `backend/`) |
| **Build Command** | `./build.sh` |
| **Start Command** | `gunicorn dermai.wsgi:application --workers 2 --timeout 120` |
| **Instance Type** | **Free** |

4. **Chưa bấm Create** — điền env vars trước (mục A2), hoặc tạo rồi vào **Environment** thêm sau.

### A2. Environment variables (Environment → Add Environment Variable)

| Key | Value | Ghi chú |
|---|---|---|
| `SECRET_KEY` | bấm **Generate** | hoặc `python -c "import secrets; print(secrets.token_urlsafe(50))"` |
| `DEBUG` | `False` | **không bao giờ** `True` trên production |
| `ALLOWED_HOSTS` | `leaf-ai.onrender.com` | đổi theo tên service + custom domain (nếu có), cách nhau dấu phẩy |
| `DATABASE_URL` | connection string **pooled** từ Neon | [NEON.md](NEON.md) mục 4 |
| `GEMINI_API_KEY` | key từ AI Studio | bắt buộc để chẩn đoán thật |
| `GEMINI_MODEL` | `gemini-2.5-flash` | optional, đã là mặc định |
| `CLOUDINARY_CLOUD_NAME` | từ Dashboard | [CLOUDINARY.md](CLOUDINARY.md) |
| `CLOUDINARY_API_KEY` | từ Dashboard | |
| `CLOUDINARY_API_SECRET` | từ Dashboard | |
| `SUPABASE_URL` | optional | đồng bộ lịch sử (nếu dùng Supabase) |
| `SUPABASE_SERVICE_ROLE_KEY` | optional | |

> `CSRF_TRUSTED_ORIGINS` **không cần set** — settings đã tự có sẵn `https://*.onrender.com`.
> Domain riêng (vd `https://leafai.example.com`) thì thêm biến `CSRF_TRUSTED_ORIGINS=https://leafai.example.com`.

### A3. Tạo & deploy

1. Bấm **Create Web Service**.
2. Render chạy `./build.sh`:
   ```bash
   pip install -r requirements.txt
   python manage.py collectstatic --no-input
   python manage.py migrate --fake-initial     # tạo bảng vào Neon
   ```
3. Xong → service live tại **`https://<tên-service>.onrender.com`**.
4. Tạo tài khoản admin: **Shell** (tab trong dashboard) →
   ```bash
   python manage.py createsuperuser
   ```
   rồi vào `https://<tên-service>.onrender.com/admin/` kiểm tra.

### A4. Tự động deploy khi push (khuyến nghị)

Service → **Settings → Build & Deploy** → bật **Auto Deploy** = `true`.
Mỗi lần `git push` lên `main`, Render tự build lại.

---

## Cách B — Deploy bằng Blueprint (`render.yaml`)

`backend/render.yaml` đã được cấu hình sẵn (tên service `leaf-ai`, region Singapore, DB `leaf-ai-db`,
env vars `GEMINI_*`, `CLOUDINARY_*`, `SUPABASE_*`, `SECRET_KEY` auto-generate…).

1. Render Dashboard → **Blueprints** → **New Blueprint Instance**.
2. Chọn repo LEAF_AI → **Connect**.
3. Nếu Render hỏi đường dẫn file cấu hình (repo có `render.yaml` trong thư mục con) → nhập **`backend/render.yaml`**.
4. Đặt tên project → **Apply**. Render tự tạo Web Service (+ Postgres `leaf-ai-db` nếu giữ section `databases`).

### ⚠️ Lưu ý quan trọng với Blueprint của repo này

- **Render Free PostgreSQL tự hết hạn sau 30 ngày** kể từ ngày tạo (kèm 14 ngày ân hạn để upgrade) —
  dữ liệu sẽ mất. **Khuyến nghị mạnh:** dùng **Neon** làm DB chính:
  - Bỏ/sửa 2 chỗ trong `render.yaml`: xóa section `databases:` và thay
    `DATABASE_URL: fromDatabase: ...` bằng
    ```yaml
      - key: DATABASE_URL
        sync: false        # rồi paste Neon URL vào dashboard sau lần deploy đầu
    ```
  - Nếu muốn giữ Blueprint sinh DB cho demo → backup định kỳ, đừng chứa dữ liệu thật.
- `fromDatabase` chỉ hoạt động khi DB cùng blueprint; lần deploy đầu sẽ tự nối DB mới.

---

## Giới hạn của Render Free (cần biết)

| Hạn mức | Giá trị | Ảnh hưởng tới LEAF_AI |
|---|---|---|
| Instance hours | **750 giờ/tháng** (reset đầu tháng) | với 1 service free là đủ 24/7 (spun-down không tính) |
| **Spin-down** | idle **15 phút** → tắt; request kế tiếp **~1 phút** để bật lại | lần đầu vào sau khi ngủ sẽ thấy loading — bình thường |
| Filesystem | **Ephemeral** — file local mất mỗi lần redeploy/spin-down | **bắt buộc dùng Cloudinary** cho ảnh upload; SQLite local cũng mất → phải dùng Neon |
| Persistent disk / SSH / scale >1 instance | không có trên Free | |
| Outbound bandwidth | có hạn mức/tháng — hết thì suspend tới tháng sau | ảnh nên serve trực tiếp từ Cloudinary CDN để không tốn bandwidth Render |
| Postgres trên Render | Free DB **hết hạn 30 ngày** | dùng Neon thay thế (mục trên) |

---

## Sự cố thường gặp

| Triệu chứng | Nguyên nhân / Cách sửa |
|---|---|
| `DisallowedHostError` | sai `ALLOWED_HOSTS` → thêm domain service |
| `CSRF verification failed` (POST login/predict) | thiếu origin trong `CSRF_TRUSTED_ORIGINS` → thêm `https://<tên>.onrender.com` (settings đã auto wildcard `*.onrender.com`) |
| `no pg_hba.conf entry...` / SSL error | thiếu `?sslmode=require` trong `DATABASE_URL` (Neon bắt buộc) |
| `OperationalError: connection refused` | URL dùng direct thay vì pooled → đổi sang hostname `-pooler`; hoặc Neon compute đang sleep (query đầu luôn wake được, thử lại) |
| Ảnh 404 sau khi deploy lại | chưa set `CLOUDINARY_*` → media đang nằm trong FS ephemeral |
| Chẩn đoán hiện “Chưa phân tích được ảnh” | thiếu `GEMINI_API_KEY` hoặc sai key → xem **Logs** |
| Build fail `manage.py: not found` | sai **Root Directory** → phải là `backend` |
| Django admin CSS 404 | `collectstatic` chạy trong `build.sh` + whitenoise đã cấu hình → nếu vẫn 404, vào Shell chạy `python manage.py collectstatic --no-input` rồi Restart |

**Xem log:** Service → **Logs**. Build log nằm ở tab **Events/Build**.

---

## Checklist sau deploy

- [ ] `https://<tên>.onrender.com/` mở được, không gặp lỗi 500
- [ ] `/admin/` login được, CSS hiển thị bình thường
- [ ] Tải ảnh thử → kết quả hiện **report HTML** của Gemini (hoặc trạng thái “Chưa phân tích được ảnh” nếu thiếu key — trung thực, không bịa bệnh)
- [ ] Ảnh upload xuất hiện trong Cloudinary (Media Library)
- [ ] `migrate` đã chạy (bảng Django trong Neon — kiểm tra SQL Editor)
- [ ] Auto Deploy đã bật
- [ ] `.env` / API secret **không** nằm trong git
