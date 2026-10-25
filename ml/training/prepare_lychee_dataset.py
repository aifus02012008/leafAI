# -*- coding: utf-8 -*-
"""
LEAF_AI — Chuẩn bị bộ dữ liệu lá vải thiều cho huấn luyện.

Việc script làm:
  1. Quét các nguồn trong dataset_sources.json (ảnh tự chụp Lục Ngạn + các bộ Mendeley CC BY 4.0).
  2. Ánh xạ tên thư mục lớp của từng bộ về 7 lớp LEAF_AI (bỏ lớp mơ hồ, bỏ thư mục ảnh đã augment sẵn).
  3. Khử trùng lặp gần giống bằng dHash 64-bit (Hamming ≤ 3) — tránh "rò rỉ" cùng một ảnh vào cả train lẫn test,
     nguyên nhân phổ biến khiến độ chính xác báo cáo đẹp nhưng chạy thực tế kém.
  4. Chia train/val/test phân tầng theo lớp; ưu tiên ảnh Lục Ngạn vào tập test để đo đúng điều kiện thực tế.
  5. Xuất ảnh đã xoay theo EXIF, thu nhỏ cạnh dài ≤ 512px vào data/lychee_v1/{train,val,test}/{lớp}/
     kèm manifest.csv và stats.json (dùng cho báo cáo KHKT).

Chạy:
  python ml/training/prepare_lychee_dataset.py                    # mặc định
  python ml/training/prepare_lychee_dataset.py --out data/lychee_v2 --val 0.15 --test 0.15 --min-per-class 40
"""

import argparse
import csv
import json
import random
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parents[2]          # thư mục repo leafAI/
HERE = Path(__file__).resolve().parent
IMG_EXT = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
Image.MAX_IMAGE_PIXELS = 80_000_000


# ---------------------------------------------------------------------------
# Ánh xạ nhãn
# ---------------------------------------------------------------------------
def normalize_name(s: str) -> str:
    s = unicodedata.normalize("NFD", s)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn").replace("đ", "d").replace("Đ", "D")
    s = re.sub(r"[^a-zA-Z0-9]+", " ", s).strip().lower()
    return s


class LabelMapper:
    def __init__(self, cfg: dict):
        self.classes = cfg["classes"]
        self.skip = [normalize_name(x) for x in cfg.get("skip_dirs_containing", [])]
        self.rules = []
        for r in cfg["rules"]:
            pats = [re.compile(r"(?<![a-z0-9])" + re.escape(normalize_name(k))) for k in r["keywords"]]
            self.rules.append((pats, r["class"]))

    def skipped(self, parts) -> bool:
        joined = [normalize_name(p) for p in parts]
        return any(s and s in p for s in self.skip for p in joined) or any(p.startswith(".") for p in parts)

    def map_dir(self, name: str):
        """Trả về tên lớp, 'IGNORE' hoặc None (không nhận ra)."""
        exact = {c.lower(): c for c in self.classes}
        if name.lower() in exact:
            return exact[name.lower()]
        n = normalize_name(name)
        for pats, cls in self.rules:
            if any(p.search(n) for p in pats):
                return cls
        return None

    def map_path(self, rel_parts):
        # Ưu tiên thư mục cha gần ảnh nhất, rồi lùi dần lên trên
        for part in reversed(rel_parts):
            cls = self.map_dir(part)
            if cls:
                return cls, part
        return None, None


# ---------------------------------------------------------------------------
# dHash + khử trùng lặp gần giống
# ---------------------------------------------------------------------------
def dhash(img: Image.Image, size: int = 8) -> int:
    g = img.convert("L").resize((size + 1, size), Image.Resampling.LANCZOS)
    px = g.tobytes()
    bits = 0
    for row in range(size):
        for col in range(size):
            left = px[row * (size + 1) + col]
            right = px[row * (size + 1) + col + 1]
            bits = (bits << 1) | (1 if left > right else 0)
    return bits


