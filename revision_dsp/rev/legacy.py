"""
legacy.py: verbatim copies of functions from repo kukuhyudhistiro/gwi-odps
(commit 91b4f83, 16 Jun 2026) used to produce Tables 1-9 of DSP-D-26-02462.

Kept ONLY for equivalence tests (scripts/01_selftest.py, T0 checks that this copy
still equals ../src when run inside the repo). Do not use for new results.
Sources: src/gabor_core.py, src/nms_odps.py, scripts/04c_evaluate_bsds_v2.py
"""
from __future__ import annotations
import time
from dataclasses import dataclass
from typing import List, Tuple
import cv2
import numpy as np

_trapz = getattr(np, "trapezoid", None) or np.trapz
from scipy.spatial import KDTree as cKDTree
from skimage.morphology import thin as sk_thin



@dataclass(frozen=True)
class GaborParams:
    """Immutable parameter container for Gabor wavelet pipeline."""

    ksize: int = 5
    wavelength: float = 4.0
    gamma: float = 0.5
    psi_deg: float = 0.0
    n_orientations: int = 8

    @property
    def sigma(self) -> float:
        """sigma = 0.56 * wavelength (Kruizinga & Petkov 1999 rule)."""
        return 0.56 * self.wavelength

    @property
    def orientations_deg(self) -> List[float]:
        """8 orientations at 22.5 degree spacing: 0, 22.5, ..., 157.5."""
        return [i * (180.0 / self.n_orientations)
                for i in range(self.n_orientations)]


def _gabor_grids(ksize: int, theta_rad: float):
    """Pre-compute rotated coordinate grids for a kernel.

    Returns:
        x_t, y_t : rotated coordinate grids (size ksize x ksize)
    """
    half = ksize // 2
    x, y = np.meshgrid(np.arange(-half, half + 1),
                       np.arange(-half, half + 1))
    cos_t, sin_t = np.cos(theta_rad), np.sin(theta_rad)
    x_t = x * cos_t + y * sin_t
    y_t = -x * sin_t + y * cos_t
    return x_t, y_t


def make_gabor_complex_pair(params: GaborParams,
                            theta_deg: float) -> Tuple[np.ndarray, np.ndarray]:
    """Generate (real, imaginary) Gabor kernel pair for one orientation.

    Both kernels share the same Gaussian envelope. Real = cos(...), Imag = sin(...).

    Returns:
        kr : real component kernel  (ksize x ksize, float64)
        ki : imag component kernel  (ksize x ksize, float64)
    """
    ksize = params.ksize if params.ksize % 2 == 1 else params.ksize + 1
    theta = np.deg2rad(theta_deg)
    psi = np.deg2rad(params.psi_deg)

    x_t, y_t = _gabor_grids(ksize, theta)
    gauss = np.exp(-0.5 * (x_t ** 2 + (params.gamma ** 2) * y_t ** 2)
                   / (params.sigma ** 2))
    sinusoid_arg = 2.0 * np.pi * x_t / params.wavelength + psi

    kr = (gauss * np.cos(sinusoid_arg)).astype(np.float64)
    ki = (gauss * np.sin(sinusoid_arg)).astype(np.float64)
    return kr, ki


def make_gabor_imaginary(params: GaborParams,
                         theta_deg: float) -> np.ndarray:
    """Generate imaginary-only Gabor kernel for one orientation."""
    ksize = params.ksize if params.ksize % 2 == 1 else params.ksize + 1
    theta = np.deg2rad(theta_deg)
    psi = np.deg2rad(params.psi_deg)

    x_t, y_t = _gabor_grids(ksize, theta)
    gauss = np.exp(-0.5 * (x_t ** 2 + (params.gamma ** 2) * y_t ** 2)
                   / (params.sigma ** 2))
    return (gauss * np.sin(2.0 * np.pi * x_t / params.wavelength + psi)
            ).astype(np.float64)


class GWCFilterBank:
    """Pre-computed GWC filter bank for fast per-image inference.

    Building the kernels is cheap (8 * 2 = 16 kernels of size 7x7), but doing
    it inside an inner loop over 280 images wastes time and obscures runtime
    measurements. Build once, apply many times.
    """

    def __init__(self, params: GaborParams = GaborParams()):
        self.params = params
        self.kernels_real: List[np.ndarray] = []
        self.kernels_imag: List[np.ndarray] = []
        for theta in params.orientations_deg:
            kr, ki = make_gabor_complex_pair(params, theta)
            self.kernels_real.append(kr)
            self.kernels_imag.append(ki)


