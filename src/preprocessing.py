"""
preprocessing.py

Image preprocessing pipeline:
    RGB -> Grayscale (BT.601) -> Histogram Equalization -> [0,1] normalize

This is the SAME preprocessing used by every method in the comparison
(GWi, GWC, Canny, Sobel, LoG, PC, ED) to ensure fair runtime evaluation —
runtime differences must come from the filtering algorithm, not from
preprocessing variations.

Author: Kukuh Yudhistiro
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Tuple

import cv2
import numpy as np
from PIL import Image, ImageOps


@dataclass
class PreprocStats:
    """Per-image preprocessing statistics for logging."""

    height: int
    width: int
    mean_before: float
    std_before: float
    mean_after: float
    std_after: float

    @property
    def contrast_change_pct(self) -> float:
        if self.std_before < 1e-10:
            return 0.0
        return (self.std_after - self.std_before) / self.std_before * 100.0


def load_and_preprocess(image_path: Path) -> Tuple[np.ndarray, np.ndarray,
                                                    np.ndarray, np.ndarray,
                                                    PreprocStats]:
    """Load image and apply the full preprocessing pipeline.

    Pipeline stages:
        1. Load RGB
        2. Convert to grayscale using ITU-R BT.601 weights (0.299, 0.587, 0.114)
        3. Apply histogram equalization
        4. Normalize to [0, 1] float64

    Returns:
        rgb         : original RGB uint8 array (H, W, 3)
        gray_raw    : grayscale before EQ (H, W) uint8
        gray_eq     : grayscale after EQ (H, W) uint8
        normalized  : final [0, 1] float64 (H, W)
        stats       : PreprocStats record
    """
    img = Image.open(str(image_path)).convert("RGB")
    rgb = np.array(img)
    img_f = rgb.astype(np.float64)

    # BT.601 grayscale
    gray_raw = (0.299 * img_f[:, :, 0]
                + 0.587 * img_f[:, :, 1]
                + 0.114 * img_f[:, :, 2])
    gray_raw = np.clip(gray_raw, 0, 255).astype(np.uint8)

    mean_b, std_b = float(gray_raw.mean()), float(gray_raw.std())

    # Histogram equalization (PIL implementation = CDF method)
    gray_eq = np.array(ImageOps.equalize(Image.fromarray(gray_raw, mode="L")))

    mean_a, std_a = float(gray_eq.mean()), float(gray_eq.std())

    normalized = gray_eq.astype(np.float64) / 255.0

    stats = PreprocStats(
        height=rgb.shape[0],
        width=rgb.shape[1],
        mean_before=mean_b, std_before=std_b,
        mean_after=mean_a, std_after=std_a,
    )

    return rgb, gray_raw, gray_eq, normalized, stats
