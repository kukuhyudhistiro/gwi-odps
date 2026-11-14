"""E23 (R1.2, R3.5): collect the cost measurements of the learning-based detectors and
write results/external/models.yaml and results/external/cost.csv.

Run with the revision environment after tools/external/run_e23.sh:
    .venv/Scripts/python.exe tools/external/summarize_e23.py --maps "$EXT/maps" --repos "$EXT/repos"

Reads, per method, <maps>/<METHOD>/provenance.json, flops*.csv and timing*.csv (written by
infer_external.py), copies them to results/external/cost/<METHOD>/ so that the repository
keeps them, and adds the SHA-256 of each checkpoint. Nothing is measured here.
For PiDiNet the cost columns use the converted model (same maps; the form the repository
times); the cost of the unconverted model is kept in cost.csv as a separate row.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import statistics as st
from pathlib import Path

import yaml

REV = Path(__file__).resolve().parents[2]
EXT = REV / "results" / "external"
DATASETS = ["BSDS500", "BIPED", "UDED"]
META = {
    "TEED": dict(reference="Soria et al., ICCVW 2023 (TEED)", license="MIT (repository LICENSE)",
                 in_domain=["BIPED"],
                 notes=["Test-time size: images below 512 px are upsampled x1.5 (BSDS500, UDED), as in the repository.",
                        "Mean subtracted per test set (dataset.py), including a UDED mean.",
                        "utils/img_processing.py replaced by a stand-in with the same count_parameters "
                        "(avoids kornia and scikit-learn); network and weights unchanged."]),
    "LDC": dict(reference="Soria et al., IEEE Access 2022 (LDC)", license="no LICENSE file in the repository",
                in_domain=["BIPED"],
                notes=["Test-time size: images below 512 px are resized to 480x480 (BSDS500) or 512x512 (UDED), "
                       "as in the repository; this changes the aspect ratio."]),
    "PiDiNet": dict(reference="Su et al., ICCV 2021 (PiDiNet), Table 5 model", license="research use only; commercial use "
                    "needs the authors' permission (repository LICENSE)",
                    in_domain=["BSDS500"],
                    notes=["Weights trained on BSDS500 train+val with PASCAL VOC augmentation.",
                           "Maps from the unconverted model (README evaluation command); the converted model gives "
                           "the same maps (max difference 1 grey level on 15 checked images) and is used for cost."]),
}


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for b in iter(lambda: fh.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read(p: Path):
    with open(p, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def timing_rows(p: Path):
    out = {}
    rows = read(p)
    for ds in DATASETS:
        r = [x for x in rows if x["dataset"] == ds]
        tot = [float(x["pre_ms"]) + float(x["forward_ms"]) + float(x["post_ms"]) for x in r]
        out[ds] = dict(n=len(r), pre_ms=round(st.mean(float(x["pre_ms"]) for x in r), 1),
                       forward_ms=round(st.mean(float(x["forward_ms"]) for x in r), 1),
                       post_ms=round(st.mean(float(x["post_ms"]) for x in r), 1),
                       total_ms=round(st.mean(tot), 1), total_ms_sd=round(st.stdev(tot), 1))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--maps", required=True)
    ap.add_argument("--repos", required=True)
    a = ap.parse_args()
    maps = Path(a.maps)
    models, cost = {}, []
    for m in META:
        src = maps / m
        dst = EXT / "cost" / m
        dst.mkdir(parents=True, exist_ok=True)
        for f in sorted(src.glob("*.csv")) + [src / "provenance.json"]:
            shutil.copy2(f, dst / f.name)
        prov = json.loads((src / "provenance.json").read_text(encoding="utf-8"))
        ck = Path(a.repos) / prov["checkpoint"]
        tag = "_converted" if m == "PiDiNet" else ""
        fl = {r["dataset"]: r for r in read(src / f"flops{tag}.csv")}
        tm = timing_rows(src / f"timing{tag}.csv")
        variants = [(m + tag, fl, tm)]
        if tag:
            variants.append((m, {r["dataset"]: r for r in read(src / "flops.csv")}, timing_rows(src / "timing.csv")))
        for name, f2, t2 in variants:
            for ds in DATASETS:
                cost.append(dict(method=name, dataset=ds, input_hw=f2[ds]["input_hw"], params=f2[ds]["params"],
                                 gmacs_first_image=f2[ds]["gmacs"], **t2[ds]))
        models[m] = dict(
            reference=META[m]["reference"], repo=prov["repository"], commit=prov["commit"],
            weights=prov["checkpoint"], weights_sha256=sha256(ck), trained_on=prov["trained_on"],
            in_domain_test_sets=META[m]["in_domain"], license=META[m]["license"],
            params=int(read(src / "flops.csv")[0]["params"]),          # learned parameters (unconverted model)
            gmacs_at_network_input={ds: f"{fl[ds]['gmacs']} at {fl[ds]['input_hw']} (first test image)" for ds in DATASETS},
            cpu_ms_1thread={ds: f"{tm[ds]['total_ms']} ± {tm[ds]['total_ms_sd']} (forward {tm[ds]['forward_ms']})"
                            for ds in DATASETS},
            cost_model=("converted (same maps; its 5x5 rd kernels store "
                        f"{int(fl['BSDS500']['params'])} values for the same learned weights)") if tag else "as used for the maps",
            torch=prov["torch"], notes=META[m]["notes"])
    hdr = ("# E23 (R1.2, R3.5). Written by tools/external/summarize_e23.py from the measurements in\n"
           "# results/external/cost/; do not edit by hand. CPU: one thread, 3 warm-up images, median of 5 runs\n"
           "# per image, mean ± sd over the test images, including pre- and post-processing (as E24);\n"
           "# unlike E24, pre-processing here includes reading and decoding the image file.\n"
           "# MACs: convolutions and matrix products executed (torch.utils.flop_counter), first test image.\n")
    (EXT / "models.yaml").write_text(hdr + yaml.safe_dump(models, sort_keys=False, allow_unicode=True, width=110),
                                     encoding="utf-8")
    with open(EXT / "cost.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cost[0]))
        w.writeheader()
        w.writerows(cost)
    print(f"-> {EXT / 'models.yaml'}\n-> {EXT / 'cost.csv'} ({len(cost)} rows)")


if __name__ == "__main__":
    main()
