"""
01_density_profiler.py
Author: Kukuh Yudhistiro, 2026

Edge Density Profiler for BSDS500, BIPED v2, and UDED datasets.

Purpose:
    Compute per-image edge density from ground-truth edge maps and classify
    each image into LOW / MID / HIGH density tertile. This stratification
    enables per-density-class analysis in the GWi paper, addressing the
    reviewer's concern about insufficient sample variation.

Input:
    Raw datasets (.mat for BSDS500, .png for BIPED and UDED).

Output:
    - density_manifest.csv : per-image record (dataset, image_id, density, tertile)
    - density_histogram.png : visualization of density distribution per dataset
    - density_summary.json : aggregate statistics per dataset

Usage:
    python 01_density_profiler.py \
        --bsds500 ./data/BSDS500 \
        --biped ./data/BIPED \
        --uded ./data/UDED \
        --output ./density_profiling

"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import List, Optional

import numpy as np
import pandas as pd
import matplotlib

matplotlib.use("Agg")  # non-interactive backend
import matplotlib.pyplot as plt
from scipy.io import loadmat
from PIL import Image


# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------

@dataclass
class DatasetSpec:
    """Specification for a single dataset."""

    name: str
    image_dir: Path        # directory containing images (for size reference)
    gt_dir: Path           # directory containing ground-truth edge files
    gt_format: str         # 'mat' (BSDS500) or 'png' (BIPED, UDED)
    split: Optional[str] = None  # for logging only


# ----------------------------------------------------------------------------
# Ground-truth loading
# ----------------------------------------------------------------------------

def load_bsds_gt(mat_path: Path) -> np.ndarray:
    """
    Load BSDS500 .mat ground truth.

    BSDS500 stores multiple annotations per image. Following the standard
    protocol used by HED/RCF/PiDiNet/EDTER, we take the UNION of all annotator
    edge maps (any pixel marked as edge by at least one annotator becomes edge).

    Returns:
        2D binary numpy array (H, W), dtype=bool.
    """
    mat = loadmat(str(mat_path))
    if "groundTruth" not in mat:
        raise ValueError(f"Unexpected .mat structure (no 'groundTruth' key): {mat_path}")

    gt_struct = mat["groundTruth"]
    # gt_struct shape: (1, N_annotators), each cell has 'Boundaries' field
    n_annotators = gt_struct.shape[1]

    union_edges = None
    for i in range(n_annotators):
        # Boundaries: (H, W) uint8 array, 1 = edge, 0 = non-edge
        boundaries = gt_struct[0, i]["Boundaries"][0, 0]
        boundaries = (boundaries > 0).astype(bool)

        if union_edges is None:
            union_edges = boundaries.copy()
        else:
            union_edges = union_edges | boundaries

    return union_edges


def load_png_gt(png_path: Path) -> np.ndarray:
    """
    Load PNG ground-truth edge map (BIPED, UDED).

    BIPED uses binary or near-binary PNG; UDED uses thin binary edges.
    We binarize at midpoint to be safe.

    Returns:
        2D binary numpy array (H, W), dtype=bool.
    """
    img = Image.open(png_path).convert("L")
    arr = np.array(img)
    # For BIPED v2: 255 = edge, 0 = non-edge. Threshold at 128.
    # For UDED: similar convention.
    return arr > 127


# ----------------------------------------------------------------------------
# Density computation
# ----------------------------------------------------------------------------

def compute_edge_density(gt_binary: np.ndarray) -> float:
    """
    Compute edge density as percentage of edge pixels.

    Args:
        gt_binary: 2D boolean array (H, W)

    Returns:
        Density as float in [0.0, 100.0] (percentage).
    """
    total_pixels = gt_binary.size
    edge_pixels = int(np.sum(gt_binary))
    return 100.0 * edge_pixels / total_pixels


# ----------------------------------------------------------------------------
# Dataset processing
# ----------------------------------------------------------------------------

def process_dataset(spec: DatasetSpec) -> List[dict]:
    """
    Process one dataset: iterate over GT files, compute density per image.

    Returns:
        List of dicts, each with keys: dataset, image_id, height, width,
        n_edge_pixels, density_pct.
    """
    records = []

    if spec.gt_format == "mat":
        gt_files = sorted(spec.gt_dir.glob("*.mat"))
    elif spec.gt_format == "png":
        gt_files = sorted(spec.gt_dir.glob("*.png"))
    else:
        raise ValueError(f"Unknown gt_format: {spec.gt_format}")

    if not gt_files:
        print(f"[WARN] No GT files found in {spec.gt_dir}", file=sys.stderr)
        return records

    print(f"\n[{spec.name}] Processing {len(gt_files)} ground-truth files...")

    for i, gt_path in enumerate(gt_files):
        try:
            if spec.gt_format == "mat":
                gt = load_bsds_gt(gt_path)
            else:
                gt = load_png_gt(gt_path)
        except Exception as e:
            print(f"[ERROR] Failed to load {gt_path}: {e}", file=sys.stderr)
            continue

        density = compute_edge_density(gt)
        h, w = gt.shape
        n_edges = int(np.sum(gt))

        records.append({
            "dataset": spec.name,
            "image_id": gt_path.stem,
            "height": int(h),
            "width": int(w),
            "n_edge_pixels": n_edges,
            "density_pct": round(density, 4),
        })

        if (i + 1) % 20 == 0 or (i + 1) == len(gt_files):
            print(f"  [{spec.name}] {i+1}/{len(gt_files)} processed")

    return records


# ----------------------------------------------------------------------------
# Tertile classification
# ----------------------------------------------------------------------------

def assign_tertiles_per_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Assign LOW / MID / HIGH tertile label to each image based on its density
    relative to its own dataset's distribution.

    This is per-dataset because absolute density values differ across
    datasets (BIPED is denser than BSDS500 on average due to texture edges).

    Adds two columns: tertile_label, tertile_rank (1=LOW, 2=MID, 3=HIGH).
    """
    df = df.copy()
    df["tertile_label"] = None
    df["tertile_rank"] = None

    for ds_name, group in df.groupby("dataset"):
        # Compute 33.33 and 66.67 percentiles
        p33 = np.percentile(group["density_pct"], 33.333)
        p67 = np.percentile(group["density_pct"], 66.667)

        def classify(d):
            if d <= p33:
                return "LOW", 1
            elif d <= p67:
                return "MID", 2
            else:
                return "HIGH", 3

        labels = group["density_pct"].apply(classify)
        df.loc[group.index, "tertile_label"] = labels.apply(lambda x: x[0])
        df.loc[group.index, "tertile_rank"] = labels.apply(lambda x: x[1])

        print(f"  [{ds_name}] p33={p33:.3f}%, p67={p67:.3f}% "
              f"| LOW <={p33:.3f}, MID <={p67:.3f}, HIGH >{p67:.3f}")

    return df


