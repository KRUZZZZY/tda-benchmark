#!/usr/bin/env python3
"""Expansion #5 residual (b) — matched-genus sphere/torus repeated 5-fold CV,
25 repetitions.

The matched-genus control (generator: scripts/generate_matched_synthetic.py;
arrays data/tda/synthetic_matched/matched_torus_genus_noise{0,30}_{X,y}.npy,
200 samples x 200 points x 3-D, 100/100) was single-split. This driver
brings it to the repeated-CV protocol of scripts/sweep_repeated_cv_r25.py
(expansion plan #5).

  * datasets: matched_torus_genus_noise0, matched_torus_genus_noise30
    (point_cloud, subsample_points=100 — the repo VR budget; the worker
    subsamples deterministically, CRC32-seeded)
  * filtrations: {vietoris_rips, weighted_rips(weights="DTM")}
    (the diversity-sweep pairing)
  * vectorizers: {betti_curve, persistence_image, persistence_landscape}
  * classifiers: {random_forest, svm_rbf}
  => 2 datasets x 12 configs x 25 reps = 600 runs, 5-fold CV each.
  * CV: StratifiedKFold(random_state=42+rep), reps 1..25 => seeds 43..67.

After the sweep, the driver prints stage-marginal statistics with BOTH
the repeated-measures CI and the Nadeau-Bengio corrected resampled CI
(CRT; SE^2 = (1/R + n2/n1) * s^2_R, n2/n1 = 0.25), copied from
scripts/analysis_repeated_cv_r25.py.

SINGLE-CPU (user directive): serial loop, n_jobs=1, resumable. DO NOT
RUN while scripts/sweep_large_n.py is live (B5 owns the CPU).

Additive-only: creates NEW DB data/tda/r25_genus.db only.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_r25_genus.py

Expected runtime: 1-2 h serial.
DB: ../../data/tda/r25_genus.db
"""
from __future__ import annotations

import importlib.util
import math
import os
import sqlite3
import statistics as st
import sys
import time
from collections import defaultdict
from itertools import product
from pathlib import Path

from scipy import stats as sstats

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO.parent))
if "tda_benchmark" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark", os.path.join(str(REPO), "__init__.py"),
        submodule_search_locations=[str(REPO)])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)

from tda_benchmark.config import (  # noqa: E402
    ClassifierConfig, DatasetConfig, FiltrationConfig, VectorizationConfig,
)
from tda_benchmark.runner import _run_one_worker  # noqa: E402

PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "r25_genus.db")

DATASETS = [
    DatasetConfig(
        name="matched_genus_n0",
        path="data/tda/synthetic_matched/matched_torus_genus_noise0_X.npy",
        labels="data/tda/synthetic_matched/matched_torus_genus_noise0_y.npy",
        modality="point_cloud", subsample_points=100,
        description="matched-genus torus vs genus-2, sigma=0.00"),
    DatasetConfig(
        name="matched_genus_n30",
        path="data/tda/synthetic_matched/matched_torus_genus_noise30_X.npy",
        labels="data/tda/synthetic_matched/matched_torus_genus_noise30_y.npy",
        modality="point_cloud", subsample_points=100,
        description="matched-genus torus vs genus-2, sigma=0.30"),
]

FILTRATIONS = [
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    FiltrationConfig(name="weighted_rips", kwargs={"homology_dimensions": [0, 1]}),
]

VECTORIZATIONS = [
    VectorizationConfig(name="betti_curve", kwargs={"n_bins": 50}),
    VectorizationConfig(name="persistence_image", kwargs={"sigma": 0.1, "n_bins": 20}),
    VectorizationConfig(name="persistence_landscape", kwargs={"n_layers": 3, "n_bins": 50}),
]

CLASSIFIERS = [
    ClassifierConfig(name="random_forest", kwargs={}),
    ClassifierConfig(name="svm_rbf", kwargs={}),
]

