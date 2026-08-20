#!/usr/bin/env python3
"""A6 — REAL peak-memory measurement for the TDA benchmark runs table.

The shipped `runs.peak_memory_mb` column is dead (0.0 everywhere — never
measured). This script measures REAL peak RSS for a representative config sweep
on ECG200: each config runs in its own fresh subprocess (so `ru_maxrss` is a
per-config high-water mark, uncontaminated by earlier runs), and the worker
reports `resource.getrusage(RUSAGE_SELF).ru_maxrss` (KB on Linux; /1024 -> MB).

Sweep: 4 filtrations (vietoris_rips, weak_alpha, sparse_rips, cubical)
        x 3 vectorizers (persistence_image, betti_curve, persistence_entropy)
        x 1 classifier (svm_rbf) = 12 configs on ECG200 (Takens d=3, tau=1),
      5-fold CV, StratifiedKFold(random_state=43) — the paper's folds.

Output: data/tda/peak_memory.db  (table peak_memory: filtration, vectorizer,
classifier, peak_memory_mb, wall_time_s, mean_accuracy, n_folds) plus a
`baseline` row for a bare interpreter (import floor).

Additive-only: creates only this script + peak_memory.db.
"""
from __future__ import annotations

import json
import os
import sqlite3
import subprocess
import sys
import textwrap
import time
from itertools import product
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent          # projects/tda-benchmark
PROJECT_ROOT = REPO.parent.parent                      # AI_KOS_PROJECT
DATA_DIR = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA_DIR / "peak_memory.db"
VENV_PY = PROJECT_ROOT / ".venv-tda" / "bin" / "python"

FILS = [
    ("vietoris_rips", {"homology_dimensions": [0, 1]}),
    ("weak_alpha", {"homology_dimensions": [0, 1]}),
    ("sparse_rips", {"homology_dimensions": [0, 1], "epsilon": 0.3}),
    ("cubical", {"homology_dimensions": [0, 1]}),
]
VECS = [
    ("persistence_image", {"sigma": 0.1, "n_bins": 20}),
    ("betti_curve", {"n_bins": 50}),
    ("persistence_entropy", {"normalize": True}),
]
CLFS = [("svm_rbf", {})]
CV_FOLDS = 5
RANDOM_SEED = 42   # rep=1 -> random_state 43
REP = 1
N_JOBS = 6

# Worker source: runs one config in isolation, mirrors runner.py preprocessing
# (Takens d=3 tau=1) and pipeline construction exactly, reports its own peak RSS.
WORKER = textwrap.dedent("""
    import json, resource, sys, time
    from pathlib import Path
    import numpy as np
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.pipeline import Pipeline

    sys.path.insert(0, {projects_repr})
    from tda_benchmark.factories import ClassifierFactory, FiltrationFactory, VectorizationFactory

    PROJECT_ROOT = Path({project_root_repr})
    X = np.load(PROJECT_ROOT / "data" / "tda" / "ucr" / "ecg200_X.npy")
    y = np.load(PROJECT_ROOT / "data" / "tda" / "ucr" / "ecg200_y.npy")

    dim, delay = 3, 1
    stride = (dim - 1) * delay
    n_points = X.shape[1] - stride
    embedded = np.zeros((X.shape[0], n_points, dim), dtype=X.dtype)
    for d in range(dim):
        embedded[:, :, d] = X[:, d * delay : d * delay + n_points]

    fil_name, fil_kw = {fil!r}
    vec_name, vec_kw = {vec!r}
    clf_name, clf_kw = {clf!r}
    pipe = Pipeline([
        ("filtration", FiltrationFactory.create(fil_name, **fil_kw)),
        ("vectorizer", VectorizationFactory.create(vec_name, **vec_kw)),
        ("classifier", ClassifierFactory.create(clf_name, **clf_kw)),
    ])
    cv = StratifiedKFold(n_splits={cv_folds}, shuffle=True, random_state={random_seed} + {rep})
    t0 = time.perf_counter()
    scores = cross_validate(pipe, embedded, y, cv=cv,
                            scoring=["accuracy", "f1_weighted", "precision_weighted", "recall_weighted"],
                            n_jobs=1)
    wall = time.perf_counter() - t0
    # list scoring (as runner.py) -> key is "test_accuracy"
    peak_mb = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0
    print(json.dumps({{
        "filtration": fil_name, "vectorizer": vec_name, "classifier": clf_name,
        "peak_memory_mb": round(peak_mb, 1), "wall_time_s": round(wall, 2),
        "mean_accuracy": float(scores["test_accuracy"].mean()),
        "n_folds": int(len(scores["test_accuracy"])),
    }}))
""")

