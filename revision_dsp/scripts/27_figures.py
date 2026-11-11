"""All figures of the revised manuscript (DSP-D-26-02462), drawn from the revision results.

Nothing is selected or tuned here: every figure reads the frozen configuration
(results/config_final.yaml) and the result files of E02, E10, E11, E20, E21, E22,
E23, E24 and E25, or recomputes synthetic responses with the same code (rev/). The test
sets are only read through the cached counts of E20 and the images named in
config.yaml -> qualitative.

Each figure is listed in results/figures/FIGURES.md with the figure it replaces,
the reviewer comments it answers, its data source and what the caption must say.
The hand-drawn flowcharts of the submission are replaced: the stage flowchart
(Figure 3) is dropped because fig_pipeline shows the stages as a flow, and the
flowcharts of Figures 2 and 4 are drawn here (fig_flow_gwc_gwi, fig_odps). All figures
of the manuscript are drawn at the printed width (PRINT_W), so that the text keeps
its size in print. Figures that depend on E23 (learning-based detectors)
or E24 (runtime) are listed as pending until those results exist; E23 enters the
PR curves (maps without NMS) and fig_dl_cost (results/external/cost.csv).

Usage:  python scripts/27_figures.py --config config.yaml [--only pr,selection]
Outputs (results/figures/): fig_*.png (300 dpi), fig_*.pdf for line plots, FIGURES.md
"""
from __future__ import annotations

import csv
import importlib
import json
import sys
from pathlib import Path

import cv2
import numpy as np

from _common import load_final, parser, setup, split_ref
from rev import cfg as C
from rev import kernels as K
from rev.data import list_items, load_gt
from rev.evaluate import aggregate, per_image_f
from rev.methods import compute
from rev.nms import odps, offsets
from rev.preproc import load_and_preprocess, load_rgb
from rev.runner import final_map, get_scale, run_counts

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).parent))
MECH = importlib.import_module("02_mechanism")   # synthetic renderers of E02

HUMAN_BSDS = 0.803          # Arbelaez et al., TPAMI 2011 (as in the submitted Figure 8)
MANIFEST = []


# --------------------------------------------------------------------------- style
def style():
    plt.rcParams.update({
        "font.family": "serif", "font.serif": ["DejaVu Serif", "Times New Roman", "Times"],
        "font.size": 8, "axes.titlesize": 9, "axes.labelsize": 8, "legend.fontsize": 7,
        "xtick.labelsize": 7, "ytick.labelsize": 7, "savefig.dpi": 300,
        "mathtext.fontset": "dejavuserif",
        "axes.grid": True, "grid.alpha": 0.25, "grid.linestyle": "--",
        "axes.spines.top": False, "axes.spines.right": False})


def save(fig, out: Path, name: str, vector=True, dpi=300, tight=True):
    files = [f"{name}.png"]
    bb = "tight" if tight else None
    fig.savefig(out / f"{name}.png", dpi=dpi, bbox_inches=bb, facecolor="white")
    if vector:
        fig.savefig(out / f"{name}.pdf", bbox_inches=bb, facecolor="white",
                    metadata={"CreationDate": None})   # reproducible PDF bytes
        files.append(f"{name}.pdf")
    plt.close(fig)
    print(f"  -> {name}")
    return files


def note(**kw):
    MANIFEST.append(kw)


def read_csv(path: Path):
    with open(path, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


# --------------------------------------------------------------------------- methods
class Methods:
    """Names, labels and colours of the frozen methods."""

    def __init__(self, final):
        self.by = {m["name"]: m for m in final["methods"]}
        P = final["primary"]
        self.odps, self.gwi, self.gwc, self.gwc0 = P["gwi_odps"], P["gwi"], P["gwc"], P["gwc_zero"]
        sub = [m for m in final["methods"] if m.get("k") == 5 and float(m.get("lam", 0)) == 4.0]
        self.sub_odps = next((m["name"] for m in sub if m["family"] == "gwi" and m.get("nms")), None)
        sel = self.by[self.odps]
        self.k, self.lam = int(sel["k"]), float(sel["lam"])
        kl = f"k{self.k} λ{self.lam:g}"
        self.label = {self.odps: f"GWi+ODPS (ours, {kl})", self.gwi: f"GWi ({kl})",
                      self.gwc: f"GWC raw ({kl})", self.gwc0: f"GWC zero-DC ({kl})",
                      "GaussGradMag1.4": "Gaussian gradient σ 1.4", "Sobel": "Sobel",
                      "LoG": "LoG", "PC": "PC", "Canny": "Canny 50/150", "ED": "ED"}
        if self.sub_odps:
            self.label[self.sub_odps] = "GWi+ODPS (k5 λ4, reference)"
        self.color = {self.odps: "#D62728", self.gwi: "#FF8A8A", self.gwc: "#FF7F0E",
                      self.gwc0: "#B35900", "GaussGradMag1.4": "#2CA02C", "Sobel": "#9467BD",
                      "LoG": "#8C564B", "PC": "#17BECF", "Canny": "#006400", "ED": "#7F7F7F",
                      self.sub_odps: "#D62728"}
        self.binary = {n for n, m in self.by.items() if m["family"] in ("canny", "ed")}


# --------------------------------------------------------------------------- figures
DSNAME = {"BIPED": "BIPED v2"}       # dataset names as written in the manuscript
PRINT_W = 6.5                        # inches: full text width; figures are drawn at the size they are printed


def dsname(ds):
    return DSNAME.get(ds, ds)


def _box(ax, x, y, w, h, text, fc="#F2F2F2", ec="0.35", bold=False, fs=7.0):
    """Rounded box with centred text, in axes-fraction coordinates (flowcharts)."""
    from matplotlib.patches import FancyBboxPatch
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle="round,pad=0.006",
                                fc=fc, ec=ec, lw=0.8, transform=ax.transAxes, clip_on=False))
    ax.text(x, y, text, ha="center", va="center", fontsize=fs, weight="bold" if bold else "normal",
            transform=ax.transAxes, linespacing=1.3)


def _arrow(ax, p0, p1):
    ax.annotate("", xy=p1, xytext=p0, xycoords="axes fraction", textcoords="axes fraction",
                arrowprops=dict(arrowstyle="-|>", color="0.25", lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7))


