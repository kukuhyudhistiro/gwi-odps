# revision_dsp: experiments for the DSP-D-26-02462 revision

This folder lives inside the original repository `kukuhyudhistiro/gwi-odps`,
on branch `revision-dsp-r1`. It contains the scripts for the work packages in
`RUNBOOK_Revisi_DSP_Paper1_GWi-ODPS.md`. All new numbers in the revised
manuscript come from here. The submitted code in `src/` and `scripts/`
(commit `91b4f83`) stays unchanged. It is used only through `rev/legacy.py`
for equivalence tests; test T0 checks that this copy still equals `src/`.

```
gwi-odps/                  original repo (branch revision-dsp-r1)
├── src/, scripts/         submitted code, unchanged
├── data/                  BSDS500/, BIPED/, UDED/ (not in git)
├── docs/                  updated at the end (ODPS_derivation.md, reproduction.md)
└── revision_dsp/          this folder
```

## 1. Setup (once)

```bash
git clone https://github.com/kukuhyudhistiro/gwi-odps.git    # or use the existing local clone
cd gwi-odps
git tag dsp-submitted-v1 91b4f83                             # state of the code at submission
git checkout -b revision-dsp-r1
unzip /path/to/revision_dsp.zip                              # creates revision_dsp/
cd revision_dsp
python3 -m venv .venv && source .venv/bin/activate
pip uninstall -y opencv-python 2>/dev/null; pip install -r requirements.txt
```

Datasets go in `gwi-odps/data/` (`config.yaml` uses `data_root: ../data`).
Besides the test splits described in `data/README.md`, the revision needs
BSDS500 `train` and `val` (images and `.mat` GT) and BIPED `train`. Check the
folder names under `datasets:` in `config.yaml`. Set `n_jobs` to the number of
cores.

```bash
bash run_all.sh smoke        # synthetic data, a few minutes: every script must finish
```

## 2. Pre-registration (before any run on real data)

```bash
cd gwi-odps
git add revision_dsp && git commit -m "revision_dsp: scripts + protocol v2"
git tag prereg-dsp-2026-11-08
```

After this tag, any change to `config.yaml` goes into `CHANGELOG.md` with its reason.

## 3. Principle

The reviewers assessed the submitted manuscript. The revision keeps its
protocol and changes only what a reviewer asked for. Every block of
`config.yaml` and every script docstring names the manuscript section it
follows or the reviewer point it answers (R1.x, R2.x, R3.x as in the response
letter).

## 4. Run order

| Command | Reviewer point | What it gives |
|---|---|---|
| `bash run_all.sh check` | R2.2, R2.4, R3.1b, R1.5 | `results/env/`, `results/selftest/selftest.json` (all PASS), `results/mechanism/` |
| `bash run_all.sh select` | R2.1 (and kernel ablation for R3.4) | `results/selection/selected.json`, `kernel_mean.csv`, `kernel_ablation.csv` |
| `bash run_all.sh ablation` | R2.5, R2.6, R3.2, R3.4 | `results/ablation/lam_d.csv`, `one_at_a_time.csv` |
| `bash run_all.sh freeze`, then `git tag freeze-2026-11-10` | R2.1 | `results/config_final.yaml` |
| `bash run_all.sh test` | all tables | `results/test/summary.csv`, `legacy_check.csv` |
| `bash run_all.sh preproc` | R2.7 | `results/preproc/preproc_ablation.csv` |
| `bash run_all.sh stats` | R1.1, R2.11 (R1.5 analysis rows) | `results/stats/pairs.csv`, `variability.csv`, `claims_guard.json` |
| `bash tools/external/run_e23.sh` (separate PyTorch CPU environment and official repositories under `D:/Project 2026/e23_external`; maps, then `scripts/23_eval_external.py --nms`, MACs, CPU time), then `tools/external/summarize_e23.py` | R1.2, R3.5 | `results/external/` (`summary.csv`, `counts/`, `cost/`, `cost.csv`, `models.yaml`) |
| `bash run_all.sh runtime` (idle machine) | R1.4, R2.5, R2.10, R3.3, R3.6 | `results/runtime/` |
| `bash run_all.sh qualitative` | R1.3 | `results/qualitative/` |
| `bash run_all.sh tables` | all | `results/TABLES.md` |
| `bash run_all.sh figures` | all (figures of the revised manuscript) | `results/figures/`, `results/figures/FIGURES.md` |

All stages above were run on 9-10 Nov 2026. The results are frozen at tag `numbers-frozen-2026-11-10`. Findings and limitations: `FINDINGS.md`. Timing of every stage: `PROCESS_LOG.md`.

Smoke run on real data before each long run: append `--limit 5`, e.g.
`python3 scripts/10_select_kernel.py --limit 5`. Limited runs are cached
separately and must never be quoted.

## 5. Protocol (`config.yaml`)

