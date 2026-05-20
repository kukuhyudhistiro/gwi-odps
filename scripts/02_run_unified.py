"""
02_run_unified.py — Unified pipeline runner for all methods + GWi+ODPS
Author: Kukuh Yudhistiro, 2026

Each image is processed by all methods sequentially
in a single thread for timing-reproducibility.

Methods included:
    - GWi (Stages 1-5)
    - GWi_odps (Stages 1-6, reuses Stages 1-5 result)
    - GWC, Canny, Sobel, LoG, PC, ED

Design:
    - Each image is loaded ONCE and processed by all methods
    - GWi computation is REUSED for GWi_odps (no redundant Stages 1-5)
    - Single CSV captures everything; per-method runtime stats easy to aggregate
    - Same single-thread enforcement as previous scripts

Output:
    output/<dataset>/<method>/<image_id>.png   # 8-bit edge magnitude
    runtime_logs/runtime_unified.csv           # single combined CSV

CSV columns:
    dataset, image_id, method, height, width,
    preproc_time_s, filter_time_s, odps_time_s, total_time_s,
    magnitude_min, magnitude_max, magnitude_mean,
    status, error_message
"""

from __future__ import annotations

# Single-thread enforcement BEFORE any heavy import
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

import argparse
import collections
import csv
import gc
import sys
import time
import traceback
from pathlib import Path
from typing import Callable, Dict, List, Optional

import cv2
cv2.setNumThreads(1)
import numpy as np

# Local imports
sys.path.insert(0, str(Path(__file__).resolve().parent))
from gabor_core import GaborParams, GWCFilterBank, GWiFilterBank, run_gwc, run_gwi
from preprocessing import load_and_preprocess
from baselines import (
    run_canny_magnitude, run_sobel, run_log, run_edge_drawing,
    run_phase_congruency, HAS_PHASEPACK,
)
from edge_eval import save_edge_map
from dataset_io import DatasetIterator, Sample
from nms_odps import odps


# ============================================================================
# GWi+ODPS combined runner: re-uses Stages 1-5 result + adds ODPS
# ============================================================================

def run_gwi_with_odps(image_norm: np.ndarray,
                      gwi_bank: GWiFilterBank,
                      odps_d: int = 2) -> tuple:
    """Run full GWi+ODPS pipeline on a normalized image.

    Implementation note: this re-computes per-orientation responses to
    capture the argmax map needed by ODPS. The cost is identical to
    running GWi standalone (the argmax is essentially free).

    Returns:
        magnitude_odps : (H, W) float — Stage 6 output
        filter_time_s  : float        — time for Stages 1-5
        odps_time_s    : float        — time for Stage 6
        total_time_s   : float        — sum of the two
    """
    n_orient = gwi_bank.params.n_orientations
    h, w = image_norm.shape

    # Stages 3-5: convolve, |·|, incremental max-pool + argmax
    # (avoids np.stack → peak memory turun dari ~17× ke ~3× ukuran gambar)
    t0 = time.perf_counter()
    magnitude = np.zeros((h, w), dtype=np.float64)
    orient_idx = np.zeros((h, w), dtype=np.int32)
    for k, ki in enumerate(gwi_bank.kernels):
        resp = np.abs(cv2.filter2D(image_norm, cv2.CV_64F, ki,
                                   borderType=cv2.BORDER_CONSTANT))
        better = resp > magnitude
        magnitude[better] = resp[better]
        orient_idx[better] = k
    t1 = time.perf_counter()

    # Stage 6: ODPS
    suppressed = odps(magnitude, orient_idx,
                      n_orientations=n_orient, d=odps_d)
    t2 = time.perf_counter()

    return suppressed, t1 - t0, t2 - t1, t2 - t0


# ============================================================================
# Method registry
# ============================================================================

