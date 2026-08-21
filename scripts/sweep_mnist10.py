#!/usr/bin/env python3
"""Expansion A3 (#7a) — full 10-class MNIST under the paper protocol.

Direct test of Conti et al.'s 10-class MNIST case study at scale. Runs the
paper's OWN worker `_run_one_worker` (bit-identical preprocessing, same
factories, same StratifiedKFold(random_state=42+rep) splits) on the full
1000-sample / 10-class MNIST set (mnist10_1000_{X,y}.npy, 100 samples/class).

Design (per the approved expansion plan): cubical + vietoris_rips
(2 image-compatible filtrations) x betti_curve, persistence_image,
persistence_landscape, silhouette (4 vectorizers) x random_forest, logistic
(2 reliable classifiers; svm_rbf collapses to majority-class on TDA features
and is already disclosed) x 5 CV repetitions = 80 runs, 5-fold CV each.

SINGLE-CPU (user directive): serial loop, n_jobs=1, one run at a time, no
delegation. Resumable: skips any (fil,vec,clf,rep) already finished in the
target DB, so an interrupted sweep resumes without losing partial progress.

Additive-only: creates NEW DB data/tda/mnist10_sweep.db (refuses to
overwrite an existing one). No existing data or code is touched.

Usage (from AI_KOS_PROJECT root):
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_mnist10.py
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
import time
from itertools import product
from pathlib import Path

# ── importlib shim for the hyphenated repo dir (same as run_all.sh) ────────
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

PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "mnist10_sweep.db")

DS = DatasetConfig(
    name="mnist10",
    path="data/tda/images/mnist10_1000_X.npy",
    labels="data/tda/images/mnist10_1000_y.npy",
    modality="image",
    max_samples=1000,
    description="Full MNIST 10-class (0-9), 1000 samples (100/class), 28x28",
)

FILTRATIONS = [
    FiltrationConfig(name="cubical", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
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
REPETITIONS = 5  # CV seeds 43..47


def finished_combos() -> set:
    """Resumable: return {(fil,vec,clf,rep)} already written to the DB."""
    if not Path(DB_PATH).exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT filtration,vectorizer,classifier,repetition FROM runs "
            "WHERE finished_at IS NOT NULL").fetchall()
    finally:
        conn.close()
    return set(rows)


def main() -> None:
    # Resumable: if the DB already exists (partial progress), skip finished
    # combos; never overwrite or delete existing rows. A fresh DB starts clean.
    if Path(DB_PATH).exists():
        print(f"[resume] existing DB found: {DB_PATH} — skipping finished combos")
    jobs = [
        (DS, fil, vec, clf, rep)
        for fil, vec, clf in product(FILTRATIONS, VECTORIZATIONS, CLASSIFIERS)
        for rep in range(1, REPETITIONS + 1)
    ]
    done = finished_combos()
    print(f"Total combos: {len(jobs)} (2 fil x 4 vec x 2 clf x 5 reps), "
          f"already finished: {len(done)}")
    t0 = time.time()
    ok = fail = skip = 0
    for i, (ds, fil, vec, clf, rep) in enumerate(jobs, 1):
        key = (fil.name, vec.name, clf.name, rep)
        if key in done:
            skip += 1
            continue
        res = _run_one_worker(
            ds, fil, vec, clf, rep,
            cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
            db_path=DB_PATH, project_root=str(PROJECT_ROOT),
        )
        if res["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {res.get('label', key)}: {res.get('error','')[:300]}")
        if i % 10 == 0 or (ok + fail + skip) == len(jobs):
            el = time.time() - t0
            rate = (ok + fail) / el if el > 0 else 0
            print(f"[{i}/{len(jobs)}] done ok={ok} fail={fail} skip={skip} "
                  f"({el:.0f}s, {rate:.3f} runs/s)")
    print(f"COMPLETE: ok={ok} failed={fail} skipped={skip} "
          f"({time.time()-t0:.0f}s). DB={DB_PATH}")


if __name__ == "__main__":
    main()
