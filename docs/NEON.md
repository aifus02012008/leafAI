# 🗄️ Hướng dẫn: Lấy PostgreSQL miễn phí trên Neon.tech

> Dùng cho LEAF_AI — database chính của app khi deploy (Render, Vercel hoặc chạy local).
> Nguồn tham khảo: [neon.com/docs](https://neon.com/docs/introduction/plans) — kế hoạch & giới hạn,
> [Connection pooling](https://neon.com/docs/connect/connection-pooling).

---

## 1. Neon là gì?

Neon là **PostgreSQL serverless** — database Postgres chuẩn, chạy trên cloud, có **free tier $0**:

| Hạng mục | Free tier |
|---|---|
| Giá | **$0/tháng**, không cần thẻ tín dụng |
| Projects | 100 project |
| Branches | 10 nhánh/project |
| Compute | **100 CU-hours/tháng** (0.25 CU ≈ chạy 400 giờ/tháng) |
| Storage | **1 GB/project** (tối đa 20 GB cho toàn account) |
| Egress | 5 GB/project |
| Scale-to-zero | Tự tắt sau **5 phút** không hoạt động (tự bật lại khi có query) |
| Auto-scaling | Tối đa 2 CU (8 GB RAM) |

Điểm quan trọng với LEAF_AI:

- **Scale-to-zero** = lần query đầu tiên sau khi idle sẽ chậm thêm vài trăm ms (compute bật lại) — chấp nhận được với app demo.
- **Pooler (PgBouncer)** cho phép tới 10.000 kết nối đồng thời — quan trọng vì Render Web Service chạy nhiều gunicorn worker.
- Free tier **không hết hạn sau N ngày** như Render Postgres — dùng lâu dài được.

---

## 2. Đăng ký tài khoản

1. Mở **[https://neon.com](https://neon.com)** → **Sign up**.
2. Đăng ký bằng **GitHub** hoặc **Google** (nhanh nhất, không cần thẻ tín dụng).
3. Xác minh email nếu Neon yêu cầu.

---

## 3. Tạo project database

1. Từ Neon Console → **Projects** → **New Project** (hoặc **Create Project** ngay lần đầu đăng nhập).
2. Điền:
   - **Project name**: `leaf-ai`
   - **Database name**: giữ mặc định `neondb` (settings của LEAF_AI không ép tên DB)
   - **Region**: chọn vùng gần Render nhất — **`Southeast Asia (Singapore)`** nếu có, vì `backend/render.yaml` dùng region `Singapore`. Cùng vùng = latency nội bộ thấp, tránh lỗi vượt vùng với một số plan.
3. Bấm **Create**. Neon tự tạo:
   - Branch gốc tên **`production`**
   - Role mặc định + database `neondb`

---

## 4. Lấy Connection String (quan trọng)

1. Trong console project → mở modal **Connect** (thanh điều hướng bên trái).
2. Chọn Branch = `production`, Database = `neondb`, Role = role mặc định.
3. Bật **Connection pooling** (mặc định đã bật) rồi **copy connection string**.

Chuỗi kết nối trông như:

```text
# Pooled (KHUYẾN NGHỊ cho app — hostname có hậu tố -pooler)
postgresql://neondb_owner:AbC123xYz@ep-cool-darkness-123456-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require

# Direct (dùng cho tool cần session ổn định: psql, pg_dump, migrate nếu lỗi qua pooler)
postgresql://neondb_owner:AbC123xYz@ep-cool-darkness-123456.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

**Dùng loại nào?**

| Tình huống | Dùng |
|---|---|
| LEAF_AI chạy trên Render (gunicorn nhiều worker, nhiều request ngắn) | **Pooled** (`-pooler`) |
| Chạy `psql`, `pg_dump`, debug schema từ máy local | Direct |
| `python manage.py migrate` báo lỗi kỳ lạ qua pooler (Django cần `SET`/session) | đổi sang Direct |

4. Dán chuỗi vào **`backend/.env`** (xem [backend/.env.example](../backend/.env.example)):

```dotenv
DATABASE_URL=postgresql://neondb_owner:...@ep-xxx-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

> ⚠️ `sslmode=require` là bắt buộc — settings của LEAF_AI tự bật `ssl_require` cho URL postgres.
> Không commit `.env` vào git (`.gitignore` đã loại trừ sẵn).

---

## 5. Kiểm tra kết nối

**Cách A — psql (nếu đã cài PostgreSQL client):**

```bash
psql "<dán connection string>"
# trong psql:
SELECT version();
\dt        -- xem bảng (sau khi migrate sẽ có bảng của Django)
\q
```

**Cách B — qua LEAF_AI (không cần cài gì thêm):**

```bash
cd backend
# .env đã có DATABASE_URL ở trên
python manage.py migrate     # tạo bảng Django vào Neon
python manage.py runserver   # chạy thử — query qua Neon
```

**Cách C — Neon Console:** sidebar → **Postgres database → SQL Editor** → chạy `SELECT 1;`

---

## 6. Bảo mật & mẹo

- **Không** đưa connection string vào code/git; chỉ để trong `.env` hoặc env vars của Render/Vercel.
- Quên password → Neon Console → **Roles** → reset; hoặc rotate credentials.
- Giám sát dùng liệu tại **Monitoring** page (connections, CU-hours). Hết 100 CU-hours tháng này → compute tạm ngừng tới tháng sau (hoặc upgrade Launch).
- Muốn tách environment → tạo **branch** mới (`development`) từ `production`: copy-on-write, có DB riêng, free 10 branch/project.
- **Migrate nên chạy khi compute awake** — lần đầu kết nối sau idle sẽ mất thêm <1s để wake up, không phải lỗi.

---

## 7. LEAF_AI mapping env vars

| Biến trong `.env` | Giá trị |
|---|---|
| `DATABASE_URL` | Pooled connection string ở mục 4 |

Các biến còn lại của LEAF_AI: xem [backend/.env.example](../backend/.env.example) — cấu hình Render nằm trong [RENDER.md](RENDER.md).
