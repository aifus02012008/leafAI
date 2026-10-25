---
title: LEAF AI Lychee Leaf Disease Engine
emoji: 🍃
colorFrom: green
colorTo: emerald
sdk: docker
app_port: 7860
pinned: false
license: mit
language:
- vi
- en
tags:
- agriculture
- lychee
- litchi
- plant-disease
- computer-vision
- resnet18
- grad-cam
- leaf-ai
metrics:
- accuracy
---

# LEAF_AI — Lychee Leaf Disease Engine

Máy chủ suy luận bệnh lá vải thiều Lục Ngạn: CNN fine-tune trên ảnh lá vải (`model_zoo.py`, `inference.py`) + Grad-CAM,
cờ `uncertain` cho ca khó (frontend chuyển sang Gemini Vision), và phác đồ IPM (`treatment.py`).

- Huấn luyện: xem `ml/training/README_TRAIN.md`
- Biến môi trường: `MODEL_DOWNLOAD_URL` (checkpoint `lychee_model.pt`), `MODEL_PATH`, `TORCH_THREADS`
- API: `GET /health` · `POST /predict_with_gradcam {"data": "data:image/jpeg;base64,..."}` · `POST /treatment/plan`
- Checkpoint cà chua cũ bị từ chối (`model_status: wrong_model`); chưa có mô hình → HTTP 503 (không trả kết quả giả).
