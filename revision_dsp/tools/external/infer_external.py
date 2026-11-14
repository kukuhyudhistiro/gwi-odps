"""E23 (R1.2, R3.5): run one learning-based edge detector from its official repository
and official weights, and write 8-bit edge maps for scripts/23_eval_external.py.

Run with the separate E23 environment (PyTorch CPU), one method per process, because
the three repositories use clashing module names (utils, models):

    $EXT/.venv-dl/Scripts/python.exe tools/external/infer_external.py \
        --method TEED --repos "$EXT/repos" --out "$EXT/maps"
(EXT: the E23 folder, see tools/external/run_e23.sh and docs/reproduction.md A.2)

Test-time processing copies each repository's own test code (checked 10 Nov 2026):
    TEED     repo xavysp/TEED, checkpoints/BIPED/7/7_model.pth (trained on BIPED)
             BGR float, minus the test-set mean of dataset.py (Windows branch);
             if H < 512 or W < 512: resize x1.5; then, if a side is not a multiple of 8,
             resize up to the next multiple of 8 (dataset.TestDataset.transform);
             output = last (fused) map, sigmoid, per-image min-max to 0-255,
             resized to the original size (utils/img_processing.save_image_batch_to_disk).
    LDC      repo xavysp/LDC, checkpoints/BIPED/16/16_model.pth (trained on BIPED)
             BGR float minus mean_pixel_values (main.py default, BIPED mean) for every test
             set; if H < 512 or W < 512: resize to test_img_width x test_img_height of the
             test set (BSDS 480x480, UDED 512x512); elif a side is not a multiple of 8:
             next multiple of 8; output as TEED.
    PiDiNet  repo hellozhuo/pidinet, trained_models/table5_pidinet.pth (trained on BSDS500 +
             PASCAL VOC), model pidinet, config carv4, --sa --dil (README, Table 5);
             RGB, ToTensor, ImageNet mean/std, original size (edge_dataloader.Custom_Loader);
             output = last map (already sigmoid) x 255 (main.test).
The official scripts write white-background images (255 - map); here the map itself is
written (edges bright), which is what the evaluator expects. No value is changed otherwise.

Also writes <out>/<METHOD>/provenance.json (repository commit, checkpoint, settings).
With --timing, measures per-image CPU time on one thread instead (3 warm-up images, median
of 5 runs per image, as E24) and writes <out>/<METHOD>/timing.csv; with --flops, the
parameter count and multiply-accumulate count (thop) at the network input size of the
first image of each test set. --converted (PiDiNet) uses the repository's converted
model, which gives the same maps and is the form the repository times.
"""
from __future__ import annotations

import argparse
import csv
import json
import statistics as st
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import torch

REV = Path(__file__).resolve().parents[2]          # revision_dsp
sys.path.insert(0, str(REV))
from rev import cfg as C            # noqa: E402
from rev.data import list_items     # noqa: E402

DATASETS = {"BSDS500": "test", "BIPED": "test", "UDED": "test"}
TEED_MEAN = {"BSDS500": [103.939, 116.669, 122.679], "BIPED": [103.939, 116.779, 123.68],
             "UDED": [104.007, 116.669, 122.679]}
LDC_MEAN = [103.939, 116.779, 123.68]
LDC_SIZE = {"BSDS500": (480, 480), "UDED": (512, 512), "BIPED": (1280, 720)}   # (w, h)
CKPT = {"TEED": "TEED/checkpoints/BIPED/7/7_model.pth",
        "LDC": "LDC/checkpoints/BIPED/16/16_model.pth",
        "PiDiNet": "pidinet/trained_models/table5_pidinet.pth"}
REPO = {"TEED": "TEED", "LDC": "LDC", "PiDiNet": "pidinet"}
TRAINED_ON = {"TEED": "BIPED", "LDC": "BIPED", "PiDiNet": "BSDS500 (+ PASCAL VOC augmentation)"}


