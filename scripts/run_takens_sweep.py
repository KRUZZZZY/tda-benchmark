#!/usr/bin/env python3
"""A5 — REAL Takens (d, tau) embedding sensitivity sweep for Appendix D.

The paper's Appendix D reports a Takens sensitivity table that was flagged
unreproducible/illustrative (no DB producer exists). This script makes it REAL:
it runs the actual (d, tau) grid through the repo's own runner worker
(`_run_one_worker` from tda_benchmark.runner), giving bit-identical
preprocessing (Takens embedding code, CV folds random_state = random_seed + rep
= 42 + 1 = 43) to the verified 616-configuration sweep.

Grid:  takens_dimension in {2, 3, 4} x takens_delay in {1, 2, 3}  (9 combos)
Configs: 2 filtrations (vietoris_rips, weak_alpha)
          x 2 vectorizers (persistence_image, persistence_entropy)
          x 2 classifiers (svm_rbf, random_forest)   = 8 configs
Total: 72 runs on ECG200 (data/tda/ucr/ecg200_X.npy), 5-fold CV seed 43.

Output: data/tda/takens_sweep.db  (ResultStore schema; dataset column encodes
the (d, tau) combo as 'ecg200_d<d>_tau<tau>'; pipeline_params in run_metadata
carry takens_dimension/takens_delay).

Additive-only: creates only this script + takens_sweep.db.
"""
from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import product
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent          # projects/tda-benchmark
PROJECT_ROOT = REPO.parent.parent                      # AI_KOS_PROJECT
sys.path.insert(0, str(PROJECT_ROOT / "projects"))     # symlink tda_benchmark -> tda-benchmark

from tda_benchmark.config import (  # noqa: E402
    BenchmarkConfig, ClassifierConfig, DatasetConfig, EvaluationConfig,
    FiltrationConfig, OutputConfig, VectorizationConfig,
)
from tda_benchmark.runner import _run_one_worker  # noqa: E402
from tda_benchmark.storage import ResultStore  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA_DIR / "takens_sweep.db"

DIMS = [2, 3, 4]
DELAYS = [1, 2, 3]

FILS = [
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="weak_alpha", kwargs={"homology_dimensions": [0, 1]}),
]
VECS = [
    VectorizationConfig(name="persistence_image", kwargs={"sigma": 0.1, "n_bins": 20}),
    VectorizationConfig(name="persistence_entropy", kwargs={"normalize": True}),
]
CLFS = [
    ClassifierConfig(name="svm_rbf", kwargs={}),
    ClassifierConfig(name="random_forest", kwargs={}),
]

CV_FOLDS = 5
RANDOM_SEED = 42   # rep=1 -> StratifiedKFold random_state = 43 (paper's seed)
REP = 1
N_JOBS = 6


def build_jobs() -> list[tuple]:
    jobs = []
    for d, tau in product(DIMS, DELAYS):
        ds = DatasetConfig(
            name=f"ecg200_d{d}_tau{tau}",
            path="data/tda/ucr/ecg200_X.npy",
            labels="data/tda/ucr/ecg200_y.npy",
            modality="time_series",
            takens_dimension=d,
            takens_delay=tau,
        )
        for fil, vec, clf in product(FILS, VECS, CLFS):
            jobs.append((ds, fil, vec, clf))
    return jobs


def run_one(args: tuple) -> dict:
    ds, fil, vec, clf = args
    return _run_one_worker(
        ds, fil, vec, clf, REP,
        cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
        db_path=str(DB_PATH), project_root=str(PROJECT_ROOT),
    )


def main() -> None:
    jobs = build_jobs()
    print(f"A5 Takens sweep: {len(DIMS)} dims x {len(DELAYS)} delays x "
          f"{len(FILS)*len(VECS)*len(CLFS)} configs = {len(jobs)} runs -> {DB_PATH}")

    # config snapshot for provenance
    store = ResultStore(DB_PATH)
    store.save_config(json.dumps({
        "script": "scripts/run_takens_sweep.py",
        "grid": {"takens_dimension": DIMS, "takens_delay": DELAYS},
        "filtrations": [f.name for f in FILS],
        "vectorizations": [v.name for v in VECS],
        "classifiers": [c.name for c in CLFS],
        "cv_folds": CV_FOLDS, "random_seed": RANDOM_SEED, "repetitions": REP,
        "dataset": "ecg200 (200 x 96), Takens-embedded per combo",
    }, indent=2))
    store.close()

    t0 = time.perf_counter()
    ok = fail = 0
    try:
        with ProcessPoolExecutor(max_workers=N_JOBS) as ex:
            for i, res in enumerate(ex.map(run_one, jobs), 1):
                if res["status"] == "ok":
                    ok += 1
                    print(f"[{i}/{len(jobs)}] OK   {res['label']}  acc={res['accuracy']:.4f}  wall={res['wall_time']:.1f}s")
                else:
                    fail += 1
                    print(f"[{i}/{len(jobs)}] FAIL {res['label']}\n{res['error'][-2000:]}")
    except Exception as exc:  # pool fallback -> serial
        print(f"ProcessPoolExecutor failed ({exc}); falling back to serial")
        for i, args in enumerate(jobs, 1):
            res = run_one(args)
            if res["status"] == "ok":
                ok += 1
                print(f"[{i}/{len(jobs)}] OK   {res['label']}  acc={res['accuracy']:.4f}  wall={res['wall_time']:.1f}s")
            else:
                fail += 1
                print(f"[{i}/{len(jobs)}] FAIL {res['label']}\n{res['error'][-2000:]}")

    print(f"\nDone in {time.perf_counter()-t0:.0f}s: {ok} ok, {fail} failed -> {DB_PATH}")


if __name__ == "__main__":
    main()
