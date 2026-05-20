# Mathematical Derivation of ODPS

This document derives the side‑lobe phenomenon in the imaginary Gabor
response and the rationale for the ODPS post‑processing step.

---

## 1. The Imaginary Gabor Kernel

In 1D, the imaginary part of the Gabor function is:

$$g_{\mathrm{imag}}(x) = \sin\!\left(\frac{2\pi x}{\lambda}\right) \cdot
                          \exp\!\left(-\frac{x^2}{2\sigma^2}\right)$$

This kernel is odd‑symmetric: $g_{\mathrm{imag}}(-x) = -g_{\mathrm{imag}}(x)$.

For the **5×5 kernel** used in this paper (k=5, λ=4, σ=2.24, γ=0.5), the discrete 1D
kernel values at integer positions are:

| x | -2 | -1 | 0 | 1 | 2 |
|---|----:|----:|----:|----:|----:|
| g(x) | 0 | −0.84 | 0 | +0.84 | 0 |

The kernel has zero crossings at x = 0, ±2 and extrema at x = ±1.

---

## 2. Convolution with a Step Edge

Consider a 1D ideal step edge $E(x) = H(x)$ (Heaviside step, transition at x = 0).
The convolution response is:

$$R(x) = (E \star g_{\mathrm{imag}})(x)$$

Because the kernel is odd‑symmetric, the result is **signed**: positive on the
right side of the edge, negative on the left side. In Stage 4 of the GWi pipeline,
we take the absolute value:

$$M(x) = |R(x)|$$

The absolute value produces a **central main peak** exactly at the edge location
(x = 0) and two **side‑lobes** at positions approximately **±λ/2**. For λ = 4,
the side‑lobes appear at x ≈ ±2 pixels.

**Why do side‑lobes arise?**  
The sine carrier $\sin(2\pi x / \lambda)$ has zero crossings at integer multiples
of λ/2. The main peak sits at the first zero crossing after the edge (x = λ/4 ≈ 1).
The absolute value folds the negative lobe into a positive magnitude, but the
next zero crossing of the sine (at x = λ/2) creates a second positive peak –
the side‑lobe.

---

## 3. Why Side‑Lobes Hurt Evaluation

The Berkeley evaluation protocol [11] matches predicted edge pixels against
ground‑truth pixels using a distance tolerance:

$$\tau_{\mathrm{tol}} = 0.0075 \cdot \text{diag}(\text{image})$$

For the datasets used in this paper:

| Dataset | Image size | Diagonal | Tolerance (pixels) |
|---------|------------|---------:|-------------------:|
| BSDS500 | 321 × 481 | ≈ 578.3   | 4.34 |
| BIPED   | 1280 × 720 | ≈ 1469.7  | 11.01 |
| UDED    | variable   | varies    | varies (0.0075 × diag) |

**Each ground‑truth pixel can match at most one prediction.** Extra predictions
become false positives (FPs). For a step edge with side‑lobes at ±2 pixels:

- The main peak (1 pixel) matches the ground truth → 1 true positive (TP)
- The two side‑lobes (±2 px) also lie within the tolerance (e.g., 4.34 px for
  BSDS500) but there is no remaining ground‑truth pixel to match → they become
  2 FPs.

Consequence: **1 TP + 2 FPs per true edge**, which depresses precision.  
On BIPED, the 11‑pixel tolerance easily covers the side‑lobes, so every edge
produces 2–3 false positives.

---

## 4. ODPS Solution

ODPS (Orientation‑aware Double‑Peak Suppression) removes these side‑lobes
by reusing the orientation argmax map from Stage 5. For each pixel $(x,y)$,
let $\theta^*(x,y)$ be the orientation index (0…7) that gave the maximum
response in Stage 5. The edge‑normal direction is:

n(x,y) = (cos θ*(x,y),sin θ*(x,y))

We then apply orientation‑aware non‑maximum suppression (a variant of
classical NMS [4]) with a fixed distance $d = \lambda/2 = 2$ pixels:

$$E_{\mathrm{ODPS}}(x, y) = \begin{cases}
E(x, y) & \text{if } E(x, y) \geq \max\!\big(E(x + d\mathbf{n}),\ E(x - d\mathbf{n})\big) \\[4pt]
0 & \text{otherwise}
\end{cases}$$

### Why It Works

- **Main peak**: magnitude is higher than both neighbors at ±d along the
  edge‑normal direction → passes the check → **kept**.
- **Side‑lobe**: magnitude is lower than the main peak (which lies at the
  center) → fails the maximum check → **suppressed (zeroed)**.
- **Flat region**: all magnitudes are low and similar → suppression may
  remove random noise peaks, bounded false positive rate.

---

## 5. Computational Cost

ODPS adds **no additional convolution** because it only performs neighbour
comparisons using the already‑computed argmax map. Its complexity is
$O(H \times W)$ for an $H \times W$ image.

Measured runtimes on the **5×5, λ=4** baseline (single CPU thread):

| Dataset | GWi (Stages 1–5) | ODPS Stage 6 | ODPS overhead |
|---------|-----------------:|-------------:|--------------:|
| BSDS500 | 11.26 ms | 6.05 ms | +54% (of GWi) |
| BIPED   | 64.65 ms | 37.91 ms | +59% |
| UDED    | 17.55 ms | 10.13 ms | +58% |

When added to the full pipeline (GWi+ODPS), the overhead relative to GWi
alone is about 54–59%, but the absolute time remains modest (e.g., 25.9 ms
on BSDS500) and the runtime is at parity with complex Gabor (GWC).

---

## 6. Empirical Validation

The effectiveness of ODPS is confirmed by the ODS improvement across all
three datasets (evaluation with 99 thresholds, k=5):

| Dataset | GWi (Stages 1–5) | GWi+ODPS | Δ ODS | Δ % |
|---------|-----------------:|---------:|------:|----:|
| BSDS500 | 0.4443 | 0.4696 | +0.0253 | +5.7% |
| BIPED   | 0.5602 | 0.5744 | +0.0142 | +2.5% |
| UDED    | 0.6072 | 0.6449 | +0.0377 | +6.2% |

The largest relative gain on UDED (+6.2%) reflects the diversity of edge
structures in cross‑domain images, where side‑lobe suppression recovers
many spurious detections. The smallest gain on BIPED (+2.5%) occurs because
GWi alone already achieves high precision on BIPED’s clean single‑annotator
boundaries; therefore fewer side‑lobe false positives remain to be
suppressed.

---

## 7. Limitations

ODPS assumes that the edge‑normal direction is well defined and that the
distance $d = \lambda/2$ is appropriate. Failures occur in three regimes:

1. **Junctions** (e.g., T‑junctions, X‑junctions): multiple competing
   orientations cause the argmax map to be unstable.
2. **Noise‑dominated regions**: random argmax values may suppress valid
   weak edges or create false positives.
3. **High curvature** (curvature radius ≪ λ): locally curved edges shift
   the argmax estimate, making the fixed $d$ suboptimal.

These limitations motivate future work on spatially‑adaptive Gabor
parameters or learning per‑pixel suppression distances.

---

## References

- Canny, J. (1986). A computational approach to edge detection. *IEEE
  Transactions on Pattern Analysis and Machine Intelligence*, 8(6), 679–698.
- Daugman, J.G. (1985). Uncertainty relation for resolution in space,
  spatial frequency, and orientation optimized by two‑dimensional visual
  cortical filters. *Journal of the Optical Society of America A*, 2(7),
  1160–1169.
- Arbeláez, P., Maire, M., Fowlkes, C., & Malik, J. (2011). Contour detection
  and hierarchical image segmentation. *IEEE TPAMI*, 33(5), 898–916.
- Kovesi, P. (1999). Image features from phase congruency. *Videre: Journal
  of Computer Vision Research*, 1(3), 1–26.
