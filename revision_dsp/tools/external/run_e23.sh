#!/usr/bin/env bash
# E23 (R1.2, R3.5): learning-based detectors with the evaluator of the revision.
# Usage (from revision_dsp):  bash tools/external/run_e23.sh [maps] [eval] [flops] [timing] [timing_converted]
#   (no argument: all steps)
# Steps, each logged to logs_local/runs.csv:
#   E23a  maps of TEED, LDC, PiDiNet (official repos and weights; tools/external/infer_external.py)
#   E23b  evaluation without and with the NMS of scripts/23_eval_external.py
#   E23c  parameters and multiply-accumulates at the network input size (torch flop counter)
#   E23d  CPU time, one thread, 3 warm-up images, median of 5 runs per image (as E24)
# PiDiNet cost is also measured with the repository's converted model (same maps,
# max difference 1 grey level; the form the repository times): E23c/E23d_PiDiNet_converted.
set -uo pipefail
cd "$(dirname "$0")/../.."
# EXT: folder with the E23 environment (.venv-dl), the official repositories (repos/) and the
#      maps (maps/); see docs/reproduction.md A.2. The revision used a folder next to the repository.
# PYD: Python of the E23 environment; PYR: Python of the revision environment (Linux: .../bin/python).
EXT="${EXT:?set EXT to the E23 folder, e.g. EXT=../../e23_external}"
PYD="${PYD:-$EXT/.venv-dl/Scripts/python.exe}"
PYR="${PYR:-.venv/Scripts/python.exe}"
export PYTHONIOENCODING=utf-8 MSYS_NO_PATHCONV=1
runs=logs_local/runs.csv
head=$(git rev-parse --short HEAD)
step() {   # id, log, command...
  local id=$1 log=$2; shift 2
  local start t0 rc end t1
  start=$(date '+%Y-%m-%d %H:%M:%S %z'); t0=$(date +%s)
  "$@" > "$log" 2>&1; rc=$?
  end=$(date '+%Y-%m-%d %H:%M:%S %z'); t1=$(date +%s)
  echo "$id,e23,$start,$end,$((t1 - t0)),$rc,$log,$head" >> "$runs"
  echo "$id: rc=$rc, $((t1 - t0)) s"
  return $rc
}
stages=${*:-maps eval flops timing timing_converted}
has() { [[ " $stages " == *" $1 "* ]]; }
has maps && for m in TEED LDC PiDiNet; do
  step "E23a_$m" "logs_local/E23a_maps_$m.log" "$PYD" tools/external/infer_external.py --method "$m" \
       --repos "$EXT/repos" --out "$EXT/maps" --threads 8 || exit 1
done
has eval && { step E23b logs_local/E23b_eval.log "$PYR" scripts/23_eval_external.py --config config.yaml --n-jobs 12 \
     --maps-root "$EXT/maps" --methods TEED LDC PiDiNet --nms || exit 1; }
has flops && for m in TEED LDC PiDiNet; do
  step "E23c_$m" "logs_local/E23c_flops_$m.log" "$PYD" tools/external/infer_external.py --method "$m" \
       --repos "$EXT/repos" --out "$EXT/maps" --flops || exit 1
done
has timing && for m in TEED LDC PiDiNet; do
  step "E23d_$m" "logs_local/E23d_timing_$m.log" "$PYD" tools/external/infer_external.py --method "$m" \
       --repos "$EXT/repos" --out "$EXT/maps" --timing || exit 1
done
has flops && { step E23c_PiDiNet_converted logs_local/E23c_flops_PiDiNet_converted.log "$PYD" \
     tools/external/infer_external.py --method PiDiNet --repos "$EXT/repos" --out "$EXT/maps" \
     --flops --converted || exit 1; }
has timing_converted && { step E23d_PiDiNet_converted logs_local/E23d_timing_PiDiNet_converted.log "$PYD" \
     tools/external/infer_external.py --method PiDiNet --repos "$EXT/repos" --out "$EXT/maps" \
     --timing --converted || exit 1; }
echo "E23 done ($stages)"
