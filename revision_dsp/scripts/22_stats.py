"""R1.1 and R2.11: variability across images and paired comparisons on the test sets.

Family of comparisons named by the reviewers ("differences among GWi, GWi+ODPS,
and GWC"; "ODS improvements over complex Gabor"), per dataset, Holm-adjusted
over all datasets (3 pairs x 3 datasets = 9 tests):
    GWi       vs GWC
    GWi+ODPS  vs GWC
    GWi+ODPS  vs GWi
Analysis for R1.5 (why GWi differs from GWC), reported separately, not in the
Holm family:
    GWi       vs GWC zero-DC
    GWC zero-DC vs GWC

For each pair: Delta ODS with paired-bootstrap 95% CI over images, Wilcoxon
signed-rank on per-image F (rank-biserial r), fraction of images where A is
better. For each method: ODS, OIS, AP with bootstrap 95% CI (OIS and AP by
dataset-level accumulation; the definitions of the submitted tables in the
*_legacy columns),
and mean, SD, median and IQR of per-image F at the dataset ODS threshold.

claims_guard.json gives the verb allowed in the manuscript for each pair
("improves" only when the 95% CI of Delta ODS excludes 0).

Outputs (results/stats/): pairs.csv, variability.csv, claims_guard.json
"""
from __future__ import annotations

from _common import dump, load_final, parser, setup, split_ref
from rev import cfg as C
from rev import stats as S
from rev.runner import align, run_counts, write_csv


def main():
    args = parser(__doc__).parse_args()
    cfg, n_jobs = setup(args)
    final = load_final(cfg, args.limit)
    proto = C.protocol_of(cfg)
    by_name = {m["name"]: m for m in final["methods"]}
    P = final["primary"]
    family = [(P["gwi"], P["gwc"]), (P["gwi_odps"], P["gwc"]), (P["gwi_odps"], P["gwi"])]
    analysis = [(P["gwi"], P["gwc_zero"]), (P["gwc_zero"], P["gwc"])]
    st = cfg["stats"]
    B, seed = int(st["bootstrap"]), int(st["seed"])
    rows, vrows, pvals, guard = [], [], [], {}
    for ref in final["test_sets"]:
        ds, sp = split_ref(ref)
        cache = {}

        def get(n):
            if n not in cache:
                cache[n] = run_counts(cfg, by_name[n], ds, sp, proto, n_jobs, limit=args.limit)
            return cache[n]
        for kind, pairs in (("reviewer_family", family), ("analysis_R1.5", analysis)):
            for a_n, b_n in pairs:
                a, b = align(get(a_n), get(b_n))
                bt = S.bootstrap_delta(a, b, B=B, seed=seed)
                wx = S.wilcoxon_paired(a, b)
                row = dict(dataset=ds, kind=kind, A=a_n, B=b_n, n=wx["n"],
                           ODS_A=round(bt["ods_a"], 4), ODS_B=round(bt["ods_b"], 4),
                           dODS=round(bt["delta"], 4),
                           ci95_lo=round(bt["ci95"][0], 4), ci95_hi=round(bt["ci95"][1], 4),
                           wilcoxon_p=wx["p"], r_rank_biserial=round(wx["r_rb"], 3),
                           frac_images_A_better=round(wx["frac_a_better"], 3),
                           superiority=S.superiority(bt["ci95"]))
                if kind == "reviewer_family":
                    pvals.append((len(rows), wx["p"]))
                rows.append(row)
                guard[f"{ds}: {a_n} vs {b_n}"] = S.claim_word(bt["ci95"])
        for m in final["methods"]:
            try:
                r = get(m["name"])
            except (RuntimeError, FileNotFoundError) as e:
                print(f"  [skip] {m['name']}: {e}")
                continue
            v = S.variability(r["counts"], r["thresholds"], B=B, seed=seed)
            vrows.append(dict(dataset=ds, method=m["name"], n=v["n"],
                              ODS=round(v["ods"], 4), ODS_ci95=fmt(v["ods_ci95"]),
                              OIS=round(v["ois"], 4), OIS_ci95=fmt(v["ois_ci95"]),
                              AP=round(v["ap"], 4), AP_ci95=fmt(v["ap_ci95"]),
                              OIS_legacy=round(v["ois_legacy"], 4),
                              OIS_legacy_ci95=fmt(v["ois_legacy_ci95"]),
                              AP_legacy=round(v["ap_legacy"], 4),
                              AP_legacy_ci95=fmt(v["ap_legacy_ci95"]),
                              F_img_mean=round(v["f_img_mean"], 4),
                              F_img_sd=round(v["f_img_sd"], 4),
                              F_img_median=round(v["f_img_median"], 4),
                              F_img_iqr=fmt(v["f_img_iqr"])))
    adj = S.holm([p for _, p in pvals])
    for (i, _), a in zip(pvals, adj):
        rows[i]["wilcoxon_p_holm"] = a
    out = C.results_dir(cfg, "stats")
    write_csv(rows, out / "pairs.csv")
    write_csv(vrows, out / "variability.csv")
    dump(guard, out / "claims_guard.json")


def fmt(pair):
    return f"[{pair[0]:.4f}, {pair[1]:.4f}]"


if __name__ == "__main__":
    main()
