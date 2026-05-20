"""
05_generate_binary_maps.py

Generate Stage 6 binary edge maps from existing magnitude PNG outputs.

This script implements the adaptive thresholding stage from the paper:
    T = mu + k * sigma
where mu and sigma are computed over the magnitude map of each image.

It reads existing PNG magnitude maps from output/<dataset>/<method>/, applies
the adaptive threshold, and writes binary edges to output/<dataset>/<method>_binary/.

These binary maps are used for:
    - Paper Figure 5 (qualitative edge visualization)
    - Stage 6 timing measurement (post-thresholding step time)
    - Adaptive-threshold edge coverage statistics

The magnitude PNGs in output/<dataset>/<method>/ remain unchanged and continue
to be used for BSDS500 ODS/OIS/AP evaluation (threshold sweep).

Author: Kukuh Yudhistiro
"""

from __future__ import annotations

import argparse
import csv
import time
from pathlib import Path
from typing import List

import cv2
import numpy as np
from PIL import Image


def adaptive_threshold(magnitude_u8: np.ndarray, k_sigma: float = 2.0) -> tuple:
    """Apply adaptive threshold T = mean + k_sigma * std.

    Args:
        magnitude_u8 : uint8 magnitude map from saved PNG
        k_sigma      : multiplier for sigma (paper uses 2.0,
                       diagnostic suggested 1.5 for some images)

    Returns:
        binary_edges : uint8 binary map (0 or 255)
        T            : the threshold value used
        coverage_pct : percentage of pixels above threshold
    """
    mag_f = magnitude_u8.astype(np.float64)
    mu = mag_f.mean()
    sigma = mag_f.std()
    T = mu + k_sigma * sigma
    binary = (mag_f > T).astype(np.uint8) * 255
    coverage = 100.0 * np.sum(binary > 0) / binary.size
    return binary, T, coverage


def process_one(pred_path: Path, out_path: Path, k_sigma: float) -> dict:
    """Process one prediction PNG, write binary version, return stats."""
    img = np.array(Image.open(str(pred_path)).convert("L"))
    t0 = time.perf_counter()
    binary, T, coverage = adaptive_threshold(img, k_sigma)
    threshold_time = time.perf_counter() - t0

    out_path.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(out_path), binary)

    return {
        "image_id": pred_path.stem,
        "threshold_value": T,
        "coverage_pct": coverage,
        "threshold_time_s": threshold_time,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Generate Stage 6 binary edge maps from magnitude PNGs."
    )
    parser.add_argument("--output-root", type=Path, required=True,
                        help="Root containing output/<dataset>/<method>/*.png")
    parser.add_argument("--binary-suffix", default="_binary",
                        help="Suffix added to method folder name "
                             "(default: '_binary')")
    parser.add_argument("--k-sigma", type=float, default=2.0,
                        help="Sigma multiplier for T = mu + k*sigma "
                             "(paper uses 2.0)")
    parser.add_argument("--datasets", nargs="+",
                        default=["BSDS500", "BIPED", "UDED"])
    parser.add_argument("--methods", nargs="+", default=None,
                        help="Methods to process (default: all subdirs)")
    parser.add_argument("--stats-csv", type=Path, default=None,
                        help="Optional CSV path to log per-image stats")
    args = parser.parse_args()

    total_processed = 0
    all_stats = []

    print(f"{'=' * 72}")
    print(f"STAGE 6 — Binary edge map generation")
    print(f"  Threshold formula : T = mu + {args.k_sigma} * sigma")
    print(f"  Output suffix     : {args.binary_suffix}")
    print(f"{'=' * 72}")

    for dataset in args.datasets:
        ds_root = args.output_root / dataset
        if not ds_root.exists():
            print(f"[SKIP] {ds_root} not found")
            continue

        if args.methods is None:
            method_dirs = sorted([d for d in ds_root.iterdir()
                                  if d.is_dir() and not d.name.endswith(
                                      args.binary_suffix)])
        else:
            method_dirs = [ds_root / m for m in args.methods
                           if (ds_root / m).exists()]

        for method_dir in method_dirs:
            method = method_dir.name
            binary_dir = ds_root / f"{method}{args.binary_suffix}"
            pred_files = sorted(method_dir.glob("*.png"))
            if not pred_files:
                continue

            print(f"\n[{dataset}/{method}] {len(pred_files)} images "
                  f"-> {binary_dir.relative_to(args.output_root)}/")

            for pred_path in pred_files:
                out_path = binary_dir / pred_path.name
                stats = process_one(pred_path, out_path, args.k_sigma)
                stats["dataset"] = dataset
                stats["method"] = method
                all_stats.append(stats)
                total_processed += 1

            # Brief summary for this method
            sub = [s for s in all_stats
                   if s["dataset"] == dataset and s["method"] == method]
            cov_mean = np.mean([s["coverage_pct"] for s in sub])
            T_mean = np.mean([s["threshold_value"] for s in sub])
            print(f"   mean coverage = {cov_mean:.2f}%  "
                  f"mean T = {T_mean:.2f}")

    if args.stats_csv and all_stats:
        args.stats_csv.parent.mkdir(parents=True, exist_ok=True)
        fields = ["dataset", "method", "image_id",
                  "threshold_value", "coverage_pct", "threshold_time_s"]
        with open(args.stats_csv, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for s in all_stats:
                w.writerow({k: s.get(k, "") for k in fields})
        print(f"\n[OK] Per-image stats: {args.stats_csv}")

    print(f"\n[DONE] Processed {total_processed} images.")


if __name__ == "__main__":
    main()
