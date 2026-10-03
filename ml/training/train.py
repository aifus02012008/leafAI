# -*- coding: utf-8 -*-
"""
LEAF_AI - Tomato Leaf Disease Model Training Script
Trains ResNet18 on 14,218 PlantVillage tomato leaf disease images using PyTorch + CUDA.
Exports weights to ml/hf-space/tomato_model.pt for production deployment.
"""

import os
import sys
import io
import time
import json
import logging
from pathlib import Path

if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

import pyarrow.parquet as pq
from PIL import Image
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
import torchvision.models as models
from torchvision.models import ResNet18_Weights
import torchvision.transforms as transforms

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("train_tomato_model")

# 10 Lớp bệnh & lá cà chua chuẩn hóa từ PlantVillage Dataset
CLASSES = [
    "Healthy",                           # 0: Lá khỏe mạnh
    "Leaf_mold",                         # 1: Nấm mốc lá (Passalora fulva)
    "Target_spot",                       # 2: Đốm mắt cua (Corynespora cassiicola)
    "Late_blight",                       # 3: Sương mai (Phytophthora infestans)
    "Early_blight",                      # 4: Úa sớm (Alternaria solani)
    "Bacterial_spot",                    # 5: Đốm vi khuẩn (Xanthomonas campestris)
    "Septoria_leaf_spot",                # 6: Đốm lá Septoria (Septoria lycopersici)
    "Tomato_mosaic_virus",               # 7: Khảm lá virus (ToMV)
    "Tomato_yellow_leaf_curl_virus",     # 8: Xoăn vàng lá virus (TYLCV)
    "Spider_mites",                      # 9: Nhện đỏ hai chấm (Tetranychus urticae)
]

CLASS_TO_IDX = {cls_name: i for i, cls_name in enumerate(CLASSES)}


class ParquetTomatoDataset(Dataset):
    """Dataset đọc trực tiếp từ bảng Parquet lưu trong bộ nhớ RAM cực nhanh."""
    def __init__(self, parquet_path: str, transform=None):
        self.transform = transform
        logger.info(f"Đang nạp file parquet vào bộ nhớ RAM: {parquet_path}")
        t0 = time.time()
        table = pq.read_table(parquet_path, columns=['image', 'label'])
        self.images = table['image']
        self.labels = table['label'].to_pylist()
        self.length = len(self.labels)
        logger.info(f"Nạp hoàn tất {self.length} ảnh trong {time.time()-t0:.2f}s")

    def __len__(self):
        return self.length

    def __getitem__(self, idx):
        raw_bytes = self.images[idx].as_py()['bytes']
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
        label = self.labels[idx]

        if self.transform:
            img = self.transform(img)

        return img, label


def get_dataset_paths():
    """Tìm đường dẫn tệp parquet trong Hugging Face cache."""
    cache_base = Path(os.path.expanduser("~/.cache/huggingface/hub"))
    repo_dirs = list(cache_base.glob("datasets--wellCh4n--tomato-leaf-disease-image/snapshots/*"))
    if not repo_dirs:
        raise FileNotFoundError("Không tìm thấy snapshot dataset wellCh4n/tomato-leaf-disease-image trong cache!")

    snapshot_dir = repo_dirs[0]
    train_path = snapshot_dir / "data" / "train-00000-of-00001.parquet"
    val_path = snapshot_dir / "data" / "validation-00000-of-00001.parquet"

    if not train_path.exists():
        raise FileNotFoundError(f"Không tìm thấy train parquet tại {train_path}")
    if not val_path.exists():
        raise FileNotFoundError(f"Không tìm thấy val parquet tại {val_path}")

    return str(train_path), str(val_path)


