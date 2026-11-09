"""Parallel map computation + evaluation with on-disk caches.

Cache layout (results_dir):
    scales/<spec_id>.json                       only if normalization = fixed
    counts/<eval_id>/<dataset>_<split>/<spec_id>.npz
        ids (n,), counts (n, T, 4), thresholds (T,)
    maps/<dataset>_<split>/<spec_name>/<id>.png (only with save_maps=True)
"""
from __future__ import annotations

import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

from . import cfg as C
from .data import Item, list_items, load_gt
from .evaluate import aggregate, image_counts, thresholds
from .methods import NATIVE01, compute
from .normalize import normalize, sample_pixels, scale_from_samples
from .preproc import load_and_preprocess


def _init_worker():
    import cv2
    cv2.setNumThreads(1)
    for v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
        os.environ[v] = "1"


def _raw_map(item: Item, spec: Dict, proto: Dict):
    img = load_and_preprocess(item.image_path, proto["preproc"])
    raw, _ = compute(img, spec, border=C.border_for(proto, spec),
                     nms_outside=proto.get("nms_outside", "zero"))
    return raw


def final_map(item: Item, spec: Dict, proto: Dict, scale: Optional[float]):
    raw = _raw_map(item, spec, proto)
    return normalize(raw, proto["normalization"], scale,
                     spec["family"] in NATIVE01, proto.get("quantize_8bit", True))


def _task_sample(args):
    item, spec, proto = args
    raw = _raw_map(item, spec, proto)
    return sample_pixels(raw, item.image_id)


def _task_counts(args):
    item, spec, proto, scale, save_png = args
    v = final_map(item, spec, proto, scale)
    if save_png:
        import cv2
        Path(save_png).parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(save_png, (v * 255.0).round().astype(np.uint8))
    thr = thresholds(int(proto["n_thresholds"]))
    c = image_counts(v, load_gt(item), thr, float(proto["max_dist_frac"]),
                     proto.get("matching", "greedy"))
    return item.image_id, c


def _pmap(fn, tasks, n_jobs, label):
    out = []
    t0 = time.time()
    n = len(tasks)
    step = max(1, n // 10)
    if n_jobs <= 1:
        _init_worker()
        for i, t in enumerate(tasks):
            out.append(fn(t))
            if (i + 1) % step == 0 or i + 1 == n:
                print(f"    {label}: {i + 1}/{n} ({time.time() - t0:.0f}s)", flush=True)
        return out
    with ProcessPoolExecutor(max_workers=n_jobs, initializer=_init_worker) as ex:
        for i, r in enumerate(ex.map(fn, tasks, chunksize=1)):
            out.append(r)
            if (i + 1) % step == 0 or i + 1 == n:
                print(f"    {label}: {i + 1}/{n} ({time.time() - t0:.0f}s)", flush=True)
    return out


def needs_scale(spec, proto) -> bool:
    return proto["normalization"] == "fixed" and spec["family"] not in NATIVE01


def get_scale(cfg, spec: Dict, proto: Dict, n_jobs: int, limit: int = 0) -> Optional[float]:
    if not needs_scale(spec, proto):
        return None
    sid = C.spec_id(spec, proto)
    f = C.results_dir(cfg, "scales") / f"{sid}.json"
    if f.exists():
        return float(json.loads(f.read_text())["scale"])
    ds, split = proto["scale_source"].split(":")
    items = list_items(cfg, ds, split)
    if limit:
        items = items[:limit]
    print(f"  [scale] {sid} on {ds}/{split} ({len(items)} images)")
    samples = _pmap(_task_sample, [(it, spec, proto) for it in items], n_jobs, "scale")
    s = scale_from_samples(samples, float(proto.get("scale_percentile", 99.9)))
    f.write_text(json.dumps(dict(scale=s, spec=spec, source=proto["scale_source"],
                                 n_images=len(items),
                                 percentile=proto.get("scale_percentile", 99.9)),
                            indent=1))
    return s


def run_counts(cfg, spec: Dict, dataset: str, split: str, proto: Dict,
               n_jobs: int = 1, save_maps: bool = False, limit: int = 0,
               force: bool = False) -> Dict:
    spec = dict(spec)
    spec.setdefault("name", C.expand_name(spec))
    sid = C.spec_id(spec, proto)
    eid = C.eval_id(proto)
    tag = f"{dataset}_{split}" + (f"_limit{limit}" if limit else "")
    f = C.results_dir(cfg, "counts", eid, tag) / f"{sid}.npz"
    if f.exists() and not force:
        z = np.load(f, allow_pickle=False)
        return dict(name=spec["name"], sid=sid, ids=list(z["ids"]),
                    counts=z["counts"], thresholds=z["thresholds"], path=str(f))
    scale = get_scale(cfg, spec, proto, n_jobs, limit=limit)
    items = list_items(cfg, dataset, split)
    if limit:
        items = items[:limit]
    print(f"  [eval] {spec['name']} on {dataset}/{split} ({len(items)} images)")
    tasks = []
    for it in items:
        png = None
        if save_maps:
            png = str(C.results_dir(cfg, "maps", tag, spec["name"]) / f"{it.image_id}.png")
        tasks.append((it, spec, proto, scale, png))
    res = _pmap(_task_counts, tasks, n_jobs, spec["name"])
    ids = [r[0] for r in res]
    counts = np.stack([r[1] for r in res])
    thr = thresholds(int(proto["n_thresholds"]))
    np.savez_compressed(f, ids=np.array(ids), counts=counts, thresholds=thr)
    (f.with_suffix(".json")).write_text(json.dumps(dict(spec=spec, proto=proto,
                                                        scale=scale), indent=1))
    return dict(name=spec["name"], sid=sid, ids=ids, counts=counts,
                thresholds=thr, path=str(f))


def summary_row(res: Dict, dataset: str, split: str) -> Dict:
    m = aggregate(res["counts"], res["thresholds"])
    # OIS and AP (primary since 9 Nov 2026, CHANGELOG.md): dataset-level
    # accumulation, as ODS and as in the A-GWi paper (JESA 44740). OIS_legacy and
    # AP_legacy: the definitions of the submitted tables (04c, mean of per-image
    # values), kept for continuity. AP_bsds101: BSDS benchmark-code AP.
    return dict(method=res["name"], dataset=dataset, split=split,
                n=m["n_images"], ODS=round(m["ods"], 4), OIS=round(m["ois"], 4),
                AP=round(m["ap"], 4), OIS_legacy=round(m["ois_legacy"], 4),
                AP_legacy=round(m["ap_legacy"], 4), AP_bsds101=round(m["ap_bsds101"], 4),
                ODS_t=round(m["ods_t"], 3),
                P_at_ODS=round(m["ods_p"], 4), R_at_ODS=round(m["ods_r"], 4),
                spec_id=res["sid"])


def align(a: Dict, b: Dict):
    """Return counts of a and b restricted to common image ids, same order."""
    ib = {k: i for i, k in enumerate(b["ids"])}
    keep = [(i, ib[k]) for i, k in enumerate(a["ids"]) if k in ib]
    ia, jb = zip(*keep)
    return a["counts"][list(ia)], b["counts"][list(jb)]


def write_csv(rows: List[Dict], path: Path):
    import csv
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        return
    keys = list(rows[0].keys())
    for r in rows[1:]:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)
    print(f"  -> {path}")
