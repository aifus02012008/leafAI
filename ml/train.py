"""Train a per-crop LEAF_AI leaf-disease model and export it for the backend.

Usage (from the repo root):
    backend/.venv/Scripts/python.exe ml/train.py ml/configs/durian.yaml

Outputs:
    model/<crop>.pt                  weights loaded by backend/app/services/model_registry.py
    model/<crop>.labels_map.json     class index -> raw label, plus test metrics
    ml/runs/<crop>/                  Ultralytics run folder (curves, confusion matrix)
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: Path) -> dict:
    cfg = yaml.safe_load(path.read_text(encoding="utf-8"))
    required = {"crop", "task", "data", "base_model", "imgsz", "epochs", "output"}
    missing = required - cfg.keys()
    if missing:
        raise ValueError(f"Config {path} is missing keys: {sorted(missing)}")
    if cfg["task"] != "classify":
        raise ValueError("Only task=classify is supported (datasets are folder-per-class).")
    return cfg


def check_dataset(data_dir: Path) -> dict[str, dict[str, int]]:
    """Return per-split, per-class image counts; fail fast on an unusable layout."""
    counts: dict[str, dict[str, int]] = {}
    for split in ("train", "val", "test"):
        split_dir = data_dir / split
        if not split_dir.is_dir():
            raise FileNotFoundError(f"Missing split folder: {split_dir}")
        counts[split] = {c.name: sum(1 for _ in c.glob("*.jpg")) for c in sorted(split_dir.iterdir()) if c.is_dir()}
    classes = [set(v) for v in counts.values()]
    if not all(c == classes[0] for c in classes):
        raise ValueError(f"Class folders differ between splits: {counts}")
    return counts


def per_class_report(model, test_dir: Path, names: dict[int, str], imgsz: int) -> dict:
    """Accuracy, macro-F1 and per-class precision/recall/F1 on the held-out test split."""
    index = {v: k for k, v in names.items()}
    n = len(names)
    confusion = [[0] * n for _ in range(n)]
    for class_dir in sorted(p for p in test_dir.iterdir() if p.is_dir()):
        images = sorted(class_dir.glob("*.jpg"))
        for start in range(0, len(images), 64):
            for res in model.predict([str(p) for p in images[start:start + 64]], imgsz=imgsz, verbose=False):
                confusion[index[class_dir.name]][int(res.probs.top1)] += 1
    total = sum(map(sum, confusion))
    correct = sum(confusion[i][i] for i in range(n))
    per_class = {}
    for i in range(n):
        tp = confusion[i][i]
        fp = sum(confusion[r][i] for r in range(n)) - tp
        fn = sum(confusion[i]) - tp
        p = tp / (tp + fp) if tp + fp else 0.0
        r = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * p * r / (p + r) if p + r else 0.0
        per_class[names[i]] = {"precision": round(p, 4), "recall": round(r, 4), "f1": round(f1, 4), "support": sum(confusion[i])}
    return {
        "accuracy": round(correct / total, 4) if total else 0.0,
        "macro_f1": round(sum(c["f1"] for c in per_class.values()) / n, 4),
        "per_class": per_class,
        "confusion": {"labels": [names[i] for i in range(n)], "matrix": confusion},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("config", type=Path)
    parser.add_argument("--epochs", type=int, help="override epochs (e.g. 1 for a smoke run)")
    parser.add_argument("--device", default=None, help="'0' for first GPU, 'cpu' to force CPU")
    args = parser.parse_args()

    from ultralytics import YOLO  # heavy import, keep after arg parsing

    cfg = load_config(args.config)
    data_dir = (ROOT / cfg["data"]).resolve()
    counts = check_dataset(data_dir)
    print("dataset:", json.dumps(counts, ensure_ascii=False))

    run_dir = ROOT / "ml" / "runs"
    model = YOLO(cfg["base_model"])
    model.train(
        data=str(data_dir),
        epochs=args.epochs or cfg["epochs"],
        patience=cfg.get("patience", 15),
        imgsz=cfg["imgsz"],
        batch=cfg.get("batch", 32),
        seed=cfg.get("seed", 42),
        device=args.device,
        project=str(run_dir),
        name=cfg["crop"],
        exist_ok=True,
        plots=True,
        verbose=False,
        **cfg.get("augment", {}),
    )

    best = run_dir / cfg["crop"] / "weights" / "best.pt"
    trained = YOLO(str(best))
    names = {int(k): v for k, v in trained.names.items()}
    report = per_class_report(trained, data_dir / "test", names, cfg["imgsz"])
    print("test:", json.dumps({k: report[k] for k in ("accuracy", "macro_f1")}))

    out = ROOT / cfg["output"]
    out.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(best, out)
    meta = {
        "crop": cfg["crop"],
        "task": cfg["task"],
        "imgsz": cfg["imgsz"],
        "names": names,
        "trained_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "base_model": cfg["base_model"],
        "dataset_counts": counts,
        "test_metrics": report,
    }
    out.with_suffix("").with_suffix(".labels_map.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"saved {out} and labels map")
    return 0


if __name__ == "__main__":
    sys.exit(main())
