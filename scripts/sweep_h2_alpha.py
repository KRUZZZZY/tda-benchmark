#!/usr/bin/env python3
"""Expansion #9 — H2 homology via the TRUE GUDHI Alpha complex in 3D.

The paper's sweeps cap homology at H1 for cost. NOTE (corrected
2026-08-23 after the run): the sphere/torus pair does NOT differ in
beta2 — both classes are closed surfaces with beta2 = 1 (each encloses
one void). The H2-augmented sweep still classifies 100% at both noise
levels, confirming H2 adds neither signal nor harm; the discriminator
is H1 (torus beta1=2 vs sphere beta1=0). See the paper paragraph. This
driver computes homology_dimensions=[0, 1, 2] on the EXISTING
sphere/torus clouds (noise0, noise30) with a real Alpha complex:

  * Framework check: the factory's "alpha" is giotto-tda
    WeakAlphaPersistence (a Rips-on-Delaunay-1-skeleton subcomplex
    approximation). It is NOT the full Alpha complex, and the plan
    (#9) explicitly asks for Alpha-3D ("cheap for H2"). H2 is therefore
    computed with gudhi.AlphaComplex directly, exactly as verified in
    scripts/experiment_alpha.py (radius parameterization: sqrt of
    gudhi's alpha^2 values so the scale matches VR/weak_alpha; H0
    essential class dropped for reduced_homology=True parity; giotto
    padded-diagram output format).

  * Datasets: data/tda/synthetic/sphere_torus_noise0_{X,y}.npy and
    sphere_torus_noise30_{X,y}.npy (200 samples, 100 points, 3-D; the
    executed 99/101 class split is preserved).

  * Grid: vectorizers {betti_curve, persistence_image,
    persistence_landscape} x classifiers {random_forest, svm_rbf},
    5-fold CV seed 42 rep=1 => 2 datasets x 6 configs = 12 runs.

  * Storage: NEW DB data/tda/h2_alpha_sweep.db, ResultStore schema
    (runs/fold_results/config_snapshot/run_metadata); filtration column
    value is 'gudhi_alpha_h2' (true alpha, dims 0-2).

SINGLE-CPU (user directive): serial loop, n_jobs=1, resumable. DO NOT
RUN while scripts/sweep_large_n.py is live (B5 owns the CPU).

Additive-only: creates NEW DB only; no existing DB/dataset/code touched.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_h2_alpha.py

Expected runtime: 1-2 h serial (true alpha is ~7x slower than weak_alpha,
~16 ms/sample on 100-pt clouds; 12 configs x 5 folds).
DB: ../../data/tda/h2_alpha_sweep.db
"""
from __future__ import annotations

import importlib.util
import math
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
DB_PATH = str(DATA_DIR / "h2_alpha_sweep.db")

CV_FOLDS = 5
RANDOM_SEED = 42
REPETITIONS = 1

VECS = [
    VectorizationConfig(name="betti_curve", kwargs={"n_bins": 50}),
    VectorizationConfig(name="persistence_image", kwargs={"sigma": 0.1, "n_bins": 20}),
    VectorizationConfig(name="persistence_landscape", kwargs={"n_layers": 3, "n_bins": 50}),
]
CLFS = [
    ClassifierConfig(name="random_forest", kwargs={}),
    ClassifierConfig(name="svm_rbf", kwargs={}),
]

DATASETS = [
    ("sphere_torus_n0",
     DATA_DIR / "synthetic" / "sphere_torus_noise0_X.npy",
     DATA_DIR / "synthetic" / "sphere_torus_noise0_y.npy",
     "Synthetic sphere/torus, sigma=0.00 (sphere beta2=0 vs torus beta2=1)"),
    ("sphere_torus_n30",
     DATA_DIR / "synthetic" / "sphere_torus_noise30_X.npy",
     DATA_DIR / "synthetic" / "sphere_torus_noise30_y.npy",
     "Synthetic sphere/torus, sigma=0.30 (beta2 signal under noise)"),
]


