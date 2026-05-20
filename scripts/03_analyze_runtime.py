"""
03_analyze_runtime.py
Author: Kukuh Yudhistiro, 2026

Aggregate per-image runtime measurements into paper-ready 
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd


def load_runtime(csv_path: Path) -> pd.DataFrame:
    """Load runtime CSV and keep only successful rows."""
    df = pd.read_csv(csv_path)
    df = df[df["status"] == "OK"].copy()
    df["filter_time_s"] = df["filter_time_s"].astype(float)
    df["preproc_time_s"] = df["preproc_time_s"].astype(float)
    df["total_time_s"] = df["total_time_s"].astype(float)
    df["filter_time_ms"] = df["filter_time_s"] * 1000
    return df


def aggregate_by_method_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Compute per-(dataset, method) statistics."""
    rows = []
    for (ds, method), group in df.groupby(["dataset", "method"]):
        ms = group["filter_time_ms"].values
        n = len(ms)
        mean = float(np.mean(ms))
        std = float(np.std(ms, ddof=1)) if n > 1 else 0.0
        median = float(np.median(ms))
        # 95% CI via t-distribution approximation (1.96 for n large enough)
        # For small n we use 2.0 as a conservative multiplier
        se = std / np.sqrt(n) if n > 1 else 0.0
        ci95 = 1.96 * se
        rows.append({
            "dataset": ds,
            "method": method,
            "n": n,
            "mean_ms": mean,
            "median_ms": median,
            "std_ms": std,
            "ci95_ms": ci95,
            "ci_lower": mean - ci95,
            "ci_upper": mean + ci95,
            "min_ms": float(np.min(ms)),
            "max_ms": float(np.max(ms)),
        })
    return pd.DataFrame(rows)


def compute_speedups(agg: pd.DataFrame, reference: str = "GWi") -> pd.DataFrame:
    """For each dataset, compute speedup of reference vs other methods.

    speedup = other_mean / reference_mean
    (so > 1 means reference is faster)
    """
    rows = []
    for ds, group in agg.groupby("dataset"):
        ref_row = group[group["method"] == reference]
        if ref_row.empty:
            continue
        ref_mean = ref_row.iloc[0]["mean_ms"]
        ref_std = ref_row.iloc[0]["std_ms"]
        ref_n = ref_row.iloc[0]["n"]
        for _, row in group.iterrows():
            if row["method"] == reference:
                continue
            speedup = row["mean_ms"] / ref_mean if ref_mean > 0 else float("nan")
            # Propagation of uncertainty for ratio:
            #   sigma_ratio / ratio = sqrt( (sigma_a/a)^2 + (sigma_b/b)^2 )
            if row["mean_ms"] > 0 and ref_mean > 0:
                rel_unc = np.sqrt(
                    (row["std_ms"] / row["mean_ms"]) ** 2
                    + (ref_std / ref_mean) ** 2
                )
                speedup_std = speedup * rel_unc
            else:
                speedup_std = float("nan")
            rows.append({
                "dataset": ds,
                "reference": reference,
                "compared_to": row["method"],
                "speedup": speedup,
                "speedup_std": speedup_std,
                "ref_mean_ms": ref_mean,
                "other_mean_ms": row["mean_ms"],
                "n": min(ref_n, row["n"]),
            })
    return pd.DataFrame(rows)


def aggregate_by_tertile(df: pd.DataFrame) -> pd.DataFrame:
    """Per-(dataset, method, tertile) breakdown."""
    rows = []
    for (ds, method, tertile), group in df.groupby(
            ["dataset", "method", "tertile_label"]):
        if pd.isna(tertile) or tertile == "":
            continue
        ms = group["filter_time_ms"].values
        n = len(ms)
        if n == 0:
            continue
        rows.append({
            "dataset": ds,
            "method": method,
            "tertile": tertile,
            "n": n,
            "mean_ms": float(np.mean(ms)),
            "median_ms": float(np.median(ms)),
            "std_ms": float(np.std(ms, ddof=1)) if n > 1 else 0.0,
        })
    return pd.DataFrame(rows)


