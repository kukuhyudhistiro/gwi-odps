# GWi+ODPS: Imaginary-Only Gabor Wavelet with Orientation-Aware Double-Peak Suppression for Edge Detection

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/)
[![Status: Pre-Submission](https://img.shields.io/badge/status-pre--submission-orange.svg)]()

Reference implementation and evaluation pipeline for the paper:

> **"Imaginary-Only Wavelet with Orientation-Aware Double-Peak Suppression for Lightweight Edge Detection"**
> Kukuh Yudhistiro, Ruri Suko Basuki, Nova Rijati
> Universitas Dian Nuswantoro, Semarang, Indonesia

---

## Headline Results (k=5, λ=4, n=8)

The proposed pipeline halves Gabor convolutions (8 vs 16) and introduces ODPS post-processing, evaluated on three benchmarks under the Berkeley protocol with per-annotator matching.

### Accuracy (ODS↑)

| Method | BSDS500 | BIPED v2 | UDED |
|--------|--------:|---------:|-----:|
| GWC (complex Gabor, 16 conv) | 0.3941 | 0.4106 | 0.4668 |
| **GWi (proposed Stages 1-5, 8 conv)** | **0.4443** | **0.5602** | **0.6072** |
| **GWi+ODPS (proposed Stages 1-6)** | **0.4696** | **0.5744** | **0.6449** |
| GWi+ODPS gain over GWC | **+0.0756** | **+0.1638** | **+0.1781** |
| GWi+ODPS gain over GWC (relative) | **+19.2%** | **+39.9%** | **+38.2%** |

### Runtime (per-image, ms, single-thread CPU)

| Method | BSDS500 | BIPED v2 | UDED |
|--------|--------:|---------:|-----:|
| GWC | 24.60 | 143.61 | 38.94 |
| **GWi (Stages 1-5)** | **11.26** | **64.65** | **17.55** |
| **GWi+ODPS (full)** | **25.89** | **150.75** | **40.72** |
| PC (Phase Congruency) | 326.50 | 1749.39 | 469.05 |

- **GWi alone runs 2.18-2.22× faster than GWC** across all datasets
- **GWi+ODPS at runtime parity with GWC (within 5%)** while achieving substantially higher ODS
- **GWi+ODPS is 11.5-12.6× faster than Phase Congruency**

### ODPS Ablation (Stage 6 contribution)

| Dataset | GWi (Stages 1-5) | GWi+ODPS (full) | Δ ODS | Δ % |
|---------|------------------:|-----------------:|------:|----:|
| BSDS500 | 0.4443 | 0.4696 | +0.0253 | +5.7% |
| BIPED v2 | 0.5602 | 0.5744 | +0.0142 | +2.5% |
| UDED | 0.6072 | 0.6449 | +0.0377 | +6.2% |

---

## Repository Structure

```
GWi-ODPS/
├── src/                              # Core library modules
│   ├── __init__.py
│   ├── gabor_core.py                 # GWi pipeline (Stages 1-5), k=5 default
│   ├── nms_odps.py                   # ODPS module (Stage 6)
│   ├── baselines.py                  # Canny, Sobel, LoG, PC, ED, GWC
│   ├── preprocessing.py              # Stage 1 utilities
│   ├── edge_eval.py                  # Berkeley evaluation protocol
│   └── dataset_io.py                 # Dataset loaders
│
├── scripts/                          # Reproduction scripts
│   ├── 00_capture_env.py             # Log environment for reproducibility
│   ├── 01_density_profiler.py        # Edge density statistics
│   ├── 02_run_unified.py             # Unified pipeline runner (all methods)
│   ├── 03_analyze_runtime.py         # Runtime aggregation
│   ├── 04c_evaluate_bsds_v2.py       # ODS/OIS/AP computation
│   ├── 05_generate_binary_maps.py    # Optional binary maps for display
│   ├── 06c_generate_final_figures.py # Generate Figures 4-9
│   ├── 10_kernel_ablation_multi_dataset.py  # Kernel parameter ablation
│   ├── generate_figure_1_pipeline.py # Figure 1 (pipeline overview)
│   └── generate_figure_2_3.py        # Figures 2-3 (side-lobe + ODPS schematic)
│
├── data/                             # Dataset placement (gitignored, see docs/datasets.md)
│
├── eval_results/                     # Pre-computed evaluation results
│   └── k5/                           # Canonical k=5 baseline results
│       ├── ods_summary.csv           # ODS/OIS/AP for all methods × datasets
│       └── ablation_multi_dataset.csv  # Kernel parameter ablation
│
├── runtime_logs/                     # Pre-computed runtime CSVs
│   └── runtime_unified_k5.csv        # 2240 rows: dataset × method × image
│
├── manuscript/                       # Paper artifacts
│   ├── sections/                     # Section drafts (Markdown)
│   ├── tables/                       # Tables in Markdown + LaTeX
│   └── figures/                      # Pre-generated figures (placeholder; regenerate locally)
│
├── docs/                             # Documentation
│   ├── datasets.md                   # How to obtain BSDS500/BIPED/UDED
│   ├── reproduction.md               # Step-by-step reproduction guide
│   ├── benchmarks.md                 # Hardware and timing notes
│   ├── ODPS_derivation.md            # Mathematical derivation of ODPS
│   └── kernel_ablation.md            # Kernel parameter selection rationale
│
├── tests/                            # Unit tests
│
├── requirements.txt                  # Python dependencies
├── setup.py                          # Optional package install
├── LICENSE                           # MIT License
├── CITATION.cff                      # Citation metadata
├── CHANGELOG.md                      # Version history
├── .gitignore
└── README.md                         # This file
```

---

## Installation

### Requirements
- Python 3.10+
- ~3 GB disk for datasets + ~500 MB for evaluation outputs

### Setup

```bash
git clone [https://github.com/kukuhyudhistiro/gwi-odps].git
cd GWi-ODPS

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Verify Installation

```bash
python -c "from src.gabor_core import GaborParams; p = GaborParams(); assert p.ksize == 5; print('OK')"
python -c "from src.nms_odps import odps; print('ODPS module OK')"
```

---

## Quick Start

### Single Image Inference

```python
import cv2
import numpy as np
from src.gabor_core import GaborParams, GWiFilterBank
from src.nms_odps import odps

# Default GaborParams: k=5, λ=4, σ=2.24, γ=0.5, n=8 orientations
params = GaborParams()
bank = GWiFilterBank(params)

# Load and preprocess
img = cv2.imread("input.jpg", cv2.IMREAD_GRAYSCALE)
img_norm = cv2.equalizeHist(img).astype(np.float64) / 255.0

# Run pipeline (Stages 3-5: convolve, |·|, max-pool)
per_orient = [np.abs(cv2.filter2D(img_norm, cv2.CV_64F, k)) for k in bank.kernels]
stacked = np.stack(per_orient, axis=0)
magnitude = stacked.max(axis=0)
orient_idx = stacked.argmax(axis=0).astype(np.int32)

# Stage 6: ODPS
final = odps(magnitude, orient_idx, n_orientations=8, d=2)

cv2.imwrite("output.png", (final / final.max() * 255).astype(np.uint8))
```

### Reproduce Paper Results

```bash
# Download datasets first per docs/datasets.md, then:

# 1. Run all methods on all datasets (~3-4 hours, single-thread)
python scripts/02_run_unified.py \
    --data-root ./data \
    --output-root ./output \
    --runtime-csv ./runtime_logs/runtime_unified_k5.csv

# 2. Evaluate (~30-50 minutes)
python scripts/04c_evaluate_bsds_v2.py \
    --data-root ./data \
    --output-root ./output \
    --methods Canny Sobel LoG PC ED GWC GWi GWi_odps \
    --results-dir ./eval_results/k5

# 3. Generate figures
python scripts/generate_figure_2_3.py
python scripts/06c_generate_final_figures.py \
    --data-root ./data \
    --output-root ./output \
    --pr-curve-dir ./eval_results/k5 \
    --ods-summary ./eval_results/k5/ods_summary.csv \
    --figures-dir ./manuscript/figures
```

See [`docs/reproduction.md`](docs/reproduction.md) for detailed steps.

---

## Kernel Parameters (Cross-Dataset Ablation)

The selected configuration **k=5, λ=4, σ=2.24, γ=0.5, n=8 orientations** is based on systematic ablation across three datasets (full results in `eval_results/k5/ablation_multi_dataset.csv`):

| Config | BSDS500 ODS | BIPED ODS | UDED ODS | Mean ODS |
|--------|------------:|----------:|---------:|---------:|
| 5×5, λ=3 | 0.3876 | 0.4691 | 0.5457 | 0.4675 |
| **5×5, λ=4**  | **0.4351** | **0.5539** | **0.6021** | **0.5304** |
| 7×7, λ=4 | 0.3955 | 0.4693 | 0.5473 | 0.4707 |
| 7×7, λ=5 | 0.4353 | 0.5462 | 0.6076 | 0.5297 |
| 9×9, λ=4 | 0.3847 | 0.4441 | 0.5329 | 0.4539 |

**5×5 with λ=4 is selected** as it achieves the highest mean ODS (0.5304) while being 29-39% faster than the second-best 7×7, λ=5 configuration. See [`docs/kernel_ablation.md`](docs/kernel_ablation.md) for full discussion.

---

## Method Summary

The GWi+ODPS pipeline consists of six stages:

1. **Preprocessing** — BT.601 grayscale + histogram equalization + normalize to [0,1]
2. **Kernel construction** — 8 imaginary Gabor kernels at 22.5° spacing (k=5, λ=4, σ=2.24, γ=0.5)
3. **Convolution** — Zero-padded 2D convolution via `cv2.filter2D`
4. **Magnitude extraction** — Absolute value (replaces sqrt of complex Gabor)
5. **Cross-orientation max-pooling** — Per-pixel max across orientations, argmax preserved
6. **ODPS** — Orientation-aware non-maximum suppression along edge-normal direction (d=2 pixels)

**Key claim**: The imaginary component of the Gabor wavelet alone is sufficient for edge-based boundary detection. ODPS suppresses the ±λ/2 side-lobe artifact at no convolution cost.

See [`docs/ODPS_derivation.md`](docs/ODPS_derivation.md) for the mathematical derivation.

---

## Reproducibility

### Hardware Reference

- **CPU**: Intel Core i5-14400 (10P + 4E cores, 16 threads)
- **RAM**: 16 GB DDR4
- **OS**: Windows 11
- **Threading**: Single-thread enforced via `cv2.setNumThreads(1)`, `OMP_NUM_THREADS=1`, `MKL_NUM_THREADS=1`

Runtime measurements reproducible within ±10% on equivalent hardware.

### Software Stack

- Python 3.13, NumPy 2.2.6, OpenCV 4.13.0 (with `opencv-contrib-python` for Edge Drawing)
- SciPy 1.5.3, scikit-image 0.21, matplotlib 3.8+, pandas 2.0+

See [`requirements.txt`](requirements.txt).

### Deterministic Execution

The pipeline uses no random sampling. All operations are deterministic given the same inputs. Threshold sweeps use 33 uniformly distributed thresholds in [1/34, 33/34].

---

## Citation

```bibtex
@article{yudhistiro2026gwi_odps,
  title   = {Imaginary-Only Wavelet with
             Orientation-Aware Double-Peak Suppression for Edge Detection},
  author  = {Yudhistiro, Kukuh and Rijati, Nova and Basuki, Ruri Suko},
  journal = {[Submitted]},
  year    = {2026},
  note    = {Code: \url{https://github.com/kukuhyudhistiro/gwi-odps}
}
```

See [`CITATION.cff`](CITATION.cff) for machine-readable metadata.

---

## Datasets

| Dataset | Source | Size | Annotation |
|---------|--------|-----:|------------|
| BSDS500 | [Berkeley Vision Group](https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/resources.html) | 200 test | 5–6 annotators |
| BIPED v2 | [MBIPED](https://github.com/xavysp/MBIPED) | 50 test (1280×720) | 1 expert |
| UDED | [UDED](https://github.com/xavysp/UDED) | 30 cross-domain | 1 annotator |

See [`docs/datasets.md`](docs/datasets.md) for download instructions and directory layout.

---

## License

This code is released under the MIT License. See [`LICENSE`](LICENSE).

Datasets used (BSDS500, BIPED, UDED) are subject to their own licenses.

---

## Contact

- **Email**: kukuh.yudhistiro@unmer.ac.id
- **Affiliation**: Universitas Dian Nuswantoro, Semarang, Indonesia
