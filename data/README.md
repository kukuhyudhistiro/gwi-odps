# Datasets Directory

Place benchmark datasets here. **Not included in this repository** due to license restrictions.

See [`../docs/datasets.md`](../docs/datasets.md) for download instructions.

## Expected Structure

```
data/
├── BSDS500/
│   ├── images/test/         # 200 .jpg files
│   └── groundTruth/test/    # 200 .mat files
├── BIPED/
│   └── edges/
│       ├── imgs/test/       # 50 .jpg files (1280×720)
│       └── edge_maps/test/  # 50 .png files
└── UDED/
    ├── imgs/                # 30 .jpg files
    └── gt/                  # 30 .png files
```

## Verify Placement

```bash
python ../scripts/01_density_profiler.py --data-root .
```

Expected:
```
BSDS500 test: 200 images, mean edge density 6.63% ± 2.03%
BIPED test:    50 images, mean edge density 3.26% ± 1.04%
UDED test:     30 images, mean edge density 6.37% ± 4.32%
```
