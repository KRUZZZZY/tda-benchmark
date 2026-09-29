#!/usr/bin/env python3
"""B2 — multi-patient ECG (MIT-BIH) pipeline sweep with patient-disjoint CV.

The paper's ECG5000 probe is single-patient (BIDMC chf07); this closes the
objection with the standard multi-patient benchmark: 48 MIT-BIH records /
48 patients (201+202 grouped), beat windows @ 360 Hz, Takens d=3 tau=1.

Tractable config (2026-08-21, single-CPU): beats are re-capped to
MAX_PER_CLASS=500 (from the build's 2000) and the window reduced to 128
samples (Takens -> 126 points) — the full 256-sample window made VR on
254-point clouds x 5442 train beats ~20 min/config (16 configs ~ 5 h).
The patient-disjoint fold structure is preserved exactly (recomputed on
the capped subset with the same greedy-balanced assignment).

CV: PATIENT-DISJOINT 5-fold — folds precomputed by build_mitbih.py
(mitbih_folds.npy), greedy beat-balanced, no patient in both train and test.
This is stricter than record-level CV (no same-patient leakage).

Config grid (16): filtrations {vietoris_rips, weak_alpha} x vectorizers
{persistence_image, persistence_landscape, betti_curve, silhouette}
x classifiers {svm_rbf, random_forest}.

DB: data/tda/mitbih_sweep_fast.db (table results: filtration, vectorizer,
classifier, fold, accuracy, status). Additive-only.
"""
from __future__ import annotations

import sqlite3
import sys
from collections import Counter
from itertools import product
from pathlib import Path

import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.pipeline import Pipeline

sys.path.insert(0, "/home/kruzzzzy/Documents/AI_KOS_PROJECT/projects")
from tda_benchmark.factories import ClassifierFactory, FiltrationFactory, VectorizationFactory  # noqa: E402

PROJECT_ROOT = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT")
DATA = PROJECT_ROOT / "data" / "tda" / "mitbih"
DB_PATH = PROJECT_ROOT / "data" / "tda" / "mitbih_sweep_fast.db"

MAX_PER_CLASS = 500
WINDOW = 128       # samples around each R-peak (Takens d=3 tau=1 -> 126 pts)
HALF = WINDOW // 2
CV_FOLDS = 5

FILS = [
    ("vietoris_rips", {"homology_dimensions": [0, 1]}),
    ("weak_alpha", {"homology_dimensions": [0, 1]}),
]
VECS = [
    ("persistence_image", {"sigma": 0.1, "n_bins": 20}),
    ("persistence_landscape", {"n_layers": 3, "n_bins": 50}),
    ("betti_curve", {"n_bins": 50}),
    ("silhouette", {"n_bins": 50}),
]
CLFS = ["svm_rbf", "random_forest"]


def takens_embed(X: np.ndarray, dim: int = 3, delay: int = 1) -> np.ndarray:
    stride = (dim - 1) * delay
    n_points = X.shape[1] - stride
    emb = np.zeros((X.shape[0], n_points, dim), dtype=X.dtype)
    for d in range(dim):
        emb[:, :, d] = X[:, d * delay: d * delay + n_points]
    return emb


def main() -> None:
    Xfull = np.load(DATA / "mitbih_X.npy")   # (6802, 256)
    yfull = np.load(DATA / "mitbih_y.npy")
    patfull = np.load(DATA / "mitbih_patient.npy")

    # re-cap beats per class (stratified, seed 42), reduce window to 128
    keep = []
    for c in range(int(yfull.max()) + 1):
        ci = np.where(yfull == c)[0]
        if len(ci) > MAX_PER_CLASS:
            rng = np.random.default_rng(42 + c)
            ci = rng.choice(ci, MAX_PER_CLASS, replace=False)
        keep.append(ci)
    keep = np.concatenate(keep)
    rng = np.random.default_rng(7)
    rng.shuffle(keep)
    Xfull, yfull, patfull = Xfull[keep], yfull[keep], patfull[keep]

    # center the window on the same R-peak: crop the 256-window to 128 around
    # its middle (samples 64..192)
    X = Xfull[:, 64:64 + WINDOW]
    y = yfull
    pat = patfull

    # patient-disjoint folds on the capped subset (greedy beat-balanced)
    patients = sorted(set(pat.tolist()))
    pat_beats = {p: int((pat == p).sum()) for p in patients}
    fold_beats = [0] * CV_FOLDS
    pat_fold = {}
    for p in sorted(pat_beats, key=lambda x: -pat_beats[x]):
        f = int(np.argmin(fold_beats))
        pat_fold[p] = f
        fold_beats[f] += pat_beats[p]
    folds = np.array([pat_fold[p] for p in pat])
    for p in patients:
        assert len(set(folds[pat == p].tolist())) == 1, f"patient {p} split"
    print(f"capped: {X.shape}, classes={dict(Counter(y.tolist()))}, "
          f"patients={len(patients)}, folds={dict(Counter(folds.tolist()))}")

    X = takens_embed(X)
    print(f"embedded: {X.shape}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filtration TEXT NOT NULL, vectorizer TEXT NOT NULL,
            classifier TEXT NOT NULL, fold INTEGER NOT NULL,
            accuracy REAL, status TEXT
        )""")

    n_folds = CV_FOLDS
    total = len(FILS) * len(VECS) * len(CLFS)
    ok = fail = 0
    for i, ((fil_name, fil_kw), (vec_name, vec_kw), clf_name) in enumerate(
            product(FILS, VECS, CLFS), 1):
        row_ok = True
        for fold in range(n_folds):
            test = folds == fold
            try:
                pipe = Pipeline([
                    ("filtration", FiltrationFactory.create(fil_name, **fil_kw)),
                    ("vectorizer", VectorizationFactory.create(vec_name, **vec_kw)),
                    ("classifier", ClassifierFactory.create(clf_name)),
                ])
                pipe.fit(X[~test], y[~test])
                pred = pipe.predict(X[test])
                acc = accuracy_score(y[test], pred)
                conn.execute(
                    "INSERT INTO results (filtration, vectorizer, classifier, fold, accuracy, status) "
                    "VALUES (?, ?, ?, ?, ?, 'ok')",
                    (fil_name, vec_name, clf_name, fold, float(acc)))
            except Exception as exc:  # noqa: BLE001
                conn.execute(
                    "INSERT INTO results (filtration, vectorizer, classifier, fold, accuracy, status) "
                    "VALUES (?, ?, ?, ?, NULL, ?)",
                    (fil_name, vec_name, clf_name, fold, str(exc)[:300]))
                row_ok = False
        conn.commit()
        if row_ok:
            ok += 1
        else:
            fail += 1
        print(f"[{i}/{total}] {fil_name}/{vec_name}/{clf_name} "
              f"{'ok' if row_ok else 'partial-fail'}")
    print(f"\nDone: {ok} ok, {fail} failed. DB: {DB_PATH}")


if __name__ == "__main__":
    sys.exit(main())

