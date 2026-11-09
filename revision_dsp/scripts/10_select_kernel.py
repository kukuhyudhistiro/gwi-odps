"""R2.1 (and the kernel ablation of R3.4): select the GWi kernel without test data.

The rule is that of Tables 1-4 of the manuscript: for each (k, lambda) candidate
in config.yaml (selection.candidates; since amendment 1 the grid k in {5, 7, 9} x
lambda in {3..8}, which contains the five configurations of Tables 1-4), ODS of
GWi (Stages 1-5) is computed on every selection split, and the configuration with
the highest mean ODS is selected.
Only the data differ from the submission: BSDS500 train+val and BIPED train
replace the test sets (UDED has no non-test split). d = lambda/2 (Section 3.6).
N, sigma/lambda and gamma stay at the manuscript values.

GWi+ODPS (d = lambda/2) is evaluated for every candidate as well. Up to
amendment 1 it did not enter the selection, as in the manuscript. Amendment 2
(CHANGELOG.md) changes the criterion to mean ODS of GWi+ODPS
(selection.criterion = mean_ods_gwi_odps); the GWi criterion is still computed
and its choice is written to selected.json (selected_under_gwi_criterion).
selected.json also lists, per k, the best lambda under the criterion and whether
it is at the largest lambda evaluated (edge rule of amendment 2).

Outputs (results/selection/): kernel_ablation.csv (one row per candidate x split
x method), kernel_mean.csv (mean ODS and ranks, as Table 4), selected.json
"""
from __future__ import annotations

from _common import dump, parser, setup, split_ref
from rev import cfg as C
from rev.runner import run_counts, summary_row, write_csv
from rev.specs import d_of, gabor_specs, tag_of


def mac(spec):
    return int(spec["N"]) * int(spec["k"]) ** 2


def main():
    args = parser(__doc__).parse_args()
    cfg, n_jobs = setup(args)
    proto = C.protocol_of(cfg)
    S = cfg["selection"]
    crit = S.get("criterion")
    if crit not in ("mean_ods_gwi", "mean_ods_gwi_odps"):
        raise SystemExit("selection.criterion must be mean_ods_gwi or mean_ods_gwi_odps")
    fixed = S["fixed"]
    out = C.results_dir(cfg, "selection")
    rows, mean_rows = [], []
    for cand in S["candidates"]:
        kcfg = dict(cand, **fixed)
        d = d_of(cand["lam"], S["d_rule"])
        gwi, gwi_odps = gabor_specs(kcfg, d)[:2]
        per_split, per_split_odps = {}, {}
        for ref in S["splits"]:
            ds, sp = split_ref(ref)
            for s in (gwi, gwi_odps):
                r = run_counts(cfg, s, ds, sp, proto, n_jobs, limit=args.limit, force=args.force)
                row = summary_row(r, ds, sp)
                row.update(k=cand["k"], lam=cand["lam"], d=d if s is gwi_odps else "",
                           rho=round((int(cand["k"]) // 2) / float(cand["lam"]), 3),
                           mac=mac(s))
                rows.append(row)
                if s is gwi:
                    per_split[ref] = row["ODS"]
                else:
                    per_split_odps[ref] = row["ODS"]
        mean_rows.append(dict(tag=tag_of(cand["k"], cand["lam"]), k=cand["k"], lam=cand["lam"],
                              d=d, mean_ods_gwi=round(sum(per_split.values()) / len(per_split), 4),
                              mean_ods_gwi_odps=round(sum(per_split_odps.values()) / len(per_split_odps), 4),
                              **{f"ODS_GWi_{ref}": v for ref, v in per_split.items()},
                              **{f"ODS_GWiODPS_{ref}": v for ref, v in per_split_odps.items()}))
    for ref in S["splits"]:
        for meth in ("GWi", "GWiODPS"):
            key = f"ODS_{meth}_{ref}"
            order = sorted(mean_rows, key=lambda r: -r[key])
            for rank, r in enumerate(order, 1):
                r[f"rank_{meth}_{ref}"] = rank
    # max() keeps the first of equal values, i.e. the candidate listed first in config
    best = max(mean_rows, key=lambda r: r[crit])
    best_gwi = max(mean_rows, key=lambda r: r["mean_ods_gwi"])
    best_odps = max(mean_rows, key=lambda r: r["mean_ods_gwi_odps"])
    bound_f = S.get("lambda_bound_factor")
    per_k = []
    for k in sorted({int(r["k"]) for r in mean_rows}):
        rk = [r for r in mean_rows if int(r["k"]) == k]
        bk = max(rk, key=lambda r: r[crit])
        lam_max = max(float(r["lam"]) for r in rk)
        bound = float(bound_f * (k // 2)) if bound_f else None
        per_k.append(dict(k=k, best_lam=bk["lam"], value=bk[crit], lam_max_evaluated=lam_max,
                          at_upper_edge=float(bk["lam"]) == lam_max,
                          lam_bound=bound,
                          at_bound=(bound is not None and float(bk["lam"]) >= bound)))
    write_csv(rows, out / "kernel_ablation.csv")
    write_csv(sorted(mean_rows, key=lambda r: -r[crit]), out / "kernel_mean.csv")
    names = {"mean_ods_gwi": "GWi (as Table 4 of the manuscript)",
             "mean_ods_gwi_odps": "GWi+ODPS (amendment 2)"}
    dump(dict(k=best["k"], lam=best["lam"], d=best["d"], **fixed,
              criterion=crit, value=best[crit],
              mean_ods_gwi=best["mean_ods_gwi"], mean_ods_gwi_odps=best["mean_ods_gwi_odps"],
              rule="highest mean ODS of %s over %s; d = lambda/2"
                   % (names[crit], ", ".join(S["splits"])),
              selected_under_gwi_criterion=dict(k=best_gwi["k"], lam=best_gwi["lam"],
                                                mean_ods_gwi=best_gwi["mean_ods_gwi"]),
              selected_under_gwi_odps_criterion=dict(k=best_odps["k"], lam=best_odps["lam"],
                                                     mean_ods_gwi_odps=best_odps["mean_ods_gwi_odps"]),
              per_k_edge=per_k,
              submitted_config_selected=(int(best["k"]) == 5 and float(best["lam"]) == 4.0),
              limit=args.limit),
         out / "selected.json")
    print(f"  selected ({crit}): k={best['k']} lambda={best['lam']} d={best['d']} "
          f"(value {best[crit]})")
    print(f"  under GWi criterion: k={best_gwi['k']} lambda={best_gwi['lam']} "
          f"({best_gwi['mean_ods_gwi']})")
    for e in per_k:
        print(f"  k={e['k']}: best lambda {e['best_lam']} ({e['value']}), largest evaluated "
              f"{e['lam_max_evaluated']}, at edge {e['at_upper_edge']}, bound {e['lam_bound']}")


if __name__ == "__main__":
    main()