# ----------------------------------------------------------------------------
# Visualization
# ----------------------------------------------------------------------------

def plot_density_distributions(df: pd.DataFrame, output_path: Path) -> None:
    """Plot density histogram per dataset, side by side."""
    datasets = sorted(df["dataset"].unique())
    n_ds = len(datasets)

    fig, axes = plt.subplots(1, n_ds, figsize=(5 * n_ds, 4), sharey=False)
    if n_ds == 1:
        axes = [axes]

    for ax, ds_name in zip(axes, datasets):
        sub = df[df["dataset"] == ds_name]
        densities = sub["density_pct"].values
        p33 = np.percentile(densities, 33.333)
        p67 = np.percentile(densities, 66.667)

        ax.hist(densities, bins=30, edgecolor="black", alpha=0.75)
        ax.axvline(p33, color="orange", linestyle="--",
                   label=f"p33 = {p33:.2f}%")
        ax.axvline(p67, color="red", linestyle="--",
                   label=f"p67 = {p67:.2f}%")
        ax.set_xlabel("Edge density (%)")
        ax.set_ylabel("Number of images")
        ax.set_title(f"{ds_name} (n={len(sub)})")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)

    plt.suptitle("Edge density distribution per dataset (ground-truth)",
                 fontsize=12, y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"[OK] Density histogram saved: {output_path}")


# ----------------------------------------------------------------------------
# Summary statistics
# ----------------------------------------------------------------------------

def build_summary(df: pd.DataFrame) -> dict:
    """Build per-dataset summary statistics."""
    summary = {}
    for ds_name, group in df.groupby("dataset"):
        densities = group["density_pct"].values
        summary[ds_name] = {
            "n_images": int(len(group)),
            "density_mean_pct": float(np.mean(densities)),
            "density_std_pct": float(np.std(densities)),
            "density_min_pct": float(np.min(densities)),
            "density_p25_pct": float(np.percentile(densities, 25)),
            "density_p50_pct": float(np.percentile(densities, 50)),
            "density_p75_pct": float(np.percentile(densities, 75)),
            "density_max_pct": float(np.max(densities)),
            "p33_threshold_pct": float(np.percentile(densities, 33.333)),
            "p67_threshold_pct": float(np.percentile(densities, 66.667)),
            "n_LOW": int(np.sum(group["tertile_label"] == "LOW")),
            "n_MID": int(np.sum(group["tertile_label"] == "MID")),
            "n_HIGH": int(np.sum(group["tertile_label"] == "HIGH")),
        }
    return summary


