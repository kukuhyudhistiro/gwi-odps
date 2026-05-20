# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
