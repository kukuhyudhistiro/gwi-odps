# Datasets

This work uses three publicly available human-annotated edge detection
benchmarks. All datasets must be obtained from their original sources.

---

## BSDS500 (Berkeley Segmentation Dataset)

### Source
[Berkeley Vision Group](https://www2.eecs.berkeley.edu/Research/Projects/CS/vision/grouping/resources.html)

### Citation
> P. Arbelaez, M. Maire, C. Fowlkes, J. Malik, "Contour detection and
> hierarchical image segmentation," IEEE TPAMI, vol. 33, no. 5,
> pp. 898-916, 2011.

### Expected Layout

```
data/BSDS500/
├── images/test/        # 200 .jpg files (321 × 481)
└── groundTruth/test/   # 200 .mat files (5-6 annotators per image)
```

Each `.mat` file contains `groundTruth[0,i]['Boundaries']` for annotator i.

---

## BIPED v2 (Barcelona Images for Perceptual Edge Detection)

### Source
[MBIPED repository](https://github.com/xavysp/MBIPED)

### Citation
> X. Soria, E. Riba, A. Sappa, "Dense extreme inception network: Towards
> a robust CNN model for edge detection," WACV, 2020, pp. 1923-1932.

### Expected Layout

```
data/BIPED/
└── edges/
    ├── imgs/test/        # 50 .jpg files (1280 × 720)
    └── edge_maps/test/   # 50 .png files (binary edge maps)
```

---

## UDED (Unified Dataset for Edge Detection)

### Source
[UDED repository](https://github.com/xavysp/UDED)

### Citation
> X. Soria, Y. Li, M. Rouhani, A. D. Sappa, "Tiny and efficient model for
> the edge detection generalization," ICCV Workshops, 2023.

### Expected Layout

```
data/UDED/
├── imgs/    # 30 .jpg images (variable resolution)
└── gt/      # 30 .png ground truth files
```

Images drawn from: BIPED, BSDS500, DIV2K, WIREFRAME, CITYSCAPES, ADE20K,
BSDS300, CID.

---

## Verification

After downloading:

```bash
python scripts/01_density_profiler.py --data-root ./data
```

Expected output:

```
BSDS500 test: 200 images, mean edge density 6.63% ± 2.03%
BIPED test:    50 images, mean edge density 3.26% ± 1.04%
UDED test:     30 images, mean edge density 6.37% ± 4.32%
```

---

## Notes

- Total dataset size: ~610 MB on disk
- Only test splits are used; GWi+ODPS has no trainable parameters
- BSDS500 evaluation uses all 5-6 annotators with per-annotator matching
- BIPED/UDED use single annotator
