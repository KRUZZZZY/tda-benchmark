#!/usr/bin/env python3
"""Expansion #6 — dynamical-systems classification generator (self-contained).

Creates three topology-relevant classification tasks that are expected to put
the topological stage in a regime where it can win (expansion-plan item #6,
"test the regime where topology actually wins"):

  (a) Lorenz vs Roessler attractor reconstructions
      Takens embedding (d=3, tau=1) of the x(t) coordinate of Lorenz
      (sigma=10, rho=28, beta=8/3) vs Roessler (a=0.2, b=0.2, c=5.7),
      integrated with RK4. Each trajectory is z-scored BEFORE embedding so
      the classes differ in *shape/topology* (Lorenz butterfly has two
      lobes/loops, Roessler a single spiral loop), not in amplitude/scale.
  (b) Double-well vs single-well potential trajectories
      Overdamped Langevin dynamics dx = -U'(x) dt + sigma dW with
      U_dw(x) = (x^2 - 1)^2  (bimodal, two clusters in the embedding) vs
      U_sw(x) = x^2 (unimodal). Euler-Maruyama, sigma=0.5. Takens d=3 tau=1.
      The double-well's persistent H0 pair (two metastable clusters) is the
      topological signal.
  (c) Noisy circle vs torus clouds, high noise
      Circle (radius 2, in the z=0 plane of R^3) vs torus (R=2, r=1), 300
      points each, Gaussian noise sigma=0.45 — the two H1 generators of the
      torus vs the single H1 generator of the circle survive the noise.

Design / reproducibility:
  * numpy-only, single global seed 42 (np.random.default_rng(42)).
  * Per task: ~60-80 samples/class; n = 200-500 points per sample.
  * Outputs are RAW POINT CLOUDS (n_samples, n_points, 3), modality
    point_cloud, so the sweep drivers cap them with subsample_points=100
    (the repo's VR budget, C(100,3) ~ 161k 2-simplices per cloud).
  * Additive-only: writes NEW .npy files under ../../data/tda/synthetic/
    (i.e. AI_KOS_PROJECT/data/tda/synthetic/). Skips files that already
    exist unless --force is passed. Never touches existing data.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/generate_dynamical_systems.py
  .venv-tda/bin/python projects/tda-benchmark/scripts/generate_dynamical_systems.py --force   # regenerate

Expected runtime: seconds (no download, no sweep).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
OUT_DIR = PROJECT_ROOT / "data" / "tda" / "synthetic"

SEED = 42


# ── (a) Lorenz vs Roessler ──────────────────────────────────────────────────

def _lorenz(state, sigma=10.0, rho=28.0, beta=8.0 / 3.0):
    x, y, z = state
    return np.array([sigma * (y - x), x * (rho - z) - y, x * y - beta * z])


def _roessler(state, a=0.2, b=0.2, c=5.7):
    x, y, z = state
    return np.array([-y - z, x + a * y, b + z * (x - c)])


def _rk4_step(f, state, dt):
    k1 = f(state)
    k2 = f(state + 0.5 * dt * k1)
    k3 = f(state + 0.5 * dt * k2)
    k4 = f(state + dt * k3)
    return state + dt / 6.0 * (k1 + 2 * k2 + 2 * k3 + k4)


def _takens_embed(series, dim=3, delay=1):
    """Embed a 1-D series into R^dim via delay coordinates (n_points, dim)."""
    n = len(series) - (dim - 1) * delay
    out = np.empty((n, dim), dtype=np.float64)
    for d in range(dim):
        out[:, d] = series[d * delay: d * delay + n]
    return out


def gen_lorenz_rossler(n_per_class=60, n_points=500, dt=0.02,
                       burn_in=1000, rng=None):
    """(X, y): Takens-embedded x(t) clouds; 0 = Lorenz, 1 = Roessler.

    Each trajectory is integrated from a random near-attractor start,
    discards `burn_in` steps, z-scores the x(t) window, then embeds with
    d=3 tau=1 -> (n_points - 2, 3) cloud.
    """
    rng = rng if rng is not None else np.random.default_rng(SEED)
    X, y = [], []
    for _ in range(n_per_class):
        # near-attractor random start
        x0 = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
        state = x0
        for _ in range(burn_in):
            state = _rk4_step(_lorenz, state, dt)
        series = np.empty(n_points)
        for i in range(n_points):
            series[i] = state[0]
            state = _rk4_step(_lorenz, state, dt)
        series = (series - series.mean()) / (series.std() + 1e-12)
        X.append(_takens_embed(series, dim=3, delay=1))
        y.append(0)
    for _ in range(n_per_class):
        x0 = np.array([1.0, 1.0, 1.0]) + rng.normal(0, 0.1, 3)
        state = x0
        for _ in range(burn_in):
            state = _rk4_step(_roessler, state, dt)
        series = np.empty(n_points)
        for i in range(n_points):
            series[i] = state[0]
            state = _rk4_step(_roessler, state, dt)
        series = (series - series.mean()) / (series.std() + 1e-12)
        X.append(_takens_embed(series, dim=3, delay=1))
        y.append(1)
    X = np.stack(X).astype(np.float64)
    y = np.asarray(y, dtype=np.int64)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


# ── (b) double-well vs single-well ──────────────────────────────────────────

def gen_doublewell(n_per_class=60, n_points=400, dt=0.01, sigma=0.5,
                   n_steps=800, rng=None):
    """(X, y): Takens-embedded Langevin trajectories; 0 = double-well, 1 = single-well.

    Euler-Maruyama with U_dw(x) = (x^2-1)^2 / U_sw(x) = x^2. The first
    `n_steps` are discarded as burn-in (transient). Trajectories are
    z-scored, then embedded d=3 tau=1 -> (n_points - 2, 3) cloud.
    """
    rng = rng if rng is not None else np.random.default_rng(SEED)
    X, y = [], []

    def euler_maruyama(force, x0, n, rng):
        xs = np.empty(n)
        x = x0
        for i in range(n):
            xs[i] = x
            x = x - force(x) * dt + sigma * np.sqrt(dt) * rng.normal()
        return xs

    for _ in range(n_per_class):
        traj = euler_maruyama(lambda x: 4 * x * (x * x - 1.0),
                              rng.normal(0, 1.5), n_steps + n_points, rng)
        series = traj[n_steps:]
        series = (series - series.mean()) / (series.std() + 1e-12)
        X.append(_takens_embed(series, dim=3, delay=1))
        y.append(0)
    for _ in range(n_per_class):
        traj = euler_maruyama(lambda x: 2 * x,
                              rng.normal(0, 1.5), n_steps + n_points, rng)
        series = traj[n_steps:]
        series = (series - series.mean()) / (series.std() + 1e-12)
        X.append(_takens_embed(series, dim=3, delay=1))
        y.append(1)
    X = np.stack(X).astype(np.float64)
    y = np.asarray(y, dtype=np.int64)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


# ── (c) noisy circle vs torus ───────────────────────────────────────────────

def gen_circle_torus(n_per_class=80, n_points=300, noise=0.45, rng=None):
    """(X, y): high-noise 3-D point clouds; 0 = circle (radius 2), 1 = torus (R=2, r=1).

    The circle lives in the z=0 plane of R^3 with radius 2 — the SAME
    enclosing radius as the torus (R=2), so the classes are not separable
    by radial scale alone (the sphere/torus scale confound, see
    tda-pipeline-benchmark skill). Gaussian noise sigma=0.45 is added
    per-coordinate. H1: circle = 1 generator, torus = 2 generators.
    """
    rng = rng if rng is not None else np.random.default_rng(SEED)
    X, y = [], []
    for _ in range(n_per_class):
        t = rng.uniform(0, 2 * np.pi, n_points)
        pts = np.column_stack([2.0 * np.cos(t), 2.0 * np.sin(t),
                               np.zeros(n_points)])
        pts = pts + rng.normal(0, noise, pts.shape)
        X.append(pts)
        y.append(0)
    for _ in range(n_per_class):
        t = rng.uniform(0, 2 * np.pi, n_points)
        s = rng.uniform(0, 2 * np.pi, n_points)
        pts = np.column_stack([
            (2.0 + 1.0 * np.cos(s)) * np.cos(t),
            (2.0 + 1.0 * np.cos(s)) * np.sin(t),
            1.0 * np.sin(s),
        ])
        pts = pts + rng.normal(0, noise, pts.shape)
        X.append(pts)
        y.append(1)
    X = np.stack(X).astype(np.float64)
    y = np.asarray(y, dtype=np.int64)
    perm = rng.permutation(len(y))
    return X[perm], y[perm]


# ── save ────────────────────────────────────────────────────────────────────

def _save(name, X, y, force=False):
    out_x = OUT_DIR / f"{name}_X.npy"
    out_y = OUT_DIR / f"{name}_y.npy"
    if (out_x.exists() or out_y.exists()) and not force:
        print(f"  [skip] {out_x.name} / {out_y.name} already exist "
              f"(use --force to regenerate)")
        return False
    np.save(out_x, X)
    np.save(out_y, y)
    print(f"  [write] {out_x.name} {X.shape} + {out_y.name} {y.shape} "
          f"(classes {np.unique(y).tolist()})")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(
        description="Expansion #6 — dynamical-systems classification generator")
    ap.add_argument("--force", action="store_true",
                    help="regenerate existing .npy files")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    print("(a) Lorenz vs Roessler (Takens x(t), d=3 tau=1, 60/class, ~498 pts)")
    Xa, ya = gen_lorenz_rossler(rng=rng)
    _save("dyn_lorenz_rossler", Xa, ya, args.force)

    print("(b) double-well vs single-well (Langevin, Takens, 60/class, ~398 pts)")
    Xb, yb = gen_doublewell(rng=rng)
    _save("dyn_doublewell", Xb, yb, args.force)

    print("(c) noisy circle vs torus (sigma=0.45, 80/class, 300 pts)")
    Xc, yc = gen_circle_torus(rng=rng)
    _save("dyn_circle_torus", Xc, yc, args.force)

    print(f"\nAll dynamical-system arrays under {OUT_DIR}")
    # ── SHA256 checksum verification (reproducibility; additive-only) ──────
    import _checksum_verify
    for rel in ("synthetic/dyn_lorenz_rossler_X.npy", "synthetic/dyn_lorenz_rossler_y.npy",
                "synthetic/dyn_doublewell_X.npy", "synthetic/dyn_doublewell_y.npy",
                "synthetic/dyn_circle_torus_X.npy", "synthetic/dyn_circle_torus_y.npy"):
        _checksum_verify.verify(rel, OUT_DIR.parent)
    print("Next: run scripts/sweep_topology_wins.py (after sweep_large_n.py "
          "has finished — single CPU).")


if __name__ == "__main__":
    main()
