#!/usr/bin/env python3
"""A5 fill-in — complete the 6 cells where giotto's PersistenceImage crashes.

In run_takens_sweep.py, 6/72 cells failed: weak_alpha x persistence_image at
takens_dimension=2 (all tau). Root cause (verified): at d=2 the weak_alpha
Rips-of-Delaunay filtration on 2D clouds produces essential H1 classes
(death = +inf, 81 of 18800 points across the 200 samples). PersistenceImage's
binning casts coordinates through np.array(..., dtype=int); inf -> INT64_MIN
-> IndexError. At d=3 (the paper's setting) and d=4 there are 0 essential
classes, so the native pipeline runs bit-identically.

This script completes the 6 cells with the minimal standard intervention:
clip inf deaths to the maximum finite death in the batch before the vectorizer
(monotone, deterministic; equivalent to how giotto's own landscape/betti
vectorizers treat essential classes). CV folds are identical to the executed
protocol (StratifiedKFold(5, shuffle=True, random_state=43)); preprocessing is
the runner's Takens embedding verbatim. Runs are marked in pipeline_params
with "essential_class_clip": true.

Additive-only: fills data/tda/takens_sweep.db (writes only the 6 missing runs).
"""
from __future__ import annotations

import json
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

REPO = Path(__file__).resolve().parent.parent          # projects/tda-benchmark
PROJECT_ROOT = REPO.parent.parent                      # AI_KOS_PROJECT
sys.path.insert(0, str(PROJECT_ROOT / "projects"))

from tda_benchmark.factories import ClassifierFactory, FiltrationFactory, VectorizationFactory  # noqa: E402
from tda_benchmark.storage import ResultStore  # noqa: E402

DB_PATH = PROJECT_ROOT / "data" / "tda" / "takens_sweep.db"
CV_FOLDS = 5
RANDOM_SEED = 42
REP = 1
RANDOM_STATE = RANDOM_SEED + REP  # 43


class ClipEssential(BaseEstimator, TransformerMixin):
    """Clip essential-class deaths (inf) to the max finite death in the batch."""
    def fit(self, X, y=None):
        return self

    def transform(self, X):
        X = np.array(X, copy=True)
        deaths = X[:, :, 1]
        fin = np.isfinite(deaths)
        if not fin.all():
            m = float(deaths[fin].max()) if fin.any() else 0.0
            deaths[~fin] = m
        return X


def takens_embed(X, dim, delay):
    stride = (dim - 1) * delay
    n_points = X.shape[1] - stride
    emb = np.zeros((X.shape[0], n_points, dim), dtype=X.dtype)
    for d in range(dim):
        emb[:, :, d] = X[:, d * delay : d * delay + n_points]
    return emb


def run_cell(dim, delay, clf_name) -> dict:
    X = np.load(PROJECT_ROOT / "data" / "tda" / "ucr" / "ecg200_X.npy")
    y = np.load(PROJECT_ROOT / "data" / "tda" / "ucr" / "ecg200_y.npy")
    emb = takens_embed(X, dim, delay)

    pipe = Pipeline([
        ("filtration", FiltrationFactory.create("weak_alpha", homology_dimensions=[0, 1])),
        ("clip", ClipEssential()),
        ("vectorizer", VectorizationFactory.create("persistence_image", sigma=0.1, n_bins=20)),
        ("classifier", ClassifierFactory.create(clf_name)),
    ])
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    t0 = time.perf_counter()
    scores = cross_validate(
        pipe, emb, y, cv=cv,
        scoring=["accuracy", "f1_weighted", "precision_weighted", "recall_weighted"],
        n_jobs=1, error_score="raise", return_train_score=False,
    )
    wall = time.perf_counter() - t0
    return {
        "folds": [float(s) for s in scores["test_accuracy"]],
        "f1": [float(s) for s in scores["test_f1_weighted"]],
        "precision": [float(s) for s in scores["test_precision_weighted"]],
        "recall": [float(s) for s in scores["test_recall_weighted"]],
        "wall": wall,
    }


def main() -> None:
    store = ResultStore(DB_PATH)
    done = {r[0] for r in store._conn.execute(
        "SELECT DISTINCT r.dataset FROM runs r JOIN fold_results f ON r.run_id = f.run_id "
        "WHERE r.dataset LIKE 'ecg200_d2_tau%' AND r.filtration='weak_alpha' "
        "AND r.vectorizer='persistence_image'").fetchall()}
    targets = [(2, tau, clf) for tau, clf in product([1, 2, 3], ["svm_rbf", "random_forest"])]
    targets = [(d, tau, clf) for d, tau, clf in targets if f"ecg200_d{d}_tau{tau}" not in done]
    print(f"filling {len(targets)} cells: weak_alpha x persistence_image(clip) x clf at d=2")

    for dim, tau, clf_name in targets:
        ds_name = f"ecg200_d{dim}_tau{tau}"
        res = run_cell(dim, tau, clf_name)
        run_id = store.start_run(
            dataset=ds_name, filtration="weak_alpha", vectorizer="persistence_image",
            classifier=clf_name, repetition=REP,
            pipeline_params={
                "filtration": {"name": "weak_alpha", "homology_dimensions": [0, 1]},
                "vectorizer": {"name": "persistence_image", "sigma": 0.1, "n_bins": 20},
                "classifier": {"name": clf_name},
                "takens_dimension": dim, "takens_delay": tau,
                "essential_class_clip": True,
                "note": "inf deaths clipped to max finite (giotto PI essential-class edge case at d=2)",
            },
            n_train=160, n_test=40,
        )
        for fi in range(CV_FOLDS):
            store.save_fold(run_id, fi + 1, {
                "accuracy": res["folds"][fi], "f1": res["f1"][fi],
                "precision": res["precision"][fi], "recall": res["recall"][fi],
            })
        store.finish_run(run_id, wall_time_s=res["wall"])
        print(f"  {ds_name} | weak_alpha | persistence_image | {clf_name:12s} "
              f"acc={np.mean(res['folds']):.4f}  wall={res['wall']:.1f}s")
    store.close()
    print("done")


if __name__ == "__main__":
    main()