def thumb64(img: Image.Image) -> bytes:
    """Ảnh xám 64×64 để xác nhận trùng lặp (dHash 8×8 dễ gộp nhầm ảnh chỉ giống bố cục, vd lá khỏe và lá vài đốm nhỏ)."""
    return img.convert("L").resize((64, 64), Image.Resampling.BILINEAR).tobytes()


def mean_abs_diff(a: bytes, b: bytes) -> float:
    return sum(abs(x - y) for x, y in zip(a, b)) / len(a)


class NearDupIndex:
    """Bước 1 — multi-index hashing: Hamming ≤ 3 trên 64 bit ⇒ ít nhất 1 trong 4 khối 16 bit trùng khớp.
    Bước 2 — xác nhận: chênh lệch trung bình ảnh xám 64×64 < max_mad (0–255)."""

    def __init__(self, max_dist: int = 3, max_mad: float = 2.5):
        self.max_dist = max_dist
        self.max_mad = max_mad
        self.tables = [defaultdict(list) for _ in range(4)]
        self.hashes = []
        self.thumbs = []

    def find(self, h: int, thumb: bytes):
        seen = set()
        for i in range(4):
            key = (h >> (16 * i)) & 0xFFFF
            for idx in self.tables[i].get(key, ()):
                if idx in seen:
                    continue
                seen.add(idx)
                if bin(self.hashes[idx] ^ h).count("1") <= self.max_dist and mean_abs_diff(self.thumbs[idx], thumb) < self.max_mad:
                    return idx
        return None

    def add(self, h: int, thumb: bytes) -> int:
        idx = len(self.hashes)
        self.hashes.append(h)
        self.thumbs.append(thumb)
        for i in range(4):
            self.tables[i][(h >> (16 * i)) & 0xFFFF].append(idx)
        return idx


# ---------------------------------------------------------------------------
# Quét nguồn
# ---------------------------------------------------------------------------
def scan_sources(cfg, mapper, only=None):
    items, unknown_dirs, ignored = [], Counter(), Counter()
    for src in cfg["sources"]:
        if only and src["name"] not in only:
            continue
        base = (ROOT / src["path"]).resolve()
        if not base.exists():
            print(f"  [bỏ qua] {src['name']}: chưa có thư mục {base}")
            continue
        n_before = len(items)
        for p in base.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in IMG_EXT:
                continue
            rel_dirs = p.relative_to(base).parts[:-1]
            if mapper.skipped(rel_dirs):
                continue
            cls, matched = mapper.map_path(rel_dirs)
            if cls is None:
                unknown_dirs[f"{src['name']}/{'/'.join(rel_dirs) or '.'}"] += 1
                continue
            if cls == "IGNORE":
                ignored[f"{src['name']}/{matched}"] += 1
                continue
            items.append({
                "path": p,
                "class": cls,
                "source": src["name"],
                "priority_test": bool(src.get("priority_test")),
                "src_dir": matched,
            })
        print(f"  [nguồn] {src['name']}: {len(items) - n_before} ảnh")
    return items, unknown_dirs, ignored


def load_and_hash(item):
    try:
        with Image.open(item["path"]) as im:
            im = ImageOps.exif_transpose(im).convert("RGB")
            w, h = im.size
            if min(w, h) < 96:
                return None, "quá nhỏ"
            item["hash"] = dhash(im)
            item["thumb"] = thumb64(im)
            item["size"] = (w, h)
            return item, None
    except (UnidentifiedImageError, OSError, ValueError) as e:
        return None, f"lỗi đọc ({e.__class__.__name__})"


def export_image(args):
    item, dst, max_side, quality = args
    with Image.open(item["path"]) as im:
        im = ImageOps.exif_transpose(im).convert("RGB")
        im.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
        dst.parent.mkdir(parents=True, exist_ok=True)
        im.save(dst, "JPEG", quality=quality, optimize=True)


