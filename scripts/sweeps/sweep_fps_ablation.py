"""B4 (#12) — Farthest-Point Sampling (FPS) ablation for paper limitation #1.

Tests whether FPS subsampling of point clouds beats the uniform-random
subsampling the runner currently uses (`rng.choice`, runner.py:61-62).

The native point clouds are (200, 100, 3) — already 100 points, so the
runner's `subsample_points=100` guard (`X.shape[1] > 100`) NEVER fires and
both methods would be no-ops at k=100.  To make the subsampling choice
nontrivial we reduce each cloud to k=50 points (half resolution) and compare
FPS vs uniform-random on downstream pipeline accuracy.

ADDITIVE-ONLY:
  * Writes 4 NEW .npy arrays (2 datasets x fps/uniform arm).
  * Writes to a NEW DB data/tda/fps_ablation.db.
  * Never modifies existing datasets, DBs, or repo code.

SINGLE-CPU (user directive): n_jobs=1, serial loop, no fan-out.

Run (from AI_KOS_PROJECT root):
    .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_fps_ablation.py
"""

from __future__ import annotations

import os
import sys
from itertools import product
from pathlib import Path

import numpy as np

# ── Config ──────────────────────────────────────────────────────────────────
# Reduced-cloud resolution(s).  The native clouds carry 100 points, so
# subsampling to 100 is a no-op (the runner's knob never fires); we reduce to
# 50 (half) as the 'design' resolution and also 15 as a degraded, non-saturated
# regime where subsampling method even has a chance to matter.
FPS_K_LIST = [50, 15]
SUBSAMPLE_SEED = 42              # deterministic seed for the point-selection step
CV_FOLDS = 5
RANDOM_SEED = 42
REP = 1

PROJECT_ROOT = "/home/kruzzzzy/Documents/AI_KOS_PROJECT"
DB_PATH = f"{PROJECT_ROOT}/data/tda/fps_ablation.db"
SCRIPTS_DIR = os.path.abspath(os.path.dirname(__file__))

# import the hyphenated package by name via the projects/ symlink
sys.path.insert(0, os.path.abspath(os.path.join(PROJECT_ROOT, "projects")))
from tda_benchmark.config import (  # noqa: E402
    ClassifierConfig,
    DatasetConfig,
    FiltrationConfig,
    VectorizationConfig,
)
from tda_benchmark.runner import _run_one_worker  # noqa: E402


def fps(points: np.ndarray, k: int, seed: int = 0) -> np.ndarray:
    """Greedy farthest-point sampling.

    Start from a deterministic seed point, then repeatedly add the point
    farthest (max Euclidean distance) from the already-selected set until k
    distinct indices are chosen.  Returns a sorted int array of indices into
    ``points``.

    Deterministic: starts at index 0, breaks ties via np.argmax (
    first-occurrence) and an ordered fallback scan, so repeated calls with the
    same inputs return identical indices.
    """
    n = points.shape[0]
    if k >= n:
        return np.arange(n)

    # Pairwise squared Euclidean distances (avoid sqrt until needed).
    diff = points[:, None, :] - points[None, :, :]
    d2 = np.einsum("ijk,ijk->ij", diff, diff)

    selected = [0]
    dist_to_sel = d2[0].copy()  # squared distance to the seed point
    selected_set = {0}

    while len(selected) < k:
        new = int(np.argmax(dist_to_sel))
        if new in selected_set:
            # Exact ties can keep re-picking the same max; scan for first
            # unselected index as a deterministic tie-break.
            for cand in range(n):
                if cand not in selected_set:
                    new = cand
                    break
            else:
                break
        selected.append(new)
        selected_set.add(new)
        # New distance-to-selected-set = min(old, dist to the new point).
        np.minimum(dist_to_sel, d2[new], out=dist_to_sel)

    return np.array(sorted(selected))


def _uniform_idx(n: int, k: int, rng: np.random.Generator) -> np.ndarray:
    """Mimic the runner's uniform-random choice (holder.loc, rng.choice)."""
    idx = rng.choice(n, k, replace=False)
    idx.sort()
    return idx


