#!/usr/bin/env python3
"""Expansion #1 residual — LOWER-STAR cubical + SIGNED-DISTANCE cubical on
binary MNIST (extends scripts/sweep_filtration_diversity.py).

The diversity sweep (B1) added the DTM-weighted Rips arm; this driver
finishes the remaining #1 sub-items — cubical VARIANTS on images
(expansion plan: "sublevel vs superlevel vs signed-distance cubical",
the family Conti et al. actually varied). Two variants, both implemented
with gudhi.CubicalComplex (the framework's "cubical" is the stock
giotto CubicalPersistence; these variants are NOT in the factory):

  * lower_star_cubical    — top_dimensional_cells = raw grayscale image
    (float32 in [0,1]); gudhi's CubicalComplex lower-star construction
    (each cell takes the min of its top-dimensional cofaces). This is
    the standard sublevel-set cubical filtration.
  * signed_distance_cubical — binarize at 0.5, compute the signed
    distance transform (scipy.ndimage.distance_transform_edt):
    positive inside the digit, negative outside. Sublevel sets sweep
    from the exterior into the digit — a genuinely different scalar
    function with different persistence content.

Dataset: binary MNIST, data/tda/images/mnist_01_{X,y}.npy (400 samples,
28x28, 200/class — the paper's MNIST-01 set).

Grid: 2 filtrations x vectorizers {betti_curve, persistence_image,
persistence_landscape} x classifiers {random_forest, svm_rbf},
5-fold CV seed 42 rep=1 => 12 configs.

Homology dims [0,1] for both variants (H2 on 28x28 grids adds nothing
and costs; the paper's cubical arm is also [0,1]).

SINGLE-CPU (user directive): serial loop, n_jobs=1, resumable. DO NOT
RUN while scripts/sweep_large_n.py is live (B5 owns the CPU).

Additive-only: creates NEW DB data/tda/filtration_diversity_more.db only.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_filtration_diversity_more.py

Expected runtime: 1-2 h serial.
DB: ../../data/tda/filtration_diversity_more.db
"""
from __future__ import annotations

import importlib.util
import os
import sqlite3
import sys
import time
from itertools import product
from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.pipeline import Pipeline

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO.parent))
if "tda_benchmark" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark", os.path.join(str(REPO), "__init__.py"),
        submodule_search_locations=[str(REPO)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)

from tda_benchmark.config import ClassifierConfig, VectorizationConfig  # noqa: E402
from tda_benchmark.factories import ClassifierFactory, VectorizationFactory  # noqa: E402
from tda_benchmark.storage import ResultStore  # noqa: E402

PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
DATA_DIR = PROJECT_ROOT / "data" / "tda"
DB_PATH = str(DATA_DIR / "filtration_diversity_more.db")
X_PATH = DATA_DIR / "images" / "mnist_01_X.npy"
Y_PATH = DATA_DIR / "images" / "mnist_01_y.npy"

CV_FOLDS = 5
RANDOM_SEED = 42
REPETITIONS = 1

FILTRATIONS = ["lower_star_cubical", "signed_distance_cubical"]
VECS = [
    VectorizationConfig(name="betti_curve", kwargs={"n_bins": 50}),
    VectorizationConfig(name="persistence_image", kwargs={"sigma": 0.1, "n_bins": 20}),
    VectorizationConfig(name="persistence_landscape", kwargs={"n_layers": 3, "n_bins": 50}),
]
CLFS = [
    ClassifierConfig(name="random_forest", kwargs={}),
    ClassifierConfig(name="svm_rbf", kwargs={}),
]


def _pad_diagrams(raw: list[list[list[float]]], dims: tuple) -> np.ndarray:
    nfeat = 0
    for dim in dims:
        lens = [len([r for r in dg if abs(r[2] - dim) < 1e-9]) for dg in raw]
        nfeat += max(lens) if lens else 1
    out = np.zeros((len(raw), nfeat, 3))
    col = 0
    for dim in dims:
        lens = [len([r for r in dg if abs(r[2] - dim) < 1e-9]) for dg in raw]
        m = max(lens) if lens else 1
        births = [r[0] for dg in raw for r in dg if abs(r[2] - dim) < 1e-9]
        padval = min(births) if births else 0.0
        for j, dg in enumerate(raw):
            sub = [r for r in dg if abs(r[2] - dim) < 1e-9]
            for k, r in enumerate(sub):
                out[j, col + k, :] = r
            for k in range(len(sub), m):
                out[j, col + k, :] = [padval, padval, dim]
        col += m
    return out


