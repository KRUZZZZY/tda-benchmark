#!/usr/bin/env python3
"""Expansion B3 (#10) — hyperparameter-sensitivity arm.

Question: does VECTORIZER dominance survive when each vectorizer's key
hyperparameter is tuned per dataset, or is the vectorizer marginal range a
default-settings artefact?

Design: for the paper's two headline datasets (ECG200 time_series via Takens
d=3/tau=1 -> vietoris_rips; binary MNIST image via cubical), sweep each of the
4 vectorizers' key hyperparameter over a small one-parameter-at-a-time grid,
holding the OTHER vectorizer params at the paper default. Classifiers:
{random_forest, svm_rbf}. CV = 5-fold, StratifiedKFold(random_state=42+rep),
rep=1, single split.

Vectorizer grids (one param at a time; others at paper default):
  persistence_image      sigma   in {0.05, 0.1, 0.2, 0.5} (n_bins=20)
                         n_bins  in {10, 20, 50}          (sigma=0.1)
  persistence_landscape  n_layers in {1, 3, 5}             (n_bins=50)
                         n_bins  in {20, 50, 100}          (n_layers=3)
  silhouette             n_bins  in {10, 20, 50, 100}
  betti_curve            n_bins  in {10, 20, 50, 100}

Paper defaults (also cells of the grid): PI {sigma:0.1,n_bins:20},
landscape {n_layers:3,n_bins:50}, silhouette {n_bins:50}, betti {n_bins:50}.

SINGLE-CPU (user directive): serial loop through the repo's own worker
`_run_one_worker`, n_jobs=1, no parallel fan-out, no delegation — exactly
sweep_mnist10.py's loop. Resumable: skips any (dataset, fil, vec, clf, rep,
vec_kwargs) already finished in the target DB.

Additive-only: creates NEW DB data/tda/hyperparam_sweep.db (refuses to
overwrite an existing one). No existing data, DB, or code is modified.

Usage (from AI_KOS_PROJECT root):
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_hyperparam.py
"""
from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
import time
from itertools import product
from pathlib import Path

# ── importlib shim for the hyphenated repo dir (same as sweep_mnist10.py) ──
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
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "hyperparam_sweep.db")

# ── Datasets (mirror expanded_config.yaml) ──────────────────────────────────
ECG200 = DatasetConfig(
    name="ecg200",
    path="data/tda/ucr/ecg200_X.npy",
    labels="data/tda/ucr/ecg200_y.npy",
    modality="time_series",
    takens_dimension=3,
    takens_delay=1,
    description="ECG200 UCR time series, Takens d=3 tau=1 -> vietoris_rips",
)
MNIST = DatasetConfig(
    name="mnist_01",
    path="data/tda/images/mnist_01_X.npy",
    labels="data/tda/images/mnist_01_y.npy",
    modality="image",
    max_samples=400,
    description="MNIST binary (0 vs 1) — 200 per class, 28x28 greyscale",
)

# ── Functional image (time_series) filtration per dataset ───────────────────
FIL_BY_DS = {
    "ecg200": FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    "mnist_01": FiltrationConfig(name="cubical", kwargs={"homology_dimensions": [0, 1]}),
}

# ── Vectorizer hyperparameter grids ─────────────────────────────────────────
PAPER_DEFAULTS = {
    "persistence_image": {"sigma": 0.1, "n_bins": 20},
    "persistence_landscape": {"n_layers": 3, "n_bins": 50},
    "silhouette": {"n_bins": 50},
    "betti_curve": {"n_bins": 50},
}

PI_BASE = {"n_bins": 20}
LAND_BASE = {"n_bins": 50}


