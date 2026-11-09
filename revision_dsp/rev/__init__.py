"""Revision package for DSP-D-26-02462 (GWi+ODPS).

All new results for the revision are produced by this package. The original
repo (gwi-odps, commit 91b4f83) is only used through rev/legacy.py for
equivalence tests.
"""
import os

for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
           "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS"):
    os.environ.setdefault(_v, "1")

__version__ = "1.0.0"
