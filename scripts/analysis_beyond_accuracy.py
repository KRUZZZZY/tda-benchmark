#!/usr/bin/env python3
"""Expansion A4 (#14) — beyond accuracy on the imbalanced ECG5000 set.

The paper reports plain accuracy (and, post-Batch-B, balanced accuracy +
macro-F1) on ECG5000. This script adds the calibration / rank / per-class
metrics the feedback requested, by RE-RUNNING the same grid and capturing
per-fold predicted probabilities:

  * AUROC (one-vs-rest, macro-average) — rank performance,
  * per-class precision / recall / F1 (imbalance-aware),
  * multiclass Brier score (calibration; = mean over samples of the
    sum-over-classes squared error between predicted prob and one-hot).

Grid (identical to ecg5000_balanced_sweep.py): 2 filtrations
(vietoris_rips, weak_alpha) x 3 vectorizers (persistence_entropy,
silhouette, betti_curve) x 2 classifiers (random_forest, svm_rbf[prob]),
Takens d=3 tau=1, stratified 5-fold CV seed 43, subsample cap 200/class
(rng=default_rng(42)) -> 714 samples (counts 0:200,1:200,2:96,3:194,4:24).
silhouette-on-weak_alpha produces NaN features (giotto edge case) -> that
config fails and is excluded, matching the 10/12 valid configs.

Additive-only: creates NEW DB data/tda/beyond_accuracy_ecg5000.db (refuses
to overwrite). SINGLE-CPU serial loop (user directive). Reuses the repo's
factories. This is pure analysis of a re-run — no existing data touched.
"""
from __future__ import annotations

import importlib.util
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import (accuracy_score, balanced_accuracy_score,
                             f1_score, precision_score, recall_score,
                             roc_auc_score)
from sklearn.pipeline import Pipeline

REPO = Path(__file__).resolve().parent.parent          # projects/tda-benchmark
PROJECT_ROOT = REPO.parent.parent                      # AI_KOS_PROJECT
DATA = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA / "beyond_accuracy_ecg5000.db"

sys.path.insert(0, str(REPO))
spec = importlib.util.spec_from_file_location(
    "tda_benchmark", REPO / "__init__.py", submodule_search_locations=[str(REPO)])
pkg = importlib.util.module_from_spec(spec)
sys.modules["tda_benchmark"] = pkg
spec.loader.exec_module(pkg)
from tda_benchmark.factories import (  # noqa: E402
    ClassifierFactory, FiltrationFactory, VectorizationFactory)


def takens(x, d=3, tau=1):
    n = x.shape[0] - (d - 1) * tau
    return np.stack([x[i:i + n] for i in range(0, d * tau, tau)], axis=1)


def _features(pipe, X):
    """Run X through the filtration + vectorization stages."""
    xt = X
    for name in ("fil", "vec"):
        xt = pipe.named_steps[name].transform(xt)
    return xt


def multiclass_brier(y_true, y_proba):
    n = len(y_true)
    k = y_proba.shape[1]
    onehot = np.zeros((n, k))
    onehot[np.arange(n), y_true] = 1.0
    return float(np.mean(np.sum((y_proba - onehot) ** 2, axis=1)))


