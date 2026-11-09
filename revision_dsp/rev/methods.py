"""Edge-map producers. Every method returns a raw (un-normalized) float32 map.

A method is described by a spec dict, e.g.
    {"family": "gwi", "k": 5, "lam": 4, "N": 8, "sigma_ratio": 0.56,
     "gamma": 0.5, "nms": {"d": 2, "mode": "nearest"}}

Families (baselines as described in Section 4.3 of the manuscript)
    gwi        imaginary-only Gabor: max_theta |I * g_imag|, argmax -> ODPS
    gwc        complex Gabor: max_theta sqrt((I*g_real)^2 + (I*g_imag)^2), same
               kernel parameters as GWi; dc = 'raw' (manuscript) or 'zero'
               (real kernel mean removed; analysis for Reviewer 1, point 5)
    gwe        even-only Gabor (real kernel), mechanism analysis only
    sobel      3x3 Sobel, magnitude sqrt(Gx^2 + Gy^2), no extra smoothing
    gaussgrad  Gaussian smoothing (sigma) + Sobel magnitude. This is what the
               submitted code computed for the row labelled "Canny"; it is kept
               under its correct name.
    log        |I * LoG|, LoG = ksize x ksize kernel with sigma (7, 1.4)
    canny      cv2.Canny(low, high) on the preprocessed 8-bit image, OpenCV
               defaults otherwise (aperture 3, L1 gradient); binary map
    pc         phase congruency, phasepack (Python port of Kovesi's phasecong3),
               4 scales and 6 orientations, other parameters at Kovesi's defaults
    ed         Edge Drawing, cv2.ximgproc.EdgeDrawing with default Params(); binary

'nms': {"d": 2, "mode": "nearest"} applies ODPS (Eq. 10-11) using the Gabor
argmax. ODPS is part of the proposed method only.

Timing: pass a dict as `timer`; stage durations (s) are added under keys
'filter', 'pool', 'nms'.
"""
from __future__ import annotations

import time
from functools import lru_cache
from typing import Dict, Optional

import cv2
import numpy as np

from . import kernels as K
from .nms import odps, quantize_direction

_BORDER = {"reflect": cv2.BORDER_REFLECT_101, "constant": cv2.BORDER_CONSTANT}
NATIVE01 = {"canny", "ed"}               # binary maps, already in {0, 1}


class _T:
    def __init__(self, timer, key):
        self.timer, self.key = timer, key

    def __enter__(self):
        self.t0 = time.perf_counter()

    def __exit__(self, *a):
        if self.timer is not None:
            self.timer[self.key] = self.timer.get(self.key, 0.0) + \
                time.perf_counter() - self.t0


@lru_cache(maxsize=64)
def _bank(k, lam, N, sigma_ratio, gamma, dc, norm):
    return K.gabor_bank(k, lam, N, sigma_ratio, gamma, dc, norm)


def _gabor(img, spec, border, timer, part, need_idx=True):
    N = int(spec.get("N", 8))
    reals, imags = _bank(int(spec["k"]), float(spec["lam"]), N,
                         float(spec.get("sigma_ratio", 0.56)),
                         float(spec.get("gamma", 0.5)),
                         spec.get("dc", "raw"), spec.get("norm", "none"))
    b = _BORDER[border]
    resp = np.empty((N,) + img.shape, dtype=np.float64)
    with _T(timer, "filter"):
        for i in range(N):
            if part == "imag":
                resp[i] = np.abs(cv2.filter2D(img, cv2.CV_64F, imags[i], borderType=b))
            elif part == "real":
                resp[i] = np.abs(cv2.filter2D(img, cv2.CV_64F, reals[i], borderType=b))
            else:
                r = cv2.filter2D(img, cv2.CV_64F, reals[i], borderType=b)
                q = cv2.filter2D(img, cv2.CV_64F, imags[i], borderType=b)
                resp[i] = np.sqrt(r * r + q * q)
    with _T(timer, "pool"):
        if need_idx:      # argmax only when ODPS needs it (GWi alone: max only)
            idx = np.argmax(resp, axis=0).astype(np.int32)
            mag = np.take_along_axis(resp, idx[None], axis=0)[0]
        else:
            idx = None
            mag = resp.max(axis=0)
    return mag, idx, N


