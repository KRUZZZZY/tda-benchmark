#!/usr/bin/env python3
"""Expansion #11 — CROSS-LIBRARY replication sweep.

Reruns a representative configuration subset through three persistence
libraries to establish whether the paper's accuracy results are
library-invariant:

  * (a) giotto-tda (the repo's existing factory):
        - giotto_vietoris_rips  (gtda VietorisRipsPersistence)
        - giotto_weak_alpha     (gtda WeakAlphaPersistence — the
          factory's "alpha"; included so the KNOWN weak-alpha fragility
          is a first-class, documented result dimension: it crashes with
          IndexError / essential-H1 inf on quantized series elsewhere,
          and its status here (ok/failed per config) is recorded in the
          DB exactly like every other run)
  * (b) gudhi-native:
        - gudhi_alpha   (TRUE Alpha complex via gudhi.AlphaComplex,
          radius (sqrt) parameterization, dims 0-1 — pattern verified in
          scripts/experiment_alpha.py)
        - gudhi_rips    (gudhi.RipsComplex, max_dimension=2)
  * (c) ripser-native:
        - ripser_vr     (ripser.ripser, maxdim=1)

All arms share the SAME vectorization + classifier code path
(VectorizationFactory / ClassifierFactory) and the SAME giotto-format
padded-diagram interface, and the SAME CV protocol: 5-fold stratified,
random_state=42+rep, rep=1. Folds are stored with ResultStore so the
DB schema is identical to every other sweep.

Datasets (representative subset): sphere_torus_noise0, sphere_torus_noise30
(100-pt 3-D clouds) and ecg200 (Takens d=3 tau=1, 94-pt clouds).

Grid: 3 datasets x 5 arms x 3 vectorizers {betti_curve,
persistence_image, persistence_landscape} x 2 classifiers {random_forest,
svm_rbf} = 90 configs.

SINGLE-CPU (user directive): serial loop, n_jobs=1, resumable. DO NOT
RUN while scripts/sweep_large_n.py is live (B5 owns the CPU).

Additive-only: creates NEW DB data/tda/cross_library_sweep.db only.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_cross_library.py

Expected runtime: 2-4 h serial (true alpha ~7x slower than weak_alpha).
DB: ../../data/tda/cross_library_sweep.db
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
DB_PATH = str(DATA_DIR / "cross_library_sweep.db")

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

# (name, X path, y path, modality note)
DATASETS = [
    ("sphere_torus_n0",
     DATA_DIR / "synthetic" / "sphere_torus_noise0_X.npy",
     DATA_DIR / "synthetic" / "sphere_torus_noise0_y.npy"),
    ("sphere_torus_n30",
     DATA_DIR / "synthetic" / "sphere_torus_noise30_X.npy",
     DATA_DIR / "synthetic" / "sphere_torus_noise30_y.npy"),
    ("ecg200",
     DATA_DIR / "ucr" / "ecg200_X.npy",
     DATA_DIR / "ucr" / "ecg200_y.npy"),
]

ARMS = ["giotto_vietoris_rips", "giotto_weak_alpha", "gudhi_alpha",
        "gudhi_rips", "ripser_vr"]


# ── data loading (replicates runner.py preprocessing exactly) ───────────────

def load_dataset(name: str) -> tuple[np.ndarray, np.ndarray]:
    if name in ("sphere_torus_n0", "sphere_torus_n30"):
        Xp = DATASETS[0][1] if name == "sphere_torus_n0" else DATASETS[1][1]
        yp = DATASETS[0][2] if name == "sphere_torus_n0" else DATASETS[1][2]
        return np.load(Xp), np.load(yp)
    # ecg200: Takens d=3 tau=1
    X = np.load(DATASETS[2][1])
    y = np.load(DATASETS[2][2])
    dim, delay = 3, 1
    stride = (dim - 1) * delay
    n_points = X.shape[1] - stride
    embedded = np.zeros((X.shape[0], n_points, dim), dtype=X.dtype)
    for d in range(dim):
        embedded[:, :, d] = X[:, d * delay: d * delay + n_points]
    return embedded, y


# ── shared giotto-format diagram padding (pattern from experiment_alpha.py) ─

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


# ── filtration arms ─────────────────────────────────────────────────────────

class _GiottoArm(BaseEstimator, TransformerMixin):
    def __init__(self, name, homology_dimensions=(0, 1), n_jobs=1):
        self.name = name
        self.homology_dimensions = homology_dimensions
        self.n_jobs = n_jobs

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        from tda_benchmark.factories import FiltrationFactory
        filt = FiltrationFactory.create(self.name,
                                        homology_dimensions=list(self.homology_dimensions))
        return filt.fit_transform(X)


class _GudhiAlpha(BaseEstimator, TransformerMixin):
    def __init__(self, homology_dimensions=(0, 1), sqrt_values=True,
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
                    continue
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
        return _pad_diagrams(raw, tuple(self.homology_dimensions))


class _GudhiRips(BaseEstimator, TransformerMixin):
    def __init__(self, homology_dimensions=(0, 1), max_dimension=2, n_jobs=1):
        self.homology_dimensions = homology_dimensions
        self.max_dimension = max_dimension
        self.n_jobs = n_jobs

    def fit(self, X, y=None):
        return self

    def _one_diagram(self, pts):
        import gudhi
        rc = gudhi.RipsComplex(points=pts)
        st = rc.create_simplex_tree(max_dimension=self.max_dimension)
        pers = st.persistence()
        maxf = max(v for _, v in st.get_filtration())
        dims = set(self.homology_dimensions)
        dg = []
        for dim, (b, d) in pers:
            if dim not in dims:
                continue
            if math.isinf(d):
                if dim == 0:
                    continue  # H0 essential dropped (reduced_homology parity)
                d = maxf
            if b < d:
                dg.append([b, d, float(dim)])
        return dg

    def transform(self, X):
        if isinstance(X, list):
            X = np.asarray(X)
        raw = [self._one_diagram(pts) for pts in X]
        return _pad_diagrams(raw, tuple(self.homology_dimensions))


class _RipserVR(BaseEstimator, TransformerMixin):
    def __init__(self, homology_dimensions=(0, 1), maxdim=1, n_jobs=1):
        self.homology_dimensions = homology_dimensions
        self.maxdim = maxdim
        self.n_jobs = n_jobs

    def fit(self, X, y=None):
        return self

    def _one_diagram(self, pts):
        import ripser
        res = ripser.ripser(pts, maxdim=self.maxdim)
        dgms = res["dgms"]  # list of arrays, index = hom dim
        dg = []
        for dim in self.homology_dimensions:
            if dim >= len(dgms):
                continue
            for b, d in dgms[dim]:
                if np.isfinite(d) and b < d:
                    dg.append([float(b), float(d), float(dim)])
        return dg

    def transform(self, X):
        if isinstance(X, list):
            X = np.asarray(X)
        raw = [self._one_diagram(pts) for pts in X]
        return _pad_diagrams(raw, tuple(self.homology_dimensions))


def make_filtration(arm: str):
    if arm == "giotto_vietoris_rips":
        return _GiottoArm("vietoris_rips")
    if arm == "giotto_weak_alpha":
        return _GiottoArm("weak_alpha")
    if arm == "gudhi_alpha":
        return _GudhiAlpha()
    if arm == "gudhi_rips":
        return _GudhiRips()
    if arm == "ripser_vr":
        return _RipserVR()
    raise ValueError(arm)


# ── runner ──────────────────────────────────────────────────────────────────

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


def run_one(ds_name, X, y, arm, vec: VectorizationConfig, clf: ClassifierConfig,
            rep: int) -> dict:
    pipe = Pipeline([
        ("filtration", make_filtration(arm)),
        ("vectorizer", VectorizationFactory.create(vec.name, **vec.kwargs)),
        ("classifier", ClassifierFactory.create(clf.name, **clf.kwargs)),
    ])
    n_features = 0
    rng = np.random.default_rng(RANDOM_SEED + rep * 1000 + 2)
    try:
        sample_idx = rng.choice(len(X), min(10, len(X)), replace=False)
        n_features = pipe[:-1].fit_transform(X[sample_idx]).shape[1]
    except Exception:  # noqa: BLE001 — best-effort probe
        pass

    store = ResultStore(DB_PATH)
    try:
        run_id = store.start_run(
            dataset=ds_name, filtration=arm,
            vectorizer=vec.name, classifier=clf.name, repetition=rep,
            pipeline_params={
                "filtration": {"name": arm},
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
        return {"status": "ok", "accuracy": float(scores["test_accuracy"].mean()),
                "wall_time": wall,
                "label": f"{ds_name} | {arm} | {vec.name} | {clf.name}"}
    except Exception as exc:  # noqa: BLE001
        # known fragility dimension: weak-alpha failures land here as
        # unfinished rows + a printed FAIL, exactly like the factory runs
        return {"status": "failed",
                "label": f"{ds_name} | {arm} | {vec.name} | {clf.name}",
                "error": f"{type(exc).__name__}: {exc}"}
    finally:
        store.close()


def main() -> None:
    missing = [p for _, p, _ in DATASETS if not p.exists()]
    if missing:
        print(f"MISSING arrays: {missing}")
        sys.exit(1)
    if Path(DB_PATH).exists():
        print(f"[resume] existing DB: {DB_PATH} — skipping finished combos")
    jobs = [(name, Xp, yp, arm, vec, clf, rep)
            for name, Xp, yp in DATASETS
            for arm in ARMS
            for vec, clf in product(VECS, CLFS)
            for rep in range(1, REPETITIONS + 1)]
    done = finished_combos()
    print(f"Total configs: {len(jobs)} (3 datasets x 5 arms x 3 vec x 2 clf "
          f"x {REPETITIONS} rep), already finished: {len(done)}")
    print(f"DB: {DB_PATH}")
    print("Arms: giotto_vietoris_rips, giotto_weak_alpha (fragility dimension), "
          "gudhi_alpha, gudhi_rips, ripser_vr")
    t0 = time.time()
    ok = fail = skip = 0
    for i, (name, Xp, yp, arm, vec, clf, rep) in enumerate(jobs, 1):
        key = (name, arm, vec.name, clf.name, rep)
        if key in done:
            skip += 1
            continue
        X, y = load_dataset(name)
        res = run_one(name, X, y, arm, vec, clf, rep)
        if res["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {res['label']}: {res.get('error', '')[:200]}")
        if i % 9 == 0 or ok + fail + skip == len(jobs):
            el = time.time() - t0
            print(f"[{ok+fail+skip}/{len(jobs)}] ok={ok} fail={fail} "
                  f"skip={skip} ({el:.0f}s)")
    print(f"COMPLETE: ok={ok} failed={fail} skipped={skip} "
          f"({time.time()-t0:.0f}s). DB={DB_PATH}")


if __name__ == "__main__":
    main()
