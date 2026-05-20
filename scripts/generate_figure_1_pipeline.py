"""
generate_figure_1_pipeline.py — Figure 1: GWi+ODPS Pipeline Overview

Six-stage pipeline schematic with embedded illustrative images at each stage.
Designed for paper inclusion at 300 DPI.

DEFAULT STAGE IMAGES are placeholder synthetic patterns; replace with real
test images from your dataset via either:
  (a) Edit the STAGE_IMAGES dict at the top of this file, OR
  (b) Pass --stage-image-N <path> for each stage as CLI arguments.

Layout: 2 rows × 3 columns of stage panels, with arrows showing flow:
    Row 1: Stage 1 → Stage 2 → Stage 3
                                  ↓
    Row 2: Stage 4 ← Stage 5 ← Stage 6 (proposed)
    Wait, no - flow is left-to-right within rows:
    Row 1: Stage 1 → Stage 2 → Stage 3
                                  ↓ (wraps)
    Row 2: Stage 4 → Stage 5 → Stage 6 (proposed)

Author: Kukuh Yudhistiro
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

import matplotlib
matplotlib.use("Agg")
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch
from matplotlib.path import Path as MPath
from PIL import Image


# ============================================================================
# STAGE METADATA — EDIT TO CUSTOMIZE
# ============================================================================

STAGE_IMAGES = {
    1: None,
    2: None,
    3: None,
    4: None,
    5: None,
    6: None,
}

STAGE_INFO = {
    1: {"title": "Stage 1: Preprocessing",
        "desc": "BT.601 grayscale +\nhistogram equalization"},
    2: {"title": "Stage 2: Kernel construction",
        "desc": "8 imaginary Gabor kernels\nat 22.5° spacing"},
    3: {"title": "Stage 3: Convolution",
        "desc": "Rθ = Inorm ⊛ gθ\n(8 oriented responses)"},
    4: {"title": "Stage 4: Magnitude",
        "desc": "Mθ(x, y) = |Rθ(x, y)|"},
    5: {"title": "Stage 5: Max-pooling",
        "desc": "E = maxθ Mθ ,  argmax\nθ* stored for Stage 6"},
    6: {"title": "Stage 6: ODPS (proposed)",
        "desc": "Suppress side-lobes\nusing θ* from Stage 5"},
}


# ============================================================================
# Placeholder image generators
# ============================================================================

def make_placeholder_preprocessed(seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = 100, 130
    img = np.zeros((h, w), dtype=np.float32)
    img[20:80, 25:75] = 0.7
    yy, xx = np.mgrid[:h, :w]
    img[(yy + xx > 110) & (yy + xx < 130) & (xx > 80)] = 0.95
    img += rng.normal(0, 0.03, size=(h, w))
    return np.clip(img, 0, 1)


def make_placeholder_kernels() -> np.ndarray:
    ksize = 13
    n_orient = 8
    kernels = []
    for i in range(n_orient):
        theta = np.deg2rad(i * 180.0 / n_orient)
        half = ksize // 2
        y, x = np.mgrid[-half:half + 1, -half:half + 1].astype(np.float64)
        x_t = x * np.cos(theta) + y * np.sin(theta)
        y_t = -x * np.sin(theta) + y * np.cos(theta)
        gauss = np.exp(-0.5 * (x_t ** 2 + 0.25 * y_t ** 2) / (2.24 ** 2))
        sinusoidal = 2 * np.pi * x_t / 4.0
        k = gauss * np.sin(sinusoidal)
        k_max = float(np.max(np.abs(k)))
        if k_max > 1e-6:
            k = k / k_max
        kernels.append(k)
    gap = 2
    rows, cols = 2, 4
    h_total = rows * ksize + (rows - 1) * gap
    w_total = cols * ksize + (cols - 1) * gap
    grid = np.full((h_total, w_total), 0.0, dtype=np.float32)
    for idx, k in enumerate(kernels):
        r, c = idx // cols, idx % cols
        y0 = r * (ksize + gap)
        x0 = c * (ksize + gap)
        grid[y0:y0 + ksize, x0:x0 + ksize] = k
    return grid


def make_placeholder_response(seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = 100, 130
    img = np.zeros((h, w), dtype=np.float32)
    for offset, mag in [(-3, -0.4), (-2, -0.7), (-1, -1.0),
                          (0, 0.0),
                          (1, 1.0), (2, 0.7), (3, 0.4)]:
        col = 50 + offset
        if 0 <= col < w:
            img[:, col] = mag
    img += rng.normal(0, 0.03, size=(h, w))
    return img


def make_placeholder_magnitude(seed: int = 42) -> np.ndarray:
    return np.abs(make_placeholder_response(seed))


def make_placeholder_pooled(seed: int = 42) -> np.ndarray:
    rng = np.random.default_rng(seed)
    h, w = 100, 130
    img = np.zeros((h, w), dtype=np.float32)
    for offset, mag in [(-3, 0.4), (-2, 0.7), (-1, 1.0),
                          (0, 0.4),
                          (1, 1.0), (2, 0.7), (3, 0.4)]:
        col = 50 + offset
        if 0 <= col < w:
            img[:, col] = np.maximum(img[:, col], mag)
    for offset, mag in [(-3, 0.3), (-2, 0.6), (-1, 0.9),
                          (0, 0.4),
                          (1, 0.9), (2, 0.6), (3, 0.3)]:
        row = 45 + offset
        if 0 <= row < h:
            img[row, :] = np.maximum(img[row, :], mag)
    img += rng.normal(0, 0.02, size=(h, w))
    return np.clip(img, 0, 1)


def make_placeholder_odps(seed: int = 42) -> np.ndarray:
    h, w = 100, 130
    img = np.zeros((h, w), dtype=np.float32)
    img[:, 49] = 1.0
    img[:, 51] = 1.0
    img[44, :] = 0.9
    img[46, :] = 0.9
    return img


PLACEHOLDER_GENERATORS = {
    1: make_placeholder_preprocessed,
    2: make_placeholder_kernels,
    3: make_placeholder_response,
    4: make_placeholder_magnitude,
    5: make_placeholder_pooled,
    6: make_placeholder_odps,
}


def load_stage_image(stage_num: int, path: Optional[str]) -> tuple:
    """Returns (image_array, is_signed)."""
    is_signed = (stage_num in (2, 3))
    if path and Path(path).exists():
        try:
            img = np.array(Image.open(path).convert("L"))
            return img.astype(np.float32) / 255.0, False
        except Exception as e:
            print(f"[WARN] Stage {stage_num}: failed to load {path}: {e}")
    return PLACEHOLDER_GENERATORS[stage_num](), is_signed


# ============================================================================
# Plotting
# ============================================================================

def generate_figure_1(output_path: Path, stage_image_paths: dict):
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman"],
        "font.size": 9,
    })

    fig = plt.figure(figsize=(14, 8.0), facecolor="white")

    # Layout constants (figure-fraction)
    n_cols = 3
    h_gap = 0.045
    v_gap = 0.075

    panel_w = 0.265
    title_h = 0.045
    image_h = 0.270
    desc_h = 0.070
    panel_h_total = title_h + image_h + desc_h

    left_margin = 0.05
    top_margin = 0.07

    panel_colors = {
        1: ("#E8F4F8", "#5B8FB0"),
        2: ("#E8F4F8", "#5B8FB0"),
        3: ("#E8F4F8", "#5B8FB0"),
        4: ("#E8F4F8", "#5B8FB0"),
        5: ("#E8F4F8", "#5B8FB0"),
        6: ("#FDECEC", "#C9302F"),
    }

    panel_bounds = {}

    for stage_num in range(1, 7):
        idx = stage_num - 1
        row = idx // n_cols
        col = idx % n_cols

        x_panel = left_margin + col * (panel_w + h_gap)
        y_panel_top = 1.0 - top_margin - row * (panel_h_total + v_gap)
        y_panel_bot = y_panel_top - panel_h_total

        # Background panel
        bg_color, border_color = panel_colors[stage_num]
        bg_rect = mpatches.FancyBboxPatch(
            (x_panel, y_panel_bot), panel_w, panel_h_total,
            boxstyle="round,pad=0.005,rounding_size=0.015",
            facecolor=bg_color,
            edgecolor=border_color,
            linewidth=1.5,
            transform=fig.transFigure,
            zorder=1,
        )
        fig.patches.append(bg_rect)

        # Title (top strip)
        title_y_center = y_panel_top - title_h / 2
        title_color = "#000000" if stage_num != 6 else "#8B1A1B"
        fig.text(x_panel + panel_w / 2,
                 title_y_center,
                 STAGE_INFO[stage_num]["title"],
                 ha="center", va="center",
                 fontsize=12.0,
                 fontweight="bold",
                 color=title_color,
                 transform=fig.transFigure,
                 zorder=3)

        # Image axes
        img_inset_x = 0.018
        img_inset_y = 0.008
        img_x = x_panel + img_inset_x
        img_y_bot = y_panel_top - title_h - image_h + img_inset_y
        img_w_axes = panel_w - 2 * img_inset_x
        img_h_axes = image_h - 2 * img_inset_y

        ax_img = fig.add_axes([img_x, img_y_bot, img_w_axes, img_h_axes],
                              zorder=2)

        img, is_signed = load_stage_image(stage_num,
                                           stage_image_paths.get(stage_num))
        if is_signed:
            vmax = float(np.max(np.abs(img)))
            ax_img.imshow(img, cmap="RdBu_r", vmin=-vmax, vmax=vmax,
                          aspect="auto", interpolation="nearest")
        else:
            ax_img.imshow(img, cmap="gray", aspect="auto",
                          interpolation="nearest")
        ax_img.set_xticks([])
        ax_img.set_yticks([])
        for spine in ax_img.spines.values():
            spine.set_visible(True)
            spine.set_edgecolor("black")
            spine.set_linewidth(0.8)

        # Description (bottom strip)
        desc_y_center = y_panel_bot + desc_h / 2
        fig.text(x_panel + panel_w / 2,
                 desc_y_center,
                 STAGE_INFO[stage_num]["desc"],
                 ha="center", va="center",
                 fontsize=11.50,
                 color="#000000",
                 transform=fig.transFigure,
                 zorder=3,
                 linespacing=1.35)

        # Bounds for arrows
        panel_bounds[stage_num] = {
            "x_left": x_panel,
            "x_right": x_panel + panel_w,
            "y_top": y_panel_top,
            "y_bottom": y_panel_bot,
            "y_center": (y_panel_top + y_panel_bot) / 2,
            "x_center": x_panel + panel_w / 2,
        }

    # --- Inter-stage arrows ---
    arrow_color = "#444444"
    arrow_lw = 2.0

    # Horizontal arrows: 1→2, 2→3, 4→5, 5→6
    for from_s, to_s in [(1, 2), (2, 3), (4, 5), (5, 6)]:
        fp = panel_bounds[from_s]
        tp = panel_bounds[to_s]
        y_mid = (fp["y_center"] + tp["y_center"]) / 2
        arrow = FancyArrowPatch(
            (fp["x_right"] + 0.005, y_mid),
            (tp["x_left"] - 0.005, y_mid),
            transform=fig.transFigure,
            arrowstyle="-|>",
            mutation_scale=22,
            color=arrow_color,
            linewidth=arrow_lw,
            zorder=4,
        )
        fig.patches.append(arrow)

    # Wrap arrow: from Stage 3 → Stage 4 (right column row 1 → left column row 2)
    fp = panel_bounds[3]
    tp = panel_bounds[4]
    # Route: out the right of S3 → curve down + left → into the left of S4
    via_x = fp["x_right"] + 0.025
    via_y = (fp["y_bottom"] + tp["y_top"]) / 2

    verts = [
        (fp["x_right"] + 0.005, fp["y_center"]),
        (via_x, fp["y_center"]),
        (via_x, via_y),
        (tp["x_left"] - 0.025, via_y),
        (tp["x_left"] - 0.025, tp["y_center"]),
        (tp["x_left"] - 0.005, tp["y_center"]),
    ]
    codes = [MPath.MOVETO] + [MPath.LINETO] * 5
    path = MPath(verts, codes)
    arrow = FancyArrowPatch(
        path=path,
        transform=fig.transFigure,
        arrowstyle="-|>",
        mutation_scale=22,
        color=arrow_color,
        linewidth=arrow_lw,
        zorder=4,
        fill=False,
    )
    fig.patches.append(arrow)

    # --- Title ---
    fig.text(0.5, 0.978,
             "GWi+ODPS Pipeline: Six-Stage Edge Detection",
             ha="center", va="top",
             fontsize=14.5, fontweight="bold",
             transform=fig.transFigure)

    # --- Legend ---
    legend_y = 0.020
    box_size = 0.015

    fig.patches.append(
        mpatches.Rectangle((0.07, legend_y),
                            box_size, box_size,
                            facecolor="#E8F4F8",
                            edgecolor="#5B8FB0",
                            linewidth=1.3,
                            transform=fig.transFigure)
    )
    fig.text(0.092, legend_y + box_size / 2,
             "Stages 1–5: imaginary-only GWi baseline",
             ha="left", va="center",
             fontsize=12, style="italic",
             color="#070707",
             transform=fig.transFigure)

    fig.patches.append(
        mpatches.Rectangle((0.50, legend_y),
                            box_size, box_size,
                            facecolor="#FDECEC",
                            edgecolor="#C9302F",
                            linewidth=1.3,
                            transform=fig.transFigure)
    )
    fig.text(0.522, legend_y + box_size / 2,
             "Stage 6 (ODPS): proposed post-processing step",
             ha="left", va="center",
             fontsize=12, style="italic",
             color="#000000",
             transform=fig.transFigure)

    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] Figure 1 saved: {output_path}")


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Generate Figure 1: GWi+ODPS Pipeline Overview.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
EXAMPLES:

  # All placeholder images
  python generate_figure_1_pipeline.py --output figure_1.png

  # Use real BSDS500 test image for Stage 1 only
  python generate_figure_1_pipeline.py \\
      --output figure_1.png \\
      --stage-image-1 ./data/BSDS500/images/test/3063.jpg

  # Use real images for all stages
  python generate_figure_1_pipeline.py \\
      --output figure_1.png \\
      --stage-image-1 ./preprocessed/3063_eq.png \\
      --stage-image-2 ./figures/gabor_kernels_grid.png \\
      --stage-image-3 ./output/BSDS500/raw_resp_45deg/3063.png \\
      --stage-image-4 ./output/BSDS500/mag_45deg/3063.png \\
      --stage-image-5 ./output/BSDS500/GWi/3063.png \\
      --stage-image-6 ./output/BSDS500/GWi_odps/3063.png
"""
    )
    parser.add_argument("--output", type=Path,
                        default=Path("figure_1_pipeline.png"))
    for i in range(1, 7):
        parser.add_argument(f"--stage-image-{i}", type=str, default=None)
    args = parser.parse_args()

    stage_paths = {
        1: args.stage_image_1 or STAGE_IMAGES.get(1),
        2: args.stage_image_2 or STAGE_IMAGES.get(2),
        3: args.stage_image_3 or STAGE_IMAGES.get(3),
        4: args.stage_image_4 or STAGE_IMAGES.get(4),
        5: args.stage_image_5 or STAGE_IMAGES.get(5),
        6: args.stage_image_6 or STAGE_IMAGES.get(6),
    }

    print("[INFO] Stage image sources:")
    for i in range(1, 7):
        p = stage_paths[i]
        if p and Path(p).exists():
            print(f"  Stage {i}: {p}")
        else:
            note = "no path provided" if not p else "file not found"
            print(f"  Stage {i}: [placeholder] ({note})")

    generate_figure_1(args.output, stage_paths)


if __name__ == "__main__":
    main()
