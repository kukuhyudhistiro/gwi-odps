#!/usr/bin/env bash
# Run one stage of run_all.sh and record when it ran, how long it took, its exit
# code and its log, for PROCESS_LOG.md (process history of the revision).
# Usage (from revision_dsp):  bash tools/run_logged.sh <id> <stage>
#   e.g.  bash tools/run_logged.sh E22 stats
# Appends one line to logs_local/runs.csv:
#   id,stage,start,end,duration_s,exit_code,log,git_head
set -uo pipefail
cd "$(dirname "$0")/.."
id=$1; stage=$2
mkdir -p logs_local
log="logs_local/${id}_${stage}.log"
runs=logs_local/runs.csv
[ -f "$runs" ] || echo "id,stage,start,end,duration_s,exit_code,log,git_head" > "$runs"
head=$(git rev-parse --short HEAD)
start=$(date '+%Y-%m-%d %H:%M:%S %z'); t0=$(date +%s)
bash run_all.sh "$stage" > "$log" 2>&1
rc=$?
end=$(date '+%Y-%m-%d %H:%M:%S %z'); t1=$(date +%s)
echo "$id,$stage,$start,$end,$((t1 - t0)),$rc,$log,$head" >> "$runs"
echo "$id $stage: rc=$rc, $((t1 - t0)) s, log $log"
exit $rc
