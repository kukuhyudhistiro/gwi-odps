# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [3.0.0] — 2026-11-10

First revision of manuscript DSP-D-26-02462. Tag `v3.0.0-dsp-r1`. The work is in `revision_dsp/`. The submitted code is kept unchanged so that both versions can be compared.

### Added
- `revision_dsp/`: library (`rev/`), one script per reviewer comment or group of comments (`scripts/00`-`27`), and results (CSV/JSON, `results/TABLES.md`, figures).
- Pre-registered protocol (`revision_dsp/config.yaml`) and hypotheses (`revision_dsp/HYPOTHESES.md`), with the tags `prereg-dsp-2026-11-08`, `prereg-dsp-amend1-2026-11-09`, `hyp-dsp-2026-11-09`, `prereg-dsp-amend2-2026-11-09`, `freeze-2026-11-10` and `numbers-frozen-2026-11-10`.
- `revision_dsp/CHANGELOG.md`: protocol changes after pre-registration, with reasons, including the post hoc amendment 2.
- `revision_dsp/FINDINGS.md`: every finding and limitation, including the claims of the submission that the revision withdraws or corrects.
- `revision_dsp/PROCESS_LOG.md`: start, end and duration of every stage.
- Equivalence tests with the submitted code (`revision_dsp/scripts/01_selftest.py`). The legacy check reproduces the submitted GWi, GWi+ODPS, GWC and Sobel numbers to four decimals.
- Paired statistics: bootstrap CI of ΔODS, Wilcoxon signed-rank with Holm adjustment.
- New analyses, each answering a reviewer comment:
  - zero-DC GWC (R1.5);
  - preprocessing ablation (R2.7);
  - kernel, λ × d, N, σ/λ and γ ablations on non-test data (R2.5, R2.6, R3.2, R3.4);
  - localization analysis of ODPS (R1.3);
  - runtime per stage (R1.4, R2.10, R3.3, R3.6).
- Learned detectors (TEED, LDC, PiDiNet) evaluated with the same evaluator, using official repositories and weights (`revision_dsp/tools/external/`, `revision_dsp/results/external/`). The weights are not included.

### Changed
- **Configuration.** k9 λ9, d = λ/2 = 4.5, selected on BSDS500 train+val and BIPED train. It replaces k5 λ4, d = 2, which had been selected on the test sets.
- **Baselines, run as the manuscript describes them (§4.3):**
  - Canny: OpenCV 50/150, binary.
  - LoG: 7×7 kernel, σ 1.4, zero sum.
  - Edge Drawing: OpenCV default parameters.
  - Phase congruency: phasepack, 4 scales, 6 orientations.
  - The submitted "Canny" row is kept under its correct name, Gaussian gradient magnitude σ 1.4.
- **OIS and AP** are computed by dataset-level accumulation. The submitted definitions are reported alongside as `OIS_legacy` and `AP_legacy`.
- **Ablation tables** use the protocol of the main tables: per-image min-max normalization and 99 thresholds.
- **Runtime**: one thread, 3 warm-up images, median of 5 runs per image, reported per stage.
- **Documentation:**
  - `README.md`: revised numbers, with the submitted numbers in a folded section.
  - `docs/ODPS_derivation.md`: rewritten, with the mechanism corrected.
  - `docs/reproduction.md`: commands of the revision.
  - `docs/kernel_ablation.md` and `docs/benchmarks.md`: marked as describing v2.0.0.
- `CITATION.cff`: version 3.0.0. Performance claims removed from the abstract.
- **Authors and title** in `README.md` and `CITATION.cff` now follow the submitted manuscript:
  - authors: Yudhistiro, Adi, Basuki, Rijati. v2.0.0 listed three authors, in a different order.
  - title: "... for Lightweight Edge Detection". v2.0.0 had other titles.

### Corrected statements of v2.0.0
- "ODPS suppresses side lobes at ±λ/2": the reported kernels have no carrier side lobe, and ODPS acts as directional thinning.
- "The real component is redundant": most of the GWi > GWC gap is the DC response of the raw real kernel.
- "2.2× faster than GWC": this holds for the filtering stage only. The full pipeline is 1.15× faster at k5 λ4 and 1.56× faster at k9 λ9.
- "12.6× faster than PC": 8.5× at k9 λ9.
- "33 thresholds" and "SciPy 1.5.3, scikit-image 0.21": the main tables used 99 thresholds, and the actual versions are listed in `revision_dsp/results/env/`.

