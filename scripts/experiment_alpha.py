#!/usr/bin/env python3
"""Reviewer revision (A): TRUE GUDHI Alpha complex vs giotto WeakAlphaPersistence.

The paper develops the full Alpha complex (Nerve Theorem homotopy guarantee)
but the executed sweep used giotto-tda's WeakAlphaPersistence — a subcomplex
approximation (Rips filtration of the Delaunay-neighbour graph, computed by
ripser). This script implements a TRUE Alpha complex via gudhi.AlphaComplex
and compares classification accuracy AND wall-time against weak_alpha on the
same data, same pipeline hyperparameters, same CV folds.

Design decisions
----------------
* True alpha:  gudhi.AlphaComplex(points) -> create_simplex_tree() ->
  persistence(). GUDHI stores alpha^2 filtration values; we report the
  radius-parameterized diagram (b,d) -> (sqrt b, sqrt d), an order-preserving
  transform of the same filtration (identical sublevel sets), so the scale
  matches weak_alpha/VR which use Euclidean distances. The raw alpha^2 arm
  ('true_alpha_raw') is reported as a secondary column.
* Output format replicates giotto-tda's _postprocess_diagrams exactly:
  H0 essential class dropped (reduced_homology=True, giotto default),
  only b < d triples kept, per-dimension blocks padded with diagonal
  (min_birth, min_birth, dim) triples. Vectorizers filter b >= d anyway.
* Pipeline: filtration -> vectorizer -> classifier, hyperparameters taken
  from expanded_config.yaml; 5-fold stratified CV with
  StratifiedKFold(shuffle=True, random_state=43) — identical to the executed
  sweep (random_seed=42, repetition=1 => 42+1=43). Wall time measured around
  cross_validate exactly as runner.py does.

Additive-only: writes /tmp/alpha_experiment_results.json and prints tables.
"""

from __future__ import annotations

import importlib.util
import json
import math
import os
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.model_selection import StratifiedKFold, cross_validate

# ── importlib shim for the hyphenated repo dir (same as run_all.sh) ────────
REPO = Path(__file__).resolve().parent.parent
PKG_DIR = str(REPO)
if "tda_benchmark" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark", os.path.join(PKG_DIR, "__init__.py"),
        submodule_search_locations=[PKG_DIR])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)

from tda_benchmark.factories import ClassifierFactory, VectorizationFactory  # noqa: E402

PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
DATA_DIR = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA_DIR / "expanded_results.db"
OUT_JSON = "/tmp/alpha_experiment_results.json"

VECS = {
    "persistence_landscape": {"n_layers": 3, "n_bins": 50},
    "persistence_image": {"sigma": 0.1, "n_bins": 20},
    "betti_curve": {"n_bins": 50},
}
CLFS = ["svm_rbf", "random_forest"]


class GudhiAlphaPersistence(BaseEstimator, TransformerMixin):
    """True (full) Alpha complex persistence via gudhi.AlphaComplex.

    Outputs giotto-format padded diagrams (n_samples, n_features, 3).
    """

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
        # pad per-dimension like gtda.homology._utils._postprocess_diagrams
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


# ── data loading — replicates runner.py preprocessing exactly ──────────────

def load_dataset(ds_name: str):
    if ds_name == "sphere_torus_n0":
        X = np.load(DATA_DIR / "synthetic" / "sphere_torus_noise0_X.npy")
        y = np.load(DATA_DIR / "synthetic" / "sphere_torus_noise0_y.npy")
        # subsample_points=100 is a no-op (clouds already 100 pts); max_samples=200 no-op
        return X, y
    if ds_name == "ecg200":
        X = np.load(DATA_DIR / "ucr" / "ecg200_X.npy")
        y = np.load(DATA_DIR / "ucr" / "ecg200_y.npy")
        dim, delay = 3, 1  # takens_dimension=3, takens_delay=1
        stride = (dim - 1) * delay
        n_points = X.shape[1] - stride
        embedded = np.zeros((X.shape[0], n_points, dim), dtype=X.dtype)
        for d in range(dim):
            embedded[:, :, d] = X[:, d * delay: d * delay + n_points]
        return embedded, y
    raise ValueError(ds_name)


def weak_alpha_arm():
    from gtda.homology import WeakAlphaPersistence
    return WeakAlphaPersistence(homology_dimensions=[0, 1], n_jobs=1)


