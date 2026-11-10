# GWi+ODPS: Imaginary-Only Gabor Wavelet with Orientation-Aware Double-Peak Suppression for Edge Detection

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status: Under revision](https://img.shields.io/badge/status-under%20revision-orange.svg)]()

Reference implementation and evaluation pipeline for the paper:

> **"Imaginary-Only Wavelet with Orientation-Aware Double-Peak Suppression for Lightweight Edge Detection"**
> Kukuh Yudhistiro¹, Puput Dani Prasetyo Adi², Ruri Suko Basuki¹, Nova Rijati¹
> ¹ Faculty of Computer Science, Universitas Dian Nuswantoro, Semarang, Indonesia
> ² National Research and Innovation Agency (BRIN), Bandung, Indonesia

**Version 3.0.0 (first revision, manuscript DSP-D-26-02462).**
- All numbers on this page come from [`revision_dsp/`](revision_dsp/README.md). They were computed under a protocol that was pre-registered with git tags before the test sets were opened.
- The submitted code in `src/` and `scripts/` is unchanged (tag `dsp-submitted-v1`, commit `91b4f83`).
- The revision code reproduces the submitted GWi, GWi+ODPS, GWC and Sobel numbers to four decimals.
- LoG, PC and ED differ, because the revision runs them as the manuscript describes them.
- Several claims of the submission are not supported by the revision. They are listed under [What the revision found](#what-the-revision-found).
- The numbers of the submitted version (v2.0.0) are kept in the folded section [Submitted version](#submitted-version-v200) at the end of this page.

---

## Results of the revision

**Configuration (selected on non-test data, BSDS500 train+val and BIPED train):**
- k = 9, λ = 9, d = λ/2 = 4.5, N = 8, σ/λ = 0.56, γ = 0.5.

**Protocol (as in the manuscript):**
- Preprocessing: BT.601 grayscale, histogram equalization, /255.
- Borders: zero padding for the Gabor methods, OpenCV reflect-101 for the other baselines.
- Maps: per-image min-max normalization.
- Evaluation:
  - 99 thresholds;
  - thinning of prediction and ground truth;
  - greedy one-to-one matching within 0.0075 × image diagonal.
- Metrics: ODS; OIS and AP are computed by dataset-level accumulation.
- This evaluator is not the official BSDS benchmark code, so published values of other methods are not comparable with these numbers.

### Accuracy on the test sets, ODS / AP

The test sets (BSDS500 test 200 images, BIPED test 50, UDED 30) were opened once, after the freeze.

| Method | BSDS500 | BIPED | UDED |
|---|---|---|---|
| GWi k9 λ9 | 0.4998 / 0.3739 | 0.6202 / 0.5808 | 0.6476 / 0.5508 |
| **GWi+ODPS k9 λ9** | **0.5120 / 0.3970** | **0.6281 / 0.5922** | **0.6451 / 0.5524** |
| GWC k9 λ9 (raw real kernel, as in the manuscript) | 0.3176 / 0.1492 | 0.4111 / 0.2318 | 0.3753 / 0.1813 |
| GWC k9 λ9, zero-DC real kernel (analysis for R1.5) | 0.4836 / 0.3074 | 0.5811 / 0.4758 | 0.5634 / 0.3864 |
| GWi k5 λ4 (submitted configuration) | 0.4443 / 0.3365 | 0.5602 / 0.5086 | 0.6072 / 0.5267 |
| GWi+ODPS k5 λ4 (submitted configuration) | 0.4696 / 0.3860 | 0.5744 / 0.5371 | 0.6449 / 0.6097 |
| GWC k5 λ4 (raw) | 0.3941 / 0.2431 | 0.4106 / 0.2911 | 0.4668 / 0.3126 |
| GWC k5 λ4, zero-DC | 0.4536 / 0.3064 | 0.5525 / 0.4718 | 0.5818 / 0.4315 |
| Gaussian gradient magnitude σ 1.4 (the "Canny" row of the submission) | **0.5334 / 0.4920** | **0.6407 / 0.6845** | **0.6734 / 0.6784** |
| Sobel 3×3 | 0.4643 / 0.4058 | 0.5844 / 0.6096 | 0.6390 / 0.6405 |
| LoG 7×7, σ 1.4 | 0.4524 / 0.3710 | 0.5299 / 0.5180 | 0.6219 / 0.6250 |
| Phase congruency (phasepack) | 0.5089 / 0.4499 | 0.5004 / 0.4570 | 0.5853 / 0.5199 |
| Canny, OpenCV 50/150 (binary) | 0.3353 / n/c | 0.3460 / n/c | 0.5568 / n/c |
| Edge Drawing, OpenCV defaults (binary) | 0.3508 / n/c | 0.3275 / n/c | 0.5540 / n/c |

n/c: binary map with a single operating point, so its AP is not comparable with the AP of the soft maps.
The Gaussian gradient magnitude has the highest ODS, OIS and AP on all three test sets.
OIS, the submitted OIS/AP definitions (`*_legacy`) and the BSDS benchmark AP are in [`revision_dsp/results/test/summary.csv`](revision_dsp/results/test/summary.csv).

### Paired statistics

Method:
- paired bootstrap over images, 2000 resamples, 95% CI of ΔODS;
- Wilcoxon signed-rank test on per-image F, Holm-adjusted over 9 tests.

The pre-registered rule allows the word "improves" only when the CI excludes 0.

| Pair (k9 λ9) | BSDS500 | BIPED | UDED |
|---|---|---|---|
| GWi+ODPS − GWi | +0.0122 [0.0090, 0.0158] | +0.0079 [−0.0076, 0.0203] | −0.0025 [−0.0161, 0.0121] |
| GWi − GWC (raw) | +0.1822 [0.1677, 0.1962] | +0.2091 [0.1725, 0.2455] | +0.2723 [0.2254, 0.3051] |
| GWi − GWC (zero-DC), outside the Holm family | +0.0161 [0.0117, 0.0204] | +0.0391 [0.0171, 0.0671] | +0.0842 [0.0548, 0.1133] |

ODPS improves ODS on BSDS500 only. On BIPED and UDED the CI includes 0.
Source: [`revision_dsp/results/stats/pairs.csv`](revision_dsp/results/stats/pairs.csv).

### Learned detectors, same evaluator, without NMS

Official repositories and weights were used for all three detectors.

| Method (trained on) | BSDS500 ODS | BIPED ODS | UDED ODS | CPU ms per image, 1 thread (BSDS500 / BIPED / UDED) |
|---|---|---|---|---|
| TEED (BIPED) | 0.612 | 0.786 (in-domain) | 0.789 | 209 / 579 / 256 |
| LDC (BIPED) | 0.667 | 0.825 (in-domain) | 0.762 | 170 / 765 / 232 |
| PiDiNet (BSDS500) | 0.751 (in-domain) | 0.690 | 0.558 | 589 / 3880 / 979 |
| GWi+ODPS k9 λ9 | 0.512 | 0.628 | 0.645 | 42 / 245 / 69 |
| Gaussian gradient σ 1.4 | 0.533 | 0.641 | 0.673 | 10.5 / 63 / 16.5 |

How the CPU times were measured:
- In this table, the times include preprocessing.
- For the learned detectors, preprocessing also includes reading the image file.
- The learned detectors run in PyTorch, the training-free methods in OpenCV/NumPy.

Sources: [`revision_dsp/results/external/`](revision_dsp/results/external/), with `models.yaml` for commits, weights and licences.

### Runtime (ms per image, filter + pool + ODPS, preprocessing excluded)

Measurement conditions:
- Intel Core i5-14400, Windows 11, Python 3.13.13, OpenCV 4.13.0.
- One thread, 3 warm-up images, median of 5 runs per image, mean over the images.

| Method | BSDS500 | BIPED | UDED |
|---|---|---|---|
| GWi k9 λ9 | 29.2 | 153.6 | 47.6 |
| GWi+ODPS k9 λ9 | 38.7 | 224.0 | 63.4 |
| GWC k9 λ9 (raw) | 60.3 | 321.2 | 95.6 |
| GWi k5 λ4 | 11.2 | 64.6 | 16.9 |
| GWi+ODPS k5 λ4 | 21.5 | 138.2 | 34.0 |
| GWC k5 λ4 (raw) | 24.8 | 147.9 | 38.8 |
| Gaussian gradient σ 1.4 | 7.0 | 42.0 | 11.2 |
| Phase congruency | 328.3 | 1783.9 | 474.6 |
| Preprocessing (all methods) | 3.5 | 20.5 | 5.3 |

**Overstated baseline times.** For Sobel and the Gaussian gradient, the times above include a direction quantization (pool column) that these methods do not use. Their filtering alone takes 1.7 and 2.5 ms on BSDS500.

Source: [`revision_dsp/results/runtime/summary.csv`](revision_dsp/results/runtime/summary.csv).

---

## What the revision found

The full ledger, with every finding and limitation, is [`revision_dsp/FINDINGS.md`](revision_dsp/FINDINGS.md). In short:

- **Kernel selection.**
  - The kernel tables of the submission (Tables 1-4) were computed on the test sets.
  - The revision selects on non-test data only. On that data, k5 λ4 ranks 12th of 18 candidates by mean ODS of GWi.
  - The selection criterion (mean ODS of GWi+ODPS) was adopted after the first results were seen. This amendment is recorded in [`revision_dsp/CHANGELOG.md`](revision_dsp/CHANGELOG.md).
  - On UDED, which has no non-test split, the new kernel does not raise the ODS of GWi+ODPS (+0.0002).
- **ODPS mechanism.**
  - The submitted mechanism, "suppression of side lobes at ±λ/2", is not supported. At k5 λ4 and at k9 λ9 the imaginary kernel has no carrier side lobe in its window.
  - ODPS acts as directional thinning along the edge normal.
  - Where side lobes do exist (k5 λ3), ODPS keeps the two side peaks of a step edge and removes the edge pixels.
  - ODPS removes true edges when parallel edges are spaced at or below d.
  - See [`docs/ODPS_derivation.md`](docs/ODPS_derivation.md).
- **ODPS gain.** ODPS improves ODS on BSDS500 only. On BIPED and UDED the CI includes 0, and on UDED the point estimate is negative.
- **GWi vs GWC.**
  - Most of the submitted GWi > GWC gap comes from the DC response of the raw real kernel.
  - Against a zero-DC GWC, GWi at k9 λ9 stays above on all three test sets, with CIs that exclude 0.
  - At k5 λ4, the zero-DC GWC is above GWi on BSDS500 (point estimate, no CI).
- **Cost.**
  - GWi halves the filtering time of GWC: 2.1× at k9 λ9 and 2.3× at k5 λ4.
  - For the full pipeline, GWi+ODPS is 1.56× faster than GWC at k9 λ9, but only 1.15× faster at the submitted k5 λ4.
  - The Gaussian gradient magnitude is about 5.5× faster than GWi+ODPS, and its ODS is higher on all three test sets.
- **Classical baselines.**
  - The Gaussian gradient magnitude σ 1.4 is above every Gabor variant on all three test sets.
  - The Gabor methods use zero padding and the other baselines reflect-101. This handicaps the Gabor methods by an amount that was not measured on test.
- **Histogram equalization.**
  - Removing HE raises the ODS of GWi and GWi+ODPS on all three test sets.
  - Removing /255 changes nothing.
  - The protocol keeps HE, as frozen.
- **Learned detectors.**
  - The best learned detector is 0.14 to 0.24 ODS above GWi+ODPS.
  - GWi+ODPS is 2.4 to 16× faster on one CPU thread. It has no cost advantage over the Gaussian gradient.
  - No method published in 2024 or later was evaluated.

---

## Pre-registration and tags

| Tag | Commit | Content |
|---|---|---|
| `dsp-submitted-v1` | `91b4f83` | Code at submission |
| `prereg-dsp-2026-11-08` | `749931b` | Protocol v2, before any run on real data |
| `prereg-dsp-amend1-2026-11-09` | `2df5279` | Amendment 1: candidate grid k ∈ {5, 7, 9} × λ ∈ {3..8} |
| `hyp-dsp-2026-11-09` | `d5fa797` | Hypotheses H1/H2 (`revision_dsp/HYPOTHESES.md`) |
| `prereg-dsp-amend2-2026-11-09` | `31494a6` | Amendment 2: selection by mean ODS of GWi+ODPS (post hoc, disclosed) |
| `freeze-2026-11-10` | `7ae7ba5` | Frozen configuration and method list, before the test sets were opened |
| `numbers-frozen-2026-11-10` | `ed93f8c` | All results of the revision (E20-E26); `revision_dsp/results/TABLES.md` |
| `v3.0.0-dsp-r1` | this release | Revised code, results and documentation |

The tags were created in a local repository and published together with this release. Their dates are those of the local machine, so they cannot be verified independently. The order of the commits and the content of each tag can.

The timing of every stage is recorded in [`revision_dsp/PROCESS_LOG.md`](revision_dsp/PROCESS_LOG.md).

---

## Reproduce the revision

```bash
git clone https://github.com/kukuhyudhistiro/gwi-odps.git
cd gwi-odps
git checkout v3.0.0-dsp-r1
cd revision_dsp
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip uninstall -y opencv-python; pip install -r requirements.txt
bash run_all.sh smoke                                  # synthetic data, every script must finish
bash run_all.sh check                                  # environment, equivalence with src/, mechanism
```

The full order of stages and their outputs are in [`revision_dsp/README.md`](revision_dsp/README.md) and [`docs/reproduction.md`](docs/reproduction.md).

Results are cached. A stage recomputes only the files that are missing.

Datasets go in `data/`, as described in [`docs/datasets.md`](docs/datasets.md). The revision also needs BSDS500 train and val, and BIPED train.

---

## Quick start (revised configuration)

Run from the repository root:

```python
import sys
sys.path.insert(0, "revision_dsp")

import cv2
import numpy as np
from rev.preproc import load_and_preprocess
from rev.methods import compute

img = load_and_preprocess("input.jpg", mode="he")      # BT.601 grayscale, HE, /255
spec = {"family": "gwi", "k": 9, "lam": 9, "N": 8, "sigma_ratio": 0.56, "gamma": 0.5,
        "nms": {"d": 4.5, "mode": "nearest", "outside": "zero"}}   # ODPS, d = lambda/2
edge, _ = compute(img, spec, border="constant")         # zero padding, as in the manuscript

edge = (edge - edge.min()) / (edge.max() - edge.min() + 1e-12)
cv2.imwrite("edges.png", (edge * 255).astype(np.uint8))
```

Remove the `"nms"` entry to get GWi without ODPS.

The submitted library in `src/` still defaults to k5 λ4 with d = 2. It is kept unchanged for comparison.

---

## Repository structure

```
gwi-odps/
├── src/, scripts/        code at submission (commit 91b4f83), unchanged
├── eval_results/k5/      results at submission, unchanged
├── runtime_logs/         runtime logs at submission, unchanged
├── manuscript/           figures of the submission
├── docs/                 datasets, reproduction, ODPS derivation (revised), benchmarks
├── data/                 BSDS500/, BIPED/, UDED/ (not in git)
└── revision_dsp/         code, protocol and results of the revision
    ├── config.yaml       pre-registered protocol
    ├── HYPOTHESES.md     pre-registered hypotheses
    ├── CHANGELOG.md      protocol changes after pre-registration, with reasons
    ├── FINDINGS.md       findings and limitations, including withdrawn claims
    ├── PROCESS_LOG.md    timing of every stage
    ├── rev/              library: kernels, methods, ODPS, evaluator, statistics
    ├── scripts/          one script per reviewer comment or group of comments
    ├── tools/            smoke-test data, process log, learned-detector inference
    └── results/          CSV/JSON results, TABLES.md, figures
```

---

## Method summary

The GWi+ODPS pipeline consists of six stages:

1. **Preprocessing.** BT.601 grayscale, histogram equalization, /255.
2. **Kernel construction.** N imaginary (odd) Gabor kernels, one per orientation θ = i·180°/N.
   - Each kernel is sampled on the centred integer grid, truncated to k × k, with no normalization.
   - θ is the direction along which the carrier varies, that is, the edge normal.
3. **Convolution.** `cv2.filter2D` with zero padding.
4. **Magnitude.** Absolute value of each response.
5. **Pooling.** Maximum across orientations. The argmax θ* is kept for ODPS.
6. **ODPS.** A pixel is kept if its value is at least that of both neighbours at ±d·n, where n = (cos θ*, sin θ*).
   - The neighbours are sampled at the nearest pixel (`np.round`); neighbours outside the image are 0, and ties are kept.
   - d = λ/2.

The derivation, the corrected mechanism and the measured cost are in [`docs/ODPS_derivation.md`](docs/ODPS_derivation.md).

---

## Software and hardware of the revision

- Intel Core i5-14400 (10 cores, 16 threads), Windows 11.
- Python 3.13.13, NumPy 2.2.6, SciPy 1.15.3, OpenCV 4.13.0 (`opencv-contrib-python` for Edge Drawing), scikit-image 0.25.2, Pillow 12.2.0, matplotlib 3.10.9, phasepack 1.5.
- Learned detectors: a separate PyTorch 2.15.0 CPU environment (`revision_dsp/tools/external/`).
- Full lists:
  - [`revision_dsp/results/env/pip_freeze.txt`](revision_dsp/results/env/pip_freeze.txt);
  - [`revision_dsp/requirements-lock.txt`](revision_dsp/requirements-lock.txt).

The pipeline is deterministic. The bootstrap uses a fixed seed (20261107).

---

## Citation

```bibtex
@article{yudhistiro2026gwi_odps,
  title   = {Imaginary-Only Wavelet with Orientation-Aware
             Double-Peak Suppression for Lightweight Edge Detection},
  author  = {Yudhistiro, Kukuh and Adi, Puput Dani Prasetyo and Basuki, Ruri Suko and Rijati, Nova},
  journal = {[Under revision]},
  year    = {2026},
  note    = {Code: \url{https://github.com/kukuhyudhistiro/gwi-odps}}
}
```

See [`CITATION.cff`](CITATION.cff) for machine-readable metadata.

---

## Datasets

| Dataset | Source | Size | Annotation |
|---------|--------|-----:|------------|
| BSDS500 | [Berkeley Vision Group](https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/resources.html) | 200 test (+ 300 train+val for selection) | 5–6 annotators |
| BIPED v2 | [MBIPED](https://github.com/xavysp/MBIPED) | 50 test (+ 200 train for selection), 1280×720 | 1 expert |
| UDED | [UDED](https://github.com/xavysp/UDED) | 30 cross-domain | 1 annotator |

See [`docs/datasets.md`](docs/datasets.md) for download instructions and directory layout.

---

## License

This code is released under the MIT License. See [`LICENSE`](LICENSE).

Third-party material:
- The datasets (BSDS500, BIPED, UDED) are subject to their own licences.
- The weights of the learned detectors are not included in this repository:
  - TEED: MIT;
  - LDC: the repository has no licence file;
  - PiDiNet: research use only.

  Use their official repositories, listed in `revision_dsp/results/external/models.yaml`.

---

## Contact

- **Corresponding author**: Kukuh Yudhistiro, kukuh.yudhistiro@unmer.ac.id
- **Affiliation**: Faculty of Computer Science, Universitas Dian Nuswantoro, Semarang, Indonesia

---

## Submitted version (v2.0.0)

<details>
<summary>Numbers and claims of the submitted version (tag <code>dsp-submitted-v1</code>). Several are superseded; read the notes first.</summary>

**Notes.** These tables are kept unchanged for comparison.
- The kernel table was computed on the test sets, and k5 λ4 was selected from it.
- The row labelled "Canny" is a Gaussian gradient magnitude, σ 1.4, without NMS or hysteresis.
- LoG, PC and ED were run with settings that differ from the manuscript description. In v3.0.0 they are run as described.
- The kernel table used a global normalization and 33 thresholds. The main tables used per-image normalization and 99 thresholds.
- The software versions listed in v2.0.0 (SciPy 1.5.3, scikit-image 0.21 with Python 3.13) cannot be installed together.
- Runtimes were measured once per image, without repetitions.
- Claims that do not hold in v3.0.0:
  - "ODPS suppresses the ±λ/2 side-lobe artifact";
  - "the imaginary component alone is sufficient" (most of the gap is the DC response of the raw real kernel);
  - "GWi+ODPS at runtime parity with GWC while achieving substantially higher ODS", against a GWC that carries a DC term.

### Accuracy (ODS), k=5, λ=4, n=8

| Method | BSDS500 | BIPED v2 | UDED |
|--------|--------:|---------:|-----:|
| GWC (complex Gabor, 16 conv) | 0.3941 | 0.4106 | 0.4668 |
| GWi (Stages 1-5, 8 conv) | 0.4443 | 0.5602 | 0.6072 |
| GWi+ODPS (Stages 1-6) | 0.4696 | 0.5744 | 0.6449 |

The revision reproduces these three rows exactly (`revision_dsp/results/test/legacy_check.csv`).

### Runtime (per image, ms, single-thread CPU, one run per image)

| Method | BSDS500 | BIPED v2 | UDED |
|--------|--------:|---------:|-----:|
| GWC | 24.60 | 143.61 | 38.94 |
| GWi (Stages 1-5) | 11.26 | 64.65 | 17.55 |
| GWi+ODPS (full) | 25.89 | 150.75 | 40.72 |
| PC (Phase Congruency) | 326.50 | 1749.39 | 469.05 |

### ODPS ablation

| Dataset | GWi | GWi+ODPS | Δ ODS |
|---------|----:|---------:|------:|
| BSDS500 | 0.4443 | 0.4696 | +0.0253 |
| BIPED v2 | 0.5602 | 0.5744 | +0.0142 |
| UDED | 0.6072 | 0.6449 | +0.0377 |

### Kernel table (computed on the test sets)

| Config | BSDS500 ODS | BIPED ODS | UDED ODS | Mean ODS |
|--------|------------:|----------:|---------:|---------:|
| 5×5, λ=3 | 0.3876 | 0.4691 | 0.5457 | 0.4675 |
| 5×5, λ=4 | 0.4351 | 0.5539 | 0.6021 | 0.5304 |
| 7×7, λ=4 | 0.3955 | 0.4693 | 0.5473 | 0.4707 |
| 7×7, λ=5 | 0.4353 | 0.5462 | 0.6076 | 0.5297 |
| 9×9, λ=4 | 0.3847 | 0.4441 | 0.5329 | 0.4539 |

To run the submitted pipeline, check out `dsp-submitted-v1` and follow the v2.0.0 section of [`docs/reproduction.md`](docs/reproduction.md).

</details>
