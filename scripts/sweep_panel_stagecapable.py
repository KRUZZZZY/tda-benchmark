#!/usr/bin/env python3
"""B2 (#4) — stage-capable 9-dataset panel with MORE than one working filtration.

Re-runs the 9-dataset panel with a genuinely diverse set of WORKING filtrations
per modality so the paper can compare the FILTRATION stage against the
VECTORIZATION stage on equal footing (each stage now has >1 alternative).

Datasets (identical to sweep_multidataset.py):
  * time series (Takens d=3 tau=1): ecg200 (200x96), ecg5000 (subsampled
    714 -> use max_samples), FordA/FordB/Wafer/ElectricDevices/HandOutlines
    (pre-capped *_cap_X.npy: 1000 samples, length <=100)
  * images (raw 28x28): mnist10_1000, fmnist10_1000 (1000 samples, 10 classes)

Configs per dataset (16):
  * time series: filtrations {vietoris_rips, weighted_rips(DTM)} x
    vectorizers {persistence_image, persistence_landscape, betti_curve,
    silhouette} x classifiers {svm_rbf, random_forest}
      - weighted_rips defaults to weights='DTM' in gtda (a genuinely diverse,
        non-Rips filtration). weak_alpha is AVOIDED on time series because it
        throws giotto IndexError on quantized series (Wafer, ElectricDevices)
        and the essential-H1 inf crash on ECG5000.
  * images: filtrations {cubical, vietoris_rips} x same 4 vectorizers x 2 clf

DB: data/tda/panel_stagecapable.db (ResultStore schema; run_metadata carries
dataset modality + subsampling flags). 5-fold CV seed 42+rep, rep=1. Additive
& RESUMABLE: at startup it reads the combos already present with
finished_at IS NOT NULL and skips them; it never deletes or overwrites.

143 (or 144) runs, serial n_jobs=1 (single-CPU directive).

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_panel_stagecapable.py
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

PROJECT_ROOT = REPO.parent.parent
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "panel_stagecapable.db")

CV_FOLDS = 5
RANDOM_SEED = 42
REP = 1

TS_DATASETS = [
    DatasetConfig(name="ecg200", path="data/tda/ucr/ecg200_X.npy",
                  labels="data/tda/ucr/ecg200_y.npy", modality="time_series",
                  takens_dimension=3, takens_delay=1),
    DatasetConfig(name="ecg5000", path="data/tda/ucr2/ecg5000_X.npy",
                  labels="data/tda/ucr2/ecg5000_y.npy", modality="time_series",
                  takens_dimension=3, takens_delay=1, max_samples=714),
    DatasetConfig(name="FordA", path="data/tda/ucr3/FordA_cap_X.npy",
                  labels="data/tda/ucr3/FordA_cap_y.npy", modality="time_series",
                  takens_dimension=3, takens_delay=1),
    DatasetConfig(name="FordB", path="data/tda/ucr3/FordB_cap_X.npy",
                  labels="data/tda/ucr3/FordB_cap_y.npy", modality="time_series",
                  takens_dimension=3, takens_delay=1),
    DatasetConfig(name="Wafer", path="data/tda/ucr3/Wafer_cap_X.npy",
                  labels="data/tda/ucr3/Wafer_cap_y.npy", modality="time_series",
                  takens_dimension=3, takens_delay=1),
    DatasetConfig(name="ElectricDevices", path="data/tda/ucr3/ElectricDevices_cap_X.npy",
                  labels="data/tda/ucr3/ElectricDevices_cap_y.npy", modality="time_series",
                  takens_dimension=3, takens_delay=1),
    DatasetConfig(name="HandOutlines", path="data/tda/ucr3/HandOutlines_cap_X.npy",
                  labels="data/tda/ucr3/HandOutlines_cap_y.npy", modality="time_series",
                  takens_dimension=3, takens_delay=1),
]
IMG_DATASETS = [
    DatasetConfig(name="mnist10", path="data/tda/images/mnist10_1000_X.npy",
                  labels="data/tda/images/mnist10_1000_y.npy", modality="image"),
    DatasetConfig(name="fmnist10", path="data/tda/images/fmnist10_1000_X.npy",
                  labels="data/tda/images/fmnist10_1000_y.npy", modality="image"),
]

TS_FILS = [
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    # gtda WeightedRipsPersistence defaults to weights='DTM' — genuinely diverse.
    FiltrationConfig(name="weighted_rips", kwargs={"homology_dimensions": [0, 1]}),
]
IMG_FILS = [
    FiltrationConfig(name="cubical", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
]
VECS = [
    VectorizationConfig(name="persistence_image", kwargs={"sigma": 0.1, "n_bins": 20}),
    VectorizationConfig(name="persistence_landscape", kwargs={"n_layers": 3, "n_bins": 50}),
    VectorizationConfig(name="betti_curve", kwargs={"n_bins": 50}),
    VectorizationConfig(name="silhouette", kwargs={"n_bins": 50}),
]
CLFS = [
    ClassifierConfig(name="svm_rbf", kwargs={}),
    ClassifierConfig(name="random_forest", kwargs={}),
]


def done_combos(db_path: str) -> set[tuple[str, str, str, str, int]]:
    """Return (dataset, filtration, vectorizer, classifier, repetition) tuples
    already completed (finished_at IS NOT NULL) in the target DB."""
    if not os.path.exists(db_path):
        return set()
    con = sqlite3.connect(db_path)
    try:
        rows = con.execute(
            "SELECT dataset, filtration, vectorizer, classifier, repetition "
            "FROM runs WHERE finished_at IS NOT NULL"
        ).fetchall()
        return {(r[0], r[1], r[2], r[3], r[4]) for r in rows}
    finally:
        con.close()


def main() -> None:
    jobs = []
    for ds in TS_DATASETS:
        for fil, vec, clf in product(TS_FILS, VECS, CLFS):
            jobs.append((ds, fil, vec, clf))
    for ds in IMG_DATASETS:
        for fil, vec, clf in product(IMG_FILS, VECS, CLFS):
            jobs.append((ds, fil, vec, clf))

    done = done_combos(DB_PATH)
    total = len(jobs)
    # Determine a stable, reproducible sort order so resume is deterministic.
    jobs = sorted(
        jobs,
        key=lambda j: (j[0].name, j[1].name, j[2].name, j[3].name),
    )
    pending = [j for j in jobs
               if (j[0].name, j[1].name, j[2].name, j[3].name, REP) not in done]

    print(f"Planned runs: {total} ({len(TS_DATASETS)} TS + {len(IMG_DATASETS)} img "
          f"datasets x 16 configs)")
    print(f"Already finished (resume skip): {total - len(pending)}")
    print(f"Pending: {len(pending)}")
    print(f"DB: {DB_PATH}")

    if not pending:
        print("Nothing to do — all combos already finished.")
        return

    ok = fail = 0
    t0 = time.perf_counter()
    n = len(pending)
    for i, (ds, fil, vec, clf) in enumerate(pending, 1):
        key = (ds.name, fil.name, vec.name, clf.name, REP)
        if key in done:
            continue
        r = _run_one_worker(ds, fil, vec, clf, REP,
                            cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
                            db_path=DB_PATH, project_root=str(PROJECT_ROOT))
        if r["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"FAIL {ds.name}/{fil.name}/{vec.name}/{clf.name}: "
                  f"{str(r.get('error', ''))[:200]}")
        if i % 10 == 0 or i == n:
            el = time.perf_counter() - t0
            print(f"[{i}/{n}] {ok} ok {fail} fail | {i/el:.2f} runs/s | "
                  f"~{(n-i)/(i/el)/60:.0f} min remaining")
    print(f"\nDone in {time.perf_counter()-t0:.0f}s: {ok} ok, {fail} failed")


if __name__ == "__main__":
    main()