class GWiFilterBank:
    """Pre-computed GWi filter bank (imaginary-only)."""

    def __init__(self, params: GaborParams = GaborParams()):
        self.params = params
        self.kernels: List[np.ndarray] = []
        for theta in params.orientations_deg:
            self.kernels.append(make_gabor_imaginary(params, theta))


@dataclass
class GaborResult:
    """Output of a single Gabor inference run."""

    magnitude: np.ndarray   # combined max-over-orientations magnitude
    runtime_s: float        # wall-clock seconds (convolution + max only)
    per_orient: List[np.ndarray]  # per-orientation magnitudes (for analysis)


def run_gwc(image_norm: np.ndarray, bank: GWCFilterBank) -> GaborResult:
    """Run GWC pipeline on a normalized [0,1] grayscale image.

    For each orientation:
        m_theta = sqrt( (I * kr)^2 + (I * ki)^2 )
    Combined response: M(x,y) = max_theta m_theta(x,y).

    Returns raw magnitude WITHOUT thresholding.
    """
    t0 = time.perf_counter()
    mags: List[np.ndarray] = []
    for kr, ki in zip(bank.kernels_real, bank.kernels_imag):
        resp_r = cv2.filter2D(image_norm, cv2.CV_64F, kr,
                              borderType=cv2.BORDER_CONSTANT)
        resp_i = cv2.filter2D(image_norm, cv2.CV_64F, ki,
                              borderType=cv2.BORDER_CONSTANT)
        mags.append(np.sqrt(resp_r ** 2 + resp_i ** 2))
    combined = np.max(np.stack(mags, axis=0), axis=0)
    runtime = time.perf_counter() - t0
    return GaborResult(magnitude=combined, runtime_s=runtime, per_orient=mags)


def run_gwi(image_norm: np.ndarray, bank: GWiFilterBank) -> GaborResult:
    """Run GWi pipeline on a normalized [0,1] grayscale image.

    For each orientation:
        m_theta = |I * ki|
    Combined response: M(x,y) = max_theta m_theta(x,y).

    Returns raw magnitude WITHOUT thresholding.
    """
    t0 = time.perf_counter()
    mags: List[np.ndarray] = []
    for ki in bank.kernels:
        resp = cv2.filter2D(image_norm, cv2.CV_64F, ki,
                            borderType=cv2.BORDER_CONSTANT)
        mags.append(np.abs(resp))
    combined = np.max(np.stack(mags, axis=0), axis=0)
    runtime = time.perf_counter() - t0
    return GaborResult(magnitude=combined, runtime_s=runtime, per_orient=mags)


def compute_normal_offsets(orientation_idx: np.ndarray,
                           n_orientations: int = 8,
                           d: int = 2) -> tuple:
    """Compute per-pixel offsets to neighbors along edge-normal direction.

    Args:
        orientation_idx : (H, W) int — argmax orientation index from Stage 5,
                          values in [0, n_orientations - 1].
                          Orientation k corresponds to angle k*(180/n_orient)°,
                          which is the FILTER orientation.
                          The edge-normal is perpendicular to the filter,
                          i.e. at angle (k * 180/n_orient) + 90°.
        n_orientations  : number of orientations (default 8 → 22.5° spacing)
        d               : distance in pixels along normal to check (default 2)

    Returns:
        dy_pos, dx_pos : (H, W) int arrays — offsets to +normal neighbor
        dy_neg, dx_neg : (H, W) int arrays — offsets to -normal neighbor
    """
    angle_step = 180.0 / n_orientations
    # In this pipeline, θ is the EDGE-NORMAL direction
    # (verified empirically: a vertical edge produces max response at θ=0°,
    # meaning the filter detecting vertical edges has θ aligned with
    # the horizontal edge-normal direction).
    # We compare neighbors directly along θ (NOT θ+90°).
    theta_deg = orientation_idx.astype(np.float32) * angle_step
    normal_rad = np.deg2rad(theta_deg)

    # Vector along normal direction, scaled by d, rounded to integer offsets
    dx_pos = np.round(np.cos(normal_rad) * d).astype(np.int32)
    dy_pos = np.round(np.sin(normal_rad) * d).astype(np.int32)
    dx_neg = -dx_pos
    dy_neg = -dy_pos

    return dy_pos, dx_pos, dy_neg, dx_neg


