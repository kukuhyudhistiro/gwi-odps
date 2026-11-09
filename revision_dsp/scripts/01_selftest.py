"""Equivalence and sanity tests. Run before any experiment.

    T1  kernels                = repo gabor_core (exact)
    T2  GWi / GWC raw maps     = repo run_gwi / run_gwc with zero padding
    T3  ODPS nearest/zero      = repo nms_odps.odps (exact, float32)
    T4  minmax_image + 8-bit   = repo save_edge_map + load_prediction_png
    T5  evaluator (greedy)     vs repo 04c counts on real or synthetic images
    T6  submitted pipeline reproduced end to end under legacy_protocol
    T7  timing of the evaluator per image (to plan the overnight runs)
    T0  (inside the gwi-odps repo) rev/legacy.py still equals ../src/*.py

Exit code 1 if any test fails.
"""
from __future__ import annotations

import sys
import time

import numpy as np

from _common import parser, setup, dump, split_ref
from rev import cfg as C
from rev import legacy as L
from rev import kernels as K
from rev.data import list_items, load_gt
from rev.evaluate import aggregate, image_counts, thresholds
from rev.methods import compute
from rev.nms import odps
from rev.normalize import normalize
from rev.preproc import load_and_preprocess

FAIL = []


def check(name, ok, info=""):
    print(f"  [{'PASS' if ok else 'FAIL'}] {name} {info}")
    if not ok:
        FAIL.append(name)


