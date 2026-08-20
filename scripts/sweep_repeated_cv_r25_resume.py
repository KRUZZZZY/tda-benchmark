#!/usr/bin/env python3
"""A1 resume driver — serial continuation of the r=25 repeated-CV sweep.

The parallel sweep (sweep_repeated_cv_r25.py) was stopped at 219/2100 runs by
user directive (single-CPU, one-sim-at-a-time, no delegation). This driver
resumes it SERIALLY (n_jobs=1): it discovers which (config, repetition) cells
already have completed runs in data/tda/repeated_cv_r25.db and runs ONLY the
missing cells through the repo's own `_run_one_worker` (bit-identical
preprocessing, CV seeds 43..67, normalized schema, append-only writes).

Additive-only: appends to the existing repeated_cv_r25.db; never touches
expanded_results.db or any other DB/dataset/committed code.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_repeated_cv_r25_resume.py
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
PKG_DIR = str(REPO)
sys.path.insert(0, str(REPO.parent))
if "tda_benchmark" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark", os.path.join(PKG_DIR, "__init__.py"),
        submodule_search_locations=[PKG_DIR])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)

from tda_benchmark.config import (  # noqa: E402
    ClassifierConfig, DatasetConfig, FiltrationConfig, VectorizationConfig,
)
from tda_benchmark.runner import _run_one_worker  # noqa: E402

PROJECT_ROOT = REPO.parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "repeated_cv_r25.db")

DS = DatasetConfig(
    name="ecg200",
    path="data/tda/ucr/ecg200_X.npy",
    labels="data/tda/ucr/ecg200_y.npy",
    modality="time_series",
    takens_dimension=3,
    takens_delay=1,
)
FILTRATIONS = [
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="weak_alpha", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="cubical", kwargs={"homology_dimensions": [0, 1]}),
]
VECTORIZATIONS = [
    VectorizationConfig(name="persistence_image", kwargs={"sigma": 0.1, "n_bins": 20}),
    VectorizationConfig(name="persistence_landscape", kwargs={"n_layers": 3, "n_bins": 50}),
    VectorizationConfig(name="betti_curve", kwargs={"n_bins": 50}),
    VectorizationConfig(name="silhouette", kwargs={"n_bins": 50}),
    VectorizationConfig(name="persistence_entropy", kwargs={"normalize": True}),
    VectorizationConfig(name="amplitude", kwargs={"metric": "bottleneck"}),
    VectorizationConfig(name="persistence_statistics", kwargs={}),
]
CLASSIFIERS = [
    ClassifierConfig(name="svm_rbf", kwargs={}),
    ClassifierConfig(name="random_forest", kwargs={}),
    ClassifierConfig(name="logistic", kwargs={}),
    ClassifierConfig(name="svm_linear", kwargs={}),
]
CV_FOLDS = 5
RANDOM_SEED = 42
REPETITIONS = 25  # CV seeds 43..67


def done_cells() -> set[tuple[str, str, str, int]]:
    """(filtration, vectorizer, classifier, repetition) cells already in DB."""
    conn = sqlite3.connect(DB_PATH)
    cells = set(conn.execute(
        "SELECT filtration, vectorizer, classifier, repetition FROM runs "
        "WHERE finished_at IS NOT NULL").fetchall())
    conn.close()
    return cells


def main() -> None:
    done = done_cells()
    jobs = [
        (DS, fil, vec, clf, rep)
        for fil, vec, clf in product(FILTRATIONS, VECTORIZATIONS, CLASSIFIERS)
        for rep in range(1, REPETITIONS + 1)
        if (fil.name, vec.name, clf.name, rep) not in done
    ]
    total = len(FILTRATIONS) * len(VECTORIZATIONS) * len(CLASSIFIERS) * REPETITIONS
    print(f"Total cells: {total}; already done: {len(done)}; to run (serial): {len(jobs)}")
    if not jobs:
        print("Nothing to do.")
        return

    ok = fail = 0
    t0 = time.perf_counter()
    for i, (ds, fil, vec, clf, rep) in enumerate(jobs, 1):
        r = _run_one_worker(
            ds, fil, vec, clf, rep,
            cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
            db_path=DB_PATH, project_root=str(PROJECT_ROOT),
        )
        if r["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"[{i}/{len(jobs)}] FAIL {fil.name}/{vec.name}/{clf.name} rep{rep}: "
                  f"{str(r.get('error', ''))[:300]}")
        if i % 50 == 0 or i == len(jobs):
            el = time.perf_counter() - t0
            rate = i / el if el > 0 else 0
            remain = (len(jobs) - i) / rate / 60 if rate > 0 else float("nan")
            print(f"[{i}/{len(jobs)}] {ok} ok {fail} fail | {rate:.2f} runs/s | "
                  f"~{remain:.0f} min remaining")
    print(f"\nResume done in {time.perf_counter()-t0:.0f}s: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