def odps(magnitude: np.ndarray,
         orientation_idx: np.ndarray,
         n_orientations: int = 8,
         d: int = 2,
         keep_equal: bool = True) -> np.ndarray:
    """Orientation-aware Double-Peak Suppression.

    For each pixel (y, x) in the magnitude map, compare its value against
    two neighbors along the edge-normal direction (perpendicular to the
    dominant orientation found in Stage 5). If the pixel is not a local
    maximum along that direction, set its magnitude to zero.

    Args:
        magnitude       : (H, W) float — Stage 5 max-pooled magnitude
        orientation_idx : (H, W) int — argmax orientation index
        n_orientations  : number of orientations
        d               : distance in pixels for neighbor comparison
        keep_equal      : if True, "tie" pixels are kept (>=). if False, only
                          strict maxima are kept (>).

    Returns:
        suppressed : (H, W) float — magnitude with non-maxima zeroed out

    Note:
        This is a vectorized implementation using padding and indexing,
        avoiding explicit Python loops over pixels. Should run ~3-5 ms on
        a typical BSDS500 image (321×481).
    """
    if magnitude.shape != orientation_idx.shape:
        raise ValueError(
            f"Shape mismatch: magnitude {magnitude.shape}, "
            f"orientation {orientation_idx.shape}"
        )

    h, w = magnitude.shape
    mag = magnitude.astype(np.float32)

    # Compute per-pixel neighbor offsets
    dy_pos, dx_pos, dy_neg, dx_neg = compute_normal_offsets(
        orientation_idx, n_orientations, d
    )

    # Pad magnitude with zeros (out-of-bounds neighbors treat as 0)
    pad = d + 1
    mag_padded = np.pad(mag, pad, mode="constant", constant_values=0)

    # Compute coordinate grids
    yy, xx = np.meshgrid(np.arange(h), np.arange(w), indexing="ij")

    # Index into padded magnitude for + normal neighbor
    y_pos = yy + dy_pos + pad
    x_pos = xx + dx_pos + pad
    neighbor_pos = mag_padded[y_pos, x_pos]

    # Index into padded magnitude for - normal neighbor
    y_neg = yy + dy_neg + pad
    x_neg = xx + dx_neg + pad
    neighbor_neg = mag_padded[y_neg, x_neg]

    # Keep pixel if it's a local maximum along normal direction
    if keep_equal:
        is_max = (mag >= neighbor_pos) & (mag >= neighbor_neg)
    else:
        is_max = (mag > neighbor_pos) & (mag > neighbor_neg)

    suppressed = np.where(is_max, mag, 0.0).astype(np.float32)
    return suppressed


def match_single_annotator(pred_pts: np.ndarray, gt_pts: np.ndarray,
                            tree_gt, max_dist_px: float
                            ) -> Tuple[np.ndarray, int]:
    """Greedy bipartite matching between pred and one annotator's GT pts.

    Args:
        tree_gt : pre-built KDTree over gt_pts (None if gt_pts is empty)

    Returns:
        pred_matched_mask : bool array len(pred_pts), True if matched to any GT
        n_gt_matched      : number of GT points that got matched
    """
    n_pred = len(pred_pts)
    n_gt = len(gt_pts)
    pred_matched = np.zeros(n_pred, dtype=bool)
    if n_pred == 0 or n_gt == 0 or tree_gt is None:
        return pred_matched, 0

    # KDTree query for candidate matches (tree pre-built once per image)
    candidates = tree_gt.query_ball_point(pred_pts, r=max_dist_px)

    pred_idx_list, gt_idx_list, cost_list = [], [], []
    for p_i, cand in enumerate(candidates):
        for g_i in cand:
            d = np.linalg.norm(pred_pts[p_i] - gt_pts[g_i])
            pred_idx_list.append(p_i)
            gt_idx_list.append(g_i)
            cost_list.append(d)

    if not cost_list:
        return pred_matched, 0

    # Greedy match by ascending cost
    order = np.argsort(cost_list)
    gt_matched = np.zeros(n_gt, dtype=bool)
    for idx in order:
        p, g = pred_idx_list[idx], gt_idx_list[idx]
        if not pred_matched[p] and not gt_matched[g]:
            pred_matched[p] = True
            gt_matched[g] = True

    return pred_matched, int(gt_matched.sum())


