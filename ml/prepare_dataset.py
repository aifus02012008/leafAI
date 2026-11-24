"""Turn a downloaded folder-per-class zip into a leak-free train/val/test split for ml/train.py.

Usage (repo root):
    backend/.venv/Scripts/python.exe -I ml/prepare_dataset.py ml/configs/guava.yaml

The config's `source` section names the zip, the folder prefix inside it, a class-name map and an
optional regex that ties augmented copies to their original (e.g. "123_transformed_4.jpg" -> "123").

Leakage control:
- exact duplicates (same bytes) are dropped;
- originals whose perceptual hash (dHash) is within a few bits are grouped as near-duplicates;
- whole groups go to one split, so no variant of a test image is ever seen in training;
- augmented copies shipped with the dataset are used for training only (val/test = originals).
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import random
import re
import shutil
import sys
import zipfile
from collections import defaultdict
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
HASH_SIZE = 16          # 16x16 dHash = 256 bits (64-bit hashes collapse plain-background photos)
NEAR_DUP_BITS = 20      # <= ~8% of bits: same leaf re-saved/re-shot (checked visually; 24+ bits = different leaves)
SPLITS = (("train", 0.70), ("val", 0.15), ("test", 0.15))


def shrink(data: bytes, max_side: int | None) -> bytes:
    """Re-encode large photos to at most max_side px (decoding 12 MP JPEGs starves the GPU during training)."""
    if not max_side:
        return data
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    if max(img.size) <= max_side:
        return data
    img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=92)
    return buf.getvalue()


def dhash(data: bytes) -> np.ndarray:
    img = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("L").resize((HASH_SIZE + 1, HASH_SIZE), Image.Resampling.LANCZOS)
    px = np.asarray(img, dtype=np.int16)
    return np.packbits((px[:, 1:] > px[:, :-1]).flatten())


class UnionFind:
    def __init__(self, n: int):
        self.parent = list(range(n))

    def find(self, i: int) -> int:
        while self.parent[i] != i:
            self.parent[i] = self.parent[self.parent[i]]
            i = self.parent[i]
        return i

    def union(self, a: int, b: int) -> None:
        self.parent[self.find(a)] = self.find(b)


def near_duplicate_groups(hashes: list[np.ndarray]) -> list[int]:
    """Group index per item: items whose dHash differ by <= NEAR_DUP_BITS share a group."""
    n = len(hashes)
    arr = np.stack(hashes) if hashes else np.zeros((0, HASH_SIZE * HASH_SIZE // 8), dtype=np.uint8)
    uf = UnionFind(n)
    for i in range(n):
        x = np.bitwise_xor(arr[i + 1:], arr[i])
        dist = np.unpackbits(x, axis=1).sum(axis=1) if len(x) else np.array([])
        for j in np.nonzero(dist <= NEAR_DUP_BITS)[0]:
            uf.union(i, i + 1 + int(j))
    return [uf.find(i) for i in range(n)]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    cfg = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    src = cfg["source"]
    out_dir = ROOT / cfg["data"]
    group_re = re.compile(src["augmented_regex"]) if src.get("augmented_regex") else None
    rnd = random.Random(cfg.get("seed", 42))

    originals: dict[str, list[tuple[str, bytes]]] = defaultdict(list)   # class -> [(name, bytes)]
    augmented: dict[str, dict[str, list[tuple[str, bytes]]]] = defaultdict(lambda: defaultdict(list))
    seen_md5: set[str] = set()
    dropped_exact = 0
    with zipfile.ZipFile(ROOT / src["zip"]) as zf:
        for info in zf.infolist():
            name = info.filename
            if info.is_dir() or not name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            if name.startswith("/") or ".." in Path(name).parts:
                continue
            if not name.startswith(src.get("prefix", "")):
                continue
            parts = name[len(src.get("prefix", "")):].split("/")
            folder = "/".join(parts[:-1])  # class folder may be nested, e.g. "Disease/Rust"
            if len(parts) < 2 or folder not in src["class_map"]:
                continue
            cls = src["class_map"][folder]
            data = zf.read(info)
            md5 = hashlib.md5(data).hexdigest()  # dedupe on the original bytes
            if md5 in seen_md5:
                dropped_exact += 1
                continue
            seen_md5.add(md5)
            data = shrink(data, src.get("max_side"))
            stem = Path(parts[-1]).stem
            m = group_re.match(stem) if group_re else None
            if m:
                augmented[cls][m.group(1)].append((parts[-1], data))
            else:
                originals[cls].append((parts[-1], data))

    if out_dir.exists():
        shutil.rmtree(out_dir)
    report: dict = {"dropped_exact_duplicates": dropped_exact, "classes": {}}
    cap = src.get("max_per_class")
    for cls, items in sorted(originals.items()):
        if cap and len(items) > cap:  # balance a dominant class (e.g. healthy) by random subsampling
            items = rnd.sample(items, cap)
        groups = near_duplicate_groups([dhash(d) for _, d in items])
        by_group: dict[int, list[int]] = defaultdict(list)
        for idx, g in enumerate(groups):
            by_group[g].append(idx)
        group_ids = sorted(by_group)
        rnd.shuffle(group_ids)
        n_total = len(items)
        assigned: dict[str, list[int]] = {s: [] for s, _ in SPLITS}
        # Largest groups first, each to the split furthest below its target share: balanced even with big groups.
        for g in sorted(group_ids, key=lambda g: -len(by_group[g])):
            split = min(SPLITS, key=lambda sp: len(assigned[sp[0]]) / (n_total * sp[1]))[0]
            assigned[split].extend(by_group[g])
        counts = {}
        for split, idxs in assigned.items():
            dest = out_dir / split / cls
            dest.mkdir(parents=True, exist_ok=True)
            n = 0
            for i in idxs:
                fname, data = items[i]
                (dest / fname).write_bytes(data)
                n += 1
                if split == "train":  # shipped augmentations of a training original stay in training
                    for aug_name, aug_data in augmented[cls].get(Path(fname).stem, []):
                        (dest / aug_name).write_bytes(aug_data)
                        n += 1
            counts[split] = n
        report["classes"][cls] = {"originals": n_total, "near_dup_groups": len(group_ids), **counts}
        print(f"{cls:28s} originals={n_total:5d} groups={len(group_ids):5d} " + " ".join(f"{k}={v}" for k, v in counts.items()))
    (out_dir / "split_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print("exact duplicates dropped:", dropped_exact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