CV_FOLDS = 5
RANDOM_SEED = 42
REPETITIONS = 25
N2_N1 = 0.25  # 5-fold CV: test/train ratio


def existing_finished() -> set[tuple]:
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


def stage_stats(db_path: str) -> None:
    """Per-rep stage ranges + repeated-measures & Nadeau-Bengio CIs."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    rows = conn.execute(
        """SELECT r.dataset, r.repetition, r.filtration, r.vectorizer,
                  r.classifier, AVG(f.accuracy)
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL
           GROUP BY r.run_id""").fetchall()
    conn.close()
    if not rows:
        print("(no finished rows yet — stage stats deferred to a later run)")
        return
    reps = sorted({r[1] for r in rows})
    if len(reps) < 2:
        print("(need >=2 finished repetitions for CI statistics)")
        return
    # stage indexes within a row: 0=dataset, 1=rep, 2=fil, 3=vec, 4=clf, 5=acc
    def range_for(rep: int, idx: int) -> float:
        d: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            if r[1] == rep:
                d[r[idx]].append(r[5])
        means = {k: st.mean(v) for k, v in d.items()}
        return (max(means.values()) - min(means.values())) * 100.0

    stages = {0: "dataset", 2: "filtration", 3: "vectorizer", 4: "classifier"}
    print(f"\nStage marginal ranges over {len(reps)} finished reps (pp):")
    print(f"{'stage':<12} {'mean':>6} {'SD':>6} "
          f"{'CI(rep-meas)':>18} {'CI(Nadeau-Bengio)':>22}")
    for idx, name in stages.items():
        vals = [range_for(r, idx) for r in reps]
        m = st.mean(vals)
        s = st.stdev(vals) if len(vals) > 1 else 0.0
        t = sstats.t.ppf(0.975, len(vals) - 1)
        hw_rm = t * s / math.sqrt(len(vals))
        se_nb = math.sqrt((1.0 / len(vals) + N2_N1) * s * s)
        hw_nb = t * se_nb
        print(f"{name:<12} {m:6.2f} {s:6.2f} "
              f"[{m-hw_rm:7.2f},{m+hw_rm:7.2f}]  "
              f"[{m-hw_nb:7.2f},{m+hw_nb:7.2f}]")
    print(f"n2/n1 (NB correction) = {N2_N1:.2f}")


def main() -> None:
    resume = Path(DB_PATH).exists()
    done = existing_finished() if resume else set()
    jobs = [
        (ds, fil, vec, clf, rep)
        for ds in DATASETS
        for fil, vec, clf in product(FILTRATIONS, VECTORIZATIONS, CLASSIFIERS)
        for rep in range(1, REPETITIONS + 1)
        if (ds.name, fil.name, vec.name, clf.name, rep) not in done
    ]
    print(f"Total runs: {len(jobs) + len(done)} "
          f"(2 datasets x 12 configs x 25 reps), "
          f"resume={resume} ({len(done)} already finished)")
    print(f"DB: {DB_PATH}")
    t0 = time.time()
    ok = fail = 0
    for i, (ds, fil, vec, clf, rep) in enumerate(jobs, 1):
        res = _run_one_worker(
            ds, fil, vec, clf, rep,
            cv_folds=CV_FOLDS, random_seed=RANDOM_SEED,
            db_path=DB_PATH, project_root=str(PROJECT_ROOT),
        )
        if res["status"] == "ok":
            ok += 1
        else:
            fail += 1
            print(f"  FAIL {res['label']}: {res.get('error', '')[:300]}")
        if i % 25 == 0 or i == len(jobs):
            el = time.time() - t0
            print(f"[{i}/{len(jobs)}] ok={ok} fail={fail} ({el:.0f}s, "
                  f"{(ok+fail)/el if el else 0:.3f}/s)")
    print(f"SWEEP COMPLETE: ok={ok} failed={fail} "
          f"({time.time()-t0:.0f}s). DB={DB_PATH}")
    stage_stats(DB_PATH)


if __name__ == "__main__":
    main()
