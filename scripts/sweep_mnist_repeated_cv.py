#!/usr/bin/env python3
"""Reviewer-revision sweep A3: MNIST 0/1 repeated 5-fold CV (5 repetitions).

Addresses the paper's statistical-experiment fixes:
  * A3: repeated CV on MNIST 0/1 to settle whether the vectorizer > filtration
    marginal-range asymmetry on images is real (vs the single-split bootstrap
    CIs [2.00, 6.14] vec vs [0.74, 2.69] fil).
  56 configs (2 filtrations cubical + vietoris_rips x 7 vectorizers x 4
  classifiers) x 5 reps = 280 runs, 5-fold CV each (CV seeds 43..47).

Protocol fidelity: reuses the repo's OWN worker `_run_one_worker` for
bit-identical preprocessing (max_samples=400 cap, same factories, same
StratifiedKFold(random_state=42+rep) splits). Rep 1 reproduces the MNIST rows
of expanded_results.db exactly.

Additive-only: creates NEW DB data/tda/mnist_repeated_cv.db.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_mnist_repeated_cv.py
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
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "mnist_repeated_cv.db")
N_JOBS = 5

DS = DatasetConfig(
    name="mnist_01",
    path="data/tda/images/mnist_01_X.npy",
    labels="data/tda/images/mnist_01_y.npy",
    modality="image",
    max_samples=400,
    description="MNIST binary (0 vs 1) — 200 per class, 28×28 greyscale",
)

# only the two image-compatible filtrations (weak_alpha/sparse_rips fail on
# image data in the expanded sweep — excluded there and here)
FILTRATIONS = [
    FiltrationConfig(name="cubical", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
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
REPETITIONS = 5  # CV seeds 43..47


def main() -> None:
    if Path(DB_PATH).exists():
        raise SystemExit(f"Refusing to overwrite existing DB: {DB_PATH}")
    jobs = [
        (DS, fil, vec, clf, rep)
        for fil, vec, clf in product(FILTRATIONS, VECTORIZATIONS, CLASSIFIERS)
        for rep in range(1, REPETITIONS + 1)
    ]
    print(f"Total runs: {len(jobs)} (56 configs x 5 reps), n_jobs={N_JOBS}")
    print(f"DB: {DB_PATH}")
    from joblib import Parallel, delayed
    results = Parallel(n_jobs=N_JOBS, backend="loky", verbose=5)(
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
