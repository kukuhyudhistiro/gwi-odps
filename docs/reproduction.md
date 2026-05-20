# Step-by-Step Reproduction Guide

Complete reproduction of the paper's quantitative and qualitative results.

**Estimated total wall-clock time**: 4-5 hours on a modern CPU.

---

## 0. Prerequisites

1. Python 3.10+ installed
2. Datasets downloaded per [`datasets.md`](datasets.md)
3. Dependencies: `pip install -r requirements.txt`

Verify environment:

```bash
python scripts/00_capture_env.py
```

Logs to `runtime_logs/environment.json` for future reference.

---

## 1. Dataset Density Profiling (~30 seconds)

```bash
python scripts/01_density_profiler.py \
    --data-root ./data \
    --output ./eval_results/density_profile.csv
```

Expected:
```
BSDS500 test: 200 images, mean edge density 6.63% ± 2.03%
BIPED test:    50 images, mean edge density 3.26% ± 1.04%
UDED test:     30 images, mean edge density 6.37% ± 4.32%
```

---

## 2. Run Unified Pipeline (~3-4 hours)

Process all 280 test images with 8 methods using single-thread enforcement:

```bash
python scripts/02_run_unified.py \
    --data-root ./data \
    --output-root ./output \
    --runtime-csv ./runtime_logs/runtime_unified_k5.csv
```

Output structure:
```
output/
├── BSDS500/{Canny,Sobel,LoG,PC,ED,GWC,GWi,GWi_odps}/<id>.png  (1600 PNGs)
├── BIPED/{...}/                                                (400 PNGs)
└── UDED/{...}/                                                 (240 PNGs)
```

CSV `runtime_unified_k5.csv` has 2240 rows (280 images × 8 methods).

Expected GWi+ODPS runtime (k=5):
- BSDS500: 25.89 ± 1.45 ms
- BIPED: 150.75 ± 3.57 ms
- UDED: 40.72 ± 20.52 ms

---

## 3. Evaluate (~30-50 minutes)

```bash
python scripts/04c_evaluate_bsds_v2.py \
    --data-root ./data \
    --output-root ./output \
    --methods Canny Sobel LoG PC ED GWC GWi GWi_odps \
    --results-dir ./eval_results/k5 \
    --n-thresholds 99
```

Expected canonical values (full 200 BSDS500):

| Method | BSDS500 ODS | BIPED ODS | UDED ODS |
|--------|------------:|----------:|---------:|
| Canny | 0.5336 | 0.6406 | 0.6737 |
| Sobel | 0.4643 | 0.5844 | 0.6390 |
| LoG | 0.4706 | 0.5481 | 0.6364 |
| PC | 0.5245 | 0.5688 | 0.5654 |
| ED | 0.3467 | 0.3133 | 0.5376 |
| GWC | 0.3941 | 0.4106 | 0.4668 |
| GWi | 0.4443 | 0.5602 | 0.6072 |
| **GWi+ODPS** | **0.4696** | **0.5744** | **0.6449** |

If values differ by >0.005, investigate single-thread settings, OpenCV version, or dataset placement.

---

## 4. (Optional) Kernel Ablation (~2 hours)

Reproduce the cross-dataset kernel parameter ablation (Table 1-4 in paper):

```bash
python scripts/10_kernel_ablation_multi_dataset.py \
    --data-root ./data \
    --output-csv ./eval_results/k5/ablation_multi_dataset.csv \
    --datasets BSDS500 BIPED UDED
```

Expected: 7 configurations × 3 datasets = 21 evaluations. Best config:
**5×5, λ=4, n=8** with mean ODS = 0.5304.

---

## 5. Generate Figures (~5-10 minutes)

### Figure 1: Pipeline overview

```bash
python scripts/generate_figure_1_pipeline.py \
    --output ./manuscript/figures/figure_1_pipeline.png \
    --stage-image-5 ./output/BSDS500/GWi/3063.png \
    --stage-image-6 ./output/BSDS500/GWi_odps/3063.png
```

Stages 2-4 use built-in synthetic placeholders.

### Figures 2-3: Side-lobe + ODPS schematic

```bash
python scripts/generate_figure_2_3.py
```

Output: `figure_2_sidelobe.png`, `figure_3_odps_schematic.png`

### Figures 4-9: Qualitative + PR curves

```bash
python scripts/06c_generate_final_figures.py \
    --data-root ./data \
    --output-root ./output \
    --pr-curve-dir ./eval_results/k5 \
    --ods-summary ./eval_results/k5/ods_summary.csv \
    --figures-dir ./manuscript/figures
```

Output:
- `figure_4_qualitative_BSDS500.png` (4 cols: 3063, 29030, 36046, 48017)
- `figure_5_pr_curve_BSDS500.png`
- `figure_6_qualitative_BIPED.png` (3 cols: RGB_042, RGB_070, RGB_138)
- `figure_7_pr_curve_BIPED.png`
- `figure_8_qualitative_UDED.png` (3 cols: 05-WIREFRAME-2, 04-0896x4, 28-img_043_SRF_2_HR)
- `figure_9_pr_curve_UDED.png`

---

## Reproducibility Checklist

After completing the pipeline:

- [ ] `eval_results/k5/ods_summary.csv` matches Tables 2, 5, 6 in paper
- [ ] `runtime_logs/runtime_unified_k5.csv` matches Table 7 in paper
- [ ] `eval_results/k5/ablation_multi_dataset.csv` matches Tables 1-4 (ablation)
- [ ] `manuscript/figures/` contains 9 PNG files
- [ ] No errors during evaluation
- [ ] All 280 test images processed (200 BSDS500 + 50 BIPED + 30 UDED)

---

## Troubleshooting

### Edge Drawing produces same output as Sobel

You have `opencv-python` instead of `opencv-contrib-python`. Fix:
```bash
pip uninstall opencv-python opencv-contrib-python
pip install opencv-contrib-python
```

### Wildly different runtime numbers

Check single-thread enforcement:
```python
import cv2, os
print(cv2.getNumThreads())               # Should be 1
print(os.environ.get('OMP_NUM_THREADS')) # Should be 1
```

### ODS differs by > 0.01 from canonical

Most common cause: wrong matching protocol. We use per-annotator
matching following Arbelaez 2011, where a prediction is a TP if it
matches at least one annotator.

### Out of memory on BIPED

BIPED images are 1280×720 (4× pixel count). On <8GB RAM:
```bash
python scripts/02_run_unified.py --datasets BIPED --batch-size 1
```