# ----------------------------------------------------------------------------
# CLI
# ----------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Edge density profiler for GWi paper (JESA)."
    )
    parser.add_argument("--bsds500", type=Path,
                        help="Path to BSDS500 root directory")
    parser.add_argument("--biped", type=Path,
                        help="Path to BIPED root directory")
    parser.add_argument("--uded", type=Path,
                        help="Path to UDED root directory")
    parser.add_argument("--output", type=Path, required=True,
                        help="Output directory for manifest, histogram, summary")
    parser.add_argument("--bsds-gt-subdir", type=str,
                        default="groundTruth/test",
                        help="Subdir under bsds500 root containing GT .mat files")
    parser.add_argument("--biped-gt-subdir", type=str,
                        default="edge_maps/test",
                        help="Subdir under biped root containing GT .png files")
    parser.add_argument("--uded-gt-subdir", type=str,
                        default="gt",
                        help="Subdir under uded root containing GT .png files")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    specs: List[DatasetSpec] = []

    if args.bsds500 and args.bsds500.exists():
        gt_dir = args.bsds500 / args.bsds_gt_subdir
        img_dir = args.bsds500 / "images" / "test"
        if gt_dir.exists():
            specs.append(DatasetSpec(
                name="BSDS500",
                image_dir=img_dir,
                gt_dir=gt_dir,
                gt_format="mat",
                split="test",
            ))
        else:
            print(f"[WARN] BSDS500 GT dir not found: {gt_dir}")

    if args.biped and args.biped.exists():
        gt_dir = args.biped / args.biped_gt_subdir
        img_dir = args.biped / "edges/imgs/test"
        if gt_dir.exists():
            specs.append(DatasetSpec(
                name="BIPED",
                image_dir=img_dir,
                gt_dir=gt_dir,
                gt_format="png",
                split="test",
            ))
        else:
            print(f"[WARN] BIPED GT dir not found: {gt_dir}")

    if args.uded and args.uded.exists():
        gt_dir = args.uded / args.uded_gt_subdir
        img_dir = args.uded / "imgs"
        if gt_dir.exists():
            specs.append(DatasetSpec(
                name="UDED",
                image_dir=img_dir,
                gt_dir=gt_dir,
                gt_format="png",
                split="all",
            ))
        else:
            print(f"[WARN] UDED GT dir not found: {gt_dir}")

    if not specs:
        print("[ERROR] No valid datasets found. Check paths.", file=sys.stderr)
        sys.exit(1)

    # ------------------------------------------------------------------
    # 1. Process each dataset
    # ------------------------------------------------------------------
    all_records: List[dict] = []
    for spec in specs:
        all_records.extend(process_dataset(spec))

    if not all_records:
        print("[ERROR] No records collected. Aborting.", file=sys.stderr)
        sys.exit(1)

    df = pd.DataFrame(all_records)

    # ------------------------------------------------------------------
    # 2. Assign tertiles per dataset
    # ------------------------------------------------------------------
    print("\n[INFO] Assigning tertile labels per dataset...")
    df = assign_tertiles_per_dataset(df)

    # ------------------------------------------------------------------
    # 3. Save manifest CSV
    # ------------------------------------------------------------------
    manifest_path = args.output / "density_manifest.csv"
    df.to_csv(manifest_path, index=False)
    print(f"\n[OK] Density manifest saved: {manifest_path}")

    # ------------------------------------------------------------------
    # 4. Plot histograms
    # ------------------------------------------------------------------
    hist_path = args.output / "density_histogram.png"
    plot_density_distributions(df, hist_path)

    # ------------------------------------------------------------------
    # 5. Save summary JSON
    # ------------------------------------------------------------------
    summary = build_summary(df)
    summary_path = args.output / "density_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"[OK] Density summary saved: {summary_path}")

    # ------------------------------------------------------------------
    # 6. Print quick report
    # ------------------------------------------------------------------
    print("\n" + "=" * 70)
    print("EDGE DENSITY PROFILING SUMMARY")
    print("=" * 70)
    for ds_name, s in summary.items():
        print(f"\n{ds_name} (n={s['n_images']})")
        print(f"  Density: mean={s['density_mean_pct']:.3f}% "
              f"std={s['density_std_pct']:.3f}% "
              f"range=[{s['density_min_pct']:.3f}, {s['density_max_pct']:.3f}]%")
        print(f"  Tertile thresholds: p33={s['p33_threshold_pct']:.3f}%, "
              f"p67={s['p67_threshold_pct']:.3f}%")
        print(f"  Distribution: LOW={s['n_LOW']}, MID={s['n_MID']}, "
              f"HIGH={s['n_HIGH']}")
    print("=" * 70)
    print(f"\n[DONE] Outputs written to: {args.output}")


if __name__ == "__main__":
    main()
