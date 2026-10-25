# -*- coding: utf-8 -*-
"""
LEAF_AI — Huấn luyện mô hình nhận diện bệnh lá vải thiều (PyTorch, transfer learning).

Điểm chính để mô hình chạy CHUẨN ngoài vườn chứ không chỉ đẹp trên giấy:
  • Fine-tune 2 pha: đóng băng backbone vài epoch đầu (chỉ học lớp phân loại) rồi mở toàn bộ với LR thấp hơn.
  • Cân bằng lớp bằng WeightedRandomSampler (bộ dữ liệu vải lệch lớp mạnh).
  • Augment mô phỏng ảnh điện thoại ngoài vườn: cắt-phóng, xoay, đổi sáng/màu nhẹ, mờ nhẹ, che một phần.
    (Không đổi màu quá mạnh vì màu sắc là đặc trưng phân biệt đốm rong đỏ gạch / thán thư nâu.)
  • Label smoothing + AdamW + cosine warmup; AMP trên GPU; early stopping theo macro-F1 (không theo accuracy).
  • Hiệu chỉnh xác suất (temperature scaling) trên tập val → % tin cậy có ý nghĩa thật.
  • Tự tính ngưỡng chấp nhận: dưới ngưỡng thì app gắn cờ "chưa chắc chắn" và hỏi thêm Gemini (ca khó).
  • Đánh giá trên tập test với TTA (ảnh gốc + lật ngang): accuracy, macro-F1, từng lớp, ma trận nhầm lẫn,
    danh sách ảnh đoán sai để phân tích lỗi — dùng thẳng cho báo cáo KHKT.

Chạy (GPU tự nhận nếu có):
  python ml/training/train_lychee.py --data data/lychee_v1
  python ml/training/train_lychee.py --data data/lychee_v1 --arch resnet18 --epochs 40 --bs 48
"""

import argparse
import csv
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image
from torch.utils.data import DataLoader, WeightedRandomSampler
from torchvision import datasets
import torchvision.transforms as T

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "hf-space"))
from model_zoo import (ARCHS, DEFAULT_IMG_SIZE, IMAGENET_MEAN, IMAGENET_STD,  # noqa: E402
                       build_model, eval_transform, head_parameters)

CLASS_ORDER = ["Healthy", "Anthracnose", "Downy_blight", "Leaf_blight", "Algal_spot", "Erinose", "Other"]


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def set_seed(seed):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


# ---------------------------------------------------------------------------
# Dữ liệu
# ---------------------------------------------------------------------------
def train_transform(img_size):
    return T.Compose([
        T.RandomResizedCrop(img_size, scale=(0.45, 1.0), ratio=(0.75, 1.33)),
        T.RandomHorizontalFlip(),
        T.RandomVerticalFlip(p=0.2),
        T.RandomApply([T.RandomRotation(25)], p=0.5),
        T.ColorJitter(brightness=0.3, contrast=0.25, saturation=0.2, hue=0.02),
        T.RandomApply([T.GaussianBlur(kernel_size=5, sigma=(0.1, 1.6))], p=0.2),
        T.RandomGrayscale(p=0.02),
        T.ToTensor(),
        T.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        T.RandomErasing(p=0.2, scale=(0.02, 0.12), value="random"),
    ])


class OrderedImageFolder(datasets.ImageFolder):
    """ImageFolder nhưng giữ thứ tự lớp cố định theo CLASS_ORDER (ổn định giữa các lần train)."""

    def find_classes(self, directory):
        present = {p.name for p in Path(directory).iterdir() if p.is_dir()}
        classes = [c for c in CLASS_ORDER if c in present] + sorted(present - set(CLASS_ORDER))
        return classes, {c: i for i, c in enumerate(classes)}