def main() -> None:
    if DB_PATH.exists():
        raise SystemExit(f"Refusing to overwrite: {DB_PATH}")
    t0 = time.perf_counter()

    X = np.load(DATA / "ucr2" / "ecg5000_X.npy")
    y = np.load(DATA / "ucr2" / "ecg5000_y.npy")
    Xt = np.stack([takens(x) for x in X])
    rng = np.random.default_rng(42)
    idx = []
    for c in np.unique(y):
        ci = np.where(y == c)[0]
        idx.extend(rng.choice(ci, min(200, len(ci)), replace=False))
    idx = np.array(idx)
    Xb, yb = Xt[idx], y[idx]
    print(f"ECG5000 subsample: {Xb.shape}, counts="
          f"{dict(zip(*np.unique(yb, return_counts=True)))}", flush=True)

    FILS = [("vietoris_rips", {}), ("weak_alpha", {})]
    VECS = [("persistence_entropy", {"normalize": True}),
            ("silhouette", {"n_bins": 50}),
            ("betti_curve", {"n_bins": 50})]
    # svm_rbf with probability=True (Platt) so it emits predict_proba for Brier.
    CLFS = [("random_forest", {}), ("svm_rbf", {"probability": True})]
    CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=43)

    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS folds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filtration TEXT, vectorizer TEXT, classifier TEXT, fold INTEGER,
        accuracy REAL, balacc REAL, macrof1 REAL,
        auroc REAL, brier REAL, status TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS perclass (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filtration TEXT, vectorizer TEXT, classifier TEXT, fold INTEGER,
        cls INTEGER, precision REAL, recall REAL, f1 REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS snapshot (
        id INTEGER PRIMARY KEY CHECK (id=1), protocol TEXT, saved_at TEXT)""")
    con.execute(
        "INSERT INTO snapshot VALUES (1, ?, ?)",
        ("A4 #14 beyond-accuracy re-run of the ECG5000 grid capturing "
         "per-fold probabilities (AUROC-OvR macro, multiclass Brier, "
         "per-class P/R/F1). Same data/grid/CV as ecg5000_balanced_sweep.py.",
         time.strftime("%Y-%m-%dT%H:%M:%S")))

    labels = np.unique(yb)
    for fname, fkw in FILS:
        for vname, vkw in VECS:
            for cname, ckw in CLFS:
                pipe = Pipeline([
                    ("fil", FiltrationFactory.create(fname, **fkw)),
                    ("vec", VectorizationFactory.create(vname, **vkw)),
                    ("clf", ClassifierFactory.create(cname, **ckw)),
                ])
                ts = time.perf_counter()
                for fold, (tr, te) in enumerate(CV.split(Xb, yb), start=1):
                    status = "ok"
                    try:
                        pipe.fit(Xb[tr], yb[tr])
                        pred = pipe.predict(Xb[te])
                        acc = float(accuracy_score(yb[te], pred))
                        bal = float(balanced_accuracy_score(yb[te], pred))
                        mf1 = float(f1_score(yb[te], pred, average="macro"))
                        xt = _features(pipe, Xb[te])
                        clf = pipe.named_steps["clf"]
                        score = (clf.predict_proba(xt)
                                 if hasattr(clf, "predict_proba")
                                 else clf.decision_function(xt))
                        auroc = float(roc_auc_score(
                            yb[te], score, multi_class="ovr", average="macro"))
                        brier = (multiclass_brier(yb[te], score)
                                 if score.shape[1] == len(labels) else None)
                    except Exception as exc:  # noqa: BLE001
                        status = f"failed: {type(exc).__name__}: {exc}"
                        acc = bal = mf1 = auroc = brier = None

                    if status == "ok":
                        for cls in labels:
                            con.execute(
                                "INSERT INTO perclass (filtration, vectorizer,"
                                " classifier, fold, cls, precision, recall, f1)"
                                " VALUES (?,?,?,?,?,?,?,?)",
                                (fname, vname, cname, fold, int(cls),
                                 float(precision_score(yb[te], pred, labels=[
                                     int(cls)], average=None)[0]),
                                 float(recall_score(yb[te], pred, labels=[
                                     int(cls)], average=None)[0]),
                                 float(f1_score(yb[te], pred, labels=[
                                     int(cls)], average=None)[0])))
                    con.execute(
                        "INSERT INTO folds (filtration, vectorizer, classifier,"
                        " fold, accuracy, balacc, macrof1, auroc, brier, status)"
                        " VALUES (?,?,?,?,?,?,?,?,?,?)",
                        (fname, vname, cname, fold, acc, bal, mf1,
                         auroc, brier, status))
                print(f"  {fname:14s} {vname:20s} {cname:12s} "
                      f"[{time.perf_counter()-ts:.1f}s]", flush=True)

    con.commit()
    con.close()
    print(f"done in {time.perf_counter()-t0:.0f}s -> {DB_PATH}")


if __name__ == "__main__":
    main()
