# 🍃 LEAF_AI — Tài liệu bàn giao Backend cho Frontend

> **Phiên bản:** 2026-10-02
> **Trạng thái BE:** ✅ `manage.py check` sạch, ✅ 32/32 test pass
> **Stack hiện tại:** Django (Python) + PostgreSQL (Render/Neon) + Cloudinary (media) + Whitenoise (static)
> **AI server:** service riêng (FastAPI + YOLOv8) — BE gọi qua HTTP, KHÔNG train model trong repo này

---

## 1. Chạy dự án local

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt   # Windows; Linux/mac: .venv/bin/pip

# .env tối thiểu
SECRET_KEY=<khóa bí mật>
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3        # production: postgres://...
GEMINI_API_KEY=...                       # optional (chatbot + báo cáo)
AI_SERVER_URL=http://localhost:8000/predict   # optional, mặc định là HF space

.venv/Scripts/python manage.py migrate
.venv/Scripts/python manage.py runserver
```

Test / kiểm tra:

```bash
python manage.py check
python manage.py test Dermal
```

---

## 2. Model & dữ liệu

### 2.1 `Leaf_image` (một lần chẩn đoán = 1 bản ghi)

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | dùng trong URL `/result/<id>/` |
| `image` | file | ảnh gốc (Cloudinary) |
| `heatmap` | file \| null | heatmap (nếu AI server trả về) |
| `result` | JSON list | kết quả detection, xem schema §3.2 |
| `result_en` | — | **chưa tồn tại** — template đã guard `{% if ... result_en %}`, khi BE làm i18n sẽ thêm |
| `explain` | HTML string | báo cáo phân tích (Gemini), đã sanitize bleach |
| `more` | text | thông tin bổ sung người dùng nhập |
| `gender`, `age` | text | giới tính / tuổi (bước chẩn đoán nâng cao) |
| `symptom` | text | triệu chứng |
| `illness_history` | text | tiền sử bệnh |
| `drug_history` | text | tiền sử thuốc |
| `uploaded_at` | datetime | thời điểm tải lên |

### 2.2 `Profile`

`user` (OneToOne với User), `bio`, `title`, `location`, `avatar`, `birth_date`.
Profile tự tạo khi User đăng ký (signal).

---

## 3. API Contract

Tất cả URL đã được test reverse được. base = `/`

### 3.1 Auth

| Method | URL | Body | Response |
|---|---|---|---|
| GET/POST | `/signup/` | `username`, `email`, `password` (+ optional `birth_date`, `avatar` file) | 302 → `/` hoặc render lại form + message lỗi |
| GET/POST | `/login/` | `username` (hoặc `email`), `password` | 302 → `/` hoặc render + lỗi |
| GET | `/logout/` | — | 302 → `/login/` |
| — | `/accounts/google/login/` | OAuth (allauth) | redirect |

- Password được validate bằng `AUTH_PASSWORD_VALIDATORS` của Django (mật khẩu yếu bị từ chối).
- Đăng nhập **bằng email** đã hỗ trợ.

### 3.2 Chẩn đoán (upload → kết quả)

**POST `/upload/`** — camera capture (base64 trong form):

```
image = "data:image/jpeg;base64,..."      # bắt buộc
model_version = "v3" | "v4"               # optional, mặc định "v3"
csrfmiddlewaretoken = ...                  # bắt buộc (form)
```

**POST `/upload/file/`** — upload file:

```
image = <File>        # bắt buộc, image/*, ≤ 10MB
model_version = "v3" | "v4"   # optional
```

Response (cả 2):

- **302** → `/result/<id>/` khi thành công
- **400** `{error}` — không có ảnh / ảnh sai loại / >10MB / base64 hỏng
- **429** `{error}` — rate-limit: 10 request/phút/user
- **502** `{error}` — AI server lỗi/timeout (60s)

**Schema `result` (JSONField):**

```json
[
  {"class": "Early_blight", "probability": 87.5},
  {"class": "Bacterial_spot", "probability": 9.2}
]
```

> Khi AI server chuyển sang YOLOv8 trả bounding box, BE sẽ mở rộng schema
> (dự kiến thêm `bbox: [x, y, w, h]` và `confidence`) — FE render theo §5.

**GET `/result/<id>/`** — trang kết quả (HTML, cần đăng nhập;
không thuộc về mình → 404).

### 3.3 Chẩn đoán nâng cao (báo cáo Gemini)

**POST `/predict/<id>/`**

```
gender = "Nam" | "Nữ"
age = "30"
symptom = "..."
illness_history = "..."
drug_history = ...
```

- **302** → `/result/<id>/` — đã lưu info + `explain` (HTML)
- **404** nếu ảnh không tồn tại / không thuộc user
- Gemini lỗi → fallback text thân thiện, KHÔNG 500.

### 3.4 Lịch sử chẩn đoán

| Method | URL | Ghi chú |
|---|---|---|
| GET | `/profile/` | danh sách bản ghi của user (mới nhất trước) |
| POST | `/history/<id>/delete/` | **xóa bản ghi** (chỉ của mình), 404 nếu không phải, 405 nếu GET, 302 → `/profile/` |

### 3.5 Chatbot

**POST `/chatbot/api/`** (JSON, cần đăng nhập + CSRF header `X-CSRFToken`):

```json
// request
{"message": "Cách phòng bệnh đốm lá?"}
// response 200
{"reply": "markdown text...", "reply_html": "<p>...</p>"}
```

- 400 `{error}` — thiếu message / JSON hỏng / message > 4000 ký tự
- 429 `{error}` — 20 tin/phút/user
- Gemini chết → reply thân thiện (không crash)

### 3.6 Trang tĩnh / khác

| URL | Ghi chú |
|---|---|
| `/` | home (camera capture) — **cần đăng nhập** |
| `/pharmacy/` | bản đồ cơ sở vật tư/nông nghiệp gần tôi (public) |
| `/chatbot/` | trang chatbot |
| `/health/` | health check: `{"status":"ok"}` (GET/HEAD) |
| `/i18n/setlang/` | POST `language=vi\|en`, `next=<path>` |

**i18n:** URL tiếng Anh có prefix `/en/...`, tiếng Việt **không prefix**
(`/login/` thay vì `/vi/login/`) — đã sửa (`prefix_default_language=False`).

---

## 4. Ràng buộc kỹ thuật cho FE

- **CSRF:** mọi POST cần token (form: `{% csrf_token %}`; fetch:
  header `X-CSRFToken` đọc cookie `csrftoken`).
- **Auth:** đa số trang redirect `/login/` nếu chưa đăng nhập.
- **Rate-limit:** upload 10/phút, chatbot 20/phút → UI nên hiện thông báo
  thân thiện khi nhận 429.
- **Lỗi server:** JSON `{error: "<tiếng Việt>"}` với mã 400/405/429/502.
- **Upload ảnh:** ≤ 10MB, chỉ `image/*`.

---

## 5. Việc FE cần làm (theo spec trong ảnh) — BE đã sẵn sàng cho phần này

### ✅ FE đã có template tham chiếu (Django templates hiện tại)

- Home (camera + upload modal) — `home.html`
- Kết quả chẩn đoán — `result.html`
- Lịch sử + **nút "Xóa bản ghi"** (mới thêm) — `profile.html`
- Chatbot — `chatbot.html`
- Login/Signup/Profile — có sẵn
- Navbar dưới đã trỏ route `pharmacy` hợp lệ (bug cũ: 500 toàn trang)

### ⚠️ Việc FE cần làm tiếp

1. **Rebranding DermAI → LEAF_AI** — toàn bộ title/meta OG/nội dung vẫn còn
   "DermAI / chẩn đoán bệnh da liễu". Các nơi cần sửa:
   `home.html`, `login.html`, `signup.html`, `result.html`, `profile.html`,
   `chatbot.html`, `pharmacy.html`, `socialaccount/*.html`.
2. **Nội dung theo spec ảnh (chưa có, FE dựng tĩnh hoặc BE bổ sung sau):**
   - Thư viện bệnh (6 bệnh cà chua: Bacterial Spot, Early Blight, Late Blight,
     Septoria Leaf Spot, Leaf Mold, Powderly Mildew) — KHÔNG cần API, content tĩnh.
   - Cẩm nang chăm sóc (8 nguyên tắc / 7 bước kiểm tra / 10 bước FAQ BVTV).
   - Thống kê trang chủ (spec ghi *mock data* → FE tự render số giả).
   - Panel "Thông số AI/Model": V3 (mặc định, 3 bệnh) / V4 (experimental, 6 bệnh) —
     gửi `model_version` khi upload, số liệu hiển thị (mAP50 0.768, Recall 80.8%,
     input 640×640, confidence 0.25) là content tĩnh.
3. **Kết quả chẩn đoán theo spec:** khung YOLO scan, bounding box trên ảnh,
   bệnh chính + %, mức độ nguy hiểm, danh sách bệnh phụ %.
   - Hiện schema `result` mới có `{class, probability}` (classification).
   - **Chờ BE nâng cấp schema bbox** (khi AI server YOLOv8 hoàn thiện) —
     FE chuẩn bị component vẽ overlay canvas/SVG trên ảnh, đọc `bbox`.
4. **Bước "Xem phác đồ / IPM & chăm sóc"** — nút sau khi có báo cáo;
   nội dung phác đồ tĩnh (chưa có API).
5. **Gọi cấp cứu 115** trong navbar → đổi thành hotline nông nghiệp / CSDL
   (theo spec "nhà nông" không phải 115).
6. **i18n:** thêm file `.po` cho `en` (hiện `LOCALE_PATHS/locale` chưa có
   file dịch → tiếng Anh gần như bằng tiếng Việt). Dùng
   `python manage.py makemessages -l en && compilemessages`.

### 🔌 Khi nào cần nói chuyện với BE

- Schema `result` mở rộng `bbox` + `confidence` (YOLOv8) — BE sẽ báo thêm.
- API thống kê thật (nếu không muốn mock).
- Endpoint gợi ý phác đồ theo bệnh (nếu không làm content tĩnh).
- Thêm trường `result_en`/`explain_en` khi làm i18n kết quả (mẫu template
  đã sẵn, chờ field).

---

## 6. Changes BE đã fix (tóm tắt, để FE khỏi test lại chỗ chết)

- P0: `admin.py` register model không tồn tại → server không boot được.
- P0: route `pharmacy` thiếu → 500 mọi trang (navbar).
- P0: `predict` gán `more=None` → IntegrityError 500 → đã nhận đúng field
  form (`gender/age/symptom/illness_history/drug_history`).
- Thêm field cho model, migration `0001_initial` đã commit.
- AI client: timeout 60s, validate response, param `model_version`,
  exception riêng → không còn `output[...]` crash.
- Upload: validate MIME + ≤10MB, rate-limit 10/phút, bỏ `csrf_exempt`.
- Chatbot: rate-limit 20/phút, sanitize HTML, fallback khi Gemini lỗi.
- Bỏ `print(api_key)` (rò rỉ secret), `DEBUG` đọc từ env, HTTPS cookie
  production, `SITE_ID=1`, đăng nhập được bằng email,
  `login()` sau signup chỉ định backend (bug 2 auth backend).
- `i18n_patterns(prefix_default_language=False)` — hết redirect `/vi/`.
- Thêm endpoint `POST /history/<id>/delete/` (spec "Xóa bản ghi").