def make_loaders(data_dir, img_size, bs, workers, balance):
    tr = OrderedImageFolder(data_dir / "train", transform=train_transform(img_size))
    ev_tf = eval_transform(img_size)
    va = OrderedImageFolder(data_dir / "val", transform=ev_tf)
    te = OrderedImageFolder(data_dir / "test", transform=ev_tf) if (data_dir / "test").exists() else None
    for ds, name in ((va, "val"), (te, "test")):
        if ds is not None and ds.classes != tr.classes:
            raise SystemExit(f"✗ Lớp của {name} {ds.classes} khác train {tr.classes}. Chạy lại prepare_lychee_dataset.py.")

    counts = np.bincount([y for _, y in tr.samples], minlength=len(tr.classes))
    sampler = None
    if balance == "sampler":
        w_cls = 1.0 / np.maximum(counts, 1)
        weights = [w_cls[y] for _, y in tr.samples]
        sampler = WeightedRandomSampler(weights, num_samples=len(weights), replacement=True)

    pin = torch.cuda.is_available()
    kw = dict(num_workers=workers, pin_memory=pin, persistent_workers=workers > 0)
    train_loader = DataLoader(tr, batch_size=bs, sampler=sampler, shuffle=sampler is None, drop_last=True, **kw)
    val_loader = DataLoader(va, batch_size=bs * 2, shuffle=False, **kw)
    test_loader = DataLoader(te, batch_size=bs * 2, shuffle=False, **kw) if te else None
    return tr, va, te, train_loader, val_loader, test_loader, counts


