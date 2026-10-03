# 🍃 LEAF_AI — Tài liệu bàn giao Backend cho Frontend

> **Phiên bản:** 2026-10-03 (cập nhật pipeline Gemini Vision)
> **Trạng thái BE:** ✅ `manage.py check` sạch, ✅ **49/49 test pass**
> **Stack:** Django (Python) + Gemini Vision API (`google-genai`) + PostgreSQL/SQLite + Cloudinary (media) + Whitenoise (static)
> **Pipeline AI:** ❌ KHÔNG còn AI server YOLOv8 (model không kịp bàn giao) →
> **lấy link ảnh từ DB → đọc base64 → gửi Gemini API → nhận JSON + báo cáo HTML**

---

## 1. Pipeline chẩn đoán mới (đọc kỹ)

```
Upload ảnh
  └─ 1. Lưu Leaf_image vào DB  →  record.image.url  (link ảnh lấy TỪ DB)
       · URL https (Cloudinary) → download qua requests (timeout 20s)
       · URL /media/...         → đọc trực tiếp từ storage
  └─ 2. bytes → base64 (SDK google-genai mã hoá inline_data) → Gemini API
       · model: GEMINI_MODEL (mặc định gemini-2.5-flash), timeout 45s
       · response_mime_type = application/json
  └─ 3. JSON {healthy, diseases[], regions[], report_html}
       · chuẩn hoá theo knowledge base 6 bệnh cà chua
       · report_html được sanitize bằng bleach (whitelist tag/attr)
  └─ 4. Lưu vào DB (result, primary_*, detections, explain=report_html) → trả FE
```

- **Không còn** `AI_SERVER_URL` / `fast_api()` / heatmap Grad-CAM — xóa khỏi env & docs.
- Mọi biến đều **best-effort**: AI lỗi KHÔNG BAO GIỜ chặn upload hay làm 500.

### `.env` tối thiểu

```bash
SECRET_KEY=<khóa bí mật>
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3        # production: postgres://...
GEMINI_API_KEY=...                       # BẮT BUỘC nếu muốn chẩn đoán thật
GEMINI_MODEL=gemini-2.5-flash            # optional, mặc định gemini-2.5-flash
```

> Thiếu `GEMINI_API_KEY` → hệ thống **không bịa bệnh**: API trả `analysis_unavailable: true`
> kèm `note` giải thích, FE hiển thị trạng thái "Chưa phân tích được" (xem §3.2).

---

## 2. Model & dữ liệu

### 2.1 `Leaf_image` (một lần chẩn đoán = 1 bản ghi)

| Field | Kiểu | Ý nghĩa |
|---|---|---|
| `id` | int | dùng trong URL `/result/<id>/` và `record.id` của API |
| `image` | file | ảnh gốc — **link lấy từ đây** (`image.url`) |
| `result` | JSON list | `[{class, probability}]` cho bảng kết quả (template) |
| `detections` | JSON list | bbox pixel `[{class, name_vi, confidence, probability_percent, color, bbox:[x,y,w,h]}]` |
| `primary_disease` / `primary_disease_vi` | text | mã bệnh + tên Việt (trống nếu healthy/unavailable) |
| `confidence` | float | % bệnh chính (0-100) |
| `severity` | text | `Nghiêm trọng` ≥60 / `Trung bình` 35-59 / `Nhẹ` <35 / `Khỏe` |
| `is_coinfection` | bool | đồng nhiễm (nhiều bệnh) |
| `secondary_diseases` | JSON list | bệnh phụ |
| `explain` | HTML string | **báo cáo Gemini** (đã sanitize) — FE render bằng container `.ai-report` |
| `model_version` | text | `v3` (3 bệnh) / `v4` (6 bệnh) |
| `heatmap` | — | **không còn dữ liệu** — FE bỏ mọi UI Grad-CAM |
| `more`, `gender`, `age`, `symptom`, `illness_history`, `drug_history` | text | thông tin người dùng (predict) |

### 2.26 bệnh cà chua (mã chuẩn hóa — `class` chỉ nhận đúng bộ này)

`Bacterial_spot`, `Early_blight`, `Late_blight` (V3 mặc định)
`+ Septoria_leaf_spot`, `Leaf_mold`, `Powdery_mildew` (V4)

---

## 3. API Contract

### 3.1 Upload (Django template flow)

**POST `/upload/`** (base64 trong form) · **POST `/upload/file/`** (multipart):

```
image = "data:image/jpeg;base64,..." | <File>     # bắt buộc, ≤10MB, image/*
model_version = "v3" | "v4"                       # optional, mặc định v3
```

| Response | Ý nghĩa |
|---|---|
| **302** → `/result/<id>/` | ảnh đã lưu (kèm chẩn đoán best-effort) |
| **400** `{error}` | thiếu ảnh / sai MIME / base64 hỏng |
| **429** `{error}` | rate-limit 10 request/phút/user |

