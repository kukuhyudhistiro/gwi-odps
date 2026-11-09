"""Orientation-aware non-maximum suppression (ODPS) and gradient-direction NMS.

ODPS (Eq. 10-11): a pixel is kept if E(x) >= E(x + d n) and E(x) >= E(x - d n),
with n = (cos theta*, sin theta*), theta* = argmax orientation (edge normal).

Sampling modes
    nearest  : offsets round(d cos theta), round(d sin theta) with np.round, as in
               the submitted code. Effective distance differs per orientation
               (N = 8, d = 2: 2, 2.24, 1.41, 2.24, 2, 2.24, 1.41, 2.24 px).
    bilinear : neighbour value bilinearly interpolated at the exact position.
Outside the image
    zero     : neighbour = 0 (submitted code)
    reflect  : reflect-101 border
Ties are kept (>=), as in the submitted code.

quantize_direction() is used only by the optional standard NMS applied to the
maps of learning-based detectors (scripts/23_eval_external.py --nms).
"""
from __future__ import annotations

import cv2
import numpy as np

_BORDER = {"zero": cv2.BORDER_CONSTANT, "reflect": cv2.BORDER_REFLECT_101}


def offsets(N: int, d: float, mode: str):
    """List of (dx, dy) per orientation index (x = column, y = row)."""
    out = []
    for k in range(N):
        t = np.deg2rad(k * 180.0 / N)
        dx, dy = np.cos(t) * d, np.sin(t) * d
        if mode == "nearest":
            dx, dy = float(np.round(dx)), float(np.round(dy))
        elif mode != "bilinear":
            raise ValueError(f"unknown sampling mode {mode}")
        out.append((dx, dy))
    return out


def _shift(img: np.ndarray, dx: float, dy: float, mode: str, outside: str):
    """Return S with S[y, x] = img[y + dy, x + dx]."""
    h, w = img.shape
    M = np.array([[1.0, 0.0, dx], [0.0, 1.0, dy]], dtype=np.float64)
    interp = cv2.INTER_NEAREST if mode == "nearest" else cv2.INTER_LINEAR
    return cv2.warpAffine(img, M, (w, h), flags=interp | cv2.WARP_INVERSE_MAP,
                          borderMode=_BORDER[outside], borderValue=0.0)


def odps(mag: np.ndarray, idx: np.ndarray, N: int = 8, d: float = 2,
         mode: str = "nearest", outside: str = "zero",
         keep_equal: bool = True) -> np.ndarray:
    mag = mag.astype(np.float32, copy=False)
    keep = np.zeros(mag.shape, dtype=bool)
    for k, (dx, dy) in enumerate(offsets(N, d, mode)):
        sel = idx == k
        if not sel.any():
            continue
        pos = _shift(mag, dx, dy, mode, outside)
        neg = _shift(mag, -dx, -dy, mode, outside)
        if keep_equal:
            ok = (mag >= pos) & (mag >= neg)
        else:
            ok = (mag > pos) & (mag > neg)
        keep |= sel & ok
    return np.where(keep, mag, np.float32(0.0)).astype(np.float32)


def quantize_direction(gx: np.ndarray, gy: np.ndarray, N: int = 8) -> np.ndarray:
    """Gradient direction (normal of the edge) to orientation index in [0, N)."""
    theta = np.mod(np.arctan2(gy, gx), np.pi)
    return (np.round(theta / (np.pi / N)).astype(np.int32)) % N