def fig_pipeline(cfg, final, M, proto, out):
    """Stages 1-6 on one test image with the frozen kernel, drawn as a flow (it replaces the stage flowchart)."""
    from matplotlib.lines import Line2D
    from matplotlib.patches import FancyArrowPatch, Rectangle
    ds, iid = "BSDS500", cfg["qualitative"]["BSDS500"][2]
    it = next(i for i in list_items(cfg, ds, "test") if i.image_id == iid)
    img = load_and_preprocess(it.image_path, proto["preproc"])
    spec = M.by[M.odps]
    N, k, lam = int(spec["N"]), M.k, M.lam
    reals, imags = K.gabor_bank(k, lam, N, float(spec["sigma_ratio"]), float(spec["gamma"]))
    border = cv2.BORDER_CONSTANT if C.border_for(proto, spec) == "constant" else cv2.BORDER_REFLECT_101
    signed = cv2.filter2D(img, cv2.CV_64F, imags[0], borderType=border)
    E, idx = compute(img, dict(spec, nms=None), border=C.border_for(proto, spec), need_idx=True)
    Eo = odps(E, idx, N, float(spec["nms"]["d"]), spec["nms"].get("mode", "nearest"),
              proto.get("nms_outside", "zero"))

    def p995(a):        # display range only: 99.5th percentile, so that a few border pixels do not set it
        return float(np.percentile(np.abs(a), 99.5)) or 1.0

    # detail window: the s x s window with the largest GWi response, away from the zero-padding border
    s, m = 48, 24
    Ein = E.copy()
    Ein[:m, :] = 0
    Ein[-m:, :] = 0
    Ein[:, :m] = 0
    Ein[:, -m:] = 0
    S = cv2.boxFilter(Ein, -1, (s, s), normalize=False, borderType=cv2.BORDER_CONSTANT)
    cy, cx = np.unravel_index(int(np.argmax(S)), S.shape)
    y0 = int(np.clip(cy - s // 2, 0, E.shape[0] - s))
    x0 = int(np.clip(cx - s // 2, 0, E.shape[1] - s))
    vE = p995(E)
    pair = np.concatenate([E[y0:y0 + s, x0:x0 + s], np.zeros((s, 2)), Eo[y0:y0 + s, x0:x0 + s]], axis=1)
    t = [np.pad(q / np.abs(q).max(), 1, constant_values=0) for q in imags]
    half = (N + 1) // 2
    row2 = t[half:] + [np.zeros_like(t[0])] * (half - len(t[half:]))
    tiles = np.concatenate([np.concatenate(t[:half], axis=1), np.concatenate(row2, axis=1)], axis=0)
    lim = p995(signed)
    hsv = plt.get_cmap("hsv")(idx / N)[..., :3] * np.clip(E / vE, 0, 1)[..., None]
    panels = [
        (img, dict(cmap="gray"), "1  Preprocessing\n(Eqs. (1)–(2))"),
        (tiles, dict(cmap="RdBu_r", vmin=-1, vmax=1), f"2  Kernel bank, N = {N}\n(k = {k}, λ = {lam:g})"),
        (signed, dict(cmap="RdBu_r", vmin=-lim, vmax=lim), "3  Convolution, θ = 0°\n(signed response)"),
        (np.abs(signed), dict(cmap="gray_r", vmin=0, vmax=lim), "4  Magnitude |·|, θ = 0°"),
        (E, dict(cmap="gray_r", vmin=0, vmax=vE), "5  Max over θ:\nGWi output E"),
        (hsv, dict(interpolation="nearest"), "5  Orientation index θ*\n(hue, weighted by E)"),
        (Eo, dict(cmap="gray_r", vmin=0, vmax=vE), f"6  ODPS, d = λ/2 = {lam / 2:g}\n(GWi+ODPS output)"),
        (pair, dict(cmap="gray_r", vmin=0, vmax=vE, interpolation="nearest"), "Box in 6, enlarged:\nGWi | GWi+ODPS"),
    ]
    fig, axs = plt.subplots(2, 4, figsize=(PRINT_W, 3.25))
    ax = axs.ravel()
    for a, (im, kw, title) in zip(ax, panels):
        a.imshow(im, **kw)
        a.set_title(title, fontsize=7)
        a.axis("off")
    ax[6].add_patch(Rectangle((x0 - 0.5, y0 - 0.5), s, s, fill=False, ec="#D62728", lw=0.9))
    ax[7].axvline(s + 0.5, color="#D62728", lw=0.8)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.88, bottom=0.02, wspace=0.24, hspace=0.5)
    fig.canvas.draw()
    pos = [a.get_position() for a in ax]
    arrow = dict(arrowstyle="-|>", mutation_scale=7, lw=0.8, color="0.3", transform=fig.transFigure)
    for i in (0, 1, 2, 4, 5, 6):
        y = (pos[i].y0 + pos[i].y1) / 2
        fig.add_artist(FancyArrowPatch((pos[i].x1 + 0.004, y), (pos[i + 1].x0 - 0.004, y), **arrow))
    # from the end of the first row to the start of the second, through the gap between the rows
    xm = (pos[3].x0 + pos[3].x1) / 2
    ym = pos[3].y0 - 0.03
    xl = pos[4].x0 + 0.012
    fig.add_artist(Line2D([xm, xm, xl], [pos[3].y0 - 0.004, ym, ym], color="0.3", lw=0.8,
                          transform=fig.transFigure))
    fig.add_artist(FancyArrowPatch((xl, ym), (xl, pos[4].y1 + 0.004), **arrow))
    files = save(fig, out, "fig_pipeline", vector=False, tight=False)
    note(id="fig_pipeline", old="Figures 1 and 3",
         title="GWi+ODPS pipeline: the six stages as a flow, with their output on a test image",
         reviewer="R2.2 (Stage 6 as thinning, not side-lobe removal), R2.m4", source=f"{ds} {iid}, frozen {M.odps}",
         files=files, status="drawn",
         caption=f"Kernel k = {k}, λ = {lam:g} (frozen). Display range of panels 3-6 clipped at the 99.5th percentile "
                 "(display only). Gabor convolutions use zero padding: the lines at the image border are the zero-padding "
                 "response (H5). Stage 6 removes pixels that are not maxima along θ* at distance d; the last panel enlarges "
                 "the boxed region of panel 6 (left GWi, right GWi+ODPS). Replaces the submitted Figure 1 and the stage "
                 "flowchart (Figure 3), which repeated it.")


def fig_flow_gwc_gwi(cfg, final, M, proto, out):
    """Flowchart: complex Gabor (2N convolutions and a square root) against imaginary-only Gabor (N and |.|)."""
    spec = M.by[M.odps]
    N, k = int(spec["N"]), M.k
    rt = {(r["method"], r["dataset"]): r for r in read_csv(C.results_dir(cfg, "runtime") / "summary.csv")}
    f_gwc, f_gwi = (float(rt[(n, "BSDS500")]["filter_ms_mean"]) for n in (M.gwc, M.gwi))
    fig, ax = plt.subplots(figsize=(PRINT_W, 3.7))
    ax.set_axis_off()
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    L, Lr, Li, R = 0.25, 0.13, 0.37, 0.75
    yy = dict(inp=0.85, ker=0.69, conv=0.53, mag=0.37, pool=0.22, tot=0.07)
    h, w = 0.095, 0.21
    ax.text(L, 0.975, "Complex Gabor (GWC)", ha="center", va="center", fontsize=9, weight="bold")
    ax.text(R, 0.975, "Imaginary-only Gabor (GWi)", ha="center", va="center", fontsize=9, weight="bold")
    ax.plot([0.5, 0.5], [0.02, 0.93], ls="--", color="0.7", lw=0.8)
    for x in (L, R):
        _box(ax, x, yy["inp"], 0.18, h, r"$I_\mathrm{norm}$ (Stage 1)")
    _box(ax, Lr, yy["ker"], w, h, f"{N} even kernels\n(cosine carrier)")
    _box(ax, Li, yy["ker"], w, h, f"{N} odd kernels\n(sine carrier)")
    _box(ax, R, yy["ker"], w, h, f"{N} odd kernels\n(sine carrier)")
    _box(ax, Lr, yy["conv"], w, h, f"{N} convolutions\n" + r"$\rightarrow R_{\mathrm{real},i}$")
    _box(ax, Li, yy["conv"], w, h, f"{N} convolutions\n" + r"$\rightarrow R_{\mathrm{imag},i}$")
    _box(ax, R, yy["conv"], w, h, f"{N} convolutions\n" + r"$\rightarrow R_{\mathrm{imag},i}$")
    _box(ax, L, yy["mag"], 0.30, h, r"$\sqrt{R_{\mathrm{real},i}^{2}+R_{\mathrm{imag},i}^{2}}$" + "\nsquare root per pixel")
    _box(ax, R, yy["mag"], w, h, r"$|R_{\mathrm{imag},i}|$" + "\nabsolute value")
    for x in (L, R):
        _box(ax, x, yy["pool"], 0.24, h, r"max over $i$ (Stage 5)")
    _box(ax, L, yy["tot"], 0.42, h, f"{2 * N} convolutions, {2 * N * k * k} MAC per pixel\n"
         f"filtering: {f_gwc:.1f} ms per BSDS500 image", fc="#E3E3E3", bold=True)
    _box(ax, R, yy["tot"], 0.42, h, f"{N} convolutions, {N * k * k} MAC per pixel\n"
         f"filtering: {f_gwi:.1f} ms per BSDS500 image", fc="#E3E3E3", bold=True)
    hh = h / 2 + 0.008
    for x in (Lr, Li):
        _arrow(ax, (L, yy["inp"] - hh), (x, yy["ker"] + hh))
        _arrow(ax, (x, yy["ker"] - hh), (x, yy["conv"] + hh))
        _arrow(ax, (x, yy["conv"] - hh), (L, yy["mag"] + hh))
    for a_, b_ in (("inp", "ker"), ("ker", "conv"), ("conv", "mag")):
        _arrow(ax, (R, yy[a_] - hh), (R, yy[b_] + hh))
    for x in (L, R):
        _arrow(ax, (x, yy["mag"] - hh), (x, yy["pool"] + hh))
        _arrow(ax, (x, yy["pool"] - hh), (x, yy["tot"] + hh))
    files = save(fig, out, "fig_flow_gwc_gwi")
    note(id="fig_flow_gwc_gwi", old="Figure 2", title="Flowchart, complex Gabor against imaginary-only Gabor",
         reviewer="R2.m4, R2.10, R3.3", source="results/runtime/summary.csv (E24), frozen k and N", files=files,
         status="drawn",
         caption=f"k = {k}, N = {N}. MAC per pixel of the convolutions: GWC {2 * N * k * k}, GWi {N * k * k}. Filtering "
                 f"time per BSDS500 test image (one thread, Table of runtimes): GWC {f_gwc:.1f} ms, GWi {f_gwi:.1f} ms. "
                 "Replaces the hand-drawn Figure 2, whose times (24.6 / 11.3 ms, 2.2x) were those of the submission.")


def fig_odps(cfg, final, M, proto, out):
    """ODPS (Stage 6): processing of one pixel, and the pixels compared for each orientation (nearest sampling)."""
    N = int(M.by[M.odps]["N"])
    cases = []
    if M.sub_odps:
        cases.append(("reference k5 λ4", float(M.by[M.sub_odps]["nms"]["d"])))
    cases.append((f"selected k{M.k} λ{M.lam:g}", float(M.by[M.odps]["nms"]["d"])))
    fig = plt.figure(figsize=(PRINT_W, 3.3))
    top = fig.add_axes([0.0, 0.69, 1.0, 0.235])
    top.set_axis_off()
    top.set_xlim(0, 1)
    top.set_ylim(0, 1)
    fig.text(0.005, 0.985, "(a) Processing of one pixel p", fontsize=8, va="top")
    texts = ["Stage 5 output:\n$E(p)$ and $i^{*}(p)$",
             "offset for $\\theta^{*}(p)$:\n$\\Delta=\\mathrm{round}(d\\,\\mathbf{n})$,\n$d=\\lambda/2$ (nearest pixel)",
             "neighbors:\n$E^{+}=E(p+\\Delta)$\n$E^{-}=E(p-\\Delta)$\n(0 outside the image)",
             "$E(p)\\geq\\max(E^{+},E^{-})$ ?\n(ties are kept)",
             "$E_\\mathrm{ODPS}(p)$:\n$E(p)$ if yes,\n0 if no"]
    w, gap = 0.178, 0.0275
    xs = [w / 2 + 0.005 + i * (w + gap) for i in range(len(texts))]
    for x, t in zip(xs, texts):
        _box(top, x, 0.5, w, 0.95, t, fs=6.8)
    for a_, b_ in zip(xs, xs[1:]):
        _arrow(top, (a_ + w / 2 + 0.004, 0.5), (b_ - w / 2 - 0.004, 0.5))
    cmap = plt.get_cmap("tab10")
    for j, (title, d) in enumerate(cases):
        a = fig.add_axes([0.075 + 0.5 * j, 0.115, 0.215, 0.43])      # about square: 1.4 in x 1.42 in
        R = int(np.ceil(d)) + 1
        for g in np.arange(-R - 0.5, R + 1.0, 1.0):
            a.axhline(g, color="0.85", lw=0.5)
            a.axvline(g, color="0.85", lw=0.5)
        a.add_patch(plt.Rectangle((-0.5, -0.5), 1, 1, color="black"))
        for kk, (dx, dy) in enumerate(offsets(N, d, "nearest")):
            ang = kk * 180.0 / N
            eff = float(np.hypot(dx, dy))
            for sgn in (1, -1):
                a.add_patch(plt.Rectangle((sgn * dx - 0.5, sgn * dy - 0.5), 1, 1, color=cmap(kk), alpha=0.55))
            a.annotate("", xy=(dx, dy), xytext=(0, 0), arrowprops=dict(arrowstyle="->", color=cmap(kk), lw=1.0))
            a.plot([], [], color=cmap(kk), lw=4, alpha=0.6, label=f"{ang:.1f}°: ({dx:+.0f}, {dy:+.0f}), {eff:.2f} px")
        a.set_xlim(-R - 0.5, R + 0.5)
        a.set_ylim(R + 0.5, -R - 0.5)          # image coordinates: rows grow downwards
        a.set_aspect("equal")
        a.grid(False)
        step = 2 if R > 4 else 1
        a.set_xticks(range(-R + (R % step), R + 1, step))
        a.set_yticks(range(-R + (R % step), R + 1, step))
        a.set_xlabel("x offset (px)", fontsize=7)
        a.set_ylabel("y offset (px, down)", fontsize=7)
        label = "bc"[j] if len(cases) > 1 else "b"
        a.set_title(f"({label}) {title}: d = {d:g}", fontsize=8, loc="left")
        a.legend(loc="center left", bbox_to_anchor=(1.04, 0.5), fontsize=6.6, frameon=False, handlelength=1.0,
                 title="θ*: offset, distance", title_fontsize=6.8)
    files = save(fig, out, "fig_odps")
    note(id="fig_odps", old="Figures 4 and 6", title="ODPS (Stage 6): rule for one pixel, and the pixels compared",
         reviewer="R2.2, R2.3 (sampling, effective distance), R2.5, R3.2 (d = λ/2)",
         source="rev/nms.py offsets(), frozen d", files=files, status="drawn",
         caption="(a) The rule of Eqs. (10)-(11) as implemented: nearest-pixel offsets, neighbours outside the image "
                 "count as 0, ties are kept. (b, c) Pixels compared for each orientation: the effective distance differs "
                 "per orientation and, for odd λ, d = λ/2 is rounded (np.round, halves to even; F13). Replaces the "
                 "hand-drawn ODPS flowchart (Figure 4), which explained ODPS by side lobes (R2.2), and fig_odps_offsets.")


def fig_step_profiles(cfg, final, M, proto, out):
    """1D view of the corrected ODPS mechanism (replaces the side-lobe figure)."""
    kernels = [(5, 3.0), (5, 4.0), (M.k, M.lam)]
    fig, axes = plt.subplots(len(kernels), 3, figsize=(PRINT_W, 4.7), squeeze=False)
    for r, (k, lam) in enumerate(kernels):
        h = k // 2
        last = r == len(kernels) - 1
        _, ki = K.gabor_pair(k, lam, 0.0)
        row = ki[h]
        xs = np.arange(-h, h + 1)
        xx = np.linspace(-h, h, 200)
        sig = 0.56 * lam
        cont = np.exp(-xx ** 2 / (2 * sig ** 2)) * np.sin(2 * np.pi * xx / lam)
        a = axes[r, 0]
        a.plot(xx, cont / np.abs(cont).max() * np.abs(row).max(), color="0.6", lw=1, label="continuous carrier × envelope")
        a.stem(xs, row, basefmt=" ", linefmt="C0-", markerfmt="C0o", label="sampled kernel (center row)")
        a.axhline(0, color="k", lw=0.5)
        a.set_title(f"k{k} λ{lam:g}, $r_c$ = {h / lam:.2f}" + ("\nsecond carrier lobe in window" if h / lam > 0.5 else ""),
                    fontsize=8)
        if last:
            a.set_xlabel("x (px)")
        for c, ang in enumerate((0.0, 45.0), start=1):
            img = MECH.render_halfplane(ang)
            spec = dict(family="gwi", k=k, lam=lam)
            E, idx = compute(img, spec, border="reflect", need_idx=True)
            Eo = odps(E, idx, 8, lam / 2.0, "nearest", "reflect")
            _, kth = K.gabor_pair(k, lam, ang)
            signed = cv2.filter2D(img, cv2.CV_64F, kth, borderType=cv2.BORDER_REFLECT_101)
            s, vE = MECH.profile(E, ang)
            _, vS = MECH.profile(signed, ang)
            _, vO = MECH.profile(Eo, ang)
            mx = vE.max()
            a = axes[r, c]
            a.plot(s, vS / mx, "--", lw=1, color="C0", label="signed response, matched θ")
            a.plot(s, vE / mx, lw=1.8, color="C1", label="|·| and max over 8 orientations (GWi)")
            a.plot(s, vO / mx, lw=1.2, color="C3", label="after ODPS (d = λ/2)")
            a.axhline(0, color="k", lw=0.5)
            a.set_title(f"step edge, normal {ang:g}°", fontsize=8)
            if last:
                a.set_xlabel("offset along the normal (px)")
    h1, l1 = axes[0, 0].get_legend_handles_labels()
    h2, l2 = axes[0, 1].get_legend_handles_labels()
    fig.legend(h1 + h2, l1 + l2, loc="lower center", ncol=3, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0.09, 1, 1), h_pad=0.6)
    files = save(fig, out, "fig_step_profiles")
    note(id="fig_step_profiles", old="Figure 5", title="Kernel profile and step-edge response before and after ODPS",
         reviewer="R2.2 (1D demonstration, relation of λ and d), R1.3, R3.2",
         source="synthetic (scripts/02_mechanism.py renderers)", files=files, status="drawn",
         caption="Replaces the side-lobe figure. A carrier side lobe exists only when r_c = (k//2)/λ > 0.5 (top row). "
                 "There, on an axis-aligned step, the max over orientations peaks 1.5 px on either side of the edge, and "
                 "ODPS keeps both peaks and removes the two edge pixels: it does not suppress the double peak (F12, "
                 "correction). At k5 λ4 and at the selected kernel there is no side lobe; ODPS removes the shoulder of "
                 "the max over orientations (directional thinning; F12).")


def fig_structures_dc(cfg, final, M, proto, out):
    """Odd, even and complex responses to step, ridge and bar; DC leakage."""
    k, lam = M.k, M.lam
    fams = [("odd (GWi)", dict(family="gwi"), "C3", "-"),
            ("even raw", dict(family="gwe", dc="raw"), "C2", "--"),
            ("even zero-DC", dict(family="gwe", dc="zero"), "C2", "-"),
            ("complex raw (GWC)", dict(family="gwc", dc="raw"), "C1", "--"),
            ("complex zero-DC", dict(family="gwc", dc="zero"), "C1", "-")]
    structs = [("(a) step", MECH.render_step()), ("(b) ridge, $\\sigma_r$ = 1 px", MECH.render_ridge(1.0)),
               ("(c) bar, 3 px wide", MECH.render_line(3))]
    fig, axes = plt.subplots(2, 2, figsize=(PRINT_W, 3.9))
    axes = axes.ravel()
    x = np.arange(-8, 9)
    C0 = MECH.C0
    for a, (sname, img) in zip(axes, structs):
        for name, base, col, ls in fams:
            E, _ = compute(img, dict(base, k=k, lam=lam), border="reflect")
            v = E[C0, C0 - 8:C0 + 9]
            a.plot(x, v / max(v.max(), 1e-12), ls=ls, color=col, marker="o", ms=2, lw=1.1, label=name)
        a.set_title(sname, fontsize=8)
        a.set_xlabel("offset (px)")
    axes[0].set_ylabel("normalized magnitude")
    axes[2].set_ylabel("normalized magnitude")
    h, lab = axes[0].get_legend_handles_labels()
    a = axes[3]
    I0s = np.linspace(0.1, 0.8, 8)
    for name, spec, col, ls, mk, ms in (("GWC raw", dict(family="gwc", dc="raw"), "C1", "--", "o", 3),
                                        ("GWC zero-DC", dict(family="gwc", dc="zero"), "C1", "-", "s", 6),
                                        ("GWi", dict(family="gwi"), "C3", "-", "o", 3)):
        ratio = []
        for I0 in I0s:
            img = MECH.render_halfplane(0.0, lo=I0, hi=I0 + 0.2)
            E, _ = compute(img, dict(spec, k=k, lam=lam), border="reflect")
            ratio.append(float(E[C0, 10]) / float(E[C0, C0 - 1:C0 + 3].max()))
        a.plot(I0s, ratio, ls=ls, color=col, marker=mk, ms=ms, mfc="none" if mk == "s" else col, label=name)
    a.set_xlabel("background level $I_0$ (step contrast 0.2)")
    a.set_ylabel("flat-region / edge response")
    a.set_title("(d) response on a flat region", fontsize=8)
    a.legend(fontsize=7)
    fig.legend(h, lab, loc="lower center", ncol=3, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0.1, 1, 1), h_pad=0.6)
    files = save(fig, out, "fig_structures_dc")
    note(id="fig_structures_dc", old="new (§3 response analysis)",
         title="Odd, even and complex responses to step, ridge and bar; DC leakage of the raw real kernel",
         reviewer="R3.1b, R2.4, R1.5, R3.7", source="synthetic (rev/ kernels, scripts/02_mechanism.py renderers)",
         files=files, status="drawn",
         caption=f"k{k} λ{lam:g}. The raw real kernel passes a brightness-dependent (DC) response that grows with the "
                 "background level; the zero-DC variant does not. This is why GWC zero-DC is the fair comparison (F14, F23).")


def fig_selection(cfg, final, M, proto, out):
    rows = read_csv(C.results_dir(cfg, "selection") / "kernel_mean.csv")
    sel = json.loads((C.results_dir(cfg, "selection") / "selected.json").read_text(encoding="utf-8"))
    fig, axes = plt.subplots(1, 2, figsize=(PRINT_W, 2.9), sharey=True)
    for a, key, title in ((axes[0], "mean_ods_gwi", "(a) GWi"),
                          (axes[1], "mean_ods_gwi_odps", "(b) GWi+ODPS, d = λ/2")):
        for kk, col in ((5, "C0"), (7, "C1"), (9, "C2")):
            pts = sorted((float(r["lam"]), float(r[key])) for r in rows if int(r["k"]) == kk)
            a.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", ms=3, color=col, label=f"k = {kk}")
        for r in rows:
            if int(r["k"]) == 5 and float(r["lam"]) == 4.0:
                a.scatter([4.0], [float(r[key])], s=60, facecolor="none", edgecolor="k", zorder=5,
                          label="k5 λ4 (reference)")
            if int(r["k"]) == int(sel["k"]) and float(r["lam"]) == float(sel["lam"]):
                a.scatter([float(sel["lam"])], [float(r[key])], s=90, marker="*", color="#D62728", zorder=6,
                          label=f"k{sel['k']} λ{float(sel['lam']):g} (selected)")
        a.set_title(title, fontsize=8)
        a.set_xlabel("λ (px)")
    axes[0].set_ylabel("mean ODS (non-test data)")
    axes[1].legend(fontsize=7, loc="lower right")
    fig.tight_layout()
    files = save(fig, out, "fig_selection")
    note(id="fig_selection", old="new (replaces Tables 1-4 as a figure; §5)",
         title="Kernel selection on non-test data: mean ODS over k and λ",
         reviewer="R2.1, R3.4", source="results/selection/kernel_mean.csv, selected.json (E10)", files=files,
         status="drawn",
         caption="No test data. Under the GWi criterion ODS rises monotonically with λ (no interior optimum, F4); "
                 "the GWi+ODPS criterion (amendment 2, decided after these results were seen, F5) selects "
                 f"k{sel['k']} λ{float(sel['lam']):g}. The optimum is a plateau over λ9-10 at k9 (F17).")


def fig_lambda_d(cfg, final, M, proto, out):
    rows = read_csv(C.results_dir(cfg, "ablation") / "lam_d.csv")
    gwi = {float(r["lam"]): float(r["ODS"]) for r in rows if r["d"].startswith("none")}
    half, fixed = {}, {}
    for r in rows:
        if r["d"].startswith("none"):
            continue
        lam, d = float(r["lam"]), float(r["d"])
        if r["d_is_half_lambda"] == "True" or abs(d - lam / 2) < 1e-9:
            half[lam] = float(r["ODS"])
        if d in (1.0, 2.0, 3.0):
            fixed.setdefault(d, {})[lam] = float(r["ODS"])
    lams = sorted(gwi)
    fig, axes = plt.subplots(1, 2, figsize=(PRINT_W, 2.8))
    a = axes[0]
    a.plot(lams, [gwi[l] for l in lams], marker="o", ms=3, color="#FF8A8A", label="GWi")
    a.plot(lams, [half[l] for l in lams], marker="o", ms=3, color="#D62728", label="GWi+ODPS, d = λ/2")
    a.axvline(M.lam, color="0.5", ls=":", lw=1)
    a.set_xlabel("λ (px)")
    a.set_ylabel("ODS, BSDS500 train+val")
    a.set_title(f"(a) ODS, k = {M.k}", fontsize=8)
    a.legend(fontsize=7)
    a = axes[1]
    for d, col in ((1.0, "C0"), (2.0, "C1"), (3.0, "C2")):
        ls = sorted(fixed[d])
        a.plot(ls, [fixed[d][l] - gwi[l] for l in ls], marker="o", ms=3, color=col, label=f"d = {d:g}")
    a.plot(lams, [half[l] - gwi[l] for l in lams], marker="s", ms=3, color="#D62728", lw=1.6, label="d = λ/2")
    a.axhline(0, color="k", lw=0.5)
    a.axvline(M.lam, color="0.5", ls=":", lw=1)
    a.set_xlabel("λ (px)")
    a.set_ylabel("ODPS gain ΔODS")
    a.set_title(f"(b) ODPS gain, k = {M.k}", fontsize=8)
    a.legend(fontsize=7)
    fig.tight_layout()
    files = save(fig, out, "fig_lambda_d")
    note(id="fig_lambda_d", old="new (§5.5; with Table 9 of the submission)", title="Effect of λ and d at the selected k",
         reviewer="R2.5, R3.2, R1.3", source="results/ablation/lam_d.csv (E11)", files=files, status="drawn",
         caption="BSDS500 train+val. d = λ/2 is within 0.0034 of the best tested d at every λ (F18); "
                 "the ODPS gain falls as λ grows (H1, F9). Dotted line: selected λ.")


def pr_and_counts(cfg, final, proto, name, ds, sp, n_jobs):
    r = run_counts(cfg, final_by(final)[name], ds, sp, proto, n_jobs)
    return r, aggregate(r["counts"], r["thresholds"])


def final_by(final):
    return {m["name"]: m for m in final["methods"]}


DL = {"TEED": dict(color="#1F3A93", ls=(0, (5, 1, 1, 1)), trained="BIPED"),
      "LDC": dict(color="#4F81BD", ls=(0, (3, 1)), trained="BIPED"),
      "PiDiNet": dict(color="#7B68AE", ls=(0, (1, 1)), trained="BSDS500")}


def dl_label(name, ds):
    t = DL[name]["trained"]
    return f"{name} (learned, {dsname(t)}{', in-domain' if t == ds else ''})"


def dl_counts(cfg, name, ds):
    """E23 counts without NMS (the same treatment as the other maps); None if E23 is absent."""
    f = C.results_dir(cfg, "external", "counts") / f"{name}_{ds}.npz"
    if not f.exists():
        return None
    z = np.load(f)
    return aggregate(z["counts"], z["thresholds"])


def fig_pr(cfg, final, M, proto, out, n_jobs):
    curves = [M.odps, M.gwi, M.gwc0, M.gwc, M.sub_odps, "GaussGradMag1.4", "Sobel", "LoG", "PC"]
    points = ["Canny", "ED"]
    have_dl = False
    for ref in final["test_sets"]:
        ds, sp = split_ref(ref)
        fig, ax = plt.subplots(figsize=(PRINT_W, 3.6))
        for f in np.arange(0.1, 1.0, 0.1):
            rr = np.linspace(f / (2 - f) + 1e-3, 1.0, 200)
            pp = f * rr / np.maximum(2 * rr - f, 1e-10)
            ok = (pp >= 0) & (pp <= 1)
            ax.plot(rr[ok], pp[ok], color="lightgray", ls=":", lw=0.7, zorder=0)
            i = np.where(ok)[0][-1]
            ax.annotate(f"F={f:.1f}", xy=(rr[i] * 0.97, pp[i] * 0.96), color="gray", fontsize=6.5)
        for n in curves:
            if not n or n not in M.by:
                continue
            _, ag = pr_and_counts(cfg, final, proto, n, ds, sp, n_jobs)
            Rr, Pp = np.array(ag["R"]), np.array(ag["P"])
            ok = (Rr + Pp) > 0
            if n == M.odps:
                lw, ls, z = 2.2, "-", 5
            elif n == M.gwi:
                lw, ls, z = 1.5, "-.", 4
            elif n == M.sub_odps:
                lw, ls, z = 1.0, ":", 3
            else:
                lw, ls, z = 1.2, "--", 2
            ax.plot(Rr[ok], Pp[ok], color=M.color[n], lw=lw, ls=ls, zorder=z,
                    label=f"[F={ag['ods']:.3f}] {M.label[n]}")
        for n in points:
            if n not in M.by:
                continue
            _, ag = pr_and_counts(cfg, final, proto, n, ds, sp, n_jobs)
            ax.scatter([ag["ods_r"]], [ag["ods_p"]], color=M.color[n], marker="D" if n == "Canny" else "s",
                       s=28, zorder=6, label=f"[F={ag['ods']:.3f}] {M.label[n]} (binary)")
        for n, st_ in DL.items():
            ag = dl_counts(cfg, n, ds)
            if ag is None:
                continue
            have_dl = True
            Rr, Pp = np.array(ag["R"]), np.array(ag["P"])
            ok = (Rr + Pp) > 0
            ax.plot(Rr[ok], Pp[ok], color=st_["color"], lw=1.1, ls=st_["ls"], zorder=2,
                    label=f"[F={ag['ods']:.3f}] {dl_label(n, ds)}")
        if ds == "BSDS500":
            ax.scatter([HUMAN_BSDS], [HUMAN_BSDS], s=70, color="#006400", edgecolor="black", zorder=7,
                       label=f"[F={HUMAN_BSDS:.3f}] Human")
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.set_xlabel("Recall")
        ax.set_ylabel("Precision")
        ax.set_title(f"{dsname(ds)} test")
        ax.set_aspect("equal")
        ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5), fontsize=6.8, frameon=False)
        fig.tight_layout()
        files = save(fig, out, f"fig_pr_{ds}")
        old = {"BSDS500": "Figure 8", "BIPED": "Figure 10", "UDED": "Figure 12"}[ds]
        note(id=f"fig_pr_{ds}", old=old, title=f"Precision-recall curves on {dsname(ds)} test",
             reviewer="R2.8, R2.9, R1.2, R3.5", files=files,
             source=f"E20 counts ({ds}/{sp})" + ("; E23 counts without NMS (results/external/counts)" if have_dl else ""),
             status="drawn" if have_dl else "drawn (DL detectors pending E23)",
             caption="Dataset-level P/R over 99 thresholds (same protocol for all methods, §4.3). Binary detectors give "
                     "one operating point. 'Gaussian gradient σ 1.4' is the row labelled 'Canny' in the submission. "
                     "Gabor methods use zero padding, the others reflect-101 (H5). At the highest thresholds the Gabor "
                     "curves start at low precision; the H5 diagnostic points to the border response under zero padding "
                     "(not tested on the test sets). At the lowest thresholds curves fold back: the binary map covers "
                     "large regions and thinning reduces the matched pixels (same for every method)."
                     + (" Learned detectors (E23): official repositories and weights, maps evaluated without NMS, i.e. "
                        "treated like every other map here; 'in-domain' marks weights trained on the training split of "
                        "this dataset. Values are not comparable with the published ones (different evaluator, F29)."
                        if have_dl else ""))


