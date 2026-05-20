"""
00_capture_env.py
 Author: Kukuh Yudhistiro, 2026

Capture full environment snapshot for reproducibility appendix in the
GWi paper.

Output:
    env_info.txt : human-readable environment record
    env_info.json : machine-readable version

Usage:
    python 00_capture_env.py --output ./
   
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from datetime import datetime
from pathlib import Path

# Standard libs first
_versions = {
    "python": sys.version.replace("\n", " "),
    "platform_system": platform.system(),
    "platform_release": platform.release(),
    "platform_version": platform.version(),
    "platform_machine": platform.machine(),
    "platform_processor": platform.processor(),
}

# Try to capture each library version individually so missing libs don't crash
def _safe_version(modname: str) -> str:
    try:
        mod = __import__(modname)
        return getattr(mod, "__version__", "unknown")
    except ImportError:
        return "NOT_INSTALLED"


def _capture_cpu_info() -> dict:
    """Capture detailed CPU info if psutil/cpuinfo available."""
    info = {}
    try:
        import psutil
        info["physical_cores"] = psutil.cpu_count(logical=False)
        info["logical_cores"] = psutil.cpu_count(logical=True)
        info["cpu_freq_max_mhz"] = psutil.cpu_freq().max if psutil.cpu_freq() else None
        info["ram_total_gb"] = round(psutil.virtual_memory().total / (1024 ** 3), 2)
    except ImportError:
        info["psutil"] = "NOT_INSTALLED"

    try:
        import cpuinfo
        ci = cpuinfo.get_cpu_info()
        info["cpu_brand"] = ci.get("brand_raw", "unknown")
        info["cpu_arch"] = ci.get("arch", "unknown")
        info["cpu_hz_advertised"] = ci.get("hz_advertised_friendly", "unknown")
    except ImportError:
        info["cpuinfo"] = "NOT_INSTALLED (run: pip install py-cpuinfo)"

    return info


def _capture_gpu_info() -> dict:
    """Capture GPU info if available (for DL baseline reproduction)."""
    info = {}
    try:
        import torch
        info["torch_version"] = torch.__version__
        info["cuda_available"] = torch.cuda.is_available()
        if torch.cuda.is_available():
            info["cuda_version"] = torch.version.cuda
            info["cudnn_version"] = torch.backends.cudnn.version()
            info["gpu_name"] = torch.cuda.get_device_name(0)
            info["gpu_memory_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 2
            )
    except ImportError:
        info["torch"] = "NOT_INSTALLED"

    return info


def capture_environment() -> dict:
    """Capture full environment snapshot."""
    snapshot = {
        "timestamp": datetime.now().isoformat(),
        "system": _versions,
        "cpu": _capture_cpu_info(),
        "gpu": _capture_gpu_info(),
        "libraries": {
            "numpy": _safe_version("numpy"),
            "scipy": _safe_version("scipy"),
            "opencv": _safe_version("cv2"),
            "skimage": _safe_version("skimage"),
            "pandas": _safe_version("pandas"),
            "matplotlib": _safe_version("matplotlib"),
            "PIL": _safe_version("PIL"),
            "torch": _safe_version("torch"),
            "torchvision": _safe_version("torchvision"),
        },
    }
    return snapshot


def format_human_readable(snapshot: dict) -> str:
    """Format snapshot as human-readable text for paper inclusion."""
    lines = []
    lines.append("=" * 72)
    lines.append("ENVIRONMENT SNAPSHOT — GWi Paper Experiments (JESA submission)")
    lines.append("=" * 72)
    lines.append(f"Captured: {snapshot['timestamp']}")
    lines.append("")

    lines.append("--- System ---")
    sys_info = snapshot["system"]
    lines.append(f"  Python : {sys_info['python']}")
    lines.append(f"  OS     : {sys_info['platform_system']} "
                 f"{sys_info['platform_release']}")
    lines.append(f"  Arch   : {sys_info['platform_machine']}")
    lines.append("")

    lines.append("--- CPU ---")
    cpu = snapshot["cpu"]
    if "cpu_brand" in cpu:
        lines.append(f"  Model        : {cpu['cpu_brand']}")
    lines.append(f"  Physical cores : {cpu.get('physical_cores', 'N/A')}")
    lines.append(f"  Logical cores  : {cpu.get('logical_cores', 'N/A')}")
    lines.append(f"  Max freq (MHz) : {cpu.get('cpu_freq_max_mhz', 'N/A')}")
    lines.append(f"  RAM (GB)       : {cpu.get('ram_total_gb', 'N/A')}")
    lines.append("")

    lines.append("--- GPU (for DL baseline inference only) ---")
    gpu = snapshot["gpu"]
    if gpu.get("cuda_available"):
        lines.append(f"  GPU        : {gpu.get('gpu_name', 'N/A')}")
        lines.append(f"  GPU memory : {gpu.get('gpu_memory_gb', 'N/A')} GB")
        lines.append(f"  CUDA       : {gpu.get('cuda_version', 'N/A')}")
        lines.append(f"  cuDNN      : {gpu.get('cudnn_version', 'N/A')}")
        lines.append(f"  PyTorch    : {gpu.get('torch_version', 'N/A')}")
    else:
        lines.append("  CUDA not available (CPU-only mode)")
    lines.append("")

    lines.append("--- Libraries ---")
    for lib, ver in snapshot["libraries"].items():
        lines.append(f"  {lib:15s}: {ver}")
    lines.append("")

    lines.append("--- Reproducibility note for paper ---")
    lines.append("  All GWi and classical baseline runtime measurements were")
    lines.append("  performed in SINGLE-THREADED mode by setting:")
    lines.append("    os.environ['OMP_NUM_THREADS'] = '1'")
    lines.append("    cv2.setNumThreads(1)")
    lines.append("  This ensures fair comparison and matches the reviewer's")
    lines.append("  request for controlled runtime evaluation.")
    lines.append("=" * 72)

    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("./"),
                        help="Output directory")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)

    snapshot = capture_environment()

    # JSON for machine-readable record
    json_path = args.output / "env_info.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=2)

    # Text for human-readable / paper inclusion
    txt_path = args.output / "env_info.txt"
    text = format_human_readable(snapshot)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Also print to console
    print(text)
    print(f"\n[OK] Written: {json_path}")
    print(f"[OK] Written: {txt_path}")


if __name__ == "__main__":
    main()