def vectorizer_variants() -> list[tuple[str, dict]]:
    """Return [(vec_name, kwargs)] — one-param-at-a-time grids, deduplicated."""
    base = PAPER_DEFAULTS
    variants: list[tuple[str, dict]] = []

    for kwargs in (
        {"sigma": s, "n_bins": PI_BASE["n_bins"]} for s in (0.05, 0.1, 0.2, 0.5)
    ):
        variants.append(("persistence_image", dict(kwargs)))
    for n in (10, 20, 50):
        kwargs = {"sigma": base["persistence_image"]["sigma"], "n_bins": n}
        variants.append(("persistence_image", dict(kwargs)))

    for L in (1, 3, 5):
        variants.append(("persistence_landscape", {"n_layers": L, "n_bins": LAND_BASE["n_bins"]}))
    for n in (20, 50, 100):
        variants.append(("persistence_landscape", {"n_layers": base["persistence_landscape"]["n_layers"], "n_bins": n}))

    for n in (10, 20, 50, 100):
        variants.append(("silhouette", {"n_bins": n}))
    for n in (10, 20, 50, 100):
        variants.append(("betti_curve", {"n_bins": n}))

    # Deduplicate (grids overlap at the paper defaults).
    seen: set[tuple[str, str]] = set()
    out: list[tuple[str, dict]] = []
    for name, kwargs in variants:
        sig = (name, json.dumps(kwargs, sort_keys=True))
        if sig in seen:
            continue
        seen.add(sig)
        out.append((name, kwargs))
    return out


CLASSIFIERS = [ClassifierConfig(name="random_forest", kwargs={}),
               ClassifierConfig(name="svm_rbf", kwargs={})]

CV_FOLDS = 5
RANDOM_SEED = 42
REPETITION = 1


def vec_kwargs_json(kwargs: dict) -> str:
    return json.dumps(kwargs, sort_keys=True)


def finished_combos() -> set[tuple]:
    """Resumable: {(dataset, fil, vec, clf, rep, vec_kwargs_json)} in the DB."""
    if not Path(DB_PATH).exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT r.dataset, r.filtration, r.vectorizer, r.classifier, "
            "r.repetition, m.pipeline_params FROM runs r "
            "JOIN run_metadata m ON r.run_id = m.run_id "
            "WHERE r.finished_at IS NOT NULL").fetchall()
    finally:
        conn.close()
    combos = set()
    for dataset, fil, vec_name, clf_name, rep, pparams in rows:
        try:
            v = json.loads(pparams)["vectorizer"]
        except Exception:
            continue
        kwargs = {k: val for k, val in v.items() if k != "name"}
        combos.add((dataset, fil, vec_name, clf_name, rep, vec_kwargs_json(kwargs)))
    return combos


def main() -> None:
    if Path(DB_PATH).exists():
        print(f"[resume] existing DB found: {DB_PATH} — skipping finished combos")

    variants = vectorizer_variants()
    datasets = [ECG200, MNIST]
    print(f"Vectorizer variants (deduplicated): {len(variants)}")
    for name, kwargs in variants:
        print(f"  {name:24s} {kwargs}")

    jobs = []
    for ds in datasets:
        fil = FIL_BY_DS[ds.name]
        for (vec_name, vec_kwargs), clf in product(variants, CLASSIFIERS):
            vec = VectorizationConfig(name=vec_name, kwargs=dict(vec_kwargs))
            jobs.append((ds, fil, vec, clf, REPETITION))

    done = finished_combos()
    print(f"Total combos: {len(jobs)} "
          f"(2 ds x {len(variants)} vec variants x 2 clf x {REPETITION} rep), "
          f"already finished: {len(done)}")

    t0 = time.time()
    ok = fail = skip = 0
    for i, (ds, fil, vec, clf, rep) in enumerate(jobs, 1):
        key = (ds.name, fil.name, vec.name, clf.name, rep, vec_kwargs_json(vec.kwargs))
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
            print(f"  FAIL {res.get('label', key)}: {res.get('error', '')[:300]}")
        if i % 8 == 0 or (ok + fail + skip) == len(jobs):
            el = time.time() - t0
            rate = (ok + fail) / el if el > 0 else 0
            print(f"[{i}/{len(jobs)}] ok={ok} fail={fail} skip={skip} "
                  f"({el:.0f}s, {rate:.3f} runs/s)")
    print(f"COMPLETE: ok={ok} failed={fail} skipped={skip} "
          f"({time.time()-t0:.0f}s). DB={DB_PATH}")


if __name__ == "__main__":
    main()
