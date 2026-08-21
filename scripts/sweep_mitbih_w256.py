#!/usr/bin/env python3
"""B2 sensitivity check — MIT-BIH sweep with the FULL 256-sample window.

The published MIT-BIH result (paper §5.3, mitbih_sweep_fast.db) uses 128-sample
beat windows (Takens d=3 tau=1 -> 126 points). This script repeats the EXACT
same protocol with the full 256-sample windows (Takens -> 254 points) to check
whether the vectorizer ordering (Betti > PI > Silhouette > Landscape) and the
accuracy range are robust to the window length.

Everything else is identical to the published run:
  * beats re-capped to MAX_PER_CLASS=500 per class (2000 beats total; the
    build's mitbih_X.npy stores 256-sample windows centred on each R-peak),
  * patient-disjoint greedy beat-balanced 5-fold CV (no patient spans folds),
  * config grid: filtrations {vietoris_rips, weak_alpha} x vectorizers
    {persistence_image, persistence_landscape, betti_curve, silhouette}
    x classifiers {svm_rbf, random_forest} = 16 configs,
  * serial (single-CPU), additive-only.

Expected runtime ~1 h (VR on 254-point clouds x ~1600 train beats per fold).
weak_alpha is expected to fail with the same giotto IndexError (degenerate
Delaunay on quantized beats) — recorded as failed rows, not fatal.

DB: data/tda/mitbih_sweep_w256.db (table results: filtration, vectorizer,
classifier, fold, accuracy, status). Additive-only: creates only this script
+ the new DB.
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
DB_PATH = PROJECT_ROOT / "data" / "tda" / "mitbih_sweep_w256.db"

MAX_PER_CLASS = 500
WINDOW = 256       # full window (no crop) — Takens d=3 tau=1 -> 254 points
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
    Xfull = np.load(DATA / "mitbih_X.npy")   # (6802, 256) — full windows
    yfull = np.load(DATA / "mitbih_y.npy")
    patfull = np.load(DATA / "mitbih_patient.npy")

    # re-cap beats per class (stratified, seed 42) — identical to published run
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
    X = Xfull[keep]                    # (2000, 256) — NO crop (w256)
    y = yfull[keep]
    pat = patfull[keep]

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
    print(f"embedded (w256): {X.shape}")

    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filtration TEXT NOT NULL, vectorizer TEXT NOT NULL,
            classifier TEXT NOT NULL, fold INTEGER NOT NULL,
            accuracy REAL, status TEXT
        )""")

    total = len(FILS) * len(VECS) * len(CLFS)
    ok = fail = 0
    import time
    t0 = time.perf_counter()
    for i, ((fil_name, fil_kw), (vec_name, vec_kw), clf_name) in enumerate(
            product(FILS, VECS, CLFS), 1):
        row_ok = True
        for fold in range(CV_FOLDS):
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
        el = time.perf_counter() - t0
        print(f"[{i}/{total}] {fil_name}/{vec_name}/{clf_name} "
              f"{'ok' if row_ok else 'partial-fail'} | {el/60:.1f} min elapsed")
    print(f"\nDone: {ok} ok, {fail} failed. DB: {DB_PATH}")


if __name__ == "__main__":
    sys.exit(main())
