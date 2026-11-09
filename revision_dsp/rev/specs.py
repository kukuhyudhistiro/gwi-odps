"""Method specs of the proposed pipeline and its Gabor comparators.

All four use the same kernel (k, lambda, N, sigma/lambda, gamma), as in Section 4.3
of the manuscript ("GWC uses the same kernel parameters as GWi").

    GWi_<tag>        Stages 1-5 (imaginary only)
    GWiODPS_<tag>    Stages 1-6, ODPS with d = lambda/2 (Section 3.6)
    GWCraw_<tag>     complex Gabor as in the manuscript
    GWCzero_<tag>    complex Gabor with the mean of the real kernel removed:
                     analysis for Reviewer 1, point 5 (why GWi differs from GWC);
                     not a baseline of the main comparison
"""
from __future__ import annotations

from typing import Dict, List


def tag_of(k, lam) -> str:
    return f"k{k}l{lam}"


def d_of(lam: float, rule: str = "half_lambda") -> float:
    if rule != "half_lambda":
        raise ValueError(f"unknown d rule {rule}")
    return float(lam) / 2.0


def gabor_specs(kcfg: Dict, d: float, mode: str = "nearest") -> List[Dict]:
    base = dict(k=int(kcfg["k"]), lam=float(kcfg["lam"]), N=int(kcfg.get("N", 8)),
                sigma_ratio=float(kcfg.get("sigma_ratio", 0.56)),
                gamma=float(kcfg.get("gamma", 0.5)))
    t = tag_of(kcfg["k"], int(kcfg["lam"]) if float(kcfg["lam"]).is_integer() else kcfg["lam"])
    return [
        dict(name=f"GWi_{t}", family="gwi", **base),
        dict(name=f"GWiODPS_{t}", family="gwi", nms=dict(d=float(d), mode=mode), **base),
        dict(name=f"GWCraw_{t}", family="gwc", dc="raw", **base),
        dict(name=f"GWCzero_{t}", family="gwc", dc="zero", **base),
    ]
