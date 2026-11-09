"""WP10 (R1.4, R2.10, R3.3, R3.6): runtime with stage breakdown.

Protocol (Section 4.4 of the manuscript, plus repeats for R2.10): 1 thread
(cv2.setNumThreads(1), OMP/MKL/OPENBLAS = 1), an untimed warm-up pass over the
first `warmup` images, then for each image `repeats` timed runs; the per-image
value is the median of the repeats; tables report mean and std over images.

Stages
    pre      Stage 1 (grayscale, HE, /255), timed separately
    filter   convolutions (+ |.| or sqrt for Gabor; magnitude for gradients)
    pool     max/argmax over orientations, or direction quantization
    nms      ODPS / NMS
    total    filter + pool + nms   (pre reported separately, as in the paper)
Kernel construction is done once, offline; its time is reported separately for
every Gabor configuration in the frozen list (kernels.csv).

Also writes the analytic multiply-accumulate count per pixel (mac.csv) and the
time of ODPS alone for every d of the ablation at the selected configuration
(odps_d.csv; R2.5 asks for the effect of d on cost).

Outputs (results/runtime/): per_image.csv, summary.csv, mac.csv, kernels.csv,
odps_d.csv, env.json
"""
from __future__ import annotations

import os
import platform
import statistics as stt
import time

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ[_v] = "1"

import cv2  # noqa: E402
import numpy as np  # noqa: E402
import yaml  # noqa: E402

from _common import load_final, parser, setup, dump, split_ref  # noqa: E402
from rev import cfg as C  # noqa: E402
from rev import kernels as K  # noqa: E402
from rev.data import list_items  # noqa: E402
from rev.methods import compute  # noqa: E402
from rev.nms import odps  # noqa: E402
from rev.preproc import load_rgb, preprocess  # noqa: E402
from rev.runner import write_csv  # noqa: E402


def mac_per_pixel(spec):
    f = spec["family"]
    N = int(spec.get("N", 8))
    if f in ("gwi", "gwe"):
        return N * int(spec["k"]) ** 2
    if f == "gwc":
        return 2 * N * int(spec["k"]) ** 2
    if f == "sobel":
        return 2 * (3 + 3)              # separable 3x3, two directions
    if f == "canny":
        return 2 * (3 + 3)              # Sobel stage only; NMS and hysteresis not counted
    if f == "gaussgrad":
        r = int(np.ceil(3 * float(spec.get("sigma", 1.4))))
        return 2 * (2 * r + 1) + 2 * (3 + 3)
    if f == "log":
        return int(spec.get("ksize", 7)) ** 2
    return None                         # PC (FFT) and ED: not a convolution count


