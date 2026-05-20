"""
generate_final_figures.py — FINAL paper figures (v3)

Updates from 06b:
  1. ADD black border around every image cell (1.0 pt line width)
  2. INCLUDE GWi+ODPS in qualitative figure (now 8 methods + Image + GT = 10 rows)
  3. Run on 3 datasets with sample IDs from user spec

Sample IDs (updated):
  BSDS500: 3063, 29030, 36046, 48017
  BIPED:   RGB_042, RGB_070, RGB_138
  UDED:    05-WIREFRAME-2, 04-0896x4, 28-img_043_SRF_2_HR

Method order (top to bottom):
  Image → Ground Truth → Canny → Sobel → LoG → PC → ED → GWC → GWi → GWi+ODPS (ours)

Author: Kukuh Yudhistiro
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from scipy.io import loadmat


# ============================================================================
# Configuration
# ============================================================================

# Method order (top to bottom in qualitative figure)
# Note: GWi as ablation reference; GWi+ODPS as the proposed method
METHOD_ORDER_DISPLAY = ["Canny", "Sobel", "LoG", "PC", "ED", "GWC",
                        "GWi", "GWi_odps"]

# Display labels
METHOD_LABELS = {
    "Canny": "Canny", "Sobel": "Sobel", "LoG": "LoG", "PC": "PC",
    "ED": "ED", "GWC": "GWC", "GWi": "GWi",
    "GWi_odps": "GWi+ODPS\n(ours)",
}

METHOD_COLORS = {
    "GWi_odps": "#D62728",   # red — proposed
    "GWi":      "#FF6B6B",   # lighter red — ablation
    "GWC":      "#FF7F0E",
    "Canny":    "#2CA02C",
    "Sobel":    "#9467BD",
    "LoG":      "#8C564B",
    "PC":       "#17BECF",
    "ED":       "#7F7F7F",
    "Human":    "#006400",
}

# Sample IDs
DEFAULT_SAMPLES = {
    "BSDS500": ["3063", "29030", "36046", "48017"],
    "BIPED":   ["RGB_042", "RGB_070", "RGB_138"],
    "UDED":    ["05-WIREFRAME-2", "04-0896x4", "28-img_043_SRF_2_HR"],
}

IMAGE_SUBDIR = {
    "BSDS500": "images/test",
    "BIPED":   "edges/imgs/test",
    "UDED":    "imgs",
}
GT_SUBDIR = {
    "BSDS500": "groundTruth/test",
    "BIPED":   "edge_maps/test",
    "UDED":    "gt",
}

HUMAN_BASELINE = {
    "BSDS500": {"ods": 0.803, "source": "Arbelaez et al., TPAMI 2011"},
}

BORDER_WIDTH = 1.0   # Black border width in points
BORDER_COLOR = "black"


# ============================================================================
# Style setup
# ============================================================================

def setup_matplotlib():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman", "Times"],
        "font.size": 8,
        "axes.titlesize": 9,
        "axes.labelsize": 8,
        "legend.fontsize": 7,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "axes.grid": True,
        "grid.alpha": 0.25,
        "grid.linestyle": "--",
        "axes.spines.top": False,
        "axes.spines.right": False,
    })


# ============================================================================
# Loaders
# ============================================================================

def find_image_file(image_dir: Path, image_id: str) -> Optional[Path]:
    for ext in [".jpg", ".jpeg", ".png", ".JPG", ".PNG"]:
        p = image_dir / f"{image_id}{ext}"
        if p.exists():
            return p
    return None


def load_gt_for_display(dataset: str, gt_dir: Path,
                        image_id: str) -> Optional[np.ndarray]:
    if dataset == "BSDS500":
        gt_path = gt_dir / f"{image_id}.mat"
        if not gt_path.exists():
            return None
        mat = loadmat(str(gt_path))
        gt_struct = mat["groundTruth"]
        union = None
        for a in range(gt_struct.shape[1]):
            b = (gt_struct[0, a]["Boundaries"][0, 0] > 0).astype(np.uint8)
            union = b if union is None else (union | b)
        return (union * 255).astype(np.uint8)
    else:
        gt_path = gt_dir / f"{image_id}.png"
        if not gt_path.exists():
            return None
        arr = np.array(Image.open(gt_path).convert("L"))
        return ((arr > 127).astype(np.uint8) * 255)


def apply_black_border(ax) -> None:
    """Add a clean black rectangular border around the axes (image cell)."""
    for spine in ax.spines.values():
        spine.set_visible(True)
        spine.set_edgecolor(BORDER_COLOR)
        spine.set_linewidth(BORDER_WIDTH)


# ============================================================================
# Figure: Per-dataset qualitative (LGLNet-style with ODPS)
# ============================================================================

def figure_qualitative_per_dataset(dataset: str,
                                   data_root: Path,
                                   output_root: Path,
                                   sample_ids: List[str],
                                   methods: List[str],
                                   output_path: Path) -> bool:
    image_dir = data_root / dataset / IMAGE_SUBDIR[dataset]
    gt_dir = data_root / dataset / GT_SUBDIR[dataset]

    if not image_dir.exists() or not gt_dir.exists():
        print(f"[WARN] {dataset}: paths missing")
        return False

    row_labels = ["Image", "Ground Truth"] + [METHOD_LABELS.get(m, m)
                                              for m in methods]
    n_rows = len(row_labels)
    n_cols = len(sample_ids)

    # Figure size: per-cell ~2 inches wide × 1.3 inches tall
    fig, axes = plt.subplots(n_rows, n_cols,
                              figsize=(n_cols * 2.0, n_rows * 1.3),
                              squeeze=False)

    for c, image_id in enumerate(sample_ids):
        # Row 0: Source image
        img_path = find_image_file(image_dir, image_id)
        if img_path is not None:
            try:
                img = np.array(Image.open(img_path).convert("RGB"))
                axes[0, c].imshow(img, aspect="auto")
            except Exception as e:
                print(f"  [WARN] {dataset}/{image_id}: cannot load: {e}")

        # Row 1: GT (inverted: white bg, black edges)
        gt = load_gt_for_display(dataset, gt_dir, image_id)
        if gt is not None:
            axes[1, c].imshow(gt, cmap="gray_r", vmin=0, vmax=255,
                              aspect="auto")

        # Rows 2..N: each method
        for r, method in enumerate(methods, start=2):
            edge_path = output_root / dataset / method / f"{image_id}.png"
            if edge_path.exists():
                edge = np.array(Image.open(edge_path).convert("L"))
                axes[r, c].imshow(edge, cmap="gray_r", vmin=0, vmax=255,
                                  aspect="auto")
            else:
                # Placeholder if missing
                axes[r, c].imshow(np.ones((100, 100)) * 255,
                                  cmap="gray", vmin=0, vmax=255,
                                  aspect="auto")
                print(f"  [WARN] missing: {edge_path}")

        # Apply black border + remove ticks on all cells in this column
        for r in range(n_rows):
            axes[r, c].set_xticks([])
            axes[r, c].set_yticks([])
            apply_black_border(axes[r, c])

    # Row labels on the left
    for r, label in enumerate(row_labels):
        is_ours = "GWi+ODPS" in label or "ours" in label.lower()
        is_baseline_gwi = label == "GWi"

        if is_ours:
            color, weight = METHOD_COLORS["GWi_odps"], "bold"
        elif is_baseline_gwi:
            color, weight = "#666666", "normal"
        else:
            color, weight = "black", "normal"

        axes[r, 0].set_ylabel(label,
                               rotation=0,
                               fontsize=9,
                               labelpad=48,
                               ha="right", va="center",
                               color=color, weight=weight)

    # Spacing kecil & uniform untuk efisiensi space di MS Word.
    # wspace/hspace = fraksi terhadap lebar/tinggi axes (sudah uniform
    # by definition). aspect="auto" di atas memastikan tiap axes punya
    # dimensi identik sehingga jarak terlihat konsisten.
    plt.subplots_adjust(left=0.11, right=0.995, top=0.995, bottom=0.005,
                        wspace=0.015, hspace=0.015)
    plt.savefig(output_path, dpi=300, bbox_inches="tight",
                pad_inches=0.02, facecolor="white")
    plt.close()
    print(f"[OK] {output_path}")
    return True


# ============================================================================
# Figure: PR curves with GWi and GWi+ODPS
# ============================================================================

def figure_pr_curves_per_dataset(dataset: str,
                                 pr_curve_dir: Path,
                                 ods_summary: pd.DataFrame,
                                 output_path: Path,
                                 methods: List[str]) -> bool:
    fig, ax = plt.subplots(figsize=(5.5, 4.5))

    # Iso-F contours
    f_values = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    for f in f_values:
        r = np.linspace(f / (2 - f) + 1e-3, 1.0, 200)
        p = (f * r) / np.maximum(2 * r - f, 1e-10)
        valid = (p >= 0) & (p <= 1.0)
        ax.plot(r[valid], p[valid], color="lightgray",
                linestyle=":", linewidth=0.7, zorder=0)
        if valid.any():
            idx = np.where(valid)[0][-1]
            ax.annotate(f"F={f:.1f}",
                        xy=(r[idx] * 0.97, p[idx] * 0.96),
                        color="gray", fontsize=6.5, alpha=0.85)

    # Each method's PR curve
    for method in methods:
        pr_path = pr_curve_dir / f"pr_curve_{dataset}_{method}.csv"
        if not pr_path.exists():
            print(f"  [WARN] missing PR curve: {pr_path}")
            continue
        df = pd.read_csv(pr_path)
        color = METHOD_COLORS.get(method, "#333333")

        ods_row = ods_summary[(ods_summary["dataset"] == dataset) &
                               (ods_summary["method"] == method)]
        ods_val = ods_row["ods_f"].values[0] if not ods_row.empty else 0

        is_ours_main = method == "GWi_odps"
        is_ours_baseline = method == "GWi"

        if is_ours_main:
            lw, ls = 2.2, "-"
            label = f"[F={ods_val:.3f}] GWi+ODPS (ours)"
            zorder = 4
        elif is_ours_baseline:
            lw, ls = 1.4, "-."
            label = f"[F={ods_val:.3f}] GWi (ablation)"
            zorder = 3
        else:
            lw, ls = 1.3, "--"
            label = f"[F={ods_val:.3f}] {method}"
            zorder = 2

        ax.plot(df["recall"], df["precision"],
                color=color, linewidth=lw, linestyle=ls,
                label=label, zorder=zorder)

    # Human baseline (BSDS500 only)
    if dataset in HUMAN_BASELINE:
        h_ods = HUMAN_BASELINE[dataset]["ods"]
        ax.scatter([h_ods], [h_ods], s=80,
                   color="#006400", marker="o",
                   edgecolor="black", linewidth=1.2,
                   label=f"[F={h_ods:.3f}] Human",
                   zorder=5)
        ax.annotate("Human",
                    xy=(h_ods, h_ods),
                    xytext=(h_ods - 0.12, h_ods + 0.02),
                    fontsize=8, color="#006400", weight="bold")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Recall")
    ax.set_ylabel("Precision")
    ax.set_title(f"{dataset}")
    ax.legend(loc="lower left", fontsize=7, framealpha=0.95,
              handlelength=2.0, handletextpad=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight",
                facecolor="white")
    plt.close()
    print(f"[OK] {output_path}")
    return True


# ============================================================================
# Tables generator
# ============================================================================

def print_quantitative_table_per_dataset(dataset: str,
                                          ods_summary: pd.DataFrame,
                                          methods: List[str]) -> str:
    lines = []
    lines.append(f"\n### Table — Quantitative comparison on {dataset}")
    lines.append("")
    lines.append("| Method | ODS↑ | OIS↑ | AP↑ |")
    lines.append("|--------|------:|------:|------:|")

    if dataset in HUMAN_BASELINE:
        h = HUMAN_BASELINE[dataset]["ods"]
        lines.append(f"| Human | {h:.3f} | — | — |")

    for method in methods:
        sub = ods_summary[(ods_summary["dataset"] == dataset) &
                           (ods_summary["method"] == method)]
        if sub.empty:
            continue
        ods = sub["ods_f"].values[0]
        ois = sub["ois_f"].values[0]
        ap = sub["ap"].values[0]

        is_proposed = method == "GWi_odps"
        label = METHOD_LABELS.get(method, method).replace("\n(ours)", " (ours)")
        if is_proposed:
            lines.append(f"| **{label}** | **{ods:.4f}** | "
                         f"**{ois:.4f}** | **{ap:.4f}** |")
        else:
            lines.append(f"| {label} | {ods:.4f} | "
                         f"{ois:.4f} | {ap:.4f} |")

    table_str = "\n".join(lines)
    print(table_str)
    return table_str


# ============================================================================
# Main driver
# ============================================================================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--data-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--pr-curve-dir", type=Path, required=True)
    parser.add_argument("--ods-summary", type=Path, required=True)
    parser.add_argument("--figures-dir", type=Path, required=True)
    parser.add_argument("--tables-out", type=Path, default=None)
    parser.add_argument("--datasets", nargs="+",
                        default=["BSDS500", "BIPED", "UDED"])
    args = parser.parse_args()

    args.figures_dir.mkdir(parents=True, exist_ok=True)
    setup_matplotlib()

    ods_summary = pd.read_csv(args.ods_summary)
    ods_summary = ods_summary[~ods_summary["method"].str.endswith("_binary")]

    all_tables = []
    for dataset in args.datasets:
        print(f"\n{'=' * 60}")
        print(f"  Dataset: {dataset}")
        print(f"{'=' * 60}")

        sample_ids = DEFAULT_SAMPLES.get(dataset, [])
        if not sample_ids:
            continue

        # 1. Qualitative figure (with black borders + GWi+ODPS)
        qual_path = args.figures_dir / f"fig_qualitative_{dataset}.png"
        figure_qualitative_per_dataset(
            dataset=dataset,
            data_root=args.data_root,
            output_root=args.output_root,
            sample_ids=sample_ids,
            methods=METHOD_ORDER_DISPLAY,
            output_path=qual_path,
        )

        # 2. PR curve (with GWi and GWi+ODPS)
        pr_path = args.figures_dir / f"fig_pr_curve_{dataset}.png"
        figure_pr_curves_per_dataset(
            dataset=dataset,
            pr_curve_dir=args.pr_curve_dir,
            ods_summary=ods_summary,
            output_path=pr_path,
            methods=METHOD_ORDER_DISPLAY,
        )

        # 3. Table
        tbl = print_quantitative_table_per_dataset(
            dataset=dataset,
            ods_summary=ods_summary,
            methods=METHOD_ORDER_DISPLAY,
        )
        all_tables.append(tbl)

    if args.tables_out is not None:
        with open(args.tables_out, "w", encoding="utf-8") as f:
            f.write("\n\n".join(all_tables))
        print(f"\n[OK] Tables: {args.tables_out}")

    print(f"\n[DONE] Figures saved to {args.figures_dir}")


if __name__ == "__main__":
    main()