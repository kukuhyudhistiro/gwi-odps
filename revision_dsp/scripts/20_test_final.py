"""Final evaluation on the test sets with the frozen configuration.

Run only after 12_freeze.py and the freeze tag. Every method in
config_final.yaml is evaluated on BSDS500 test, BIPED test and UDED.

--legacy-check additionally reproduces the submitted numbers for GWi, GWi+ODPS
and GWC (k5 lam4) under legacy_protocol (zero padding, per-image min-max). For GWi, GWi+ODPS and
GWC this protocol equals `protocol`, so the main run at k5 lambda4 must give the
same numbers.
With the same library versions these should match Tables 5-7 of the
submission to 4 decimals (BSDS500 GWi 0.4443, GWi+ODPS 0.4696, GWC 0.3941).

Outputs (results/test/): summary.csv, legacy_check.csv
"""
from __future__ import annotations

import yaml

from _common import load_final, parser, setup, split_ref
from rev import cfg as C
from rev.runner import run_counts, summary_row, write_csv


def main():
    ap = parser(__doc__)
    ap.add_argument("--legacy-check", action="store_true")
    ap.add_argument("--only", nargs="*", default=None, help="method names to run")
    args = ap.parse_args()
    cfg, n_jobs = setup(args)
    final = load_final(cfg, args.limit)
    proto = C.protocol_of(cfg)
    rows = []
    for ref in final["test_sets"]:
        ds, sp = split_ref(ref)
        for m in final["methods"]:
            if args.only and m["name"] not in args.only:
                continue
            try:
                r = run_counts(cfg, m, ds, sp, proto, n_jobs, limit=args.limit, force=args.force)
            except (RuntimeError, FileNotFoundError) as e:
                print(f"  [skip] {m['name']} on {ref}: {e}")
                continue
            rows.append(summary_row(r, ds, sp))
    out = C.results_dir(cfg, "test")
    write_csv(rows, out / "summary.csv")
    if args.legacy_check:
        lp = C.protocol_of(cfg, cfg["legacy_protocol"])
        legacy = [dict(name="GWi_k5l4_legacy", family="gwi", k=5, lam=4, N=8,
                       sigma_ratio=0.56, gamma=0.5),
                  dict(name="GWiODPS_k5l4_legacy", family="gwi", k=5, lam=4, N=8,
                       sigma_ratio=0.56, gamma=0.5, nms=dict(d=2, mode="nearest")),
                  dict(name="GWCraw_k5l4_legacy", family="gwc", k=5, lam=4, N=8,
                       sigma_ratio=0.56, gamma=0.5, dc="raw")]
        lrows = []
        for ref in final["test_sets"]:
            ds, sp = split_ref(ref)
            for m in legacy:
                r = run_counts(cfg, m, ds, sp, lp, n_jobs, limit=args.limit, force=args.force)
                lrows.append(summary_row(r, ds, sp))
        write_csv(lrows, out / "legacy_check.csv")
        for r in lrows:
            # the submitted tables used the legacy OIS/AP definitions
            print(f"    {r['dataset']:8s} {r['method']:22s} ODS {r['ODS']:.4f}  "
                  f"OIS_legacy {r['OIS_legacy']:.4f}  AP_legacy {r['AP_legacy']:.4f}")


if __name__ == "__main__":
    main()
