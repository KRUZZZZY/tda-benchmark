#!/usr/bin/env python3
"""A2 — Non-topological baselines under the 25-repetition repeated-CV protocol.

Fixes round-2 finding F4 (protocol mismatch): the round-7 baselines
(baseline_experiments.db) used a SINGLE stratified 5-fold split (seed 43)
while the paper's TDA numbers are now reported under repeated CV. This script
re-runs the four headline non-topological baselines under exactly the same
repeated-CV protocol as the A1 ECG200 fix (25 repetitions x 5 folds,
split seeds 43..67 = random_seed 42 + repetition r, r = 1..25):

  * MNIST 0/1:  LogisticRegression + RandomForest on flattened raw pixels (784)
  * ECG200:     LogisticRegression + RandomForest on the raw 96-length signal

Estimators are identical to run_baselines.py part A:
  LogisticRegression(max_iter=1000, random_state=42),
  RandomForestClassifier(n_estimators=100, random_state=42).
ECG200 executed y is {-1,1} (67/133); converted to {0,1} via (y > 0) exactly
as in run_baselines.py so the majority-class anchor is 66.5%.

Per baseline we report:
  * mean accuracy over the 25 per-repetition means,
  * SD across repetitions,
  * corrected 95% CI — repeated-measures over the 25 independent reps
    (mean +/- t_{.975, df=24} * SD/sqrt(25), t = 2.0639) — directly
    comparable to the TDA repeated-CV numbers (same estimator family as
    repeated_cv.db, which used t_{.975, df=4} over 5 reps);
  * secondary Nadeau-Bengio corrected CI over the 125 folds
    (SE^2 = (1/(k*r) + n2/n1) * s^2, t_{.975, 124} = 1.9793).

Repetition 1 (seed 43) must reproduce the round-7 single-split numbers
exactly (99.75 / 99.00 / 85.50 / 85.00) — that is the protocol anchor.

Results: data/tda/baseline_r25.db (NEW; nothing existing is modified).
Parallelism: joblib loky with n_jobs <= 6 (other agents run concurrently).
Workers are module-level and depend only on sklearn/numpy (NO tda_benchmark
import -> loky-safe).
"""

from __future__ import annotations

import json
import os
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
from joblib import Parallel, delayed
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import StratifiedKFold, cross_val_score

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # AI_KOS_PROJECT
DATA = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA / "baseline_r25.db"

N_REPS = 25
N_FOLDS = 5
BASE_SEED = 42            # sweep random_seed; actual split seeds = 42 + rep
N_JOBS = min(6, os.cpu_count() or 4)

# t_{.975, df} — scipy may be present in the venv; fall back to hardcoded.
try:
    from scipy import stats as _stats
    T_975_24 = float(_stats.t.ppf(0.975, 24))
    T_975_124 = float(_stats.t.ppf(0.975, 124))
except Exception:  # pragma: no cover
    T_975_24 = 2.063899
    T_975_124 = 1.9793


def _load_datasets():
    """Return list of (name, feature_type, X, y) matching run_baselines.py."""
    ds = []
    Xm = np.load(DATA / "images" / "mnist_01_X.npy").reshape(400, -1)
    ym = np.load(DATA / "images" / "mnist_01_y.npy")
    ds.append(("mnist_01", "raw_pixels_784", Xm, ym))
    Xe = np.load(DATA / "ucr" / "ecg200_X.npy")
    ye = (np.load(DATA / "ucr" / "ecg200_y.npy") > 0).astype(int)
    ds.append(("ecg200", "raw_signal_96", Xe, ye))
    return ds


def _run_one(dataset, feature_type, classifier, X, y, rep):
    """One (baseline, repetition) job: 5-fold CV under split seed 42+rep."""
    seed = BASE_SEED + rep
    cv = StratifiedKFold(n_splits=N_FOLDS, shuffle=True, random_state=seed)
    if classifier == "logistic":
        est = LogisticRegression(max_iter=1000, random_state=42)
    else:
        est = RandomForestClassifier(n_estimators=100, random_state=42)
    scores = cross_val_score(est, X, y, cv=cv, scoring="accuracy", n_jobs=1)
    return {
        "dataset": dataset, "feature_type": feature_type,
        "classifier": classifier, "repetition": rep, "split_seed": seed,
        "mean_acc": float(np.mean(scores)),
        "folds": [float(s) for s in scores],
    }


