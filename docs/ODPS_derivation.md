# Mathematical Derivation of ODPS

This document derives the side-lobe phenomenon in the imaginary Gabor
response and the rationale for the ODPS post-processing step.

---

## 1. The Imaginary Gabor Kernel

In 1D, the imaginary part of the Gabor function:

$$g_{\mathrm{imag}}(x) = \sin\!\left(\frac{2\pi x}{\lambda}\right) \cdot
                          \exp\!\left(-\frac{x^2}{2\sigma^2}\right)$$

Odd-symmetric: $g_{\mathrm{imag}}(-x) = -g_{\mathrm{imag}}(x)$.

For k=5, λ=4, σ=2.24 (the canonical configuration):

| x | -2 | -1 | 0 | 1 | 2 |
|---|----:|----:|----:|----:|----:|
| g(x) | 0 | −0.84 | 0 | +0.84 | 0 |

Zero crossings at x = 0, ±2; extrema at x = ±1.

---

## 2. Convolution with a Step Edge

For a 1D step edge $E(x) = H(x)$ (Heaviside, transition at 0):

$$R(x) = (E \star g_{\mathrm{imag}})(x)$$

The result is **signed**: positive on one side of the edge, negative on the
other. After taking the absolute value (Stage 4):

The result has a **central main peak** at the edge location flanked by
**side-lobes at ±λ/2** ≈ ±2 pixels for λ=4.

The side-lobes emerge because the sine carrier has zero crossings at the
edge, but its absolute value creates new peaks at the next zero crossings
of the sinusoid, which sit at ±λ/2 from the main peak.

---

## 3. Why Side-Lobes Hurt Evaluation

The Berkeley evaluation protocol matches predicted edge pixels against
ground-truth pixels using:

$$\tau_{\mathrm{tol}} = 0.0075 \cdot \mathrm{diag}(\text{image})$$

| Dataset | Image size | Tolerance |
|---------|------------|----------:|
| BSDS500 | 321 × 481 | 4.34 pixels |
| BIPED | 1280 × 720 | 11.01 pixels |

**Each ground-truth pixel matches at most one prediction.** Extra
predictions become false positives.

For a step edge with side-lobes at ±2 pixels:
- Main peak (1 pixel) matches GT → 1 TP
- Side-lobes at ±2 px fall within tolerance → no remaining GT to match → 2 FPs

Result: **1 TP, 2 FPs per true edge**, depressing precision.

For BIPED with 11-pixel tolerance, side-lobes always fall within
tolerance, so every edge produces 2-3 false positives.

---

## 4. ODPS Solution

For each pixel (x, y), use the orientation argmax θ*(x, y) from Stage 5
to define the edge-normal direction:

n(x,y)=(cos θ*(x,y),sin θ*(x,y))

Apply orientation-aware non-maximum suppression:

$$E_{\mathrm{ODPS}}(x, y) = \begin{cases}
E(x, y) & \text{if } E(x, y) \geq \max(E(x + d\mathbf{n}), E(x - d\mathbf{n})) \\
0 & \text{otherwise}
\end{cases}$$

with $d = 2$ pixels (matching side-lobe distance λ/2 for λ=4).

### Why It Works

For a main-peak pixel:
- Its magnitude is **higher** than both neighbors at ±d·n
- Passes maximum check → **kept**

For a side-lobe pixel at offset ±2:
- Main-peak neighbor has **higher** magnitude
- Fails maximum check → **suppressed (zeroed)**

For flat region pixels:
- Comparable to or lower than noise neighbors
- Net contribution to false positives is bounded

---

## 5. Computational Cost

ODPS reuses the argmax map θ*(x, y) from Stage 5 — no additional
convolutions are performed.

Per-pixel: O(1) (lookup, comparison, conditional zero).
Total: **O(H × W)** for an H × W image.

Measured (k=5 baseline, single-thread):

| Dataset | Pipeline (Stages 1-5) | ODPS (Stage 6) | ODPS overhead |
|---------|----------------------:|---------------:|--------------:|
| BSDS500 | 11.26 ms | 6.05 ms | +24% |
| BIPED | 64.65 ms | 37.91 ms | +27% |
| UDED | 17.55 ms | 10.13 ms | +25% |

---

## 6. Empirical Validation

The +2.5% to +6.2% relative ODS improvement across three datasets confirms
the theory:

| Dataset | GWi ODS | GWi+ODPS ODS | Δ ODS | Δ % |
|---------|--------:|-------------:|------:|----:|
| BSDS500 | 0.4443 | 0.4696 | +0.0253 | +5.7% |
| BIPED | 0.5602 | 0.5744 | +0.0142 | +2.5% |
| UDED | 0.6072 | 0.6449 | +0.0377 | +6.2% |

The largest gain on UDED reflects the diversity of edge structures in
cross-domain images, where side-lobe suppression has the largest
proportional effect.

The smallest gain on BIPED reflects that GWi alone already achieves high
precision on BIPED's single-annotator boundaries; remaining side-lobe
false positives are proportionally fewer.

---

## 7. Limitations

ODPS assumes the edge-normal direction is well-defined at each pixel,
which fails in three regimes:

1. **Junctions** (T-junctions, X-junctions): multiple competing orientations
2. **Noise-dominated regions**: random argmax suppresses valid edges
3. **Curvature ≫ λ**: locally curved edges shift the argmax estimate

These motivate the future direction of spatially-adaptive Gabor parameters
or learned per-pixel d prediction.

---

## References

- Daugman, J.G. (1985). "Uncertainty relation for resolution in space,
  spatial frequency, and orientation optimized by two-dimensional visual
  cortical filters." JOSA A, 2(7), 1160-1169.
- Kovesi, P. (1999). "Image features from phase congruency." Videre, 1(3), 1-26.
- Canny, J. (1986). "A computational approach to edge detection." IEEE
  TPAMI, 8(6), 679-698.
- Arbelaez, P., Maire, M., Fowlkes, C., Malik, J. (2011). "Contour detection
  and hierarchical image segmentation." IEEE TPAMI, 33(5), 898-916.