def df_to_markdown(df: pd.DataFrame, float_cols: list,
                   float_fmt: str = "{:.3f}") -> str:
    """Render a DataFrame as a markdown table."""
    df = df.copy()
    for c in float_cols:
        if c in df.columns:
            df[c] = df[c].apply(
                lambda x: float_fmt.format(x) if pd.notna(x) else "-"
            )
    return df.to_markdown(index=False, tablefmt="github")


def print_table(title: str, df: pd.DataFrame, float_cols: list,
                float_fmt: str = "{:.3f}") -> None:
    print(f"\n### {title}\n")
    print(df_to_markdown(df, float_cols, float_fmt))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--runtime-csv", type=Path, required=True,
                        help="Per-image runtime log produced by 02_run_all_methods.py")
    parser.add_argument("--output-dir", type=Path, required=True,
                        help="Directory for aggregated tables")
    parser.add_argument("--reference-method", default="GWi",
                        help="Reference method for speedup computation (default: GWi)")
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[INFO] Loading runtime log: {args.runtime_csv}")
    df = load_runtime(args.runtime_csv)
    print(f"[INFO] Loaded {len(df)} successful records.")
    print(f"[INFO] Datasets : {sorted(df['dataset'].unique())}")
    print(f"[INFO] Methods  : {sorted(df['method'].unique())}")

    # ----- 1. Aggregate by (dataset, method) -----
    agg = aggregate_by_method_dataset(df)
    agg_path = args.output_dir / "runtime_per_method_dataset.csv"
    agg.to_csv(agg_path, index=False)
    print(f"\n[OK] Saved: {agg_path}")
    print_table("Per-method, per-dataset runtime (ms)",
                agg[["dataset", "method", "n",
                     "mean_ms", "std_ms", "ci95_ms", "median_ms"]],
                float_cols=["mean_ms", "std_ms", "ci95_ms", "median_ms"])

    # ----- 2. Speedup table -----
    speedup_df = compute_speedups(agg, reference=args.reference_method)
    speedup_path = args.output_dir / f"speedup_{args.reference_method}.csv"
    speedup_df.to_csv(speedup_path, index=False)
    print(f"\n[OK] Saved: {speedup_path}")
    print_table(f"Speedup: {args.reference_method} vs others (>1 means GWi faster)",
                speedup_df[["dataset", "compared_to", "speedup",
                            "speedup_std", "ref_mean_ms", "other_mean_ms"]],
                float_cols=["speedup", "speedup_std",
                            "ref_mean_ms", "other_mean_ms"])

    # ----- 3. Per-tertile breakdown -----
    tertile_df = aggregate_by_tertile(df)
    if not tertile_df.empty:
        tert_path = args.output_dir / "runtime_per_tertile.csv"
        tertile_df.to_csv(tert_path, index=False)
        print(f"\n[OK] Saved: {tert_path}")
        # Pivot for clearer display
        pivot = tertile_df.pivot_table(
            index=["dataset", "method"],
            columns="tertile",
            values="mean_ms",
        ).reset_index()
        print_table("Mean runtime (ms) per density tertile",
                    pivot, float_cols=["LOW", "MID", "HIGH"])

    # ----- 4. Summary JSON -----
    summary = {
        "n_records": int(len(df)),
        "datasets": sorted(df["dataset"].unique().tolist()),
        "methods": sorted(df["method"].unique().tolist()),
        "reference_method": args.reference_method,
        "outputs": {
            "per_method_dataset": str(agg_path),
            "speedup": str(speedup_path),
        },
    }
    summary_path = args.output_dir / "runtime_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[OK] Saved: {summary_path}")
    print("\n[DONE] Runtime analysis complete.")


if __name__ == "__main__":
    main()
