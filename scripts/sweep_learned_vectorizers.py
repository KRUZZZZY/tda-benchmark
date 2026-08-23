#!/usr/bin/env python3
"""#8 — Learned-vectorizer sweep driver (PersLay / Hofer deep-set stubs).

DO NOT RUN in the stock .venv-tda: the two learned vectorizers (perslay,
hofer_deepset) require torch (+ perslay). This driver checks for torch at
startup and exits with the install instructions if it is missing.

Grid (small subset, 16 runs total, serial n_jobs=1 — single-CPU rule):
  * datasets: ecg200 (Takens d=3 tau=1) and sphere_torus_noise0 (point cloud)
  * filtrations: vietoris_rips, weak_alpha   (both point-cloud compatible)
  * vectorizers: perslay, hofer_deepset      (the #8 factory entries)
  * classifiers: random_forest, svm_rbf
  * 5-fold CV, random_seed 42, repetition 1 (folds = seed 43, identical to
    the 616-config sweep protocol)
Runs through the repo's own `_run_one_worker` (bit-identical preprocessing,
Takens embedding, factory pipeline, ResultStore) into a NEW DB:
data/tda/learned_vectorizers_sweep.db.

Runtime: 2-4 h AFTER torch is installed (trainable layers run on CPU inside
each worker; expect the two datasets x 8 configs each to dominate the same
way the r25 ECG200 sweep did). The driver is RESUMABLE: on restart it skips
(dataset, filtration, vectorizer, classifier) combos already finished in the
target DB (see the `finished_combos` helper).

Env preparation (documented, NOT performed here — additive-only):
  python3 -m venv /home/kruzzzzy/Documents/AI_KOS_PROJECT/.venv-perslay
  source /home/kruzzzzy/Documents/AI_KOS_PROJECT/.venv-perslay/bin/activate
  pip install torch --index-url https://download.pytorch.org/whl/cpu
  pip install perslay
  pip install giotto-tda ripser gudhi scikit-learn==1.3.2 statsmodels
  # import smoke test: see requirements-learned.md (repo root)
Use the SEPARATE .venv-perslay (NOT .venv-tda) so the sklearn 1.3.2 pin that
giotto-tda 0.6.2 requires is never upgraded by the torch/perslay installs.

Usage (AFTER the env prep above):
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-perslay/bin/python projects/tda-benchmark/scripts/sweep_learned_vectorizers.py

Additive-only: creates only this script + the new DB. No existing files
touched; the result DBs it reads are only checked for resume state.
"""

from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
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

PROJECT_ROOT = REPO.parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "learned_vectorizers_sweep.db")

CV_FOLDS = 5
RANDOM_SEED = 42
REP = 1

INSTALL_HINT = (
    "\nThe learned vectorizers need torch (and perslay). Install into the "
    "SEPARATE .venv-perslay (protects the sklearn 1.3.2 pin):\n"
    "  python3 -m venv ~/Documents/AI_KOS_PROJECT/.venv-perslay\n"
    "  source ~/Documents/AI_KOS_PROJECT/.venv-perslay/bin/activate\n"
    "  pip install torch --index-url https://download.pytorch.org/whl/cpu\n"
    "  pip install perslay\n"
    "  pip install giotto-tda ripser gudhi scikit-learn==1.3.2 statsmodels\n"
    "Full recipe + import smoke test: requirements-learned.md (repo root).\n"
)

DATASETS = [
    DatasetConfig(name="ecg200", path="data/tda/ucr/ecg200_X.npy",
                  labels="data/tda/ucr/ecg200_y.npy", modality="time_series",
                  takens_dimension=3, takens_delay=1),
    DatasetConfig(name="sphere_torus_noise0",
                  path="data/tda/synthetic/sphere_torus_noise0_X.npy",
                  labels="data/tda/synthetic/sphere_torus_noise0_y.npy",
                  modality="point_cloud"),
]
FILTRATIONS = [
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="weak_alpha", kwargs={"homology_dimensions": [0, 1]}),
]
VECTORIZERS = [
    # default hidden_dim/out_dim match the factory stubs; both are untrained
    # in this revision — the sweep exercises pipeline mechanics + the lazy
    # torch path end-to-end.
    VectorizationConfig(name="perslay", kwargs={"hidden_dim": 32, "out_dim": 16}),
    VectorizationConfig(name="hofer_deepset", kwargs={"hidden_dim": 32, "out_dim": 16}),
]
CLASSIFIERS = [
    ClassifierConfig(name="random_forest", kwargs={}),
    ClassifierConfig(name="svm_rbf", kwargs={}),
]


def finished_combos() -> set[tuple[str, str, str, str]]:
    """Resume state: (dataset, filtration, vectorizer, classifier) done."""
    if not Path(DB_PATH).exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    rows = conn.execute(
        "SELECT dataset, filtration, vectorizer, classifier FROM runs "
        "WHERE finished_at IS NOT NULL").fetchall()
    conn.close()
    return {tuple(r) for r in rows}


def main() -> None:
    if importlib.util.find_spec("torch") is None:
        print("torch is NOT installed — this driver cannot run yet." + INSTALL_HINT)
        sys.exit(1)

    jobs = [(ds, fil, vec, clf)
            for ds, fil, vec, clf in product(DATASETS, FILTRATIONS,
                                             VECTORIZERS, CLASSIFIERS)]
    print(f"Planned runs: {len(jobs)} ({len(DATASETS)} datasets x "
          f"{len(FILTRATIONS)} filtrations x {len(VECTORIZERS)} vectorizers "
          f"x {len(CLASSIFIERS)} classifiers x {REP} rep)")
    print(f"DB: {DB_PATH}")

    done = finished_combos()
    todo = [j for j in jobs if (j[0].name, j[1].name, j[2].name, j[3].name) not in done]
    print(f"Resume: {len(done)} combos already finished, "
          f"{len(todo)} to run")

    ok = fail = 0
    import time
    t0 = time.perf_counter()
    for i, (ds, fil, vec, clf) in enumerate(todo, 1):
        r = _run_one_worker(ds, fil, vec, clf, REP,
                            cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
                            db_path=DB_PATH, project_root=str(PROJECT_ROOT))
        if r["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"[{i}/{len(todo)}] FAIL {ds.name}/{fil.name}/{vec.name}/"
                  f"{clf.name}: {str(r.get('error', ''))[:200]}")
        if i % 4 == 0 or i == len(todo):
            el = time.perf_counter() - t0
            rate = i / el
            print(f"[{i}/{len(todo)}] {ok} ok {fail} fail | {rate:.4f} runs/s | "
                  f"~{(len(todo) - i) / rate / 60:.0f} min remaining")
    print(f"\nDone in {time.perf_counter() - t0:.0f}s: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