def up8(n):
    return n if n % 8 == 0 else (n // 8 + 1) * 8


def minmax_u8(x):
    x = x.astype(np.float64)
    return np.uint8((x - x.min()) * 255.0 / ((x.max() - x.min()) + 1e-12))


def build(method, repos: Path, converted=False):
    root = repos / REPO[method]
    sys.path.insert(0, str(root))
    if method == "TEED":
        # ted.py imports count_parameters from utils/img_processing.py, which also imports
        # kornia and scikit-learn for training-time saving and metrics. A stand-in module
        # with the same count_parameters avoids installing them; the network and its
        # weights are unaffected.
        import types
        import utils                                   # TEED's utils package (utils/AF is used)
        stub = types.ModuleType("utils.img_processing")
        stub.count_parameters = lambda model=None: sum(p.numel() for p in model.parameters() if p.requires_grad)
        sys.modules["utils.img_processing"] = stub
        utils.img_processing = stub
        from ted import TED
        model = TED()
        model.load_state_dict(torch.load(repos / CKPT[method], map_location="cpu"))
    elif method == "LDC":
        from modelB4 import LDC
        model = LDC()
        model.load_state_dict(torch.load(repos / CKPT[method], map_location="cpu"))
    elif method == "PiDiNet":
        import models
        args = argparse.Namespace(config="carv4", sa=True, dil=True)
        sd = torch.load(repos / CKPT[method], map_location="cpu", weights_only=False)["state_dict"]
        if converted:
            # The repository's vanilla-CNN form of the same weights (README: "it should
            # output the same results"), which its throughput.py uses for speed.
            from models.convert_pidinet import convert_pidinet
            model = models.pidinet_converted(args)
            sd = convert_pidinet(sd, args.config)
        else:
            model = models.pidinet(args)
        model.load_state_dict({k[7:] if k.startswith("module.") else k: v for k, v in sd.items()})
    else:
        raise SystemExit(f"unknown method {method}")
    return model.eval(), root


def prepare(method, ds, path):
    """Return (input tensor, original (h, w))."""
    if method == "PiDiNet":
        from PIL import Image
        rgb = np.asarray(Image.open(path).convert("RGB"), dtype=np.float32) / 255.0
        x = (rgb - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
        t = torch.from_numpy(x.transpose(2, 0, 1).astype(np.float32).copy())[None]
        return t, rgb.shape[:2]
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    h0, w0 = img.shape[:2]
    if method == "TEED":
        if img.shape[0] < 512 or img.shape[1] < 512:
            img = cv2.resize(img, (0, 0), fx=1.5, fy=1.5)
        if img.shape[0] % 8 != 0 or img.shape[1] % 8 != 0:
            img = cv2.resize(img, (up8(img.shape[1]), up8(img.shape[0])))
        mean = TEED_MEAN[ds]
    else:   # LDC
        if img.shape[0] < 512 or img.shape[1] < 512:
            img = cv2.resize(img, LDC_SIZE[ds])
        elif img.shape[0] % 8 != 0 or img.shape[1] % 8 != 0:
            img = cv2.resize(img, (up8(img.shape[1]), up8(img.shape[0])))
        mean = LDC_MEAN
    x = np.array(img, dtype=np.float32) - np.array(mean, dtype=np.float32)
    return torch.from_numpy(x.transpose(2, 0, 1).copy())[None], (h0, w0)


def postprocess(method, out, hw):
    fused = out[-1]
    if method == "PiDiNet":
        return (torch.squeeze(fused).numpy() * 255).astype(np.uint8)
    m = minmax_u8(torch.sigmoid(torch.squeeze(fused)).numpy())
    if m.shape != tuple(hw):
        m = cv2.resize(m, (hw[1], hw[0]))
    return m


def git_commit(root: Path):
    try:
        return subprocess.check_output(["git", "-C", str(root), "rev-parse", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True, choices=sorted(CKPT))
    ap.add_argument("--repos", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--config", default=str(REV / "config.yaml"))
    ap.add_argument("--threads", type=int, default=8)
    ap.add_argument("--timing", action="store_true")
    ap.add_argument("--flops", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--converted", action="store_true",
                    help="PiDiNet only: the repository's converted (vanilla CNN) model, same outputs")
    a = ap.parse_args()
    cfg = C.load_config(a.config)
    repos, out = Path(a.repos), Path(a.out) / a.method
    out.mkdir(parents=True, exist_ok=True)
    model, root = build(a.method, repos, a.converted)
    tag = "_converted" if a.converted else ""
    if a.flops:
        # Multiply-accumulates of every convolution and matrix product actually executed
        # (torch.utils.flop_counter, FLOPs / 2). thop was used first; it does not count the
        # functional convolutions inside PiDiNet's pixel-difference modules (F29).
        from torch.utils.flop_counter import FlopCounterMode
        rows = []
        for ds, sp in DATASETS.items():
            it = list_items(cfg, ds, sp)[0]
            x, _ = prepare(a.method, ds, it.image_path)
            fc = FlopCounterMode(display=False)
            with torch.no_grad(), fc:
                model(x)
            rows.append(dict(method=a.method + tag, dataset=ds, input_hw=f"{x.shape[2]}x{x.shape[3]}",
                             params=int(sum(p.numel() for p in model.parameters())),
                             gmacs=round(fc.get_total_flops() / 2e9, 3)))
            print(rows[-1])
        with open(out / f"flops{tag}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        return
    if a.timing:
        torch.set_num_threads(1)
        cv2.setNumThreads(1)
        rows = []
        for ds, sp in DATASETS.items():
            items = list_items(cfg, ds, sp)[: (a.limit or None)]
            with torch.no_grad():
                for it in items[:3]:                      # warm-up, untimed
                    x, hw = prepare(a.method, ds, it.image_path)
                    postprocess(a.method, model(x), hw)
                for it in items:
                    tp, tf, tq = [], [], []
                    for _ in range(5):
                        t0 = time.perf_counter()
                        x, hw = prepare(a.method, ds, it.image_path)
                        t1 = time.perf_counter()
                        o = model(x)
                        t2 = time.perf_counter()
                        postprocess(a.method, o, hw)
                        t3 = time.perf_counter()
                        tp.append(t1 - t0); tf.append(t2 - t1); tq.append(t3 - t2)
                    rows.append(dict(dataset=ds, image_id=it.image_id,
                                     pre_ms=round(1e3 * st.median(tp), 3), forward_ms=round(1e3 * st.median(tf), 3),
                                     post_ms=round(1e3 * st.median(tq), 3)))
            print(ds, "mean forward ms", round(np.mean([r["forward_ms"] for r in rows if r["dataset"] == ds]), 2), flush=True)
        with open(out / f"timing{tag}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader(); w.writerows(rows)
        return
    torch.set_num_threads(a.threads)
    n = 0
    t_start = time.time()
    with torch.no_grad():
        for ds, sp in DATASETS.items():
            d = out / ds
            d.mkdir(exist_ok=True)
            for it in list_items(cfg, ds, sp)[: (a.limit or None)]:
                x, hw = prepare(a.method, ds, it.image_path)
                m = postprocess(a.method, model(x), hw)
                assert m.shape == tuple(hw), (m.shape, hw)
                cv2.imwrite(str(d / f"{it.image_id}.png"), m)
                n += 1
            print(f"{a.method} {ds}: done", flush=True)
    (out / "provenance.json").write_text(json.dumps(dict(
        method=a.method, repository=f"https://github.com/{ {'TEED': 'xavysp/TEED', 'LDC': 'xavysp/LDC', 'PiDiNet': 'hellozhuo/pidinet'}[a.method]}",
        commit=git_commit(root), checkpoint=CKPT[a.method], trained_on=TRAINED_ON[a.method],
        torch=torch.__version__, threads=a.threads, images=n, seconds=round(time.time() - t_start, 1),
        test_time_processing=__doc__.split("Test-time processing")[1].split("The official scripts")[0].strip()),
        indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
