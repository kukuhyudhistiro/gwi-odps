# Kernel Parameter Selection — Cross-Dataset Ablation

This document records the systematic kernel parameter ablation that
informs the canonical configuration (k=5, λ=4, σ=2.24, γ=0.5, n=8).

---

## Methodology

- **Pipeline tested**: GWi only (Stages 1-5), without ODPS — isolates kernel effect
- **Datasets**: BSDS500 (200 images), BIPED v2 (50 images), UDED (30 cross-domain)
- **Total evaluations**: 7 configurations × 3 datasets = 21
- **σ/λ ratio**: Fixed at 0.56 (Daugman biological rule); σ derived as 0.56·λ
- **γ aspect ratio**: Fixed at 0.5
- **n orientations**: Fixed at 8 (additional orientations cause angular overlap)

Evaluator: Same Berkeley protocol used in main paper
(`scripts/04c_evaluate_bsds_v2.py`).

---

## Configurations Tested

| Config | k | λ | n | σ | σ/k |
|--------|--:|--:|--:|---:|---:|
| 1 | 5 | 3 | 8 | 1.68 | 0.34 |
| 2 | 5 | 4 | 8 | 2.24 | 0.45 |
| 3 (former baseline) | 7 | 4 | 8 | 2.24 | 0.32 |
| 4 | 7 | 5 | 8 | 2.80 | 0.40 |
| 5 | 9 | 4 | 8 | 2.24 | 0.25 |
| 6 | 7 | 4 | 12 | 2.24 | 0.32 |
| 7 | 7 | 4 | 16 | 2.24 | 0.32 |

---

## Results

### Per-Dataset Tables

#### BSDS500 (n=8)

| Kernel | λ | ODS↑ | OIS↑ | AP↑ | Runtime (ms) |
|:------:|---:|-----:|-----:|----:|-------------:|
| 5×5 | 3 | 0.3876 | 0.4481 | 0.3412 | 12.21 |
| **5×5** | **4** | **0.4351** | **0.4864** | **0.3718** | **11.51** |
| 7×7 | 4 | 0.3955 | 0.4504 | 0.3556 | 16.27 |
| 7×7 | 5 | 0.4353 | 0.4856 | 0.3672 | 16.21 |
| 9×9 | 4 | 0.3847 | 0.4382 | 0.3322 | 29.30 |

#### BIPED v2 (n=8)

| Kernel | λ | ODS↑ | OIS↑ | AP↑ | Runtime (ms) |
|:------:|---:|-----:|-----:|----:|-------------:|
| 5×5 | 3 | 0.4691 | 0.5272 | 0.4430 | 69.73 |
| **5×5** | **4** | **0.5539** | **0.5976** | **0.5230** | **67.03** |
| 7×7 | 4 | 0.4693 | 0.5151 | 0.4486 | 96.43 |
| 7×7 | 5 | 0.5462 | 0.5907 | 0.5153 | 110.03 |
| 9×9 | 4 | 0.4441 | 0.4909 | 0.4189 | 154.06 |

#### UDED (n=8)

| Kernel | λ | ODS↑ | OIS↑ | AP↑ | Runtime (ms) |
|:------:|---:|-----:|-----:|----:|-------------:|
| 5×5 | 3 | 0.5457 | 0.5703 | 0.4693 | 18.02 |
| **5×5** | **4** | **0.6021** | **0.6260** | **0.5121** | **18.39** |
| 7×7 | 4 | 0.5473 | 0.5685 | 0.4812 | 26.25 |
| 7×7 | 5 | 0.6076 | 0.6202 | 0.5019 | 26.19 |
| 9×9 | 4 | 0.5329 | 0.5455 | 0.4538 | 46.38 |

### Mean ODS Across Datasets

| Kernel | λ | Mean ODS | BSDS500 rank | BIPED rank | UDED rank |
|:------:|---:|---------:|:------------:|:----------:|:---------:|
| 5×5 | 3 | 0.4675 | 4 | 4 | 4 |
| **5×5** | **4** | **0.5304** | **2** | **1** | **2** |
| 7×7 | 4 | 0.4707 | 3 | 3 | 3 |
| 7×7 | 5 | 0.5297 | 1 | 2 | 1 |
| 9×9 | 4 | 0.4539 | 5 | 5 | 5 |

---

## Findings

### 1. Top Two Configurations Consistent Across Datasets

5×5 with λ=4 and 7×7 with λ=5 share the top spots across all three datasets,
with nearly identical mean ODS (0.5304 vs 0.5297, Δ = 0.0007).

### 2. Speed Advantage of 5×5, λ=4

| Dataset | 5×5, λ=4 | 7×7, λ=5 | Speedup |
|---------|--------:|---------:|--------:|
| BSDS500 | 11.51 ms | 16.21 ms | 29% faster |
| BIPED | 67.03 ms | 110.03 ms | 39% faster |
| UDED | 18.39 ms | 26.19 ms | 30% faster |

### 3. Suboptimality of Conventional 7×7, λ=4

The conventional choice from prior literature (k=7, λ=4) ranks **3rd on all three datasets**, indicating that this widespread choice is empirically suboptimal.

### 4. Importance of σ/k Ratio

Both top configurations have **σ/k between 0.40-0.45**, suggesting the Gaussian envelope should occupy 40-45% of the kernel half-width for optimal localization. The former baseline (k=7, λ=4) has σ/k = 0.32, where the Gaussian tail is clipped by the smaller kernel footprint.

### 5. Larger Kernels Degrade Accuracy

9×9 with λ=4 produces the lowest ODS across all datasets and the highest runtime, indicating that excessive kernel support introduces noise without resolution gain.

### 6. Higher Orientation Counts Wasteful

Doubling n_orientations from 8 to 16 (configs 6, 7) yields ODS changes <0.001 while doubling runtime — confirming that 8 orientations at 22.5° spacing provides sufficient angular coverage.

---

## Selected Configuration

Based on the Pareto frontier of accuracy and runtime:

**k = 5, λ = 4, σ = 2.24, γ = 0.5, n = 8 orientations**

This configuration:
- Achieves the highest **mean ODS (0.5304)** across three datasets
- Runs **29-39% faster** than the second-best configuration
- Maintains the **σ/λ = 0.56 biological ratio** (Daugman)
- Has σ/k = 0.45, providing adequate Gaussian envelope coverage
- Matches the predicted **ODPS d = λ/2 = 2 pixels** without modification

The selection is justified empirically (highest mean ODS at lowest runtime among top performers) and theoretically (consistent with Daugman 1985 and biological visual cortex receptive fields).

---

## Reproduction

```bash
python scripts/10_kernel_ablation_multi_dataset.py \
    --data-root ./data \
    --output-csv ./eval_results/k5/ablation_multi_dataset.csv \
    --datasets BSDS500 BIPED UDED
```

Estimated runtime: ~2 hours (BIPED at 1280×720 is the slowest).