def main() -> None:
    t0 = time.perf_counter()
    datasets = _load_datasets()
    jobs = []
    for dataset, feature_type, X, y in datasets:
        for classifier in ("logistic", "random_forest"):
            for rep in range(1, N_REPS + 1):
                jobs.append((dataset, feature_type, classifier, X, y, rep))
    print(f"running {len(jobs)} jobs (4 baselines x {N_REPS} reps x {N_FOLDS} folds) "
          f"on {N_JOBS} workers")
    out = Parallel(n_jobs=N_JOBS, backend="loky", verbose=5)(
        delayed(_run_one)(*j) for j in jobs
    )
    out.sort(key=lambda r: (r["dataset"], r["classifier"], r["repetition"]))

    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS baseline_runs (
        run_id INTEGER PRIMARY KEY AUTOINCREMENT,
        dataset TEXT NOT NULL, classifier TEXT NOT NULL, feature_type TEXT NOT NULL,
        repetition INTEGER NOT NULL, split_seed INTEGER NOT NULL,
        mean_acc REAL, folds TEXT, wall_time_s REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS baseline_summary (
        dataset TEXT, classifier TEXT, feature_type TEXT,
        n_reps INTEGER, mean_acc REAL, sd_acc REAL,
        ci95_lo REAL, ci95_hi REAL,
        nb_ci95_lo REAL, nb_ci95_hi REAL,
        min_acc REAL, max_acc REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS config_snapshot (
        id INTEGER PRIMARY KEY CHECK (id = 1), protocol TEXT, saved_at TEXT)""")
    con.execute("DELETE FROM baseline_runs")
    con.execute("DELETE FROM baseline_summary")
    con.execute("DELETE FROM config_snapshot")

    protocol = (
        f"25 repetitions x 5-fold stratified CV; split seeds 43..67 "
        f"(random_seed 42 + rep, rep=1..25); estimators: "
        f"LogisticRegression(max_iter=1000, random_state=42), "
        f"RandomForestClassifier(n_estimators=100, random_state=42); "
        f"MNIST flattened 784-d raw pixels (400 samples, 200/class); "
        f"ECG200 raw 96-d signal, executed y {{-1,1}} -> {{0,1}} (67/133, "
        f"majority 66.5%); primary CI = repeated-measures over reps "
        f"(t_{{.975,24}}=2.0639 * SD/sqrt(25)); secondary = Nadeau-Bengio "
        f"over 125 folds (t_{{.975,124}}=1.9793, SE^2=(1/(k*r)+n2/n1)*s^2)."
    )
    con.execute("INSERT INTO config_snapshot VALUES (1,?,?)",
                (protocol, time.strftime("%Y-%m-%dT%H:%M:%S")))

    for r in out:
        con.execute(
            "INSERT INTO baseline_runs (dataset, classifier, feature_type, "
            "repetition, split_seed, mean_acc, folds) VALUES (?,?,?,?,?,?,?)",
            (r["dataset"], r["classifier"], r["feature_type"],
             r["repetition"], r["split_seed"], r["mean_acc"],
             json.dumps(r["folds"])))

    # ── aggregates ────────────────────────────────────────────────────────
    print("\n" + "=" * 100)
    print(f"{'dataset':12s} {'classifier':14s} {'feat':16s} {'mean':>8s} "
          f"{'SD':>7s} {'rep1':>7s} {'CI95 lo':>8s} {'CI95 hi':>8s} "
          f"{'NB lo':>8s} {'NB hi':>8s} {'min':>7s} {'max':>7s}")
    print("-" * 100)
    for dataset, feature_type, classifier in sorted(
            {(r["dataset"], r["feature_type"], r["classifier"]) for r in out}):
        rows = [r for r in out if r["dataset"] == dataset
                and r["classifier"] == classifier]
        means = np.array([r["mean_acc"] for r in rows])
        folds = np.concatenate([np.array(r["folds"]) for r in rows])
        mean, sd = float(means.mean()), float(means.std(ddof=1))
        half = T_975_24 * sd / np.sqrt(N_REPS)
        # Nadeau-Bengio: n1=160, n2=40 for ECG200; MNIST 320/80. Use data sizes.
        n1 = {("mnist_01", "raw_pixels_784"): 320,
              ("ecg200", "raw_signal_96"): 160}[(dataset, feature_type)]
        n2 = n1 // 4
        s2_folds = float(folds.var(ddof=1))
        se_nb = np.sqrt((1.0 / (N_FOLDS * N_REPS) + n2 / n1) * s2_folds)
        nb_half = T_975_124 * se_nb
        rep1 = next(r["mean_acc"] for r in rows if r["repetition"] == 1)
        summary = (dataset, classifier, feature_type, N_REPS, mean, sd,
                   mean - half, mean + half, mean - nb_half, mean + nb_half,
                   float(means.min()), float(means.max()))
        con.execute("INSERT INTO baseline_summary VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
                    summary)
        print(f"{dataset:12s} {classifier:14s} {feature_type:16s} "
              f"{mean*100:7.2f}% {sd*100:6.2f}pp {rep1*100:6.2f}% "
              f"{(mean-half)*100:7.2f}% {(mean+half)*100:7.2f}% "
              f"{(mean-nb_half)*100:7.2f}% {(mean+nb_half)*100:7.2f}% "
              f"{means.min()*100:6.2f}% {means.max()*100:6.2f}%")
    con.commit()
    con.close()
    print("-" * 100)
    print(f"done in {time.perf_counter() - t0:.1f}s -> {DB_PATH}")


if __name__ == "__main__":
    sys.exit(main())
