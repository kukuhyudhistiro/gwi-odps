"""Boundary evaluation (Berkeley-style), vectorized.

Per image and threshold t:
    pred = thin(map >= t)                       (skimage.morphology.thin)
    for each annotator a: gt_a = thin(GT_a)
        one-to-one matching pred <-> gt_a within max_dist = frac * diagonal
    cntP = #pred pixels matched to at least one annotator,   sumP = #pred
    cntR = sum_a #gt_a pixels matched,                        sumR = sum_a #gt_a
These counts are identical in definition to scripts/04c_evaluate_bsds_v2.py.

Matching
    greedy  : edges processed by ascending distance in the same order as 04c
              (np.argsort over candidates listed by pred index, then GT index);
              implemented as repeated locally-dominant-edge rounds, which give
              the same matching as 04c's sequential greedy pass.
    maxcard : maximum-cardinality bipartite matching within max_dist
              (scipy.sparse.csgraph), for calibration only.

Aggregation (both reported)
    bsds    : ODS from summed counts; OIS from counts summed at each image's best
              threshold; AP = area of the dataset PR curve sampled at recall
              0:0.01:1 by linear interpolation (BSDS benchmark convention).
    legacy  : as 04c: OIS = mean of per-image best F; AP = mean of per-image
              trapezoid areas.
"""
from __future__ import annotations

from typing import List

import numpy as np

_trapz = getattr(np, "trapezoid", None) or np.trapz
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import maximum_bipartite_matching
from scipy.spatial import cKDTree
from skimage.morphology import thin as _sk_thin

try:  # same lookup tables as skimage.morphology.thin (Guo-Hall, 2 subiterations)
    from skimage.morphology._skeletonize import G123_LUT, G123P_LUT
    import cv2
    _MASK = np.array([[8, 4, 2], [16, 0, 1], [32, 64, 128]], dtype=np.float32)
    _HAVE_FAST_THIN = True
except Exception:  # pragma: no cover
    _HAVE_FAST_THIN = False

EPS = 1e-10


def sk_thin(image: np.ndarray) -> np.ndarray:
    """skimage.morphology.thin with the neighbourhood correlation done by
    cv2.filter2D (exact integer sums, zero border). Output is identical to
    skimage's (checked in scripts/01_selftest.py)."""
    if not _HAVE_FAST_THIN:
        return _sk_thin(image)
    skel = np.asarray(image, dtype=bool).astype(np.uint8)
    n_old, n_new = -1, int(skel.sum())
    while n_old != n_new:
        n_old = n_new
        for lut in (G123_LUT, G123P_LUT):
            N = cv2.filter2D(skel, cv2.CV_16S, _MASK, borderType=cv2.BORDER_CONSTANT)
            D = np.take(lut, N.astype(np.intp))
            skel[D] = 0
        n_new = int(skel.sum())
    return skel.astype(bool)


def thresholds(n: int) -> np.ndarray:
    return np.linspace(1.0 / (n + 1), 1.0 - 1.0 / (n + 1), n)


def _greedy(pi, gj, dist, n_pred, n_gt, want_dist=False):
    if pi.size == 0:
        return (np.zeros(n_pred, bool), 0, np.array([])) if want_dist else \
            (np.zeros(n_pred, bool), 0)
    # Edge order of 04c: candidates listed by pred index, then GT index (KD-tree
    # multi-point queries return sorted indices), then np.argsort on the cost
    # list (default kind). The locally-dominant-edge rounds below give the same
    # matching as 04c's sequential greedy pass for this order.
    o0 = np.lexsort((gj, pi))
    pi, gj, dist = pi[o0], gj[o0], dist[o0]
    order = np.argsort(dist)
    pi, gj, dist = pi[order], gj[order], dist[order]
    pm = np.zeros(n_pred, bool)
    gm = np.zeros(n_gt, bool)
    alive = np.arange(pi.size)
    md = []
    while alive.size:
        p, g = pi[alive], gj[alive]
        _, fp = np.unique(p, return_index=True)
        _, fg = np.unique(g, return_index=True)
        bp = np.zeros(alive.size, bool)
        bp[fp] = True
        bg = np.zeros(alive.size, bool)
        bg[fg] = True
        mutual = bp & bg
        pm[p[mutual]] = True
        gm[g[mutual]] = True
        if want_dist:
            md.append(dist[alive[mutual]])
        alive = alive[~(pm[p] | gm[g])]
    if want_dist:
        return pm, int(gm.sum()), (np.concatenate(md) if md else np.array([]))
    return pm, int(gm.sum())


def _maxcard(pi, gj, n_pred, n_gt):
    if pi.size == 0:
        return np.zeros(n_pred, bool), 0
    A = csr_matrix((np.ones(pi.size, np.int8), (pi, gj)), shape=(n_pred, n_gt))
    m = maximum_bipartite_matching(A, perm_type="column")
    pm = m >= 0
    return pm, int(pm.sum())


class GTCache:
    def __init__(self, gts: List[np.ndarray]):
        self.pts, self.trees = [], []
        self.total = 0
        for g in gts:
            p = np.argwhere(sk_thin(g))
            self.pts.append(p)
            self.trees.append(cKDTree(p) if len(p) else None)
            self.total += len(p)


