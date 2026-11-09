# Hypotheses on scale, ρ and ODPS (written before the 18-candidate selection results)

**Written:** Monday 9 November 2026, about 16:45 (UTC+7), while E10 with the
18 candidates of amendment 1 (`prereg-dsp-amend1-2026-11-09`) was running.
**Committed and tagged:** `hyp-dsp-2026-11-09`.
**Evaluated by:** `scripts/13_hypotheses.py` (committed with this file, before the
results exist), on `results/selection/kernel_ablation.csv` of the 18-candidate run.
**Reported in:** response letter (R2.2, R3.1b, R3.2, R3.4) and the revised §5.5,
whatever the outcome. A hypothesis that fails is reported as failed.

## What had been seen when this was written

Only non-test data. Test splits not opened.

- E10 with the five candidates of Tables 1-4 (commit `aa2bc01`): GWi and GWi+ODPS
  on BSDS500 train+val and BIPED train for k5 λ3, k5 λ4, k7 λ4, k7 λ5, k9 λ4.
- E11 around k7 λ5 (commit `aa2bc01`): GWi and GWi+ODPS on BSDS500 train+val for
  k7 λ3, λ4, λ5, λ6, and the one-factor variants.
- E02 (synthetic): the carrier side lobe of the imaginary kernel exists only
  when ρ > 0.5 (runbook §4).
- Not seen: any ODS of the 13 new candidates. At the time of writing E10 had
  finished the counts of k5 λ5 and was computing k5 λ6; their ODS values were
  not printed or opened.

Observed pattern that motivates the hypotheses (ODPS gain Δ = ODS(GWi+ODPS) − ODS(GWi)):

| ρ | Config | ODS GWi BSDS | ODS GWi BIPED | Δ BSDS | Δ BIPED |
|---|---|---|---|---|---|
| 1.0 | k9 λ4 | 0.3711 | 0.4256 | +0.050 | +0.047 |
| 1.0 | k7 λ3 | 0.3559 | – | +0.044 | – |
| 0.75 | k7 λ4 | 0.3839 | 0.4467 | +0.047 | +0.042 |
| 0.667 | k5 λ3 | 0.3727 | 0.4452 | +0.037 | +0.024 |
| 0.6 | k7 λ5 | 0.4270 | 0.5214 | +0.031 | +0.020 |
| 0.5 | k5 λ4 | 0.4221 | 0.5255 | +0.026 | +0.016 |
| 0.5 | k7 λ6 | 0.4514 | – | +0.022 | – |

## Definitions

- ρ = (k // 2) / λ: half-width of the kernel over the carrier wavelength.
- Data: the 18 candidates k ∈ {5, 7, 9} × λ ∈ {3, ..., 8}, d = λ/2, N = 8,
  σ/λ = 0.56, γ = 0.5, on each selection split separately: BSDS500 train+val (300
  images) and BIPED train (200 images). Protocol of `config.yaml` (99 thresholds,
  per-image min-max).
- Δ = ODS(GWi+ODPS) − ODS(GWi) for the same candidate and split.
- ρ groups: ρ > 0.5 (9 candidates: k5 λ3; k7 λ3-5; k9 λ3-7), ρ = 0.5 (3: k5 λ4,
  k7 λ6, k9 λ8), ρ < 0.5 (6: k5 λ5-8; k7 λ7-8).
- Known confounder: for odd λ, d = λ/2 is not an integer and the ODPS offsets are
  rounded with `np.round` (half to even): d 1.5 → 2, 2.5 → 2, 3.5 → 4 on the axes.
  This is reported with the results, not corrected.

## H1. The benefit of ODPS decreases as ρ decreases

Claim for the manuscript: ODPS helps most when the carrier side lobe exists
(ρ > 0.5, E02); its benefit shrinks as ρ decreases.

| ID | Prediction | Supported if (each split separately) |
|---|---|---|
| H1a | Δ increases with ρ | Spearman r_s(ρ, Δ) > 0 with one-sided p < 0.05 over the 18 candidates |
| H1b | Group ordering | median Δ (ρ < 0.5) < median Δ (ρ = 0.5) < median Δ (ρ > 0.5) |
| H1c | Separation (strict) | max Δ over ρ < 0.5 < min Δ over ρ > 0.5 |

H1 is supported if H1a and H1b hold on both splits. H1c is reported separately as
the strict form. If H1a/H1b hold on one split only, H1 is reported as partial.

**Q1 (open, no prediction):** the sign of Δ for ρ < 0.5 (whether ODPS still helps,
does nothing, or hurts when d ≥ 2.5 px). Reported as observed.

## H2. GWi performance depends on ρ and on kernel scale, not on λ alone

Claim for the manuscript: GWi needs a small enough ρ, and at equal ρ a larger
kernel does better on BSDS500.

| ID | Prediction | Supported if |
|---|---|---|
| H2a | Large ρ is poor | on each split, every candidate with ρ ≥ 0.667 (k5 λ3, k7 λ3, k7 λ4, k9 λ3-6) has lower ODS of GWi than every candidate with 0.5 ≤ ρ ≤ 0.6 (k5 λ4, k7 λ5, k7 λ6, k9 λ7, k9 λ8) |
| H2b | Scale at equal ρ (BSDS500 only) | all four orderings of ODS of GWi on BSDS500 train+val hold: k7 λ3 < k9 λ4 (ρ 1.0); k5 λ3 < k9 λ6 (ρ 0.667); k5 λ4 < k7 λ6 < k9 λ8 (ρ 0.5) |
| H2c | BIPED prefers a smaller scale (lower confidence) | for each k, the λ with the highest ODS of GWi on BIPED train is ≤ the λ with the highest ODS on BSDS500 train+val |

Notes:
- H2b: two of the four orderings were already seen (k7 λ3 < k9 λ4; k5 λ4 < k7 λ6,
  both BSDS500). The new tests are k5 λ3 < k9 λ6 and k7 λ6 < k9 λ8. Both are
  reported, and the already-seen ones are marked as such.
- No prediction is made for scale at equal ρ on BIPED.
- H2a mixes seen and new candidates; the new ones are k9 λ3, k9 λ5, k9 λ6 (ρ ≥ 0.667)
  and k9 λ7, k9 λ8 (0.5 ≤ ρ ≤ 0.6).

**Q2 (open, no prediction):** whether, for each k, ODS of GWi has an interior
maximum within λ ≤ 8. For the selected configuration this is handled by the edge
rule of amendment 1.

## What these hypotheses do not do

- They do not change the selection rule or the selected configuration.
- They are tested on non-test splits only. Whether the same pattern holds on the
  test sets is read from E20 as a descriptive check, not as a new test.
- No correction for multiple comparisons is applied (descriptive mechanism
  analysis, outside the Holm family of E22).
