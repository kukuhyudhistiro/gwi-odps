# How to Upload to GitHub

> Maintainer guide for uploading this reproducibility package.
> **Delete this file after upload.**

---

## Pre-Upload Checklist

```
GWi_ODPS_GITHUB_v2/
├── .gitignore
├── CHANGELOG.md
├── CITATION.cff
├── LICENSE
├── README.md                          # ← main repo page
├── requirements.txt
├── setup.py
├── UPLOAD_TO_GITHUB.md                # delete after upload
├── data/
│   └── README.md
├── docs/
│   ├── ODPS_derivation.md
│   ├── benchmarks.md
│   ├── datasets.md
│   ├── kernel_ablation.md
│   └── reproduction.md
├── eval_results/k5/
│   ├── ablation_multi_dataset.csv
│   └── ods_summary.csv
├── manuscript/
│   ├── README.md
│   ├── PAPER_REVISION_k5_FINAL.md
│   ├── figures/                       # 3 PNGs + README
│   ├── sections/                      # 8 .md files
│   └── tables/tables.md
├── runtime_logs/
│   └── runtime_unified_k5.csv
├── scripts/                           # 10 .py files
├── src/                               # 7 .py files (incl. __init__.py)
└── tests/                             # placeholder
```

---

## Step 1: Create GitHub Repo

1. Sign in to [github.com](https://github.com), click **+** → **New repository**
2. **Name**: `GWi-ODPS` (or `gwi-odps`)
3. **Description**: "Imaginary-only Gabor wavelet edge detection with orientation-aware double-peak suppression. Reference implementation."
4. **Public**, **don't initialize** with README/.gitignore/license (we have them)
5. **Create repository**

Note URL: `https://github.com/<your-username>/GWi-ODPS.git`

---

## Step 2: Personalize Placeholders

```bash
cd GWi_ODPS_GITHUB_v2

# Linux/macOS — replace <username> in 3 files
sed -i 's|<username>|your-actual-username|g' README.md CITATION.cff setup.py

# Windows PowerShell
(Get-Content README.md) -replace '<username>', 'your-username' | Set-Content README.md
(Get-Content CITATION.cff) -replace '<username>', 'your-username' | Set-Content CITATION.cff
(Get-Content setup.py) -replace '<username>', 'your-username' | Set-Content setup.py
```

Update email/affiliation if needed in `README.md`, `CITATION.cff`, `LICENSE`.

---

## Step 3: Initialize Local Repo

```bash
cd GWi_ODPS_GITHUB_v2

git init -b main
git add .
git status                          # verify ~40-50 files staged
git commit -m "Initial release v2.0.0: GWi+ODPS reference (k=5 canonical)"
```

---

## Step 4: Push to GitHub

```bash
git remote add origin https://github.com/<your-username>/GWi-ODPS.git
git push -u origin main
```

If prompted, use **Personal Access Token** (https://github.com/settings/tokens) with `repo` scope.

---

## Step 5: Verify

Visit `https://github.com/<your-username>/GWi-ODPS`. You should see:

1. README.md rendered as main page with badges
2. License badge (MIT)
3. All directories present
4. CITATION.cff parsed → "Cite this repository" button in sidebar

---

## Step 6: Create Release (Recommended for DOI)

1. Repo page → **Releases** → **Create a new release**
2. **Tag**: `v2.0.0`
3. **Title**: `v2.0.0 — Canonical k=5 baseline`
4. **Description**: Copy from `CHANGELOG.md`
5. **Publish release**

### Get Zenodo DOI (optional)

1. Sign in to [Zenodo](https://zenodo.org) with GitHub
2. Toggle this repo on at https://zenodo.org/account/settings/github/
3. Re-create release → Zenodo auto-archives + assigns DOI
4. Update `CITATION.cff` with DOI

---

## Step 7: Repository Polish

### Add topics (helps discoverability)

Settings → gear icon next to "About" → topics:
- `edge-detection`
- `gabor-wavelet`
- `computer-vision`
- `image-processing`
- `non-maximum-suppression`
- `reproducible-research`

### Description and homepage

Same gear icon:
- **Description**: "Imaginary-only Gabor wavelet edge detection with orientation-aware double-peak suppression"
- **Website**: (after publication) link to paper

---

## Step 8: Cleanup

```bash
git rm UPLOAD_TO_GITHUB.md
git commit -m "docs: remove maintainer-only upload guide"
git push
```

---

## Maintenance

### Updating code

```bash
git add <changed files>
git commit -m "type: brief description"
git push
```

Conventional commit types: `feat:`, `fix:`, `docs:`, `refactor:`, `perf:`, `test:`.

### Tag releases

```bash
git tag -a v2.1.0 -m "Description of changes"
git push --tags
```

### When paper is published

1. Update README citation block with published reference
2. Update `CITATION.cff` with `journal:`, `doi:`, `volume:`, `pages:`
3. Create `v2.0.0-published` release

---

## Troubleshooting

### "Permission denied (publickey)" on push

Switch to HTTPS:
```bash
git remote set-url origin https://github.com/<username>/GWi-ODPS.git
```

### Files too large

`.gitignore` excludes datasets and large outputs. If accidentally added:
```bash
git rm --cached path/to/large-file
echo "path/to/large-file" >> .gitignore
git add .gitignore
git commit -m "chore: ignore large file"
```

### CITATION.cff doesn't validate

Use [CFF validator](https://citation-file-format.github.io/cff-validator/).

---

## Total Time

| Task | Time |
|------|------|
| Personalize files | 2 min |
| Create repo | 2 min |
| Git init + commit + push | 3 min |
| Verify + add topics | 5 min |
| Create release + Zenodo (optional) | 5 min |
| **Total** | **~15-20 min** |

After upload, link to repo in paper cover letter under "Code availability".
