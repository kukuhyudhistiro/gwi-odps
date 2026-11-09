"""Stage 1 preprocessing, identical to repo src/preprocessing.py when mode='he'.

BT.601 grayscale -> (optional) histogram equalization (PIL CDF method) -> (optional) /255.

Modes (Reviewer 2, point 7: contribution of HE and of the [0, 1] normalization):
    he            HE, then /255          (manuscript, Eq. 2)
    none          no HE, /255
    he_noscale    HE, values kept in [0, 255]
    none_noscale  no HE, values kept in [0, 255]
"""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageOps


def load_rgb(path: str) -> np.ndarray:
    return np.array(Image.open(path).convert("RGB"))


def to_gray_u8(rgb: np.ndarray) -> np.ndarray:
    f = rgb.astype(np.float64)
    g = 0.299 * f[:, :, 0] + 0.587 * f[:, :, 1] + 0.114 * f[:, :, 2]
    return np.clip(g, 0, 255).astype(np.uint8)


MODES = ("he", "none", "he_noscale", "none_noscale")


def preprocess(rgb: np.ndarray, mode: str = "he") -> np.ndarray:
    """Return a float64 image; in [0, 1] unless the mode ends with '_noscale'."""
    if mode not in MODES:
        raise ValueError(f"unknown preproc mode: {mode}")
    g = to_gray_u8(rgb)
    if mode.startswith("he"):
        g = np.array(ImageOps.equalize(Image.fromarray(g, mode="L")))
    g = g.astype(np.float64)
    return g if mode.endswith("_noscale") else g / 255.0


def load_and_preprocess(path: str, mode: str = "he") -> np.ndarray:
    return preprocess(load_rgb(path), mode)
