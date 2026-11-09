"""Freeze the method list before the test sets are opened.

Reads results/selection/selected.json and writes config_final.yaml:
    GWi, GWi+ODPS, GWC (same kernel)       selected configuration
    GWC zero-DC (same kernel)              analysis for Reviewer 1, point 5
    the same four for k5 lambda4           if the selected configuration differs
                                           (continuity with the submission)
    baselines                              config.yaml -> baselines (Section 4.3)

After this script:
    git add results/config_final.yaml results/selection results/ablation
    git commit -m "freeze before test"
    git tag freeze-2026-11-10
"""
from __future__ import annotations

import hashlib

import yaml

from _common import dump, final_config_path, load_json, parser, setup
from rev import cfg as C
from rev.specs import d_of, gabor_specs, tag_of


def main():
    args = parser(__doc__).parse_args()
    cfg, _ = setup(args)
    proto = C.protocol_of(cfg)
    rd = C.results_dir(cfg)
    sel = load_json(rd / "selection" / "selected.json")
    kcfg = dict(k=sel["k"], lam=sel["lam"], N=sel["N"], sigma_ratio=sel["sigma_ratio"],
                gamma=sel["gamma"])
    tag = tag_of(sel["k"], sel["lam"])
    methods = list(gabor_specs(kcfg, float(sel["d"])))
    if tag != "k5l4":
        methods += gabor_specs(dict(kcfg, k=5, lam=4), d_of(4, cfg["selection"]["d_rule"]))
    methods += [dict(b) for b in cfg["baselines"]]
    seen, uniq = set(), []
    for m in methods:
        key = C.spec_id(m, proto)
        if key not in seen:
            seen.add(key)
            uniq.append(m)
    final = dict(frozen_from=cfg["_path"], protocol=proto, selected_tag=tag,
                 selection=sel,
                 primary=dict(gwi=f"GWi_{tag}", gwi_odps=f"GWiODPS_{tag}",
                              gwc=f"GWCraw_{tag}", gwc_zero=f"GWCzero_{tag}"),
                 methods=uniq, test_sets=cfg["test_sets"])
    text = yaml.safe_dump(final, sort_keys=False)
    digest = hashlib.sha256(text.encode()).hexdigest()
    path = final_config_path(cfg, args.limit)
    path.write_text(f"# sha256 of the body below: {digest}\n" + text)
    dump(dict(sha256=digest, n_methods=len(uniq), selected=tag), rd / "freeze" / "freeze.json")
    print(f"  -> {path}\n  methods: {len(uniq)}; selected: {tag}")
    print("  Next: git add results/config_final.yaml && git commit -m 'freeze' && "
          "git tag freeze-2026-11-10")


if __name__ == "__main__":
    main()
