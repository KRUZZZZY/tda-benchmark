#!/usr/bin/env python3
"""Reviewer revision (C): second UCR time-series dataset (ECG5000).

The paper's time-series thesis rests on n=1 dataset (ECG200). This script
adds ECG5000 (UCR archive, 5000 x 140, 5 classes; downloaded by
scripts/download_ucr.py into data/tda/ucr2/) and runs the same ECG200-style
pipeline subset, through the repo's OWN runner worker (_run_one_worker) so
preprocessing (Takens d=3 tau=1), factories, hyperparameters and CV seeding
are bit-identical to the executed sweep:

  filtrations:  vietoris_rips, weak_alpha, cubical        (homology [0,1])
  vectorizers:  persistence_entropy, silhouette, betti_curve
  classifiers:  svm_rbf, random_forest
  3 x 3 x 2 = 18 configs, 5-fold StratifiedKFold(shuffle=True, seed 42+1=43)

Results are written to a NEW sqlite db at /tmp/ecg5000_results.db (additive),
then stage-impact tables (marginal accuracy ranges) are computed WITH and
WITHOUT the cubical arm, mirroring analysis.py's stage_impact().
"""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
PKG_DIR = str(REPO)
if "tda_benchmark" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark", os.path.join(PKG_DIR, "__init__.py"),
        submodule_search_locations=[PKG_DIR])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)

from tda_benchmark.config import (  # noqa: E402
    BenchmarkConfig, ClassifierConfig, DatasetConfig, EvaluationConfig,
    FiltrationConfig, OutputConfig, VectorizationConfig)
from tda_benchmark.runner import _run_one_worker  # noqa: E402

PROJECT_ROOT = REPO.parent.parent
DB_PATH = "/tmp/ecg5000_results.db"
OUT_JSON = "/tmp/second_dataset_results.json"

DS = DatasetConfig(
    name="ecg5000",
    path="data/tda/ucr2/ecg5000_X.npy",
    labels="data/tda/ucr2/ecg5000_y.npy",
    modality="time_series",
    takens_dimension=3,
    takens_delay=1,
    description="UCR ECG5000 (combined TRAIN+TEST, 5000 x 140, 5 classes)",
)
FILS = [
    FiltrationConfig("vietoris_rips", {"homology_dimensions": [0, 1]}),
    FiltrationConfig("weak_alpha", {"homology_dimensions": [0, 1]}),
    FiltrationConfig("cubical", {"homology_dimensions": [0, 1]}),
]
VECS = [
    VectorizationConfig("persistence_entropy", {"normalize": True}),
    VectorizationConfig("silhouette", {"n_bins": 50}),
    VectorizationConfig("betti_curve", {"n_bins": 50}),
]
CLFS = [ClassifierConfig("svm_rbf"), ClassifierConfig("random_forest")]
EVAL = EvaluationConfig(cv_folds=5, scoring="accuracy", random_seed=42, repetitions=1)


def _init_worker():
    """Register the tda_benchmark importlib shim inside loky worker processes
    (loky workers are fresh interpreters; the parent's sys.modules entry does
    not propagate)."""
    import importlib.util
    import sys
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark", os.path.join(REPO_PATH, "__init__.py"),
        submodule_search_locations=[REPO_PATH])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)


REPO_PATH = str(REPO)


def run_sweep(n_jobs: int = 6) -> list[dict]:
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)  # fresh db for this experiment (only /tmp file)
    from joblib import Parallel, delayed
    if n_jobs > 1:
        try:
            from loky import get_reusable_executor
            get_reusable_executor(max_workers=n_jobs, initializer=_init_worker)
        except ImportError:
            print("loky not available; falling back to serial execution")
            n_jobs = 1
    jobs = [(ds, fil, vec, clf, rep)
            for ds in [DS] for fil in FILS for vec in VECS for clf in CLFS
            for rep in range(1, EVAL.repetitions + 1)]
    results = Parallel(n_jobs=n_jobs, backend="loky", verbose=5)(
        delayed(_run_one_worker)(
            ds, fil, vec, clf, rep,
            cv_folds=EVAL.cv_folds, random_seed=EVAL.random_seed,
            db_path=DB_PATH, project_root=str(PROJECT_ROOT))
        for ds, fil, vec, clf, rep in jobs)
    return [dict(r) for r in results]


def stage_impact(rows, key):
    groups = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r["acc"])
    means = {k: sum(v) / len(v) for k, v in groups.items()}
    return means, (max(means.values()) - min(means.values())) if means else 0.0


def analyse() -> dict:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = [dict(r) for r in conn.execute(
        """SELECT r.filtration, r.vectorizer, r.classifier, AVG(f.accuracy) acc
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL GROUP BY r.run_id""").fetchall()]
    conn.close()

    def table(include_cubical: bool):
        sub = [r for r in rows if include_cubical or r["filtration"] != "cubical"]
        out = {}
        for key, label in [("filtration", "Filtration"),
                           ("vectorizer", "Vectorizer"),
                           ("classifier", "Classifier")]:
            means, rng = stage_impact(sub, key)
            out[label.lower()] = {
                "means": {k: round(v, 4) for k, v in sorted(means.items(), key=lambda x: -x[1])},
                "range_pp": round(rng * 100, 2),
            }
        best = max(sub, key=lambda r: r["acc"])
        out["best_config"] = {k: best[k] for k in ("filtration", "vectorizer", "classifier")}
        out["best_config"]["acc"] = round(best["acc"], 4)
        out["n_configs"] = len(sub)
        return out

    top5 = sorted(rows, key=lambda r: -r["acc"])[:5]
    return {
        "n_runs_ok": sum(1 for r in rows),
        "top5": [{"filtration": r["filtration"], "vectorizer": r["vectorizer"],
                  "classifier": r["classifier"], "acc": round(r["acc"], 4),
                  "is_cubical": r["filtration"] == "cubical"} for r in top5],
        "with_cubical": table(True),
        "without_cubical": table(False),
    }


def main():
    import numpy as np
    X = np.load(PROJECT_ROOT / "data" / "tda" / "ucr2" / "ecg5000_X.npy")
    y = np.load(PROJECT_ROOT / "data" / "tda" / "ucr2" / "ecg5000_y.npy")
    print(f"ECG5000: X={X.shape} y={y.shape} classes={sorted(set(y.tolist()))} "
          f"counts={dict(zip(*np.unique(y, return_counts=True)))}")

    results = run_sweep(n_jobs=int(os.environ.get("NJOBS", "6")))
    ok = [r for r in results if r["status"] == "ok"]
    failed = [r for r in results if r["status"] != "ok"]
    print(f"\nsweep: {len(ok)} ok, {len(failed)} failed")
    for r in failed:
        print("FAILED:", r["label"], r.get("error", "")[:500])

    analysis = analyse()
    for label in ("with_cubical", "without_cubical"):
        t = analysis[label]
        print(f"\n--- {label} ---")
        for stage in ("filtration", "vectorizer", "classifier"):
            print(f"  {stage:<12} range {t[stage]['range_pp']:>6.2f} pp   " +
                  ", ".join(f"{k}={v:.4f}" for k, v in t[stage]["means"].items()))
        print(f"  best: {t['best_config']}")
    print(f"\n  top5: {json.dumps(analysis['top5'], indent=2)}")

    with open(OUT_JSON, "w") as fh:
        json.dump(analysis, fh, indent=2, default=str)
    print(f"\nwrote {OUT_JSON}")


if __name__ == "__main__":
    main()
