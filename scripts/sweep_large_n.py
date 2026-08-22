#!/usr/bin/env python3
"""Expansion B5 (#7b) — Sparse Rips at its design point (large n).

The paper's recommendation row for Sparse Rips is untestable there because
the synthetic point clouds are only 100 points (Sparse Rips is a SPARSE
approximation whose runtime benefit appears at large n, and whose geometry
accuracy degrades only mildly then). This sweep generates sphere/torus point
clouds at n = {1000, 3000} and runs Sparse Rips — the design point — plus a
Vietoris-Rips control on n=1000 (VR at 3000 is infeasible: C(3000,3) tessels).

Design: sphere/torus synthetic clouds, noise0, 20 spheres + 20 tori = 40
samples per (n, filtration) arm. Filtrations x {betti_curve,
persistence_landscape} x {random_forest, svm_rbf}, 5-fold CV seed 42 rep=1.

SINGLE-CPU (user directive): n_jobs=1, serial loop, no delegation.
Additive-only: NEW large-n .npy arrays in data/tda/synthetic/ + NEW DB
data/tda/large_n_sweep.db. No existing data/code touched.

Usage (from AI_KOS_PROJECT root):
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_large_n.py
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO.parent))
if "tda_benchmark" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark", os.path.join(str(REPO), "__init__.py"),
        submodule_search_locations=[str(REPO)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)

from tda_benchmark.config import (  # noqa: E402
    ClassifierConfig, DatasetConfig, FiltrationConfig, VectorizationConfig,
)
from tda_benchmark.runner import _run_one_worker  # noqa: E402

PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
SYNTH = PROJECT_ROOT / "data" / "tda" / "synthetic"
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "large_n_sweep.db")

CV_FOLDS = 5
RANDOM_SEED = 42
REP = 1
N_SAMPLES_PER_CLASS = 20


def sphere_cloud(n_points, rng):
    pts = rng.normal(size=(n_points, 3))
    return pts / np.linalg.norm(pts, axis=1, keepdims=True)


def torus_cloud(n_points, R=2.0, r=1.0, rng=None):
    rng = rng or np.random.default_rng()
    u = rng.uniform(0, 2 * np.pi, n_points)
    v = rng.uniform(0, 2 * np.pi, n_points)
    return np.column_stack([
        (R + r * np.cos(v)) * np.cos(u),
        (R + r * np.cos(v)) * np.sin(u),
        r * np.sin(v),
    ])


def make_large_clouds() -> dict:
    """Generate additive sphere/torus arrays at n=1000,3000. Returns {n: path}."""
    out = {}
    rng = np.random.default_rng(42)
    for n in (1000, 3000):
        X = np.empty((2 * N_SAMPLES_PER_CLASS, n, 3))
        for i in range(N_SAMPLES_PER_CLASS):
            X[i] = sphere_cloud(n, rng)
            X[N_SAMPLES_PER_CLASS + i] = torus_cloud(n, rng=rng)
        y = np.array([0] * N_SAMPLES_PER_CLASS + [1] * N_SAMPLES_PER_CLASS)
        xpath = SYNTH / f"sphere_torus_n{n}_X.npy"
        ypath = SYNTH / f"sphere_torus_n{n}_y.npy"
        np.save(xpath, X)
        np.save(ypath, y)
        out[n] = (str(xpath), str(ypath))
        print(f"  wrote sphere_torus_n{n}: {X.shape}")
    return out


FILS_TINY = [FiltrationConfig(name="sparse_rips", kwargs={"homology_dimensions": [0, 1]})]
FILS_1000 = [
    FiltrationConfig(name="sparse_rips", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
]
VECS = [
    VectorizationConfig(name="betti_curve", kwargs={"n_bins": 50}),
    VectorizationConfig(name="persistence_landscape", kwargs={"n_layers": 3, "n_bins": 50}),
]
CLFS = [
    ClassifierConfig(name="random_forest", kwargs={}),
    ClassifierConfig(name="svm_rbf", kwargs={}),
]


def finished_combos() -> set:
    if not Path(DB_PATH).exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT dataset,filtration,vectorizer,classifier FROM runs "
            "WHERE finished_at IS NOT NULL").fetchall()
    finally:
        conn.close()
    return set(rows)


def main() -> None:
    if Path(DB_PATH).exists():
        print(f"[resume] existing DB {DB_PATH} — skipping finished combos")
    clouds = make_large_clouds()
    ds_cache = {}
    jobs = []
    # n=1000: sparse_rips + vietoris_rips; n=3000: sparse_rips only (VR infeasible)
    for n, (xp, yp) in clouds.items():
        ds = DatasetConfig(name=f"sphere_torus_n{n}", path=xp, labels=yp,
                           modality="point_cloud",
                           description=f"synthetic sphere/torus n={n}")
        ds_cache[n] = ds
        fils = FILS_1000 if n == 1000 else FILS_TINY
        for fil, vec, clf in product(fils, VECS, CLFS):
            jobs.append((ds, fil, vec, clf))
    done = finished_combos()
    print(f"Total configs: {len(jobs)}; already finished: {len(done)}")
    t0 = time.time()
    ok = fail = skip = 0
    for i, (ds, fil, vec, clf) in enumerate(jobs, 1):
        key = (ds.name, fil.name, vec.name, clf.name)
        if key in done:
            skip += 1
            continue
        try:
            r = _run_one_worker(ds, fil, vec, clf, REP,
                                cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
                                db_path=DB_PATH, project_root=str(PROJECT_ROOT))
        except Exception as exc:  # noqa: BLE001
            fail += 1
            print(f"  EXC {key}: {type(exc).__name__}: {exc}")
            continue
        if r["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {key}: {r.get('error','')[:300]}")
        if i % 4 == 0 or ok + fail + skip == len(jobs):
            el = time.time() - t0
            print(f"[{ok+fail+skip}/{len(jobs)}] ok={ok} fail={fail} skip={skip} "
                  f"({el:.0f}s, {(ok+fail)/el if el else 0:.3f}/s)")
    print(f"COMPLETE: ok={ok} failed={fail} skipped={skip} ({time.time()-t0:.0f}s). "
          f"DB={DB_PATH}")


if __name__ == "__main__":
    main()