> **KHÔNG CÒN 502** — AI lỗi không chặn upload; nếu không tạo được báo cáo thì
> trang kết quả sẽ hiển thị form "Thêm thông tin" (predict tạo báo cáo lần2).

### 3.2 ⭐ POST `/api/diagnose/` — endpoint chính của SPA

`Content-Type: multipart/form-data` (hoặc JSON body `{image: "<data-url>", model_version}`):

```
image = <File> | "data:image/jpeg;base64,..."    # bắt buộc
model_version = "v3" | "v4"                      # optional
```

**Response200:**

```jsonc
{
  "success": true,
  "id": 123,                          // record.id (null nếu lỗi lưu DB)
  "model_version": "v3",
  "model_badge": "Model V3 (Production)",
  "is_coinfection": false,
  "warning_banner": null,             // "Phát hiện đa bệnh (đồng nhiễm)" nếu true
  "healthy": false,                   // true = lá không có dấu hiệu bệnh
  "primary_disease": {                // null nếu healthy hoặc unavailable
    "class": "Early_blight", "name_en": "Early Blight",
    "name_vi": "Úa sớm (Đốm vòng)", "probability": 87.0,
    "severity": "Nghiêm trọng", "color": "#f97316",
    "treatment": {"cultural": "...", "biological": "...", "chemical": "..."},
    "prevention": "..."
  },
  "secondary_diseases": [ { "class": "...", "name_vi": "...", "probability": 42.0,
                            "severity": "Trung bình", "color": "#ef4444" } ],
  "detections": [                     // bbox theo PIXEL ảnh gốc (canvas đã scale)
    { "class": "Early_blight", "name_vi": "Úa sớm (Đốm vòng)",
      "confidence": 0.87, "probability_percent": 87.0,
      "color": "#f97316", "bbox": [40, 30, 200, 150] }
  ],
  "lesion_count": 3,
  "report_html": "<h3>Kết luận nhanh</h3>...",   // BÁO CÁO — render nguyên khối, KHÔNG escape
  "analysis_unavailable": false,      // true = AI không phân tích được
  "note": "",                         // message tiếng Việt khi unavailable
  "heatmap_available": false,         // luôn false (không còn Grad-CAM)
  "heatmap_base64": null,
  "heatmap_url": null,
  "synced_to_supabase": false,
  "supabase_id": null
}
```

**Lỗi:**

| Status | Body | Ghi chú |
|---|---|---|
| 400 | `{error}` | thiếu ảnh / >10MB |
| 429 | `{error}` | **rate-limit 10/phút** (theo user hoặc IP) — FE nên hiện toast thân thiện |

**Khi AI không khả dụng** (`analysis_unavailable: true`): response vẫn **200 + `success: true`**
(ảnh đã lưu), nhưng `primary_disease: null`, `detections: []`, `report_html: null`,
`note`: *"Dịch vụ AI chưa được cấu hình (thiếu biến GEMINI_API_KEY)..."*.
→ **FE TUYỆT ĐỐNG không được hiển thị "Lá khỏe mạnh"** trong trường hợp này —
hãy hiện "Chưa phân tích được ảnh" + `note` (SPA đã làm sẵn: nhánh `analysis_unavailable`
trong `scan.js`).

### 3.3 Predict (tạo/repair báo cáo + context người dùng)

**POST `/predict/<id>/`** — form: `gender`, `age`, `symptom`, `illness_history`, `drug_history`
→ backend gọi lại Gemini **kèm ảnh từ DB + context** → cập nhật `explain` → 302 `/result/<id>/`.
AI lỗi → `explain` = HTML thông báo thân thiện (không trống, không gặp lỗi 500).

### 3.4 Các endpoint khác (giữ nguyên)

| Method | URL | Ghi chú |
|---|---|---|
| GET | `/result/<id>/` | trang kết quả; report render trong `.ai-report` |
| GET | `/profile/` | lịch sử |
| POST | `/history/<id>/delete/` | xóa bản ghi (404 nếu không phải mình, 405 với GET) |
| POST | `/chatbot/api/` | JSON `{message}` → `{reply, reply_html}` — 20/phút |
| GET | `/api/history/?limit=50` | danh sách; bản ghi healthy trả `primary_disease: "Healthy"`, `primary_disease_vi: "Lá khỏe mạnh"` |
| DELETE | `/api/history/<id>/delete/` | xóa1 bản ghi |
| GET | `/api/diseases/`, `/api/handbook/`, `/api/models/`, `/api/stats/` | knowledge base (không đổi) |
| POST | `/api/chat/` | chatbot tư vấn (Gemini + fallback nội tuyến) |
| GET | `/health/` | `{status: "ok"}` |

---

## 4. ⭐ Contract HTML của `report_html` (quan trọng cho styling)