def fig_qualitative(cfg, final, M, proto, out, n_jobs):
    rows = ["Canny", "Sobel", "LoG", "PC", "ED", "GaussGradMag1.4", M.gwc, M.gwc0, M.gwi, M.odps]
    for ref in final["test_sets"]:
        ds, sp = split_ref(ref)
        ids = cfg["qualitative"].get(ds, [])
        items = {i.image_id: i for i in list_items(cfg, ds, sp)}
        ids = [i for i in ids if i in items]
        if not ids:
            continue
        scales = {n: get_scale(cfg, M.by[n], proto, n_jobs) for n in rows}
        labels = ["Image", "GT"] + [M.label[n].replace(" (", "\n(").replace("gradient σ", "gradient\nσ") for n in rows]
        pw, ph, lw_, top_ = 1.1, 0.66, 1.0, 0.18     # inches: panel width and height, label column, title row
        W, H = lw_ + pw * len(ids), ph * len(labels) + top_
        fig, axes = plt.subplots(len(labels), len(ids), figsize=(W, H), squeeze=False)
        for c, iid in enumerate(ids):
            it = items[iid]
            axes[0, c].imshow(load_rgb(it.image_path), aspect="auto")
            gt = np.mean(np.stack(load_gt(it)).astype(float), axis=0)
            axes[1, c].imshow(gt, cmap="gray_r", vmin=0, vmax=max(gt.max(), 1e-6), aspect="auto")
            axes[0, c].set_title(iid, fontsize=7)
            for r, n in enumerate(rows, start=2):
                v = final_map(it, M.by[n], proto, scales[n])
                axes[r, c].imshow(v, cmap="gray_r", vmin=0, vmax=1, aspect="auto")
        for r in range(len(labels)):
            for c in range(len(ids)):
                axes[r, c].set_xticks([])
                axes[r, c].set_yticks([])
                for s in axes[r, c].spines.values():
                    s.set_visible(True)
                    s.set_linewidth(0.6)
            col = "#D62728" if labels[r].startswith("GWi+ODPS") else "black"
            axes[r, 0].set_ylabel(labels[r], rotation=0, ha="right", va="center", fontsize=7, labelpad=4,
                                  color=col, weight="bold" if col != "black" else "normal")
        plt.subplots_adjust(left=lw_ / W, right=0.995, top=1 - top_ / H, bottom=0.003, wspace=0.03, hspace=0.04)
        files = save(fig, out, f"fig_qualitative_{ds}", vector=False, dpi=600)
        old = {"BSDS500": "Figure 7", "BIPED": "Figure 9", "UDED": "Figure 11"}[ds]
        note(id=f"fig_qualitative_{ds}", old=old, title=f"Qualitative comparison on {dsname(ds)} test ({', '.join(ids)})",
             reviewer="R2.m2 (row order), R2.m6, R1.5 (failure cases)", source=f"maps recomputed with the frozen methods, {ds}/{sp}",
             files=files, status="drawn",
             caption="Normalized maps (per-image min-max, 8-bit), shown inverted. Row order is the same in every "
                     "qualitative figure (fix 'Row order same as Figure 4', R2.m2). Gabor rows: zero padding, so the image "
                     "border can appear as a line (H5)." + (" RGB_139 is the failure case of E25 (CHANGELOG)." if ds == "BIPED" else ""))


