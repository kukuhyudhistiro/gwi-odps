"""Create a tiny synthetic dataset with the same layout as config.yaml.

For smoke tests only (scripts run end to end without real data):
    python tools/make_synthetic_data.py --out /tmp/synth_data
    python scripts/01_selftest.py --config tests/config_synth.yaml
"""
from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from scipy.io import savemat


def scene(rng, h, w):
    lab = np.zeros((h, w), np.int32)
    img = np.full((h, w), rng.uniform(40, 200), np.float64)
    for i in range(1, rng.integers(4, 8)):
        m = np.zeros((h, w), np.uint8)
        if rng.random() < 0.5:
            c = (int(rng.integers(0, w)), int(rng.integers(0, h)))
            cv2.circle(m, c, int(rng.integers(h // 10, h // 3)), 1, -1)
        else:
            pts = rng.integers(0, [w, h], size=(rng.integers(3, 6), 2)).astype(np.int32)
            cv2.fillPoly(m, [pts], 1)
        lab[m > 0] = i
        img[m > 0] = rng.uniform(20, 235)
    img += rng.normal(0, 6, img.shape)
    tex = cv2.GaussianBlur(rng.normal(0, 10, img.shape), (0, 0), 1.0)
    img = np.clip(img + tex, 0, 255)
    rgb = np.stack([img, img * 0.95, img * 1.05], -1).clip(0, 255).astype(np.uint8)
    return rgb, lab


def boundaries(lab, rng, jitter=0):
    b = np.zeros(lab.shape, bool)
    b[:, 1:] |= lab[:, 1:] != lab[:, :-1]
    b[1:, :] |= lab[1:, :] != lab[:-1, :]
    if jitter:
        dy, dx = rng.integers(-jitter, jitter + 1, 2)
        b = np.roll(np.roll(b, dy, 0), dx, 1)
    return b


def write_bsds(root, split, n, rng, h, w):
    (root / "images" / split).mkdir(parents=True, exist_ok=True)
    (root / "groundTruth" / split).mkdir(parents=True, exist_ok=True)
    for i in range(n):
        rgb, lab = scene(rng, h, w)
        iid = f"{split}{i:03d}"
        Image.fromarray(rgb).save(root / "images" / split / f"{iid}.jpg", quality=95)
        gts = np.empty((1, 5), dtype=object)
        for a in range(5):
            gts[0, a] = {"Segmentation": lab.astype(np.uint16),
                         "Boundaries": boundaries(lab, rng, jitter=a % 2).astype(np.uint8)}
        savemat(root / "groundTruth" / split / f"{iid}.mat", {"groundTruth": gts})


def write_png(img_dir, gt_dir, n, rng, h, w, prefix):
    img_dir.mkdir(parents=True, exist_ok=True)
    gt_dir.mkdir(parents=True, exist_ok=True)
    for i in range(n):
        rgb, lab = scene(rng, h, w)
        iid = f"{prefix}{i:03d}"
        Image.fromarray(rgb).save(img_dir / f"{iid}.jpg", quality=95)
        Image.fromarray((boundaries(lab, rng) * 255).astype(np.uint8)).save(gt_dir / f"{iid}.png")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--h", type=int, default=96)
    ap.add_argument("--w", type=int, default=144)
    a = ap.parse_args()
    rng = np.random.default_rng(7)
    out = Path(a.out)
    for split, n in (("train", 6), ("val", 4), ("test", 6)):
        write_bsds(out / "BSDS500", split, n, rng, a.h, a.w)
    write_png(out / "BIPED/edges/imgs/train/rgbr/real",
              out / "BIPED/edges/edge_maps/train/rgbr/real", 4, rng, a.h, a.w, "RGB_t")
    write_png(out / "BIPED/edges/imgs/test", out / "BIPED/edges/edge_maps/test",
              4, rng, a.h, a.w, "RGB_")
    write_png(out / "UDED/imgs", out / "UDED/gt", 4, rng, a.h, a.w, "uded")
    print(f"synthetic data in {out}")


if __name__ == "__main__":
    main()
