#!/usr/bin/env python3
"""Reviewer-revision sweep A1: ECG200 repeated 5-fold CV with 25 repetitions.

Addresses the paper's statistical-experiment fixes:
  * A1: repeated CV with 25 repetitions (not 5) to tighten the stage-marginal
    range CIs and test ordering stability.
  * sparse_rips is DROPPED (mean ~15.7 s/run vs ~2.3 s for the other three
    filtrations) => 3 filtrations x 7 vectorizers x 4 classifiers = 84 configs
    x 25 reps = 2100 runs, 5-fold CV each.

Protocol fidelity (bit-identical to the paper's executed sweep): this driver
reuses the repo's OWN worker `tda_benchmark.runner._run_one_worker`, which
performs the exact executed pipeline (Takens embedding for time_series,
FiltrationFactory/VectorizationFactory/ClassifierFactory construction,
StratifiedKFold(random_state=random_seed + rep) with random_seed=42,
repetition 1..25 => actual CV seeds 43..67, SQLite storage in the same
normalized schema). Reps 1..5 reproduce the existing repeated_cv.db exactly.

Additive-only: creates NEW DB data/tda/repeated_cv_r25.db. Existing DBs,
datasets and committed code are untouched.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_repeated_cv_r25.py
"""

from __future__ import annotations

import importlib.util
import os
import sys
from itertools import product
from pathlib import Path

# ── importlib shim for the hyphenated repo dir (same as run_all.sh) ────────
REPO = Path(__file__).resolve().parent.parent
PKG_DIR = str(REPO)
# symlink projects/tda_benchmark -> tda-benchmark lets loky workers import the
# package by name when pickling dataclass/function args (workers do NOT inherit
# sys.modules, only sys.path)
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

PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "repeated_cv_r25.db")
N_JOBS = 5  # other agents run sweeps concurrently; cap <= 6

DS = DatasetConfig(
    name="ecg200",
    path="data/tda/ucr/ecg200_X.npy",
    labels="data/tda/ucr/ecg200_y.npy",
    modality="time_series",
    takens_dimension=3,
    takens_delay=1,
)

# sparse_rips deliberately dropped (15.7 s/run mean; 84 configs x 25 reps = 2100 runs)
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


def existing_finished(db_path: str) -> set[tuple]:
    """Return {(filtration, vectorizer, classifier, repetition)} already in DB."""
    import sqlite3
    conn = sqlite3.connect(db_path)
    rows = conn.execute(
        "SELECT filtration, vectorizer, classifier, repetition FROM runs "
        "WHERE finished_at IS NOT NULL").fetchall()
    conn.close()
    return set(rows)


def main() -> None:
    n_jobs = int(os.environ.get("SWEEP_N_JOBS", str(N_JOBS)))
    resume = Path(DB_PATH).exists()
    done = existing_finished(DB_PATH) if resume else set()
    jobs = [
        (DS, fil, vec, clf, rep)
        for fil, vec, clf in product(FILTRATIONS, VECTORIZATIONS, CLASSIFIERS)
        for rep in range(1, REPETITIONS + 1)
        if (fil.name, vec.name, clf.name, rep) not in done
    ]
    print(f"Total runs: {len(jobs) + len(done)} (84 configs x 25 reps), "
          f"n_jobs={n_jobs}, resume={resume} ({len(done)} already finished)")
    print(f"DB: {DB_PATH}")
    if not jobs:
        print("nothing to do — all runs finished")
        return
    from joblib import Parallel, delayed
    results = Parallel(n_jobs=n_jobs, backend="loky", verbose=5)(
        delayed(_run_one_worker)(
            ds, fil, vec, clf, rep,
            cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
            db_path=DB_PATH, project_root=str(PROJECT_ROOT),
        )
        for ds, fil, vec, clf, rep in jobs
    )
    ok = sum(1 for r in results if r["status"] == "ok")
    failed = sum(1 for r in results if r["status"] != "ok")
    print(f"done: {ok} ok, {failed} failed")
    if failed:
        for r in results:
            if r["status"] != "ok":
                print(r["label"], r.get("error", "")[:500])


if __name__ == "__main__":
    main()
