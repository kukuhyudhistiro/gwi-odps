# ODPS: definition, mechanism and cost

**Version 3.0.0 (first revision).** This document replaces the v2.0.0 text, which derived "side lobes at ±λ/2 ≈ ±2 px" for k5 λ4.

Two statements of v2.0.0 are wrong:
- **The kernel row.** It was given as 0, −0.84, 0, +0.84, 0. The computed centre row is 0, −0.905, 0, +0.905, 0.
- **The side lobes.** This kernel has no carrier side lobe inside its window.

The v2.0.0 text is still in the history: `git show dsp-submitted-v1:docs/ODPS_derivation.md`.

All numbers below come from `revision_dsp/results/`:
- E02: `mechanism/`, synthetic structures;
- E20 and E22: `test/`, `stats/`;
- E24: `runtime/`;
- E25: `qualitative/`.

The findings are in `revision_dsp/FINDINGS.md`: F12, F13, F18, F22, F25, F27 and F28.

---

## 1. The kernels

Imaginary (odd) and real (even) Gabor kernels, Eq. (3)-(5) of the manuscript:

$$g_{\mathrm{imag}}(x, y) = \exp\!\left(-\frac{x'^2 + \gamma^2 y'^2}{2\sigma^2}\right)\sin\!\left(\frac{2\pi x'}{\lambda}\right),\qquad
x' = x\cos\theta + y\sin\theta,\; y' = -x\sin\theta + y\cos\theta$$

The real kernel uses cos instead of sin.

**Discretization** (`revision_dsp/rev/kernels.py`, identical to `src/gabor_core.py`):
- The kernel is sampled on the integer grid x, y ∈ [−h, h], with h = k//2, x the column and y the row.
- It is centred at (0, 0), truncated to k × k, and not normalized.
- σ = 0.56 λ and γ = 0.5.
- θ = i·180°/N for i = 0, …, N−1.
- θ is the direction along which the carrier varies, that is, the normal of the edge that the kernel detects.

**When does the window contain a carrier side lobe?** Along x′, sin(2πx′/λ) changes sign at x′ = λ/2. The window therefore contains a second lobe of opposite sign only if h > λ/2, that is, h/λ > 0.5.
- At h/λ = 0.5 (k5 λ4) the samples at x = ±2 are sin(π) = 0.
- At h/λ < 0.5 (k9 λ9: 4/9 = 0.44) the window ends before the first zero crossing.

Centre row of the imaginary kernel at θ = 0 (`mechanism/kernels.csv`):

| k | λ | h/λ | Centre row | Carrier side-lobe ratio |
|---|---|---|---|---|
| 5 | 3 | 0.67 | +0.426 −0.725 0 +0.725 −0.426 | 0.588 |
| 5 | 4 | 0.50 | 0 −0.905 0 +0.905 0 | 0 |
| 7 | 4 | 0.75 | +0.408 0 −0.905 0 +0.905 0 −0.408 | 0.451 |
| 7 | 9 | 0.33 | −0.725 −0.910 −0.630 0 +0.630 +0.910 +0.725 | 0 |
| 9 | 9 | 0.44 | −0.250 −0.725 −0.910 −0.630 0 +0.630 +0.910 +0.725 +0.250 | 0 |

The submitted configuration (k5 λ4) and the configuration selected in the revision (k9 λ9) both have no carrier side lobe.

---

## 2. Step response after |·| and the maximum over orientations

The table below is for a synthetic step edge, after the absolute value (Stage 4) and the maximum over N = 8 orientations (Stage 5). Values are relative to the peak. The width is that of the band above 50% of the maximum (`mechanism/step_profiles.csv`).

| k, λ | Edge normal | E at 1 px | E at 2 px | Secondary maxima | Width before ODPS | Width after ODPS |
|---|---|---|---|---|---|---|
| k5 λ3 | 0° | 0.874 | 0.500 | 1.0 at ±1.5 px | 4.0 px | 2.0 px |
| k5 λ3 | 22.5° | 0.651 | 0.396 | none | 1.38 px | 1.48 px |
| k5 λ3 | 45° | 0.498 | 0.342 | none | 0.86 px | 4.76 px |
| k5 λ4 | 0° | 0.599 | 0.099 | none | 2.0 px | 2.0 px |
| k5 λ4 | 22.5° | 0.685 | 0.290 | none | 2.0 px | 2.19 px |
| k5 λ4 | 45° | 0.636 | 0.336 | none | 2.57 px | 1.71 px |
| k9 λ9 | 0° | 0.875 | 0.571 | none | 4.0 px | 4.0 px |
| k9 λ9 | 22.5° | 0.864 | 0.572 | none | 4.52 px | 4.0 px |
| k9 λ9 | 45° | 0.848 | 0.513 | none | 4.24 px | 4.24 px |

**Without a carrier side lobe (h/λ ≤ 0.5).**
- The response is a single ridge with no secondary maximum.
- The ridge widens on oblique edges because of the maximum across orientations.
- At k9 λ9 it is about 4 px wide. ODPS trims its tails, but leaves a band of about 4 px.
- The one-pixel line seen in evaluation comes from the thinning step of the evaluation protocol, not from ODPS.

**With a carrier side lobe (k5 λ3, normal 0°).**
- The two edge pixels (±0.5 px) are at 0.75 of the maximum, and the maxima lie at ±1.5 px.
- ODPS keeps the two maxima and removes the edge pixels, leaving a double line about 1.5 px from the edge.
- On oblique edges there is no secondary maximum.

**Conclusion.**
- "Double-peak suppression" does not describe what ODPS does in any regime tested.
- ODPS is a directional thinning step along the normal given by the orientation argmax.

---

## 3. ODPS as implemented

For each pixel p, let θ\*(p) be the argmax orientation from Stage 5 and n = (cos θ\*, sin θ\*). ODPS keeps a pixel when it is not smaller than its two neighbours along the normal:

$$E_{\mathrm{ODPS}}(p) = \begin{cases}
E(p) & \text{if } E(p) \ge E(p + d\mathbf{n}) \text{ and } E(p) \ge E(p - d\mathbf{n}) \\
0 & \text{otherwise}
\end{cases}$$

Implementation (`revision_dsp/rev/nms.py`; the same as `src/nms_odps.py`, checked by selftest T3):
- **Sampling: nearest.**
  - The offsets are `np.round(d·cos θ)` and `np.round(d·sin θ)`.
  - `np.round` rounds halves to even, so 4.5 becomes 4.
  - The effective distance therefore differs between orientations.
- **Outside the image:** the neighbour is 0.
- **Ties:** kept (≥).
- **d:** λ/2 (the rule asked about in R3.2).

| d | Offsets (dx, dy) for θ = 0°, 22.5°, …, 157.5° | Effective distance (px) |
|---|---|---|
| 2 (k5 λ4) | (2,0) (2,1) (1,1) (1,2) (0,2) (−1,2) (−1,1) (−2,1) | 2, 2.24, 1.41, 2.24, 2, 2.24, 1.41, 2.24 |
| 4.5 (k9 λ9) | (4,0) (4,2) (3,3) (2,4) (0,4) (−2,4) (−3,3) (−4,2) | 4, 4.47, 4.24, 4.47, 4, 4.47, 4.24, 4.47 |

For odd λ, d = λ/2 is rounded. At λ9 the axis offsets are 4, the same as at λ8 (F13).

**Choice of d** (E11, k9, BSDS500 train+val, F18):
- d = λ/2 is the best of the tested d for λ = 3, 4, 5, 6, 8 and 9.
- For λ7 and λ10, a fixed d = 3 is better, by 0.0034 and 0.0016.
- The rule is therefore near-optimal across λ, not exactly optimal.

---

## 4. Effect on the evaluation

**Matching tolerance.** It is 0.0075 × the image diagonal: about 4.3 px on BSDS500 and 11.0 px on BIPED.

**Order of operations in the evaluation.** At each threshold:
1. the map is binarized;
2. the binary map is thinned;
3. the thinned map is matched one-to-one to the thinned ground truth.

**The v2.0.0 argument is withdrawn.** It said that every edge produced "1 TP, 2 FPs" because of side lobes. That argument did not account for the thinning step, and the kernels have no side lobes (Section 2).

**What was measured on the test sets** (E25, F27). Each method was evaluated at its own dataset ODS threshold.
- **BSDS500.**
  - ODPS does not raise precision (−0.0015).
  - It removes the shoulder pixels around a ridge, so a lower threshold (0.20 against 0.23) keeps precision and adds recall (+0.029).
- **UDED.** The trade goes the other way: precision +0.0135, recall −0.0109.
- **Mean matched distance.** It grows by less than 0.1 px on average: +0.070, +0.085 and +0.015 px on BSDS500, BIPED and UDED.
- **Separating the two effects.** This design cannot tell whether the extra distance comes from ODPS moving responses or from the extra recall at the lower threshold.

**Failure case: parallel edges spaced at or below d.**
- ODPS compares each pixel with neighbours about d pixels away. Neighbouring true edges inside that distance are therefore removed.
- Example, BIPED RGB_139 (louvred panels, median edge spacing 5 to 6 px):
  - recall falls from 0.861 to 0.610 after ODPS;
  - precision falls from 0.735 to 0.701.
- This links d = λ/2 to the smallest edge spacing the method can keep.

**ODS, GWi+ODPS minus GWi.** Paired bootstrap 95% CI, at the selected k9 λ9 (E22, F25). The k5 λ4 values are point estimates.

| | BSDS500 | BIPED | UDED |
|---|---|---|---|
| k9 λ9 | +0.0122 [0.0090, 0.0158] | +0.0079 [−0.0076, 0.0203] | −0.0025 [−0.0161, 0.0121] |
| k5 λ4 (submitted, no CI) | +0.0253 | +0.0142 | +0.0377 |

- ODPS improves ODS on BSDS500 only. On BIPED and UDED the CI includes 0.
- The gain is smaller at the selected kernel, because the kernel that makes GWi strongest leaves ODPS less to remove.

---

## 5. Cost

ODPS performs no extra convolution. It does need the argmax over orientations instead of the maximum.

Measured in E24 (one thread, median of 5 runs per image, Intel Core i5-14400, k9 λ9; F28):
- **BSDS500.**
  - Pooling goes from 0.8 to 6.2 ms when the argmax is kept.
  - ODPS itself takes 3.8 ms.
  - The overhead is therefore 9.6 ms over GWi (29.2 → 38.7 ms, +33%).
- **BIPED:** 153.6 → 224.0 ms (+46%).
- **UDED:** 47.6 → 63.4 ms (+33%).
- **Dependence on d:** with nearest sampling, ODPS takes 3.61 to 3.64 ms for d = 1, 2, 3 and 4.5. Its cost does not depend on d.

The v2.0.0 table (ODPS 6.05 ms on BSDS500) came from a single run per image.

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