def _build_arm_arrays() -> list[dict]:
    """Create the NEW additive .npy arrays for both arms / datasets / ks.

    Returns a list of plans: each is a dict with the subsampled dataset name,
    X path, labels path, and the sampling method tag.
    """
    data_dir = Path(PROJECT_ROOT) / "data" / "tda" / "synthetic"
    plans = []
    for noise in ("noise0", "noise30"):
        src_X = data_dir / f"sphere_torus_{noise}_X.npy"
        src_y = data_dir / f"sphere_torus_{noise}_y.npy"
        X = np.load(src_X)
        y = np.load(src_y)
        n_points = X.shape[1]

        for k in FPS_K_LIST:
            # FPS arm — deterministic greedy subsampling.
            fps_idx = fps(X[0], k)  # topology is shared across samples; use a reference
            X_fps = X[:, fps_idx, :]
            fps_X_path = data_dir / f"sphere_torus_{noise}_fps{k}_X.npy"
            np.save(fps_X_path, X_fps)
            np.save(data_dir / f"sphere_torus_{noise}_fps{k}_y.npy", y)

            # Uniform-random arm — mirrors the runner's rng.choice, fixed seed.
            rng = np.random.default_rng(SUBSAMPLE_SEED)
            uni_idx = _uniform_idx(n_points, k, rng)
            X_uni = X[:, uni_idx, :]
            uni_X_path = data_dir / f"sphere_torus_{noise}_uniform{k}_X.npy"
            np.save(uni_X_path, X_uni)
            np.save(data_dir / f"sphere_torus_{noise}_uniform{k}_y.npy", y)

            print(f"[data] {noise}: n_points={n_points} -> k={k}")
            print(f"       FPS      idx[:8]={fps_idx[:8]}")
            print(f"       uniform  idx[:8]={uni_idx[:8]}")

            plans.append({
                "arm": "fps", "k": k,
                "name": f"sphere_torus_{noise}_fps{k}",
                "X": str(fps_X_path.relative_to(PROJECT_ROOT)),
                "y": str(data_dir / f"sphere_torus_{noise}_fps{k}_y.npy"),
            })
            plans.append({
                "arm": "uniform", "k": k,
                "name": f"sphere_torus_{noise}_uniform{k}",
                "X": str(uni_X_path.relative_to(PROJECT_ROOT)),
                "y": str(data_dir / f"sphere_torus_{noise}_uniform{k}_y.npy"),
            })
    return plans


def _config_grid():
    filtrations = [
        FiltrationConfig("vietoris_rips", {"homology_dimensions": [0, 1]}),
        FiltrationConfig("weighted_rips", {"homology_dimensions": [0, 1], "weights": "DTM"}),
    ]
    vectorizations = [
        VectorizationConfig("betti_curve", {"n_bins": 50}),
        VectorizationConfig("persistence_landscape", {"n_layers": 3, "n_bins": 50}),
    ]
    classifiers = [
        ClassifierConfig("random_forest"),
        ClassifierConfig("svm_rbf"),
    ]
    return filtrations, vectorizations, classifiers


def _already_finished(db_path: str) -> set[tuple]:
    """Return the set of (dataset, filtration, vectorizer, classifier, rep)
    combos already present as completed runs, for resumability."""
    import sqlite3

    done = set()
    if not os.path.exists(db_path):
        return done
    try:
        con = sqlite3.connect(db_path)
        rows = con.execute(
            "SELECT dataset, filtration, vectorizer, classifier, repetition "
            "FROM runs WHERE finished_at IS NOT NULL"
        ).fetchall()
        con.close()
        done = {tuple(r) for r in rows}
    except sqlite3.Error:
        pass
    return done


def main():
    plans = _build_arm_arrays()
    filtrations, vectorizations, classifiers = _config_grid()

    done = _already_finished(DB_PATH)
    print(f"\n{f'config':<70} {'acc':>8}")
    print("-" * 80)

    total = len(plans) * len(filtrations) * len(vectorizations) * len(classifiers)
    completed = 0
    for plan, fil, vec, clf in product(
        plans, filtrations, vectorizations, classifiers
    ):
        ds = DatasetConfig(
            name=plan["name"],
            path=plan["X"],
            labels=plan["y"],
            modality="point_cloud",
            subsample_points=None,  # arrays are pre-subsampled
            max_samples=None,
        )
        key = (plan["name"], fil.name, vec.name, clf.name, REP)
        if key in done:
            print(f"[skip] {key[0]} | {fil.name} | {vec.name} | {clf.name} (already finished)")
            continue
        completed += 1
        label = f"{key[0]} {fil.name} {vec.name} {clf.name}"
        res = _run_one_worker(
            ds, fil, vec, clf, REP,
            cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
            db_path=DB_PATH, project_root=PROJECT_ROOT,
        )
        if res["status"] == "ok":
            print(f"[{completed:>2}/{total}] {label:<52} {res['accuracy']:>8.4f}")
        else:
            print(f"[{completed:>2}/{total}] {label:<52} FAILED ({res.get('error','')[:120]})")

    print("\nDone.")


if __name__ == "__main__":
    main()
