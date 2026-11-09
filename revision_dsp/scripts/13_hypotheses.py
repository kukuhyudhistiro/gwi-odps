"""Evaluate the hypotheses of HYPOTHESES.md (H1: ODPS gain vs rho; H2: GWi vs rho and scale).

Written and committed before the 18-candidate selection results existed (tag
hyp-dsp-2026-11-09). Reads results/selection/kernel_ablation.csv (E10) and does
not run any image computation. Descriptive mechanism analysis on non-test splits
(R2.2, R3.1b, R3.2, R3.4); outside the Holm family of E22.

Outputs (results/hypotheses/): per_candidate.csv, hypotheses.json, hypotheses.md
"""
from __future__ import annotations

import csv
from fractions import Fraction
from statistics import median

from _common import dump, parser, setup
from rev import cfg as C
from rev.runner import write_csv

SPLITS = ["BSDS500:trainval", "BIPED:train"]
SEEN_H2B = {("k7l3", "k9l4"), ("k5l4", "k7l6")}   # orderings seen before writing


def rho_of(k: int, lam: float) -> Fraction:
    return Fraction(k // 2) / Fraction(lam).limit_denominator(100)


def tag(k, lam) -> str:
    lam = float(lam)
    return f"k{k}l{int(lam) if lam.is_integer() else lam}"


def load(path):
    """{split: {tag: dict(k, lam, rho, gwi, odps)}} from kernel_ablation.csv."""
    out = {s: {} for s in SPLITS}
    with open(path, encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            s = f"{r['dataset']}:{r['split']}"
            if s not in out:
                continue
            k, lam = int(r["k"]), float(r["lam"])
            t = tag(k, lam)
            e = out[s].setdefault(t, dict(tag=t, k=k, lam=lam, rho=rho_of(k, lam)))
            key = "odps" if r["method"].startswith("GWiODPS_") else "gwi"
            e[key] = float(r["ODS"])
    for s in out:
        for e in out[s].values():
            if "gwi" in e and "odps" in e:
                e["delta"] = e["odps"] - e["gwi"]
    return out


def spearman_greater(x, y):
    from scipy.stats import spearmanr
    res = spearmanr(x, y, alternative="greater")
    return float(res.statistic), float(res.pvalue)


def h1(d):
    """d: {tag: entry} for one split, entries with delta."""
    E = [e for e in d.values() if "delta" in e]
    out = dict(n=len(E))
    if len(E) < 18:
        out["note"] = f"only {len(E)} of 18 candidates available: not evaluated"
        return out
    rho = [float(e["rho"]) for e in E]
    dl = [e["delta"] for e in E]
    rs, p = spearman_greater(rho, dl)
    lo = [e["delta"] for e in E if e["rho"] < Fraction(1, 2)]
    eq = [e["delta"] for e in E if e["rho"] == Fraction(1, 2)]
    hi = [e["delta"] for e in E if e["rho"] > Fraction(1, 2)]
    out.update(
        H1a=dict(spearman_rs=round(rs, 4), p_one_sided=round(p, 5), supported=bool(rs > 0 and p < 0.05)),
        H1b=dict(median_lt=round(median(lo), 4), median_eq=round(median(eq), 4),
                 median_gt=round(median(hi), 4), n_lt=len(lo), n_eq=len(eq), n_gt=len(hi),
                 supported=bool(median(lo) < median(eq) < median(hi))),
        H1c=dict(max_delta_lt=round(max(lo), 4), min_delta_gt=round(min(hi), 4),
                 supported=bool(max(lo) < min(hi))),
        Q1=dict(n_lt_positive=sum(x > 0 for x in lo), n_lt_zero=sum(x == 0 for x in lo),
                n_lt_negative=sum(x < 0 for x in lo), deltas_lt=[round(x, 4) for x in lo]),
    )
    out["H1_split_supported"] = out["H1a"]["supported"] and out["H1b"]["supported"]
    return out


def h2a(d):
    big = [e for e in d.values() if "gwi" in e and e["rho"] >= Fraction(2, 3)]
    mid = [e for e in d.values() if "gwi" in e and Fraction(1, 2) <= e["rho"] <= Fraction(3, 5)]
    if len(big) < 7 or len(mid) < 5:
        return dict(note=f"only {len(big)}/7 and {len(mid)}/5 candidates available: not evaluated")
    mb, mm = max(e["gwi"] for e in big), min(e["gwi"] for e in mid)
    return dict(max_gwi_rho_ge_0667=mb, argmax=max(big, key=lambda e: e["gwi"])["tag"],
                min_gwi_rho_05_06=mm, argmin=min(mid, key=lambda e: e["gwi"])["tag"],
                supported=bool(mb < mm))


def h2b(d):
    pairs = [("k7l3", "k9l4"), ("k5l3", "k9l6"), ("k5l4", "k7l6"), ("k7l6", "k9l8")]
    rows, ok = [], True
    for a, b in pairs:
        if a not in d or b not in d or "gwi" not in d[a] or "gwi" not in d[b]:
            return dict(note=f"{a} or {b} missing: not evaluated")
        holds = d[a]["gwi"] < d[b]["gwi"]
        ok &= holds
        rows.append(dict(smaller_k=a, larger_k=b, ods_a=d[a]["gwi"], ods_b=d[b]["gwi"],
                         holds=bool(holds), seen_before=(a, b) in SEEN_H2B))
    return dict(orderings=rows, supported=bool(ok))


def h2c(bsds, biped):
    rows, ok = [], True
    for k in (5, 7, 9):
        a = [e for e in bsds.values() if e["k"] == k and "gwi" in e]
        b = [e for e in biped.values() if e["k"] == k and "gwi" in e]
        if len(a) < 6 or len(b) < 6:
            return dict(note=f"k={k}: not all six lambdas available: not evaluated")
        la, lb = max(a, key=lambda e: e["gwi"])["lam"], max(b, key=lambda e: e["gwi"])["lam"]
        ok &= lb <= la
        rows.append(dict(k=k, best_lam_bsds=la, best_lam_biped=lb, holds=bool(lb <= la)))
    return dict(per_k=rows, supported=bool(ok))


def q2(d):
    rows = []
    for k in (5, 7, 9):
        a = [e for e in d.values() if e["k"] == k and "gwi" in e]
        if not a:
            continue
        best = max(a, key=lambda e: e["gwi"])
        rows.append(dict(k=k, best_lam=best["lam"], at_upper_edge=best["lam"] == max(e["lam"] for e in a)))
    return rows


def main():
    args = parser(__doc__).parse_args()
    cfg, _ = setup(args)
    src = C.results_dir(cfg, "selection") / "kernel_ablation.csv"
    out = C.results_dir(cfg, "hypotheses")
    data = load(src)
    per = []
    for s in SPLITS:
        for e in sorted(data[s].values(), key=lambda e: (-e["rho"], e["k"])):
            per.append(dict(split=s, tag=e["tag"], k=e["k"], lam=e["lam"], rho=round(float(e["rho"]), 3),
                            ods_gwi=e.get("gwi"), ods_gwi_odps=e.get("odps"),
                            delta=round(e["delta"], 4) if "delta" in e else None))
    write_csv(per, out / "per_candidate.csv")

    res = dict(source=str(src), H1={s: h1(data[s]) for s in SPLITS},
               H2a={s: h2a(data[s]) for s in SPLITS},
               H2b=h2b(data["BSDS500:trainval"]),
               H2c=h2c(data["BSDS500:trainval"], data["BIPED:train"]),
               Q2={s: q2(data[s]) for s in SPLITS})
    h1s = [res["H1"][s].get("H1_split_supported") for s in SPLITS]
    res["H1_verdict"] = ("not evaluated" if None in h1s else
                         "supported" if all(h1s) else "partial" if any(h1s) else "not supported")
    dump(res, out / "hypotheses.json")

    def v(x):
        return x.get("supported", x.get("note", "?")) if isinstance(x, dict) else x

    lines = ["# Hypothesis results (scripts/13_hypotheses.py)", "",
             f"Source: `{src.name}`. Pre-registered in HYPOTHESES.md (tag hyp-dsp-2026-11-09).", "",
             "| Hypothesis | BSDS500 train+val | BIPED train |", "|---|---|---|"]
    for h in ("H1a", "H1b", "H1c"):
        lines.append(f"| {h} | " + " | ".join(str(v(res['H1'][s].get(h, res['H1'][s]))) for s in SPLITS) + " |")
    lines.append(f"| H2a | " + " | ".join(str(v(res['H2a'][s])) for s in SPLITS) + " |")
    lines.append(f"| H2b | {v(res['H2b'])} | (no prediction) |")
    lines.append(f"| H2c | {v(res['H2c'])} (both splits) | |")
    lines += ["", f"**H1 verdict:** {res['H1_verdict']}", ""]
    (out / "hypotheses.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"  -> {out / 'hypotheses.md'}")


if __name__ == "__main__":
    main()
