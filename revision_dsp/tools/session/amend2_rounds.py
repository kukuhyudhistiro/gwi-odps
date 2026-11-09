"""Amendment 2: selection under the GWi+ODPS criterion, edge rule for every k, then E11.

Run from revision_dsp with the venv python. Each round:
  1. run the selection (cached counts are reused; only new candidates are computed)
  2. read selected.json per_k_edge; every k at its upper edge and below the bound
     gets one more lambda (lam_max + 1)
  3. stop when no k needs extending
Then set ablation.lam_d.lam to the lambda range evaluated at the selected k and run E11.
"""
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(r"D:\Project 2026\gwi-odps\revision_dsp")
os.chdir(ROOT)
ENV = dict(os.environ, MSYS_NO_PATHCONV="1", PYTHONIOENCODING="utf-8",
           PY=".venv/Scripts/python.exe", NJ="12")
BASH = r"C:\Program Files\Git\bin\bash.exe"
CFG = ROOT / "config.yaml"
CAND = re.compile(r"^    - \{k: (\d+), lam: (\d+)\}$")


def log(msg):
    print(time.strftime("%H:%M:%S"), msg, flush=True)


def run_stage(stage, logname):
    with open(ROOT / "logs_local" / logname, "w", encoding="utf-8") as fh:
        rc = subprocess.call([BASH, "run_all.sh", stage], stdout=fh, stderr=subprocess.STDOUT, env=ENV)
    tail = (ROOT / "logs_local" / logname).read_text(encoding="utf-8").strip().splitlines()[-6:]
    for t in tail:
        log("   | " + t)
    if rc != 0:
        log(f"{stage} failed rc={rc}")
        sys.exit(rc)


def add_candidates(new):
    lines = CFG.read_text(encoding="utf-8").splitlines()
    last = max(i for i, l in enumerate(lines) if CAND.match(l))
    ins = [f"    - {{k: {k}, lam: {lam}}}" for k, lam in new]
    lines[last + 1:last + 1] = ins
    CFG.write_text("\n".join(lines) + "\n", encoding="utf-8")


def evaluated(k):
    return sorted(int(m.group(2)) for l in CFG.read_text(encoding="utf-8").splitlines()
                  if (m := CAND.match(l)) and int(m.group(1)) == k)


rnd = 0
while True:
    rnd += 1
    log(f"round {rnd}: selection")
    run_stage("select", f"E10d_amend2_round{rnd}.log")
    sel = json.loads((ROOT / "results/selection/selected.json").read_text(encoding="utf-8"))
    log(f"selected ({sel['criterion']}): k={sel['k']} lam={sel['lam']} value={sel['value']}")
    new = []
    for e in sel["per_k_edge"]:
        log(f"  k={e['k']} best lam {e['best_lam']} ({e['value']}), largest evaluated "
            f"{e['lam_max_evaluated']}, edge {e['at_upper_edge']}, bound {e['lam_bound']}, at bound {e['at_bound']}")
        if e["at_upper_edge"] and not e["at_bound"]:
            new.append((int(e["k"]), int(e["lam_max_evaluated"]) + 1))
    if not new:
        log("no k at its upper edge below the bound: selection final")
        break
    log(f"extending: {new}")
    add_candidates(new)

k = int(sel["k"])
lams = evaluated(k)
txt = CFG.read_text(encoding="utf-8")
pat = re.compile(r"^    lam: \[[0-9, ]*\] +# at the selected k.*$", re.M)
assert pat.search(txt), "ablation lam line not found"
txt = pat.sub(f"    lam: [{', '.join(map(str, lams))}]  # at the selected k (lambda range evaluated "
              f"at k = {k} in the selection)", txt)
CFG.write_text(txt, encoding="utf-8")
log(f"E11 at k={k}, lambda {lams}")
run_stage("ablation", "E11c_amend2_ablation.log")
log("done")
