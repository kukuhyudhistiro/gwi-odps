"""Shared CLI helpers for the revision scripts."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from rev import cfg as C  # noqa: E402


def parser(desc: str) -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=desc)
    p.add_argument("--config", default=str(ROOT / "config.yaml"))
    p.add_argument("--n-jobs", type=int, default=None)
    p.add_argument("--limit", type=int, default=0,
                   help="first N images only (smoke tests; never for the paper)")
    p.add_argument("--force", action="store_true", help="ignore cached counts")
    return p


def setup(args):
    cfg = C.load_config(args.config)
    n_jobs = args.n_jobs or int(cfg.get("n_jobs", 1))
    if args.limit:
        print(f"[WARN] --limit {args.limit}: results are for smoke tests only")
    return cfg, n_jobs


def split_ref(s: str):
    ds, sp = s.split(":")
    return ds, sp


def dump(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, default=float))
    print(f"  -> {path}")


def load_json(path: Path):
    return json.loads(Path(path).read_text())


def final_config_path(cfg, limit: int = 0) -> Path:
    name = "config_final_LIMIT.yaml" if limit else "config_final.yaml"
    return C.results_dir(cfg) / name


def load_final(cfg, limit: int = 0):
    import yaml
    p = final_config_path(cfg, limit)
    if not p.exists():
        raise SystemExit(f"{p} not found: run scripts/12_freeze.py first")
    return yaml.safe_load(p.read_text())