# Bare-import floor: interpreter + numpy + sklearn + gtda + gudhi, no data, no pipeline.
FLOOR_WORKER = textwrap.dedent("""
    import json, resource, sys
    sys.path.insert(0, {projects_repr})
    import numpy, sklearn, gtda, gudhi  # noqa
    print(json.dumps({{
        "peak_memory_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024.0, 1),
        "note": "bare interpreter + numpy/sklearn/gtda/gudhi import floor",
    }}))
""")


def run_worker(src: str) -> dict:
    proc = subprocess.run(
        [str(VENV_PY), "-c", src],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), timeout=1200,
    )
    if proc.returncode != 0:
        return {"error": proc.stderr[-3000:]}
    return json.loads(proc.stdout.strip().splitlines()[-1])


def main() -> None:
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS peak_memory (
            run_id INTEGER PRIMARY KEY AUTOINCREMENT,
            filtration TEXT NOT NULL,
            vectorizer TEXT NOT NULL,
            classifier TEXT NOT NULL,
            peak_memory_mb REAL,
            wall_time_s REAL,
            mean_accuracy REAL,
            n_folds INTEGER
        );
        CREATE TABLE IF NOT EXISTS baseline (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            peak_memory_mb REAL,
            note TEXT,
            measured_at TEXT
        );
    """)
    conn.commit()
    conn.close()

    rows = []
    t0 = time.perf_counter()
    for (fname, fkw), (vname, vkw), (cname, ckw) in product(FILS, VECS, CLFS):
        src = WORKER.format(
            projects_repr=repr(str(PROJECT_ROOT / "projects")),
            project_root_repr=repr(str(PROJECT_ROOT)),
            fil=(fname, fkw), vec=(vname, vkw), clf=(cname, ckw),
            cv_folds=CV_FOLDS, random_seed=RANDOM_SEED, rep=REP,
        )
        res = run_worker(src)
        if "error" in res:
            print(f"  FAIL {fname:14s} {vname:20s} {cname:12s}: {res['error'][-500:]}")
            continue
        rows.append(res)
        print(f"  {res['filtration']:14s} {res['vectorizer']:20s} {res['classifier']:12s} "
              f"peak={res['peak_memory_mb']:7.1f} MB  wall={res['wall_time_s']:5.1f}s  "
              f"acc={res['mean_accuracy']*100:5.2f}%")

    # bare-import floor (single measurement)
    floor = run_worker(FLOOR_WORKER.format(projects_repr=repr(str(PROJECT_ROOT / "projects"))))
    if "error" not in floor:
        print(f"  [baseline] bare import floor: peak={floor['peak_memory_mb']:.1f} MB")

    conn = sqlite3.connect(str(DB_PATH))
    for r in rows:
        conn.execute(
            "INSERT INTO peak_memory (filtration, vectorizer, classifier, peak_memory_mb, wall_time_s, mean_accuracy, n_folds) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (r["filtration"], r["vectorizer"], r["classifier"],
             r["peak_memory_mb"], r["wall_time_s"], r["mean_accuracy"], r["n_folds"]),
        )
    if "error" not in floor:
        conn.execute(
            "INSERT OR REPLACE INTO baseline (id, peak_memory_mb, note, measured_at) VALUES (1, ?, ?, datetime('now'))",
            (floor["peak_memory_mb"], floor["note"]),
        )
    conn.commit()
    conn.close()
    print(f"\nDone in {time.perf_counter()-t0:.0f}s: {len(rows)} configs + baseline -> {DB_PATH}")


if __name__ == "__main__":
    main()
