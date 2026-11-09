"""Freeze and record the software/hardware environment (A10 in the runbook).

Writes results/env/env.json and results/env/pip_freeze.txt. The versions in
§4.4 of the revised manuscript must be copied from these files.
"""
from __future__ import annotations

import importlib
import json
import os
import platform
import subprocess
import sys

from _common import parser, setup
from rev import cfg as C


def main():
    args = parser(__doc__).parse_args()
    cfg, _ = setup(args)
    out = C.results_dir(cfg, "env")
    vers = {}
    for m in ("numpy", "scipy", "cv2", "skimage", "PIL", "yaml", "matplotlib", "phasepack"):
        try:
            mod = importlib.import_module(m)
            vers[m] = getattr(mod, "__version__", "?")
        except Exception as e:  # noqa: BLE001
            vers[m] = f"missing ({e.__class__.__name__})"
    import cv2
    info = dict(python=sys.version, platform=platform.platform(),
                machine=platform.machine(), processor=platform.processor(),
                cpu_count=os.cpu_count(), packages=vers,
                opencv_contrib_ximgproc=hasattr(cv2, "ximgproc"),
                opencv_build_simd=[l.strip() for l in cv2.getBuildInformation().splitlines()
                                   if "Baseline" in l or "Dispatched" in l][:4],
                thread_env={v: os.environ.get(v) for v in
                            ("OMP_NUM_THREADS", "MKL_NUM_THREADS", "OPENBLAS_NUM_THREADS")})
    try:
        info["cpu_brand"] = subprocess.run(["sysctl", "-n", "machdep.cpu.brand_string"],
                                           capture_output=True, text=True).stdout.strip()
    except Exception:  # noqa: BLE001
        pass
    (out / "env.json").write_text(json.dumps(info, indent=1))
    freeze = subprocess.run([sys.executable, "-m", "pip", "freeze"], capture_output=True, text=True)
    (out / "pip_freeze.txt").write_text(freeze.stdout)
    print(json.dumps(info, indent=1))


if __name__ == "__main__":
    main()
