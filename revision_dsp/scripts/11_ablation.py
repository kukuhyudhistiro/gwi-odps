"""Sensitivity analyses on BSDS500 train+val, reported only.

A  lambda x d at the selected k (R2.5: effect of d; R3.2: vary lambda and check
   whether d = lambda/2 suppresses the artifact). d in ablation.lam_d.d plus
   d = lambda/2 for every lambda. GWi without ODPS is included for each lambda,
   so the gain of ODPS is visible per row.
B  one factor at a time around the selected configuration (d = lambda/2):
   N (R2.6, R3.4), sigma/lambda and gamma (R3.4).

Every row carries the analytic multiply-accumulate count per pixel (N k^2);
ODPS adds two comparisons per pixel whatever d is. Measured ODPS time per d is
in scripts/24_runtime.py (odps_d.csv).

None of these results changes the selected configuration.

Outputs (results/ablation/): lam_d.csv, one_at_a_time.csv
"""
from __future__ import annotations

from _common import load_json, parser, setup, split_ref
from rev import cfg as C
from rev.runner import run_counts, summary_row, write_csv
from rev.specs import gabor_specs


def mac(spec):
    return int(spec["N"]) * int(spec["k"]) ** 2


def main():
    args = parser(__doc__).parse_args()
    cfg, n_jobs = setup(args)
    proto = C.protocol_of(cfg)
    A = cfg["ablation"]
    ds, sp = split_ref(A["split"])
    sel = load_json(C.results_dir(cfg, "selection") / "selected.json")
    base = dict(k=sel["k"], lam=sel["lam"], N=sel["N"], sigma_ratio=sel["sigma_ratio"],
                gamma=sel["gamma"])
    out = C.results_dir(cfg, "ablation")

    def run(spec, **extra):
        r = run_counts(cfg, spec, ds, sp, proto, n_jobs, limit=args.limit, force=args.force)
        row = summary_row(r, ds, sp)
        row.update(mac=mac(spec), **extra)
        return row

    # A: lambda x d
    rowsA = []
    for lam in A["lam_d"]["lam"]:
        kc = dict(base, lam=lam)
        gwi = gabor_specs(kc, lam / 2)[0]
        rowsA.append(run(gwi, k=base["k"], lam=lam, d="none (GWi)", d_is_half_lambda=""))
        ds_list = sorted(set(float(d) for d in A["lam_d"]["d"]) | {lam / 2.0})
        for d in ds_list:
            s = gabor_specs(kc, d)[1]
            s["name"] = f"{s['name']}_d{d:g}"
            rowsA.append(run(s, k=base["k"], lam=lam, d=d, d_is_half_lambda=(d == lam / 2.0)))
    write_csv(rowsA, out / "lam_d.csv")

    # B: one factor at a time
    O = A["one_at_a_time"]
    d0 = float(sel["d"])
    variants = [("selected", base)]
    for N in O.get("N", []):
        variants.append((f"N={N}", dict(base, N=N)))
    for sr in O.get("sigma_ratio", []):
        variants.append((f"sigma/lambda={sr}", dict(base, sigma_ratio=sr)))
    for gm in O.get("gamma", []):
        variants.append((f"gamma={gm}", dict(base, gamma=gm)))
    rowsB = []
    for label, kc in variants:
        gwi, gwi_odps = gabor_specs(kc, d0)[:2]
        for s, m in ((gwi, "GWi"), (gwi_odps, "GWi+ODPS")):
            s = dict(s, name=f"{s['name']}_{label.replace('/', '').replace('=', '')}")
            rowsB.append(run(s, variant=label, pipeline=m))
    write_csv(rowsB, out / "one_at_a_time.csv")


if __name__ == "__main__":
    main()