Backend **đã sanitize** (bleach) — FE render nguyên khối bằng `innerHTML` / `|safe`
trong container **`.ai-report`**. Chỉ các tag và class sau được sống sót:

**Tag:** `h3 h4 p ul ol li strong em b i small br hr div span table thead tbody tr th td a`

**Class (FE chỉ cần style đúng bộ này — SPA đã có sẵn trong `style.css`):**

| Class | Ý nghĩa |
|---|---|
| `badge` + `badge-high` / `badge-mid` / `badge-low` | pill mức độ: Nghiêm trọng / Trung bình / Nhẹ |
| `pct` | số % đậm (xanh lá) |
| `report-table` | bảng (thường cột: Bệnh / Độ tin cậy / Mức độ) |
| `callout` + `callout-warn` / `callout-info` | khung chú ý / thông tin |

**Cấu trúc6 phần** (prompt yêu cầu Gemini): Kết luận nhanh → Quan sát trên ảnh →
Bệnh chính và mức độ → Nguyên nhân → Phác đồ xử lý → Phòng ngừa và lưu ý
(khuyến cáo tham khảo chuyên gia BVTV).

Nếu Gemini không trả HTML → backend tự sinh bảng tối giản (`render_basic_report`)
nên `report_html` **gần như luôn có** khi phân tích thành công.

### Nơi render

- **SPA:** `<section id="aiReportSection">` + `<div id="aiReport" class="ai-report">`
  trong `scan.html`, điền bởi `scan.js` — đã có CSS sẵn trong `style.css`.
- **Template:** `<div class="ai-report">{{ skin_image.explain|safe }}</div>` trong `result.html`
  — đã có CSS sẵn trong `<style>` của trang.

---

## 5. Ràng buộc kỹ thuật cho FE

- **Rate-limit:** upload10/phút, `/api/diagnose/` **10/phút**, chatbot 20/phút → hiện toast khi 429.
- **Ảnh mẫu (sample):** PHẢI gửi **data URL**, không gửi chuỗi đường dẫn.
  `api.js` đã có `_toDataUrl()` chuyển tự động — đừng ghi đè.
- **Service Worker:** sau khi sửa asset phải **bump `CACHE_NAME`** trong `sw.js`
  (đã bump lên `leaf-ai-v2.1.0`) nếu không trình duyệt vẫn chạy bundle cũ.
- **CSRF:** POST form cần token; `/api/*` là `csrf_exempt` (dùng `credentials: 'include'`).
- **Không còn heatmap** — ẩn toggle "Bản đồ nhiệt" (SPA đã tự ẩn khi `heatmap_url === null`).
- **Timeout:** backend gọi Gemini tối đa45s; `api.js` timeout60s — OK.

---

## 6. Checklist FE còn lại (ngoài phạm vi BE)

1. ~~Rebranding legacy templates DermAI → LEAF_AI~~ — **hoàn tất** (toàn bộ trang Django template đã LEAF_AI).
2. ~~i18n / đa ngôn ngữ~~ — **đã gỡ khỏi dự án** (chỉ còn tiếng Việt, không còn switcher, route `/i18n/`, `{% trans %}`).
3. ~~Hotline `tel:115`~~ — **đã thay** bằng link Thư viện bệnh & phác đồ; trang `pharmacy` + đăng nhập Google + allauth **đã gỡ**.
4. Nếu FE muốn badge/severity đổi màu theo `severity` backend trả —
   dùng đúng3 giá trị `Nghiêm trọng | Trung bình | Nhẹ` (+`Khỏe` cho bản ghi healthy).

---

## 7. Thay đổi BE trong lần cập nhật này (tóm tắt)

- **Bỏ toàn bộ pipeline AI server** (`Dermal/fastapi.py` đã xóa; không còn `fast_api()`,
  `AIServerError`, `AI_SERVER_URL`, phản hồi502).
- Module mới **`Dermal/leaf_ai.py`**: đọc link ảnh từ DB → base64 → Gemini Vision →
  JSON chuẩn hóa + HTML sanitize; throttle dùng chung; `FALLBACK_REPORT_HTML`.
- `api_diagnose` (Django) & `/api/diagnose/` (FastAPI serverless Vercel) dùng **cùng**
  `diagnose_leaf_image()` — không còn2 phiên bản lệch nhau; bịa kết quả theo tên file đã bỏ.
- Thêm **rate-limit10/phút** cho `/api/diagnose/` (429).
- `predict` gọi Gemini **kèm ảnh** (trước chỉ gửi text) — báo cáo sát thực tế hơn.
- FE: container báo cáo `.ai-report` (SPA + `result.html`), nhánh
  `analysis_unavailable` trung thực, fix ảnh mẫu gửi data URL, bump SW cache.
- Fix dev: `dermai/urls.py` serve `/media/` khi DEBUG (trước đó ảnh upload404 local).
- `test_full_suite.py` cập nhật theo contract mới; **49 unit test** trong `Dermal/tests.py`.
