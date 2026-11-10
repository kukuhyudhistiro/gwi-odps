# Findings and limitations ledger (revision of DSP-D-26-02462)

Every finding of the revision is recorded here, whether or not it supports the
submitted manuscript. Entries are not removed. If an entry is later corrected,
the correction is added below it. All entries are carried into the response
letter and the revised manuscript (§5.5, §5.7 limitations, conclusion), and into
the update of the dissertation roadmap (`Roadmap_KGWavelet_Paper1_Paper2_Paper3.docx`).

Status labels:
- **Finding**: observed result, reported as is.
- **Claim withdrawn**: a claim of the submission that the revision does not support.
- **Claim corrected**: the claim survives in a narrower or different form.
- **Limitation**: a restriction on what the results can show.
- **Process**: something in how the revision was run that a reader should know.
- **Open**: decided by the test-set run (E20, E22, E24), not yet known.

Unless stated otherwise, numbers in sections A-H are ODS on non-test splits:
BSDS500 train+val (300 images) and BIPED train (200 images). Section I holds the
test-set results (E20), run once after the freeze (tag `freeze-2026-11-10`, commit
7ae7ba5), and the paired statistics of E22 (F25). Only the pairs pre-registered in
scripts/22_stats.py have confidence intervals. Every other test-set difference is a
point estimate.
Last update: 10 Nov 2026, after E26, the numbers freeze (tag `numbers-frozen-2026-11-10`) and the release documentation of v3.0.0. Timings of every stage: PROCESS_LOG.md.

## Original claims and their status

