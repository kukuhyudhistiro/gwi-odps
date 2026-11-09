"""Dataset listing and ground-truth loading.

Layout is configured in config.yaml (datasets.*). Images and GT are matched by
file stem. BSDS500 GT is the official .mat (multi-annotator); BIPED and UDED GT
are single-annotator PNG maps.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List

import numpy as np
from PIL import Image
from scipy.io import loadmat

IMG_EXT = (".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff")


@dataclass(frozen=True)
class Item:
    dataset: str
    split: str
    image_id: str
    image_path: str
    gt_path: str
    gt_format: str


def _list_images(d: Path) -> List[Path]:
    if not d.is_dir():
        raise FileNotFoundError(f"Image folder not found: {d}")
    return sorted(p for p in d.iterdir() if p.suffix.lower() in IMG_EXT)


def list_items(cfg, dataset: str, split: str) -> List[Item]:
    """split may be 'train', 'val', 'test', or 'trainval' (train + val)."""
    if split == "trainval":
        return list_items(cfg, dataset, "train") + list_items(cfg, dataset, "val")
    dcfg = cfg["datasets"][dataset]
    if split not in dcfg["splits"]:
        raise KeyError(f"{dataset} has no split '{split}' in config.yaml")
    sp = dcfg["splits"][split]
    root = Path(cfg["paths"]["data_root"])
    img_dir = root / sp["images"]
    gt_dir = root / sp["gt"]
    fmt = dcfg["gt_format"]
    items = []
    missing = []
    for p in _list_images(img_dir):
        if fmt == "mat":
            g = gt_dir / f"{p.stem}.mat"
        else:
            g = None
            for ext in (".png", ".jpg", ".bmp"):
                cand = gt_dir / f"{p.stem}{ext}"
                if cand.exists():
                    g = cand
                    break
        if g is None or not Path(g).exists():
            missing.append(p.stem)
            continue
        items.append(Item(dataset, split, p.stem, str(p), str(g), fmt))
    if missing:
        print(f"[WARN] {dataset}/{split}: {len(missing)} image(s) without GT, "
              f"skipped (e.g. {missing[:3]})")
    if not items:
        raise RuntimeError(f"No items for {dataset}/{split} "
                           f"(images={img_dir}, gt={gt_dir})")
    return items


def load_gt(item: Item) -> List[np.ndarray]:
    if item.gt_format == "mat":
        mat = loadmat(item.gt_path)
        gt = mat["groundTruth"]
        return [(gt[0, i]["Boundaries"][0, 0] > 0) for i in range(gt.shape[1])]
    arr = np.array(Image.open(item.gt_path).convert("L"))
    return [arr > 127]
