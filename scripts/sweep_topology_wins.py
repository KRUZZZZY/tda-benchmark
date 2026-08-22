#!/usr/bin/env python3
"""Expansion #6 — TOPOLOGY-WINS REGIME: full stage decomposition on
topology-heavy datasets (novelty candidate).

Everything measured so far sits in a regime where TDA loses to raw
baselines, so stage importance is measured where topological features
are decorative. This sweep runs the SAME stage decomposition on datasets
where topology is known to carry the signal:

  * dyn_lorenz_rossler  — Lorenz vs Roessler Takens reconstructions
    (scripts/generate_dynamical_systems.py; H1 structure of the strange
    attractors; 120 samples, ~498-pt clouds -> subsample_points=100)
  * dyn_doublewell      — double-well vs single-well Langevin trajectories
    (persistent H0 pair of the two metastable wells; 120 samples)
  * dyn_circle_torus    — noisy circle vs torus clouds, sigma=0.45
    (1 vs 2 H1 generators; 160 samples, 300-pt clouds -> subsample=100)
  * outex               — Outex_TC_00000 textures OR synthetic texture
    proxy (scripts/download_outex.py; image modality, 64x64; NOTE the
    repo's documented VR-on-image semantics apply: the worker passes
    (n, 64, 64) raw images to VietorisRipsPersistence, i.e. the image
    ROWS are the points — same executed protocol as the paper's MNIST arm)
  * modelnet10 / shapes_proxy — ModelNet10 point clouds OR the 5-primitive
    proxy (scripts/download_modelnet.py; 500-pt clouds -> subsample=100)

Grid (per the approved expansion plan): filtrations
{vietoris_rips, weighted_rips(weights="DTM")} x vectorizers
{betti_curve, persistence_image, persistence_landscape,
persistence_entropy} x classifiers {random_forest, svm_rbf},
5-fold CV seed 42 rep=1 => 5 datasets x 16 configs = 80 runs.

The interesting read-out is whether the dominant stage CHANGES when
topology matters (i.e. filtration's marginal range stops being ~0).

SINGLE-CPU (user directive): serial loop, n_jobs=1, resumable (finished
(ds,fil,vec,clf) combos are skipped). DO NOT RUN while
scripts/sweep_large_n.py is live — B5 owns the CPU (documented; no lock
is implemented).

Additive-only: creates NEW DB data/tda/topology_wins_sweep.db and (via
the generators/downloaders) new arrays under data/tda/. No existing
files are touched.

Prerequisites (run once each, in this order):
  .venv-tda/bin/python projects/tda-benchmark/scripts/generate_dynamical_systems.py
  .venv-tda/bin/python projects/tda-benchmark/scripts/download_outex.py
  .venv-tda/bin/python projects/tda-benchmark/scripts/download_modelnet.py

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_topology_wins.py

Expected runtime: 3-8 h serial (weighted_rips/DTM dominates; 80 configs).
DB: ../../data/tda/topology_wins_sweep.db
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
import time
from itertools import product
from pathlib import Path

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
DATA_TDA = PROJECT_ROOT / "data" / "tda"
DB_PATH = str(DATA_TDA / "topology_wins_sweep.db")

CV_FOLDS = 5
RANDOM_SEED = 42
REPETITIONS = 1

SYN = DATA_TDA / "synthetic"
IMG = DATA_TDA / "images"
SHP = DATA_TDA / "shapes"

# dataset -> (path, labels) relative to PROJECT_ROOT (as in the verified
# sweep_multidataset.py pattern)
REQUIRED = [
    ("dyn_lorenz_rossler", SYN / "dyn_lorenz_rossler_X.npy", SYN / "dyn_lorenz_rossler_y.npy"),
    ("dyn_doublewell", SYN / "dyn_doublewell_X.npy", SYN / "dyn_doublewell_y.npy"),
    ("dyn_circle_torus", SYN / "dyn_circle_torus_X.npy", SYN / "dyn_circle_torus_y.npy"),
    ("outex", IMG / "outex_64x64_X.npy", IMG / "outex_64x64_y.npy"),
    ("modelnet10", SHP / "modelnet10_X.npy", SHP / "modelnet10_y.npy"),
    ("shapes_proxy", SHP / "shapes_proxy_X.npy", SHP / "shapes_proxy_y.npy"),
]


def build_datasets() -> list[DatasetConfig]:
    """Point-cloud datasets with subsample_points=100 (repo VR budget).

    modelnet10 is preferred over shapes_proxy; outex is the image arm.
    """
    ds = [
        DatasetConfig(name="dyn_lorenz_rossler",
                      path="data/tda/synthetic/dyn_lorenz_rossler_X.npy",
                      labels="data/tda/synthetic/dyn_lorenz_rossler_y.npy",
                      modality="point_cloud", subsample_points=100,
                      description="Lorenz vs Roessler Takens reconstructions"),
        DatasetConfig(name="dyn_doublewell",
                      path="data/tda/synthetic/dyn_doublewell_X.npy",
                      labels="data/tda/synthetic/dyn_doublewell_y.npy",
                      modality="point_cloud", subsample_points=100,
                      description="double-well vs single-well Langevin trajectories"),
        DatasetConfig(name="dyn_circle_torus",
                      path="data/tda/synthetic/dyn_circle_torus_X.npy",
                      labels="data/tda/synthetic/dyn_circle_torus_y.npy",
                      modality="point_cloud", subsample_points=100,
                      description="noisy circle vs torus clouds (sigma=0.45)"),
        DatasetConfig(name="outex",
                      path="data/tda/images/outex_64x64_X.npy",
                      labels="data/tda/images/outex_64x64_y.npy",
                      modality="image",
                      description="Outex_TC_00000 (or synthetic texture proxy), 64x64"),
    ]
    if (SHP / "modelnet10_X.npy").exists():
        ds.append(DatasetConfig(
            name="modelnet10",
            path="data/tda/shapes/modelnet10_X.npy",
            labels="data/tda/shapes/modelnet10_y.npy",
            modality="point_cloud", subsample_points=100,
            description="ModelNet10 sampled point clouds, 10 classes"))
        print("[data] using REAL ModelNet10 arrays")
    else:
        ds.append(DatasetConfig(
            name="shapes_proxy",
            path="data/tda/shapes/shapes_proxy_X.npy",
            labels="data/tda/shapes/shapes_proxy_y.npy",
            modality="point_cloud", subsample_points=100,
            description="synthetic shape proxy (5 primitives), 40/class"))
        print("[data] ModelNet10 unavailable -> using synthetic shape proxy")
    return ds


FILTRATIONS = [
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="weighted_rips", kwargs={"homology_dimensions": [0, 1]}),
]

VECTORIZATIONS = [
    VectorizationConfig(name="betti_curve", kwargs={"n_bins": 50}),
    VectorizationConfig(name="persistence_image", kwargs={"sigma": 0.1, "n_bins": 20}),
    VectorizationConfig(name="persistence_landscape", kwargs={"n_layers": 3, "n_bins": 50}),
    VectorizationConfig(name="persistence_entropy", kwargs={"normalize": True}),
]

CLASSIFIERS = [
    ClassifierConfig(name="random_forest", kwargs={}),
    ClassifierConfig(name="svm_rbf", kwargs={}),
]


def check_data() -> bool:
    missing = []
    for name, path, _labels in REQUIRED:
        if name == "modelnet10" and not path.exists():
            continue  # proxy is the fallback; only one of the pair is needed
        if name == "shapes_proxy" and (SHP / "modelnet10_X.npy").exists():
            continue  # real data present; proxy not needed
        if not path.exists():
            missing.append((name, path))
    if missing:
        print("MISSING required arrays — run the generators/downloaders first:")
        for name, path in missing:
            print(f"  - {name}: {path}")
        print("  .venv-tda/bin/python projects/tda-benchmark/scripts/"
              "generate_dynamical_systems.py")
        print("  .venv-tda/bin/python projects/tda-benchmark/scripts/"
              "download_outex.py")
        print("  .venv-tda/bin/python projects/tda-benchmark/scripts/"
              "download_modelnet.py")
        return False
    return True


def finished_combos() -> set:
    if not Path(DB_PATH).exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT dataset,filtration,vectorizer,classifier,repetition "
            "FROM runs WHERE finished_at IS NOT NULL").fetchall()
    finally:
        conn.close()
    return set(rows)


def main() -> None:
    if not check_data():
        sys.exit(1)
    datasets = build_datasets()
    if Path(DB_PATH).exists():
        print(f"[resume] existing DB: {DB_PATH} — skipping finished combos")
    jobs = [
        (ds, fil, vec, clf, rep)
        for ds in datasets
        for fil, vec, clf in product(FILTRATIONS, VECTORIZATIONS, CLASSIFIERS)
        for rep in range(1, REPETITIONS + 1)
    ]
    done = finished_combos()
    print(f"Total configs: {len(jobs)} "
          f"({len(datasets)} datasets x 2 fil x 4 vec x 2 clf x "
          f"{REPETITIONS} rep), already finished: {len(done)}")
    print(f"DB: {DB_PATH}")
    t0 = time.time()
    ok = fail = skip = 0
    for i, (ds, fil, vec, clf, rep) in enumerate(jobs, 1):
        key = (ds.name, fil.name, vec.name, clf.name, rep)
        if key in done:
            skip += 1
            continue
        try:
            res = _run_one_worker(
                ds, fil, vec, clf, rep,
                cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
                db_path=DB_PATH, project_root=str(PROJECT_ROOT),
            )
        except Exception as exc:  # noqa: BLE001
            fail += 1
            print(f"  EXC {key}: {type(exc).__name__}: {exc}")
            continue
        if res["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {key}: {res.get('error', '')[:300]}")
        if i % 8 == 0 or ok + fail + skip == len(jobs):
            el = time.time() - t0
            print(f"[{ok+fail+skip}/{len(jobs)}] ok={ok} fail={fail} "
                  f"skip={skip} ({el:.0f}s, "
                  f"{(ok+fail)/el if el else 0:.3f}/s)")
    print(f"COMPLETE: ok={ok} failed={fail} skipped={skip} "
          f"({time.time()-t0:.0f}s). DB={DB_PATH}")


if __name__ == "__main__":
    main()