def build_method_registry(params: GaborParams,
                          odps_d: int = 2,
                          enabled: Optional[List[str]] = None) -> Dict[str, Callable]:
    """Build registry of method_name -> callable.

    Each callable takes (image_norm) and returns:
        (magnitude, filter_time_s, odps_time_s_or_zero)

    The combined runner expects this 3-tuple so we can log ODPS-specific
    timing for GWi_odps and zero for all other methods.
    """
    gwc_bank = GWCFilterBank(params)
    gwi_bank = GWiFilterBank(params)

    def gwi_fn(img):
        r = run_gwi(img, gwi_bank)
        return r.magnitude, r.runtime_s, 0.0

    def gwi_odps_fn(img):
        # NOTE: this re-runs Stages 3-5 to capture argmax map.
        # If we wanted to share state with the GWi_fn call, we'd need a
        # closure trick. Currently both timings are independent for fairness.
        out, ft, ot, _ = run_gwi_with_odps(img, gwi_bank, odps_d=odps_d)
        return out, ft, ot

    def gwc_fn(img):
        r = run_gwc(img, gwc_bank)
        return r.magnitude, r.runtime_s, 0.0

    def canny_fn(img):
        r = run_canny_magnitude(img)
        return r.magnitude, r.runtime_s, 0.0

    def sobel_fn(img):
        r = run_sobel(img)
        return r.magnitude, r.runtime_s, 0.0

    def log_fn(img):
        r = run_log(img)
        return r.magnitude, r.runtime_s, 0.0

    def ed_fn(img):
        r = run_edge_drawing(img)
        return r.magnitude, r.runtime_s, 0.0

    def pc_fn(img):
        r = run_phase_congruency(img)
        return r.magnitude, r.runtime_s, 0.0

    registry = {
        "GWi": gwi_fn,
        "GWi_odps": gwi_odps_fn,
        "GWC": gwc_fn,
        "Canny": canny_fn,
        "Sobel": sobel_fn,
        "LoG": log_fn,
        "ED": ed_fn,
    }
    if HAS_PHASEPACK:
        registry["PC"] = pc_fn

    if enabled is not None:
        registry = {k: v for k, v in registry.items() if k in enabled}
    return registry


# ============================================================================
# Unified runtime logger
# ============================================================================

class RuntimeLogger:
    """Single CSV logger with method-agnostic schema."""

    FIELDS = [
        "dataset", "image_id", "method",
        "height", "width",
        "preproc_time_s", "filter_time_s", "odps_time_s", "total_time_s",
        "magnitude_min", "magnitude_max", "magnitude_mean",
        "status", "error_message",
    ]

    def __init__(self, csv_path: Path, append: bool = False):
        self.csv_path = csv_path
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        new_file = not (append and self.csv_path.exists())
        self.fh = open(self.csv_path, mode, newline="", encoding="utf-8")
        self.writer = csv.DictWriter(self.fh, fieldnames=self.FIELDS)
        if new_file:
            self.writer.writeheader()
            self.fh.flush()

    def log(self, **row):
        out = {k: row.get(k, "") for k in self.FIELDS}
        self.writer.writerow(out)
        self.fh.flush()

    def close(self):
        self.fh.close()


# ============================================================================
# Per-sample driver
# ============================================================================

def process_sample(sample: Sample,
                   methods: Dict[str, Callable],
                   output_root: Path,
                   logger: RuntimeLogger) -> None:
    """Process one image: preprocess once, then run all methods."""
    try:
        t_pre = time.perf_counter()
        rgb, gray_raw, gray_eq, normalized, stats = load_and_preprocess(
            sample.image_path
        )
        preproc_time = time.perf_counter() - t_pre
    except Exception as e:
        for method_name in methods:
            logger.log(dataset=sample.dataset, image_id=sample.image_id,
                       method=method_name, status="PREPROC_FAIL",
                       error_message=str(e)[:200])
        return

    for method_name, method_fn in methods.items():
        try:
            magnitude, filter_time, odps_time = method_fn(normalized)

            # Save PNG
            out_path = (output_root / sample.dataset / method_name
                        / f"{sample.image_id}.png")
            save_edge_map(magnitude, out_path)

            logger.log(
                dataset=sample.dataset,
                image_id=sample.image_id,
                method=method_name,
                height=stats.height,
                width=stats.width,
                preproc_time_s=f"{preproc_time:.6f}",
                filter_time_s=f"{filter_time:.6f}",
                odps_time_s=f"{odps_time:.6f}" if odps_time > 0 else "",
                total_time_s=f"{preproc_time + filter_time + odps_time:.6f}",
                magnitude_min=f"{float(magnitude.min()):.4f}",
                magnitude_max=f"{float(magnitude.max()):.4f}",
                magnitude_mean=f"{float(magnitude.mean()):.4f}",
                status="OK",
            )
        except Exception as e:
            logger.log(
                dataset=sample.dataset,
                image_id=sample.image_id,
                method=method_name,
                height=stats.height,
                width=stats.width,
                status="METHOD_FAIL",
                error_message=str(e)[:200],
            )

    del rgb, gray_raw, gray_eq, normalized, stats
    gc.collect()


# ============================================================================
# Warm-up
# ============================================================================