def counts_at(binary: np.ndarray, gtc: GTCache, max_dist: float,
              matching: str = "greedy", return_dist: bool = False):
    pts = np.argwhere(sk_thin(binary))
    n_pred = len(pts)
    if n_pred == 0:
        return (0, gtc.total, 0, 0) if not return_dist else ((0, gtc.total, 0, 0), np.array([]))
    tree_p = cKDTree(pts)
    any_m = np.zeros(n_pred, bool)
    cnt_r = 0
    dists = []
    for gp, tg in zip(gtc.pts, gtc.trees):
        if tg is None:
            continue
        sdm = tree_p.sparse_distance_matrix(tg, max_dist, output_type="ndarray")
        pi = sdm["i"].astype(np.int64)
        gj = sdm["j"].astype(np.int64)
        dd = sdm["v"]
        if matching == "greedy" and return_dist:
            pm, ng, md = _greedy(pi, gj, dd, n_pred, len(gp), want_dist=True)
            dists.append(md)
        elif matching == "greedy":
            pm, ng = _greedy(pi, gj, dd, n_pred, len(gp))
        elif matching == "maxcard":
            pm, ng = _maxcard(pi, gj, n_pred, len(gp))
        else:
            raise ValueError(matching)
        any_m |= pm
        cnt_r += ng
    c = (int(cnt_r), int(gtc.total), int(any_m.sum()), int(n_pred))
    if return_dist:
        return c, (np.concatenate(dists) if dists else np.array([]))
    return c


def image_counts(pred: np.ndarray, gts: List[np.ndarray], thr: np.ndarray,
                 max_dist_frac: float = 0.0075, matching: str = "greedy") -> np.ndarray:
    h, w = pred.shape
    max_dist = max_dist_frac * float(np.hypot(h, w))
    gtc = GTCache(gts)
    out = np.zeros((len(thr), 4), np.int64)
    pmax = float(pred.max())
    for i, t in enumerate(thr):
        if t > pmax:
            out[i] = (0, gtc.total, 0, 0)
            continue
        out[i] = counts_at(pred >= t, gtc, max_dist, matching)
    return out


def _prf(c):
    p = c[..., 2] / np.maximum(c[..., 3], EPS)
    r = c[..., 0] / np.maximum(c[..., 1], EPS)
    f = 2 * p * r / np.maximum(p + r, EPS)
    return p, r, f


def aggregate(counts: np.ndarray, thr: np.ndarray) -> dict:
    """counts: (n_images, T, 4). Returns BSDS-style and legacy metrics."""
    tot = counts.sum(axis=0).astype(np.float64)
    P, R, F = _prf(tot)
    i = int(np.argmax(F))
    per = counts.astype(np.float64)
    p_i, r_i, f_i = _prf(per)
    best = np.argmax(f_i, axis=1)
    ois_c = per[np.arange(len(per)), best].sum(axis=0)
    op, orr, of = _prf(ois_c)
    # AP, BSDS benchmark code convention (101 recall points, NaN outside the curve)
    o = np.argsort(R)
    Rs, Ps = R[o], P[o]
    Ru, ui = np.unique(Rs, return_index=True)
    grid = np.linspace(0, 1, 101)
    Pi = np.interp(grid, Ru, Ps[ui], left=np.nan, right=np.nan)
    ap_bsds101 = float(np.nansum(Pi) * 0.01)
    # AP, primary since 9 Nov 2026 (CHANGELOG.md): area under the dataset-level PR
    # curve with precision made monotone, the definition of the A-GWi paper
    # (JESA 44740, evaluate_v2.interpolated_ap), so that both papers use one AP.
    p_env = np.maximum.accumulate(Ps[::-1])[::-1]
    ap_mono = float(np.sum(np.diff(np.concatenate(([0.0], Rs))) * p_env))
    # legacy
    ap_leg = float(np.mean([_trapz(p_i[k][np.argsort(r_i[k])],
                                         r_i[k][np.argsort(r_i[k])])
                            for k in range(len(per))]))
    # ois / ap: dataset-level accumulation (primary). ois_legacy / ap_legacy: the
    # definitions of the submitted tables (mean of per-image values), kept for continuity.
    return dict(ods=float(F[i]), ods_p=float(P[i]), ods_r=float(R[i]),
                ods_t=float(thr[i]), ois=float(of), ap=ap_mono, ap_bsds101=ap_bsds101,
                ois_legacy=float(np.mean(f_i[np.arange(len(per)), best])),
                ap_legacy=ap_leg, n_images=int(len(per)),
                P=P.tolist(), R=R.tolist(), F=F.tolist())


def per_image_f(counts: np.ndarray, t_index: int) -> np.ndarray:
    _, _, f = _prf(counts[:, t_index, :].astype(np.float64))
    return f


def ods_of(counts: np.ndarray) -> tuple:
    _, _, F = _prf(counts.sum(axis=0).astype(np.float64))
    i = int(np.argmax(F))
    return float(F[i]), i
