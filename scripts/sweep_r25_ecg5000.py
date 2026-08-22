#!/usr/bin/env python3
"""Expansion #5 residual (a) — ECG5000 repeated 5-fold CV, 25 repetitions.

The paper's ECG200 result got 25 reps; ECG5000 was single-split. This
driver brings the ECG5000 headline subset to the SAME repeated-CV
protocol (expansion plan #5: "bring everything supporting a headline
claim to the same protocol").

Protocol (bit-identical worker + same config conventions as
scripts/sweep_repeated_cv_r25.py):
  * dataset: data/tda/ucr2/ecg5000_{X,y}.npy (5000x140), time_series,
    Takens d=3 tau=1, max_samples=714 (the paper's ECG5000 subsample —
    same cap as scripts/sweep_multidataset.py)
  * filtrations: {vietoris_rips, weighted_rips(weights="DTM")} —
    weak_alpha is EXCLUDED deliberately: the known weak-alpha fragility
    (essential-H1 inf crash) hits ECG5000 specifically (documented in
    the tda-pipeline-benchmark skill); the DTM arm is the diversity-sweep
    pairing used for ECG200 in sweep_filtration_diversity.py
  * vectorizers: {betti_curve, persistence_image, persistence_landscape}
  * classifiers: {random_forest, svm_rbf}
  => 12 configs x 25 reps = 300 runs, 5-fold CV each.
  * CV: StratifiedKFold(random_state=42+rep), reps 1..25 => seeds 43..67.

After the sweep, the driver prints the stage-marginal statistics with
BOTH the repeated-measures CI and the Nadeau-Bengio corrected resampled
CI (CRT; SE^2 = (1/R + n2/n1) * s^2_R, n2/n1 = 0.25 for 5-fold), copied
from scripts/analysis_repeated_cv_r25.py.

SINGLE-CPU (user directive): serial loop, n_jobs=1, resumable (finished
(fil,vec,clf,rep) combos are skipped). DO NOT RUN while
scripts/sweep_large_n.py is live (B5 owns the CPU).

Additive-only: creates NEW DB data/tda/r25_ecg5000.db only.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/sweep_r25_ecg5000.py

Expected runtime: 1-2 h serial.
DB: ../../data/tda/r25_ecg5000.db
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

import numpy as np
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
DB_PATH = str(PROJECT_ROOT / "data" / "tda" / "r25_ecg5000.db")

DS = DatasetConfig(
    name="ecg5000",
    path="data/tda/ucr2/ecg5000_X.npy",
    labels="data/tda/ucr2/ecg5000_y.npy",
    modality="time_series",
    takens_dimension=3,
    takens_delay=1,
    max_samples=714,
    description="ECG5000 (UCR), 714-sample subsample (paper protocol), "
                "Takens d=3 tau=1",
)

FILTRATIONS = [
    FiltrationConfig(name="vietoris_rips", kwargs={"homology_dimensions": [0, 1]}),
    # weak_alpha excluded: documented essential-H1 inf crash on ECG5000
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
            "SELECT filtration,vectorizer,classifier,repetition FROM runs "
            "WHERE finished_at IS NOT NULL").fetchall()
    finally:
        conn.close()
    return set(rows)


# ── Nadeau-Bengio stage statistics (copied from analysis_repeated_cv_r25.py) ─

def stage_stats(db_path: str) -> None:
    """Per-rep stage ranges + repeated-measures & Nadeau-Bengio CIs."""
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    rows = conn.execute(
        """SELECT r.repetition, r.filtration, r.vectorizer, r.classifier,
                  AVG(f.accuracy)
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL
           GROUP BY r.run_id""").fetchall()
    conn.close()
    if not rows:
        print("(no finished rows yet — stage stats deferred to a later run)")
        return
    reps = sorted({r[0] for r in rows})
    if len(reps) < 2:
        print("(need >=2 finished repetitions for CI statistics)")
        return
    # row: 0=rep, 1=fil, 2=vec, 3=clf, 4=acc
    def range_for(rep: int, idx: int) -> float:
        d: dict[str, list[float]] = defaultdict(list)
        for r in rows:
            if r[0] == rep:
                d[r[idx]].append(r[4])
        means = {k: st.mean(v) for k, v in d.items()}
        return (max(means.values()) - min(means.values())) * 100.0

    stages = {1: "filtration", 2: "vectorizer", 3: "classifier"}
    per_rep = {name: [range_for(r, idx) for r in reps]
               for idx, name in stages.items()}
    print(f"\nStage marginal ranges over {len(reps)} finished reps (pp):")
    print(f"{'stage':<12} {'mean':>6} {'SD':>6} "
          f"{'CI(rep-meas)':>18} {'CI(Nadeau-Bengio)':>22}")
    for idx, name in stages.items():
        vals = per_rep[name]
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
        (DS, fil, vec, clf, rep)
        for fil, vec, clf in product(FILTRATIONS, VECTORIZATIONS, CLASSIFIERS)
        for rep in range(1, REPETITIONS + 1)
        if (fil.name, vec.name, clf.name, rep) not in done
    ]
    print(f"Total runs: {len(jobs) + len(done)} (12 configs x 25 reps), "
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
