"""WP9 (R1.2, R3.5): evaluate edge maps produced by learning-based detectors
(TEED, PiDiNet, LDC, ...) with exactly the same evaluator.

Run each detector from its official repository, then save 8-bit PNG maps at
the original resolution:
    <maps_root>/<METHOD>/<DATASET>/<image_id>.png
Pass --nms to also report the maps after a standard edge NMS (orientation from
the Sobel gradient of the smoothed map, d = 1, bilinear); learned detectors
are usually reported with NMS.

Also fill results/external/models.yaml (by hand) with: params, FLOPs at the
test resolution, training data of the weights, CPU runtime (1 thread).
BIPED results of weights trained on BIPED train are in-domain: mark them.

Outputs (results/external/): summary.csv
"""
from __future__ import annotations

from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import cv2
import numpy as np
import yaml

from _common import parser, setup, split_ref
from rev import cfg as C
from rev.data import list_items, load_gt
from rev.evaluate import aggregate, image_counts, thresholds
from rev.nms import odps, quantize_direction


def _std_nms(v):
    sm = cv2.GaussianBlur(v, (0, 0), 1.0, borderType=cv2.BORDER_REFLECT_101)
    gx = cv2.Sobel(sm, cv2.CV_64F, 1, 0, ksize=3, borderType=cv2.BORDER_REFLECT_101)
    gy = cv2.Sobel(sm, cv2.CV_64F, 0, 1, ksize=3, borderType=cv2.BORDER_REFLECT_101)
    idx = quantize_direction(gx, gy, 16)
    return odps(v, idx, N=16, d=1, mode="bilinear", outside="reflect")


def _task(a):
    png, item, proto, use_nms = a
    v = cv2.imread(png, cv2.IMREAD_GRAYSCALE)
    if v is None:
        raise FileNotFoundError(png)
    gts = load_gt(item)
    if v.shape != gts[0].shape:
        v = cv2.resize(v, (gts[0].shape[1], gts[0].shape[0]), interpolation=cv2.INTER_LINEAR)
    v = v.astype(np.float32) / 255.0
    if use_nms:
        v = _std_nms(v)
    thr = thresholds(int(proto["n_thresholds"]))
    return image_counts(v, gts, thr, float(proto["max_dist_frac"]), proto["matching"])


def main():
    ap = parser(__doc__)
    ap.add_argument("--maps-root", required=True)
    ap.add_argument("--methods", nargs="+", required=True)
    ap.add_argument("--nms", action="store_true")
    args = ap.parse_args()
    cfg, n_jobs = setup(args)
    proto = C.protocol_of(cfg)
    rows = []
    for ref in cfg["test_sets"]:
        ds, sp = split_ref(ref)
        items = list_items(cfg, ds, sp)
        if args.limit:
            items = items[: args.limit]
        for m in args.methods:
            d = Path(args.maps_root) / m / ds
            if not d.is_dir():
                print(f"  [skip] {d} not found")
                continue
            for use_nms in ([False, True] if args.nms else [False]):
                tasks = [(str(d / f"{it.image_id}.png"), it, proto, use_nms) for it in items]
                with ProcessPoolExecutor(max_workers=n_jobs) as ex:
                    counts = np.stack(list(ex.map(_task, tasks)))
                thr = thresholds(int(proto["n_thresholds"]))
                f = C.results_dir(cfg, "external", "counts") / f"{m}{'_nms' if use_nms else ''}_{ds}.npz"
                np.savez_compressed(f, ids=np.array([it.image_id for it in items]),
                                    counts=counts, thresholds=thr)
                a = aggregate(counts, thr)
                rows.append(dict(method=m + (" +NMS" if use_nms else ""), dataset=ds,
                                 n=a["n_images"], ODS=round(a["ods"], 4),
                                 OIS=round(a["ois"], 4), AP=round(a["ap"], 4)))
                print(f"    {rows[-1]}")
    from rev.runner import write_csv
    write_csv(rows, C.results_dir(cfg, "external") / "summary.csv")
    mf = C.results_dir(cfg, "external") / "models.yaml"
    if not mf.exists():
        mf.write_text(yaml.safe_dump({m: dict(repo="", weights="", trained_on="", params="",
                                              flops_at_test_res="", cpu_ms_1thread="")
                                      for m in args.methods}, sort_keys=False))


if __name__ == "__main__":
    main()