def main():
    ap = parser(__doc__)
    ap.add_argument("--only", nargs="*", default=None)
    args = ap.parse_args()
    cfg, _ = setup(args)
    cv2.setNumThreads(1)
    proto = C.protocol_of(cfg)
    final = load_final(cfg, args.limit)
    R, W = int(cfg["runtime"]["repeats"]), int(cfg["runtime"]["warmup"])
    methods = [m for m in final["methods"] if not args.only or m["name"] in args.only]
    rows = []
    for ref in final["test_sets"]:
        ds, sp = split_ref(ref)
        items = list_items(cfg, ds, sp)
        if args.limit:
            items = items[: args.limit]
        imgs = {}
        for it in items:
            rgb = load_rgb(it.image_path)
            tp = []
            for _ in range(R):
                t0 = time.perf_counter()
                img = preprocess(rgb, proto["preproc"])
                tp.append(time.perf_counter() - t0)
            imgs[it.image_id] = (img, stt.median(tp))
        for m in methods:
            bd = C.border_for(proto, m)
            try:
                for img, _ in list(imgs.values())[:W]:
                    compute(img, m, border=bd, nms_outside=proto["nms_outside"])
            except RuntimeError as e:
                print(f"  [skip] {m['name']}: {e}")
                continue
            for iid, (img, tpre) in imgs.items():
                st = {"filter": [], "pool": [], "nms": [], "total": []}
                for _ in range(R):
                    tm = {}
                    compute(img, m, border=bd, nms_outside=proto["nms_outside"], timer=tm)
                    for k in ("filter", "pool", "nms"):
                        st[k].append(tm.get(k, 0.0))
                    st["total"].append(sum(tm.values()))
                rows.append(dict(dataset=ds, method=m["name"], image_id=iid,
                                 h=img.shape[0], w=img.shape[1],
                                 pre_ms=1e3 * tpre,
                                 **{f"{k}_ms": 1e3 * stt.median(v) for k, v in st.items()}))
            print(f"    {ds} {m['name']}: done")
    out = C.results_dir(cfg, "runtime")
    write_csv(rows, out / "per_image.csv")
    summ = []
    for ds in sorted({r["dataset"] for r in rows}):
        for name in dict.fromkeys(r["method"] for r in rows if r["dataset"] == ds):
            sub = [r for r in rows if r["dataset"] == ds and r["method"] == name]
            d = dict(dataset=ds, method=name, n=len(sub),
                     res=f"{sub[0]['h']}x{sub[0]['w']}" if len({(r['h'], r['w']) for r in sub}) == 1 else "varied")
            for k in ("pre_ms", "filter_ms", "pool_ms", "nms_ms", "total_ms"):
                v = [r[k] for r in sub]
                d[k + "_mean"] = round(float(np.mean(v)), 3)
                d[k + "_std"] = round(float(np.std(v)), 3)
            summ.append(d)
    write_csv(summ, out / "summary.csv")
    write_csv([dict(method=m["name"], family=m["family"], mac_per_pixel=mac_per_pixel(m))
               for m in methods], out / "mac.csv")
    # kernel construction, per Gabor configuration (median of R runs)
    krows, seen = [], set()
    for m in methods:
        if m["family"] not in C.GABOR_FAMILIES:
            continue
        key = (m["k"], m["lam"], m.get("N", 8), m.get("sigma_ratio", 0.56),
               m.get("gamma", 0.5), m.get("dc", "raw"))
        if key in seen:
            continue
        seen.add(key)
        tk = []
        for _ in range(R):
            t0 = time.perf_counter()
            K.gabor_bank(key[0], key[1], key[2], key[3], key[4], key[5])
            tk.append(time.perf_counter() - t0)
        krows.append(dict(k=key[0], lam=key[1], N=key[2], sigma_ratio=key[3], gamma=key[4],
                          dc=key[5], kernel_construction_ms=round(1e3 * stt.median(tk), 4)))
    write_csv(krows, out / "kernels.csv")
    # ODPS alone for every d of the ablation, selected configuration, first test set
    P = final["primary"]
    by = {m["name"]: m for m in methods}
    drows = []
    if P["gwi"] in by and "ablation" in cfg:
        g = by[P["gwi"]]
        lam = float(g["lam"])
        dlist = sorted(set(float(d) for d in cfg["ablation"]["lam_d"]["d"]) | {lam / 2.0})
        ds0, sp0 = split_ref(final["test_sets"][0])
        items = list_items(cfg, ds0, sp0)[: (args.limit or None)]
        per_d = {d: [] for d in dlist}
        for it in items:
            img = preprocess(load_rgb(it.image_path), proto["preproc"])
            mag, idx = compute(img, g, border=C.border_for(proto, g),
                               nms_outside=proto["nms_outside"], need_idx=True)
            for d in dlist:
                tt = []
                for _ in range(R):
                    t0 = time.perf_counter()
                    odps(mag, idx, int(g.get("N", 8)), d, "nearest", proto["nms_outside"])
                    tt.append(time.perf_counter() - t0)
                per_d[d].append(1e3 * stt.median(tt))
        for d in dlist:
            drows.append(dict(dataset=ds0, config=P["gwi"], d=d, n=len(per_d[d]),
                              odps_ms_mean=round(float(np.mean(per_d[d])), 3),
                              odps_ms_std=round(float(np.std(per_d[d])), 3)))
    write_csv(drows, out / "odps_d.csv")
    dump(dict(platform=platform.platform(), processor=platform.processor(),
              machine=platform.machine(), python=platform.python_version(),
              opencv=cv2.__version__, numpy=np.__version__,
              cv2_threads=cv2.getNumThreads(), cpu_count=os.cpu_count(),
              repeats=R, warmup_images=W),
         out / "env.json")


if __name__ == "__main__":
    main()
