#!/usr/bin/env bash
# Edge rule of amendment 1, rounds 2.. at k = 7, then E11 if the selection is interior.
# Stops (without E11) if lambda 12 is reached and still selected: that needs a decision.
set -u
cd "/d/Project 2026/gwi-odps/revision_dsp"
export MSYS_NO_PATHCONV=1 PYTHONIOENCODING=utf-8 PY=.venv/Scripts/python.exe NJ=12
CAP=12
# Windows python prints CRLF: strip the CR, or the comparisons below fail
sel_lam() { $PY -c "import json;d=json.load(open('results/selection/selected.json'));print(int(d['k']), int(float(d['lam'])))" | tr -d '\r'; }
max_k7() { grep -oE '^    - \{k: 7, lam: [0-9]+\}' config.yaml | grep -oE '[0-9]+\}$' | tr -d '}' | sort -n | tail -1; }

while :; do
  read -r k lam < <(sel_lam)
  maxlam=$(max_k7)
  echo "$(date) selected k=[$k] lam=[$lam]; max lambda at k7 = [$maxlam]"
  if [ "$k" != 7 ] || [ "$lam" != "$maxlam" ]; then
    echo "INTERIOR: selection k=$k lam=$lam"; break
  fi
  if [ "$lam" -ge "$CAP" ]; then
    echo "CAP: lambda $lam still at the upper edge; stopping for a decision"; exit 3
  fi
  nxt=$((lam + 1))
  sed -i "s/^    - {k: 7, lam: $lam}\$/&\n    - {k: 7, lam: $nxt}/" config.yaml
  grep -q "^    - {k: 7, lam: $nxt}\$" config.yaml || { echo "config edit failed"; exit 4; }
  echo "=== round: + k7 lam $nxt  $(date)"
  bash run_all.sh select > "logs_local/E10c_edge_k7l${nxt}.log" 2>&1 || { echo "select failed"; exit 5; }
  tail -1 "logs_local/E10c_edge_k7l${nxt}.log"
done

# E11 at the final configuration: lambda range at k = 7 as evaluated in the selection
maxlam=$(max_k7)
list=$(seq -s ', ' 3 "$maxlam" | sed 's/, /, /g')
sed -i -E "s/^    lam: \[[0-9, ]*\] +# at the selected k.*\$/    lam: [$list]  # at the selected k (amendment 1 + edge rule: lambda range evaluated at k = 7)/" config.yaml
grep -n "^    lam: \[" config.yaml
echo "=== E11 start $(date)"
bash run_all.sh ablation > logs_local/E11b_ablation.log 2>&1; rc=$?
echo "=== E11 rc=$rc end $(date)"; tail -3 logs_local/E11b_ablation.log
exit $rc