# ---------------------------------------------------------------------------
# Chia tập
# ---------------------------------------------------------------------------
def split_items(items, val_frac, test_frac, seed, max_priority_test_frac=0.5):
    rng = random.Random(seed)
    by_cls = defaultdict(list)
    for it in items:
        by_cls[it["class"]].append(it)

    for cls, lst in by_cls.items():
        rng.shuffle(lst)
        n = len(lst)
        n_test = max(1, round(n * test_frac)) if n >= 10 else 0
        n_val = max(1, round(n * val_frac)) if n >= 10 else 0

        prio = [x for x in lst if x["priority_test"]]
        rest = [x for x in lst if not x["priority_test"]]
        # Ảnh Lục Ngạn: tối đa 50% đưa vào test, phần còn lại để mô hình được học điều kiện địa phương
        take_prio = min(len(prio), n_test, int(len(prio) * max_priority_test_frac) or (1 if prio and n_test else 0))
        test = prio[:take_prio] + rest[: n_test - take_prio]
        remaining = prio[take_prio:] + rest[n_test - take_prio:]
        rng.shuffle(remaining)
        val = remaining[:n_val]
        train = remaining[n_val:]
        for x in train:
            x["split"] = "train"
        for x in val:
            x["split"] = "val"
        for x in test:
            x["split"] = "test"
    return items


# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Chuẩn bị dữ liệu lá vải LEAF_AI")
    ap.add_argument("--config", default=str(HERE / "dataset_sources.json"))
    ap.add_argument("--out", default="data/lychee_v1", help="thư mục xuất (tương đối với repo)")
    ap.add_argument("--val", type=float, default=0.15)
    ap.add_argument("--test", type=float, default=0.15)
    ap.add_argument("--min-per-class", type=int, default=40, help="lớp ít hơn số ảnh này sẽ bị loại (kèm cảnh báo)")
    ap.add_argument("--max-per-class", type=int, default=0, help="giới hạn số ảnh mỗi lớp (0 = không giới hạn)")
    ap.add_argument("--max-side", type=int, default=512)
    ap.add_argument("--quality", type=int, default=92)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--only", nargs="*", help="chỉ dùng các nguồn có tên này")
    ap.add_argument("--dry-run", action="store_true", help="chỉ thống kê, không ghi ảnh")
    args = ap.parse_args()

    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    mapper = LabelMapper(cfg)
    out_dir = (ROOT / args.out).resolve()

    print("1) Quét nguồn dữ liệu…")
    items, unknown_dirs, ignored = scan_sources(cfg, mapper, args.only)
    if unknown_dirs:
        print("\n  ⚠ Thư mục không nhận ra lớp (thêm từ khoá vào dataset_sources.json nếu cần):")
        for k, v in unknown_dirs.most_common(20):
            print(f"     {v:6d}  {k}")
    if ignored:
        print("\n  Bỏ qua lớp mơ hồ (IGNORE):")
        for k, v in ignored.most_common():
            print(f"     {v:6d}  {k}")
    if not items:
        sys.exit("\n✗ Không tìm thấy ảnh nào. Xem hướng dẫn trong ml/training/README_TRAIN.md")

    print(f"\n2) Đọc ảnh + tính dHash cho {len(items)} ảnh…")
    # Ảnh Lục Ngạn xử lý trước để khi trùng thì giữ bản địa phương
    items.sort(key=lambda x: (not x["priority_test"], x["source"], str(x["path"])))
    loaded, bad = [], Counter()
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for it, err in ex.map(load_and_hash, items):
            if it:
                loaded.append(it)
            else:
                bad[err] += 1
    if bad:
        print(f"  Loại {sum(bad.values())} ảnh: {dict(bad)}")

    print("3) Khử trùng lặp gần giống…")
    index = NearDupIndex(max_dist=3)
    kept, dup_conflict = [], 0
    owner_class = []
    for it in loaded:
        j = index.find(it["hash"], it["thumb"])
        if j is not None:
            if owner_class[j] != it["class"]:
                dup_conflict += 1   # cùng ảnh nhưng khác nhãn giữa các bộ → bỏ bản sau
            continue
        index.add(it["hash"], it.pop("thumb"))
        owner_class.append(it["class"])
        kept.append(it)
    n_dups = len(loaded) - len(kept)
    print(f"  Giữ {len(kept)} / {len(loaded)} ảnh (loại {len(loaded) - len(kept)} bản trùng, {dup_conflict} bản trùng nhưng khác nhãn)")

    counts = Counter(x["class"] for x in kept)
    dropped = [c for c, n in counts.items() if n < args.min_per_class]
    if dropped:
        print(f"\n  ⚠ Loại lớp quá ít ảnh (< {args.min_per_class}): " + ", ".join(f"{c}={counts[c]}" for c in dropped))
        print("    → Cần chụp thêm ảnh thật ở Lục Ngạn cho các lớp này (xem README_TRAIN.md). Gemini sẽ xử lý tạm các ca này.")
        kept = [x for x in kept if x["class"] not in dropped]

    if args.max_per_class:
        rng = random.Random(args.seed)
        by = defaultdict(list)
        for x in kept:
            by[x["class"]].append(x)
        kept = []
        for c, lst in by.items():
            prio = [x for x in lst if x["priority_test"]]
            rest = [x for x in lst if not x["priority_test"]]
            rng.shuffle(rest)
            kept += prio + rest[: max(0, args.max_per_class - len(prio))]

    if not kept:
        sys.exit("\n✗ Không còn ảnh nào sau khi lọc. Kiểm tra lại dữ liệu nguồn và --min-per-class.")

    print("\n4) Chia train/val/test…")
    split_items(kept, args.val, args.test, args.seed)
    classes = [c for c in cfg["classes"] if any(x["class"] == c for x in kept)]

    table = defaultdict(Counter)
    for x in kept:
        table[x["class"]][x["split"]] += 1
    print(f"  {'Lớp':<14}{'train':>8}{'val':>8}{'test':>8}{'tổng':>8}")
    for c in classes:
        t = table[c]
        print(f"  {c:<14}{t['train']:>8}{t['val']:>8}{t['test']:>8}{sum(t.values()):>8}")

    if args.dry_run:
        print("\n(dry-run) Không ghi ảnh.")
        return

    print(f"\n5) Xuất ảnh vào {out_dir} …")
    if out_dir.exists() and any(out_dir.iterdir()):
        sys.exit(f"✗ {out_dir} đã có dữ liệu. Đổi --out sang thư mục mới (vd data/lychee_v2) để không trộn phiên bản.")
    jobs, rows = [], []
    for x in kept:
        fname = f"{x['source']}_{x['hash']:016x}.jpg"
        dst = out_dir / x["split"] / x["class"] / fname
        jobs.append((x, dst, args.max_side, args.quality))
        rows.append({
            "split": x["split"], "class": x["class"], "source": x["source"],
            "file": str(dst.relative_to(out_dir)).replace("\\", "/"),
            "orig": str(x["path"].relative_to(ROOT)).replace("\\", "/") if x["path"].is_relative_to(ROOT) else str(x["path"]),
            "src_dir": x["src_dir"], "dhash": f"{x['hash']:016x}",
        })
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for i, _ in enumerate(ex.map(export_image, jobs), 1):
            if i % 500 == 0 or i == len(jobs):
                print(f"   {i}/{len(jobs)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "manifest.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    by_source = defaultdict(Counter)
    for x in kept:
        by_source[x["source"]][x["class"]] += 1
    stats = {
        "classes": classes,
        "dropped_classes": {c: counts[c] for c in dropped},
        "splits": {c: dict(table[c]) for c in classes},
        "by_source": {s: dict(v) for s, v in by_source.items()},
        "total": len(kept),
        "near_duplicates_removed": n_dups,
        "duplicate_label_conflicts": dup_conflict,
        "seed": args.seed,
        "val_frac": args.val,
        "test_frac": args.test,
        "max_side": args.max_side,
    }
    (out_dir / "stats.json").write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n✓ Xong. {len(kept)} ảnh, {len(classes)} lớp → {out_dir}")
    print("  Tiếp theo: python ml/training/train_lychee.py --data " + args.out)


if __name__ == "__main__":
    main()
