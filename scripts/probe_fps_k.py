"""Probe: find the subsampling resolution k where sphere/torus accuracy drops
below saturation, so the FPS-vs-uniform comparison can discriminate.

Additive probe — writes to a THROWAWAY /tmp/fps_probe.db so the real
fps_ablation.db is not polluted. Representative config (2 filtrations x
betti_curve x random_forest) across several k values, both arms, both noise
levels.
"""

from __future__ import annotations

import os
import sys
from itertools import product
from pathlib import Path

import numpy as np

PROJECT_ROOT = "/home/kruzzzzy/Documents/AI_KOS_PROJECT"
PROBE_DB = "/tmp/fps_probe.db"
CV_FOLDS = 5
RANDOM_SEED = 42
REP = 1
SUBSAMPLE_SEED = 42

sys.path.insert(0, os.path.abspath(os.path.join(PROJECT_ROOT, "projects")))
from tda_benchmark.config import (  # noqa: E402
    ClassifierConfig,
    DatasetConfig,
    FiltrationConfig,
    VectorizationConfig,
)
from tda_benchmark.runner import _run_one_worker  # noqa: E402

sys.path.insert(0, os.path.abspath(os.path.join(PROJECT_ROOT, "projects/tda-benchmark/scripts")))
import importlib.util  # noqa: E402

spec = importlib.util.spec_from_file_location(
    "sweep_fps", os.path.join(PROJECT_ROOT, "projects/tda-benchmark/scripts/sweep_fps_ablation.py"))
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

KS = [40, 30, 20, 15, 10, 8]

data_dir = Path(PROJECT_ROOT) / "data" / "tda" / "synthetic"

filts = [
    FiltrationConfig("vietoris_rips", {"homology_dimensions": [0, 1]}),
    FiltrationConfig("weighted_rips", {"homology_dimensions": [0, 1], "weights": "DTM"}),
]
vec = VectorizationConfig("betti_curve", {"n_bins": 50})
clf = ClassifierConfig("random_forest")

print(f"{'dataset':<28} {'k':>3} {'arm':<8} {'fil':<14} {'acc':>7}")
print("-" * 80)

for noise, k, fil in product(("noise0", "noise30"), KS, filts):
    src_X = data_dir / f"sphere_torus_{noise}_X.npy"
    src_y = data_dir / f"sphere_torus_{noise}_y.npy"
    X = np.load(src_X)
    y = np.load(src_y)
    n_points = X.shape[1]

    fps_idx = m.fps(X[0], k)
    X_fps = X[:, fps_idx, :]
    fps_X = data_dir / f"sphere_torus_{noise}_fps{k}_X.npy"
    fps_y = data_dir / f"sphere_torus_{noise}_fps{k}_y.npy"
    np.save(fps_X, X_fps)
    np.save(fps_y, y)

    rng = np.random.default_rng(SUBSAMPLE_SEED)
    uni_idx = m._uniform_idx(n_points, k, rng)
    X_uni = X[:, uni_idx, :]
    uni_X = data_dir / f"sphere_torus_{noise}_uniform{k}_X.npy"
    uni_y = data_dir / f"sphere_torus_{noise}_uniform{k}_y.npy"
    np.save(uni_X, X_uni)
    np.save(uni_y, y)

    for arm, Xp, yp in (("fps", X_fps, y), ("uniform", X_uni, y)):
        name = f"sphere_torus_{noise}_{arm}{k}"
        ds = DatasetConfig(name=name, path=str(fps_X.relative_to(PROJECT_ROOT)) if arm == "fps"
                           else str(uni_X.relative_to(PROJECT_ROOT)),
                           labels=str(fps_y.relative_to(PROJECT_ROOT)) if arm == "fps"
                           else str(uni_y.relative_to(PROJECT_ROOT)),
                           modality="point_cloud", subsample_points=None)
        res = _run_one_worker(ds, fil, vec, clf, REP,
                              cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
                              db_path=PROBE_DB, project_root=PROJECT_ROOT)
        a = res["accuracy"] if res["status"] == "ok" else float("nan")
        print(f"{name:<28} {k:>3} {arm:<8} {fil.name:<14} {a:>7.4f}")

print("\nprobe done")