def warmup(methods: Dict[str, Callable], n_warmup: int = 3) -> None:
    """Run each method on synthetic images to warm caches."""
    rng = np.random.default_rng(42)
    for _ in range(n_warmup):
        synthetic = rng.random((128, 128), dtype=np.float64)
        for method_name, fn in methods.items():
            try:
                _ = fn(synthetic)
            except Exception as exc:
                print(f"  [WARN] warmup {method_name}: {exc}", file=sys.stderr)


# ============================================================================
# Main
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Unified runner: all methods + GWi+ODPS, single CSV output."
    )
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--runtime-csv", type=Path, required=True,
                        help="Single combined CSV output path")
    parser.add_argument("--datasets", nargs="+",
                        default=["BSDS500", "BIPED", "UDED"])
    parser.add_argument("--methods", nargs="+", default=None,
                        help="Methods to run. Default: all available.")
    parser.add_argument("--odps-d", type=int, default=2,
                        help="ODPS neighbor distance (default 2 for λ=4)")
    parser.add_argument("--warm-up", type=int, default=3,
                        help="Number of warm-up images")
    parser.add_argument("--append", action="store_true",
                        help="Append to existing CSV instead of overwriting")
    args = parser.parse_args()

    # Build Gabor parameters (now defaults to k=5 after patch)
    params = GaborParams()
    print(f"[INFO] Gabor parameters: k={params.ksize}, λ={params.wavelength}, "
          f"σ={params.sigma:.3f}, γ={params.gamma}, "
          f"n_orient={params.n_orientations}")

    # Build method registry
    methods = build_method_registry(params, odps_d=args.odps_d,
                                     enabled=args.methods)
    print(f"[INFO] Methods enabled: {list(methods.keys())}")

    # Open logger
    logger = RuntimeLogger(args.runtime_csv, append=args.append)
    print(f"[INFO] Logging to: {args.runtime_csv}")

    iterator = DatasetIterator(data_root=args.data_root)

    total_t0 = time.perf_counter()
    try:
        # Warm-up
        print(f"[INFO] Warming up ({args.warm_up} synthetic images)...")
        warmup(methods, args.warm_up)

        # Process each dataset
        for dataset_name in args.datasets:
            print(f"\n{'=' * 60}\n  Processing: {dataset_name}\n{'=' * 60}")
            try:
                samples = list(iterator.iter_dataset(dataset_name))
            except FileNotFoundError as e:
                print(f"  [WARN] Skipping {dataset_name}: {e}")
                continue
            if not samples:
                print(f"  [WARN] No samples found for {dataset_name}")
                continue
            print(f"  Samples: {len(samples)}")

            ds_t0 = time.perf_counter()
            for i, sample in enumerate(samples, 1):
                process_sample(sample, methods, args.output_root, logger)
                if i % 25 == 0 or i == len(samples):
                    elapsed = time.perf_counter() - ds_t0
                    rate = i / elapsed if elapsed > 0 else 0
                    eta = (len(samples) - i) / rate if rate > 0 else 0
                    print(f"  {i}/{len(samples)}  "
                          f"({rate:.2f} img/s, ETA {eta/60:.1f} min)")
    finally:
        logger.close()

    total_elapsed = (time.perf_counter() - total_t0) / 60.0
    print(f"\n[DONE] Total elapsed: {total_elapsed:.1f} min")
    print(f"[OK] Combined CSV: {args.runtime_csv}")

    # Summary aggregation
    print(f"\n{'=' * 60}\n  Runtime summary\n{'=' * 60}")
    if args.append:
        print("  [NOTE] --append mode: summary mencakup seluruh data historis dalam CSV")
    _print_summary(args.runtime_csv, args.datasets, list(methods.keys()))


def _print_summary(csv_path: Path, datasets: List[str], methods: List[str]):
    """Read CSV and print mean ± std runtime per (dataset, method)."""
    if not csv_path.exists():
        return
    grouped: Dict[tuple, List[float]] = collections.defaultdict(list)
    with open(csv_path, "r", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if r["status"] == "OK":
                grouped[(r["dataset"], r["method"])].append(
                    float(r["total_time_s"])
                )
    for ds in datasets:
        print(f"\n  {ds}:")
        for m in methods:
            tt = grouped.get((ds, m), [])
            if not tt:
                continue
            mean_ms = np.mean(tt) * 1000
            std_ms = np.std(tt) * 1000
            print(f"    {m:12s}: {mean_ms:7.2f} ± {std_ms:6.2f} ms  "
                  f"(n={len(tt)})")


if __name__ == "__main__":
    main()
