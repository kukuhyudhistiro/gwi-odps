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
Last update: 10 Nov 2026, after E21. Timings of every stage: PROCESS_LOG.md.

## Original claims and their status

| # | Claim in the submission or the roadmap | Status now | Entries |
|---|---|---|---|
| C1 | k5 λ4 is the best configuration across three datasets (Table 4) | **Claim withdrawn.** It was selected on test data. On non-test data it ranks 12 of 18 by ODS of GWi. On test, k9 λ9 is above it for GWi on all three sets; for GWi+ODPS on BSDS500 and BIPED but not UDED (+0.0002) | F1, F2, F21 |
| C2 | ODPS suppresses carrier side lobes located at ±λ/2, with d = 2 for λ = 4 | **Claim corrected.** Carrier side lobes exist only when (k//2)/λ > 0.5. At k5 λ4 and at the new selection there are none; ODPS then thins a broad response across orientations | F12 |
| C3 | ODPS improves ODS over GWi | **Claim corrected: supported on BSDS500 only.** E22 at k9 λ9: BSDS500 +0.0122, 95% CI [0.0090, 0.0158]; BIPED +0.0079, CI [−0.0076, 0.0203]; UDED −0.0025, CI [−0.0161, 0.0121]. "Improves" may be written for BSDS500 only. At the submitted k5 λ4 the point gains were larger (+0.0253, +0.0142, +0.0377), with no CI | F9, F10, F11, F22, F25 |
| C4 | The real component of the Gabor kernel is redundant (GWi > GWC) | **Claim corrected.** GWi is above raw GWC on all test sets (CIs exclude 0), but most of that gap is the DC response of the raw real kernel. Against zero-DC GWC at k9 λ9, GWi stays above, with CIs excluding 0: +0.0161, +0.0391 and +0.0842. At k5 λ4, zero-DC GWC is above GWi on BSDS500 (−0.0093, no CI) | F14, F23, F25 |
| C5 | GWi is about 2.2× faster than GWC | **Open (E24).** The claim applies to the filtering stage only (R2.10, R3.3). The selected k9 kernel costs 3.24× the submitted one per pixel | F15 |
| C6 | (implicit) the Gabor carrier is what makes GWi work | **Not supported for GWi alone.** GWi scores best as the kernel loses its carrier lobe and approaches a smoothed oriented derivative. This was already published in Paper 2 (A-GWi) | F7, H1 |
| C7 | (not claimed, but implied by roadmap §6, which lists only Gabor methods) where GWi+ODPS stands among the evaluated detectors | **Below a classical baseline, in the submission and in the revision.** The Gaussian gradient magnitude σ 1.4 is above every Gabor variant on all three test sets, in ODS, OIS and AP. Measured under the manuscript border protocol, which handicaps the Gabor methods (H5) | F16, F24, H3, H5 |
| C8 | (design choice, R2.6) N = 8 orientations is an appropriate balance | **Not supported at the selected kernel.** N = 4 reaches the same ODS at half the cost; N = 16 adds nothing. It was supported at k7 λ5 (E11 of the five-candidate run) | F19 |
| C9 | (§3.1, R2.7) Histogram equalization is important, notably for low-contrast images; normalization to [0, 1] is necessary | **Claim withdrawn.** On all three test sets, removing HE raises ODS of GWi (+0.0055 to +0.0623) and of GWi+ODPS (+0.0111 to +0.0591). /255 changes nothing. The protocol stays as frozen (HE) | F26 |

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

**F13. Limitation. For odd λ, d = λ/2 is rounded.**
- The offsets use `np.round`, which rounds halves to even. For d = 4.5 (λ9) the axis offsets are 4, the same as for λ8. For λ10 they are 5.
- The drop in gain between λ9 and λ10 coincides with this step from 4 to 5. Reported, not corrected.

## D. GWi vs GWC (operator I of the roadmap)

**F14. Limitation, Open. The raw real kernel's DC response grows with λ, which biases GWi vs GWC at large λ.**
- DC-to-gain ratio of the raw real kernel: 0.15 at k5 λ4, 0.76 at k7 λ9, 1.24 at k7 λ12. At k7 λ12 the real kernel is entirely non-negative, a low-pass filter.
- GWC built with the same kernel therefore carries a brightness-dependent response that grows with λ. A GWi > GWC gap at k7 λ9 may partly reflect this DC leakage, not only the redundancy of the even component.
- The GWC zero-DC analysis (R1.5, evaluated in E20) is needed to interpret the comparison, and the claim must be stated with this limit.
- *Added after E20:* the DC concern was correct, and it already applies at the submitted k5 λ4. See F23.

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

## G. Open until the test run

Status after E20, E21 and E22 (10 Nov 2026):

- Sign and 95% CI of ΔODS for GWi vs GWC, GWi+ODPS vs GWC, and GWi+ODPS vs GWi on BSDS500, BIPED and UDED (E20, E22).
  - **Resolved by F25.** ODPS improves ODS on BSDS500 only. GWi and GWi+ODPS are above raw GWC on all three sets. GWi is above zero-DC GWC on all three sets at k9 λ9.
- UDED: no non-test split, so the selected configuration was never checked on UDED-like data before the test run.
  - **Resolved by F21.** The selection carries over for GWi but not for GWi+ODPS.
- Whether the non-test patterns above (H1, F7) also appear on the test sets: a descriptive check, not a new test.
  - **F22.** The direction is consistent with H1 on all three sets, with only two kernels.
- Still open: runtime and C5 (E24). E23, E25 and E26 have not been run.
- E21 (R2.7) was run on 10 Nov 2026: see F26 and C9.
