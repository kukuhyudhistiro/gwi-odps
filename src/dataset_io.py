"""
dataset_io.py

Dataset abstraction for BSDS500, BIPED v2, and UDED.

Each dataset is iterated as a list of `Sample(image_path, gt_path, image_id)`.
The density manifest from Phase 1 is used to attach tertile labels.

This module replaces the original hardcoded 3-image dict from the Colab
notebook with a clean iterator pattern that scales to hundreds of images.

Author: Kukuh Yudhistiro
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, Optional, List

import pandas as pd


@dataclass
class Sample:
    """One evaluation sample."""

    dataset: str          # 'BSDS500' | 'BIPED' | 'UDED'
    image_id: str         # filename stem
    image_path: Path
    gt_path: Path
    tertile_label: Optional[str] = None  # 'LOW' | 'MID' | 'HIGH'
    density_pct: Optional[float] = None


class DatasetIterator:
    """Iterate over samples from one or more datasets.

    Parameters:
        data_root          : root directory containing BSDS500/, BIPED/, UDED/
        density_manifest   : optional path to density_manifest.csv from Phase 1
        datasets           : list of datasets to include
                             (default: all three)
        split              : 'test' for BSDS500 and BIPED, 'all' for UDED
    """

    # Default subdirectory layout (matches README)
    LAYOUTS = {
        "BSDS500": {
            "image_subdir": "images/test",
            "image_ext": [".jpg", ".png"],
            "gt_subdir": "groundTruth/test",
            "gt_ext": [".mat"],
        },
        "BIPED": {
            "image_subdir": "edges/imgs/test",
            "image_ext": [".jpg", ".png"],
            "gt_subdir": "edge_maps/test",
            "gt_ext": [".png"],
        },
        "UDED": {
            "image_subdir": "imgs",
            "image_ext": [".jpg", ".png"],
            "gt_subdir": "gt",
            "gt_ext": [".png"],
        },
    }

    def __init__(self,
                 data_root: Path,
                 density_manifest: Optional[Path] = None,
                 datasets: Optional[List[str]] = None) -> None:
        self.data_root = Path(data_root)
        self.datasets = datasets or list(self.LAYOUTS.keys())

        # Load density manifest if provided
        self.density_lookup = {}  # (dataset, image_id) -> (tertile, density)
        if density_manifest and Path(density_manifest).exists():
            df = pd.read_csv(density_manifest)
            for _, row in df.iterrows():
                key = (row["dataset"], str(row["image_id"]))
                self.density_lookup[key] = (
                    row["tertile_label"],
                    float(row["density_pct"]),
                )

    def _find_image_for_gt(self, dataset: str, gt_path: Path,
                           image_dir: Path) -> Optional[Path]:
        """Find matching image file for a ground-truth file."""
        stem = gt_path.stem
        for ext in self.LAYOUTS[dataset]["image_ext"]:
            p = image_dir / f"{stem}{ext}"
            if p.exists():
                return p
        return None

    def iter_dataset(self, dataset: str) -> Iterator[Sample]:
        """Iterate over all samples in one dataset."""
        if dataset not in self.LAYOUTS:
            raise ValueError(f"Unknown dataset: {dataset}")

        layout = self.LAYOUTS[dataset]
        ds_root = self.data_root / dataset
        image_dir = ds_root / layout["image_subdir"]
        gt_dir = ds_root / layout["gt_subdir"]

        if not gt_dir.exists():
            raise FileNotFoundError(f"GT directory not found: {gt_dir}")
        if not image_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {image_dir}")

        # Iterate based on GT files (each GT must have a matching image)
        gt_files = []
        for ext in layout["gt_ext"]:
            gt_files.extend(sorted(gt_dir.glob(f"*{ext}")))

        for gt_path in gt_files:
            image_path = self._find_image_for_gt(dataset, gt_path, image_dir)
            if image_path is None:
                continue  # silently skip orphan GT
            tertile, density = self.density_lookup.get(
                (dataset, gt_path.stem), (None, None)
            )
            yield Sample(
                dataset=dataset,
                image_id=gt_path.stem,
                image_path=image_path,
                gt_path=gt_path,
                tertile_label=tertile,
                density_pct=density,
            )

    def iter_all(self) -> Iterator[Sample]:
        """Iterate over all configured datasets."""
        for ds in self.datasets:
            yield from self.iter_dataset(ds)

    def count(self, dataset: str) -> int:
        """Count samples in one dataset."""
        return sum(1 for _ in self.iter_dataset(dataset))
