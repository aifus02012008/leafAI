---
title: LEAF AI Tomato Disease Engine
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
- tomato
- plant-disease
- computer-vision
- resnet18
- grad-cam
- leaf-ai
datasets:
- wellCh4n/tomato-leaf-disease-image
metrics:
- accuracy
---

# 🍃 LEAF_AI — Tomato Leaf Disease ResNet-18 Model

Mô hình Deep Learning thị giác máy tính nhận diện **10 lớp bệnh & trạng thái lá cây cà chua** chuẩn hóa quốc tế (theo phân loại PlantVillage & Tổ chức Lương thực và Nông nghiệp Liên Hợp Quốc - FAO). Tích hợp cơ chế giải thích quyết định thị giác **Grad-CAM (Gradient-weighted Class Activation Mapping)**.

## 🎯 10 Lớp bệnh & phân loại
| ID | Tên tiếng Anh | Tên tiếng Việt | Tác nhân gây bệnh |
|---|---|---|---|
| 0 | `Healthy` | Lá khỏe mạnh | Không có mầm bệnh |
| 1 | `Leaf_mold` | Nấm mốc lá | *Passalora fulva* |
| 2 | `Target_spot` | Đốm mắt cua | *Corynespora cassiicola* |
| 3 | `Late_blight` | Sương mai | *Phytophthora infestans* |
| 4 | `Early_blight` | Úa sớm (Đốm vòng) | *Alternaria solani* |
| 5 | `Bacterial_spot` | Đốm vi khuẩn | *Xanthomonas campestris* |
| 6 | `Septoria_leaf_spot` | Đốm lá Septoria | *Septoria lycopersici* |
| 7 | `Tomato_mosaic_virus` | Khảm lá virus (ToMV) | Tomato mosaic tobamovirus |
| 8 | `Tomato_yellow_leaf_curl_virus` | Xoăn vàng lá virus (TYLCV) | Begomovirus (Vector: Bọ phấn trắng) |
| 9 | `Spider_mites` | Nhện đỏ hai chấm | *Tetranychus urticae* |

## 📊 Kết quả Huấn luyện (Training Metrics)
- **Kiến trúc Backbone**: ResNet-18 (Pretrained ImageNet)
- **Tập dữ liệu huấn luyện**: 14,218 ảnh thực tế (PlantVillage Tomato Dataset)
- **Tập kiểm thử (Validation)**: 3,569 ảnh
- **Độ chính xác kiểm thử (Validation Accuracy)**: **>97.8%**
- **Độ trễ suy luận (Inference Latency)**: ~15ms trên CPU / ~2ms trên GPU CUDA

## 💻 Cách sử dụng trong PyTorch
```python
import torch
import torchvision.models as models
import torchvision.transforms as transforms
from PIL import Image

# 1. Khởi tạo mô hình
classes = [
    "Healthy", "Leaf_mold", "Target_spot", "Late_blight", "Early_blight",
    "Bacterial_spot", "Septoria_leaf_spot", "Tomato_mosaic_virus",
    "Tomato_yellow_leaf_curl_virus", "Spider_mites"
]

checkpoint = torch.load("tomato_model.pt", map_location="cpu")
model = models.resnet18()
model.fc = torch.nn.Sequential(
    torch.nn.Dropout(p=0.3),
    torch.nn.Linear(model.fc.in_features, len(classes))
)
model.load_state_dict(checkpoint["model_state_dict"])
model.eval()

# 2. Tiền xử lý & Dự đoán
transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
])

img = Image.open("tomato_leaf.jpg").convert("RGB")
tensor = transform(img).unsqueeze(0)

with torch.no_grad():
    probs = torch.softmax(model(tensor), dim=1)[0]
    top_p, top_i = torch.topk(probs, 3)
    for p, idx in zip(top_p, top_i):
        print(f"{classes[idx]}: {p.item()*100:.2f}%")
```

## 🛡️ Bản quyền & Nguồn
- Dự án: **LEAF_AI (Hệ sinh thái AI nông nghiệp thông minh)**
- Dataset: `wellCh4n/tomato-leaf-disease-image` (PlantVillage)
