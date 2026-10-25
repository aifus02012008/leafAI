# Huấn luyện mô hình nhận diện bệnh lá vải thiều — LEAF_AI

## Kiến trúc chẩn đoán

```
Ảnh lá ──► Kiểm tra chất lượng trên điện thoại (mờ / tối / cháy sáng / không thấy lá) + nén ảnh
        └► Mô hình LEAF_AI (CNN huấn luyện trên ảnh lá vải, máy chủ Render)  ── chắc chắn ──► Kết quả + Grad-CAM
                     │ chưa chắc (dưới ngưỡng hiệu chỉnh) / 2 lớp sát nhau / "Other" / máy chủ chưa sẵn sàng
                     ▼
              Gemini Vision (/api/diagnose) — chuyên gia thứ hai cho ca khó
                     ▼
        Kết hợp: đồng thuận → tin cậy cao · bất đồng → báo rõ, gợi ý chụp thêm · không bao giờ bịa kết quả
```

**Mô hình `.pt` là thành phần chính.** Gemini chỉ xử lý tình huống khó. Mô hình cũ (`tomato_model.pt`) được
huấn luyện trên lá **cà chua** rồi đổi tên lớp sang bệnh vải, nên kết quả trên lá vải thật gần như ngẫu nhiên.
Máy chủ mới **từ chối** checkpoint cà chua.

7 lớp: `Healthy` (khỏe), `Anthracnose` (thán thư), `Downy_blight` (sương mai), `Leaf_blight` (cháy lá),
`Algal_spot` (đốm rong), `Erinose` (nhện lông nhung), `Other` (vấn đề khác: lá khô, sâu ăn, cháy nắng, virus…).
Lớp `Other` giúp mô hình biết nói "không phải 5 bệnh" thay vì ép vào một bệnh.

---

## Bước 1 — Môi trường

```bash
cd D:\LEAF_AI\leafAI
python -m venv .venv-train && .venv-train\Scripts\activate
# Có GPU NVIDIA: cài torch bản CUDA trước (chọn lệnh trên https://pytorch.org/get-started/locally/)
pip install -r ml/training/requirements-train.txt
python -c "import torch; print(torch.cuda.is_available())"
```

Không có GPU → dùng Google Colab (xem cuối file).

## Bước 2 — Tải dữ liệu công khai (CC BY 4.0)

Tải bằng trình duyệt (nút **Download All**), giải nén vào đúng thư mục:

