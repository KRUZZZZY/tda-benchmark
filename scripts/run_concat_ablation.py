#!/usr/bin/env python3
"""B3 — TDA + raw-feature concatenation ablation (ECG200 + MNIST-01).

Question: does TDA add value ON TOP of raw features? Baselines beat TDA
alone (MNIST raw-pixel logistic 99.65 vs TDA 98.0; ECG200 raw-signal 85.28
vs 83.0). This ablation concatenates [raw features || TDA vector] and
compares against raw-only and TDA-only on IDENTICAL folds (5-fold CV,
seed 43), 2 classifiers (svm_rbf, random_forest), 2 vectorizers
(betti_curve, persistence_image), 2 filtrations (cubical + vietoris_rips
for images; vietoris_rips + weak_alpha for TS).

Verdict rule (honest): if concat >= max(raw, TDA) on most configs, TDA is
complementary (the positive story); if concat ~= max, it is redundant;
if concat < raw, TDA features add noise.

Output: data/tda/concat_ablation.db (table results: dataset, arm, filtration,
vectorizer, classifier, fold, accuracy). Additive-only.
"""
from __future__ import annotations

import sqlite3
import sys
from itertools import product
from pathlib import Path

import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer
from sklearn.svm import SVC

sys.path.insert(0, "/home/kruzzzzy/Documents/AI_KOS_PROJECT/projects")
from tda_benchmark.factories import FiltrationFactory, VectorizationFactory  # noqa: E402

PROJECT_ROOT = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT")
DATA = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA / "concat_ablation.db"

CV_FOLDS = 5
RANDOM_STATE = 43  # sweep rep-1 folds

DATASETS = {
    "ecg200": {
        "X": "ucr/ecg200_X.npy", "y": "ucr/ecg200_y.npy",
        "fils": ["vietoris_rips", "weak_alpha"],
        "raw": lambda X: X,  # raw 96-d signal
    },
    "mnist_01": {
        "X": "images/mnist_01_X.npy", "y": "images/mnist_01_y.npy",
        "fils": ["cubical", "vietoris_rips"],
        "raw": lambda X: X.reshape(len(X), -1),  # flattened 784 pixels
    },
}
VECS = [("betti_curve", {"n_bins": 50}),
        ("persistence_image", {"sigma": 0.1, "n_bins": 20})]
CLFS = {
    "svm_rbf": lambda: SVC(kernel="rbf", C=1.0, gamma="scale"),
    "random_forest": lambda: RandomForestClassifier(n_estimators=100, random_state=42),
    "logistic": lambda: LogisticRegression(max_iter=2000),
}


def takens_embed(X: np.ndarray, dim: int = 3, delay: int = 1) -> np.ndarray:
    stride = (dim - 1) * delay
    n_points = X.shape[1] - stride
    emb = np.zeros((X.shape[0], n_points, dim), dtype=X.dtype)
    for d in range(dim):
        emb[:, :, d] = X[:, d * delay: d * delay + n_points]
    return emb


def tda_features(X, fil_name, vec_name, vec_kw):
    if X.ndim == 2:  # time series -> Takens embed
        X = takens_embed(X)
    pipe = Pipeline([
        ("filtration", FiltrationFactory.create(fil_name, homology_dimensions=[0, 1])),
        ("vectorizer", VectorizationFactory.create(vec_name, **vec_kw)),
        ("flatten", FunctionTransformer(lambda Z: Z.reshape(Z.shape[0], -1), validate=False)),
    ])
    return pipe.fit_transform(X)


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset TEXT NOT NULL, arm TEXT NOT NULL,
            filtration TEXT NOT NULL, vectorizer TEXT NOT NULL,
            classifier TEXT NOT NULL, fold INTEGER NOT NULL, accuracy REAL
        )""")
    rows = []
    for ds_name, cfg in DATASETS.items():
        X = np.load(DATA / cfg["X"])
        y = np.load(DATA / cfg["y"])
        raw = cfg["raw"](X)
        cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)

        for fil_name, (vec_name, vec_kw), clf_name in product(
                cfg["fils"], VECS, [c for c in CLFS]):
            # TDA-only arm
            Z = tda_features(X, fil_name, vec_name, vec_kw)
            scores = cross_validate(CLFS[clf_name](), Z, y, cv=cv,
                                    scoring="accuracy", n_jobs=1)
            for fi, s in enumerate(scores["test_score"], 1):
                rows.append((ds_name, "tda", fil_name, vec_name, clf_name, fi, s))
            # concat arm: [raw || TDA]
            Zc = np.hstack([raw, Z])
            scores = cross_validate(CLFS[clf_name](), Zc, y, cv=cv,
                                    scoring="accuracy", n_jobs=1)
            for fi, s in enumerate(scores["test_score"], 1):
                rows.append((ds_name, "concat", fil_name, vec_name, clf_name, fi, s))

        # raw-only arm (once per dataset per classifier, no filtration/vectorizer)
        for clf_name in CLFS:
            scores = cross_validate(CLFS[clf_name](), raw, y, cv=cv,
                                    scoring="accuracy", n_jobs=1)
            for fi, s in enumerate(scores["test_score"], 1):
                rows.append((ds_name, "raw", "-", "-", clf_name, fi, s))
        print(f"{ds_name}: done ({len(rows)} rows so far)")

    conn.executemany(
        "INSERT INTO results (dataset, arm, filtration, vectorizer, classifier, fold, accuracy) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)", rows)
    conn.commit()
    conn.close()
    print(f"wrote {DB_PATH}: {len(rows)} rows "
          f"({2*len(DATASETS)*2*len(VECS)*2*len(CLFS) + len(DATASETS)*len(CLFS)*CV_FOLDS} expected)")


if __name__ == "__main__":
    main()
