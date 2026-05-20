"""
generate_figure_2_3.py — Side-lobe phenomenon (Fig 2) + ODPS schematic (Fig 3)

Both figures generated as standalone PNG at 300 DPI, suitable for paper inclusion.

Figure 2: 1D simulation of step edge convolved with imaginary Gabor kernel,
          showing the double-peak side-lobe artifact that motivates ODPS.

Figure 3: 2D schematic of ODPS neighbor comparison along edge-normal direction,
          using the argmax orientation map from Stage 5.

Author: Kukuh Yudhistiro
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch, Rectangle, Circle
import numpy as np


# ============================================================================
# Common style setup
# ============================================================================

def setup_style():
    plt.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman"],
        "font.size": 10,
        "axes.titlesize": 11,
        "axes.labelsize": 10,
        "axes.linewidth": 0.8,
        "xtick.labelsize": 9,
        "ytick.labelsize": 9,
        "legend.fontsize": 9,
        "legend.frameon": True,
        "legend.framealpha": 0.95,
        "legend.edgecolor": "black",
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
    })


# ============================================================================
# FIGURE 2 — Side-lobe phenomenon (1D step edge demonstration)
# ============================================================================

def generate_figure_2(output_path: Path):
    """Three-panel figure: step edge, kernel, convolution result."""
    setup_style()

    # 1D step edge — transition at x=0
    x = np.arange(-15, 16, dtype=np.float64)
    step = np.where(x >= 0, 1.0, 0.0)

    # Imaginary Gabor kernel (sin Gabor)
    # Parameters: lambda=4, sigma=2.24 (same as paper)
    kx = np.arange(-2, 3, dtype=np.float64)  # 5-tap (kernel size 5)
    lam, sigma = 4.0, 2.24
    kernel = np.sin(2 * np.pi * kx / lam) * np.exp(-kx ** 2 / (2 * sigma ** 2))

    # Use a finer-resolution analytic kernel for visualization (smoother curve)
    kx_smooth = np.linspace(-2.5, 2.5, 200)
    kernel_smooth = (np.sin(2 * np.pi * kx_smooth / lam)
                     * np.exp(-kx_smooth ** 2 / (2 * sigma ** 2)))

    # Compute response analytically: convolve step with kernel on finer grid
    # For visualization clarity, use a finer x grid
    x_fine = np.linspace(-15, 15, 601)
    step_fine = np.where(x_fine >= 0, 1.0, 0.0)

    # Convolve at full integer locations only for true alignment
    response = np.convolve(step, kernel, mode="same")
    abs_response = np.abs(response)

    # Create figure with 3 subplots in a row
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))

    # --- Panel (a): Input step edge ---
    ax = axes[0]
    ax.plot(x, step, color="#222222", linewidth=2.0, drawstyle="steps-post")
    ax.axvline(0, color="#888888", linestyle="--", linewidth=1.0,
                alpha=0.7, label="True edge (x = 0)")
    ax.set_xlim(-12, 12)
    ax.set_ylim(-0.15, 1.25)
    ax.set_xlabel("Position x (pixels)")
    ax.set_ylabel("Intensity")
    ax.set_title("(a) Input: 1D step edge", fontsize=11, pad=8)
    ax.grid(alpha=0.3, linestyle=":")
    ax.legend(loc="upper left", fontsize=8)
    ax.set_xticks([-12, -8, -4, 0, 4, 8, 12])

    # --- Panel (b): Imaginary Gabor kernel cross-section ---
    ax = axes[1]
    ax.plot(kx_smooth, kernel_smooth, color="#1F77B4", linewidth=2.0,
            label="sin Gabor (continuous)")
    ax.plot(kx, kernel, "o", color="#0F4C81", markersize=7,
            label="Discrete kernel tap (k=5)")
    ax.axhline(0, color="#888888", linestyle="-", linewidth=0.6, alpha=0.6)
    ax.axvline(0, color="#888888", linestyle="--", linewidth=1.0, alpha=0.7)
    ax.set_xlim(-3, 3)
    ax.set_ylim(-1.15, 1.15)
    ax.set_xlabel("Position x (pixels)")
    ax.set_ylabel("Weight")
    ax.set_title(r"(b) Kernel: sin Gabor ($\lambda$=4, $\sigma$=2.24)",
                 fontsize=11, pad=8)
    ax.grid(alpha=0.3, linestyle=":")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xticks([-2, -1, 0, 1, 2])

    # --- Panel (c): Convolution result (signed and absolute) ---
    ax = axes[2]
    # Plot bars for visualization clarity (since data is discrete)
    bar_width = 0.4
    ax.bar(x - bar_width/2, response, width=bar_width,
           color="#2CA02C", alpha=0.55, label="Raw response R(x)",
           edgecolor="#1A6A1A", linewidth=0.5)
    ax.bar(x + bar_width/2, abs_response, width=bar_width,
           color="#D62728", alpha=0.85, label="|R(x)| = GWi magnitude",
           edgecolor="#8B1A1B", linewidth=0.5)

    # Annotate main peak (place label TOP-LEFT, well away from data)
    peak_idx = int(np.argmax(abs_response))
    peak_x, peak_y = x[peak_idx], abs_response[peak_idx]

    # Annotate side-lobes (place label TOP-RIGHT)
    sl_idx_l = 12  # x=-3 (left side-lobe)
    sl_idx_r = 17  # x=+2 (right side-lobe)

    # Main peak label — high up on the LEFT
    ax.annotate("Main peak\n(true edge location)",
                xy=(peak_x, peak_y),
                xytext=(-9.5, 1.05),
                fontsize=8.5, color="#8B1A1B", fontweight="bold",
                ha="center",
                arrowprops=dict(arrowstyle="->", color="#8B1A1B",
                                lw=1.2, shrinkA=2, shrinkB=4,
                                connectionstyle="arc3,rad=0.2"))

    # Side-lobe label — high up on the RIGHT, with one leader to each side-lobe
    ax.annotate("Side-lobes\n(±λ/2 ≈ ±2 pixels)",
                xy=(x[sl_idx_l], abs_response[sl_idx_l]),
                xytext=(7.5, 1.05),
                fontsize=8.5, color="#8B1A1B", fontweight="bold",
                ha="center",
                arrowprops=dict(arrowstyle="->", color="#8B1A1B",
                                lw=1.2, shrinkA=2, shrinkB=4,
                                connectionstyle="arc3,rad=-0.25"))

    # Second arrow to the right-side side-lobe
    ax.annotate("",
                xy=(x[sl_idx_r], abs_response[sl_idx_r]),
                xytext=(7.5, 0.97),
                arrowprops=dict(arrowstyle="->", color="#8B1A1B",
                                lw=1.0, alpha=0.6,
                                shrinkA=2, shrinkB=4,
                                connectionstyle="arc3,rad=0.15"))

    ax.axvline(0, color="#888888", linestyle="--", linewidth=1.0,
                alpha=0.7, label="True edge")
    ax.axhline(0, color="#000000", linewidth=0.6)
    ax.set_xlim(-12, 12)
    ax.set_ylim(-0.75, 1.40)
    ax.set_xlabel("Position x (pixels)")
    ax.set_ylabel("Response")
    ax.set_title("(c) Convolution result", fontsize=11, pad=8)
    ax.grid(alpha=0.3, linestyle=":")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xticks([-12, -8, -4, 0, 4, 8, 12])

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] Figure 2 saved: {output_path}")


# ============================================================================
# FIGURE 3 — ODPS schematic (2D neighbor comparison)
# ============================================================================

def generate_figure_3(output_path: Path):
    """Schematic showing ODPS neighbor comparison along edge-normal direction."""
    setup_style()

    fig, ax = plt.subplots(1, 1, figsize=(7.5, 5.5))
    ax.set_aspect("equal")

    # Background pixel grid (light gray)
    grid_color = "#DDDDDD"
    for gx in range(-6, 7):
        ax.axvline(gx + 0.5, color=grid_color, linewidth=0.3, zorder=0)
    for gy in range(-5, 6):
        ax.axhline(gy + 0.5, color=grid_color, linewidth=0.3, zorder=0)

    # --- Draw representative edge in the image ---
    # Suppose the edge runs vertically at x=0 (a vertical edge)
    # The orientation that detects this edge is θ=0° (filter orientation aligned with edge-normal)
    # So θ* points in the +x direction (horizontal)
    # Edge-normal direction n = (cos(0°), sin(0°)) = (1, 0)

    # Highlight the edge region: pixels at x=-2,-1,0,1,2 with stronger magnitudes
    # x=0 is the main peak; x=±2 are side-lobes
    pixel_magnitudes = {
        -3: 0.10, -2: 0.50, -1: 0.85, 0: 1.00, 1: 0.85, 2: 0.50, 3: 0.10,
    }
    for px, mag in pixel_magnitudes.items():
        alpha = 0.20 + 0.65 * mag  # darker = higher magnitude
        rect = Rectangle((px - 0.5, -0.5), 1, 1,
                         facecolor=plt.cm.Reds(alpha),
                         edgecolor="#444444", linewidth=0.5, zorder=1)
        ax.add_patch(rect)

    # Label magnitudes inside the strong pixels
    for px, mag in pixel_magnitudes.items():
        if mag >= 0.30:
            ax.text(px, -0.5 + 1.05, f"E={mag:.2f}",
                    ha="center", va="bottom", fontsize=7,
                    color="black", zorder=4)

    # --- Highlight pixel (x, y) at the main peak: x=0, y=0 ---
    center_pixel = Rectangle((-0.5, -0.5), 1, 1,
                              facecolor="none",
                              edgecolor="#D62728", linewidth=2.5, zorder=3)
    ax.add_patch(center_pixel)
    ax.text(0, -0.5 - 0.35, "Center pixel\n(x, y)",
            ha="center", va="top", fontsize=9, color="#D62728",
            fontweight="bold")

    # --- Highlight neighbors: at (x + d·n, y + d·n) and (x - d·n, y - d·n) ---
    # Since n = (1, 0) and d = 2, neighbors are at x=+2 and x=-2
    for nx, label_offset in [(-2, "−d·n"), (2, "+d·n")]:
        neighbor = Rectangle((nx - 0.5, -0.5), 1, 1,
                              facecolor="none",
                              edgecolor="#0713BB", linewidth=2.0,
                              linestyle="--", zorder=3)
        ax.add_patch(neighbor)
        ax.text(nx, -0.5 - 0.35, f"Neighbor\n({label_offset})",
                ha="center", va="top", fontsize=9, color="#1F77B4")

    # --- Draw the edge-normal direction arrows ---
    arrow_y = 1.6
    # Right arrow (+n direction)
    arrow_right = FancyArrowPatch((0.2, arrow_y), (1.8, arrow_y),
                                   arrowstyle="-|>", mutation_scale=15,
                                   color="#1F77B4", linewidth=1.8, zorder=4)
    ax.add_patch(arrow_right)
    ax.text(1.0, arrow_y + 0.20, "+n direction",
            ha="center", va="bottom", fontsize=8,
            color="#1F77B4", style="italic")

    # Left arrow (-n direction)
    arrow_left = FancyArrowPatch((-0.2, arrow_y), (-1.8, arrow_y),
                                  arrowstyle="-|>", mutation_scale=15,
                                  color="#1F77B4", linewidth=1.8, zorder=4)
    ax.add_patch(arrow_left)
    ax.text(-1.0, arrow_y + 0.20, "−n direction",
            ha="center", va="bottom", fontsize=8,
            color="#1F77B4", style="italic")

    # n vector formula
    ax.text(0, arrow_y + 0.55,
            r"$\mathbf{n}(x,y) = (\cos\theta^*,\ \sin\theta^*)$",
            ha="center", va="bottom", fontsize=10, color="#0F4C81")
    ax.text(0, arrow_y + 0.95,
            r"with $d = 2$ pixels",
            ha="center", va="bottom", fontsize=12, color="#555555",
            style="italic")

#     # --- Draw the decision rule below the diagram ---
#     decision_text = (
#         r"Keep $E(x, y)$ if $E(x, y) \geq \max(E(x+d\cdot\mathbf{n}),\ E(x-d\cdot\mathbf{n}))$,"
#         "\n"
#         r"otherwise set $E_{\mathrm{ODPS}}(x, y) = 0$"
#     )
#     ax.text(0, -2.8, decision_text,
#             ha="center", va="top", fontsize=10,
#             bbox=dict(boxstyle="round,pad=0.5",
#                       facecolor="#FFF8E1",
#                       edgecolor="#B8860B",
#                       linewidth=1.0))

    # --- Annotation: vertical edge schematic on the left ---
    # Show a small panel showing what the orientation is
    ax.text(-5.0, 2.0, r"Edge example:",
            ha="left", va="center", fontsize=12, color="#666666",
            style="italic")
    ax.text(-5.0, 1.5, r"vertical edge,",
            ha="left", va="center", fontsize=12, color="#666666",
            style="italic")
    ax.text(-5.0, 1.0, r"so $\theta^* = 0°$",
            ha="left", va="center", fontsize=12, color="#666666",
            style="italic")

    # --- Final axis adjustments ---
    ax.set_xlim(-6, 6)
    ax.set_ylim(-2.5, 3.0)
    ax.set_xticks(range(-5, 6))
    ax.set_yticks([])
    ax.set_xlabel("x (pixels)")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(False)

    # Title
    ax.set_title("ODPS neighbor comparison along edge-normal direction",
                  fontsize=11, pad=10)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close()
    print(f"[OK] Figure 3 saved: {output_path}")


# ============================================================================
# Main
# ============================================================================

if __name__ == "__main__":
    output_dir = Path("manuscript/figure")
    output_dir.mkdir(parents=True, exist_ok=True)

    fig2_path = output_dir / "figure_2_sidelobe.png"
    fig3_path = output_dir / "figure_3_odps_schematic.png"

    generate_figure_2(fig2_path)
    generate_figure_3(fig3_path)

    print("\n[DONE] Both figures saved.")