### Fixed
- `revision_dsp/run_all.sh` now quotes `$PY`, so an interpreter path that contains spaces works, e.g. `PY="C:/My Projects/gwi-odps/revision_dsp/.venv/Scripts/python.exe"`.
  - Found by the smoke test on a fresh clone on 10 Nov 2026, after the numbers were frozen.
  - No result is affected.
- **Smoke test on Windows.** The smoke test now keeps its synthetic data and results in `revision_dsp/tests/_smoke/` (git-ignored) instead of `/tmp`.
  - **The problem.** Under Git Bash on Windows, `/tmp` passed as an argument became the Windows Temp folder. `/tmp` read from the config became `C:\tmp`. The synthetic data were therefore written to one folder and looked for in another, and `01_selftest` failed.
  - **Also changed.** Earlier smoke results are now removed before each run, so the test does not read old cached results.
  - No result of the revision is affected.

### Before publication (14 Nov 2026)
No result changed. The tag `v3.0.0-dsp-r1` was moved to the release commit.
- **Per-image counts included** (`revision_dsp/results/counts/`, 34 MB). The kernel selection, the statistics and the tables can be recomputed without the datasets (`docs/reproduction.md` A.0b).
- **Documentation for users outside the project:**
  - `revision_dsp/README.md`: setup from a clone, the pre-registration tags, the Windows interpreter setting.
  - `docs/datasets.md` and `data/README.md`: layouts of the train and val splits used by the revision; UDED images are PNG.
  - `docs/reproduction.md`: check without the datasets; setup of the E23 environment.
- **E23 tools:** the local folder of the E23 environment is no longer written into `tools/external/run_e23.sh`; it is passed as `EXT`. The package list of that environment is in `revision_dsp/results/external/requirements-e23.txt`.
- **Corrections of text, not of results:**
  - k5 λ4 ranks 18th of the final 24 candidates under both selection criteria (12th of the 18 candidates of amendment 1); `README.md`, `docs/kernel_ablation.md` and `revision_dsp/FINDINGS.md` gave only the latter.
  - `revision_dsp/FINDINGS.md` (E23 cost table): the converted PiDiNet has 720,709 parameters; 710,149 is the published model.
- **Authors and affiliations** in `README.md` and `CITATION.cff` follow the revised manuscript: Universitas Merdeka Malang (first author), Universitas Dian Nuswantoro, BRIN.
- Root `.gitignore`: datasets, environments and local logs.
- **Commit history.** Before publication, a co-author line was removed from the messages of the revision commits. The commit hashes therefore changed; the hashes cited in the documentation refer to the published commits. File contents, author and commit dates, and the dates of the pre-registration tags are unchanged (process log REL-2e).
- **After the first push (14 Nov 2026):** planning notes on other work of the authors were moved out of `revision_dsp/FINDINGS.md` (section F and a few references). No result of the revision changed. The tag `v3.0.0-dsp-r1` was moved to this version; the pre-registration tags were not moved (process log REL-3a).

### Unchanged
- `src/`, `scripts/`, `eval_results/k5/` and `runtime_logs/`, as at submission (commit `91b4f83`, tag `dsp-submitted-v1`).

---

## [2.0.0] — 2026-05-19

### Changed (Breaking)
- **Default kernel size changed from k=7 to k=5** based on cross-dataset ablation
- All canonical evaluation values updated for k=5 baseline

### Added
- `02_run_unified.py` — unified pipeline runner (combines `02_run_all_methods.py` + `02b_run_gwi_odps.py`)
- `10_kernel_ablation_multi_dataset.py` — cross-dataset kernel parameter ablation
- Documentation: `docs/kernel_ablation.md`, `docs/ODPS_derivation.md`
- Canonical evaluation results: `eval_results/k5/` with combined ODS summary and ablation data

### Removed
- `02_run_all_methods.py` and `02b_run_gwi_odps.py` deprecated; use `02_run_unified.py`
- Old k=7 evaluation results moved to legacy folder

### Notes
- New canonical results: GWi alone ODS = 0.4443/0.5602/0.6072 (BSDS500/BIPED/UDED)
- New canonical results: GWi+ODPS ODS = 0.4696/0.5744/0.6449
- GWi alone is 2.18-2.22× faster than GWC (verified)
- GWi+ODPS at runtime parity with GWC (~5% slower) while achieving +0.076-0.178 ODS

---

## [1.0.0] — 2026-05-16

### Added
- Initial public release for paper submission
- GWi pipeline implementation (Stages 1-5) with k=7 default
- ODPS post-processing module (Stage 6)
- Six baseline implementations: Canny, Sobel, LoG, PC, ED, GWC
- Berkeley evaluation protocol
- Reproduction scripts (00-06) for end-to-end pipeline
- Figure generation scripts
- Documentation: datasets, reproduction
