# -*- coding: utf-8 -*-
"""
Đánh giá mô hình LEAF_AI (ResNet-18) trên tập validation để lấy số liệu thật cho báo cáo.

Kết quả:
  - Phân bố số ảnh theo nhãn trong tập validation (kiểm tra thứ tự nhãn có khớp CLASSES không)
  - Ma trận nhầm lẫn 10x10, Precision / Recall / F1 từng lớp, Macro average, Accuracy
  - Thời gian suy luận trên CPU (batch = 1) của máy đang chạy script

Chạy (cùng môi trường đã dùng để huấn luyện, dataset đã có trong cache Hugging Face):
    python ml/training/evaluate.py
Kết quả được ghi vào ml/hf-space/evaluation_metrics.json
"""

import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torchvision.models as models
import torchvision.transforms as transforms
from torch.utils.data import DataLoader

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train import CLASSES, ParquetTomatoDataset, get_dataset_paths  # noqa: E402

HF_SPACE_DIR = Path(__file__).resolve().parents[1] / "hf-space"
MODEL_PATH = HF_SPACE_DIR / "tomato_model.pt"
OUT_PATH = HF_SPACE_DIR / "evaluation_metrics.json"


def load_model(device):
    ckpt = torch.load(MODEL_PATH, map_location=device)
    model = models.resnet18(weights=None)
    model.fc = nn.Sequential(nn.Dropout(p=0.3), nn.Linear(model.fc.in_features, len(CLASSES)))
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()
    return model, ckpt


@torch.no_grad()
def predict_all(model, loader, device):
    y_true, y_pred = [], []
    for images, labels in loader:
        out = model(images.to(device))
        y_pred.extend(out.argmax(1).cpu().tolist())
        y_true.extend(labels.tolist())
    return np.array(y_true), np.array(y_pred)


@torch.no_grad()
def cpu_latency_ms(model, dataset, n=100, warmup=10):
    model_cpu = model.to("cpu").eval()
    times = []
    for i in range(min(n + warmup, len(dataset))):
        x, _ = dataset[i]
        t0 = time.perf_counter()
        model_cpu(x.unsqueeze(0))
        if i >= warmup:
            times.append((time.perf_counter() - t0) * 1000)
    return float(np.mean(times)), float(np.std(times))


def main():
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    _, val_path = get_dataset_paths()
    tf = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    ds = ParquetTomatoDataset(val_path, transform=tf)

    # 1. Phân bố nhãn — nếu có nhãn trống hoặc nhãn >= 10 thì thứ tự CLASSES không khớp dataset
    counts = np.bincount(np.array(ds.labels), minlength=len(CLASSES))
    print("\nSố ảnh theo nhãn trong tập validation:")
    for i, c in enumerate(counts):
        name = CLASSES[i] if i < len(CLASSES) else f"<nhãn lạ {i}>"
        print(f"  {i:>2} {name:<32} {c}")

    model, ckpt = load_model(device)
    loader = DataLoader(ds, batch_size=64, shuffle=False, num_workers=0)
    y_true, y_pred = predict_all(model, loader, device)

    k = len(CLASSES)
    cm = np.zeros((k, k), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1

    tp = np.diag(cm).astype(float)
    fp = cm.sum(0) - tp
    fn = cm.sum(1) - tp
    with np.errstate(divide="ignore", invalid="ignore"):
        precision = np.where(tp + fp > 0, tp / (tp + fp), 0.0)
        recall = np.where(tp + fn > 0, tp / (tp + fn), 0.0)
        f1 = np.where(precision + recall > 0, 2 * precision * recall / (precision + recall), 0.0)
    present = cm.sum(1) > 0  # chỉ lấy trung bình trên các lớp có ảnh
    accuracy = tp.sum() / cm.sum()

    print(f"\nAccuracy: {accuracy * 100:.2f}%  ({int(tp.sum())}/{int(cm.sum())} ảnh đúng)")
    print("\n| Lớp | Số ảnh | Đúng | Precision | Recall | F1 |")
    print("|---|---|---|---|---|---|")
    for i, name in enumerate(CLASSES):
        print(f"| {name} | {cm[i].sum()} | {int(tp[i])} | {precision[i] * 100:.1f}% | {recall[i] * 100:.1f}% | {f1[i] * 100:.1f}% |")
    print(f"| Macro avg | {cm.sum()} | {int(tp.sum())} | {precision[present].mean() * 100:.2f}% | "
          f"{recall[present].mean() * 100:.2f}% | {f1[present].mean() * 100:.2f}% |")

    print("\nMa trận nhầm lẫn (hàng = nhãn thật, cột = dự đoán):")
    print(cm)

    lat_mean, lat_std = cpu_latency_ms(model, ds)
    print(f"\nThời gian suy luận CPU (batch=1): {lat_mean:.1f} ± {lat_std:.1f} ms/ảnh")

    OUT_PATH.write_text(json.dumps({
        "checkpoint_epoch": ckpt.get("epoch"),
        "n_val": int(cm.sum()),
        "label_counts": counts.tolist(),
        "accuracy": round(float(accuracy) * 100, 2),
        "per_class": {
            name: {
                "support": int(cm[i].sum()), "tp": int(tp[i]),
                "precision": round(float(precision[i]) * 100, 2),
                "recall": round(float(recall[i]) * 100, 2),
                "f1": round(float(f1[i]) * 100, 2),
            } for i, name in enumerate(CLASSES)
        },
        "macro_avg": {
            "precision": round(float(precision[present].mean()) * 100, 2),
            "recall": round(float(recall[present].mean()) * 100, 2),
            "f1": round(float(f1[present].mean()) * 100, 2),
        },
        "confusion_matrix": cm.tolist(),
        "cpu_latency_ms": {"mean": round(lat_mean, 1), "std": round(lat_std, 1)},
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nĐã ghi {OUT_PATH}")


if __name__ == "__main__":
    main()
