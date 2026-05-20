"""GWi+ODPS: Imaginary-only Gabor Wavelet edge detection with
Orientation-aware Double-Peak Suppression.

Public API:
    - gabor_core.GaborParams         : Parameter container (defaults k=5, λ=4)
    - gabor_core.GWiFilterBank        : 8-orientation imaginary Gabor bank
    - gabor_core.run_gwi              : Stage 3-5 GWi pipeline runner
    - gabor_core.run_gwc              : Reference complex Gabor runner
    - nms_odps.odps                   : Stage 6 — orientation-aware NMS
    - baselines                       : Canny, Sobel, LoG, PC, ED wrappers
    - preprocessing.load_and_preprocess : Stage 1 preprocessing
    - edge_eval                        : Berkeley evaluation protocol

Author: Kukuh Yudhistiro, Nova Rijati, Ruri Suko Basuki
"""

__version__ = "2.0.0"
__author__ = "Kukuh Yudhistiro, Nova Rijati, Ruri Suko Basuki"
__license__ = "MIT"
