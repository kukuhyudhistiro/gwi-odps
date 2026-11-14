# Datasets Directory

Place benchmark datasets here. **Not included in this repository** due to license restrictions.

See [`../docs/datasets.md`](../docs/datasets.md) for download instructions.

## Expected Structure

```
data/
├── BSDS500/
│   ├── images/{train,val,test}/        # 200 / 100 / 200 .jpg (train and val: revision only)
│   └── groundTruth/{train,val,test}/   # 200 / 100 / 200 .mat
├── BIPED/
│   └── edges/
│       ├── imgs/train/rgbr/real/       # 200 .jpg (revision only)
│       ├── imgs/test/                  # 50 .jpg (1280×720)
│       ├── edge_maps/train/rgbr/real/  # 200 .png (revision only)
│       └── edge_maps/test/             # 50 .png
└── UDED/
    ├── imgs/                           # 30 .png files
    └── gt/                             # 30 .png files
```

The revision (`revision_dsp/`) reads these paths from `revision_dsp/config.yaml` (`datasets:`).

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
