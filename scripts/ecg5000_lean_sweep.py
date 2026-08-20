#!/usr/bin/env python3
"""ECG5000 second-dataset sweep (lean): does vectorization dominate filtration?

Answers reviewer objection O4/Ob: 'n=1 real time-series dataset'. Uses the
repo's exact pipeline components (VR + weak_alpha filtrations, 3 vectorizers,
2 classifiers, 5-fold CV seed 43) on UCR ECG5000 (5000 x 140, 5 classes —
the multiclass generalization of the paper's binary setup).

Serial execution (loky pickling broken in this env); ~3-8s per config.
"""
import os
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold, cross_val_score
from sklearn.pipeline import Pipeline

REPO = Path(__file__).resolve().parent.parent
PROJECT_ROOT = REPO.parent.parent
sys.path.insert(0, str(REPO))
import importlib.util
spec = importlib.util.spec_from_file_location(
    "tda_benchmark", REPO / "__init__.py", submodule_search_locations=[str(REPO)])
pkg = importlib.util.module_from_spec(spec)
sys.modules["tda_benchmark"] = pkg
spec.loader.exec_module(pkg)
from tda_benchmark.factories import FiltrationFactory, VectorizationFactory, ClassifierFactory
from tda_benchmark.config import load_config

X = np.load(PROJECT_ROOT / "data" / "tda" / "ucr2" / "ecg5000_X.npy")
y = np.load(PROJECT_ROOT / "data" / "tda" / "ucr2" / "ecg5000_y.npy")
print(f"ECG5000: X={X.shape} y={y.shape} classes={sorted(set(y.tolist()))} "
      f"counts={dict(zip(*np.unique(y, return_counts=True)))}")

# Takens embedding d=3, tau=1 (same as the paper's ECG200 protocol)
def takens(x, d=3, tau=1):
    n = x.shape[0] - (d - 1) * tau
    return np.stack([x[i:i + n] for i in range(0, d * tau, tau)], axis=1)

Xt = np.stack([takens(x) for x in X])
print(f"Takens-embedded: {Xt.shape} (5000 clouds of {Xt.shape[1]}x3)")

# subsample to 1000 for tractability (stratified)
rng = np.random.default_rng(42)
idx = []
for c in np.unique(y):
    ci = np.where(y == c)[0]
    n = min(200, len(ci))
    idx.extend(rng.choice(ci, n, replace=False))
idx = np.array(idx)
Xb, yb = Xt[idx], y[idx]
print(f"Subsampled: {Xb.shape} counts={dict(zip(*np.unique(yb, return_counts=True)))}")

FILS = [("vietoris_rips", {}), ("weak_alpha", {})]
VECS = [("persistence_entropy", {"normalize": True}),
        ("silhouette", {"n_bins": 50}),
        ("betti_curve", {"n_bins": 50})]
CLFS = [("svm_rbf", {}), ("random_forest", {})]
CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=43)

rows = []
t0 = time.perf_counter()
for fname, fkw in FILS:
    for vname, vkw in VECS:
        for cname, ckw in CLFS:
            pipe = Pipeline([
                ("fil", FiltrationFactory.create(fname, **fkw)),
                ("vec", VectorizationFactory.create(vname, **vkw)),
                ("clf", ClassifierFactory.create(cname, **ckw)),
            ])
            ts = time.perf_counter()
            scores = cross_val_score(pipe, Xb, yb, cv=CV, scoring="accuracy", n_jobs=1)
            rows.append({"filtration": fname, "vectorizer": vname,
                         "classifier": cname, "acc": scores.mean(),
                         "folds": [round(s, 4) for s in scores],
                         "wall": time.perf_counter() - ts})
            print(f"  {fname:14s} {vname:20s} {cname:12s} "
                  f"{scores.mean()*100:6.2f}%  [{time.perf_counter()-ts:.1f}s]")
print(f"done in {time.perf_counter()-t0:.0f}s, {len(rows)} configs")

# stage-impact marginal ranges
from collections import defaultdict
for stage in ("filtration", "vectorizer", "classifier"):
    g = defaultdict(list)
    for r in rows:
        g[r[stage]].append(r["acc"])
    means = {k: sum(v)/len(v) for k, v in g.items()}
    rng_pp = (max(means.values()) - min(means.values())) * 100
    print(f"\n{stage}: range {rng_pp:.2f}pp  " +
          ", ".join(f"{k}={v*100:.2f}%" for k, v in sorted(means.items(), key=lambda kv: -kv[1])))

import json
json.dump(rows, open("/tmp/ecg5000_lean_results.json", "w"), indent=1)
print("\nwrote /tmp/ecg5000_lean_results.json")
