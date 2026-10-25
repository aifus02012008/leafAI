# -*- coding: utf-8 -*-
"""
Kiểm tra nhanh mô hình lá vải trên 1 ảnh hoặc cả thư mục.
  python ml/training/predict_lychee.py --model ml/hf-space/lychee_model.pt anh_la.jpg
  python ml/training/predict_lychee.py --model ml/hf-space/lychee_model.pt data/raw/luc_ngan/Anthracnose
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageOps

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "ml" / "hf-space"))
from inference import LycheeClassifier  # noqa: E402

IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp"}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="ml/hf-space/lychee_model.pt")
    ap.add_argument("paths", nargs="+")
    args = ap.parse_args()

    clf = LycheeClassifier(str((ROOT / args.model) if not Path(args.model).is_absolute() else args.model))
    print(f"Mô hình: {clf.meta['arch']} {clf.meta['version']} | ngưỡng chấp nhận {100 * clf.accept_threshold:.0f}%\n")
    files = []
    for p in map(Path, args.paths):
        files += sorted(f for f in p.rglob("*") if f.suffix.lower() in IMG_EXT) if p.is_dir() else [p]
    for f in files:
        with Image.open(f) as im:
            r = clf.predict(ImageOps.exif_transpose(im), with_heatmap=False, top_k=3)
        tops = ", ".join(f"{x['class']} {x['probability']}%" for x in r["results"])
        flag = f"  ⚠ ca khó: {','.join(r['uncertain_reasons'])} → hỏi Gemini" if r["uncertain"] else ""
        print(f"{f.name:<40} {tops}{flag}")


if __name__ == "__main__":
    main()
