
# Hardware and Timing Notes

## Reference Hardware

All timing measurements use:

| Component | Specification |
|-----------|---------------|
| CPU | Intel Core i5-14400 (Raptor Lake, 10P + 4E, 16 threads) |
| Base clock | 2.5 GHz (P-cores), 1.8 GHz (E-cores) |
| Turbo | 4.7 GHz max |
| Cache | 20 MB L3 |
| RAM | 16 GB DDR4-3200 |
| OS | Windows 11 Pro |
| Python | 3.13 |

## Single-Thread Enforcement

Scripts enforce single-thread before NumPy/OpenCV import:

```python
import os
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

import cv2
cv2.setNumThreads(1)
```

Environment variables must be set **before** import. Scripts handle this automatically.

## Warm-Up

Before timing, each script processes 3 synthetic images to warm caches. This discards cold-start effects.

## Timing Methodology

```python
start = time.perf_counter()
result = apply_filter(image)
elapsed_ms = (time.perf_counter() - start) * 1000.0
```

Image loading and disk I/O are excluded from `filter_time`. Total time (`total_time_s`) includes preprocessing + filter + ODPS (if applicable).

## Expected Runtime on Different Hardware

| Hardware tier | Relative speed | BSDS500 GWi+ODPS |
|---------------|---------------:|------------------:|
| Intel i9-13900K / Ryzen 9 7950X | 0.7× | ~18 ms |
| **Intel i5-14400 (reference)** | **1.0×** | **25.9 ms** |
| Intel i5-10400 | 1.3× | ~34 ms |
| Apple M1/M2 | 1.0-1.3× | ~26-34 ms |
| Mid-range laptop | 1.5-2.0× | ~40-55 ms |

Relative comparisons (vs GWC, vs PC) should remain stable across hardware.

## Memory Footprint

| Dataset | Peak RAM |
|---------|---------:|
| BSDS500 | ~250 MB |
| BIPED | ~600 MB (large images) |
| UDED | ~200 MB |

No GPU required.

## Per-Method Operation Counts

Per single-channel input image of H×W pixels with N=8 orientations:

| Method | Convolutions | Sqrt? | NMS? |
|--------|:-----------:|:-----:|:----:|
| Sobel | 2 (3×3) | per-pixel | no |
| LoG | 1 (7×7) | no | no |
| Canny | 2 (3×3) | per-pixel | yes (gradient-based) |
| Edge Drawing | 2 (3×3) | per-pixel | implicit |
| GWC | 16 (k×k) | per-pixel | no |
| **GWi** | **8 (k×k)** | **no** | **no** |
| **GWi+ODPS** | **8 (k×k)** | **no** | **yes (orientation-based)** |
| Phase Congruency | multi-scale FFT (4 scales × 6 orient) | yes | no |