def _grad(img, gxk, gyk, border, timer, N, smooth_sigma=None):
    b = _BORDER[border]
    with _T(timer, "filter"):
        src = img
        if smooth_sigma:
            src = cv2.GaussianBlur(img, (0, 0), float(smooth_sigma), borderType=b)
        if gxk is None:
            gx = cv2.Sobel(src, cv2.CV_64F, 1, 0, ksize=3, borderType=b)
            gy = cv2.Sobel(src, cv2.CV_64F, 0, 1, ksize=3, borderType=b)
        else:
            gx = cv2.filter2D(src, cv2.CV_64F, gxk, borderType=b)
            gy = cv2.filter2D(src, cv2.CV_64F, gyk, borderType=b)
        mag = np.sqrt(gx * gx + gy * gy)
    with _T(timer, "pool"):
        idx = quantize_direction(gx, gy, N)
    return mag, idx


def compute(img: np.ndarray, spec: Dict, border: str = "reflect",
            nms_outside: str = "reflect", timer: Optional[dict] = None,
            need_idx: bool = False):
    """Return (raw_map float32, orientation_index or None)."""
    f = spec["family"]
    nms = spec.get("nms")
    idx = None
    N = int(spec.get("N", 8))
    if f in ("gwi", "gwc", "gwe"):
        part = {"gwi": "imag", "gwc": "complex", "gwe": "real"}[f]
        mag, idx, N = _gabor(img, spec, border, timer, part, need_idx=bool(nms) or need_idx)
    elif f == "sobel":
        mag, idx = _grad(img, None, None, border, timer, N)
    elif f == "gaussgrad":
        mag, idx = _grad(img, None, None, border, timer, N,
                         smooth_sigma=spec.get("sigma", 1.4))
    elif f == "log":
        b = _BORDER[border]
        kern = _log_kernel(int(spec.get("ksize", 7)), float(spec.get("sigma", 1.4)))
        with _T(timer, "filter"):
            mag = np.abs(cv2.filter2D(img, cv2.CV_64F, kern, borderType=b))
        if nms:
            raise ValueError("NMS is not defined for |LoG| (no direction)")
    elif f == "canny":
        mag = _canny(img, spec, timer)
        nms = None
    elif f == "pc":
        mag = _pc(img, spec, timer)
        nms = None
    elif f == "ed":
        mag = _ed(img, timer)
        nms = None
    else:
        raise ValueError(f"unknown family {f}")
    mag = mag.astype(np.float32)
    if nms:
        with _T(timer, "nms"):
            mag = odps(mag, idx, N=N, d=float(nms.get("d", 2)),
                       mode=nms.get("mode", "nearest"),
                       outside=nms.get("outside", nms_outside))
    return mag, idx


@lru_cache(maxsize=8)
def _log_kernel(ksize, sigma):
    return K.log_kernel(ksize, sigma)


def _to_u8(img):
    """Preprocessed image back to 8 bit (handles [0, 1] and [0, 255] inputs)."""
    v = img * 255.0 if img.max() <= 1.0 + 1e-9 else img
    return np.clip(np.round(v), 0, 255).astype(np.uint8)


def _canny(img, spec, timer):
    with _T(timer, "filter"):
        e = cv2.Canny(_to_u8(img), float(spec.get("low", 50)), float(spec.get("high", 150)))
    return (e > 0).astype(np.float64)


def _pc(img, spec, timer):
    try:
        from phasepack import phasecong
    except ImportError as e:
        raise RuntimeError("phasepack not installed: pip install phasepack") from e
    with _T(timer, "filter"):
        M = phasecong(_to_u8(img).astype(np.float64), nscale=int(spec.get("nscale", 4)),
                      norient=int(spec.get("norient", 6)),
                      minWaveLength=float(spec.get("min_wavelength", 3)),
                      mult=float(spec.get("mult", 2.1)),
                      sigmaOnf=float(spec.get("sigma_onf", 0.55)),
                      k=float(spec.get("k", 2.0)))[0]
    return np.asarray(M, dtype=np.float64)


def _ed(img, timer):
    if not hasattr(cv2, "ximgproc"):
        raise RuntimeError("Edge Drawing needs opencv-contrib-python")
    with _T(timer, "filter"):
        ed = cv2.ximgproc.createEdgeDrawing()
        ed.setParams(cv2.ximgproc.EdgeDrawing.Params())   # default parameter set (Section 4.3)
        ed.detectEdges(_to_u8(img))
        e = ed.getEdgeImage()
    return (e > 0).astype(np.float64)