def evaluate_threshold_bsds(pred_bool: np.ndarray,
                            gt_cache: List[Tuple[np.ndarray, object]],
                            total_gt: int,
                            max_dist_px: float) -> Tuple[int, int, int, int]:
    """BSDS500-correct: per-annotator matching with prediction-side aggregation.

    For each annotator, match prediction pts against that annotator's GT.
    A prediction pixel is TP if matched by ANY annotator (union OR across
    annotator matchings). Total GT count is SUM across annotators.

    Args:
        pred_bool : binary prediction (threshold sudah diterapkan)
        gt_cache  : list of (gt_pts, tree_gt) pre-computed per image
        total_gt  : pre-summed total GT count across annotators

    Returns:
        count_r : true positives for recall = total matched GT (summed)
        sum_r   : total GT positives (summed across annotators)
        count_p : true positives for precision = unique matched pred pts
        sum_p   : total predicted positives
    """
    pred_thin = sk_thin(pred_bool)
    pred_pts = np.argwhere(pred_thin)
    n_pred = len(pred_pts)
    if n_pred == 0:
        return 0, total_gt, 0, 0

    pred_matched_any = np.zeros(n_pred, dtype=bool)
    total_gt_matched = 0

    for gt_pts, tree_gt in gt_cache:
        pred_matched, n_gt_matched = match_single_annotator(
            pred_pts, gt_pts, tree_gt, max_dist_px
        )
        pred_matched_any |= pred_matched
        total_gt_matched += n_gt_matched

    count_p = int(pred_matched_any.sum())
    count_r = int(total_gt_matched)
    return count_r, total_gt, count_p, n_pred


def evaluate_image_thresholds(pred: np.ndarray, gts: List[np.ndarray],
                              thresholds: np.ndarray,
                              max_dist_frac: float
                              ) -> List[Tuple[int, int, int, int]]:
    h, w = pred.shape
    diag = np.sqrt(h * h + w * w)
    max_dist_px = max_dist_frac * diag

    # Pre-compute thinning + KDTree per annotator (konstan untuk semua threshold).
    # Ini menghilangkan kerja yang dulu diulang n_thresholds kali per gambar.
    gt_cache: List[Tuple[np.ndarray, object]] = []
    total_gt = 0
    for gt in gts:
        gt_pts = np.argwhere(sk_thin(gt))
        tree_gt = cKDTree(gt_pts) if len(gt_pts) > 0 else None
        gt_cache.append((gt_pts, tree_gt))
        total_gt += len(gt_pts)

    results = []
    for thresh in thresholds:
        bmap = pred >= thresh
        counts = evaluate_threshold_bsds(bmap, gt_cache, total_gt, max_dist_px)
        results.append(counts)
    return results

def aggregate_legacy(per_image_counts, thresholds):
    """Same arithmetic as aggregate_scores() in 04c (ODS, OIS = mean per-image F,
    AP = mean per-image trapezoid). Returns dict."""
    eps = 1e-10
    n_thresh = len(thresholds)
    ods_counts = np.zeros((n_thresh, 4))
    for img_counts in per_image_counts:
        for t_i, (cr, sr, cp, sp) in enumerate(img_counts):
            ods_counts[t_i] += [cr, sr, cp, sp]
    p_t = ods_counts[:, 2] / np.maximum(ods_counts[:, 3], eps)
    r_t = ods_counts[:, 0] / np.maximum(ods_counts[:, 1], eps)
    f_t = 2 * p_t * r_t / np.maximum(p_t + r_t, eps)
    ods_i = int(np.argmax(f_t))
    ois_f, ap = [], []
    for img_counts in per_image_counts:
        a = np.array(img_counts, dtype=np.float64)
        p_i = a[:, 2] / np.maximum(a[:, 3], eps)
        r_i = a[:, 0] / np.maximum(a[:, 1], eps)
        f_i = 2 * p_i * r_i / np.maximum(p_i + r_i, eps)
        ois_f.append(f_i[int(np.argmax(f_i))])
        order = np.argsort(r_i)
        ap.append(float(_trapz(p_i[order], r_i[order])))
    return dict(ods=float(f_t[ods_i]), ods_t=float(thresholds[ods_i]),
                ois=float(np.mean(ois_f)), ap=float(np.mean(ap)))


def save_edge_map_legacy(magnitude):
    """In-memory equivalent of edge_eval.save_edge_map + load_prediction_png."""
    mag = magnitude.astype(np.float32)
    mn, mx = mag.min(), mag.max()
    if mx > mn:
        mag = (mag - mn) / (mx - mn)
    img = (mag * 255.0).clip(0, 255).astype(np.uint8)
    return img.astype(np.float32) / 255.0
