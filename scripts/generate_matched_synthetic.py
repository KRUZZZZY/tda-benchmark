#!/usr/bin/env python3
"""Generate scale-matched synthetic point clouds for the TDA benchmark (additive).

Produces, under data/tda/synthetic_matched/:
  matched_torus_genus_noise{0,30}_{X,y}.npy   200 x 200 x 3 (+ labels)

Classes (200 points per cloud, 100 clouds per class, matching the paper's
200-sample / 5-fold protocol):
  class 0  genus-1 torus, R = 2.0, r = 1.0 (same geometry as the executed sweep)
  class 1  genus-2 "double torus": two tori of equal total surface area
           (R' = 1.5, r' = 0.75, centres at z = +/-1.0) joined by a tube of
           radius R' - r' = 0.75 through their holes (connected sum).

Scale matching: the class-1 point cloud is radially rescaled by a monotone
piecewise-linear map f (quantile matching, estimated on pooled reference
clouds) so that the *empirical norm distribution of class 1 equals that of
class 0 exactly* (up to quantile-estimation error). f is a radial
homeomorphism of R^3 \\ {0}, so it preserves the topology of the point cloud
(afterwards class 1 still has Betti_1 = 4 vs Betti_1 = 2 for class 0).

Noise model matches the paper: additive Gaussian noise N(0, sigma^2 I_3)
added to the *same* clean clouds (sigma = 0.00 / 0.30).

Diagnostics printed: H1 persistence profile (ripser) of sample clouds and
norm-feature separability of the generated pair.
"""

from __future__ import annotations

import os
import sys

import numpy as np

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "tda", "synthetic_matched")
N_SAMPLES = 100          # clouds per class
N_POINTS = 200           # points per cloud
N_PIPE = 20              # points on the connecting tube
SIGMAS = [0.00, 0.30]
SEED = 42


def torus_cloud(n: int, R: float = 2.0, r: float = 1.0, cz: float = 0.0,
                rng: np.random.Generator | None = None) -> np.ndarray:
    """Uniform points on a torus of major radius R, minor radius r, centre (0,0,cz)."""
    rng = rng or np.random.default_rng()
    u = rng.uniform(0, 2 * np.pi, n)
    v = rng.uniform(0, 2 * np.pi, n)
    return np.stack([
        (R + r * np.cos(v)) * np.cos(u),
        (R + r * np.cos(v)) * np.sin(u),
        cz + r * np.sin(v),
    ], axis=1)


def double_torus_cloud(n_total: int, rng: np.random.Generator) -> np.ndarray:
    """Genus-2 connected sum: two equal-area tori (R'=1.5, r'=0.75, cz=+-1.0)
    joined by a tube of radius 0.75 through their holes."""
    n_a = n_b = (n_total - N_PIPE) // 2
    A = torus_cloud(n_a, R=1.5, r=0.75, cz=1.0, rng=rng)
    B = torus_cloud(n_b, R=1.5, r=0.75, cz=-1.0, rng=rng)
    u = rng.uniform(0, 2 * np.pi, N_PIPE)
    z = rng.uniform(-1.0, 1.0, N_PIPE)
    T = np.stack([0.75 * np.cos(u), 0.75 * np.sin(u), z], axis=1)
    return np.vstack([A, B, T])


def quantile_map(pool0: np.ndarray, pool1: np.ndarray) -> callable:
    """Monotone piecewise-linear radial map f with f(Q1(q)) = Q0(q)."""
    qs = np.linspace(0.0005, 0.9995, 400)
    q0 = np.quantile(pool0, qs)
    q1 = np.quantile(pool1, qs)
    return lambda s: np.interp(s, q1, q0)


def main() -> None:
    os.makedirs(DATA_DIR, exist_ok=True)
    base = np.random.default_rng(SEED)

    # ── pooled reference distributions for quantile matching ──────────────
    pool0, pool1 = [], []
    for i in range(40):
        r = np.random.default_rng(6000 + i)
        pool0.append(np.linalg.norm(torus_cloud(N_POINTS, cz=0.0, rng=r), axis=1))
        pool1.append(np.linalg.norm(double_torus_cloud(N_POINTS, rng=r), axis=1))
    pool0 = np.concatenate(pool0)
    pool1 = np.concatenate(pool1)
    f = quantile_map(pool0, pool1)

    # ── generate the two classes ───────────────────────────────────────────
    X0 = np.stack([torus_cloud(N_POINTS, cz=0.0, rng=np.random.default_rng(100 + i))
                   for i in range(N_SAMPLES)])
    X1 = []
    for i in range(N_SAMPLES):
        r = np.random.default_rng(200 + i)
        c = double_torus_cloud(N_POINTS, rng=r)
        nn = np.linalg.norm(c, axis=1)
        X1.append(c * (f(nn) / nn)[:, None])
    X1 = np.stack(X1)
    y = np.concatenate([np.zeros(N_SAMPLES), np.ones(N_SAMPLES)]).astype(np.int64)

    # ── topology + norm-separability diagnostics (clean) ──────────────────
    try:
        import ripser
        for i in (0, 1, 2):
            p0 = np.sort(ripser.ripser(X0[i], maxdim=1)['dgms'][1][:, 1] -
                         ripser.ripser(X0[i], maxdim=1)['dgms'][1][:, 0])[::-1]
            p1 = np.sort(ripser.ripser(X1[i], maxdim=1)['dgms'][1][:, 1] -
                         ripser.ripser(X1[i], maxdim=1)['dgms'][1][:, 0])[::-1]
            print(f"  diag cloud {i}: genus1 top-4 H1 pers {[round(x,2) for x in p0[:4]]} | "
                  f"genus2 top-4 {[round(x,2) for x in p1[:4]]}")
        from sklearn.linear_model import LogisticRegression
        from sklearn.model_selection import StratifiedKFold, cross_val_score
        N = np.linalg.norm(np.vstack([X0, X1]), axis=2)
        F = np.stack([N.mean(1), N.max(1), N.min(1)], axis=1)
        cv = StratifiedKFold(5, shuffle=True, random_state=43)
        s = cross_val_score(LogisticRegression(max_iter=2000), F, y, cv=cv)
        print(f"  norm-feature logistic on matched pair: mean {s.mean():.4f} "
              f"(folds {[round(x,3) for x in s]})")
    except Exception as exc:  # pragma: no cover
        print(f"  [diagnostics skipped: {exc}]")

    # ── save clean + noisy versions ────────────────────────────────────────
    X_clean = np.vstack([X0, X1])
    for sigma in SIGMAS:
        X = X_clean.copy()
        if sigma > 0.0:
            X = X + base.normal(0.0, sigma, X.shape)
        tag = f"noise{int(sigma * 100)}"
        np.save(os.path.join(DATA_DIR, f"matched_torus_genus_{tag}_X.npy"), X)
        np.save(os.path.join(DATA_DIR, f"matched_torus_genus_{tag}_y.npy"), y)
        print(f"  matched_torus_genus_{tag}: {X.shape} sigma={sigma}")
    # ── SHA256 checksum verification (reproducibility; additive-only) ──────
    import _checksum_verify
    for tag in ("noise0", "noise30"):
        _checksum_verify.verify(f"synthetic_matched/matched_torus_genus_{tag}_X.npy",
                                os.path.dirname(DATA_DIR))
        _checksum_verify.verify(f"synthetic_matched/matched_torus_genus_{tag}_y.npy",
                                os.path.dirname(DATA_DIR))
    print("done.")


if __name__ == "__main__":
    sys.exit(main())
