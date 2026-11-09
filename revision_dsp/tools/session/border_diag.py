"""Diagnostic only (not for the manuscript): how much of the edge map lies in the
image-border band under zero padding vs reflect-101, on 20 BSDS500 val images.
Run from revision_dsp with the venv python."""
import csv
import sys

import numpy as np

sys.path.insert(0, ".")
from rev import cfg as C                      # noqa: E402
from rev.data import list_items               # noqa: E402
from rev.runner import final_map, load_gt  # noqa: E402
from rev.evaluate import image_counts, thresholds  # noqa: E402
from rev.specs import gabor_specs             # noqa: E402

cfg = C.load_config("config.yaml")
proto0 = C.protocol_of(cfg)
items = list_items(cfg, "BSDS500", "val")[:20]
ods_t = {}
with open("results/selection/kernel_ablation.csv", encoding="utf-8") as fh:
    for r in csv.DictReader(fh):
        if r["dataset"] == "BSDS500":
            ods_t[r["method"]] = float(r["ODS_t"])

rows = []
for k, lam in [(5, 4), (7, 9), (9, 9)]:
    kc = dict(k=k, lam=lam, N=8, sigma_ratio=0.56, gamma=0.5)
    gwi, odps = gabor_specs(kc, lam / 2)[:2]
    for spec in (gwi, odps):
        spec = dict(spec)
        spec.setdefault("name", C.expand_name(spec))
        t = ods_t[spec["name"]]
        thr = thresholds(int(proto0["n_thresholds"]))
        ti = int(np.argmin(np.abs(thr - t)))
        for border, outside in (("paper", "zero"), ("reflect", "reflect")):
            proto = dict(proto0, border=border, nms_outside=outside)
            share_mass, share_above, fs = [], [], []
            for it in items:
                v = final_map(it, spec, proto, None)
                h, w = v.shape
                b = k // 2 + 1
                band = np.zeros_like(v, dtype=bool)
                band[:b, :] = band[-b:, :] = True
                band[:, :b] = band[:, -b:] = True
                share_mass.append(v[band].sum() / max(v.sum(), 1e-12))
                above = v >= t
                share_above.append(above[band].sum() / max(above.sum(), 1))
                c = image_counts(v, load_gt(it), thr, float(proto0["max_dist_frac"]),
                                 proto0.get("matching", "greedy"))
                cr, sr, cp, sp = c[ti]
                p, r = cp / max(sp, 1), cr / max(sr, 1)
                fs.append(2 * p * r / max(p + r, 1e-12))
            area = band.mean()
            rows.append((spec["name"], border, area, np.mean(share_mass), np.mean(share_above), np.mean(fs)))
            print(f"{spec['name']:14s} {border:8s} band area {area:.3f}  edge mass in band {np.mean(share_mass):.3f}  "
                  f"pixels>=t in band {np.mean(share_above):.3f}  mean F@t {np.mean(fs):.4f}", flush=True)