def db_reference(ds_name: str) -> dict:
    """weak_alpha acc/time for the same combos from expanded_results.db."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    ref = {}
    for vec, clf in [(v, c) for v in VECS for c in CLFS]:
        row = conn.execute(
            """SELECT AVG(f.accuracy) acc, r.wall_time_s t
               FROM runs r JOIN fold_results f ON r.run_id = f.run_id
               WHERE r.dataset=? AND r.filtration='weak_alpha'
                 AND r.vectorizer=? AND r.classifier=?
                 AND r.finished_at IS NOT NULL
               GROUP BY r.run_id""",
            (ds_name, vec, clf)).fetchone()
        ref[(vec, clf)] = dict(row) if row else None
    conn.close()
    return ref


def run_arm(ds_name, X, y, filtration, vec_name, clf_name, cv_folds=5, seed=42, rep=1):
    pipeline = [
        ("filtration", filtration),
        ("vectorizer", VectorizationFactory.create(vec_name, **VECS[vec_name])),
        ("classifier", ClassifierFactory.create(clf_name)),
    ]
    from sklearn.pipeline import Pipeline
    pipe = Pipeline(pipeline)
    cv = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed + rep)
    t0 = time.perf_counter()
    scores = cross_validate(
        pipe, X, y, cv=cv, scoring=["accuracy"], n_jobs=1,
        error_score="raise", return_train_score=False)
    wall = time.perf_counter() - t0
    acc = float(scores["test_accuracy"].mean())
    acc_std = float(scores["test_accuracy"].std())
    folds = [float(a) for a in scores["test_accuracy"]]
    return {"accuracy": acc, "acc_std": acc_std, "folds": folds, "wall_time_s": wall}


def time_filtration(filtration, X, n=200):
    """Per-sample filtration wall time on the first n samples."""
    sub = X[:n]
    t0 = time.perf_counter()
    filtration.fit_transform(sub)
    dt = time.perf_counter() - t0
    return dt / len(sub) * 1000.0  # ms per sample


def main():
    results = {"datasets": {}, "filtration_timing": {}}
    datasets = ["sphere_torus_n0", "ecg200"]

    for ds_name in datasets:
        X, y = load_dataset(ds_name)
        print(f"\n{'='*90}\nDataset: {ds_name}  X={X.shape}  y-classes={sorted(set(y.tolist()))}")
        ref = db_reference(ds_name)
        arms = {
            "weak_alpha": weak_alpha_arm(),
            "true_alpha": GudhiAlphaPersistence(homology_dimensions=[0, 1], sqrt_values=True),
            "true_alpha_raw": GudhiAlphaPersistence(homology_dimensions=[0, 1], sqrt_values=False),
        }
        # filtration-only timing (same 200 samples for all arms)
        ds_timing = {}
        for arm_name, filt in arms.items():
            ms = time_filtration(filt, X)
            ds_timing[arm_name] = round(ms, 3)
            print(f"  filtration {arm_name:<16} {ms:8.3f} ms/sample")
        results["filtration_timing"][ds_name] = ds_timing

        ds_res = {"configs": []}
        for vec_name in VECS:
            for clf_name in CLFS:
                row = {"dataset": ds_name, "vectorizer": vec_name, "classifier": clf_name}
                for arm_name, filt in arms.items():
                    r = run_arm(ds_name, X, y, filt, vec_name, clf_name)
                    row[f"{arm_name}_acc"] = round(r["accuracy"], 4)
                    row[f"{arm_name}_acc_std"] = round(r["acc_std"], 4)
                    row[f"{arm_name}_wall"] = round(r["wall_time_s"], 2)
                db = ref.get((vec_name, clf_name))
                row["db_weak_acc"] = round(db["acc"], 4) if db else None
                row["db_weak_wall"] = round(db["t"], 2) if db else None
                ds_res["configs"].append(row)
                print(
                    f"  {vec_name:<22} {clf_name:<13} "
                    f"weak={row['weak_alpha_acc']:.4f} ({row['weak_alpha_wall']:.1f}s) | "
                    f"db_weak={row['db_weak_acc']} | "
                    f"true={row['true_alpha_acc']:.4f} ({row['true_alpha_wall']:.1f}s) | "
                    f"true_raw={row['true_alpha_raw_acc']:.4f}")
        results["datasets"][ds_name] = ds_res

    # aggregate: mean |weak - true|, mean wall-time ratio
    agg = {"mean_abs_acc_diff": {}, "mean_wall_ratio": {}}
    for ds_name in datasets:
        diffs = [abs(c["weak_alpha_acc"] - c["true_alpha_acc"])
                 for c in results["datasets"][ds_name]["configs"]]
        ratios = [c["true_alpha_wall"] / c["weak_alpha_wall"]
                  for c in results["datasets"][ds_name]["configs"]
                  if c["weak_alpha_wall"] > 0]
        agg["mean_abs_acc_diff"][ds_name] = round(float(np.mean(diffs)), 4)
        agg["mean_wall_ratio"][ds_name] = round(float(np.mean(ratios)), 3)
    results["aggregate"] = agg
    print(f"\naggregate: {json.dumps(agg, indent=2)}")

    with open(OUT_JSON, "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    print(f"\nwrote {OUT_JSON}")


if __name__ == "__main__":
    main()