def fig_pr_all(cfg, final, M, proto, out, n_jobs):
    """Precision-recall curves of the three test sets in one figure, with one shared legend."""
    from matplotlib.lines import Line2D
    curves = [M.odps, M.gwi, M.gwc0, M.gwc, M.sub_odps, "GaussGradMag1.4", "Sobel", "LoG", "PC"]
    style_ = {}
    fig, axes = plt.subplots(1, 3, figsize=(PRINT_W, 3.05))
    for j, (a, ref) in enumerate(zip(axes, final["test_sets"])):
        ds, sp = split_ref(ref)
        for f in np.arange(0.1, 1.0, 0.1):
            rr = np.linspace(f / (2 - f) + 1e-3, 1.0, 200)
            pp = f * rr / np.maximum(2 * rr - f, 1e-10)
            ok = (pp >= 0) & (pp <= 1)
            a.plot(rr[ok], pp[ok], color="lightgray", ls=":", lw=0.6, zorder=0)
        for n in curves:
            if not n or n not in M.by:
                continue
            _, ag = pr_and_counts(cfg, final, proto, n, ds, sp, n_jobs)
            Rr, Pp = np.array(ag["R"]), np.array(ag["P"])
            ok = (Rr + Pp) > 0
            lw, ls = {M.odps: (1.8, "-"), M.gwi: (1.2, "-."), M.sub_odps: (0.9, ":")}.get(n, (1.0, "--"))
            a.plot(Rr[ok], Pp[ok], color=M.color[n], lw=lw, ls=ls, zorder=5 if n == M.odps else 2)
            style_[M.label[n]] = Line2D([], [], color=M.color[n], lw=lw, ls=ls)
        for n in ("Canny", "ED"):
            _, ag = pr_and_counts(cfg, final, proto, n, ds, sp, n_jobs)
            mk = "D" if n == "Canny" else "s"
            a.scatter([ag["ods_r"]], [ag["ods_p"]], color=M.color[n], marker=mk, s=18, zorder=6)
            style_[M.label[n] + " (binary)"] = Line2D([], [], ls="", marker=mk, ms=4, color=M.color[n])
        for n, st_ in DL.items():
            ag = dl_counts(cfg, n, ds)
            if ag is None:
                continue
            Rr, Pp = np.array(ag["R"]), np.array(ag["P"])
            ok = (Rr + Pp) > 0
            a.plot(Rr[ok], Pp[ok], color=st_["color"], lw=0.9, ls=st_["ls"], zorder=2)
            style_[f"{n} (learned, {dsname(st_['trained'])})"] = Line2D([], [], color=st_["color"], lw=0.9, ls=st_["ls"])
        if ds == "BSDS500":
            a.scatter([HUMAN_BSDS], [HUMAN_BSDS], s=30, color="#006400", edgecolor="black", zorder=7)
            style_["Human (BSDS500)"] = Line2D([], [], ls="", marker="o", ms=5, mfc="#006400", mec="black")
        a.set_xlim(0, 1)
        a.set_ylim(0, 1)
        a.set_aspect("equal")
        a.set_xlabel("Recall")
        if j == 0:
            a.set_ylabel("Precision")
        a.set_title(f"({'abc'[j]}) {dsname(ds)} test", fontsize=8)
    fig.legend(list(style_.values()), list(style_.keys()), loc="lower center", ncol=3, fontsize=6.6, frameon=False,
               handlelength=2.2, columnspacing=1.0)
    fig.tight_layout(rect=(0, 0.3, 1, 1), w_pad=0.8)
    files = save(fig, out, "fig_pr_all")
    note(id="fig_pr_all", old="Figures 8, 10 and 12", title="Precision-recall curves on the three test sets",
         reviewer="R2.8, R2.9, R1.2, R3.5", files=files, source="E20 counts; E23 counts without NMS", status="drawn",
         caption="Dataset-level P/R over 99 thresholds, one protocol for all methods. Binary detectors give one point. "
                 "Learned detectors without NMS; the training set is given in the legend. Single-dataset versions with "
                 "the ODS of each curve: fig_pr_<dataset>.")


