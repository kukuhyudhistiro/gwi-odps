# Step-by-Step Reproduction Guide

This guide has two parts:
- **Part A, version 3.0.0 (first revision).** The numbers of the revised manuscript and of `README.md` come from here.
- **Part B, version 2.0.0 (submitted version).** Kept unchanged so that the submitted numbers can still be reproduced.

---

## A. Revision (v3.0.0, `revision_dsp/`)

Commands run from `revision_dsp/`. The order of stages, the reviewer comment each one answers, and its outputs are listed in [`revision_dsp/README.md`](../revision_dsp/README.md) §4. The protocol is in `revision_dsp/config.yaml`.

### A.0 Environment

```bash
cd revision_dsp
python -m venv .venv && source .venv/bin/activate      # Windows (Git Bash): source .venv/Scripts/activate
pip uninstall -y opencv-python; pip install -r requirements.txt
```

`requirements-lock.txt` and `results/env/pip_freeze.txt` hold the exact versions used:
- Python 3.13.13, NumPy 2.2.6, SciPy 1.15.3;
- OpenCV 4.13.0 (contrib), scikit-image 0.25.2, phasepack 1.5.

Datasets go in `../data/`, see [`datasets.md`](datasets.md). Besides the test splits, the revision needs BSDS500 train and val, and BIPED train.

### A.0b Check the numbers without the datasets

`results/counts/` holds the per-image matching counts of every evaluated map. The stages that aggregate counts read them from this cache, so they run without the images and finish in a few minutes:

```bash
PY=.venv/Scripts/python.exe bash run_all.sh select       # Windows; on Linux/macOS omit PY=...
PY=.venv/Scripts/python.exe bash run_all.sh hypotheses
PY=.venv/Scripts/python.exe bash run_all.sh stats
PY=.venv/Scripts/python.exe bash run_all.sh tables
git status --short results/                              # only results/hypotheses/hypotheses.json changes
```

The one changed file differs only in its `source` field, which records the absolute path of the input file; every number is identical (checked on a fresh clone without the datasets).

This recomputes the kernel selection (Table 4, Table S1), the confidence intervals and paired tests (Tables 5-6, Table S2) and `results/TABLES.md` from the released counts. Recomputing the maps and counts themselves needs the datasets (A.1).

### A.1 Stages

How to run a stage:
- `bash run_all.sh <stage>` runs one stage.
- `bash tools/run_logged.sh <id> <stage>` does the same, and also writes the log to `logs_local/` and records the start, end and exit code in `logs_local/runs.csv`.
- On Windows, set the interpreter explicitly: `PY=.venv/Scripts/python.exe bash run_all.sh <stage>`.

Results are cached per method specification, so a stage computes only the files that are missing. To recompute a result, delete its file.

The durations below are those of the revision runs, on an Intel Core i5-14400 with 8 jobs. Single-thread runtime measurement (E24) is the exception: it ran as one job.

| Stage | Command | Output | Duration in the revision |
|---|---|---|---|
| Smoke test (synthetic data) | `bash run_all.sh smoke` | every script finishes | 2 min |
| E00-E02: environment, equivalence with `src/`, mechanism | `bash run_all.sh check` | `results/env/`, `results/selftest/selftest.json` (all PASS), `results/mechanism/` | 6 min |
| E10: kernel selection on BSDS500 train+val and BIPED train | `bash run_all.sh select` | `results/selection/` | about 9.5 h over all rounds (protocol v2 and amendments 1-2) |
| E11: ablations λ × d, N, σ/λ, γ | `bash run_all.sh ablation` | `results/ablation/` | 43 min + 48 min |
| E13: hypotheses H1/H2 | `bash run_all.sh hypotheses` | `results/hypotheses/` | seconds |
| E12: freeze | `bash run_all.sh freeze`, then tag `freeze-2026-11-10` | `results/config_final.yaml` | 3 min |
| E20: test sets, once, with the legacy check | `bash run_all.sh test` | `results/test/summary.csv`, `legacy_check.csv` | 2 h 28 min |
| E21: preprocessing ablation | `bash run_all.sh preproc` | `results/preproc/` | 22 min |
| E22: statistics | `bash run_all.sh stats` | `results/stats/` | 2 min |
| E24: runtime, on an otherwise idle machine | `bash run_all.sh runtime` | `results/runtime/` | 28 min |
| E25: localization and qualitative ODPS | `bash run_all.sh qualitative` | `results/qualitative/` | 2 min |
| E26: tables | `bash run_all.sh tables` | `results/TABLES.md` | seconds |
| Figures | `bash run_all.sh figures` | `results/figures/`, `FIGURES.md` | 1 min |

The test sets are opened only by `test` and the stages after it.

A run with `--limit N` (e.g. `python scripts/10_select_kernel.py --limit 5`) is a quick check. It is cached separately and must not be quoted.

### A.2 Learned detectors (E23)

E23 runs in a separate PyTorch CPU environment, outside the repository. It uses the official repositories and weights of TEED, LDC and PiDiNet. Commits and checkpoints are listed in `results/external/models.yaml`.

The weights are not redistributed (licences: TEED MIT; LDC no licence file; PiDiNet research use only).

