"""Gabor kernel construction.

Formula identical to repo src/gabor_core.py (Eq. 3-5 of the manuscript):

    g(x, y) = exp(-(x'^2 + gamma^2 y'^2) / (2 sigma^2)) * {sin|cos}(2 pi x' / lambda)
    x' =  x cos(theta) + y sin(theta),   y' = -x sin(theta) + y cos(theta)

Sampling: integer grid x, y in [-(k//2), k//2] (x = column, y = row), centred
at (0, 0), truncated to k x k, no normalization (same as the submitted code).
theta is the direction along which the carrier varies, i.e. the normal of the
edge that the kernel detects.

Options added for the revision:
    dc='zero'  : subtract the kernel mean from the real (cos) kernel
"""
from __future__ import annotations

from typing import List, Tuple

import numpy as np


def orientations_deg(N: int) -> List[float]:
    return [i * (180.0 / N) for i in range(N)]


def _grids(k: int, theta_rad: float) -> Tuple[np.ndarray, np.ndarray]:
    h = k // 2
    x, y = np.meshgrid(np.arange(-h, h + 1), np.arange(-h, h + 1))
    c, s = np.cos(theta_rad), np.sin(theta_rad)
    return x * c + y * s, -x * s + y * c


def gabor_pair(k: int, lam: float, theta_deg: float, sigma_ratio: float = 0.56,
               gamma: float = 0.5, dc: str = "raw", norm: str = "none"):
    """Return (real, imag) kernels, float64, k x k (k forced odd as in repo)."""
    k = k if k % 2 == 1 else k + 1
    sigma = sigma_ratio * lam
    xt, yt = _grids(k, np.deg2rad(theta_deg))
    env = np.exp(-0.5 * (xt ** 2 + (gamma ** 2) * yt ** 2) / sigma ** 2)
    arg = 2.0 * np.pi * xt / lam
    kr = env * np.cos(arg)
    ki = env * np.sin(arg)
    if dc == "zero":
        kr = kr - kr.mean()
    elif dc != "raw":
        raise ValueError(f"dc must be 'raw' or 'zero', got {dc}")
    if norm == "l2":
        kr = kr / np.linalg.norm(kr)
        ki = ki / np.linalg.norm(ki)
    elif norm != "none":
        raise ValueError(f"norm must be 'none' or 'l2', got {norm}")
    return kr.astype(np.float64), ki.astype(np.float64)


def gabor_bank(k, lam, N=8, sigma_ratio=0.56, gamma=0.5, dc="raw", norm="none"):
    reals, imags = [], []
    for th in orientations_deg(N):
        kr, ki = gabor_pair(k, lam, th, sigma_ratio, gamma, dc, norm)
        reals.append(kr)
        imags.append(ki)
    return reals, imags


def dc_to_gain(kr: np.ndarray, lam: float) -> float:
    """DC of the real kernel relative to its gain at the carrier frequency
    (both measured at theta = 0)."""
    k = kr.shape[0]
    h = k // 2
    x, _ = np.meshgrid(np.arange(-h, h + 1), np.arange(-h, h + 1))
    gain = float(np.sum(kr * np.cos(2 * np.pi * x / lam)))
    return float(kr.sum() / gain) if gain != 0 else float("nan")


def log_kernel(ksize: int = 7, sigma: float = 1.4) -> np.ndarray:
    """Laplacian-of-Gaussian kernel, ksize x ksize, sampled on the integer grid
    centred at 0 and shifted to zero sum (a flat region gives 0).
    Manuscript Section 4.3: "LoG is implemented as a 7x7 kernel with sigma = 1.4"."""
    h = ksize // 2
    x, y = np.meshgrid(np.arange(-h, h + 1, dtype=np.float64),
                       np.arange(-h, h + 1, dtype=np.float64))
    r2 = (x * x + y * y) / (2.0 * sigma * sigma)
    g = -(1.0 / (np.pi * sigma ** 4)) * (1.0 - r2) * np.exp(-r2)
    return g - g.mean()
