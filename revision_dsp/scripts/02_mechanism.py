"""Response analysis on synthetic structures (no dataset needed), for the five
kernel configurations of Tables 1-4 (config.yaml -> selection.candidates), so the
configuration selected later is always included.

A  kernel table (R2.2): carrier side-lobe ratio of the sampled imaginary kernel
   (centre row, theta = 0), rho = (k//2)/lambda, DC/gain of the real kernel;
   also lambda = 3..6 at k = 5 and 7 (lambda sweep of R3.2)
B  step edge at normal angle 0, 22.5, 45 deg (R2.2): signed response of the
   matched imaginary kernel, the same after |.|, the max over orientations (GWi
   map) and the map after ODPS (d = lambda/2), sampled along the normal;
   secondary maxima and values at +-1, +-2 px
C  step, ridge and bar (R3.1b: "response of both kernels to ideal step, ridge,
   and bar structures"; R2.4: ridge, bar, line): magnitude after the max over
   orientations for odd (GWi), even raw, even zero-DC, complex raw and complex
   zero-DC kernels (number and position of maxima), and the signed responses of
   the odd and even kernels at theta = 0
D  DC leakage (R1.5): flat-region and edge magnitude of GWC raw / GWC zero-DC /
   GWi at background levels I0 = 0.2, 0.5, 0.8 (step contrast 0.2)

Outputs (results/mechanism/): kernels.csv, step_profiles.csv, structures.csv,
structures_signed.csv, dc_leakage.csv, fig_step.png, fig_structures.png
"""
from __future__ import annotations

import cv2
import numpy as np

from _common import parser, setup
from rev import cfg as C
from rev import kernels as K
from rev.methods import compute
from rev.nms import odps
from rev.runner import write_csv

SIZE = 101
C0 = SIZE // 2


def render_halfplane(angle_deg, lo=0.25, hi=0.75, ss=8):
    """Anti-aliased step: hi where (x - c) cos a + (y - c) sin a > 0.
    The edge passes through the pixel-corner point (c + 0.5, c + 0.5)."""
    a = np.deg2rad(angle_deg)
    g = (np.arange(SIZE * ss) + 0.5) / ss - 0.5
    X, Y = np.meshgrid(g, g)
    s = (X - C0 - 0.5) * np.cos(a) + (Y - C0 - 0.5) * np.sin(a)
    img = np.where(s > 0, hi, lo)
    return img.reshape(SIZE, ss, SIZE, ss).mean(axis=(1, 3))


def render_line(width, lo=0.25, hi=0.75):
    """Bar (rectangular profile) of the given width, vertical, bright on dark."""
    img = np.full((SIZE, SIZE), lo)
    x0 = C0 - width // 2
    img[:, x0:x0 + width] = hi
    return img


def render_ridge(s_r, lo=0.25, hi=0.75):
    """Ridge (Gaussian profile, standard deviation s_r px), vertical, bright on dark."""
    x = np.arange(SIZE) - C0
    prof = lo + (hi - lo) * np.exp(-x ** 2 / (2.0 * s_r ** 2))
    return np.tile(prof, (SIZE, 1))


def render_step(lo=0.25, hi=0.75):
    """Vertical step between columns C0 - 1 and C0 (edge at x = -0.5)."""
    img = np.full((SIZE, SIZE), lo)
    img[:, C0:] = hi
    return img


def profile(m, angle_deg, smax=6.0, step=0.25):
    a = np.deg2rad(angle_deg)
    s = np.arange(-smax, smax + 1e-9, step)
    xs = (C0 + 0.5 + s * np.cos(a)).astype(np.float32)
    ys = (C0 + 0.5 + s * np.sin(a)).astype(np.float32)
    v = cv2.remap(m.astype(np.float32), xs[None], ys[None], cv2.INTER_LINEAR)[0]
    return s, v


def local_maxima(s, v, rel=0.05):
    out = []
    for i in range(1, len(v) - 1):
        if v[i] >= v[i - 1] and v[i] > v[i + 1] and v[i] >= rel * v.max():
            out.append((round(float(s[i]), 2), round(float(v[i] / v.max()), 3)))
    return out