class GudhiCubicalVariant(BaseEstimator, TransformerMixin):
    """Lower-star / signed-distance cubical persistence via gudhi.

    Outputs giotto-format padded diagrams (n_samples, n_features, 3),
    dims [0,1], H0 essential class dropped (reduced_homology parity).
    """

    def __init__(self, variant="lower_star_cubical",
                 homology_dimensions=(0, 1), threshold=0.5, n_jobs=1):
        self.variant = variant
        self.homology_dimensions = homology_dimensions
        self.threshold = threshold
        self.n_jobs = n_jobs

    def fit(self, X, y=None):
        return self

    @staticmethod
    def _signed_distance(img: np.ndarray, threshold: float) -> np.ndarray:
        from scipy.ndimage import distance_transform_edt
        fg = img > threshold
        pos = distance_transform_edt(fg)
        neg = distance_transform_edt(~fg)
        return pos - neg  # positive inside the digit, negative outside

    def _one_diagram(self, img):
        import gudhi
        if self.variant == "signed_distance_cubical":
            vals = self._signed_distance(img, self.threshold)
        else:  # lower_star_cubical: raw grayscale values
            vals = np.asarray(img, dtype=np.float64)
        cc = gudhi.CubicalComplex(top_dimensional_cells=vals)
        pers = cc.persistence()
        finite = [v for _, (b, d) in pers for v in (b, d) if np.isfinite(v)]
        maxf = max(finite) if finite else 1.0
        dims = set(self.homology_dimensions)
        dg = []
        for dim, (b, d) in pers:
            if dim not in dims:
                continue
            if np.isinf(d):
                if dim == 0:
                    continue  # H0 essential dropped
                d = maxf
            if b < d:
                dg.append([float(b), float(d), float(dim)])
        return dg

    def transform(self, X):
        raw = [self._one_diagram(img) for img in X]
        return _pad_diagrams(raw, tuple(self.homology_dimensions))


def make_filtration(name: str):
    return GudhiCubicalVariant(variant=name)


def finished_combos() -> set:
    if not Path(DB_PATH).exists():
        return set()
    conn = sqlite3.connect(DB_PATH)
    try:
        rows = conn.execute(
            "SELECT dataset,filtration,vectorizer,classifier,repetition "
            "FROM runs WHERE finished_at IS NOT NULL").fetchall()
    finally:
        conn.close()
    return set(rows)


def run_one(fil_name, vec: VectorizationConfig, clf: ClassifierConfig,
            rep: int) -> dict:
    pipe = Pipeline([
        ("filtration", make_filtration(fil_name)),
        ("vectorizer", VectorizationFactory.create(vec.name, **vec.kwargs)),
        ("classifier", ClassifierFactory.create(clf.name, **clf.kwargs)),
    ])
    store = ResultStore(DB_PATH)
    try:
        run_id = store.start_run(
            dataset="mnist_01", filtration=fil_name,
            vectorizer=vec.name, classifier=clf.name, repetition=rep,
            pipeline_params={
                "filtration": {"name": fil_name, "homology_dimensions": [0, 1]},
                "vectorizer": {"name": vec.name, **vec.kwargs},
                "classifier": {"name": clf.name, **clf.kwargs},
            },
            n_train=int(400 * (1 - 1.0 / CV_FOLDS)),
            n_test=400 - int(400 * (1 - 1.0 / CV_FOLDS)),
            n_features=0,
        )
        t0 = time.perf_counter()
        cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True,
                             random_state=RANDOM_SEED + rep)
        scores = cross_validate(
            pipe, X, y, cv=cv,
            scoring=["accuracy", "f1_weighted", "precision_weighted",
                     "recall_weighted"],
            n_jobs=1, error_score="raise", return_train_score=False,
        )
        wall = time.perf_counter() - t0
        for fold_idx in range(CV_FOLDS):
            store.save_fold(run_id, fold_idx + 1, {
                "accuracy": float(scores["test_accuracy"][fold_idx]),
                "f1": float(scores["test_f1_weighted"][fold_idx]),
                "precision": float(scores["test_precision_weighted"][fold_idx]),
                "recall": float(scores["test_recall_weighted"][fold_idx]),
            })
        store.finish_run(run_id, wall_time_s=wall)
        return {"status": "ok", "accuracy": float(scores["test_accuracy"].mean()),
                "wall_time": wall,
                "label": f"mnist_01 | {fil_name} | {vec.name} | {clf.name}"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed",
                "label": f"mnist_01 | {fil_name} | {vec.name} | {clf.name}",
                "error": f"{type(exc).__name__}: {exc}"}
    finally:
        store.close()


X, y = None, None  # module-level cache (populated lazily in main, not at import)


def main() -> None:
    global X, y
    if not (X_PATH.exists() and Y_PATH.exists()):
        print(f"MISSING {X_PATH} / {Y_PATH}")
        sys.exit(1)
    X = np.load(X_PATH)
    y = np.load(Y_PATH)
    print(f"mnist_01: X={X.shape} y={y.shape} classes={np.unique(y).tolist()}")
    if Path(DB_PATH).exists():
        print(f"[resume] existing DB: {DB_PATH} — skipping finished combos")
    jobs = [(fil, vec, clf, rep)
            for fil in FILTRATIONS
            for vec, clf in product(VECS, CLFS)
            for rep in range(1, REPETITIONS + 1)]
    done = finished_combos()
    print(f"Total configs: {len(jobs)} (2 fil x 3 vec x 2 clf x "
          f"{REPETITIONS} rep), already finished: {len(done)}")
    print(f"DB: {DB_PATH}")
    t0 = time.time()
    ok = fail = skip = 0
    for i, (fil, vec, clf, rep) in enumerate(jobs, 1):
        key = ("mnist_01", fil, vec.name, clf.name, rep)
        if key in done:
            skip += 1
            continue
        res = run_one(fil, vec, clf, rep)
        if res["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {res['label']}: {res.get('error', '')[:300]}")
        if i % 3 == 0 or ok + fail + skip == len(jobs):
            el = time.time() - t0
            print(f"[{ok+fail+skip}/{len(jobs)}] ok={ok} fail={fail} "
                  f"skip={skip} ({el:.0f}s)")
    print(f"COMPLETE: ok={ok} failed={fail} skipped={skip} "
          f"({time.time()-t0:.0f}s). DB={DB_PATH}")


if __name__ == "__main__":
    main()
