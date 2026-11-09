"""Paired statistics over images.

The pipelines are deterministic (no training, no random initialization), so
repeated runs give identical maps. Variability is therefore estimated over
images:

    bootstrap_delta : paired bootstrap of Delta ODS (resample images with
                      replacement, recompute ODS of each method from summed
                      counts, take the difference). Percentile CIs.
    wilcoxon        : signed-rank test on per-image F at each method's dataset
                      ODS threshold; effect size = matched-pairs rank-biserial r.
    holm            : Holm step-down adjustment over a family of p-values.
    variability     : per method, bootstrap 95% CI of ODS, OIS and AP over images
                      (OIS/AP by dataset-level accumulation, and the submitted
                      definitions as *_legacy),
                      and the spread of per-image F at the dataset ODS threshold
                      (Reviewer 2, point 11).
"""
from __future__ import annotations

from typing import Dict, List

import numpy as np
from scipy.stats import wilcoxon as _wilcoxon

from .evaluate import _prf, aggregate, ods_of, per_image_f


def _ods_from_sum(c):
    _, _, F = _prf(c)
    return F.max(axis=-1)


def bootstrap_delta(ca: np.ndarray, cb: np.ndarray, B: int = 2000,
                    seed: int = 0, ci=(0.95, 0.90)) -> Dict:
    """ca, cb: (n_images, T, 4) counts on the same images in the same order."""
    assert ca.shape[0] == cb.shape[0], "methods must share images"
    n = ca.shape[0]
    rng = np.random.default_rng(seed)
    oa, _ = ods_of(ca)
    ob, _ = ods_of(cb)
    deltas = np.empty(B)
    ca_f, cb_f = ca.astype(np.float64), cb.astype(np.float64)
    for b in range(B):
        w = np.bincount(rng.integers(0, n, n), minlength=n).astype(np.float64)
        sa = np.tensordot(w, ca_f, axes=(0, 0))
        sb = np.tensordot(w, cb_f, axes=(0, 0))
        deltas[b] = _ods_from_sum(sa) - _ods_from_sum(sb)
    out = dict(ods_a=oa, ods_b=ob, delta=oa - ob, B=B,
               p_boot_two_sided=float(min(1.0, 2 * min((deltas <= 0).mean(),
                                                         (deltas >= 0).mean()))))
    for c in ci:
        lo, hi = np.percentile(deltas, [100 * (1 - c) / 2, 100 * (1 + c) / 2])
        out[f"ci{int(c * 100)}"] = [float(lo), float(hi)]
    return out


def wilcoxon_paired(ca: np.ndarray, cb: np.ndarray) -> Dict:
    _, ia = ods_of(ca)
    _, ib = ods_of(cb)
    fa, fb = per_image_f(ca, ia), per_image_f(cb, ib)
    d = fa - fb
    nz = d[d != 0]
    if nz.size == 0:
        return dict(n=int(d.size), p=1.0, r_rb=0.0, median_diff=0.0,
                    mean_diff=0.0, frac_a_better=0.0)
    res = _wilcoxon(fa, fb, zero_method="wilcox", alternative="two-sided")
    ranks = np.argsort(np.argsort(np.abs(nz))) + 1.0
    w_pos, w_neg = ranks[nz > 0].sum(), ranks[nz < 0].sum()
    r_rb = float((w_pos - w_neg) / (w_pos + w_neg))
    return dict(n=int(d.size), p=float(res.pvalue), r_rb=r_rb,
                median_diff=float(np.median(d)), mean_diff=float(d.mean()),
                frac_a_better=float((d > 0).mean()))


def holm(pvals: List[float]) -> List[float]:
    m = len(pvals)
    order = np.argsort(pvals)
    adj = np.empty(m)
    running = 0.0
    for rank, i in enumerate(order):
        running = max(running, (m - rank) * pvals[i])
        adj[i] = min(1.0, running)
    return adj.tolist()


def superiority(ci95) -> str:
    lo, hi = ci95
    if lo > 0:
        return "a_better"
    if hi < 0:
        return "b_better"
    return "no_difference"


def claim_word(ci95) -> str:
    """Word allowed in the manuscript for 'A vs B' given the 95% CI."""
    return {"a_better": "improves", "b_better": "is lower than",
            "no_difference": "does not differ from (CI includes 0)"}[superiority(ci95)]


def variability(c: np.ndarray, thr: np.ndarray, B: int = 2000, seed: int = 0) -> Dict:
    """c: (n_images, T, 4) counts of one method. Resamples images with replacement."""
    n = c.shape[0]
    m = aggregate(c, thr)
    rng = np.random.default_rng(seed)
    keys = ("ods", "ois_legacy", "ap_legacy", "ois", "ap")
    bs = {k: np.empty(B) for k in keys}
    for b in range(B):
        a = aggregate(c[rng.integers(0, n, n)], thr)
        for k in bs:
            bs[k][b] = a[k]
    _, i_ods = ods_of(c)
    f = per_image_f(c, i_ods)
    out = dict(n=int(n), B=int(B))
    for k in keys:
        lo, hi = np.percentile(bs[k], [2.5, 97.5])
        out[k] = float(m[k])
        out[k + "_ci95"] = [float(lo), float(hi)]
    q1, med, q3 = np.percentile(f, [25, 50, 75])
    out.update(f_img_mean=float(f.mean()), f_img_sd=float(f.std(ddof=1)) if n > 1 else 0.0,
               f_img_median=float(med), f_img_iqr=[float(q1), float(q3)])
    return out
