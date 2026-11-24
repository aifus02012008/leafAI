"""Background-composite augmentation for datasets shot on a plain white background.

Leaves photographed (or cut out) on white teach a model that "leaf = the only thing in the frame",
so real orchard photos with foliage, soil and sky behind the leaf get misclassified. This script cuts
each TRAINING leaf out of its white background and pastes it onto real field backgrounds
(random crops of outdoor photos, blurred and re-lit), writing extra training images next to the originals.
Validation/test splits are untouched so reported metrics stay comparable.

Usage (repo root):
    backend/.venv/Scripts/python.exe -I ml/compose_backgrounds.py datasets/pomelo/cls --backgrounds datasets/durian/cls/train --per-image 2
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageEnhance, ImageFilter

WHITE_LEVEL = 235          # pixels brighter than this in all channels count as background
MIN_LEAF_FRACTION = 0.08   # skip images where almost nothing is left after removing white


def leaf_alpha(img: Image.Image) -> Image.Image | None:
    arr = np.asarray(img.convert("RGB"), dtype=np.uint8)
    leaf = ~(arr >= WHITE_LEVEL).all(axis=2)
    if leaf.mean() < MIN_LEAF_FRACTION:
        return None
    alpha = Image.fromarray((leaf * 255).astype(np.uint8), "L")
    return alpha.filter(ImageFilter.MinFilter(5)).filter(ImageFilter.GaussianBlur(1.5))  # trim white halo, feather


def random_background(pool: list[Path], size: int, rnd: random.Random) -> Image.Image:
    bg = Image.open(rnd.choice(pool)).convert("RGB")
    scale = rnd.uniform(1.0, 2.0)
    bg = bg.resize((int(bg.width * scale) + 1, int(bg.height * scale) + 1))
    x = rnd.randint(0, max(0, bg.width - size)); y = rnd.randint(0, max(0, bg.height - size))
    bg = bg.crop((x, y, x + size, y + size)).resize((size, size))
    if rnd.random() < 0.5:
        bg = bg.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    bg = bg.filter(ImageFilter.GaussianBlur(rnd.uniform(1.5, 5)))          # depth of field
    bg = ImageEnhance.Brightness(bg).enhance(rnd.uniform(0.6, 1.3))
    return ImageEnhance.Color(bg).enhance(rnd.uniform(0.7, 1.3))


def compose(leaf_path: Path, pool: list[Path], rnd: random.Random, size: int = 384) -> Image.Image | None:
    img = Image.open(leaf_path).convert("RGB")
    alpha = leaf_alpha(img)
    if alpha is None:
        return None
    box = alpha.getbbox()
    if not box:
        return None
    leaf, alpha = img.crop(box), alpha.crop(box)
    target = rnd.uniform(0.55, 0.92) * size
    k = target / max(leaf.size)
    leaf = leaf.resize((max(1, int(leaf.width * k)), max(1, int(leaf.height * k))))
    alpha = alpha.resize(leaf.size)
    angle = rnd.uniform(-35, 35)
    leaf, alpha = leaf.rotate(angle, expand=True), alpha.rotate(angle, expand=True)
    leaf = ImageEnhance.Brightness(leaf).enhance(rnd.uniform(0.75, 1.2))  # field lighting
    canvas = random_background(pool, size, rnd)
    x = rnd.randint(0, max(0, size - leaf.width)); y = rnd.randint(0, max(0, size - leaf.height))
    canvas.paste(leaf, (x, y), alpha)
    return canvas


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", type=Path, help="prepared dataset root containing train/<class>/")
    parser.add_argument("--backgrounds", type=Path, required=True, help="folder of outdoor photos (searched recursively)")
    parser.add_argument("--per-image", type=int, default=2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()
    rnd = random.Random(args.seed)
    pool = sorted(args.backgrounds.rglob("*.jpg"))
    if not pool:
        raise SystemExit("no background photos found")
    made = skipped = 0
    for img_path in sorted((args.dataset / "train").rglob("*.jpg")):
        if "_bg" in img_path.stem:
            continue  # idempotent: never composite a composite
        for k in range(args.per_image):
            out = img_path.with_name(f"{img_path.stem}_bg{k}.jpg")
            composed = compose(img_path, pool, rnd)
            if composed is None:
                skipped += 1
                break
            composed.save(out, "JPEG", quality=90)
            made += 1
    print(f"composited {made} images, skipped {skipped} (no white background)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
