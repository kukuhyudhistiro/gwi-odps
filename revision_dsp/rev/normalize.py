"""Map normalization before thresholding.

    minmax_image per-image min-max to [0, 1] (manuscript protocol; submitted code,
                 edge_eval.save_edge_map). Used for every method and every table.
    fixed        v = clip(raw / s, 0, 1) with one scale per method; not used in the
                 revision (kept only so that older cached results stay readable).

Binary maps (canny, ed) are only clipped.
If quantize_8bit, v is floored to 8-bit levels as in the submitted PNG maps.
"""
from __future__ import annotations

import zlib

import numpy as np


def sample_pixels(raw: np.ndarray, image_id: str, n: int = 20000) -> np.ndarray:
    flat = raw.ravel()
    if flat.size <= n:
        return flat.astype(np.float64)
    rng = np.random.default_rng(zlib.crc32(image_id.encode()))
    return flat[rng.choice(flat.size, n, replace=False)].astype(np.float64)


def scale_from_samples(samples, percentile: float) -> float:
    pool = np.concatenate(samples)
    s = float(np.percentile(pool, percentile))
    if not np.isfinite(s) or s <= 0:
        s = float(pool.max()) if pool.size and pool.max() > 0 else 1.0
    return s


def normalize(raw: np.ndarray, mode: str, scale: float | None,
              native01: bool, quantize_8bit: bool = True) -> np.ndarray:
    raw = raw.astype(np.float32)
    if native01:
        v = np.clip(raw, 0, 1)
    elif mode == "fixed":
        if scale is None:
            raise ValueError("fixed normalization needs a scale")
        v = np.clip(raw / np.float32(scale), 0, 1)
    elif mode == "minmax_image":
        mn, mx = raw.min(), raw.max()
        v = (raw - mn) / (mx - mn) if mx > mn else np.zeros_like(raw)
    else:
        raise ValueError(f"unknown normalization {mode}")
    if quantize_8bit:
        v = (v * 255.0).clip(0, 255).astype(np.uint8).astype(np.float32) / 255.0
    return v.astype(np.float32)
