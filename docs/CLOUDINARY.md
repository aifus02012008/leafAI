# ☁️ Hướng dẫn: Lấy Cloudinary API cho LEAF_AI

## 1. Cloudinary là gì và vì sao LEAF_AI cần

> Cloudinary lưu **ảnh người dùng tải lên** (ảnh lá chụp/cả bệnh phẩm).
> **Bắt buộc khi deploy Render**: filesystem trên Render Free là **thường trú (ephemeral)** —
> file upload sẽ **mất sạch** khi redeploy/restart/spin-down. Khi cấu hình Cloudinary,
> `settings.py` tự chuyển storage sang `MediaCloudinaryStorage`, ảnh sống trên CDN vĩnh viễn.
>
> Nguồn tham khảo: [Finding your credentials](https://cloudinary.com/documentation/finding_your_credentials_tutorial),
> [Billing & Plans](https://cloudinary.com/documentation/billing_and_plans).

## 2. Đăng ký

1. Mở **[https://cloudinary.com](https://cloudinary.com)** → **Sign Up / Get Started as a Developer**.
2. Đăng ký bằng **Google / GitHub / email**.
3. Chọn **Free plan**:
   - **$0**, không cần thẻ tín dụng, không giới hạn thời gian
   - **25 credits/tháng** (≈ 25 GB lưu trữ *hoặc* băng thông *hoặc* transform — dùng chung một “ví”)
   - 3 users, đủ cho team nhỏ
4. Vào Console/ Dashboard lần đầu — Cloudinary tự tạo cho bạn một **Product Environment** kèm cloud name riêng.

## 3. Lấy API credentials (Cloud name + API Key + API Secret)

Theo tài liệu chính thức của Cloudinary, có 2 đường:

**Cách A — từ Dashboard (nhanh nhất):**

1. Đăng nhập → mở **Dashboard** (`https://console.cloudinary.com/` hoặc link từ trang chủ).
2. Ở **đầu trang**, dưới mục **Product Environment**, thấy ngay:
   - **Cloud name** → bấm icon copy
   - **API Key** → bấm copy
   - **API Secret** → bấm **Show** (có thể yêu cầu xác thực lại) rồi copy

**Cách B — từ Settings (khi cần tạo key mới / key cũ bị lộ):**

1. Console → **Settings → API Keys**.
2. **Generate New Access Key** → nhập **mã xác thực gửi qua email** → **Save**.
3. Lấy Cloud name tương tự từ Dashboard.

## 4. Điền vào `.env`

Mở [backend/.env.example](../backend/.env.example), copy sang `backend/.env` và điền:

```dotenv
CLOUDINARY_CLOUD_NAME=xxxxxxx
CLOUDINARY_API_KEY=123456789012345
CLOUDINARY_API_SECRET=AbCdEfGhIjKlMnOpQrStUvWxYz
```

Khi `CLOUDINARY_API_KEY` có mặt, `dermai/settings.py` tự kích hoạt backend
`cloudinary_storage.storage.MediaCloudinaryStorage` — không cần sửa code.

## 5. Kiểm tra credentials hoạt động

Chạy trong `backend/` (SDK `cloudinary` đã có trong requirements):

```bash
python - <<'EOF'
import os, cloudinary, cloudinary.api
from dotenv import load_dotenv
load_dotenv()
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
)
print("Account:", cloudinary.api.ping())
# Upload thử 1 ảnh nhỏ rồi xóa ngay
up = cloudinary.uploader.upload(
    "https://res.cloudinary.com/demo/image/upload/sample.jpg",
    public_id="leaf_ai_smoke_test", folder="leaf_ai",
)
print("Upload OK:", up["secure_url"])
cloudinary.uploader.destroy(up["public_id"])
print("Cleanup OK")
EOF
```

- `Upload OK` + `Cleanup OK` = credentials đúng, sẵn sàng cho Render.
- Lỗi `401 Unauthorized` = sai API Key/Secret → kiểm tra lại (xem mục 3).

## 6. Lưu ý an toàn

- **Không commit** API Secret vào git — chỉ nằm trong `.env` / env vars của Render.
- API Secret bị lộ → Console → **Settings → API Keys → Reset** (secret mới, thay env tương ứng).
- Project upload **server-side** (Django upload qua form/API) ⇒ **không cần** upload preset unsigned phía browser.
- Hosting ảnh: đường dẫn trả về dạng `https://res.cloudinary.com/<cloud>/image/upload/...` — served qua CDN toàn cầu, LEAF_AI chỉ cần hiển thị `<img src>` bình thường.

## 7. Mapping env vars cho LEAF_AI

| Biến | Nguồn |
|---|---|
| `CLOUDINARY_CLOUD_NAME` | Dashboard → Product Environment → Cloud name |
| `CLOUDINARY_API_KEY` | Dashboard → API Key |
| `CLOUDINARY_API_SECRET` | Dashboard → API Secret (Show) |

Tiếp theo: điền các biến này vào env group của Render — xem [RENDER.md](RENDER.md).
