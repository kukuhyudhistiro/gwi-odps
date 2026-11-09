"""Config loading, method-spec hashing, and result paths."""
from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import yaml

ROOT = Path(__file__).resolve().parents[1]


def load_config(path: str | Path | None = None) -> Dict[str, Any]:
    path = Path(path) if path else ROOT / "config.yaml"
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["_path"] = str(path)
    base = Path(path).resolve().parent
    for key in ("data_root", "results_dir"):
        p = Path(cfg["paths"][key]).expanduser()
        cfg["paths"][key] = str(p if p.is_absolute() else (base / p).resolve())
    return cfg


def results_dir(cfg, *parts) -> Path:
    p = Path(cfg["paths"]["results_dir"]).joinpath(*parts)
    p.mkdir(parents=True, exist_ok=True)
    return p


def protocol_of(cfg, overrides: Dict[str, Any] | None = None) -> Dict[str, Any]:
    proto = copy.deepcopy(cfg["protocol"])
    if overrides:
        proto.update(overrides)
    return proto


GABOR_FAMILIES = ("gwi", "gwc", "gwe")


def border_for(proto: Dict[str, Any], spec: Dict[str, Any]) -> str:
    """Border mode of the convolutions for one method.

    'paper': as in the submitted manuscript and code: zero padding for the Gabor
    filters (Algorithm 1, line 9), OpenCV's default (reflect-101) for the other
    baselines. Any other value is applied to every method.
    """
    b = proto["border"]
    if b == "paper":
        return "constant" if spec["family"] in GABOR_FAMILIES else "reflect"
    return b


def canonical(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def spec_id(spec: Dict[str, Any], proto: Dict[str, Any]) -> str:
    """Stable id for (method spec, map-producing protocol).

    Only protocol fields that change the edge map enter the hash.
    Evaluation-only fields (thresholds, tolerance) are kept separately
    in the counts file name.
    """
    keys = ("preproc", "border", "nms_outside", "normalization",
            "quantize_8bit", "scale_source", "scale_percentile")
    sub = {k: proto.get(k) for k in keys}
    body = {k: v for k, v in spec.items() if k != "name"}
    h = hashlib.sha1(canonical({"spec": body, "proto": sub}).encode()).hexdigest()[:10]
    return f"{spec['family']}__{h}"   # name excluded: identical specs share caches


def eval_id(proto: Dict[str, Any]) -> str:
    keys = ("n_thresholds", "max_dist_frac", "matching", "thinning")
    return "eval_" + hashlib.sha1(
        canonical({k: proto.get(k) for k in keys}).encode()).hexdigest()[:8]


def expand_name(spec: Dict[str, Any]) -> str:
    """Readable default name for a spec without 'name'."""
    f = spec["family"]
    parts = [f]
    for k in ("k", "lam", "N", "sigma_ratio", "gamma", "dc", "sigma"):
        if k in spec:
            parts.append(f"{k}{spec[k]}")
    if spec.get("nms"):
        n = spec["nms"]
        parts.append(f"nms-d{n.get('d')}-{n.get('mode', 'nearest')}")
    return "_".join(str(p) for p in parts)