# ---------------------------------------------------------------------------
# Chỉ số đánh giá (không cần sklearn)
# ---------------------------------------------------------------------------
def confusion(y_true, y_pred, k):
    cm = np.zeros((k, k), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    return cm


def report(y_true, probs, classes):
    y_pred = probs.argmax(1)
    k = len(classes)
    cm = confusion(y_true, y_pred, k)
    per = {}
    f1s = []
    for i, c in enumerate(classes):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        per[c] = {"precision": round(100 * p, 2), "recall": round(100 * r, 2), "f1": round(100 * f1, 2), "support": int(cm[i].sum())}
        if cm[i].sum():
            f1s.append(f1)
    conf = probs.max(1)
    correct = (y_pred == y_true).astype(np.float64)
    # Expected Calibration Error (15 bins)
    bins = np.linspace(0, 1, 16)
    ece = 0.0
    for lo, hi in zip(bins[:-1], bins[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            ece += m.mean() * abs(correct[m].mean() - conf[m].mean())
    return {
        "accuracy": round(100 * correct.mean(), 2),
        "macro_f1": round(100 * float(np.mean(f1s)) if f1s else 0.0, 2),
        "ece": round(100 * ece, 2),
        "per_class": per,
        "confusion_matrix": cm.tolist(),
        "n": int(len(y_true)),
    }


@torch.no_grad()
def collect_logits(model, loader, device, tta=False):
    model.eval()
    all_logits, all_y = [], []
    for x, y in loader:
        x = x.to(device, non_blocking=True)
        with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
            logits = model(x).float()
            if tta:
                logits = (logits + model(torch.flip(x, dims=[3])).float()) / 2
        all_logits.append(logits.cpu())
        all_y.append(y)
    return torch.cat(all_logits), torch.cat(all_y)


def fit_temperature(logits, labels):
    """Temperature scaling (Guo et al. 2017): tìm T > 0 tối thiểu NLL trên tập val."""
    log_t = torch.zeros(1, requires_grad=True)
    opt = torch.optim.LBFGS([log_t], lr=0.05, max_iter=200)

    def closure():
        opt.zero_grad()
        loss = F.cross_entropy(logits / log_t.exp(), labels)
        loss.backward()
        return loss

    opt.step(closure)
    return float(log_t.detach().exp().clamp(0.5, 5.0))


def pick_accept_threshold(probs, labels, target_acc=0.95):
    """Ngưỡng tin cậy nhỏ nhất mà các ca vượt ngưỡng đạt độ chính xác ≥ target_acc."""
    conf = probs.max(1)
    correct = probs.argmax(1) == labels
    best = (0.9, float((conf >= 0.9).mean()), float(correct[conf >= 0.9].mean()) if (conf >= 0.9).any() else 0.0)
    for t in np.arange(0.30, 0.96, 0.01):
        m = conf >= t
        if m.sum() < 20:
            break
        acc = correct[m].mean()
        if acc >= target_acc:
            return round(float(t), 2), round(float(m.mean()), 4), round(float(acc), 4)
    return best


def save_confusion_png(cm, classes, path, title):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return False
    cm = np.array(cm)
    norm = cm / np.maximum(cm.sum(1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(1.2 * len(classes) + 2, 1.1 * len(classes) + 1.5))
    ax.imshow(norm, cmap="Greens", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes)), classes, rotation=35, ha="right")
    ax.set_yticks(range(len(classes)), classes)
    ax.set_xlabel("Dự đoán")
    ax.set_ylabel("Thực tế")
    ax.set_title(title)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, f"{cm[i, j]}\n{100 * norm[i, j]:.0f}%", ha="center", va="center",
                    color="white" if norm[i, j] > 0.6 else "#12301f", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
    return True


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Huấn luyện mô hình bệnh lá vải LEAF_AI")
    ap.add_argument("--data", default="data/lychee_v1")
    ap.add_argument("--arch", default="efficientnet_b0", choices=ARCHS)
    ap.add_argument("--img", type=int, default=0, help="kích thước ảnh (0 = theo kiến trúc)")
    ap.add_argument("--epochs", type=int, default=30)
    ap.add_argument("--freeze-epochs", type=int, default=2)
    ap.add_argument("--bs", type=int, default=32)
    ap.add_argument("--lr", type=float, default=1e-3, help="LR lớp phân loại; backbone dùng lr × --backbone-lr-mult")
    ap.add_argument("--backbone-lr-mult", type=float, default=0.3)
    ap.add_argument("--wd", type=float, default=1e-4)
    ap.add_argument("--label-smoothing", type=float, default=0.1)
    ap.add_argument("--balance", default="sampler", choices=["sampler", "weights", "none"])
    ap.add_argument("--patience", type=int, default=8)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--target-acc", type=float, default=0.95, help="độ chính xác mong muốn cho các ca vượt ngưỡng chấp nhận")
    ap.add_argument("--out", default="ml/hf-space/lychee_model.pt")
    ap.add_argument("--version", default="", help="nhãn phiên bản, vd lychee-v1")
    ap.add_argument("--cpu", action="store_true")
    ap.add_argument("--no-pretrained", action="store_true", help="không tải trọng số ImageNet (chỉ dùng để thử pipeline)")
    args = ap.parse_args()

    set_seed(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() and not args.cpu else "cpu")
    log(f"Thiết bị: {device}" + (f" ({torch.cuda.get_device_name(0)})" if device.type == "cuda" else " — không có GPU, sẽ chậm; cân nhắc Google Colab"))
    if device.type == "cuda":
        torch.backends.cudnn.benchmark = True

    data_dir = (ROOT / args.data).resolve()
    if not (data_dir / "train").exists():
        raise SystemExit(f"✗ Không thấy {data_dir}/train. Chạy prepare_lychee_dataset.py trước.")
    img_size = args.img or DEFAULT_IMG_SIZE[args.arch]

    tr, va, te, train_loader, val_loader, test_loader, counts = make_loaders(data_dir, img_size, args.bs, args.workers, args.balance)
    classes = tr.classes
    log(f"Lớp ({len(classes)}): " + ", ".join(f"{c}={n}" for c, n in zip(classes, counts)))
    log(f"Ảnh: train={len(tr)} val={len(va)} test={len(te) if te else 0}")

    model = build_model(args.arch, len(classes), pretrained=not args.no_pretrained).to(device)
    head = set(id(p) for p in head_parameters(model, args.arch))
    backbone_params = [p for p in model.parameters() if id(p) not in head]
    head_params = [p for p in model.parameters() if id(p) in head]

    cls_weights = None
    if args.balance == "weights":
        w = counts.sum() / np.maximum(counts, 1) / len(counts)
        cls_weights = torch.tensor(w, dtype=torch.float32, device=device)
    criterion = nn.CrossEntropyLoss(weight=cls_weights, label_smoothing=args.label_smoothing)

    optimizer = torch.optim.AdamW([
        {"params": backbone_params, "lr": args.lr * args.backbone_lr_mult},
        {"params": head_params, "lr": args.lr},
    ], weight_decay=args.wd)
    base_lrs = [g["lr"] for g in optimizer.param_groups]
    steps_per_epoch = len(train_loader)
    total_steps = args.epochs * steps_per_epoch
    warmup = steps_per_epoch

    def lr_at(step):
        if step < warmup:
            return (step + 1) / warmup
        prog = (step - warmup) / max(1, total_steps - warmup)
        return 0.02 + 0.98 * 0.5 * (1 + math.cos(math.pi * prog))

    scaler = torch.amp.GradScaler("cuda", enabled=device.type == "cuda")
    out_path = (ROOT / args.out).resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_best = out_path.with_suffix(".best_tmp.pt")

    history, best_f1, best_epoch, bad_epochs, step = [], -1.0, 0, 0, 0
    t_start = time.time()
    for epoch in range(1, args.epochs + 1):
        frozen = epoch <= args.freeze_epochs
        for p in backbone_params:
            p.requires_grad_(not frozen)
        model.train()
        t0, run_loss, run_ok, seen = time.time(), 0.0, 0, 0
        for x, y in train_loader:
            for g, base in zip(optimizer.param_groups, base_lrs):
                g["lr"] = base * lr_at(step)
            x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=device.type, enabled=device.type == "cuda"):
                logits = model(x)
                loss = criterion(logits, y)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            scaler.step(optimizer)
            scaler.update()
            step += 1
            run_loss += loss.item() * x.size(0)
            run_ok += (logits.argmax(1) == y).sum().item()
            seen += x.size(0)

        vl, vy = collect_logits(model, val_loader, device)
        vrep = report(vy.numpy(), F.softmax(vl, 1).numpy(), classes)
        val_loss = F.cross_entropy(vl, vy).item()
        rec = {
            "epoch": epoch, "frozen_backbone": frozen,
            "train_loss": round(run_loss / seen, 4), "train_acc": round(100 * run_ok / seen, 2),
            "val_loss": round(val_loss, 4), "val_acc": vrep["accuracy"], "val_macro_f1": vrep["macro_f1"],
            "lr": round(optimizer.param_groups[1]["lr"], 6), "sec": round(time.time() - t0, 1),
        }
        history.append(rec)
        flag = ""
        if vrep["macro_f1"] > best_f1:
            best_f1, best_epoch, bad_epochs = vrep["macro_f1"], epoch, 0
            torch.save(model.state_dict(), tmp_best)
            flag = "  ★ tốt nhất"
        else:
            bad_epochs += 1
        log(f"Epoch {epoch:>2}/{args.epochs} {'[đóng băng] ' if frozen else ''}loss {rec['train_loss']:.3f} acc {rec['train_acc']:.1f}% | "
            f"val loss {val_loss:.3f} acc {vrep['accuracy']:.1f}% F1 {vrep['macro_f1']:.1f}% | {rec['sec']}s{flag}")
        if bad_epochs >= args.patience and epoch > args.freeze_epochs:
            log(f"Dừng sớm: {args.patience} epoch liền macro-F1 không cải thiện.")
            break

    log(f"Huấn luyện xong trong {(time.time() - t_start) / 60:.1f} phút. Epoch tốt nhất: {best_epoch} (val macro-F1 {best_f1}%)")
    model.load_state_dict(torch.load(tmp_best, map_location=device))

    # ---- Hiệu chỉnh xác suất & ngưỡng chấp nhận (trên val, có TTA giống lúc chạy thật) ----
    vl, vy = collect_logits(model, val_loader, device, tta=True)
    temperature = fit_temperature(vl, vy)
    vprobs = F.softmax(vl / temperature, 1).numpy()
    thr, coverage, acc_at = pick_accept_threshold(vprobs, vy.numpy(), args.target_acc)
    val_report = report(vy.numpy(), vprobs, classes)
    log(f"Temperature = {temperature:.3f} | ngưỡng chấp nhận = {thr} (phủ {100 * coverage:.1f}% ca val, đúng {100 * acc_at:.1f}%)")

    # ---- Đánh giá test ----
    test_report, misclassified = None, []
    if test_loader:
        tl, ty = collect_logits(model, test_loader, device, tta=True)
        tprobs = F.softmax(tl / temperature, 1).numpy()
        test_report = report(ty.numpy(), tprobs, classes)
        conf = tprobs.max(1)
        acc_mask = conf >= thr
        test_report["accept_threshold_coverage"] = round(100 * float(acc_mask.mean()), 2)
        test_report["accuracy_above_threshold"] = round(100 * float((tprobs.argmax(1) == ty.numpy())[acc_mask].mean()), 2) if acc_mask.any() else None
        for (path, y), p in zip(te.samples, tprobs):
            if p.argmax() != y:
                misclassified.append({"file": str(Path(path).relative_to(data_dir)).replace("\\", "/"), "true": classes[y],
                                      "pred": classes[int(p.argmax())], "confidence": round(100 * float(p.max()), 1)})
        log(f"TEST: accuracy {test_report['accuracy']}% | macro-F1 {test_report['macro_f1']}% | ECE {test_report['ece']}% | "
            f"vượt ngưỡng {test_report['accept_threshold_coverage']}% ca, đúng {test_report['accuracy_above_threshold']}%")
        for c, m in test_report["per_class"].items():
            log(f"   {c:<14} P {m['precision']:>6}%  R {m['recall']:>6}%  F1 {m['f1']:>6}%  (n={m['support']})")

    # ---- Lưu checkpoint + báo cáo ----
    stats_file = data_dir / "stats.json"
    version = args.version or f"lychee-{time.strftime('%Y%m%d')}"
    ckpt = {
        "format": "leafai-lychee-v1",
        "crop": "lychee",
        "version": version,
        "arch": args.arch,
        "classes": classes,
        "img_size": img_size,
        "eval_resize": int(round(img_size * 1.07)),
        "mean": IMAGENET_MEAN,
        "std": IMAGENET_STD,
        "temperature": temperature,
        "accept_threshold": thr,
        "tta": True,
        "best_epoch": best_epoch,
        "best_acc": test_report["accuracy"] if test_report else val_report["accuracy"],
        "metrics": {"val": {k: v for k, v in val_report.items() if k != "confusion_matrix"},
                    "test": {k: v for k, v in test_report.items() if k != "confusion_matrix"} if test_report else None},
        "dataset": json.loads(stats_file.read_text(encoding="utf-8")) if stats_file.exists() else {"path": str(data_dir)},
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_state_dict": {k: v.cpu() for k, v in model.state_dict().items()},
    }
    torch.save(ckpt, out_path)
    tmp_best.unlink(missing_ok=True)

    out_dir = out_path.parent
    metrics = {k: v for k, v in ckpt.items() if k not in ("model_state_dict",)}
    metrics["val_full"] = val_report
    metrics["test_full"] = test_report
    metrics["history"] = history
    metrics["args"] = vars(args)
    (out_dir / "lychee_metrics.json").write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")
    if misclassified:
        with open(out_dir / "lychee_misclassified.csv", "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(misclassified[0].keys()))
            w.writeheader()
            w.writerows(sorted(misclassified, key=lambda r: -r["confidence"]))
    if test_report and save_confusion_png(test_report["confusion_matrix"], classes, out_dir / "lychee_confusion_matrix.png",
                                          f"LEAF_AI {args.arch} — test acc {test_report['accuracy']}% / macro-F1 {test_report['macro_f1']}%"):
        log(f"Đã lưu ma trận nhầm lẫn: {out_dir / 'lychee_confusion_matrix.png'}")

    size_mb = out_path.stat().st_size / 1e6
    log(f"✓ Đã lưu mô hình: {out_path} ({size_mb:.1f} MB) — phiên bản {version}")
    log("  Kiểm tra nhanh: python ml/training/predict_lychee.py --model " + args.out + " <ảnh.jpg>")


if __name__ == "__main__":
    main()
