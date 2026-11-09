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
Last update: 9 Nov 2026, before amendment 2 was run.

## Original claims and their status

| # | Claim in the submission or the roadmap | Status now | Entries |
|---|---|---|---|
| C1 | k5 λ4 is the best configuration across three datasets (Table 4) | **Claim withdrawn.** It was selected on test data. On non-test data it ranks 12 of 18 by ODS of GWi | F1, F2 |
| C2 | ODPS suppresses carrier side lobes located at ±λ/2, with d = 2 for λ = 4 | **Claim corrected.** Carrier side lobes exist only when (k//2)/λ > 0.5. At k5 λ4 and at the new selection there are none; ODPS then thins a broad response across orientations | F12 |
| C3 | ODPS improves ODS over GWi | **Finding (non-test), Open (test).** Positive for all 22 candidates evaluated, but the gain shrinks as the kernel half-width over λ shrinks. At the best kernels it is about +0.01 | F9, F10, F11 |
| C4 | The real component of the Gabor kernel is redundant (GWi > GWC) | **Open (E20).** Interpretation is limited: at the new kernel the raw real component has a large DC response | F14 |
| C5 | GWi is about 2.2× faster than GWC | **Open (E24).** The claim applies to the filtering stage only (R2.10, R3.3). The new kernel roughly doubles the absolute cost | F15 |
| C6 | (implicit) the Gabor carrier is what makes GWi work | **Not supported for GWi alone.** GWi scores best as the kernel loses its carrier lobe and approaches a smoothed oriented derivative | F7 |

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

**F15. Finding. The selected kernel roughly doubles the filtering cost.**
- k7 with N = 8 needs 392 MAC per pixel, against 200 for k5 λ4 (1.96×).
- GWi still uses N convolutions against 2N for GWC at the same kernel, but its absolute cost is about double that of the submitted configuration.
- Measured times come from E24.

## F. Consequences for the dissertation roadmap

**R1.** Transfer (b) of the roadmap ("k5 λ4 N8 as default for Paper 2") is invalid (F2). Paper 2 should take the evidence on λ and scale from Paper 1, not a single default.

**R2.** The numbers in roadmap §6 (GWi vs GWC +0.050 to +0.150 ODS, 2.2× faster) come from the submitted, test-selected protocol. They are replaced after E20 and E24.

**R3.** Notation clash: the roadmap uses ρ_L and A_ρ for local density, while this revision used ρ = (k//2)/λ. The manuscript needs another symbol for the latter.

**R4.** Paper 2 replaces ODPS with a learned decoder, so C2 and C3 concern Paper 1 only.

**R5.** F7 (single-scale GWi performs best when the kernel acts as a smoothed derivative) bears on Paper 2's adaptation of λ and σ. It is a question Paper 2 must test, not a result Paper 1 provides.

## G. Open until the test run

- Sign and 95% CI of ΔODS for GWi vs GWC, GWi+ODPS vs GWC, and GWi+ODPS vs GWi on BSDS500, BIPED and UDED (E20, E22).
- UDED: no non-test split, so the selected configuration was never checked on UDED-like data before the test run.
- Whether the non-test patterns above (H1, F7) also appear on the test sets: a descriptive check, not a new test.