def fig_qualitative_all(cfg, final, M, proto, out, n_jobs):
    """Edge maps of all methods on four test images (two BSDS500, one BIPED v2, one UDED) in one figure."""
    rows = ["Canny", "Sobel", "LoG", "PC", "ED", "GaussGradMag1.4", M.gwc, M.gwc0, M.gwi, M.odps]
    picks = [("BSDS500", "29030"), ("BSDS500", "48017"), ("BIPED", "RGB_139"), ("UDED", "28-img_043_SRF_2_HR")]
    split = {split_ref(r)[0]: split_ref(r)[1] for r in final["test_sets"]}
    items = []
    for ds, iid in picks:
        assert iid in cfg["qualitative"].get(ds, []), (ds, iid)      # only images listed in config.yaml
        items.append((ds, next(i for i in list_items(cfg, ds, split[ds]) if i.image_id == iid)))
    scales = {n: get_scale(cfg, M.by[n], proto, n_jobs) for n in rows}
    labels = ["Image", "GT"] + [M.label[n].replace(" (", "\n(").replace("gradient σ", "gradient\nσ") for n in rows]
    pw, ph, lw_, top_ = 1.0, 0.5, 1.0, 0.3
    W, H = lw_ + pw * len(items), ph * len(labels) + top_
    fig, axes = plt.subplots(len(labels), len(items), figsize=(W, H), squeeze=False)
    for c, (ds, it) in enumerate(items):
        axes[0, c].imshow(load_rgb(it.image_path), aspect="auto")
        gt = np.mean(np.stack(load_gt(it)).astype(float), axis=0)
        axes[1, c].imshow(gt, cmap="gray_r", vmin=0, vmax=max(gt.max(), 1e-6), aspect="auto")
        axes[0, c].set_title(f"{dsname(ds)}\n{it.image_id}", fontsize=7)
        for r, n in enumerate(rows, start=2):
            axes[r, c].imshow(final_map(it, M.by[n], proto, scales[n]), cmap="gray_r", vmin=0, vmax=1, aspect="auto")
    for r in range(len(labels)):
        for c in range(len(items)):
            axes[r, c].set_xticks([])
            axes[r, c].set_yticks([])
            for s in axes[r, c].spines.values():
                s.set_linewidth(0.6)
        col = "#D62728" if labels[r].startswith("GWi+ODPS") else "black"
        axes[r, 0].set_ylabel(labels[r], rotation=0, ha="right", va="center", fontsize=7, labelpad=4,
                              color=col, weight="bold" if col != "black" else "normal")
    plt.subplots_adjust(left=lw_ / W, right=0.995, top=1 - top_ / H, bottom=0.003, wspace=0.03, hspace=0.04)
    files = save(fig, out, "fig_qualitative_all", vector=False, dpi=600)
    note(id="fig_qualitative_all", old="Figures 7, 9 and 11", title="Edge maps of all methods on four test images",
         reviewer="R2.m2 (row order), R2.m6, R1.5 (failure cases)", files=files,
         source="images listed in config.yaml -> qualitative; maps of the frozen methods", status="drawn",
         caption="Normalized maps (per-image min-max, 8-bit), inverted. BIPED RGB_139 and UDED 28-img_043_SRF_2_HR "
                 "contain parallel edges spaced at or below the ODPS distance (failure case, F27). Per-dataset versions: "
                 "fig_qualitative_<dataset>.")


