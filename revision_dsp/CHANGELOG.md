# Changelog: protocol changes after pre-registration

Every change to `config.yaml` after the tag `prereg-dsp-2026-11-08`, and every
change to the method list after `freeze-2026-11-10`, is recorded here with the
reason. These entries are reported in the response letter.

| Date | File / key | Old | New | Reason | Results already seen? |
|---|---|---|---|---|---|
| 2026-11-08 | config.yaml (whole file), scripts 10-13, 21, 22, 24, 25 | Protocol v1 (7 Nov): border reflect for all; fixed normalization scale from train+val; selection of k, λ, d by ODS of GWi+ODPS with tie tolerance 0.005; gate G1 with TOST margin 0.01; gradient operators with NMS (Sobel, Prewitt-5, Gaussian); GWC tuned on its own grid; baselines tuned; Canny over 40 levels, low ratio 0.4 | Protocol v2: the manuscript protocol (zero padding for Gabor, per-image min-max); selection with the rule and candidates of Tables 1-4 on non-test splits, d = λ/2; no gate, no TOST; no gradient+NMS controls; GWC with the same kernel as GWi; baselines as in Section 4.3 with fixed parameters (Canny 50/150, LoG 7×7 σ 1.4, PC 4 scales, ED defaults); GWC zero-DC kept only as R1.5 analysis | Keep the protocol the reviewers assessed and change only what they asked for | No real-data results existed when v2 was written (none in the review folder); v1 was never tagged on real data as far as known |
