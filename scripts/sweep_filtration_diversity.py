#!/usr/bin/env python3
"""Expansion B1 (#1) — diverse filtrations sweep.

The paper's 3 of 4 filtrations (Vietoris-Rips, weak Alpha, Sparse Rips)
approximate the same Rips-type geometry, so "filtration barely matters"
is partly baked in. This sweep adds a genuinely different filtration —
the DTM-weighted Rips (gtda WeightedRipsPersistence, weights="DTM",
Anai et al. "DTM-based filtrations"), which weights vertices/edges by a
distance-to-measure estimate and is robust to outliers — and re-measures
the stage ranges alongside the Rips-type baseline.

Design (per the approved expansion plan): ECG200 (Takens d=3 tau=1) +
sphere/torus (noise0, noise30) point clouds x {vietoris_rips,
weighted_rips/DTM} x {betti_curve, persistence_image,
persistence_landscape, silhouette} x {random_forest, svm_rbf}, 5-fold CV
single split (seed 43), 1 repetition = 48 configs.

SINGLE-CPU (user directive): serial loop, n_jobs=1, one run at a time, no
delegation. Resumable: any (ds,fil,vec,clf) already finished is skipped.

Additive-only: creates NEW DB data/tda/filtration_diversity_sweep.db (does
not overwrite existing data). No existing DBs/datasets/code touched.

Usage (from AI_KOS_PROJECT root):
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_filtration_diversity.py
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
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "filtration_diversity_sweep.db")

DATASETS = [
    DatasetConfig(
        name="ecg200",
        path="data/tda/ucr/ecg200_X.npy",
        labels="data/tda/ucr/ecg200_y.npy",
        modality="time_series",
        takens_dimension=3,
        takens_delay=1,
        description="ECG200 (UCR) Takens-embedded d=3 tau=1",
    ),
    DatasetConfig(
        name="sphere_torus_n0",
        path="data/tda/synthetic/sphere_torus_noise0_X.npy",
        labels="data/tda/synthetic/sphere_torus_noise0_y.npy",
        modality="point_cloud",
        description="Synthetic sphere/torus, sigma=0.00, 100 pts",
    ),
    DatasetConfig(
        name="sphere_torus_n30",
        path="data/tda/synthetic/sphere_torus_noise30_X.npy",
        labels="data/tda/synthetic/sphere_torus_noise30_y.npy",
        modality="point_cloud",
        description="Synthetic sphere/torus, sigma=0.30, 100 pts",
    ),
]

# Rips-type baseline (in the paper) vs genuinely-diverse DTM-weighted Rips.
FILTRATIONS = [
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="weighted_rips", kwargs={"homology_dimensions": [0, 1]}),
]

VECTORIZATIONS = [
    VectorizationConfig(name="betti_curve", kwargs={"n_bins": 50}),
    VectorizationConfig(name="persistence_image", kwargs={"sigma": 0.1, "n_bins": 20}),
    VectorizationConfig(name="persistence_landscape", kwargs={"n_layers": 3, "n_bins": 50}),
    VectorizationConfig(name="silhouette", kwargs={"n_bins": 50}),
]

CLASSIFIERS = [
    ClassifierConfig(name="random_forest", kwargs={}),
    ClassifierConfig(name="svm_rbf", kwargs={}),
]

CV_FOLDS = 5
RANDOM_SEED = 42
REPETITIONS = 1  # single split (seed 43); Phase 3 adds repeated CV


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
    if Path(DB_PATH).exists():
        print(f"[resume] existing DB: {DB_PATH} — skipping finished combos")
    jobs = [
        (ds, fil, vec, clf, rep)
        for ds in DATASETS
        for fil, vec, clf in product(FILTRATIONS, VECTORIZATIONS, CLASSIFIERS)
        for rep in range(1, REPETITIONS + 1)
    ]
    done = finished_combos()
    print(f"Total configs: {len(jobs)} (3 datasets x 2 fil x 4 vec x 2 clf x "
          f"{REPETITIONS} rep), already finished: {len(done)}")
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
            print(f"  FAIL {key}: {res.get('error','')[:300]}")
        if i % 6 == 0 or ok + fail + skip == len(jobs):
            el = time.time() - t0
            print(f"[{ok+fail+skip}/{len(jobs)}] ok={ok} fail={fail} "
                  f"skip={skip} ({el:.0f}s, {(ok+fail)/el if el else 0:.3f}/s)")
    print(f"COMPLETE: ok={ok} failed={fail} skipped={skip} "
          f"({time.time()-t0:.0f}s). DB={DB_PATH}")


if __name__ == "__main__":
    main()
