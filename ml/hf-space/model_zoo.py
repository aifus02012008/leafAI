# -*- coding: utf-8 -*-
"""
LEAF_AI — Định nghĩa kiến trúc mô hình dùng CHUNG cho huấn luyện (ml/training) và máy chủ suy luận (app.py).
Giữ một nguồn duy nhất để checkpoint lưu ra luôn nạp lại đúng cấu trúc.
"""
from typing import List

import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as T

IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]

# Kích thước ảnh khuyến nghị theo kiến trúc
DEFAULT_IMG_SIZE = {
    "resnet18": 224,
    "resnet50": 224,
    "efficientnet_b0": 224,
    "efficientnet_b2": 260,
    "convnext_tiny": 224,
    "mobilenet_v3_large": 224,
}
ARCHS = list(DEFAULT_IMG_SIZE)


def _weights(name: str, pretrained: bool):
    if not pretrained:
        return None
    return {
        "resnet18": models.ResNet18_Weights.DEFAULT,
        "resnet50": models.ResNet50_Weights.DEFAULT,
        "efficientnet_b0": models.EfficientNet_B0_Weights.DEFAULT,
        "efficientnet_b2": models.EfficientNet_B2_Weights.DEFAULT,
        "convnext_tiny": models.ConvNeXt_Tiny_Weights.DEFAULT,
        "mobilenet_v3_large": models.MobileNet_V3_Large_Weights.DEFAULT,
    }[name]


def build_model(arch: str, num_classes: int, pretrained: bool = False, dropout: float = 0.3) -> nn.Module:
    if arch not in DEFAULT_IMG_SIZE:
        raise ValueError(f"Kiến trúc không hỗ trợ: {arch}. Chọn một trong {ARCHS}")
    m = getattr(models, arch)(weights=_weights(arch, pretrained))
    if arch.startswith("resnet"):
        m.fc = nn.Sequential(nn.Dropout(p=dropout), nn.Linear(m.fc.in_features, num_classes))
    elif arch.startswith("efficientnet"):
        m.classifier = nn.Sequential(nn.Dropout(p=dropout), nn.Linear(m.classifier[1].in_features, num_classes))
    elif arch == "convnext_tiny":
        m.classifier[2] = nn.Linear(m.classifier[2].in_features, num_classes)
    elif arch == "mobilenet_v3_large":
        m.classifier[3] = nn.Linear(m.classifier[3].in_features, num_classes)
    return m


def head_parameters(model: nn.Module, arch: str) -> List[nn.Parameter]:
    head = model.fc if arch.startswith("resnet") else model.classifier
    return list(head.parameters())


def gradcam_layer(model: nn.Module, arch: str) -> nn.Module:
    """Tầng tích chập cuối cùng để trích Grad-CAM."""
    if arch.startswith("resnet"):
        return model.layer4[-1]
    return model.features[-1]


def eval_transform(img_size: int, eval_resize: int = None, mean=None, std=None):
    """Tiền xử lý lúc đánh giá/suy luận — PHẢI giống hệt nhau giữa train và app."""
    eval_resize = eval_resize or int(round(img_size * 1.07))
    return T.Compose([
        T.Resize(eval_resize),
        T.CenterCrop(img_size),
        T.ToTensor(),
        T.Normalize(mean or IMAGENET_MEAN, std or IMAGENET_STD),
    ])