def thickness(m, rel):
    """Mean number of pixels per row (rows c-10..c+10, columns c-8..c+9) whose
    value exceeds rel * max: the width of the detected edge band."""
    win = m[C0 - 10:C0 + 11, C0 - 8:C0 + 10]
    return round(float((win > rel * m.max()).sum(axis=1).mean()), 2)


def main():
    args = parser(__doc__).parse_args()
    cfg, _ = setup(args)
    out = C.results_dir(cfg, "mechanism")

    cands = [(int(c["k"]), float(c["lam"])) for c in cfg["selection"]["candidates"]]
    sweep = [(k, float(l)) for k in (5, 7) for l in cfg["ablation"]["lam_d"]["lam"]]
    table_cfgs = list(dict.fromkeys(cands + sweep))

    # A
    rows = []
    for k, lam in table_cfgs:
        kr, ki = K.gabor_pair(k, lam, 0.0)
        row = ki[k // 2]
        h = k // 2
        xs = np.arange(-h, h + 1)
        main_lobe = row[(xs > 0) & (xs < lam / 2)]
        outer = row[xs > lam / 2]
        ratio = float(np.abs(outer).max() / main_lobe.max()) if outer.size and main_lobe.size else 0.0
        rows.append(dict(k=k, lam=lam, rho=round(h / lam, 3),
                         imag_centre_row=" ".join(f"{v:+.3f}" for v in row),
                         carrier_sidelobe_ratio=round(ratio, 3),
                         real_dc_over_gain=round(K.dc_to_gain(kr, lam), 3)))
    write_csv(rows, out / "kernels.csv")

    # B
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    srows = []
    fig, axes = plt.subplots(len(cands), 3, figsize=(12, 3 * len(cands)), sharex=True,
                             squeeze=False)
    for r_i, (k, lam) in enumerate(cands):
        spec = dict(family="gwi", k=k, lam=lam)
        for c_i, ang in enumerate((0.0, 22.5, 45.0)):
            img = render_halfplane(ang)
            E, idx = compute(img, spec, border="reflect", need_idx=True)
            Eo = odps(E, idx, 8, lam / 2.0, "nearest", "reflect")
            _, ki = K.gabor_pair(k, lam, ang)
            signed = cv2.filter2D(img, cv2.CV_64F, ki, borderType=cv2.BORDER_REFLECT_101)
            s, vE = profile(E, ang)
            _, vS = profile(signed, ang)
            _, vO = profile(Eo, ang)
            mx = vE.max()
            ax = axes[r_i, c_i]
            ax.plot(s, vS / mx, "--", lw=1, label="signed (matched theta)")
            ax.plot(s, np.abs(vS) / mx, ":", lw=1.2, label="|signed|")
            ax.plot(s, vE / mx, lw=1.8, label="max over 8 orientations")
            ax.plot(s, vO / mx, lw=1.2, label="after ODPS (d = lambda/2)")
            ax.axhline(0, color="k", lw=0.5)
            ax.set_title(f"k{k} lambda{lam}, edge normal {ang} deg", fontsize=9)
            if r_i == len(cands) - 1:
                ax.set_xlabel("offset along normal (px)")
            def val(dist):
                return float(np.interp([-dist, dist], s, vE).mean() / mx)
            srows.append(dict(k=k, lam=lam, normal_deg=ang,
                              E_at_1px=round(val(1.0), 3), E_at_1_5px=round(val(1.5), 3),
                              E_at_2px=round(val(2.0), 3), E_at_3px=round(val(3.0), 3),
                              secondary_maxima=str([m for m in local_maxima(s, vE)
                                                    if abs(m[0]) >= 1.25]),
                              width_before_px=thickness(E, 0.5),
                              width_after_odps_px=thickness(Eo, 0.05)))
    axes[0, 0].legend(fontsize=7)
    fig.tight_layout()
    fig.savefig(out / "fig_step.png", dpi=150)
    plt.close(fig)
    write_csv(srows, out / "step_profiles.csv")

    # C
    fams = [("odd (GWi)", dict(family="gwi")), ("even raw", dict(family="gwe", dc="raw")),
            ("even zero-DC", dict(family="gwe", dc="zero")),
            ("complex raw", dict(family="gwc", dc="raw")),
            ("complex zero-DC", dict(family="gwc", dc="zero"))]
    structs = [("step", render_step())]
    structs += [(f"ridge s={sr}px", render_ridge(sr)) for sr in (0.5, 1.0, 2.0)]
    structs += [(f"bar w={w}px", render_line(w)) for w in (1, 2, 3, 5, 8)]
    crows, srows = [], []
    x = np.arange(-8, 9)
    for k, lam in cands:
        show = (k, lam) == cands[0] or (k, lam) == (5, 4.0)
        if show:
            fig, axes = plt.subplots(len(structs), 2, figsize=(11, 2.0 * len(structs)),
                                     sharex=True, squeeze=False)
        for s_i, (sname, img) in enumerate(structs):
            for name, base in fams:
                spec = dict(base, k=k, lam=lam)
                E, _ = compute(img, spec, border="reflect")
                v = E[C0, C0 - 8:C0 + 9]
                mx = v.max() if v.max() > 0 else 1
                if show:
                    axes[s_i, 0].plot(x, v / mx, marker="o", ms=2, label=name)
                pk = [(int(x[i]), round(float(v[i] / mx), 3)) for i in range(1, len(v) - 1)
                      if v[i] >= v[i - 1] and v[i] > v[i + 1] and v[i] >= 0.2 * mx]
                crows.append(dict(structure=sname, method=name, k=k, lam=lam,
                                  n_maxima=len(pk), maxima=str(pk),
                                  flat_level=round(float(E[C0, 2] / mx), 3)))
            kr_raw, ki = K.gabor_pair(k, lam, 0.0)
            kr_zero, _ = K.gabor_pair(k, lam, 0.0, dc="zero")
            for kname, kern in (("odd (imag)", ki), ("even raw (real)", kr_raw),
                                ("even zero-DC (real)", kr_zero)):
                r = cv2.filter2D(img, cv2.CV_64F, kern, borderType=cv2.BORDER_REFLECT_101)
                v = r[C0, C0 - 8:C0 + 9]
                m = np.abs(v).max() if np.abs(v).max() > 0 else 1
                if show:
                    axes[s_i, 1].plot(x, v / m, marker=".", ms=3, label=kname)
                srows.append(dict(structure=sname, kernel=kname, k=k, lam=lam,
                                  **{f"x{int(o):+d}": round(float(val / m), 3)
                                     for o, val in zip(x, v)}))
            if show:
                axes[s_i, 0].set_title(f"{sname}: |.| after max over orientations (k{k} lambda{lam:g})",
                                       fontsize=8)
                axes[s_i, 1].set_title(f"{sname}: signed response at theta = 0", fontsize=8)
                axes[s_i, 1].axhline(0, color="k", lw=0.5)
        if show:
            axes[0, 0].legend(fontsize=6, ncol=2)
            axes[0, 1].legend(fontsize=6)
            axes[-1, 0].set_xlabel("column offset (px)")
            axes[-1, 1].set_xlabel("column offset (px)")
            fig.tight_layout()
            fig.savefig(out / f"fig_structures_k{k}l{lam:g}.png", dpi=150)
            plt.close(fig)
    write_csv(crows, out / "structures.csv")
    write_csv(srows, out / "structures_signed.csv")

    # D
    drows = []
    for k, lam in cands:
        for I0 in (0.2, 0.5, 0.8):
            img = render_halfplane(0.0, lo=I0, hi=min(1.0, I0 + 0.2))
            for name, spec in (("GWC raw", dict(family="gwc", dc="raw")),
                               ("GWC zero-DC", dict(family="gwc", dc="zero")),
                               ("GWi", dict(family="gwi"))):
                E, _ = compute(img, dict(spec, k=k, lam=lam), border="reflect")
                drows.append(dict(k=k, lam=lam, I0=I0, method=name,
                                  flat=round(float(E[C0, 10]), 3),
                                  edge=round(float(E[C0, C0 - 1:C0 + 3].max()), 3)))
    write_csv(drows, out / "dc_leakage.csv")
    print(f"  mechanism outputs in {out}")


if __name__ == "__main__":
    main()