Setup of the E23 folder (`EXT`, outside the repository):
- `EXT/.venv-dl/`: a separate environment with the packages of `results/external/requirements-e23.txt` (Python 3.13.13, PyTorch 2.15.0 CPU build, thop).
- `EXT/repos/TEED`, `EXT/repos/LDC`, `EXT/repos/pidinet`: clones of the official repositories at the commits listed in `results/external/models.yaml`. The weights are part of these repositories (paths and SHA-256 in `models.yaml`).
- `EXT/maps/`: written by the run.

```bash
EXT=<E23 folder> bash tools/external/run_e23.sh   # maps, evaluation (scripts/23_eval_external.py --nms), MACs, CPU time
.venv/Scripts/python.exe tools/external/summarize_e23.py --maps <E23 folder>/maps --repos <E23 folder>/repos
```

On Linux or macOS, set `PYD=<E23 folder>/.venv-dl/bin/python` and `PYR=.venv/bin/python` as well.

Outputs:
- `results/external/summary.csv`: ODS, OIS and AP, without and with the NMS of the script.
- `results/external/counts/`.
- `results/external/cost.csv`, `cost/` and `models.yaml`.

The run took 1 h 33 min, plus 29 min for the corrected cost measurement.

### A.3 Checks

- **Selftest.** `results/selftest/selftest.json` has every test at PASS. T0 checks that `rev/legacy.py` still equals `src/`.
- **Legacy check.** `results/test/legacy_check.csv` reproduces the submitted GWi, GWi+ODPS, GWC and Sobel numbers of `eval_results/k5/ods_summary.csv` to four decimals.
- **Traceability.** Every number of the revised manuscript can be traced to a row of `results/TABLES.md`. The tag `numbers-frozen-2026-11-10` marks the result state.

---

## B. Submitted version (v2.0.0)

Check out `dsp-submitted-v1` (commit `91b4f83`) to run exactly the submitted code. The code in `src/` and `scripts/` is the same at `v3.0.0-dsp-r1`.

Notes on the submitted version, from the revision audit (`revision_dsp/FINDINGS.md`):
- **Baseline names and settings.**
  - The "Canny" row is a Gaussian gradient magnitude, σ 1.4, without NMS or hysteresis.
  - LoG uses a Gaussian blur with σ 1.5 followed by `cv2.Laplacian`.
  - ED uses non-default parameters.
- **Kernel ablation (step 4).** It runs on the test sets, with a global normalization and 33 thresholds.
- **Runtimes.** They are a single run per image.

**Estimated total wall-clock time**: 4-5 hours on a modern CPU.

---

### 0. Prerequisites

1. Python 3.10+ installed
2. Datasets downloaded per [`datasets.md`](datasets.md)
3. Dependencies: `pip install -r requirements.txt`

Verify environment:

```bash
python scripts/00_capture_env.py
```

Logs to `runtime_logs/environment.json` for future reference.

---

### 1. Dataset Density Profiling (~30 seconds)

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

### 2. Run Unified Pipeline (~3-4 hours)

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

### 3. Evaluate (~30-50 minutes)

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

### 4. (Optional) Kernel Ablation (~2 hours)

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

### 5. Generate Figures (~5-10 minutes)

#### Figure 1: Pipeline overview

```bash
python scripts/generate_figure_1_pipeline.py \
    --output ./manuscript/figures/figure_1_pipeline.png \
    --stage-image-5 ./output/BSDS500/GWi/3063.png \
    --stage-image-6 ./output/BSDS500/GWi_odps/3063.png
```

Stages 2-4 use built-in synthetic placeholders.

#### Figures 2-3: Side-lobe + ODPS schematic

```bash
python scripts/generate_figure_2_3.py
```

Output: `figure_2_sidelobe.png`, `figure_3_odps_schematic.png`

#### Figures 4-9: Qualitative + PR curves

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

### Reproducibility Checklist

After completing the pipeline:

- [ ] `eval_results/k5/ods_summary.csv` matches Tables 2, 5, 6 in paper
- [ ] `runtime_logs/runtime_unified_k5.csv` matches Table 7 in paper
- [ ] `eval_results/k5/ablation_multi_dataset.csv` matches Tables 1-4 (ablation)
- [ ] `manuscript/figures/` contains 9 PNG files
- [ ] No errors during evaluation
- [ ] All 280 test images processed (200 BSDS500 + 50 BIPED + 30 UDED)

---

### Troubleshooting

#### Edge Drawing produces same output as Sobel

You have `opencv-python` instead of `opencv-contrib-python`. Fix:
```bash
pip uninstall opencv-python opencv-contrib-python
pip install opencv-contrib-python
```

#### Wildly different runtime numbers

Check single-thread enforcement:
```python
import cv2, os
print(cv2.getNumThreads())               # Should be 1
print(os.environ.get('OMP_NUM_THREADS')) # Should be 1
```

#### ODS differs by > 0.01 from canonical

Most common cause: wrong matching protocol. We use per-annotator
matching following Arbelaez 2011, where a prediction is a TP if it
matches at least one annotator.

#### Out of memory on BIPED

BIPED images are 1280×720 (4× pixel count). On <8GB RAM:
```bash
python scripts/02_run_unified.py --datasets BIPED --batch-size 1
```