| # | Claim in the submission or the roadmap | Status now | Entries |
|---|---|---|---|
| C1 | k5 λ4 is the best configuration across three datasets (Table 4) | **Claim withdrawn.** It was selected on test data. On non-test data it ranks 12 of 18 by ODS of GWi. On test, k9 λ9 is above it for GWi on all three sets; for GWi+ODPS on BSDS500 and BIPED but not UDED (+0.0002) | F1, F2, F21 |
| C2 | ODPS suppresses carrier side lobes located at ±λ/2, with d = 2 for λ = 4 | **Claim withdrawn (mechanism), replaced by directional thinning.** Carrier side lobes exist only when (k//2)/λ > 0.5. At k5 λ4 and at the new selection there are none; ODPS thins a broad response across orientations. Where side lobes exist (k5 λ3), ODPS keeps the two side peaks of an axis-aligned step and removes the edge pixels | F12 (correction), F27 |
| C3 | ODPS improves ODS over GWi | **Claim corrected: supported on BSDS500 only.** E22 at k9 λ9: BSDS500 +0.0122, 95% CI [0.0090, 0.0158]; BIPED +0.0079, CI [−0.0076, 0.0203]; UDED −0.0025, CI [−0.0161, 0.0121]. "Improves" may be written for BSDS500 only. At the submitted k5 λ4 the point gains were larger (+0.0253, +0.0142, +0.0377), with no CI | F9, F10, F11, F22, F25 |
| C4 | The real component of the Gabor kernel is redundant (GWi > GWC) | **Claim corrected.** GWi is above raw GWC on all test sets (CIs exclude 0), but most of that gap is the DC response of the raw real kernel. Against zero-DC GWC at k9 λ9, GWi stays above, with CIs excluding 0: +0.0161, +0.0391 and +0.0842. At k5 λ4, zero-DC GWC is above GWi on BSDS500 (−0.0093, no CI) | F14, F23, F25 |
| C5 | GWi is about 2.2× faster than GWC | **Claim corrected (scope).** It holds for the filtering stage: 2.1× at k9 λ9 and 2.3× at k5 λ4. For the full pipeline, GWi+ODPS is 1.56× faster than GWC at k9 λ9, but only 1.15× at the submitted k5 λ4. The Gaussian gradient baseline is about 5.5× faster than GWi+ODPS and has higher ODS. "12.6× faster than PC" becomes 8.5× at k9 λ9 | F15, F28 |
| C6 | (implicit) the Gabor carrier is what makes GWi work | **Not supported for GWi alone.** GWi scores best as the kernel loses its carrier lobe and approaches a smoothed oriented derivative. This was already published in Paper 2 (A-GWi) | F7, H1 |
| C7 | (not claimed, but implied by roadmap §6, which lists only Gabor methods) where GWi+ODPS stands among the evaluated detectors | **Below a classical baseline, in the submission and in the revision.** The Gaussian gradient magnitude σ 1.4 is above every Gabor variant on all three test sets, in ODS, OIS and AP. Measured under the manuscript border protocol, which handicaps the Gabor methods (H5) | F16, F24, H3, H5 |
| C8 | (design choice, R2.6) N = 8 orientations is an appropriate balance | **Not supported at the selected kernel.** N = 4 reaches the same ODS at half the cost; N = 16 adds nothing. It was supported at k7 λ5 (E11 of the five-candidate run) | F19 |
| C9 | (§3.1, R2.7) Histogram equalization is important, notably for low-contrast images; normalization to [0, 1] is necessary | **Claim withdrawn.** On all three test sets, removing HE raises ODS of GWi (+0.0055 to +0.0623) and of GWi+ODPS (+0.0111 to +0.0591). /255 changes nothing. The protocol stays as frozen (HE) | F26 |
| C10 | (R1.3, as the reviewer frames it) ODPS reduces artifacts without introducing boundary distortions | **Claim corrected.** At the selected kernel, ODPS works by thinning, so that a lower threshold gives more recall at about the same precision. The mean matched distance grows by less than 0.1 px on average. Some images lose true boundary pixels (BIPED RGB_139: recall −0.25). "Without distortion" can only be stated with these numbers | F27 |
| C11 | (§5.6, R1.2, R3.5) "competitive boundary localization"; learned detectors compared only through their published ODS | **Claim withdrawn.** Measured with the same evaluator, the best learned detector is +0.239 (BSDS500, in-domain), +0.197 (BIPED, in-domain) and +0.144 (UDED) ODS above GWi+ODPS. GWi+ODPS is 2.4 to 16× faster on one CPU thread, but the Gaussian gradient is faster still and more accurate. Framing: training-free and CPU-oriented, without a claim of competitive accuracy or of a cost advantage over classical baselines. Exception: PiDiNet (trained on BSDS500) is below GWi+ODPS on UDED | F29 |

## Reviewer map

Each entry answers one or more reviewer comments. IDs follow the comment register (runbook §7, `PANDUAN_Komentar_Reviewer_DSP.md`). The register also says where in the manuscript each answer goes.

Entries marked *not requested* answer no reviewer comment. They are kept for one of two reasons:
- consistency with Paper 2 (A-GWi, already published);
- transparency about how the revision was run.

They add no experiment that a reviewer did not ask for.

| Entry | Reviewer comments | Note |
|---|---|---|
| F1, F2 | R2.1 | Selection without test data |
| F3, F4, F5 | R2.1, R3.4 | Selection procedure and its amendments (CHANGELOG.md) |
| F6 | *not requested* | Run incidents, disclosed for transparency; no result affected |
| F7 | R3.1a, R3.1b, R3.7 | Framing of GWi as an odd Gabor or derivative filter |
| F8 | R2.2, R3.1b, R3.2, R3.4 | Pre-registered hypotheses H2 (HYPOTHESES.md) |
| F9, F10, F11 | R1.3, R3.2, R1.1 | ODPS gain vs λ; "improves" governed by E22 |
| F12 | R2.2, R1.3 | Double-peak (side-lobe) mechanism |
| F13 | R2.3 | Discretization of d |
| F14 | R1.5 | DC response of the real kernel |
| F15 | R1.4, R2.10, R3.3 | Cost per pixel |
| F16 | R2.8, R2.12 | Position against the classical baselines |
| F17 | R2.1, R3.4 | Final selection |
| F18 | R2.5, R3.2 | Effect of d |
| F19 | R2.6, R3.4 | N, σ/λ, γ |
| F20 | R2.8, R2.9 | Reproduction of the submitted numbers; baselines as described in §4.3 |
| F21 | R2.1, R2.12 | Selected vs submitted kernel on test |
| F22 | R1.3, R3.2, R1.1 | ODPS gain on test |
| F23 | R1.5, R2.4, R3.7 | GWi vs GWC zero-DC |
| F24 | R2.8, R2.12 | Ranking against the classical baselines |
| F25 | R1.1, R2.11, R1.5 | Paired statistics (E22) |
| F26 | R2.7, R2.12 | Preprocessing ablation (E21) |
| F27 | R1.3, R1.5, R2.3 | Localization and qualitative analysis of ODPS (E25); failure cases; border responses visible in the figures |
| F28 | R1.4, R2.5, R2.10, R3.3, R3.6 | Runtime per stage, full pipeline vs filtering, cost of d, measurement conditions (E24) |
| F29 | R1.2, R3.5 | Learned detectors with the same evaluator; parameters, MACs, CPU time; in-domain marks; NMS rows (E23) |
| H1 | R3.1a (citation) | Published in A-GWi; Paper 1 must cite it |
| H2 | R2.9 | Metric definitions; aligned with A-GWi |
| H3 | R2.8 | Binary Canny and GaussGradMag naming |
| H4 | *not requested* | Consistency with A-GWi (roadmap premise) |
| H5 | R2.3 (description only), R2.12 | Border handling is described, not changed. The border diagnostic itself was *not requested* |
| H6 | R2.10 | Runtime procedure; compared with A-GWi |

## A. Selection procedure

**F1. Process. Tables 1-4 of the submission were computed on the test sets and used to select k5 λ4 (R2.1).**
The response letter acknowledges this. The revision selects on non-test splits only.

**F2. Claim withdrawn. On non-test data, k5 λ4 is not the best configuration.**
Its mean ODS of GWi is 0.4738, rank 12 of the 18 candidates of amendment 1.
UDED has no non-test split, so selection uses two datasets instead of three.

**F3. Process. The five configurations of Tables 1-4 did not bracket the optimum.**
E11 at k7 showed ODS of GWi still rising at λ6. Amendment 1 extended the grid to k ∈ {5, 7, 9} × λ ∈ {3..8}. The E10 run with the five candidates (selected k7 λ5, 0.4742) is reported as well.

**F4. Finding and process. Under the manuscript criterion (ODS of GWi), there is no interior optimum.**
- ODS of GWi increases monotonically with λ for every k up to λ8 (Q2 of HYPOTHESES.md).
- At k7 it keeps increasing up to λ12: 0.5331, 0.5366, 0.5384, 0.5393, 0.5399 for λ8 to λ12. The increments shrink: +0.0035, +0.0018, +0.0009, +0.0006.
- The edge rule of amendment 1 therefore did not terminate. This was a design flaw of amendment 1: monotone convergence was not anticipated.
- The rounds were stopped at λ12. That is where the first extremum of the sine carrier reaches the edge of the 7×7 window (λ/4 = 3 px).

**F5. Process. Amendment 2 changed the criterion to mean ODS of GWi+ODPS after the results above were seen.**
- Known at the time of the decision:
  - At k7, GWi+ODPS peaks at λ9 on both splits (0.4890 BSDS, 0.6104 BIPED).
  - Under this criterion the ODPS gain at the selected kernel (+0.012 / +0.015) is larger than under a GWi rule bounded at λ12 (+0.003 / +0.006).
- The change is therefore post hoc, and it also makes the ODPS claim look better than the alternative would.
- Reason given: the manuscript proposes GWi+ODPS as the detector. Table 4 used GWi only because ODPS was defined for λ4 alone. The d = λ/2 rule requested by R3.2 now defines ODPS for every λ.
- Both outcomes are reported: the GWi criterion has no interior optimum (F4), and the GWi+ODPS criterion selects the configuration of amendment 2.

**F6. Process. Two incidents, neither of which produced or changed a result file.**
- `run_all.sh` was edited while E10 was running. Bash then stopped after the selection had finished, so the selection outputs were complete.
- A script error (Windows CRLF) started E11 at 21:38 while the selection was still at its edge. It was stopped within seconds and wrote no result file. Counts that completed are cached by specification and are identical to a normal run.

## B. GWi (claim 1)

**F7. Finding and limitation. With k fixed, GWi scores best as λ grows and the kernel loses its carrier lobe.**
- For λ > 4·(k//2) the imaginary kernel inside the window is a monotone ramp. As λ → ∞ it tends to an oriented first-derivative filter averaged over the window.
- At the GWi+ODPS optimum, k7 λ9, the kernel still has its lobe: the centre row peaks at ±2 px (0.91) and falls to 0.73 at ±3 px.
- On these benchmarks the oscillating carrier is not what gives GWi alone its best ODS; scale and smoothing do.
- This narrows the "Gabor wavelet" framing of GWi alone. It is relevant to R3.1a (odd-Gabor and derivative edge filters are not new) and R3.1b.

**F8. Finding. Hypotheses H2 (HYPOTHESES.md, 18 candidates):**
- **H2a failed on both splits.** Large half-width over λ is not uniformly poor: k9 λ6 (0.667) beats k5 λ4 on BSDS (0.4312 vs 0.4221) and k7 λ5 on BIPED (0.5230 vs 0.5214).
- **H2b supported.** At equal half-width over λ, a larger kernel is better on BSDS. Two of the four orderings had been seen before H2b was written.
- **H2c holds only trivially.** For every k the best λ is at the grid edge (λ8) on both splits, so the test is uninformative.

## C. ODPS (claim 2)

**F9. Finding. H1 supported on both splits: the ODPS gain decreases as (k//2)/λ decreases.**
- Spearman correlation 0.92 (BSDS) and 0.90 (BIPED), one-sided p < 0.0001.
- The group medians are ordered as predicted, and the strict separation (H1c) also holds.
- The largest gains (+0.03 to +0.05) occur for kernels with (k//2)/λ > 0.5, which have the lowest ODS of GWi.

**F10. Finding, Open. At the configuration selected under amendment 2, the ODPS gain is about +0.01.**
- At k7 λ9 the gain is +0.0116 (BSDS) and +0.0145 (BIPED). For λ ≥ 10 at k7 it drops to +0.003 to +0.010.
- Whether the gain at the selected kernel has a 95% CI excluding 0 on test is decided by E22. If it does not, the manuscript may not say "improves".
- *Added after E22 (F25):* the CI excludes 0 on BSDS500 only. On BIPED and UDED, the verb is "does not differ".

**F11. Finding. ODPS did not reduce ODS for any candidate (Q1).**
For all six candidates with half-width over λ below 0.5, the gain is positive: +0.012 to +0.019 on BSDS, +0.009 to +0.016 on BIPED.
- *Added after E20:* F10 and F11 hold on non-test data only. On test (F22), the gain at k9 λ9 is +0.0122 on BSDS500, matching non-test; +0.0079 on BIPED, about half the non-test value; and −0.0025 on UDED. "ODPS never reduces ODS" cannot be stated.

**F12. Claim corrected. The side-lobe mechanism of §3.6 does not apply to the reported kernels.**
- The carrier side lobe exists only when (k//2)/λ > 0.5 (E02). At k5 λ4 and at k7 λ9 there is none.
- At these kernels ODPS removes the shoulder of the response produced by the maximum across orientations, acting as directional thinning.
- "Double-peak suppression" describes the large-ratio regime only. The text must say so.
- *Correction (10 Nov 2026, found while drawing the figure that replaces Figure 5):* the bullet above is too generous. Even where the carrier side lobe exists, ODPS does not suppress the double peak on an axis-aligned step.
  - Source: E02, `results/mechanism/step_profiles.csv` (9 Nov), checked pixel by pixel. At k5 λ3 ((k//2)/λ = 0.67), normal 0°:
    - the max over orientations is 1.0 at ±1.5 px from the edge and 0.75 at the two edge pixels (±0.5 px);
    - after ODPS (d = 1.5, offset 2 px) the two peaks at ±1.5 px are kept and the two edge pixels are removed (width 4 → 2 px).
  - At 22.5° and 45° there is no secondary maximum.
  - So in the side-lobe regime, ODPS leaves a double line about 1.5 px off the edge instead of a single edge. The large ODPS gains of that regime (F9) come with this behaviour; the tolerance of about 4.3 px still matches both lines.
  - The submitted mechanism ("suppresses side lobes at ±λ/2") is therefore not supported in any regime tested. ODPS is a directional thinning step.
- *Added after E02b (10 Nov 2026, E02 re-run so that its tables include the final candidates):* at the selected k9 λ9 there is no carrier side lobe ((k//2)/λ = 0.444). On a step edge, the band above 50% of the maximum is 4.0, 4.52 and 4.24 px wide at normals 0°, 22.5° and 45°. After ODPS, 4.0, 4.0 and 4.24 px remain.
  - ODPS therefore trims the tails, but leaves a band about 4 px wide. The one-pixel line comes from the thinning step of the evaluation protocol, not from ODPS.

**F13. Limitation. For odd λ, d = λ/2 is rounded.**
- The offsets use `np.round`, which rounds halves to even. For d = 4.5 (λ9) the axis offsets are 4, the same as for λ8. For λ10 they are 5.
- The drop in gain between λ9 and λ10 coincides with this step from 4 to 5. Reported, not corrected.

## D. GWi vs GWC (operator I of the roadmap)

**F14. Limitation, Open. The raw real kernel's DC response grows with λ, which biases GWi vs GWC at large λ.**
- DC-to-gain ratio of the raw real kernel: 0.15 at k5 λ4, 0.76 at k7 λ9, 1.24 at k7 λ12. At k7 λ12 the real kernel is entirely non-negative, a low-pass filter.
- GWC built with the same kernel therefore carries a brightness-dependent response that grows with λ. A GWi > GWC gap at k7 λ9 may partly reflect this DC leakage, not only the redundancy of the even component.
- The GWC zero-DC analysis (R1.5, evaluated in E20) is needed to interpret the comparison, and the claim must be stated with this limit.
- *Added after E20:* the DC concern was correct, and it already applies at the submitted k5 λ4. See F23.
- *Added after E02b (10 Nov 2026):* at the final selection k9 λ9 the DC-to-gain ratio of the raw real kernel is 0.157, not the 0.76 of k7 λ9. The 9×9 window holds more of the negative cosine lobes.
  - The ratio is therefore not a sufficient summary of the bias.
  - On a flat region next to a step of contrast 0.2, GWC raw at k9 λ9 responds at 0.52, 0.74 and 0.82 of its edge response for backgrounds 0.2, 0.5 and 0.8. GWC zero-DC and GWi respond at 0 (`results/mechanism/dc_leakage.csv`).
  - GWC raw at k9 λ9 is the lowest of all 14 methods on BSDS500 and UDED (F23).

## E. Cost

**F15. Finding. The selected kernel costs about 3.2 times the submitted one.**
- The final selection is k9 (F17). With N = 8 it needs 648 MAC per pixel, against 200 for k5 λ4 (3.24×). k7 would need 392 (1.96×).
- GWi still uses N convolutions against 2N for GWC at the same kernel, but its absolute cost is about three times that of the submitted configuration.
- Measured times come from E24.

**F16. Finding (submitted test results), Open (E20). GWi+ODPS ranked below the Gaussian gradient magnitude baseline on all three test sets.**
- In the submission (`eval_results/k5/ods_summary.csv`), the row labelled "Canny" is a Gaussian gradient magnitude with σ 1.4, without NMS (runbook A2). Its ODS is 0.534 (BSDS500), 0.641 (BIPED) and 0.674 (UDED). GWi+ODPS has 0.470, 0.574 and 0.645.
- Sobel is also above GWi+ODPS on BIPED (0.584). Phase congruency is above it on BSDS500 (0.524).
- The roadmap summary (§6) reports only GWC, GWi and GWi+ODPS, so this ranking does not appear there.
- The new selection raises GWi+ODPS on non-test data (0.489 BSDS500 train+val, 0.610 BIPED train), so whether it reaches this baseline on test is open. It cannot be assumed.
- Paper 2 (A-GWi, H3 below) found the same baseline not separable from its method (p = 0.82 on both datasets).
- *Added after E20:* the ranking holds in the revision. The new selection narrows the gap on BSDS500 and BIPED but not on UDED. See F24.

**F17. Finding. Final selection under amendment 2: k9 λ9, d = 4.5, N = 8, σ/λ = 0.56, γ = 0.5.**
- Mean ODS of GWi+ODPS 0.5558 (BSDS500 train+val 0.4953, BIPED train 0.6163). Mean ODS of GWi 0.5425 (0.4830, 0.6020).
- Next candidates: k9 λ10 0.5552, k7 λ9 0.5497, k9 λ8 0.5478, k7 λ10 0.5466.
- **The interior optimum at k9 is marginal.** k9 λ10 is 0.0006 lower on the mean, and the two splits disagree: BSDS500 prefers λ9 (0.4953 vs 0.4934), BIPED prefers λ10 (0.6170 vs 0.6163). The optimum is a plateau over λ9-10; the rule picks λ9.
- Under the manuscript's GWi criterion the best candidate would be k9 λ10 (0.5472), still at the largest λ evaluated for k9. Consistent with F4.
- ODPS gain at the selected kernel: +0.0123 (BSDS500), +0.0143 (BIPED).
- Under zero padding the selection may be biased against large kernels (H5). k9 was selected nonetheless.

**F18. Finding. The distance d (R2.5, R3.2), k9 on BSDS500 train+val.**
- d = λ/2 is the best of the tested d for λ = 3, 4, 5, 6, 8 and 9.
- For λ7 and λ10, a fixed d = 3 is better by 0.0034 and 0.0016.
- d = λ/2 is never more than 0.0034 below the best tested d. Answer to R3.2: the rule is near-optimal across λ, not exactly optimal.
- The ODPS gain at d = λ/2 falls with λ: +0.046 (λ3), +0.050 (λ4), +0.046 (λ5), +0.035 (λ6), +0.020 (λ7), +0.015 (λ8), +0.012 (λ9), +0.006 (λ10). Consistent with H1.

**F19. Finding. N, σ/λ and γ barely matter at the selected kernel (R2.6, R3.4), k9 λ9, BSDS500 train+val.**
- Every one-factor variant lies within 0.002 of the selected configuration:

  | Variant | GWi | GWi+ODPS | MAC per pixel |
  |---|---|---|---|
  | selected (N = 8) | 0.4830 | 0.4953 | 648 |
  | N = 4 | 0.4850 | 0.4962 | 324 |
  | N = 16 | 0.4826 | 0.4945 | 1296 |

  σ/λ (0.4, 0.7) and γ (0.75, 1.0) change ODS by at most 0.0006.
- So 4 orientations are as good as 8 at half the cost here. N = 8 is not changed, because the selection rule fixes it, but the manuscript cannot claim that 8 orientations are needed at this kernel.
- **Interpretation:** at λ9, σ = 5.0 px and σ/γ = 10 px, both larger than the window half-width of 4 px. The Gaussian envelope is therefore nearly flat and truncated by the window, so σ and γ have little left to change. Broad kernels are also broadly tuned in orientation.
- This is a property of the large-λ regime. In the five-candidate E11 around k7 λ5, N = 4 was 0.008 below N = 8.
- It adds to F7: at the selected configuration, the Gabor envelope plays little role.

## F. Consequences for the dissertation roadmap

Correction (9 Nov 2026, after reading the JESA 44740 files): R1, R4 and R5 were first written from the roadmap document in `arsip/`. That document describes Paper 2 as LDA-GaborNet, a learned model. The Paper 2 actually accepted is A-GWi (JESA 44740, final proof 18 Sep 2026): a handcrafted per-pixel imaginary Gabor method, k = 7 fixed, without ODPS. The entries below refer to that paper. The roadmap document itself is outdated on Paper 2 and needs updating.

**R1.** The roadmap transfer "k5 λ4 N8 as the Paper 2 default" is invalid (F2). It also does not describe what Paper 2 did: A-GWi used k = 7, and its static GWi baseline was k7 λ4.

**R2.** The numbers in roadmap §6 (GWi vs GWC +0.050 to +0.150 ODS, 2.2× faster) come from the submitted, test-selected protocol. They are replaced after E20 and E24. The §6 table should also show the classical baselines (F16).

**R3.** Notation clash: Paper 2 (published) uses ρL for local gradient activity and ρc for the sigmoid centre. This revision used ρ = (k//2)/λ, so the Paper 1 manuscript needs another symbol for it.

**R4.** A-GWi does not use ODPS, so C2 and C3 concern Paper 1 only.

**R5.** The roadmap premise for adaptation ("dense regions need high-frequency, small-λ kernels") was tested in Paper 2 and **not supported** (H4). Paper 1 must not restate it as motivation.

**R6. Histogram equalization across the papers (after E21, 10 Nov 2026).**
- **Paper 1:** HE lowers ODS of GWi and GWi+ODPS on all three test sets (F26). The protocol keeps HE as frozen.
- **Paper 2 (A-GWi):**
  - HE is applied to all six methods (Eq. 2, Algorithm 1 line 1, note to Table 3 of the final proof).
  - An "A-GWi without HE" ablation was planned in the revision plan (A4) but is not in the published Table 8. The effect of HE on A-GWi itself is therefore not measured.
  - The only measured effect is in the JESA response letter: binary Canny fell from 0.4441 to 0.4078 on BSDS500 when given the equalized image.
- **Paper 3 (PTBM, Research_Topic_KG-Wavelet_6Nopember2026.docx):**
  - Stage 1 is BT.601 grayscale and an Otsu mask, without HE.
  - In `ptbm_v2.py`, HE is optional (`--he`) and off by default. All pilot outputs in `ptbm_v2_out/` have `he=False`.
  - Brightness is handled by the zero-DC even kernel, not by global HE.
- **What can be carried forward:** two measurements on natural-scene edge benchmarks point the same way: HE is not neutral and lowered ODS.
  - This supports keeping PTBM without global HE, and writing that choice as a design rule of the framework.
- **What cannot be carried forward:**
  - None of this was measured on maize trays, on counting accuracy, or on UV fluorescence.
  - It was not measured on A-GWi either.
  - For Paper 3 it is a motivated default, not a result. If Paper 3 reports an HE on/off check, it should be fixed before its test images are opened, as in Paper 1.
- **Decision of the first author (10 Nov 2026):** PTBM (Paper 3) and the later stages of the dissertation will not use HE. The reason is the HE findings of Papers 1 and 2 above.
  - When this is written in Paper 3 or the dissertation, the evidence must be stated as it stands. In Paper 1, HE lowers GWi and GWi+ODPS. In Paper 2, HE lowered the binary Canny baseline; A-GWi itself was not measured without HE.
- **Pending (decided 10 Nov 2026, to be done later):** update the Paper 1 statements in Research_Topic_KG-Wavelet_6Nopember2026.docx listed in R7. Add the no-HE design rule to the same document.
- *Done (10 Nov 2026, 15:36):* see R7. The no-HE rule is a new paragraph in §2.3.2 ("Aturan desain kedua"). It carries the evidence and its limits as stated above.
  - Table 20 (stage 1) and line 1 of Algorithm 1 now say "tanpa HE". Line 1 of Algorithm 1 had said "HE opsional".

**R7. Paper 1 statements in Research_Topic_KG-Wavelet_6Nopember2026.docx that the revision has changed.**
- "GWi melebihi GWC sebesar +0,050 (BSDS500), +0,150 (BIPED v2), dan +0,140 (UDED) ODS dengan waktu 2,2× lebih cepat":
  - These are the submitted, test-selected numbers against raw GWC.
  - Against zero-DC GWC at the selected kernel the gaps are +0.016, +0.039 and +0.084 (F23, F25). At k5 λ4, zero-DC GWC is above GWi on BSDS500.
  - The 2.2× figure awaits E24.
- RQ1 "apakah ODPS menekan side-lobe": the side-lobe mechanism does not apply at the reported kernels (F12). ODPS improves ODS significantly on BSDS500 only (F25).
- Design rule 1 "Komponen real redundan untuk tepi langkah (Paper 1)" must be narrowed (C4).
- The topic document's own argument for a zero-DC even kernel in Paper 3 is supported by F23: most of GWC's deficit in Paper 1 came from the DC response of the raw real kernel.
- *Done (10 Nov 2026, 15:36):* the edits are tracked changes in a new file, `D:\Proposal Disertasi\Research_Topic_KG-Wavelet_10Nopember2026.docx`. The 6 Nov file is unchanged.
  - **Edited:**
    - the three statements above;
    - four more statements that carried the same claims:
      - contribution 1 in §1.6.1;
      - note 1 of the roadmap figure;
      - point 1 of "Kesinambungan antar-paper" in §3.5.1;
      - the Paper 1 grid search in §2.3.4, now marked as selected on test data in the submission.
  - **RQ1 is kept as written.** Its answer after the revision is added:
    - yes to the first part, also against zero-DC GWC at k9 λ9;
    - the side-lobe part is not supported.
    The question is not rewritten to fit the result.
  - **The 2.2× figure** is replaced by the E24 values: filtering 2.1× at k9 λ9; full pipeline 1.56×. The text also states that the Gaussian gradient has higher ODS than every Gabor variant and is about 5.5× faster than GWi+ODPS (F24, F28).
  - **Not changed:** status words ("under review") and the reference entry of Paper 1.
  - **Author list.** That entry has four authors, while README.md and CITATION.cff of v2.0.0 had three. The submitted PDF (DSP-D-26-02462.pdf) has four: Yudhistiro, Adi (BRIN), Basuki, Rijati. README.md and CITATION.cff were corrected to match it in v3.0.0.
  - **Checks done:**
    - the XML is well-formed;
    - with all changes rejected, the text equals the original paragraph by paragraph.
  - **Not done:** the file was not opened in Word. No Word or LibreOffice is installed on this machine.

## H. Consistency with Paper 2 (A-GWi, JESA 44740, accepted)

Paper 2 was revised after review and accepted. Several of its corrected statements bear directly on Paper 1. Paper 1 must not contradict a published paper by the same authors. Sources: `D:\Paper AGWi\REVIEW JESA\Response_Letter_JESA_44740_15082026.md` and the final proof.

**H1. Finding, already published. A lower carrier frequency (larger λ) raises ODS of static GWi.**
- In A-GWi Table 8 (BSDS500 test), a static k7 kernel at f = 0.05 cycles/px (λ = 20) reaches 0.535. The static GWi baseline at k7 λ4 reaches 0.417.
- F4 and F7 of this revision are therefore a replication on non-test data with Paper 1's σ = 0.56λ, not a new discovery. Paper 1 must cite A-GWi for it.
- The two papers' kernels differ (A-GWi: σ = 0.1874/f; Paper 1: σ = 0.56λ), so the numbers are not interchangeable.

**H2. Consistency item, decision before the freeze. Definitions of OIS and AP.**
- JESA reviewers flagged that the A-GWi submission computed OIS as the mean of per-image best F (a different accumulation from ODS), which allowed OIS < ODS. A-GWi corrected it to dataset-level accumulation.
- The Paper 1 revision currently reports `OIS` = mean of per-image best F and `AP` = mean of per-image curves (submitted 04c definitions, `ois_legacy`, `ap_legacy`). These are exactly the definitions corrected in Paper 2.
- The dataset-accumulated versions are computed from the same counts.
- **Decided 9 Nov 2026, before the freeze and before any test split was opened (CHANGELOG.md).**
  - Primary OIS and AP now use dataset-level accumulation, with AP identical to the A-GWi definition: monotone precision, checked on 118 count files.
  - The submitted definitions remain as `OIS_legacy` and `AP_legacy`.
  - The change does not favour one direction. Over the 118 non-test count files, the new OIS is higher than the legacy one in 96 cases and lower in 22. The new AP is lower in 96 and higher in 22.

**H3. Consistency item. Binary Canny.**
- A-GWi's reviewers also flagged a binary Canny map: 99 thresholds give one operating point, and AP is zero.
- The Paper 1 revision adds OpenCV Canny 50/150 (binary), as §4.3 describes. It must be reported with the same caveat: one operating point, ODS = OIS, AP not comparable.
- The Gaussian gradient magnitude that A-GWi calls "Canny" (described there explicitly) is Paper 1's GaussGradMag1.4. Paper 1 must say so.
- A-GWi states that this detector gave 0.533 under its protocol, against 0.534 in "our previous work" (the Paper 1 submission). If E20 under the revised protocol gives a different value, the reason must be stated.
- *Added after E20:* GaussGradMag1.4 gives ODS 0.5334 on BSDS500 test (submission 0.5336, A-GWi 0.533). BIPED: 0.6407 vs 0.6406. UDED: 0.6734 vs 0.6737.
  - Probable cause of the difference of at most 0.0003: the submitted code (`src/baselines.py`) blurs an 8-bit image, so the smoothed image is rounded to integers. The revision blurs in floating point. This was not checked by a separate run.
  - The 0.533 of A-GWi and the 0.5334 of the revision agree to three decimals.
- *Added after E20:* binary Canny 50/150 gives ODS 0.3353, 0.3460 and 0.5568. ED gives 0.3508, 0.3275 and 0.5540. Both are single-operating-point maps: ODS = OIS, and their AP is not comparable with that of the soft maps.

**H4. Finding, already published. The adaptation premise was not supported.**
- A-GWi Table 8: making the frequency modulation active across its full range lowered ODS (0.361). The paper states that the hypothesis "high-activity regions require high-frequency kernels" is not supported on BSDS500.
- 92.8% of pixels received a frequency near the lower bound, so the per-pixel mechanism selected an operating point rather than improving on the best static one.

**H5. Consistency item, disclosed rather than changed. Border handling.**
- A-GWi's reviewers found that zero padding for the static Gabor baselines created spurious border responses and lowered their precision. A-GWi switched all methods to the same border handling.
- The Paper 1 revision keeps the manuscript protocol: zero padding for the Gabor methods (GWi, GWi+ODPS, GWC) and reflect-101 for the other baselines (config `protocol.border: paper`).
- Within the Gabor comparison the setting is the same, so GWi vs GWC is unaffected. Against the classical baselines, it disadvantages the Gabor methods.
- Changing it now would mean redoing the selection. It is kept, and the manuscript must state it with the Paper 2 observation.
- **Decision, 10 Nov 2026 ~00:30, by the first author:** keep zero padding; do not redo the selection (about 10 h). The decision was taken before the diagnostic below was read.
- **Diagnostic only, not a reportable result.** It used 20 BSDS500 val images and per-image F at the zero-padding ODS threshold, without re-optimizing the threshold.
  - Under zero padding, 15-20% of the pixels above threshold lie in the border band of width k//2+1, which covers 3-5% of the image area. Under reflect-101 this falls to 3-5%, about the band's area share.
  - Mean per-image F rose with reflect for every Gabor variant:

    | Kernel | GWi | GWi+ODPS |
    |---|---|---|
    | k5 λ4 | +0.034 | +0.037 |
    | k7 λ9 | +0.043 | +0.042 |
    | k9 λ9 | +0.046 | +0.045 |

  - The ODPS gain at the fixed threshold was about the same under both border modes.
  - GWC was not measured.
- **Consequences:**
  - The absolute ODS of all Gabor methods is likely understated, more so on BSDS500 (small images) and for larger kernels.
  - Zero padding penalizes large kernels more, so it may bias the selection toward smaller k. k9 was selected nonetheless.
  - The comparison against the classical baselines (F16) is confounded by this handicap. The manuscript must not draw a ranking against them on BSDS500 without stating it.
  - GWi vs GWC uses the same border and stays internally fair. The size of the effect on that gap is unknown.
- **No border sensitivity rows are added to E20** (decision of the first author, 10 Nov 2026). Border handling was not raised by the reviewers, so the revision keeps to what they asked. The limitation is stated in the text without test-set numbers.
- *Correction (10 Nov 2026, while E21 was running):* R2.3 does mention border handling. It asks only that the handling be **described** for reproducibility: how ODPS samples x ± d·n, what happens at the image edge, and how the kernel is discretized.
  - It does not ask for a different border mode or a sensitivity test.
  - The decision above therefore stands. The zero-padding specification (WP4), and this limitation, are part of the answer to R2.3 and R2.12.

**H6. Consistency item. Runtime.**
A-GWi measured static GWi k7 at 15.54 ms and GWC at 33.70 ms per BSDS500 image (ratio 2.17, single thread, minimum of 3 runs). Paper 1 E24 uses the median of 5 runs. If the machines or timing rules differ, both must be stated, and E24 values for k7 should be compared with these.

## I. Test-set results (E20)

Source: `results/test/summary.csv` and `results/test/legacy_check.csv`. ODS, with OIS and AP as defined in H2 (dataset accumulation). The submitted definitions are kept in the same files as `OIS_legacy` and `AP_legacy`. Differences below are point estimates; none has a CI yet (E22).

| Method | BSDS500 ODS | BSDS500 AP | BIPED ODS | BIPED AP | UDED ODS | UDED AP |
|---|---|---|---|---|---|---|
| GWi k9 λ9 | 0.4998 | 0.3739 | 0.6202 | 0.5808 | 0.6476 | 0.5508 |
| GWi+ODPS k9 λ9 | 0.5120 | 0.3970 | 0.6281 | 0.5922 | 0.6451 | 0.5524 |
| GWC raw k9 λ9 | 0.3176 | 0.1492 | 0.4111 | 0.2318 | 0.3753 | 0.1813 |
| GWC zero-DC k9 λ9 | 0.4836 | 0.3074 | 0.5811 | 0.4758 | 0.5634 | 0.3864 |
| GWi k5 λ4 | 0.4443 | 0.3365 | 0.5602 | 0.5086 | 0.6072 | 0.5267 |
| GWi+ODPS k5 λ4 | 0.4696 | 0.3860 | 0.5744 | 0.5371 | 0.6449 | 0.6097 |
| GWC raw k5 λ4 | 0.3941 | 0.2431 | 0.4106 | 0.2911 | 0.4668 | 0.3126 |
| GWC zero-DC k5 λ4 | 0.4536 | 0.3064 | 0.5525 | 0.4718 | 0.5818 | 0.4315 |
| Canny 50/150 (binary) | 0.3353 | n/c | 0.3460 | n/c | 0.5568 | n/c |
| Sobel 3×3 | 0.4643 | 0.4058 | 0.5844 | 0.6096 | 0.6390 | 0.6405 |
| LoG 7×7 σ 1.4 | 0.4524 | 0.3710 | 0.5299 | 0.5180 | 0.6219 | 0.6250 |
| PC | 0.5089 | 0.4499 | 0.5004 | 0.4570 | 0.5853 | 0.5199 |
| ED (binary) | 0.3508 | n/c | 0.3275 | n/c | 0.5540 | n/c |
| GaussGradMag σ 1.4 | **0.5334** | **0.4920** | **0.6407** | **0.6845** | **0.6734** | **0.6784** |

n/c: binary map with one operating point; AP is not comparable (H3).

**F20. Process. E20 ran once, and the submitted numbers are reproduced.**
- Run on 10 Nov 2026, 00:59:36 to 03:27:08 WIB (2 h 27 min), from commit 7ae7ba5 (tag `freeze-2026-11-10`). See PROCESS_LOG.md. There were 14 methods and three test sets: BSDS500 (200 images), BIPED (50) and UDED (30).
- **Reproduction is exact.** GWi, GWi+ODPS and raw GWC at k5 λ4, under the submitted definitions, match the submission to four decimals in ODS, OIS and AP on all three datasets (`legacy_check.csv` vs `eval_results/k5/ods_summary.csv`). Sobel matches as well.
- The revision code therefore computes what the submitted code computed for these methods. The differences in this section come from the kernel, the metric definitions or the baseline definitions, not from a change of code.
- LoG, PC and ED differ from the submission, because the revision runs them as §4.3 describes (R2.8, README). The revision values are not uniformly higher or lower than the submitted ones:

  | Baseline | Revision (BSDS500 / BIPED / UDED) | Submission | Direction |
  |---|---|---|---|
  | LoG | 0.4524 / 0.5299 / 0.6219 | 0.4706 / 0.5481 / 0.6364 | lower on all three |
  | PC | 0.5089 / 0.5004 / 0.5853 | 0.5245 / 0.5688 / 0.5654 | lower on BSDS500 and BIPED, higher on UDED |
  | ED | 0.3508 / 0.3275 / 0.5540 | 0.3467 / 0.3133 / 0.5376 | higher on all three |

  Lower LoG and PC values make GWi look better against them. The revision does not tune any baseline.

**F21. Finding. Selected kernel (k9 λ9) vs submitted kernel (k5 λ4) on test.**

| ODS difference, k9 λ9 minus k5 λ4 | BSDS500 | BIPED | UDED |
|---|---|---|---|
| GWi | +0.0555 | +0.0600 | +0.0404 |
| GWi+ODPS | +0.0424 | +0.0537 | **+0.0002** |

- On UDED, GWi+ODPS does not gain from the new kernel in ODS. Its OIS is lower by 0.0260 and its AP by 0.0573.
- UDED has no non-test split, so this is the only check of the selection on data of a kind it never saw. For GWi+ODPS, the selection did not carry over to UDED. For GWi alone, it did in ODS (+0.0404) and AP (+0.0241), but not in OIS (−0.0008).
- UDED has 30 images, so the CIs (E22) will be wide.

**F22. Finding. The ODPS gain on test is smaller at the selected kernel and negative on UDED.**

| GWi+ODPS minus GWi | BSDS500 | BIPED | UDED |
|---|---|---|---|
| k9 λ9, ODS | +0.0122 | +0.0079 | **−0.0025** |
| k9 λ9, OIS | +0.0058 | +0.0019 | −0.0049 |
| k9 λ9, AP | +0.0231 | +0.0114 | +0.0016 |
| k5 λ4, ODS (same as the submission) | +0.0253 | +0.0142 | +0.0377 |
| k5 λ4, AP | +0.0495 | +0.0285 | +0.0830 |

- On BSDS500 the test gain at k9 λ9 matches the non-test value (+0.0123). On BIPED it is about half (+0.0143 non-test). On UDED it is negative.
- **Descriptive check of H1, not a test.** On all three sets the gain is smaller at k9 λ9 ((k//2)/λ = 0.44) than at k5 λ4 (0.50). That is the direction of H1, but two kernels cannot test it.
- **Trade-off.** The kernel that makes GWi strongest leaves ODPS little to add. Of the k9 λ9 improvement in GWi+ODPS over the submitted configuration, most comes from GWi itself, not from ODPS.
- The manuscript may say "improves" only for datasets where the E22 CI excludes 0. On UDED, the point estimate is negative.

**F23. Finding. Most of the submitted GWi > GWC gap is the DC response of the raw real kernel (R1.5).**

| GWi minus GWC, ODS | BSDS500 | BIPED | UDED |
|---|---|---|---|
| raw GWC, k5 λ4 (the submitted comparison) | +0.0502 | +0.1496 | +0.1404 |
| zero-DC GWC, k5 λ4 | **−0.0093** | +0.0077 | +0.0254 |
| raw GWC, k9 λ9 | +0.1822 | +0.2091 | +0.2723 |
| zero-DC GWC, k9 λ9 | +0.0162 | +0.0391 | +0.0842 |

- Removing the DC of the real kernel removes 69% to 119% of the raw gap.
- At the submitted kernel k5 λ4, zero-DC GWC is above GWi on BSDS500 and only slightly below it on BIPED. The submitted statement "the real component is redundant", supported by a gap of 0.05 to 0.15, rested mostly on comparing against a GWC that carried a brightness (DC) term.
- At k9 λ9, GWi stays above zero-DC GWC on all three sets. The gap is moderate on BSDS500 and BIPED and larger on UDED.
- GWi+ODPS minus zero-DC GWC at k9 λ9 is +0.0284, +0.0470 and +0.0817.
- In AP, GWi stays further above zero-DC GWC: +0.0665, +0.1050 and +0.1644 at k9 λ9; +0.0301, +0.0368 and +0.0952 at k5 λ4.
- Raw GWC at k9 λ9 is the lowest of all 14 methods on BSDS500 and UDED. This is the DC leakage predicted in F14.
- The roadmap §6 numbers (+0.050 to +0.150) must be replaced (R2). The manuscript must report the zero-DC comparison as the fair one.

**F24. Finding. The Gaussian gradient magnitude is above every Gabor variant on all three test sets.**
- GaussGradMag σ 1.4 ranks first in ODS, OIS and AP on BSDS500, BIPED and UDED.
- Gap of GWi+ODPS k9 λ9 to it:
  - ODS: −0.0214, −0.0126 and −0.0283.
  - AP: −0.095, −0.092 and −0.126.
- Compared with the submitted configuration, the ODS gap narrows on BSDS500 (−0.0638 → −0.0214) and BIPED (−0.0663 → −0.0126). It does not narrow on UDED (−0.0285 → −0.0283).
- **ODS rank of GWi+ODPS k9 λ9 among the 14 methods:** 2nd on BSDS500, 2nd on BIPED, and 3rd on UDED, behind GaussGradMag and GWi k9 λ9.
- PC on BSDS500 is 0.5089, against 0.5120 for GWi+ODPS (+0.0031). That is probably not separable (E22).
- **Sobel:** GWi+ODPS k9 λ9 is above it in ODS on all three sets (+0.0477, +0.0437 and +0.0061). Sobel is above GWi+ODPS in AP on all three sets (−0.0088, −0.0174 and −0.0881), and in OIS on UDED (−0.0241).
- **AP rank of GWi+ODPS k9 λ9:** 4th on BSDS500 (behind GaussGradMag, PC and Sobel), 3rd on BIPED (behind GaussGradMag and Sobel), and 5th on UDED (behind GaussGradMag, Sobel, LoG and GWi+ODPS k5 λ4).
- The Gabor maps are therefore weak in AP relative to gradient baselines. A ranking claim cannot rest on ODS alone.
- **Confound (H5).** The Gabor methods use zero padding, and the baselines use reflect-101. How much this lowers the Gabor ODS on test is not known.
  - The H5 diagnostic measured per-image F at a fixed threshold on 20 val images, not ODS. It cannot be used to adjust these numbers.
  - The ranking is reported as measured, with the confound stated.
- **Relation to Paper 2.** A-GWi reports 0.534 on BSDS500 test with the same border handling for all methods. GWi+ODPS k9 λ9 reaches 0.5120 with zero padding.
  - The two values are not directly comparable.
  - In both papers, the Gaussian gradient magnitude is at the level of the best handcrafted Gabor variant or above it.

**F25. Finding. Paired statistics (E22): ODPS improves ODS only on BSDS500; GWi is above both GWC variants.**
- Run on 10 Nov 2026, 05:26:10 to 05:27:41 WIB (91 s), at commit 7ae7ba5. Files: `results/stats/pairs.csv`, `variability.csv` and `claims_guard.json`.
- Statistics:
  - Paired bootstrap over images, 2000 resamples, seed 20261107, giving a 95% CI of ΔODS.
  - Wilcoxon signed-rank on per-image F, with Holm correction over the 9 tests of the reviewer family.
- Pre-registered rule: "improves" only when the CI of ΔODS excludes 0.

  | Pair (k9 λ9) | Dataset | ΔODS | 95% CI | Wilcoxon p (Holm) | Images where A is better | Allowed verb |
  |---|---|---|---|---|---|---|
  | GWi+ODPS vs GWi | BSDS500 | +0.0122 | [0.0090, 0.0158] | 2.7e-10 | 70.5% | improves |
  | GWi+ODPS vs GWi | BIPED | +0.0079 | [−0.0076, 0.0203] | 1.1e-4 | 80.0% | does not differ |
  | GWi+ODPS vs GWi | UDED | −0.0025 | [−0.0161, 0.0121] | 0.75 | 46.7% | does not differ |
  | GWi vs GWC raw | BSDS500 / BIPED / UDED | +0.1822 / +0.2091 / +0.2723 | all exclude 0 | ≤ 1.5e-8 | 97-99% | improves |
  | GWi+ODPS vs GWC raw | BSDS500 / BIPED / UDED | +0.1944 / +0.2170 / +0.2698 | all exclude 0 | ≤ 1.5e-8 | 97-100% | improves |
  | GWi vs GWC zero-DC (R1.5, outside Holm family) | BSDS500 | +0.0161 | [0.0117, 0.0204] | 4.0e-21 (raw) | 82.5% | improves |
  | same | BIPED | +0.0391 | [0.0171, 0.0671] | 1.0e-5 (raw) | 76.0% | improves |
  | same | UDED | +0.0842 | [0.0548, 0.1133] | 4.7e-8 (raw) | 93.3% | improves |

- **BIPED, ODPS vs GWi: the two tests disagree, and the pre-registered rule decides.**
  - Per-image F favours ODPS on 80% of images (Holm p = 1.1e-4).
  - The CI of ΔODS includes 0. ODS pools counts over images, so a few large or edge-dense images can outweigh many small per-image gains.
  - The manuscript must use "does not differ" for BIPED. It may report the per-image result alongside it. The Wilcoxon result must not be used to upgrade the verb.
- **UDED:** no evidence either way (n = 30, p = 0.75).
- **What E22 does not cover:**
  - Only the k9 λ9 pairs above were tested.
  - The k5 λ4 differences (F21-F23) have no CI, including zero-DC GWC above GWi on BSDS500.
  - The comparisons against the classical baselines (F24) also have no CI. The pre-registered family covers only the reviewers' Gabor pairs, so those rankings stay descriptive.
  - The per-method CIs in `variability.csv` are marginal. Overlap or non-overlap between them is not a test, and must not be used to claim that the Gaussian gradient magnitude and GWi+ODPS are "not separable" or "separable".

**F26. Finding. Histogram equalization lowers ODS of the proposed method on all three test sets; /255 has no effect (E21, R2.7).**
- Run on 10 Nov 2026, 06:05:26 to 06:27:53 WIB (22 min), at commit 87b21a5, with the frozen configuration k9 λ9. Nothing was selected. File: `results/preproc/preproc_ablation.csv`.

  | Method (k9 λ9) | Dataset | ODS with HE (manuscript protocol) | ODS without HE | Effect of HE |
  |---|---|---|---|---|
  | GWi | BSDS500 | 0.4998 | 0.5053 | −0.0055 |
  | GWi+ODPS | BSDS500 | 0.5120 | 0.5231 | −0.0111 |
  | GWi | BIPED | 0.6202 | 0.6825 | −0.0623 |
  | GWi+ODPS | BIPED | 0.6281 | 0.6872 | −0.0591 |
  | GWi | UDED | 0.6476 | 0.6737 | −0.0261 |
  | GWi+ODPS | UDED | 0.6451 | 0.6812 | −0.0361 |

- **OIS and AP:**
  - On BIPED and UDED, HE also lowers OIS (−0.018 to −0.035) and AP (−0.005 to −0.049).
  - On BSDS500 its effect on OIS and AP is close to zero. For GWi, OIS is +0.0007 and AP +0.0083 with HE. For GWi+ODPS, OIS is −0.0039 and AP +0.0005.
- **/255:** ODS, OIS and AP are identical with and without /255, for both methods on all three sets. This is as expected: the filtering is linear and the maps are min-max normalized per image.
- **Answer to R2.7.** The GWi+ODPS results are not produced by preprocessing. HE lowers them.
  - The statement that HE is important is not supported on these test sets.
  - A low-contrast subset was not tested (the reviewer did not ask for one). The manuscript therefore must not claim that HE helps low-contrast images either.
  - The §3.1 sentence calling the [0, 1] normalization "necessary" must be corrected: it does not change the evaluated maps.
- **What must not be done with this result.**
  - The protocol stays as frozen, with HE. Switching to "no HE" now would choose the preprocessing on the test sets, the problem raised in R2.1.
  - The kernel (k9 λ9) was selected with HE on non-test data. Whether the selection would differ without HE is unknown.
- **Baselines.**
  - In the main tables every method uses HE (same protocol, R2.8).
  - E21 measures only GWi and GWi+ODPS, which is what R2.7 asks ("the proposed method with and without these preprocessing steps").
  - The no-HE values must not be compared with baselines run with HE. For example, GWi+ODPS without HE on BIPED (0.6872) is not comparable with GaussGradMag with HE (0.6407). Whether the baselines also gain without HE is not known.
- **ODPS gain without HE (descriptive):** +0.0178, +0.0047 and +0.0075. With HE it is +0.0122, +0.0079 and −0.0025. On UDED, the sign of the ODPS gain depends on the preprocessing. This is consistent with F25: no difference on UDED.
- **No confidence intervals.** The E21 differences are not part of the pre-registered E22 family, so they are point estimates.
- **Possible reason, not tested.** HE stretches the contrast of flat and textured regions. That can create gradients that the Gabor filter reports as edges.

**F27. Finding. ODPS thins rather than relocates. Its matched distance grows by a sub-pixel amount, and some images lose true boundaries (E25, R1.3).**
- Run on 10 Nov 2026, 07:30:18 to 07:32:11 WIB, at commit c25d821, frozen k9 λ9.
  - Files: `results/qualitative/localization.csv`, `localization_summary.csv`, and 10 figures (the images of Figures 7, 9 and 11).
- **Operational definition**, written in `scripts/25_qualitative_odps.py` before the run:
  - Per image, GWi and GWi+ODPS are compared at each method's own dataset ODS threshold.
  - A distortion would show as a larger matched prediction-GT distance, or as a recall drop at similar precision.
  - The thresholds differ (BSDS500 0.23 vs 0.20, BIPED 0.18 vs 0.16, UDED 0.10 vs 0.08), so each difference mixes the effect of ODPS with that of its lower threshold.
- **Results.** Per-image differences, GWi+ODPS minus GWi:

  | | BSDS500 (200) | BIPED (50) | UDED (30) |
  |---|---|---|---|
  | Precision, mean | −0.0015 | +0.0053 | +0.0135 |
  | Recall, mean | +0.0289 | +0.0112 | −0.0109 |
  | Images with lower recall | 13% | 22% | 53% |
  | Mean matched distance (base GWi) | +0.070 px (1.386) | +0.085 px (1.877) | +0.015 px (1.207) |
  | Images with larger mean distance | 94% | 88% | 60% |
  | P90 distance, median change | 0 px | 0 px | 0 px |
  | Largest P90 increase, one image | +0.76 px | +1.61 px | +0.76 px |

- **Mechanism.**
  - On BSDS500, ODPS does not raise precision at its own threshold.
  - It removes the shoulder pixels around a ridge, so a lower threshold keeps precision while adding recall. This is the directional thinning of F12, not side-lobe removal.
  - On UDED the trade goes the other way: precision rises, recall falls. This is consistent with no ODS difference on UDED (F25).
- **Against the pre-defined criterion:**
  - The matched distance grows on most images. A small localization change is therefore present, and has to be reported.
  - Its size is less than 0.1 px on average, about 5% of the base distance. The matching tolerance is about 4.3 px on BSDS500 and about 11 px on BIPED.
  - Whether the increase comes from ODPS moving responses, or from the extra recall at the lower threshold matching farther pixels, cannot be separated with this design.
- **Failure cases (R1.5):**
  - BIPED RGB_139: recall 0.861 → 0.610, precision 0.735 → 0.701, P90 distance +1.6 px.
  - BIPED RGB_029: recall −0.128, precision −0.030.
  - BSDS500 108004: recall −0.073, precision −0.067.
  - UDED 28-img_043_SRF_2_HR (one of the figure images, a façade grid): recall −0.107, precision +0.081. ODPS removes many pixels along the paired edges of the bars.
- **Figures.**
  - The ten figure images are those of the submitted Figures 7, 9 and 11. Nine of them show a gain or a small change. None of the three worst cases above is among them except UDED 28-img.
  - A figure set made only of these images would understate the failures. At least the worst case should be shown.
  - In the difference panel, green marks GT pixels not detected after ODPS. That includes pixels GWi also missed, so green does not mean "lost by ODPS".
  - **Border responses are visible.** In BSDS500 36046 the image border appears as a detected line in the GWi+ODPS map. This is the zero-padding effect of H5, visible in the qualitative figures.
  - The figures must not be cropped to hide it. The caption should state it (R2.3 asks for the border handling to be described).
- **No confidence intervals.** E25 is descriptive, and its differences are not part of the E22 family.
- *Added after the failure-case figure (10 Nov 2026, 07:37 to 07:39, run E25b, CHANGELOG):* BIPED RGB_139 was added to the figure list. The re-run reproduced `localization.csv` byte for byte.
- **Failure mechanism (BIPED RGB_139).** The image is dominated by louvred panels: many parallel horizontal slats.
  - On the panels, the spacing between neighbouring GT edges has a median of 5 to 6 px (IQR 2 to 7 px), measured on three columns.
  - At λ9, ODPS compares each pixel with neighbours about 4 px away along the gradient (d = 4.5, rounded, F13). Neighbouring true edges therefore fall inside the suppression distance, and ODPS removes the weaker one.
  - The difference panel shows exactly this: red and green along the slats.
  - The UDED façade grid (28-img) is the same case with the paired edges of the bars.
  - **Limitation for the manuscript (R1.3, R2.5, R2.12):** ODPS assumes that one edge is isolated within about d pixels. For parallel edges spaced at or below d it removes true edges.
  - This links the choice d = λ/2 to the smallest edge spacing the method can keep (R2.2 asks for the relation between λ and d).

**F28. Finding. GWi halves the filtering time of GWC, but at the selected kernel the full GWi+ODPS pipeline is 1.56× faster than GWC and 5.5× slower than the Gaussian gradient baseline (E24).**
- **Run:** 10 Nov 2026, 08:08:51 to 08:36:57 WIB (28 min), at commit bb6905d. Files: `results/runtime/summary.csv`, `per_image.csv`, `mac.csv`, `odps_d.csv`, `kernels.csv` and `env.json`.
- **Protocol** (`scripts/24_runtime.py`, written before the run):
  - one thread (`cv2.setNumThreads(1)`, OMP/MKL/OpenBLAS = 1);
  - 3 warm-up images, then the median of 5 runs per image, and the mean ± std over the images;
  - stage 1 (preprocessing) is reported separately.
- **Machine:** Intel Core i5-14400 (10 cores, 16 threads), Windows 11, Python 3.13.13, OpenCV 4.13.0.
  - The machine was not fully idle. Just before the run, the desktop app and an open Notepad window used about 0.6 of one core. This has to be stated with the numbers.
  - Per-image spread is small: GWi k9 λ9 on BSDS500 is 29.2 ± 1.7 ms.
- **BSDS500 test, ms per image (filter + pool + ODPS; preprocessing 3.5 ms not included):**

  | Method | k9 λ9 (selected) | k5 λ4 (submitted) |
  |---|---|---|
  | GWi | 29.2 (filtering 28.4) | 11.2 (filtering 10.4) |
  | GWi+ODPS | 38.7 | 21.5 |
  | GWC raw | 60.3 (filtering 59.5) | 24.8 (filtering 24.0) |
  | GWC zero-DC | 60.7 | 24.8 |

  Baselines: Gaussian gradient σ 1.4: 7.0, Sobel: 6.8, LoG: 1.7, Canny: 2.0, ED: 4.7, PC: 328.3.
- **Reproduction of the submitted numbers (k5 λ4):** GWi 11.2 ms (submitted 11.3), GWC 24.8 ms (24.6), ratio 2.22× (2.2×), PC 328.3 ms (326.5).
  - GWi+ODPS is 21.5 ms against the submitted 25.9 ms. The ODPS implementation of the revision is faster than the submitted one; the result is the same (E01).
  - The submitted measurement machine is not recorded in the submission, so the agreement is approximate by nature.
- **Filtering stage (R2.10):** GWC over GWi is 2.09× at k9 λ9 and 2.31× at k5 λ4. The halving holds, as expected from N against 2N convolutions.
  - The k9 kernel costs 2.73× the k5 kernel in filtering time, against 3.24× in MAC per pixel.
- **Full pipeline (R3.3):**
  - ODPS needs the argmax instead of the max. Pooling goes from 0.8 to 6.2 ms, and ODPS itself takes 3.8 ms.
  - Its overhead is therefore 9.6 ms on BSDS500 (+33% over GWi), 70 ms on BIPED (+46%) and 16 ms on UDED (+33%).
  - At the submitted k5 λ4, GWi+ODPS (21.5 ms) is only 1.15× faster than GWC (24.8 ms); with preprocessing, 25.0 against 28.3 ms. The reviewer's point that the full pipeline is not clearly faster than GWC is essentially right for the submitted configuration.
  - At k9 λ9 filtering dominates, and GWi+ODPS is 1.56× faster than GWC (38.7 against 60.3 ms; 1.51× with preprocessing).
- **Cost of d (R2.5):** ODPS takes 3.61 to 3.64 ms for d = 1, 2, 3 and 4.5. With nearest sampling, its cost does not depend on d.
- **Kernel construction:** about 0.2 ms per configuration, done once (excluded).
- **Against the baselines:**
  - The Gaussian gradient σ 1.4, which has the highest ODS on all three test sets (F24), takes 7.0 ms on BSDS500. GWi+ODPS takes 38.7 ms, 5.5× more; BIPED 42.0 against 224.0 ms (5.3×).
  - Even this understates the gap. The runtime script always computes the direction quantization for the gradient baselines (4.5 ms of their 7.0 ms), although they use no NMS. Their filtering alone takes 2.5 ms (Gaussian gradient) and 1.7 ms (Sobel).
  - The submitted comparison "12.6× faster than Phase Congruency" uses the slowest baseline. At k9 λ9 it becomes 8.5×. The Gaussian gradient comparison is the informative one, and it is unfavourable.
- **Relation to Paper 2 (H6):** A-GWi measured static GWi k7 at 15.54 ms and GWC at 33.70 ms (ratio 2.17; minimum of 3 runs, another machine). The ratios here (2.09× and 2.31× in filtering) are consistent. The absolute times are not comparable across machines and timing rules.

**F29. Finding. The three learned detectors are far above GWi+ODPS on BSDS500 and BIPED and two of them on UDED; GWi+ODPS is 2.4 to 16× cheaper on one CPU thread, but the Gaussian gradient is cheaper still and more accurate, so "training-free/CPU" does not by itself give GWi+ODPS a place on the accuracy-cost trade-off (E23).**
- **Run:** 10 Nov 2026, 10:03:05 to 11:35:45 WIB, at commit 0233bd2 (`tools/external/run_e23.sh`; times in `logs_local/runs.csv`, rows E23a to E23d). Setup of the separate environment and the official repositories: 09:58 to 10:03.
  - Maps: E23a, 10:03:05 to 10:06:48. Evaluation: E23b, 10:06:48 to 10:51:37. Cost: E23c and E23d, 10:51:37 to 11:35:45.
  - Correction run, 11:40:01 to 12:09:02 (E23c again for all three with the PyTorch counter; E23c and E23d_PiDiNet_converted). The thop counts of the first run are kept in `results/external/cost/*/flops_thop.csv`; its E23c logs were overwritten.
- **Detectors** (official repositories and weights; `results/external/models.yaml`):
  - TEED (xavysp/TEED, commit 40fa4b1, BIPED checkpoint 7);
  - LDC (xavysp/LDC, commit 8b6e328, BIPED checkpoint 16);
  - PiDiNet (hellozhuo/pidinet, commit d21aa88, `table5_pidinet`, BSDS500 train+val with PASCAL VOC).
  - Test-time processing copies each repository's test code (`tools/external/infer_external.py`). The maps are written without the white-background inversion of the official scripts; no value is changed otherwise.
  - No method published in 2024 or later was added (runbook E23: "usahakan"). The paper has to say this.
- **Evaluation:** `scripts/23_eval_external.py`, written with the pre-registration (8 Nov 2026), with the same evaluator, thresholds and matching as every other method.
  - Maps are evaluated without NMS, which is the treatment of the other maps (binarize, then thin). This is the comparable row.
  - The script also reports "+NMS" rows; see the NMS paragraph below.
- **Results, test sets, without NMS** (`results/external/summary.csv`):

  | Method | Trained on | BSDS500 ODS / OIS / AP | BIPED ODS / OIS / AP | UDED ODS / OIS / AP |
  |---|---|---|---|---|
  | TEED | BIPED | 0.612 / 0.628 / 0.489 | 0.786 / 0.794 / 0.788 (in-domain) | 0.789 / 0.801 / 0.707 |
  | LDC | BIPED | 0.667 / 0.683 / 0.602 | 0.825 / 0.829 / 0.824 (in-domain) | 0.762 / 0.776 / 0.665 |
  | PiDiNet | BSDS500 | 0.751 / 0.763 / 0.669 (in-domain) | 0.690 / 0.697 / 0.563 | 0.558 / 0.575 / 0.395 |
  | GWi+ODPS k9 λ9 | — (selected on BSDS500/BIPED non-test data) | 0.512 / 0.542 / 0.397 | 0.628 / 0.670 / 0.592 | 0.645 / 0.690 / 0.552 |
  | Gaussian gradient σ 1.4 | — | 0.533 / 0.563 / 0.492 | 0.641 / 0.687 / 0.685 | 0.673 / 0.730 / 0.678 |

  - The gap to the best learned detector is +0.239 ODS on BSDS500 (PiDiNet, in-domain), +0.197 on BIPED (LDC, in-domain) and +0.144 on UDED (TEED, not in-domain for any method).
  - Out of domain, the learned detectors are still well above GWi+ODPS on BSDS500 (TEED +0.100, LDC +0.155) and BIPED (PiDiNet +0.062).
  - **PiDiNet on UDED is below GWi+ODPS** (0.558 against 0.645) and below the Gaussian gradient, Sobel, LoG and PC; it is at the level of binary Canny (0.557) and ED (0.554). PiDiNet's thick, object-contour maps (BSDS500 training) miss the dense structural edges that UDED and BIPED annotate (visible in the maps, e.g. the louvres of BIPED RGB_139).
  - These are point estimates. No CI was computed: the learned detectors are not in the pre-registered E22 family.
  - **Not comparable with the published values.** For example, PiDiNet reports ODS 0.807 on BSDS500 with the official benchmark (NMS, bipartite matching). The evaluator here uses greedy matching, skimage thinning and no NMS. The submitted §5.6 quoted published values (PiDiNet 0.789, LGLNet 0.805, EDTER 0.848, EdgeNAT 0.860); those numbers are replaced by the measured ones.
- **NMS rows.** The pre-registered script applies its own NMS: orientation from the Sobel gradient of the map smoothed with σ 1, 16 directions, d = 1, bilinear.
  - It lowers ODS in 7 of 9 cases (−0.045 for PiDiNet on BSDS500; +0.001 for TEED on BSDS500 and +0.002 for LDC on UDED).
  - This NMS is not the Structured-Edge NMS (Dollár and Zitnick) that the learned detectors' papers use. That one takes the orientation from second derivatives, which are defined at the crest of a ridge; a first-derivative orientation is not. This is a likely reason for the loss, **not tested**.
  - The "+NMS" rows therefore do not represent the detectors' standard post-processing, and must not be presented as such. The runbook asked for "± standard NMS".
  - **Decision (10 Nov 2026, 13:06:42, first author): the "+NMS" rows are reported as they are, with this description.** The Structured-Edge NMS is not added and no deviation is made.
  - In the manuscript, the rows are labelled with what was applied (for example "+ first-derivative NMS, script of the pre-registration"), not "standard NMS". The text states that this NMS lowered ODS in 7 of 9 cases, and that the rows without NMS are the comparison under the common protocol.
  - The comparison is not affected: the learned detectors are already above GWi+ODPS without NMS. A better NMS could only widen the gap, except for PiDiNet on UDED, where its effect is unknown.
  - The docstring of `scripts/23_eval_external.py` calls this NMS "a standard edge NMS". The pre-registered script is left unchanged, and this entry corrects the wording.
- **Cost** (`results/external/cost.csv`; one thread, 3 warm-up images, median of 5 runs per image, mean over images, including pre- and post-processing, same machine as E24; PyTorch 2.15 CPU):

  | Method | Learned parameters | GMAC at network input (BSDS500 / BIPED / UDED, first image) | CPU ms per image (BSDS500 / BIPED / UDED) |
  |---|---|---|---|
  | TEED | 58,910 | 2.56 (488×728) / 6.64 (720×1280) / 2.84 (512×768) | 209 / 579 / 256 |
  | LDC | 674,500 | 5.58 (480×480) / 22.15 (720×1280) / 6.34 (512×512) | 170 / 765 / 232 |
  | PiDiNet (converted) | 710,149 | 12.47 (321×481) / 74.64 (720×1280) / 13.94 (339×510) | 589 / 3880 / 979 |
  | GWi+ODPS k9 λ9 (E24) | 0 | 0.10 / 0.60 / — (filtering only: 648 MAC per pixel) | 42 / 245 / 69 |
  | Gaussian gradient σ 1.4 (E24) | 0 | — | 10.5 / 63 / 16.5 |

  - The unconverted PiDiNet takes 627 / 4159 / 1037 ms; the converted model is about 6% faster.
  - UDED images differ in size, so the per-image spread there is large (sd 73 to 502 ms); BSDS500 and BIPED spreads are below 8 and 45 ms.
  - The learned detectors' preprocessing includes reading and decoding the image file (5 to 31 ms); E24 excluded it. This favours the training-free methods by at most that amount, small against the forward pass.

  - Parameters: TEED 58,910; LDC 674,500; PiDiNet 710,149 (as published). GWi+ODPS has no learned parameter (k = 9, λ = 9, d = 4.5, N = 8, and the HE preprocessing are fixed by selection).
  - The input sizes follow the repositories: TEED upsamples BSDS500 and UDED images ×1.5, LDC resizes BSDS500 to 480×480 and UDED to 512×512. Their cost is therefore not per original pixel.
  - thop, used first, counts PiDiNet at 11.46 GMAC for the unconverted model on the first BSDS500 image. The PyTorch counter gives 12.50, because thop does not count the functional convolutions inside the pixel-difference modules. The MACs in cost.csv come from the PyTorch counter (convolutions and matrix products only).
  - The frameworks differ (PyTorch against OpenCV/NumPy). The times are a practical comparison on one CPU thread, not a comparison of operation counts.
- **Position on the accuracy-cost trade-off (R1.2, R3.5):**
  - GWi+ODPS (42.2 ms on BSDS500 with preprocessing) is 4.0× (LDC), 5.0× (TEED) and 14× (PiDiNet) faster on one thread than the learned detectors; over the three sets the range is 2.4× (TEED, BIPED) to 16× (PiDiNet, BIPED). It is also much less accurate.
  - In convolution MACs the learned detectors need 25 to 125× more than GWi filtering on BSDS500, but only 4 to 14× more time: PyTorch convolutions are faster per MAC than the OpenCV filtering of E24. MAC ratios alone would overstate the speed advantage.
  - The Gaussian gradient σ 1.4 (10.5 ms) is 4× faster than GWi+ODPS and has higher ODS on all three sets (F24).
  - On these measurements, GWi+ODPS is dominated within the training-free group. "Training-free/CPU-oriented" (R3.5) describes the setting correctly, but it is not an advantage over the classical baseline. The manuscript must not suggest competitive accuracy with learned detectors, nor a cost advantage over the Gaussian gradient.
- **In-domain marks:** TEED and LDC on BIPED; PiDiNet on BSDS500. The selection of GWi+ODPS also used BSDS500 and BIPED non-test data (E10), so no method is entirely out of domain there; UDED is out of domain for all.
- **Other notes:**
  - TEED's `utils/img_processing.py` was replaced by a stand-in with the same `count_parameters`, to avoid installing kornia and scikit-learn. The network and the weights are unchanged.
  - TEED subtracts a per-test-set mean, including one for UDED, as in its repository.
  - The learned maps also show a weak response along the image border (mean of the 2-px frame above the interior on BSDS500 and UDED for all three). This is descriptive and was not analysed further (cf. H5).
  - Licences: TEED MIT; PiDiNet research use only; LDC has no licence file. The maps can be used for evaluation. The weights must not be redistributed with the release.

## G. Open until the test run

Status after E20 to E26 (10 Nov 2026):

- Sign and 95% CI of ΔODS for GWi vs GWC, GWi+ODPS vs GWC, and GWi+ODPS vs GWi on BSDS500, BIPED and UDED (E20, E22).
  - **Resolved by F25.** ODPS improves ODS on BSDS500 only. GWi and GWi+ODPS are above raw GWC on all three sets. GWi is above zero-DC GWC on all three sets at k9 λ9.
- UDED: no non-test split, so the selected configuration was never checked on UDED-like data before the test run.
  - **Resolved by F21.** The selection carries over for GWi but not for GWi+ODPS.
- Whether the non-test patterns above (H1, F7) also appear on the test sets: a descriptive check, not a new test.
  - **F22.** The direction is consistent with H1 on all three sets, with only two kernels.
- Runtime and C5: E24 was run on 10 Nov 2026 (F28). E23 was run on 10 Nov 2026 (F29).
- E26 (10 Nov 2026, 13:12): `results/TABLES.md` collects every result CSV, so that each number of the manuscript can be traced to a row.
  - Two sections were added to `scripts/26_tables.py` before its first real run: the per-candidate H2 values (E13) and the cost of the learned detectors (E23). Three section titles now carry the caveats of F26, F28 and F29. The output file is written as UTF-8.
  - Spot checks against this file (E22 pairs, E21, E24, E25, E23) match the numbers in C3, C4, C9, F25 to F29.
  - TABLES.md lists the numbers only. Where a caveat is needed, the FINDINGS entry decides how a number may be written.
- E25 (R1.3) was run on 10 Nov 2026: see F27 and C10.
- **Figures (10 Nov 2026):** `scripts/27_figures.py` (stage `figures` of run_all.sh) draws every figure of the revised manuscript from the frozen results.
  - `results/figures/FIGURES.md` lists, for each figure: the figure of the submission it replaces, the reviewer comments it answers, its data source, and what its caption must say.
  - Figures 2-4 of the submission are hand-drawn; FIGURES.md lists the edits they need.
  - The runtime figure (E24) and the learned detectors (E23: PR curves, `fig_dl_cost`) are now drawn.
  - Choices made by the script:
    - images are chosen by rule (config.yaml list; median and worst recall change for the ODPS figure);
    - display ranges are clipped only where the caption says so;
    - no figure is cropped to hide the border response.
- E21 (R2.7) was run on 10 Nov 2026: see F26 and C9.
- **Numbers frozen (10 Nov 2026, 15:22):** tag `numbers-frozen-2026-11-10` at commit ed93f8c (E26). No result file has changed since.
- **Release documentation (10 Nov 2026):** written from this ledger.
  - `README.md`: revised numbers; the submitted numbers are in a folded section with notes.
  - `CHANGELOG.md` 3.0.0 and `CITATION.cff`: performance claims removed from the abstract.
  - `docs/ODPS_derivation.md`: rewritten with the corrected mechanism (F12, F13, F18, F27, F28).
  - `docs/reproduction.md`: commands of the revision.
  - `docs/kernel_ablation.md` and `docs/benchmarks.md`: marked as describing v2.0.0.
  - The documents state the negative results with the same weight as the others: C1 to C11, the Gaussian gradient above every Gabor variant, and the learned detectors far above.
  - **What the tag does and does not cover.** `v3.0.0-dsp-r1` is a local tag. It precedes the manuscript writing (WP12-WP13). If writing or the number audit changes any file, the tag is moved before it is published.
- **Before the repository is pushed (decision of the first author, not taken yet):**
  - Every commit of the revision branch since 8 Nov 2026 carries a `Co-Authored-By` trailer.
  - FINDINGS sections F and H, and the decision rows (D-) and short analysis rows (A-) of the process log, are internal notes.
  - Both are part of the commit history. Filtering the latest version would not remove them from the published history. Rewriting the history would change every hash, including those of the pre-registration and freeze tags quoted in this ledger and in CHANGELOG.md.
