"""R1.3: what ODPS removes, and whether it distorts boundaries.

Reviewer 1, point 3 asks how ODPS reduces artifacts "without introducing
boundary distortions". Operational definition used here: for every test image,
at each method's dataset ODS threshold, precision, recall, and the mean /
90th-percentile distance (px) of matched prediction-GT pairs, for GWi and
GWi+ODPS (same kernel). A distortion would show up as a larger matched distance
or a recall drop at similar precision.
For the images of Figures 7, 9 and 11 (config.yaml -> qualitative): input, GT,
GWi, GWi+ODPS, and a difference map (pixels removed by ODPS in red, kept in
white, GT not detected after ODPS in green).

Outputs (results/qualitative/): localization.csv, <dataset>_<id>.png
"""
from __future__ import annotations

import numpy as np
import yaml

from _common import load_final, parser, setup, split_ref
from rev import cfg as C
from rev.data import list_items, load_gt
from rev.evaluate import GTCache, aggregate, counts_at
from rev.preproc import load_and_preprocess
from rev.runner import final_map, get_scale, run_counts, write_csv


def main():
    ap = parser(__doc__)
    args = ap.parse_args()
    cfg, n_jobs = setup(args)
    final = load_final(cfg, args.limit)
    proto = C.protocol_of(cfg)
    by = {m["name"]: m for m in final["methods"]}
    P = final["primary"]
    names = [P["gwi"], P["gwi_odps"]]
    out = C.results_dir(cfg, "qualitative")
    rows = []
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    for ref in final["test_sets"]:
        ds, sp = split_ref(ref)
        items = list_items(cfg, ds, sp)
        if args.limit:
            items = items[: args.limit]
        t_ods, scales = {}, {}
        for n in names:
            r = run_counts(cfg, by[n], ds, sp, proto, n_jobs, limit=args.limit)
            t_ods[n] = aggregate(r["counts"], r["thresholds"])["ods_t"]
            scales[n] = get_scale(cfg, by[n], proto, n_jobs)
        want = set(cfg.get("qualitative", {}).get(ds, []))
        for it in items:
            gts = load_gt(it)
            gtc = GTCache(gts)
            h, w = gts[0].shape
            maxd = float(proto["max_dist_frac"]) * float(np.hypot(h, w))
            maps = {}
            for n in names:
                v = final_map(it, by[n], proto, scales[n])
                maps[n] = v
                (cr, sr, cp, sp_), dist = counts_at(v >= t_ods[n], gtc, maxd, "greedy",
                                                    return_dist=True)
                rows.append(dict(dataset=ds, image_id=it.image_id, method=n,
                                 threshold=round(t_ods[n], 3),
                                 precision=round(cp / max(sp_, 1), 4),
                                 recall=round(cr / max(sr, 1), 4),
                                 mean_match_dist_px=round(float(dist.mean()), 3) if dist.size else None,
                                 p90_match_dist_px=round(float(np.percentile(dist, 90)), 3) if dist.size else None))
            if it.image_id in want:
                img = load_and_preprocess(it.image_path, "none")
                gt_union = np.any(np.stack(gts), axis=0)
                a = maps[P["gwi"]] >= t_ods[P["gwi"]]
                b = maps[P["gwi_odps"]] >= t_ods[P["gwi_odps"]]
                diff = np.zeros((h, w, 3))
                diff[a & ~b] = (1, 0, 0)
                diff[b] = (1, 1, 1)
                diff[gt_union & ~b] = (0, 0.8, 0)
                panels = [("input", img, "gray"), ("GT (union)", gt_union, "gray")] + \
                         [(n, maps[n], "gray") for n in names] + [("removed by ODPS (red)", diff, None)]
                fig, ax = plt.subplots(1, len(panels), figsize=(3.2 * len(panels), 3.2))
                for a_, (t, im, cm) in zip(ax, panels):
                    a_.imshow(im, cmap=cm)
                    a_.set_title(t, fontsize=8)
                    a_.axis("off")
                fig.tight_layout()
                fig.savefig(out / f"{ds}_{it.image_id}.png", dpi=150)
                plt.close(fig)
    write_csv(rows, out / "localization.csv")
    summ = []
    for ds in sorted({r["dataset"] for r in rows}):
        for n in names:
            sub = [r for r in rows if r["dataset"] == ds and r["method"] == n]
            md = [r["mean_match_dist_px"] for r in sub if r["mean_match_dist_px"] is not None]
            summ.append(dict(dataset=ds, method=n, n=len(sub),
                             mean_precision=round(float(np.mean([r["precision"] for r in sub])), 4),
                             mean_recall=round(float(np.mean([r["recall"] for r in sub])), 4),
                             mean_match_dist_px=round(float(np.mean(md)), 3) if md else None))
    write_csv(summ, out / "localization_summary.csv")


if __name__ == "__main__":
    main()
