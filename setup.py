"""Setup script for GWi+ODPS package.

Installation:
    pip install -e .

Optional — the scripts can be run directly without installing.
"""

from pathlib import Path
from setuptools import find_packages, setup


root = Path(__file__).parent
long_description = (root / "README.md").read_text(encoding="utf-8")


setup(
    name="gwi-odps",
    version="2.0.0",
    description=(
        "Imaginary-only Gabor Wavelet edge detection with "
        "Orientation-aware Double-Peak Suppression"
    ),
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Kukuh Yudhistiro, Nova Rijati, Ruri Suko Basuki",
    author_email="kukuh.yudhistiro@dsn.dinus.ac.id",
    url="https://github.com/<username>/GWi-ODPS",
    license="MIT",
    python_requires=">=3.10",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "numpy>=1.26,<3.0",
        "scipy>=1.10",
        "scikit-image>=0.21",
        "Pillow>=10.0",
        "opencv-contrib-python>=4.10",
        "pandas>=2.0",
        "matplotlib>=3.8",
        "phasepack>=1.5",
        "psutil>=5.9",
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Programming Language :: Python :: 3.13",
        "Topic :: Scientific/Engineering :: Image Recognition",
    ],
    keywords=[
        "edge detection",
        "Gabor wavelet",
        "non-maximum suppression",
        "computer vision",
        "image processing",
    ],
)