class GudhiAlphaH2(BaseEstimator, TransformerMixin):
    """TRUE gudhi.AlphaComplex persistence over dims 0,1,2 (3-D clouds).

    Outputs giotto-format padded diagrams (n_samples, n_features, 3).
    Radius parameterization (sqrt of gudhi's alpha^2 values) so the
    scale matches VR/weak_alpha hyperparameters (see experiment_alpha.py).
    """

    def __init__(self, homology_dimensions=(0, 1, 2), sqrt_values=True,
                 reduced_homology=True, n_jobs=1):
        self.homology_dimensions = homology_dimensions
        self.sqrt_values = sqrt_values
        self.reduced_homology = reduced_homology
        self.n_jobs = n_jobs

    def fit(self, X, y=None):
        return self

    def _one_diagram(self, pts):
        import gudhi
        ac = gudhi.AlphaComplex(points=pts)
        st = ac.create_simplex_tree()
        pers = st.persistence()
        maxf = max(v for _, v in st.get_filtration())
        dims = set(self.homology_dimensions)
        dg = []
        for dim, (b, d) in pers:
            if dim not in dims:
                continue
            if math.isinf(d):
                if self.reduced_homology and dim == 0:
                    continue  # drop H0 essential class (giotto default)
                d = maxf
            if self.sqrt_values:
                b, d = math.sqrt(b), math.sqrt(d)
            if b < d:
                dg.append([b, d, float(dim)])
        return dg

    def transform(self, X):
        if isinstance(X, list):
            X = np.asarray(X)
        raw = [self._one_diagram(pts) for pts in X]
        dims = sorted(self.homology_dimensions)
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


def load_dataset(path_x: Path, path_y: Path):
    X = np.load(path_x)
    y = np.load(path_y)
    return X, y


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


def run_one(ds_name, X, y, vec: VectorizationConfig, clf: ClassifierConfig,
            rep: int) -> dict:
    pipe = Pipeline([
        ("filtration", GudhiAlphaH2(homology_dimensions=(0, 1, 2))),
        ("vectorizer", VectorizationFactory.create(vec.name, **vec.kwargs)),
        ("classifier", ClassifierFactory.create(clf.name, **clf.kwargs)),
    ])
    n_features = 0
    rng = np.random.default_rng(RANDOM_SEED + rep * 1000 + 1)
    try:
        sample_idx = rng.choice(len(X), min(10, len(X)), replace=False)
        n_features = pipe[:-1].fit_transform(X[sample_idx]).shape[1]
    except Exception:  # noqa: BLE001 — feature probe is best-effort
        pass

    store = ResultStore(DB_PATH)
    try:
        run_id = store.start_run(
            dataset=ds_name, filtration="gudhi_alpha_h2",
            vectorizer=vec.name, classifier=clf.name, repetition=rep,
            pipeline_params={
                "filtration": {"name": "gudhi_alpha_h2",
                               "homology_dimensions": [0, 1, 2]},
                "vectorizer": {"name": vec.name, **vec.kwargs},
                "classifier": {"name": clf.name, **clf.kwargs},
            },
            n_train=int(len(X) * (1 - 1.0 / CV_FOLDS)),
            n_test=len(X) - int(len(X) * (1 - 1.0 / CV_FOLDS)),
            n_features=n_features,
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
        return {"status": "ok",
                "accuracy": float(scores["test_accuracy"].mean()),
                "wall_time": wall,
                "label": f"{ds_name} | gudhi_alpha_h2 | {vec.name} | {clf.name}"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "failed", "label": f"{ds_name} | {vec.name} | {clf.name}",
                "error": f"{type(exc).__name__}: {exc}"}
    finally:
        store.close()


def main() -> None:
    missing = [p for _, p, _, _ in DATASETS if not p.exists()]
    if missing:
        print(f"MISSING arrays: {missing}")
        sys.exit(1)
    if Path(DB_PATH).exists():
        print(f"[resume] existing DB: {DB_PATH} — skipping finished combos")
    jobs = [(name, Xp, yp, vec, clf, rep)
            for name, Xp, yp, desc in DATASETS
            for vec, clf in product(VECS, CLFS)
            for rep in range(1, REPETITIONS + 1)]
    done = finished_combos()
    print(f"Total configs: {len(jobs)} (2 datasets x 3 vec x 2 clf x "
          f"{REPETITIONS} rep), already finished: {len(done)}")
    print(f"DB: {DB_PATH}")
    t0 = time.time()
    ok = fail = skip = 0
    for i, (name, Xp, yp, vec, clf, rep) in enumerate(jobs, 1):
        key = (name, "gudhi_alpha_h2", vec.name, clf.name, rep)
        if key in done:
            skip += 1
            continue
        X, y = load_dataset(Xp, yp)
        res = run_one(name, X, y, vec, clf, rep)
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
