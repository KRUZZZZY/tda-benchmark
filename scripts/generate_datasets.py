#!/usr/bin/env python3
"""Regenerate the executed benchmark datasets (tda-benchmark, 616-config sweep).

Produces, under data/tda/:
  synthetic/sphere_torus_noise{0,5,15,30}_{X,y}.npy   200 x 100 x 3 (+ labels)
  ucr/ecg200_{X,y}.npy                                 200 x 96 (+ labels)
  images/mnist_01_{X,y}.npy                            400 x 28 x 28 (+ labels)

Shapes match the executed sweep (verified against expanded_results.db):
sphere/torus point clouds are 200 samples x 100 points x 3D, noise applied to
coordinates; ECG200 is the UCR archive (96 timesteps); MNIST 0/1 is the binary
subset with 200 samples per class.

Usage: python scripts/generate_datasets.py [--data-dir data/tda] [--seed 42]
Requires: numpy, and (for ECG200/MNIST) the source archives on disk:
  ECG200: UCR archive .arff (see tda-experiments skill for parsing) or
          pre-parsed .npy from the author.
  MNIST:  standard 28x28 digits; the binary 0/1 subset is extracted here.
"""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np


def sphere_cloud(n_points: int = 100, rng: np.random.Generator | None = None) -> np.ndarray:
    """Uniform points on S^2."""
    rng = rng or np.random.default_rng()
    pts = rng.normal(size=(n_points, 3))
    return pts / np.linalg.norm(pts, axis=1, keepdims=True)


def torus_cloud(n_points: int = 100, R: float = 2.0, r: float = 1.0,
                rng: np.random.Generator | None = None) -> np.ndarray:
    """Uniform points on a torus of major radius R and minor radius r."""
    rng = rng or np.random.default_rng()
    u = rng.uniform(0, 2 * np.pi, n_points)
    v = rng.uniform(0, 2 * np.pi, n_points)
    return np.stack([
        (R + r * np.cos(v)) * np.cos(u),
        (R + r * np.cos(v)) * np.sin(u),
        r * np.sin(v),
    ], axis=1)


def make_sphere_torus(data_dir: str, seed: int) -> None:
    """200 samples per noise level: 100 spheres (label 0) + 100 tori (label 1)."""
    out = os.path.join(data_dir, "synthetic")
    os.makedirs(out, exist_ok=True)
    base_rng = np.random.default_rng(seed)
    sigmas = [0.00, 0.05, 0.15, 0.30]
    n_per_class = 100
    for sigma in sigmas:
        rng = np.random.default_rng(seed + int(sigma * 1000))
        X = np.empty((2 * n_per_class, 100, 3))
        y = np.concatenate([np.zeros(n_per_class), np.ones(n_per_class)]).astype(np.int64)
        for i in range(n_per_class):
            X[i] = sphere_cloud(rng=rng)
            X[n_per_class + i] = torus_cloud(rng=rng, R=2.0, r=1.0)
        if sigma > 0:
            noise = rng.normal(0, sigma, X.shape)
            X = X + noise
        tag = f"noise{int(sigma * 100)}"
        np.save(os.path.join(out, f"sphere_torus_{tag}_X.npy"), X)
        np.save(os.path.join(out, f"sphere_torus_{tag}_y.npy"), y)
        print(f"  sphere_torus_{tag}: {X.shape} sigma={sigma}")


