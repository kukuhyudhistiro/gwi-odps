"""
10_kernel_ablation_multi_dataset.py — Ablasi 7 konfigurasi di 3 dataset

Extension dari 08_kernel_ablation_corrected.py. Menjalankan ablation pada
BSDS500, BIPED v2, dan UDED untuk menentukan parameter optimal per dataset.

Output:
  - Single combined CSV with columns: dataset, config, kernel_size,
    lambda, n_orientations, sigma, ODS, OIS, AP, runtime_ms_mean, runtime_ms_std
  - Console: 3 tables (one per dataset) in paper-ready Markdown format
  - Summary: best config per dataset + recommendation

Usage:
    python 10_kernel_ablation_multi_dataset.py \\
        --data-root ./data \\
        --output-csv ./eval_results/ablation_multi_dataset.csv

Author: Kukuh Yudhistiro
"""

from __future__ import annotations

import argparse
import csv
import os
import sys
import time
from pathlib import Path
from typing import List

# Re-use the proven evaluator from 04c_evaluate_bsds_v2.py
sys.path.insert(0, str(Path(__file__).parent))

# Note: import path may need adjustment based on your project layout
try:
    # Try as relative import first (if scripts are in same folder)
    import importlib.util
    eval_script_path = Path(__file__).parent / "04c_evaluate_bsds_v2.py"
    if not eval_script_path.exists():
        # Try alternate location
        eval_script_path = Path(__file__).parent.parent / "scripts" / "04c_evaluate_bsds_v2.py"
    spec = importlib.util.spec_from_file_location("eval_module", eval_script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot create spec for {eval_script_path}")
    eval_module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = eval_module  # required for @dataclass in Python 3.13+
    spec.loader.exec_module(eval_module)
    load_gt_bsds_mat = eval_module.load_gt_bsds_mat
    evaluate_image_thresholds = eval_module.evaluate_image_thresholds
    aggregate_scores = eval_module.aggregate_scores
    print(f"[INFO] Loaded evaluator from {eval_script_path}")
except Exception as e:
    print(f"[ERROR] Cannot import evaluator: {e}")
    print(f"[ERROR] Please ensure 04c_evaluate_bsds_v2.py is in the same folder.")
    sys.exit(1)


os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import cv2
cv2.setNumThreads(1)
import numpy as np
from PIL import Image
from scipy.io import loadmat


# ============================================================================
# Configurations
# ============================================================================

CONFIGS = [
    (5, 3.0, 8, "5x5_lam3_n8"),
    (5, 4.0, 8, "5x5_lam4_n8"),
    (7, 4.0, 8, "7x7_lam4_n8_BASELINE"),
    (7, 5.0, 8, "7x7_lam5_n8"),
    (9, 4.0, 8, "9x9_lam4_n8"),
]

# Dataset directory layout
DATASET_LAYOUT = {
    "BSDS500": {
        "img_dir": "BSDS500/images/test",
        "gt_dir": "BSDS500/groundTruth/test",
        "img_ext": "*.jpg",
        "gt_ext": "*.mat",
    },
    "BIPED": {
        "img_dir": "BIPED/edges/imgs/test",
        "gt_dir": "BIPED/edge_maps/test",
        "img_ext": "*.jpg",
        "gt_ext": "*.png",
    },
    "UDED": {
        "img_dir": "UDED/imgs",
        "gt_dir": "UDED/gt",
        "img_ext": "*.jpg",
        "gt_ext": "*.png",
    },
}


# ============================================================================
# Pipeline (Stages 1-5)
# ============================================================================

def build_gwi_kernels(ksize: int, wavelength: float,
                      n_orientations: int, gamma: float = 0.5) -> List[np.ndarray]:
    sigma = 0.56 * wavelength
    kernels = []
    half = ksize // 2
    y, x = np.mgrid[-half:half + 1, -half:half + 1].astype(np.float64)
    for i in range(n_orientations):
        theta = np.deg2rad(i * 180.0 / n_orientations)
        x_t = x * np.cos(theta) + y * np.sin(theta)
        y_t = -x * np.sin(theta) + y * np.cos(theta)
        gauss = np.exp(-0.5 * (x_t ** 2 + gamma ** 2 * y_t ** 2) / sigma ** 2)
        sinusoidal = 2 * np.pi * x_t / wavelength
        kernels.append((gauss * np.sin(sinusoidal)).astype(np.float64))
    return kernels


def preprocess(image_path: Path) -> np.ndarray:
    img = cv2.imread(str(image_path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot load: {image_path}")
    b, g, r = cv2.split(img)
    gray = (0.299 * r.astype(np.float64) +
            0.587 * g.astype(np.float64) +
            0.114 * b.astype(np.float64))
    gray_u8 = np.clip(gray, 0, 255).astype(np.uint8)
    eq = cv2.equalizeHist(gray_u8)
    return eq.astype(np.float64) / 255.0


def run_gwi(normalized: np.ndarray,
            kernels: List[np.ndarray]) -> np.ndarray:
    """Stages 3-5: convolve, |·|, max-pool. Returns RAW magnitude (no per-image normalization)."""
    per_orient = []
    for k in kernels:
        r = cv2.filter2D(normalized, cv2.CV_64F, k,
                          borderType=cv2.BORDER_CONSTANT)
        per_orient.append(np.abs(r))
    return np.max(np.stack(per_orient, axis=0), axis=0)


# ============================================================================
# GT loaders per dataset
# ============================================================================

def load_gt_universal(dataset: str, gt_path: Path) -> List[np.ndarray]:
    """Load GT for any dataset. Returns list of binary maps (one per annotator)."""
    if dataset == "BSDS500":
        # Multi-annotator .mat file
        return load_gt_bsds_mat(gt_path)
    else:
        # Single-annotator PNG (BIPED, UDED)
        arr = np.array(Image.open(gt_path).convert("L"))
        gt_bin = (arr > 127)
        return [gt_bin]  # wrap in list for unified API


def find_test_images(data_root: Path, dataset: str) -> list:
    """Returns list of (img_path, gt_path) pairs for the test split of a dataset."""
    layout = DATASET_LAYOUT[dataset]
    img_dir = data_root / layout["img_dir"]
    gt_dir = data_root / layout["gt_dir"]

    if not img_dir.exists() or not gt_dir.exists():
        return []

    img_paths = sorted(img_dir.glob(layout["img_ext"]))
    if not img_paths:
        # Try alternate extensions
        for ext in ["*.png", "*.jpeg", "*.JPG"]:
            img_paths.extend(sorted(img_dir.glob(ext)))
        # Dedup by stem
        seen, unique = set(), []
        for p in img_paths:
            if p.stem not in seen:
                seen.add(p.stem)
                unique.append(p)
        img_paths = sorted(unique)

    # Match with GT
    if dataset == "BSDS500":
        gt_ext = ".mat"
    else:
        gt_ext = ".png"

    valid_pairs = []
    for img_path in img_paths:
        gt_path = gt_dir / f"{img_path.stem}{gt_ext}"
        if gt_path.exists():
            valid_pairs.append((img_path, gt_path))

    return valid_pairs


# ============================================================================
# Per-dataset ablation
# ============================================================================

def run_ablation_one_dataset(dataset: str, data_root: Path,
                              n_thresholds: int = 33) -> List[dict]:
    """Run 7 configurations on a single dataset, return results list."""
    print(f"\n{'=' * 78}")
    print(f"  ABLATION: {dataset}")
    print(f"{'=' * 78}")

    pairs = find_test_images(data_root, dataset)
    if not pairs:
        print(f"  [WARN] No images found for {dataset}, skipping")
        return []

    print(f"  Found {len(pairs)} test images")

    # Preprocess + load GT cache
    print(f"  Preprocessing images and loading GT...")
    img_cache = {}
    gt_cache = {}
    for img_path, gt_path in pairs:
        img_cache[img_path.stem] = preprocess(img_path)
        gt_cache[img_path.stem] = load_gt_universal(dataset, gt_path)

    image_stems = [p[0].stem for p in pairs]

    # Threshold sweep
    thresholds = np.linspace(1.0 / (n_thresholds + 1),
                              1.0 - 1.0 / (n_thresholds + 1),
                              n_thresholds)

    results = []
    for cfg_idx, (k, lam, n_orient, label) in enumerate(CONFIGS, 1):
        print(f"\n  [{cfg_idx}/{len(CONFIGS)}] {label} (k={k}, λ={lam}, n={n_orient})")
        kernels = build_gwi_kernels(k, lam, n_orient)

        # Run pipeline on all images
        magnitudes_raw = []
        runtimes = []
        for stem in image_stems:
            norm = img_cache[stem]
            t0 = time.perf_counter()
            mag = run_gwi(norm, kernels)
            t1 = time.perf_counter()
            runtimes.append((t1 - t0) * 1000)
            magnitudes_raw.append(mag)

        # Global normalization for threshold-sweep consistency
        min_mag = min(m.min() for m in magnitudes_raw)
        max_mag = max(m.max() for m in magnitudes_raw)
        if max_mag > min_mag:
            magnitudes = [(m - min_mag) / (max_mag - min_mag) for m in magnitudes_raw]
        else:
            magnitudes = [np.zeros_like(m) for m in magnitudes_raw]

        # Evaluate
        per_image_counts = []
        for idx, stem in enumerate(image_stems):
            gts = gt_cache[stem]
            counts = evaluate_image_thresholds(
                magnitudes[idx], gts, thresholds, max_dist_frac=0.0075
            )
            per_image_counts.append(counts)

        score, _ = aggregate_scores(per_image_counts, thresholds,
                                     dataset=dataset, method=label)

        mean_rt = float(np.mean(runtimes))
        std_rt = float(np.std(runtimes))

        print(f"      ODS = {score.ods_f:.4f}, OIS = {score.ois_f:.4f}, "
              f"AP = {score.ap:.4f}, RT = {mean_rt:.2f} ± {std_rt:.2f} ms")

        results.append({
            "dataset": dataset,
            "config": label,
            "kernel_size": k,
            "lambda": lam,
            "n_orientations": n_orient,
            "sigma": round(0.56 * lam, 3),
            "ODS": round(score.ods_f, 4),
            "OIS": round(score.ois_f, 4),
            "AP": round(score.ap, 4),
            "runtime_ms_mean": round(mean_rt, 2),
            "runtime_ms_std": round(std_rt, 2),
            "n_images": len(image_stems),
        })

    return results


# ============================================================================
# Main driver
# ============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-csv", type=Path, required=True)
    parser.add_argument("--datasets", nargs="+",
                        default=["BSDS500", "BIPED", "UDED"])
    parser.add_argument("--n-thresholds", type=int, default=33)
    args = parser.parse_args()

    args.output_csv.parent.mkdir(parents=True, exist_ok=True)

    all_results = []
    total_t0 = time.perf_counter()

    valid_datasets = [d for d in args.datasets if d in DATASET_LAYOUT]
    unknown = [d for d in args.datasets if d not in DATASET_LAYOUT]
    if unknown:
        print(f"[WARN] Unknown dataset(s) ignored: {unknown}")
        print(f"[WARN] Valid options: {list(DATASET_LAYOUT.keys())}")

    for dataset in valid_datasets:
        results = run_ablation_one_dataset(dataset, args.data_root,
                                            args.n_thresholds)
        all_results.extend(results)

    # Write combined CSV
    if all_results:
        with open(args.output_csv, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(all_results[0].keys()))
            writer.writeheader()
            writer.writerows(all_results)
        print(f"\n[OK] Combined CSV: {args.output_csv}")

    total_elapsed = (time.perf_counter() - total_t0) / 60.0
    print(f"\n[DONE] Total elapsed: {total_elapsed:.1f} minutes")

    # ========================================================================
    # Per-dataset summary tables
    # ========================================================================
    print(f"\n\n{'=' * 78}")
    print(f"  PAPER-READY TABLES (one per dataset)")
    print(f"{'=' * 78}")

    for dataset in valid_datasets:
        ds_results = [r for r in all_results if r["dataset"] == dataset]
        if not ds_results:
            continue

        print(f"\n### {dataset} ablation:\n")
        print(f"| Kernel size *k* | λ | ODS↑ | OIS↑ | AP↑ |")
        print(f"|----------------|---:|-----:|-----:|----:|")
        # Find best config by ODS for bolding
        best_idx = max(range(len(ds_results)), key=lambda i: ds_results[i]["ODS"])
        for i, r in enumerate(ds_results):
            k_str = f"{r['kernel_size']}×{r['kernel_size']}"
            if r["n_orientations"] != 8:
                k_str += f" (n_orient = {r['n_orientations']})"
            if i == best_idx:
                print(f"| **{k_str}** | **{r['lambda']:.0f}** | "
                      f"**{r['ODS']:.4f}** | **{r['OIS']:.4f}** | "
                      f"**{r['AP']:.4f}** |")
            else:
                print(f"| {k_str} | {r['lambda']:.0f} | "
                      f"{r['ODS']:.4f} | {r['OIS']:.4f} | {r['AP']:.4f} |")

    # ========================================================================
    # Cross-dataset best-config analysis
    # ========================================================================
    print(f"\n\n{'=' * 78}")
    print(f"  CROSS-DATASET ANALYSIS")
    print(f"{'=' * 78}")

    # Find best ODS config per dataset
    print(f"\nBest config (by ODS) per dataset:")
    for dataset in valid_datasets:
        ds_results = [r for r in all_results if r["dataset"] == dataset]
        if not ds_results:
            continue
        best = max(ds_results, key=lambda r: r["ODS"])
        print(f"  {dataset:10s} → k={best['kernel_size']}×{best['kernel_size']}, "
              f"λ={best['lambda']:.0f}, n={best['n_orientations']}  "
              f"(ODS={best['ODS']:.4f}, RT={best['runtime_ms_mean']:.1f}ms)")

    # Aggregate ranking across datasets
    print(f"\nMean ODS across datasets per config:")
    cfg_means = {}
    for cfg_label in [c[3] for c in CONFIGS]:
        odss = [r["ODS"] for r in all_results if r["config"] == cfg_label]
        if odss:
            cfg_means[cfg_label] = float(np.mean(odss))
    sorted_cfgs = sorted(cfg_means.items(), key=lambda x: -x[1])
    for i, (cfg, mean_ods) in enumerate(sorted_cfgs, 1):
        marker = " ← Recommended baseline (best avg)" if i == 1 else ""
        print(f"  {i}. {cfg:30s} mean ODS = {mean_ods:.4f}{marker}")

    print(f"\n{'=' * 78}")
    print(f"  RECOMMENDATION")
    print(f"{'=' * 78}")
    if cfg_means:
        best_avg_cfg = sorted_cfgs[0][0]
        print(f"\nBest overall configuration (highest mean ODS across 3 datasets):")
        print(f"  {best_avg_cfg}")
        # Get parameters
        for c in CONFIGS:
            if c[3] == best_avg_cfg:
                print(f"\n  k = {c[0]}, λ = {c[1]:.0f}, n_orientations = {c[2]}")
                print(f"  σ = {0.56 * c[1]:.3f} (derived as 0.56·λ)")
                break


if __name__ == "__main__":
    main()
