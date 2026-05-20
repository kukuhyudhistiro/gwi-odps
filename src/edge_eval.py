"""
edge_eval.py

Edge map post-processing and BSDS-style evaluation utilities.

Functions:
    - non_max_suppression(): Canny-style thinning along gradient direction
    - threshold_sweep():     binarize a magnitude map across many thresholds
    - save_edge_map():       persist a magnitude map as PNG (uint8)

The full ODS/OIS/AP scoring will be delegated to py-bsds500 in a separate
script (03_evaluate_bsds.py) since that toolbox provides the canonical
matching with diagonal-based tolerance. This module focuses on producing
the edge map artifacts that py-bsds500 will consume.

Author: Kukuh Yudhistiro
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


def non_max_suppression(magnitude: np.ndarray,
                        grad_x: np.ndarray = None,
                        grad_y: np.ndarray = None) -> np.ndarray:
    """Non-maximum suppression along gradient direction.

    If grad_x/grad_y not provided, computed via Sobel on the magnitude.
    Returns the suppressed magnitude (non-edge pixels set to 0).

    Standard step in BSDS-protocol edge detection. Without NMS, broad
    ridges of magnitude get matched as multiple edges, inflating recall
    artificially.
    """
    mag = magnitude.astype(np.float32)
    if grad_x is None or grad_y is None:
        # Estimate gradient direction from the magnitude itself
        grad_x = cv2.Sobel(mag, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(mag, cv2.CV_32F, 0, 1, ksize=3)

    angle = np.arctan2(grad_y, grad_x) * 180.0 / np.pi
    angle[angle < 0] += 180.0
    # Quantize to 4 directions: 0, 45, 90, 135
    h, w = mag.shape
    out = np.zeros_like(mag)

    # Pad to simplify boundary handling
    pad = np.pad(mag, 1, mode="constant", constant_values=0)
    a = angle

    # 0 degrees (horizontal)
    mask0 = ((a >= 0) & (a < 22.5)) | ((a >= 157.5) & (a <= 180))
    n1 = pad[1:-1, :-2]
    n2 = pad[1:-1, 2:]
    out[mask0 & (mag >= n1) & (mag >= n2)] = mag[mask0 & (mag >= n1)
                                                  & (mag >= n2)]

    # 45 degrees
    mask45 = (a >= 22.5) & (a < 67.5)
    n1 = pad[:-2, 2:]
    n2 = pad[2:, :-2]
    out[mask45 & (mag >= n1) & (mag >= n2)] = mag[mask45 & (mag >= n1)
                                                    & (mag >= n2)]

    # 90 degrees (vertical)
    mask90 = (a >= 67.5) & (a < 112.5)
    n1 = pad[:-2, 1:-1]
    n2 = pad[2:, 1:-1]
    out[mask90 & (mag >= n1) & (mag >= n2)] = mag[mask90 & (mag >= n1)
                                                    & (mag >= n2)]

    # 135 degrees
    mask135 = (a >= 112.5) & (a < 157.5)
    n1 = pad[:-2, :-2]
    n2 = pad[2:, 2:]
    out[mask135 & (mag >= n1) & (mag >= n2)] = mag[mask135 & (mag >= n1)
                                                      & (mag >= n2)]

    return out


def save_edge_map(magnitude: np.ndarray, out_path: Path) -> None:
    """Save normalized magnitude as 8-bit PNG.

    py-bsds500 evaluation expects 8-bit grayscale PNG where pixel value
    represents edge probability. It will run its own threshold sweep
    internally over the 256 levels.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    mag = magnitude.astype(np.float32)
    mn, mx = mag.min(), mag.max()
    if mx > mn:
        mag = (mag - mn) / (mx - mn)
    img = (mag * 255.0).clip(0, 255).astype(np.uint8)
    cv2.imwrite(str(out_path), img)


def adaptive_threshold(magnitude: np.ndarray,
                       k_sigma: float = 2.0) -> tuple:
    """Compute T = mean + k*std and return (binary_edges, T).

    Provided for analysis/visualization (Block A figures), NOT for ODS
    evaluation. ODS uses threshold sweep instead.
    """
    T = float(magnitude.mean() + k_sigma * magnitude.std())
    return (magnitude > T).astype(bool), T