| Bộ dữ liệu | Thư mục giải nén | Lớp dùng được |
|---|---|---|
| [High-Resolution Images of Lychee Plant Diseases](https://data.mendeley.com/datasets/52sstfpf5p) | `data/raw/mendeley_52sstfpf5p/` | Anthracnose, Algal Spot, Leaf Mites → Erinose, Dry → Other |
| [BDLitchi](https://data.mendeley.com/datasets/jhb24mszdk) | `data/raw/mendeley_bdlitchi/` | Healthy, Leaf Blight, Red Rust → Đốm rong, Burned/Dried/Insect/Mosaic → Other |
| [LitchiLeaf4001](https://data.mendeley.com/datasets/c3n2tc6jf4) | `data/raw/mendeley_litchileaf4001/` | Healthy, Anthrax → Anthracnose, Insect Hole/Dried/Mosaic → Other |
| [Lychee Leaf Disease Dataset](https://data.mendeley.com/datasets/jb7w4452pg) | `data/raw/mendeley_jb7w4452pg/` | Anthrax, Leaf Blight, Felt Leaf → Erinose, Healthy, Bituminous/Deficiency/Dry/Gall → Other |

- Script **tự bỏ** thư mục ảnh đã augment sẵn (`Augmented…`). Nếu không, ảnh xoay/lật của cùng một lá sẽ lọt vào cả train lẫn test và làm độ chính xác ảo.
- Lớp mơ hồ (Black Spot, White Spot, Fungal Stripe, Curl…) mặc định bị bỏ qua để tránh nhiễu nhãn. Muốn dùng thì sửa `dataset_sources.json`.
- Thư mục `data/` đã được thêm vào `.gitignore`.

## Bước 3 — Ảnh tự chụp ở Lục Ngạn (QUAN TRỌNG NHẤT)

Dữ liệu công khai được chụp ở Bangladesh, giống vải và điều kiện vườn khác Lục Ngạn, và **không có ảnh sương mai trên lá**.
Mô hình chỉ thực sự chuẩn khi có ảnh địa phương.

```
data/raw/luc_ngan/
  Healthy/        Anthracnose/   Downy_blight/   Leaf_blight/
  Algal_spot/     Erinose/       Other/
```

- Mục tiêu: **≥ 150 ảnh/lớp**, tối thiểu 40 ảnh (lớp ít hơn sẽ bị loại và tạm thời do Gemini xử lý).
- Chụp bằng chính điện thoại người dân hay dùng, ánh sáng tự nhiên, lá chiếm 60–80% khung, nhiều cây/vườn/ngày khác nhau.
- Nhện lông nhung: chụp **mặt dưới** lá. Sương mai: chụp lộc non, chùm hoa sau mưa phùn.
- Nhờ cán bộ BVTV xác nhận nhãn: nhãn sai làm mô hình học sai.
- Script ưu tiên đưa tối đa 50% ảnh Lục Ngạn vào **tập test**, để con số độ chính xác phản ánh đúng thực tế.

## Bước 4 — Chuẩn bị bộ dữ liệu

```bash
python ml/training/prepare_lychee_dataset.py --dry-run          # xem thống kê trước, chưa ghi ảnh
python ml/training/prepare_lychee_dataset.py --max-per-class 1500
```

Script sẽ: ánh xạ lớp → loại ảnh hỏng/nhỏ → khử trùng lặp (dHash + xác nhận ảnh 64×64) → chia 70/15/15 → xuất
`data/lychee_v1/{train,val,test}/<lớp>/`, kèm `manifest.csv` và `stats.json`. Đọc kỹ các dòng ⚠: thư mục không nhận ra lớp, lớp bị loại vì ít ảnh.
Mỗi lần thêm dữ liệu, xuất ra thư mục mới (`--out data/lychee_v2`) để không trộn các phiên bản.

## Bước 5 — Huấn luyện

```bash
python ml/training/train_lychee.py --data data/lychee_v1 --version lychee-v1
```

| Kiến trúc (`--arch`) | Kích thước file | Ghi chú |
|---|---|---|
| `efficientnet_b0` (mặc định) | ~16 MB | Nhẹ, chính xác tốt, chạy được trên Render free 512 MB |
| `resnet18` | ~45 MB | Tương thích kiến trúc cũ |
| `convnext_tiny` | ~110 MB | Thường chính xác hơn, nhưng nặng và chậm trên CPU miễn phí |

Thời gian ước lượng với khoảng 10 nghìn ảnh và 30 epoch: 30–60 phút trên GPU tầm RTX 3060, khoảng 1–1,5 giờ trên Colab T4.
Script tự dừng sớm khi macro-F1 trên tập val không tăng thêm.

Kết quả lưu trong `ml/hf-space/`:
- `lychee_model.pt`: checkpoint gồm kiến trúc, lớp, tiền xử lý, temperature và ngưỡng chấp nhận.
- `lychee_metrics.json`: accuracy, macro-F1, precision/recall từng lớp, ECE, lịch sử train. Dùng cho báo cáo KHKT.
- `lychee_confusion_matrix.png`: ma trận nhầm lẫn trên tập test.
- `lychee_misclassified.csv`: các ảnh đoán sai, xếp theo độ tự tin. **Xem file này đầu tiên** khi muốn cải thiện mô hình (thường do nhãn sai, ảnh mờ, hoặc thiếu ảnh của lớp đó).

**Ngưỡng chấp nhận**: script tìm ngưỡng tin cậy nhỏ nhất mà các ca vượt ngưỡng trên tập val đúng ≥ 95% (`--target-acc`).
Ca dưới ngưỡng được web chuyển sang Gemini kiểm tra chéo.

Kiểm tra nhanh:
```bash
python ml/training/predict_lychee.py --model ml/hf-space/lychee_model.pt data/raw/luc_ngan/Anthracnose
```

## Bước 6 — Đưa lên máy chủ

1. Tạo model repo trên Hugging Face (ví dụ `leaf-ai-lychee-model`) rồi upload:
   ```bash
   pip install -U huggingface_hub
   huggingface-cli login
   huggingface-cli upload <user>/leaf-ai-lychee-model ml/hf-space/lychee_model.pt lychee_model.pt
   ```
2. Vào Render, mở service `leaf-ai-engine`, chọn **Environment**, đặt
   `MODEL_DOWNLOAD_URL = https://huggingface.co/<user>/leaf-ai-lychee-model/resolve/main/lychee_model.pt`, rồi **Manual Deploy**.
3. Mở `https://leaf-ai-engine.onrender.com/health`, kiểm tra `"model_status": "ready"` và danh sách lớp là lớp vải.
4. Lên web, mở trang Quét lá: nhãn kết quả sẽ đổi thành **"Mô hình LEAF_AI efficientnet_b0"**.

Trước khi có mô hình mới, web vẫn chạy bằng Gemini Vision và ghi rõ nguồn kết quả. Không còn kết quả bịa.

## Google Colab (không có GPU)

```python
!git clone https://github.com/aifus02012008/leafAI.git /content/leafAI
# Upload data/raw/... lên Google Drive rồi:
from google.colab import drive; drive.mount('/content/drive')
!mkdir -p /content/leafAI/data && ln -s /content/drive/MyDrive/leafai_data/raw /content/leafAI/data/raw
%cd /content/leafAI
!pip -q install matplotlib
!python ml/training/prepare_lychee_dataset.py --max-per-class 1500
!python ml/training/train_lychee.py --data data/lychee_v1 --workers 2 --version lychee-v1
# Tải ml/hf-space/lychee_model.pt + lychee_metrics.json + lychee_confusion_matrix.png về máy
```

## Trích dẫn dữ liệu (bắt buộc với CC BY 4.0)

Ghi tên các bộ dữ liệu Mendeley ở bảng trên (tác giả, năm, DOI trên trang Mendeley) vào phần tài liệu tham khảo của báo cáo.
