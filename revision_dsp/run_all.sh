#!/usr/bin/env bash
# Run order for the DSP-D-26-02462 revision (see README.md).
# Usage:  bash run_all.sh <stage>      e.g.  bash run_all.sh smoke
#         CFG=config.yaml NJ=8 bash run_all.sh select
set -euo pipefail
cd "$(dirname "$0")"
CFG=${CFG:-config.yaml}
NJ=${NJ:-8}
PY=${PY:-python3}
run() { echo; echo "=== $*"; $PY "$@" --config "$CFG" --n-jobs "$NJ"; }

case "${1:-help}" in
  smoke)       # synthetic data, a few minutes, checks that every script runs
    $PY tools/make_synthetic_data.py --out /tmp/synth_data
    CFG=tests/config_synth.yaml NJ=2
    for s in 00_env 01_selftest 02_mechanism 10_select_kernel 11_ablation 12_freeze \
             20_test_final 21_ablation_preproc 22_stats 24_runtime 25_qualitative_odps 26_tables; do
      extra=""; [ "$s" = "20_test_final" ] && extra="--legacy-check"
      echo "=== $s"; $PY scripts/$s.py --config "$CFG" --n-jobs "$NJ" $extra
    done ;;
  check)       # real data: environment + equivalence with the submitted code + mechanism
    run scripts/00_env.py
    run scripts/01_selftest.py --dataset BSDS500:val --n-images 5
    run scripts/02_mechanism.py ;;
  select)      # R2.1: kernel selection on BSDS500 train+val and BIPED train
    run scripts/10_select_kernel.py ;;
  ablation)    # R2.5, R2.6, R3.2, R3.4 (BSDS500 train+val, reported only)
    run scripts/11_ablation.py ;;
  hypotheses)  # HYPOTHESES.md (H1 ODPS gain vs rho, H2 GWi vs rho and scale); reads E10 output only
    run scripts/13_hypotheses.py ;;
  freeze)      # then git tag freeze-2026-11-10
    run scripts/12_freeze.py ;;
  test)        # test sets are opened here, once
    run scripts/20_test_final.py --legacy-check ;;
  preproc)     # R2.7
    run scripts/21_ablation_preproc.py ;;
  stats)       # R1.1, R2.11
    run scripts/22_stats.py ;;
  runtime)     # R1.4, R2.5, R2.10, R3.3, R3.6: machine otherwise idle, 1 job
    $PY scripts/24_runtime.py --config "$CFG" --n-jobs 1 ;;
  qualitative) # R1.3
    run scripts/25_qualitative_odps.py ;;
  tables)
    run scripts/26_tables.py ;;
  *)
    echo "stages: smoke | check | select | ablation | hypotheses | freeze | test | preproc | stats | runtime | qualitative | tables"
    echo "external DL maps (R1.2): python3 scripts/23_eval_external.py --maps-root <dir> --methods TEED PiDiNet LDC --nms" ;;
esac
