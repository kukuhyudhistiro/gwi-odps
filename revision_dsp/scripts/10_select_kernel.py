"""R2.1 (and the kernel ablation of R3.4): select the GWi kernel without test data.

The rule is that of Tables 1-4 of the manuscript: for each (k, lambda) candidate
in config.yaml (selection.candidates; since amendment 1 the grid k in {5, 7, 9} x
lambda in {3..8}, which contains the five configurations of Tables 1-4), ODS of
GWi (Stages 1-5) is computed on every selection split, and the configuration with
the highest mean ODS is selected.
Only the data differ from the submission: BSDS500 train+val and BIPED train
replace the test sets (UDED has no non-test split). d = lambda/2 (Section 3.6).
N, sigma/lambda and gamma stay at the manuscript values.

GWi+ODPS (d = lambda/2) is evaluated for every candidate as well and reported;
it does not enter the selection, as in the manuscript.

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
    if S.get("criterion") != "mean_ods_gwi":
        raise SystemExit("selection.criterion must be mean_ods_gwi")
    fixed = S["fixed"]
    out = C.results_dir(cfg, "selection")
    rows, mean_rows = [], []
    for cand in S["candidates"]:
        kcfg = dict(cand, **fixed)
        d = d_of(cand["lam"], S["d_rule"])
        gwi, gwi_odps = gabor_specs(kcfg, d)[:2]
        per_split = {}
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
        mean_rows.append(dict(tag=tag_of(cand["k"], cand["lam"]), k=cand["k"], lam=cand["lam"],
                              d=d, mean_ods_gwi=round(sum(per_split.values()) / len(per_split), 4),
                              **{f"ODS_GWi_{ref}": v for ref, v in per_split.items()}))
    for ref in S["splits"]:
        key = f"ODS_GWi_{ref}"
        order = sorted(mean_rows, key=lambda r: -r[key])
        for rank, r in enumerate(order, 1):
            r[f"rank_{ref}"] = rank
    best = max(mean_rows, key=lambda r: r["mean_ods_gwi"])
    write_csv(rows, out / "kernel_ablation.csv")
    write_csv(sorted(mean_rows, key=lambda r: -r["mean_ods_gwi"]), out / "kernel_mean.csv")
    dump(dict(k=best["k"], lam=best["lam"], d=best["d"], **fixed,
              mean_ods_gwi=best["mean_ods_gwi"],
              rule="highest mean ODS of GWi over %s (as Table 4 of the manuscript); "
                   "d = lambda/2" % ", ".join(S["splits"]),
              submitted_config_selected=(int(best["k"]) == 5 and float(best["lam"]) == 4.0),
              limit=args.limit),
         out / "selected.json")
    print(f"  selected: k={best['k']} lambda={best['lam']} d={best['d']} "
          f"(mean ODS of GWi {best['mean_ods_gwi']})")


if __name__ == "__main__":
    main()
