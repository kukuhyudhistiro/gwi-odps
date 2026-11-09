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

Unless stated otherwise, numbers are ODS on non-test splits: BSDS500 train+val
(300 images) and BIPED train (200 images). The test splits have not been opened.
Last update: 10 Nov 2026, after the final selection (k9 λ9) and E11, before the freeze.

## Original claims and their status

| # | Claim in the submission or the roadmap | Status now | Entries |
|---|---|---|---|
| C1 | k5 λ4 is the best configuration across three datasets (Table 4) | **Claim withdrawn.** It was selected on test data. On non-test data it ranks 12 of 18 by ODS of GWi | F1, F2 |
| C2 | ODPS suppresses carrier side lobes located at ±λ/2, with d = 2 for λ = 4 | **Claim corrected.** Carrier side lobes exist only when (k//2)/λ > 0.5. At k5 λ4 and at the new selection there are none; ODPS then thins a broad response across orientations | F12 |
| C3 | ODPS improves ODS over GWi | **Finding (non-test), Open (test).** Positive for all 22 candidates evaluated, but the gain shrinks as the kernel half-width over λ shrinks. At the best kernels it is about +0.01 | F9, F10, F11 |
| C4 | The real component of the Gabor kernel is redundant (GWi > GWC) | **Open (E20).** Interpretation is limited: at the new kernel the raw real component has a large DC response | F14 |
| C5 | GWi is about 2.2× faster than GWC | **Open (E24).** The claim applies to the filtering stage only (R2.10, R3.3). The selected k9 kernel costs 3.24× the submitted one per pixel | F15 |
| C6 | (implicit) the Gabor carrier is what makes GWi work | **Not supported for GWi alone.** GWi scores best as the kernel loses its carrier lobe and approaches a smoothed oriented derivative. This was already published in Paper 2 (A-GWi) | F7, H1 |
| C7 | (not claimed, but implied by roadmap §6, which lists only Gabor methods) where GWi+ODPS stands among the evaluated detectors | **Below a classical baseline in the submission's own table.** The Gaussian gradient magnitude (labelled "Canny") is above GWi+ODPS on all three test sets. Revision: open | F16, H3 |
| C8 | (design choice, R2.6) N = 8 orientations is an appropriate balance | **Not supported at the selected kernel.** N = 4 reaches the same ODS at half the cost; N = 16 adds nothing. It was supported at k7 λ5 (E11 of the five-candidate run) | F19 |

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

**F11. Finding. ODPS did not reduce ODS for any candidate (Q1).**
For all six candidates with half-width over λ below 0.5, the gain is positive: +0.012 to +0.019 on BSDS, +0.009 to +0.016 on BIPED.

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

**H6. Consistency item. Runtime.**
A-GWi measured static GWi k7 at 15.54 ms and GWC at 33.70 ms per BSDS500 image (ratio 2.17, single thread, minimum of 3 runs). Paper 1 E24 uses the median of 5 runs. If the machines or timing rules differ, both must be stated, and E24 values for k7 should be compared with these.

## G. Open until the test run

- Sign and 95% CI of ΔODS for GWi vs GWC, GWi+ODPS vs GWC, and GWi+ODPS vs GWi on BSDS500, BIPED and UDED (E20, E22).
- UDED: no non-test split, so the selected configuration was never checked on UDED-like data before the test run.
- Whether the non-test patterns above (H1, F7) also appear on the test sets: a descriptive check, not a new test.