- **Preprocessing:** BT.601 grayscale, histogram equalization (PIL), /255 (Eq. 1-2). `21_ablation_preproc.py` evaluates GWi and GWi+ODPS without HE and without /255 (R2.7).
- **Border:** as in the manuscript: zero padding for GWi and GWC (Algorithm 1), OpenCV's default (reflect-101) for Sobel, LoG and the Gaussian gradient. ODPS neighbours outside the image are 0.
- **Map normalization:** per-image min-max to [0, 1], 8-bit levels, as in the submitted code, for every method and every table. The ablation tables of the submission used a different normalization and 33 thresholds; in the revision they use the same protocol as the main tables (R2.9).
- **Evaluation:** 99 thresholds, `skimage` thinning of prediction and GT, one-to-one greedy matching within 0.0075 × diagonal, multi-annotator counts as in 04c. Counts are bit-identical to `04c_evaluate_bsds_v2.py` (selftest T5/T6).
- **Metrics:** ODS; OIS and AP by dataset-level accumulation (since 9 Nov 2026, CHANGELOG.md): OIS = F of the counts accumulated over images at each image's best threshold; AP = area under the dataset-level PR curve with precision made monotone. These are the definitions of the A-GWi paper (JESA 44740), so both papers report the same metrics. The definitions of the submitted tables (04c: mean of per-image best F, mean of per-image areas) are reported alongside as `OIS_legacy` and `AP_legacy`, and the BSDS benchmark-code AP as `AP_bsds101`. Canny and ED give binary maps: one operating point, so ODS = OIS and AP is not comparable with the other methods.
- **Selection (R2.1):** on BSDS500 train+val and BIPED train instead of the test sets; d = λ/2 (Section 3.6); N, σ/λ, γ at the manuscript values. Protocol v2 used the five configurations and the rule of Tables 1-4 (highest mean ODS of GWi). Amendment 1 extended the candidates to k ∈ {5, 7, 9} × λ ∈ {3..8} with an edge rule; amendment 2, written after those results were seen, changed the criterion to the highest mean ODS of GWi+ODPS, because under the GWi criterion ODS rises monotonically with λ and has no interior optimum. Both criteria are reported. See CHANGELOG.md and FINDINGS.md. The test sets are opened once, after the freeze.
- **Baselines (R2.8):** run as described in Section 4.3 with fixed parameters: Canny OpenCV 50/150, Sobel 3×3, LoG 7×7 σ 1.4, PC (phasepack, 4 scales, 6 orientations, Kovesi's defaults otherwise), ED (OpenCV default parameters). GWC uses the same kernel as GWi. The submitted "Canny" row (Gaussian σ 1.4 + Sobel magnitude) is kept as `GaussGradMag1.4`.
- **Statistics (R1.1, R2.11):** per method, bootstrap 95% CI of ODS, OIS, AP and the spread of per-image F; for GWi vs GWC, GWi+ODPS vs GWC and GWi+ODPS vs GWi, paired bootstrap 95% CI of ΔODS (B = 2000) and Wilcoxon signed-rank on per-image F with Holm adjustment over the 9 tests.
- **Analysis for R1.5:** GWC with a zero-mean real kernel (same kernel otherwise), compared with GWi and GWC outside the Holm family.

## 6. Methods (`rev/methods.py`)

| family | what it is |
|---|---|
| `gwi` | imaginary-only Gabor, max over N orientations of \|I ∗ g_imag\| (+ ODPS with `nms`) |
| `gwc` | complex Gabor, same kernel; `dc: raw` (manuscript) or `dc: zero` (R1.5 analysis) |
| `gwe` | even-only Gabor (mechanism analysis only) |
| `sobel` | 3×3 Sobel magnitude, no extra smoothing |
| `gaussgrad` | Gaussian σ + Sobel magnitude (the submitted "Canny" row) |
| `log` | \|I ∗ LoG\|, 7×7 kernel, σ 1.4, zero sum |
| `canny` | cv2.Canny(50, 150) on the preprocessed 8-bit image; binary (AP not defined) |
| `pc` | phase congruency, phasepack, 4 scales, 6 orientations |
| `ed` | Edge Drawing, cv2.ximgproc default parameters; binary (AP not defined) |

ODPS (`rev/nms.py`): `nearest` sampling reproduces the submitted code exactly. Its effective distance differs per orientation (2, 2.24, 1.41 px for N = 8, d = 2); the manuscript must state this (R2.3).

## 7. Expected compute (test container: about 2 s per image per method at 321 × 481, 1 core; BIPED images count about 6×)

| Stage | image-method pairs (BSDS-size equivalent) | 8 cores |
|---|---|---|
| select (BSDS train+val + BIPED train) | ≈ 15 000 | ≈ 1 h |
| ablation | ≈ 9 600 | ≈ 40 min |
| test (+ legacy check) | ≈ 8 500 | ≈ 35 min |
| preproc | ≈ 4 500 | ≈ 20 min |

Measure the real speed with `01_selftest.py` (T7) on your machine.

## 8. Folder layout (revision_dsp/)

```
config.yaml            protocol, selection rule, ablations, baselines
rev/                   library (kernels, methods, specs, ODPS, normalization, evaluator, stats, runner)
rev/legacy.py          verbatim functions from the submitted repo (tests only)
scripts/00..26         one script per reviewer point or group of points (docstring at the top)
tools/                 synthetic data for the smoke test
tests/config_synth.yaml
results/               everything the scripts write (cached; delete a file to recompute)
CHANGELOG.md           protocol changes
```