def make_ecg200(data_dir: str) -> None:
    """ECG200 from the UCR archive .arff (timeseriesclassification.com).

    The executed file is 200 x 96 float64 with binary labels. If a pre-parsed
    .npy exists (author's copy), it is copied as-is; otherwise the .arff is
    parsed (class label is the LAST comma-separated field after @data).
    """
    out = os.path.join(data_dir, "ucr")
    os.makedirs(out, exist_ok=True)
    x_path, y_path = os.path.join(out, "ecg200_X.npy"), os.path.join(out, "ecg200_y.npy")
    if os.path.exists(x_path) and os.path.exists(y_path):
        print(f"  ecg200: already present ({np.load(x_path).shape}) — skipping")
        return
    arff = os.path.join(out, "ECG200.arff")
    if not os.path.exists(arff):
        print("  ecg200: no ECG200.arff found; place the UCR .arff in data/tda/ucr/")
        print("          (or provide pre-parsed ecg200_X.npy / ecg200_y.npy)")
        return
    with open(arff) as fh:
        lines = fh.readlines()
    data_start = next(i for i, l in enumerate(lines) if l.strip().startswith("@data"))
    rows = []
    for l in lines[data_start + 1:]:
        l = l.strip()
        if not l:
            continue
        parts = l.split(",")
        rows.append((np.array([float(x) for x in parts[:-1]]), int(float(parts[-1]))))
    X = np.stack([r[0] for r in rows])
    y = np.array([r[1] for r in rows], dtype=np.int64)
    # UCR ECG200 labels are {1, -1}; the executed benchmark uses {0, 1}
    y = (y > 0).astype(np.int64)
    np.save(x_path, X)
    np.save(y_path, y)
    print(f"  ecg200: {X.shape} from ECG200.arff")


def make_mnist_01(data_dir: str) -> None:
    """MNIST binary 0/1 subset: 200 per class, 400 total, 28x28.

    Requires mnist_X.npy / mnist_y.npy (full 70k set) in data/tda/images/.
    """
    out = os.path.join(data_dir, "images")
    os.makedirs(out, exist_ok=True)
    xp, yp = os.path.join(out, "mnist_01_X.npy"), os.path.join(out, "mnist_01_y.npy")
    if os.path.exists(xp) and os.path.exists(yp):
        print(f"  mnist_01: already present ({np.load(xp).shape}) — skipping")
        return
    full_x, full_y = os.path.join(out, "mnist_X.npy"), os.path.join(out, "mnist_y.npy")
    if not (os.path.exists(full_x) and os.path.exists(full_y)):
        print("  mnist_01: mnist_X.npy / mnist_y.npy not found; place the full set in")
        print("           data/tda/images/ (or provide mnist_01_X.npy directly)")
        return
    X, y = np.load(full_x), np.load(full_y)
    sel = np.where((y == 0) | (y == 1))[0]
    # balanced 200 per class, deterministic
    rng = np.random.default_rng(42)
    idx0 = rng.choice(sel[y[sel] == 0], 200, replace=False)
    idx1 = rng.choice(sel[y[sel] == 1], 200, replace=False)
    idx = np.concatenate([idx0, idx1])
    X01 = X[idx].astype(np.float32)
    y01 = y[idx].astype(np.int64)
    np.save(xp, X01)
    np.save(yp, y01)
    print(f"  mnist_01: {X01.shape} (200/class)")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default="data/tda")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()
    os.makedirs(args.data_dir, exist_ok=True)
    make_sphere_torus(args.data_dir, args.seed)
    make_ecg200(args.data_dir)
    make_mnist_01(args.data_dir)
    # ── SHA256 checksum verification (reproducibility; additive-only) ──────
    import _checksum_verify
    for rel in ("synthetic/sphere_torus_noise0_X.npy", "synthetic/sphere_torus_noise0_y.npy",
                "synthetic/sphere_torus_noise5_X.npy", "synthetic/sphere_torus_noise5_y.npy",
                "synthetic/sphere_torus_noise15_X.npy", "synthetic/sphere_torus_noise15_y.npy",
                "synthetic/sphere_torus_noise30_X.npy", "synthetic/sphere_torus_noise30_y.npy"):
        _checksum_verify.verify(rel, args.data_dir)
    for rel in ("ucr/ecg200_X.npy", "ucr/ecg200_y.npy",
                "images/mnist_01_X.npy", "images/mnist_01_y.npy"):
        _checksum_verify.verify_if_covered(rel, args.data_dir)
    print("done.")


if __name__ == "__main__":
    main()