def fig_forest(cfg, final, M, proto, out):
    rows = read_csv(C.results_dir(cfg, "stats") / "pairs.csv")
    guard = json.loads((C.results_dir(cfg, "stats") / "claims_guard.json").read_text(encoding="utf-8"))
    short = {M.odps: "GWi+ODPS", M.gwi: "GWi", M.gwc: "GWC raw", M.gwc0: "GWC zero-DC"}
    dsets = list(dict.fromkeys(r["dataset"] for r in rows))
    pairs = list(dict.fromkeys((r["A"], r["B"], r["kind"]) for r in rows))
    fig, axes = plt.subplots(1, len(dsets), figsize=(PRINT_W, 0.32 * len(pairs) + 1.1), sharey=True)
    for a, ds in zip(np.atleast_1d(axes), dsets):
        for y, (A, B, kind) in enumerate(pairs):
            r = next(x for x in rows if x["dataset"] == ds and x["A"] == A and x["B"] == B)
            d, lo, hi = float(r["dODS"]), float(r["ci95_lo"]), float(r["ci95_hi"])
            col = "#D62728" if kind == "reviewer_family" else "#555555"
            a.errorbar([d], [y], xerr=[[d - lo], [hi - d]], fmt="o", color=col, ms=4, capsize=3)
            verb = guard.get(f"{ds}: {A} vs {B}", "")
            a.annotate("improves" if verb == "improves" else "CI includes 0", xy=(hi, y),
                       xytext=(3, -3), textcoords="offset points", fontsize=6.5, color=col)
        lo_all = min(float(x["ci95_lo"]) for x in rows if x["dataset"] == ds)
        hi_all = max(float(x["ci95_hi"]) for x in rows if x["dataset"] == ds)
        a.set_xlim(min(lo_all, 0) - 0.02, hi_all + 0.15)
        a.axvline(0, color="k", lw=0.7)
        a.set_title(f"{dsname(ds)} test", fontsize=8)
        a.set_xlabel("ΔODS (A − B), 95% CI")
    labels = [f"{short.get(A, A)} − {short.get(B, B)}" + ("" if kind == "reviewer_family" else " (DC)")
              for A, B, kind in pairs]
    ax0 = np.atleast_1d(axes)[0]
    ax0.set_yticks(range(len(pairs)))
    ax0.set_yticklabels(labels)
    ax0.invert_yaxis()
    fig.tight_layout()
    files = save(fig, out, "fig_forest_dODS")
    note(id="fig_forest_dODS", old="new (with Tables 5-7)", title="Paired differences in ODS with 95% CI",
         reviewer="R1.1, R2.11, R1.5", source="results/stats/pairs.csv, claims_guard.json (E22)", files=files,
         status="drawn",
         caption=f"Paired bootstrap over images (2000 resamples). Red: pre-specified family (Holm over 9 tests); grey: "
                 f"DC analysis outside the family. 'improves' only where the CI excludes 0. Kernel k{M.k} λ{M.lam:g}.")


def fig_perimage_f(cfg, final, M, proto, out, n_jobs):
    meths = [M.odps, M.gwi, M.gwc0, M.gwc, "GaussGradMag1.4", "Sobel", "LoG", "PC"]
    fig, axes = plt.subplots(1, len(final["test_sets"]), figsize=(PRINT_W, 3.1), sharey=True)
    for a, ref in zip(np.atleast_1d(axes), final["test_sets"]):
        ds, sp = split_ref(ref)
        data = []
        for n in meths:
            r, ag = pr_and_counts(cfg, final, proto, n, ds, sp, n_jobs)
            ti = int(np.argmin(np.abs(np.asarray(r["thresholds"]) - ag["ods_t"])))
            data.append(per_image_f(r["counts"], ti))
        bp = a.boxplot(data, patch_artist=True, widths=0.6, showfliers=True, flierprops=dict(ms=2))
        for patch, n in zip(bp["boxes"], meths):
            patch.set_facecolor(M.color[n])
            patch.set_alpha(0.55)
        a.set_xticks(range(1, len(meths) + 1))
        a.set_xticklabels([M.label[n].split(" (")[0] for n in meths], rotation=60, ha="right", fontsize=6.5)
        a.set_title(f"{dsname(ds)} test (n = {len(data[0])})", fontsize=8)
    np.atleast_1d(axes)[0].set_ylabel("per-image F")
    fig.tight_layout()
    files = save(fig, out, "fig_perimage_F")
    note(id="fig_perimage_F", old="new", title="Per-image F distribution",
         reviewer="R2.11 (variability, notably UDED)", source="E20 counts", files=files, status="drawn",
         caption="Each method at its own dataset ODS threshold. UDED has 30 images: wide spread, wide CIs (F25).")


def fig_preproc(cfg, final, M, proto, out):
    rows = read_csv(C.results_dir(cfg, "preproc") / "preproc_ablation.csv")
    dsets = list(dict.fromkeys(r["dataset"] for r in rows))
    fig, ax = plt.subplots(figsize=(PRINT_W, 2.9))
    w = 0.2
    for j, (n, mode, hatch) in enumerate(((M.gwi, "he", ""), (M.gwi, "none", "//"),
                                          (M.odps, "he", ""), (M.odps, "none", "//"))):
        vals = [float(next(r for r in rows if r["dataset"] == ds and r["method"] == n)[f"ODS_{mode}"]) for ds in dsets]
        xs = np.arange(len(dsets)) + (j - 1.5) * w
        ax.bar(xs, vals, w, color=M.color[n], hatch=hatch, edgecolor="k", lw=0.5,
               label=f"{M.label[n].split(' (')[0]}, {'with HE' if mode == 'he' else 'without HE'}")
    ax.set_xticks(range(len(dsets)))
    ax.set_xticklabels([f"{dsname(d)} test" for d in dsets])
    ax.set_ylabel("ODS")
    ax.set_ylim(0.4, 0.75)
    ax.legend(fontsize=7, ncol=2)
    fig.tight_layout()
    files = save(fig, out, "fig_preproc")
    note(id="fig_preproc", old="new (§5)", title="Effect of histogram equalization (E21)",
         reviewer="R2.7", source="results/preproc/preproc_ablation.csv", files=files, status="drawn",
         caption="Frozen k9 λ9, nothing selected. /255 gives identical maps (not shown). The protocol keeps HE as "
                 "frozen; baselines were not run without HE, so these bars are not comparable with baselines (F26).")