def main():
    ap = parser(__doc__)
    ap.add_argument("--dataset", default="BSDS500:val")
    ap.add_argument("--n-images", type=int, default=3)
    args = ap.parse_args()
    cfg, _ = setup(args)
    report = {}

    repo_src = C.ROOT.parent / "src"
    if (repo_src / "gabor_core.py").exists():
        print("T0 rev/legacy.py vs repo src/")
        import importlib.util

        def _load(name):
            spec = importlib.util.spec_from_file_location(f"repo_{name}", repo_src / f"{name}.py")
            mod = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = mod          # needed by @dataclass
            spec.loader.exec_module(mod)
            return mod
        gc_, no_ = _load("gabor_core"), _load("nms_odps")
        d0 = 0.0
        for k, lam in [(5, 4), (7, 4), (5, 6)]:
            for th in K.orientations_deg(8):
                a = gc_.make_gabor_imaginary(gc_.GaborParams(ksize=k, wavelength=lam), th)
                b = L.make_gabor_imaginary(L.GaborParams(ksize=k, wavelength=lam), th)
                d0 = max(d0, float(np.abs(a - b).max()))
        rnd = np.random.default_rng(3).random((60, 80)).astype(np.float32)
        ri = np.random.default_rng(4).integers(0, 8, (60, 80)).astype(np.int32)
        d0 = max(d0, float(np.abs(no_.odps(rnd, ri, 8, 2) - L.odps(rnd, ri, 8, 2)).max()))
        check("legacy copy == repo src", d0 == 0.0, f"max|diff|={d0:g}")
    else:
        print("T0 skipped (not inside the gwi-odps repo)")

    print("T1 kernels")
    worst = 0.0
    for k, lam in [(3, 3), (5, 4), (5, 6), (7, 4), (7, 5), (9, 4)]:
        p = L.GaborParams(ksize=k, wavelength=lam)
        for th in K.orientations_deg(8):
            kr0, ki0 = L.make_gabor_complex_pair(p, th)
            kr1, ki1 = K.gabor_pair(k, lam, th)
            worst = max(worst, np.abs(kr0 - kr1).max(), np.abs(ki0 - ki1).max(),
                        np.abs(L.make_gabor_imaginary(p, th) - ki1).max())
    check("kernels identical", worst == 0.0, f"max|diff|={worst:g}")

    ds, sp = split_ref(args.dataset)
    items = list_items(cfg, ds, sp)[: args.n_images]
    print(f"T2-T6 on {len(items)} image(s) from {args.dataset}")
    p = L.GaborParams()
    gwi_bank, gwc_bank = L.GWiFilterBank(p), L.GWCFilterBank(p)
    spec_gwi = dict(family="gwi", k=5, lam=4)
    spec_gwc = dict(family="gwc", k=5, lam=4, dc="raw")
    spec_odps = dict(family="gwi", k=5, lam=4, nms=dict(d=2, mode="nearest"))
    thr = thresholds(99)
    old_c = {m: [] for m in ("GWi", "GWi_odps", "GWC")}
    new_c = {m: [] for m in ("GWi", "GWi_odps", "GWC")}
    t_eval = []
    d_t2 = d_t3 = 0.0
    t4_ok = True
    for it in items:
        img = load_and_preprocess(it.image_path, "he")
        a = L.run_gwi(img, gwi_bank).magnitude
        b, idx = compute(img, spec_gwi, border="constant")
        d_t2 = max(d_t2, float(np.abs(a.astype(np.float32) - b).max()))
        a = L.run_gwc(img, gwc_bank).magnitude
        b, _ = compute(img, spec_gwc, border="constant")
        d_t2 = max(d_t2, float(np.abs(a.astype(np.float32) - b).max()))
        # T3: ODPS on the legacy GWi magnitude and argmax
        resp = np.stack([np.abs(__import__("cv2").filter2D(img, 6, k_, borderType=0))
                         for k_ in gwi_bank.kernels])
        mag = resp.max(0)
        oi = resp.argmax(0).astype(np.int32)
        lo = L.odps(mag, oi, 8, 2)
        nw = odps(mag, oi, 8, 2, mode="nearest", outside="zero")
        d_t3 = max(d_t3, float(np.abs(lo - nw).max()))
        rnd = np.random.default_rng(0).random(mag.shape).astype(np.float32)
        ri = np.random.default_rng(1).integers(0, 8, mag.shape).astype(np.int32)
        d_t3 = max(d_t3, float(np.abs(L.odps(rnd, ri, 8, 2) -
                                      odps(rnd, ri, 8, 2, "nearest", "zero")).max()))
        # T4
        v0 = L.save_edge_map_legacy(lo)
        v1 = normalize(nw, "minmax_image", None, False, True)
        t4_ok &= bool(np.array_equal(v0, v1))
        # T5/T6: legacy pipeline + legacy evaluator vs new pipeline + new evaluator
        gts = load_gt(it)
        h, w = img.shape
        maxd = 0.0075 * np.hypot(h, w)
        maps_old = {"GWi": L.save_edge_map_legacy(L.run_gwi(img, gwi_bank).magnitude),
                    "GWi_odps": v0,
                    "GWC": L.save_edge_map_legacy(L.run_gwc(img, gwc_bank).magnitude)}
        proto = dict(border="constant", nms_outside="zero")
        for m, sp_ in (("GWi", spec_gwi), ("GWi_odps", spec_odps), ("GWC", spec_gwc)):
            old_c[m].append(np.array(L.evaluate_image_thresholds(maps_old[m], gts, thr, 0.0075)))
            raw, _ = compute(img, sp_, border=proto["border"], nms_outside=proto["nms_outside"])
            v = normalize(raw, "minmax_image", None, False, True)
            t0 = time.perf_counter()
            new_c[m].append(image_counts(v, gts, thr, 0.0075, "greedy"))
            t_eval.append(time.perf_counter() - t0)
    check("GWi/GWC raw maps", d_t2 < 1e-5, f"max|diff|={d_t2:.2e}")
    check("ODPS nearest/zero", d_t3 == 0.0, f"max|diff|={d_t3:g}")
    check("minmax + 8-bit", t4_ok)

    print("T5/T6 legacy pipeline+04c vs new pipeline+evaluator (legacy protocol)")
    for m in old_c:
        co, cn = np.stack(old_c[m]), np.stack(new_c[m])
        diff = np.abs(co - cn)
        rel = float(diff[..., [0, 2]].sum() / max(1, co[..., [0, 2]].sum()))
        ao = L.aggregate_legacy(co, thr)
        an = aggregate(cn, thr)
        report[m] = dict(ods_old=ao["ods"], ods_new=an["ods"], rel_count_diff=rel,
                         sumR_equal=bool(np.array_equal(co[..., 1], cn[..., 1])),
                         sumP_equal=bool(np.array_equal(co[..., 3], cn[..., 3])))
        print(f"    {m:9s} ODS old={ao['ods']:.4f} new={an['ods']:.4f} "
              f"rel.count diff={rel:.2e}")
        check(f"{m}: sumP/sumR identical", report[m]["sumR_equal"] and report[m]["sumP_equal"])
        check(f"{m}: counts identical to 04c", rel == 0.0)
    te = float(np.mean(t_eval))
    report["eval_seconds_per_image_pair"] = te
    print(f"T7 evaluator: {te:.2f} s per image per method (99 thresholds), "
          f"image size {img.shape}")
    report["failed"] = FAIL
    dump(report, C.results_dir(cfg, "selftest") / "selftest.json")
    if FAIL:
        sys.exit(1)


if __name__ == "__main__":
    main()
