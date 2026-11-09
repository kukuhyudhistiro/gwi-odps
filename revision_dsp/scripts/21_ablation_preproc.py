"""R2.7: contribution of the preprocessing stage to the proposed method.

The reviewer asks for the proposed method "with and without these preprocessing
steps" (histogram equalization and the normalization to [0, 1]). GWi and
GWi+ODPS of the frozen configuration are evaluated on every test set with:
    he            HE + /255           (manuscript, Eq. 2)
    none          no HE, /255
    he_noscale    HE, no /255
    none_noscale  no HE, no /255
Parameters are frozen before this run; nothing is selected here.

Note: /255 is a constant factor. The convolutions are linear and the maps are
min-max normalized per image, so /255 cannot change the evaluated maps; the
'_noscale' rows are reported to show this empirically.

Outputs (results/preproc/): preproc_ablation.csv
"""
from __future__ import annotations

from _common import load_final, parser, setup, split_ref
from rev import cfg as C
from rev.runner import run_counts, summary_row, write_csv

MODES = ("he", "none", "he_noscale", "none_noscale")


def main():
    ap = parser(__doc__)
    args = ap.parse_args()
    cfg, n_jobs = setup(args)
    final = load_final(cfg, args.limit)
    by = {m["name"]: m for m in final["methods"]}
    P = final["primary"]
    rows = []
    for ref in final["test_sets"]:
        ds, sp = split_ref(ref)
        for name in (P["gwi"], P["gwi_odps"]):
            res = {}
            for mode in MODES:
                proto = C.protocol_of(cfg, {"preproc": mode})
                res[mode] = summary_row(run_counts(cfg, by[name], ds, sp, proto, n_jobs,
                                                   limit=args.limit, force=args.force), ds, sp)
            row = dict(method=name, dataset=ds)
            for mode in MODES:
                for k in ("ODS", "OIS", "AP"):
                    row[f"{k}_{mode}"] = res[mode][k]
            row["dODS_HE"] = round(res["he"]["ODS"] - res["none"]["ODS"], 4)
            row["dODS_scale"] = round(res["he"]["ODS"] - res["he_noscale"]["ODS"], 4)
            rows.append(row)
    write_csv(rows, C.results_dir(cfg, "preproc") / "preproc_ablation.csv")


if __name__ == "__main__":
    main()