def fig_odps_effect(cfg, final, M, proto, out, n_jobs):
    """ODPS removal maps, images chosen by rule: per dataset the median and the minimum recall change."""
    loc = read_csv(C.results_dir(cfg, "qualitative") / "localization.csv")
    picks = []
    for ref in final["test_sets"]:
        ds, sp = split_ref(ref)
        d = {}
        for r in loc:
            if r["dataset"] == ds:
                d.setdefault(r["image_id"], {})[r["method"]] = float(r["recall"])
        dr = sorted((v[M.odps] - v[M.gwi], k) for k, v in d.items())
        picks.append((ds, sp, dr[len(dr) // 2][1], "median ΔR", dr[len(dr) // 2][0]))
        picks.append((ds, sp, dr[0][1], "worst ΔR", dr[0][0]))
    # rows mix portrait and landscape images: each row gets the height of its image, plus a title band
    pw, gap, tband, mrg = 1.35, 0.08, 0.3, 0.12          # inches
    items_ = [next(i for i in list_items(cfg, ds, sp) if i.image_id == iid) for ds, sp, iid, _, _ in picks]
    ratios = [float(np.divide(*load_rgb(it.image_path).shape[:2])) for it in items_]
    W = 2 * mrg + 4 * pw + 3 * gap
    H = 2 * mrg + sum(pw * r + tband for r in ratios)
    fig = plt.figure(figsize=(W, H))
    axes = np.empty((len(picks), 4), dtype=object)
    ytop = mrg
    for r_i, r in enumerate(ratios):
        ih = pw * r
        for c in range(4):
            axes[r_i, c] = fig.add_axes([(mrg + c * (pw + gap)) / W, 1 - (ytop + tband + ih) / H, pw / W, ih / H])
        ytop += tband + ih
    for r_i, (ds, sp, iid, why, dR) in enumerate(picks):
        it = items_[r_i]
        maps, ts = {}, {}
        for n in (M.gwi, M.odps):
            res, ag = pr_and_counts(cfg, final, proto, n, ds, sp, n_jobs)
            ts[n] = ag["ods_t"]
            maps[n] = final_map(it, M.by[n], proto, get_scale(cfg, M.by[n], proto, n_jobs)) >= ts[n]
        gts = load_gt(it)
        gtu = np.any(np.stack(gts), axis=0)
        a, b = maps[M.gwi], maps[M.odps]
        diff = np.zeros(a.shape + (3,))
        diff[a & ~b] = (1, 0, 0)
        diff[b] = (1, 1, 1)
        diff[gtu & ~b] = (0, 0.8, 0)
        panels = [(load_and_preprocess(it.image_path, "none"), "gray", f"{dsname(ds)} {iid}\n({why}: {dR:+.3f})"),
                  (a, "gray_r", f"GWi ≥ {ts[M.gwi]:.2f}"), (b, "gray_r", f"GWi+ODPS ≥ {ts[M.odps]:.2f}"),
                  (diff, None, "red: removed by ODPS;\ngreen: GT missed")]
        for c, (im, cm, t) in enumerate(panels):
            axes[r_i, c].imshow(im, cmap=cm, aspect="auto")
            axes[r_i, c].set_title(t, fontsize=7, pad=2)
            axes[r_i, c].axis("off")
    files = save(fig, out, "fig_odps_effect", vector=False, dpi=600, tight=False)
    note(id="fig_odps_effect", old="new (§5.5, R1.3)", title="What ODPS removes: median and worst case per dataset",
         reviewer="R1.3, R1.5", source="results/qualitative/localization.csv (E25), maps of the frozen methods",
         files=files, status="drawn",
         caption="Images chosen by rule, not by eye: per dataset, the image with the median and the one with the lowest "
                 "recall change under ODPS. Each method at its own ODS threshold. Green includes GT pixels GWi also "
                 "missed. Parallel edges spaced at or below about d are removed (F27). The rectangle along the image border in "
                 "the binary maps is the zero-padding response (H5).")


def fig_localization(cfg, final, M, proto, out):
    loc = read_csv(C.results_dir(cfg, "qualitative") / "localization.csv")
    dsets = list(dict.fromkeys(r["dataset"] for r in loc))
    keys = [("precision", "Δ precision"), ("recall", "Δ recall"), ("mean_match_dist_px", "Δ mean matched distance (px)")]
    fig, axes = plt.subplots(1, 3, figsize=(PRINT_W, 2.7))
    for i_, (a, (k, lab)) in enumerate(zip(axes, keys)):
        data = []
        for ds in dsets:
            d = {}
            for r in loc:
                if r["dataset"] == ds and r[k] not in ("", "None"):
                    d.setdefault(r["image_id"], {})[r["method"]] = float(r[k])
            data.append([v[M.odps] - v[M.gwi] for v in d.values() if M.odps in v and M.gwi in v])
        a.boxplot(data, widths=0.5, flierprops=dict(ms=2))
        a.axhline(0, color="k", lw=0.6)
        a.set_xticks(range(1, len(dsets) + 1))
        a.set_xticklabels([dsname(d) for d in dsets])
        a.set_title(f"({'abc'[i_]}) {lab}", fontsize=8)
    fig.tight_layout()
    files = save(fig, out, "fig_localization")
    note(id="fig_localization", old="new (§5.5, R1.3)", title="Per-image change in precision, recall and matched distance under ODPS",
         reviewer="R1.3", source="results/qualitative/localization.csv (E25)", files=files, status="drawn",
         caption="Descriptive, no CI. The matched distance grows by < 0.1 px on average (matching tolerance ≈ 4.3 px on "
                 "BSDS500, ≈ 11 px on BIPED); the increase cannot be separated from the extra recall at the lower threshold (F27).")


def fig_runtime(cfg, final, M, proto, out, n_jobs):
    """Stage times (E24) and ODS against runtime (E20 + E24)."""
    summ = read_csv(C.results_dir(cfg, "runtime") / "summary.csv")
    meths = [M.odps, M.gwi, M.gwc, M.gwc0, M.sub_odps] + \
            [n for n in M.by if M.by[n].get("k") == 5 and n != M.sub_odps and M.by[n]["family"] in ("gwi", "gwc")
             and not M.by[n].get("nms") and M.by[n].get("dc", "raw") == "raw"] + \
            ["GaussGradMag1.4", "Sobel", "LoG", "Canny", "ED", "PC"]
    meths = [n for n in dict.fromkeys(meths) if n]
    lab = dict(M.label)
    for n in meths:
        if n not in lab:
            m = M.by[n]
            lab[n] = f"{'GWi' if m['family'] == 'gwi' else 'GWC raw'} (k5 λ4, reference)"
    fig = plt.figure(figsize=(PRINT_W, 6.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1])
    stages = [("pre_ms_mean", "Stage 1 preprocessing", "#BBBBBB"), ("filter_ms_mean", "filtering", "#4C72B0"),
              ("pool_ms_mean", "pooling (gradients: direction quantization)", "#55A868"), ("nms_ms_mean", "ODPS / NMS", "#D62728")]
    for j, ds in enumerate(("BSDS500", "BIPED")):
        a = fig.add_subplot(gs[0, j])
        rows = {r["method"]: r for r in summ if r["dataset"] == ds}
        shown = [n for n in meths if n in rows and n != "PC"]
        y = np.arange(len(shown))
        left = np.zeros(len(shown))
        for key, sl, col in stages:
            v = np.array([float(rows[n][key]) for n in shown])
            a.barh(y, v, left=left, color=col, label=sl, height=0.7)
            left += v
        for yi, n in zip(y, shown):
            a.text(left[yi] + left.max() * 0.01, yi, f"{left[yi]:.1f}", va="center", fontsize=6)
        a.set_yticks(y)
        a.set_yticklabels([lab[n] for n in shown], fontsize=6.5)
        a.invert_yaxis()
        pc = rows.get("PC")
        a.set_title(f"({'ab'[j]}) {dsname(ds)}" + (f"; PC: {float(pc['total_ms_mean']) + float(pc['pre_ms_mean']):.0f} ms" if pc else ""), fontsize=8)
        a.set_xlabel("time per image (ms)")
        if j == 0:
            leg = a.get_legend_handles_labels()
    a = fig.add_subplot(gs[1, :])
    ds, sp = "BSDS500", "test"
    rows = {r["method"]: r for r in summ if r["dataset"] == ds}
    for n in meths:
        if n not in rows:
            continue
        _, ag = pr_and_counts(cfg, final, proto, n, ds, sp, n_jobs)
        t = float(rows[n]["total_ms_mean"]) + float(rows[n]["pre_ms_mean"])
        a.scatter([t], [ag["ods"]], color=M.color.get(n, "#333333"), s=30 if n != M.odps else 70,
                  marker="*" if n == M.odps else "o", zorder=3)
        a.annotate(lab[n].split(" (")[0] + (" k5" if "reference" in lab[n] else ""), (t, ag["ods"]),
                   xytext=(3, 2), textcoords="offset points", fontsize=6.5)
    a.set_xscale("log")
    a.set_xlabel("total time incl. preprocessing (ms, log scale)")
    a.set_ylabel("ODS")
    a.set_title("(c) BSDS500: ODS against time per image", fontsize=8)
    fig.legend(*leg, loc="lower center", ncol=4, fontsize=6.5, frameon=False)
    fig.tight_layout(rect=(0, 0.035, 1, 1))
    files = save(fig, out, "fig_runtime")
    note(id="fig_runtime", old="new (with Table 8)", title="Runtime per stage, and ODS against runtime",
         reviewer="R1.4, R2.5, R2.10, R3.3, R3.6", source="results/runtime/summary.csv (E24), E20 counts", files=files,
         status="drawn",
         caption="Single thread (cv2.setNumThreads(1)), 3 warm-up images, median of 5 runs per image, mean over images; "
                 "Intel i5-14400, Windows 11, Python 3.13, OpenCV 4.13 (results/runtime/env.json). Kernel construction "
                 "(about 0.2 ms) is excluded. ODPS needs the argmax instead of the max, so its cost appears in pooling "
                 "and ODPS. For Sobel and the Gaussian gradient the green part is the direction quantization, which the runtime "
                 "script always computes although these baselines use no NMS: their times are overstated by that part (F28). "
                 "Background load during the run was about 0.6 of one core (F28).")


def fig_dl_cost(cfg, final, M, proto, out):
    """ODS against CPU time per test set: frozen methods (E20, E24) and learned detectors (E23)."""
    from matplotlib.lines import Line2D
    ext = C.results_dir(cfg, "external")
    if not (ext / "cost.csv").exists():
        return
    cost = {(r["method"], r["dataset"]): r for r in read_csv(ext / "cost.csv")}
    ext_ods = {(r["method"], r["dataset"]): float(r["ODS"]) for r in read_csv(ext / "summary.csv")}
    rt = {(r["method"], r["dataset"]): r for r in read_csv(C.results_dir(cfg, "runtime") / "summary.csv")}
    test = {(r["method"], r["dataset"]): float(r["ODS"]) for r in read_csv(C.results_dir(cfg, "test") / "summary.csv")}
    classic = [M.odps, M.gwi, M.gwc0, "GaussGradMag1.4", "Sobel", "LoG", "Canny", "ED", "PC"]
    short = {M.odps: "GWi+ODPS", M.gwi: "GWi", M.gwc0: "GWC zero-DC", "GaussGradMag1.4": "Gaussian gradient",
             "Sobel": "Sobel", "LoG": "LoG", "Canny": "Canny", "ED": "Edge Drawing", "PC": "Phase congruency"}
    marker = {M.odps: "*", M.gwi: "o", M.gwc0: "h", "GaussGradMag1.4": "o", "Sobel": "s", "LoG": "D", "Canny": "X",
              "ED": "P", "PC": "p"}
    fig, axes = plt.subplots(1, 3, figsize=(PRINT_W, 3.2), sharey=True)
    handles = {}
    for j, (a, ref) in enumerate(zip(axes, final["test_sets"])):
        ds, _ = split_ref(ref)
        for n in classic:
            if (n, ds) not in rt or (n, ds) not in test:
                continue
            t = float(rt[(n, ds)]["total_ms_mean"]) + float(rt[(n, ds)]["pre_ms_mean"])
            handles[short[n]] = a.scatter([t], [test[(n, ds)]], color=M.color.get(n, "#333333"),
                                          s=90 if n == M.odps else 26, marker=marker[n], zorder=3, linewidths=0)
        for n, st_ in DL.items():
            key = (n + "_converted", ds) if (n + "_converted", ds) in cost else (n, ds)
            if key not in cost or (n, ds) not in ext_ods:
                continue
            t, f = float(cost[key]["total_ms"]), ext_ods[(n, ds)]
            ind = st_["trained"] == ds
            a.scatter([t], [f], marker="^", s=40, zorder=3, color=st_["color"] if not ind else "white",
                      edgecolor=st_["color"], linewidth=1.2)
            handles.setdefault(f"{n} (learned)", Line2D([], [], ls="", marker="^", ms=6, color=st_["color"]))
        a.set_xscale("log")
        a.set_ylim(0.3, 0.9)
        a.set_xlabel("CPU time per image (ms, log)")
        a.set_title(f"({'abc'[j]}) {dsname(ds)} test", fontsize=8)
    axes[0].set_ylabel("ODS")
    handles["learned, in-domain (hollow)"] = Line2D([], [], ls="", marker="^", ms=6, mfc="white", mec="0.3")
    fig.legend(list(handles.values()), list(handles.keys()), loc="lower center", ncol=5, fontsize=7, frameon=False,
               handletextpad=0.3, columnspacing=1.0)
    fig.tight_layout(rect=(0, 0.2, 1, 1))
    files = save(fig, out, "fig_dl_cost")
    note(id="fig_dl_cost", old="new (§5.6, with the table of learned detectors)",
         title="ODS against CPU time: training-free methods and learned detectors",
         reviewer="R1.2, R3.5", files=files,
         source="results/test/summary.csv (E20), results/runtime/summary.csv (E24), results/external/summary.csv and cost.csv (E23)",
         status="drawn",
         caption="Same machine and timing rule for all points: one thread, 3 warm-up images, median of 5 runs per image, mean "
                 "over images, including preprocessing (E24, E23); for the learned detectors it also includes reading "
                 "the image file (5-31 ms), which E24 excludes. Training-free methods run in OpenCV/NumPy, learned "
                 "detectors in PyTorch 2.15 CPU; the frameworks differ. Learned detectors: maps without NMS; hollow "
                 "triangles are in-domain (weights trained on this dataset's training split). PiDiNet time is that of "
                 "its converted model (same maps). Input sizes of the learned detectors follow their repositories "
                 "(TEED upsamples BSDS500 and UDED x1.5; LDC resizes BSDS500 to 480x480), so their cost is not per "
                 "original pixel (F29).")


def manual_and_pending(cfg, M, out):
    note(id="(dropped) flowchart of stages", old="Figure 3", title="Flowchart of the stages", reviewer="R2.m4, R2.2",
         source="-", files=[], status="dropped",
         caption="It repeated Figure 1, which now shows the six stages as a flow with their outputs (fig_pipeline). Its "
                 "Stage 6 box also repeated the side-lobe explanation (R2.2) and the k5 λ4 parameters.")
    rt = C.results_dir(cfg, "runtime")
    if not (rt / "summary.csv").exists():
        note(id="fig_runtime", old="new (with Table 8)", title="Runtime per stage and MAC per pixel",
             reviewer="R1.4, R2.5, R2.10, R3.3, R3.6", source="results/runtime/ (E24)", files=[],
             status="pending E24", caption="Filtering stage vs full pipeline, single thread, median of 5 runs.")
    ext = C.results_dir(cfg, "external")
    if not (ext / "cost.csv").exists():
        note(id="(DL in PR figures and cost figure)", old="Figures 8, 10, 12", title="Learning-based detectors (TEED, PiDiNet, LDC)",
             reviewer="R1.2, R3.5", source="results/external/ (E23)", files=[], status="pending E23",
             caption="Added to the PR curves and to a cost figure once E23 and tools/external/summarize_e23.py are run.")


def write_manifest(out: Path, M):
    lines = ["# Figures of the revised manuscript", "",
             "Generated by `scripts/27_figures.py` from the frozen results; do not edit by hand.",
             f"Selected kernel k{M.k} λ{M.lam:g}. Numbering in the revised manuscript is decided when writing; "
             "'Replaces' gives the figure of the submission.", "",
             "| Figure file | Replaces | Content | Reviewer comments | Data source | Status | Caption must say |",
             "|---|---|---|---|---|---|---|"]
    for m in MANIFEST:
        files = ", ".join(f"`{f}`" for f in m["files"]) or m["id"]
        lines.append("| " + " | ".join(str(x).replace("|", "/") for x in
                                         (files, m["old"], m["title"], m["reviewer"], m["source"], m["status"], m["caption"])) + " |")
    (out / "FIGURES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"  -> FIGURES.md ({len(MANIFEST)} entries)")


FIGS = ["pipeline", "flow_gwc_gwi", "odps", "step_profiles", "structures_dc", "selection", "lambda_d",
        "qualitative", "pr", "qualitative_all", "pr_all", "forest", "perimage_f", "preproc", "odps_effect", "localization", "runtime",
        "dl_cost"]


def main():
    ap = parser(__doc__)
    ap.add_argument("--only", default="", help="comma-separated subset of: " + ", ".join(FIGS))
    args = ap.parse_args()
    cfg, n_jobs = setup(args)
    final = load_final(cfg, args.limit)
    proto = C.protocol_of(cfg)
    out = C.results_dir(cfg, "figures")
    style()
    M = Methods(final)
    only = [s.strip() for s in args.only.split(",") if s.strip()] or FIGS
    run = {
        "pipeline": lambda: fig_pipeline(cfg, final, M, proto, out),
        "flow_gwc_gwi": lambda: fig_flow_gwc_gwi(cfg, final, M, proto, out),
        "odps": lambda: fig_odps(cfg, final, M, proto, out),
        "step_profiles": lambda: fig_step_profiles(cfg, final, M, proto, out),
        "structures_dc": lambda: fig_structures_dc(cfg, final, M, proto, out),
        "selection": lambda: fig_selection(cfg, final, M, proto, out),
        "lambda_d": lambda: fig_lambda_d(cfg, final, M, proto, out),
        "qualitative": lambda: fig_qualitative(cfg, final, M, proto, out, n_jobs),
        "pr": lambda: fig_pr(cfg, final, M, proto, out, n_jobs),
        "qualitative_all": lambda: fig_qualitative_all(cfg, final, M, proto, out, n_jobs),
        "pr_all": lambda: fig_pr_all(cfg, final, M, proto, out, n_jobs),
        "forest": lambda: fig_forest(cfg, final, M, proto, out),
        "perimage_f": lambda: fig_perimage_f(cfg, final, M, proto, out, n_jobs),
        "preproc": lambda: fig_preproc(cfg, final, M, proto, out),
        "odps_effect": lambda: fig_odps_effect(cfg, final, M, proto, out, n_jobs),
        "localization": lambda: fig_localization(cfg, final, M, proto, out),
        "runtime": lambda: fig_runtime(cfg, final, M, proto, out, n_jobs),
        "dl_cost": lambda: fig_dl_cost(cfg, final, M, proto, out),
    }
    for name in only:
        print(f"[{name}]")
        run[name]()
    if set(only) == set(FIGS):
        manual_and_pending(cfg, M, out)
        write_manifest(out, M)


if __name__ == "__main__":
    main()