def train_model(epochs: int = 5, batch_size: int = 64, lr: float = 5e-4):
    device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
    logger.info(f"Thiết bị huấn luyện: {device} ({torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'})")

    train_path, val_path = get_dataset_paths()

    # Data Augmentations
    train_transform = transforms.Compose([
        transforms.Resize((240, 240)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(p=0.5),
        transforms.RandomVerticalFlip(p=0.2),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.15, contrast=0.15, saturation=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    val_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    train_dataset = ParquetTomatoDataset(train_path, transform=train_transform)
    val_dataset = ParquetTomatoDataset(val_path, transform=val_transform)

    train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False, num_workers=0, pin_memory=True)

    # Khởi tạo ResNet18 Pretrained ImageNet
    logger.info("Khởi tạo mạng ResNet18 Pretrained...")
    model = models.resnet18(weights=ResNet18_Weights.DEFAULT)
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Dropout(p=0.3),
        nn.Linear(in_features, len(CLASSES))
    )
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_acc = 0.0
    output_dir = Path(__file__).resolve().parents[1] / "hf-space"
    output_dir.mkdir(parents=True, exist_ok=True)
    model_save_path = output_dir / "tomato_model.pt"

    history = []

    logger.info(f"Bắt đầu huấn luyện {epochs} Epochs trên tập dữ liệu {len(train_dataset)} mẫu...")

    total_start = time.time()
    for epoch in range(1, epochs + 1):
        epoch_start = time.time()
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for step, (images, labels) in enumerate(train_loader):
            images = images.to(device, non_blocking=True)
            labels = labels.to(device, non_blocking=True)

            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * images.size(0)
            _, preds = torch.max(outputs, 1)
            correct += torch.sum(preds == labels.data).item()
            total += labels.size(0)

            if (step + 1) % 50 == 0 or (step + 1) == len(train_loader):
                logger.info(f"Epoch [{epoch}/{epochs}] Step [{step+1}/{len(train_loader)}] "
                            f"Loss: {running_loss/total:.4f} Acc: {100.0*correct/total:.2f}%")

        train_loss = running_loss / total
        train_acc = 100.0 * correct / total

        # Validation phase
        model.eval()
        val_loss = 0.0
        val_correct = 0
        val_total = 0

        with torch.no_grad():
            for images, labels in val_loader:
                images = images.to(device, non_blocking=True)
                labels = labels.to(device, non_blocking=True)
                outputs = model(images)
                loss = criterion(outputs, labels)

                val_loss += loss.item() * images.size(0)
                _, preds = torch.max(outputs, 1)
                val_correct += torch.sum(preds == labels.data).item()
                val_total += labels.size(0)

        val_loss = val_loss / val_total
        val_acc = 100.0 * val_correct / val_total
        epoch_time = time.time() - epoch_start

        logger.info(f"Epoch {epoch}/{epochs} HOAN TAT ({epoch_time:.1f}s) - "
                    f"Train Loss: {train_loss:.4f} | Train Acc: {train_acc:.2f}% | "
                    f"Val Loss: {val_loss:.4f} | Val Acc: {val_acc:.2f}%")

        scheduler.step()

        history.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 4),
            "train_acc": round(train_acc, 2),
            "val_loss": round(val_loss, 4),
            "val_acc": round(val_acc, 2),
            "time_s": round(epoch_time, 1)
        })

        if val_acc > best_acc:
            best_acc = val_acc
            logger.info(f"Kỷ lục mới! Lưu trọng số tốt nhất ({best_acc:.2f}%) vào {model_save_path}")
            torch.save({
                "epoch": epoch,
                "model_state_dict": model.state_dict(),
                "optimizer_state_dict": optimizer.state_dict(),
                "best_acc": best_acc,
                "classes": CLASSES,
                "arch": "resnet18",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }, model_save_path)

    total_time = time.time() - total_start
    logger.info(f"HUAN LUYEN HOAN TAT trong {total_time:.1f}s! Do chinh xac cao nhat: {best_acc:.2f}%")

    # Lưu metrics file
    metrics_path = output_dir / "training_metrics.json"
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump({
            "arch": "resnet18",
            "epochs": epochs,
            "best_acc": round(best_acc, 2),
            "total_training_time_s": round(total_time, 1),
            "classes": CLASSES,
            "history": history
        }, f, indent=2, ensure_ascii=False)
    logger.info(f"Da ghi file chi so tai: {metrics_path}")

    return best_acc


if __name__ == "__main__":
    epochs = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    batch_size = int(sys.argv[2]) if len(sys.argv) > 2 else 64
    train_model(epochs=epochs, batch_size=batch_size)
