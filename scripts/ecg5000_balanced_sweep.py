#!/usr/bin/env python3
"""A4 — ECG5000 sweep with balanced accuracy + macro-F1 (reviewer metrics).

Re-runs the exact ecg5000_lean_sweep.py grid (12 configs = 2 filtrations x
3 vectorizers x 2 classifiers, same components, same CV) and, per fold,
additionally computes the two reviewer-facing metrics alongside plain
accuracy:

    * accuracy        = fraction of correct predictions
    * balanced acc    = mean of per-class recall (sklearn
                        balanced_accuracy_score, unadjusted)
    * macro-F1        = mean of per-class F1 (sklearn f1_score,
                        average='macro')

DISCLOSURES (for the paper):
  * SUBSAMPLE: the executed sweep used a stratified subsample of the 5000
    ECG5000 samples, capped at 200 per class with rng = np.random.default_rng(42)
    -> 714 samples (class counts {0:200, 1:200, 2:96, 3:194, 4:24}).
  * FULL-DATA CLASS DISTRIBUTION: 5000 samples, classes
    2919 / 1767 / 96 / 194 / 24  (58.38% majority class 0) — severely
    imbalanced, which is why balanced accuracy / macro-F1 are reported.
  * NaN EXCLUSIONS: 2 of 12 configs produce NaN — silhouette vectorizer on
    weak_alpha filtration (both classifiers; a giotto-tda edge case where
    silhouette emits NaN on the weak-alpha diagrams). Stage-impact marginals
    and per-vectorizer CIs are computed over the 10 VALID configs only,
    matching /tmp/ecg5000_lean_results.json (vec 24.89pp, fil 3.60pp, 10
    valid of 12).

Per-vectorizer CI: over the valid config means per vectorizer, we report the
t-CI (mean +/- t_{.975, df=n-1} * SD/sqrt(n), df = n_valid_configs - 1) AND
the min-max range. With only 2 valid configs (silhouette) the t-CI is
degenerate (t = 12.706) — the range is the more informative summary there.

Serial execution (loky pickling of the tda_benchmark shim is broken in this
env — see tda-experiments skill); ~3-18s per config, n_jobs=1 everywhere.
Results: data/tda/ecg5000_balanced.db (NEW; nothing existing is modified).
"""

from __future__ import annotations

import importlib.util
import json
import sqlite3
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
from sklearn.pipeline import Pipeline

REPO = Path(__file__).resolve().parent.parent          # projects/tda-benchmark
PROJECT_ROOT = REPO.parent.parent                      # AI_KOS_PROJECT
DATA = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA / "ecg5000_balanced.db"

# ── importlib shim so the repo's exact factories are reused (serial only) ──
sys.path.insert(0, str(REPO))
spec = importlib.util.spec_from_file_location(
    "tda_benchmark", REPO / "__init__.py", submodule_search_locations=[str(REPO)])
pkg = importlib.util.module_from_spec(spec)
sys.modules["tda_benchmark"] = pkg
spec.loader.exec_module(pkg)
from tda_benchmark.factories import (  # noqa: E402
    ClassifierFactory, FiltrationFactory, VectorizationFactory)

try:
    from scipy import stats as _stats
    T_975 = {1: 12.7062, 2: 4.3027, 3: 3.1824, 4: 2.7764}
except Exception:  # pragma: no cover
    T_975 = {1: 12.7062, 2: 4.3027, 3: 3.1824, 4: 2.7764}


def takens(x, d=3, tau=1):
    n = x.shape[0] - (d - 1) * tau
    return np.stack([x[i:i + n] for i in range(0, d * tau, tau)], axis=1)


def main() -> None:
    t0 = time.perf_counter()

    # ── data (identical to ecg5000_lean_sweep.py) ─────────────────────────
    X = np.load(DATA / "ucr2" / "ecg5000_X.npy")
    y = np.load(DATA / "ucr2" / "ecg5000_y.npy")
    full_counts = dict(zip(*np.unique(y, return_counts=True)))
    Xt = np.stack([takens(x) for x in X])
    rng = np.random.default_rng(42)
    idx = []
    for c in np.unique(y):
        ci = np.where(y == c)[0]
        n = min(200, len(ci))
        idx.extend(rng.choice(ci, n, replace=False))
    idx = np.array(idx)
    Xb, yb = Xt[idx], y[idx]
    sub_counts = dict(zip(*np.unique(yb, return_counts=True)))
    print(f"ECG5000: X={X.shape} full counts={full_counts} "
          f"-> subsample {Xb.shape} counts={sub_counts}")

    FILS = [("vietoris_rips", {}), ("weak_alpha", {})]
    VECS = [("persistence_entropy", {"normalize": True}),
            ("silhouette", {"n_bins": 50}),
            ("betti_curve", {"n_bins": 50})]
    CLFS = [("svm_rbf", {}), ("random_forest", {})]
    CV = StratifiedKFold(n_splits=5, shuffle=True, random_state=43)

    con = sqlite3.connect(DB_PATH)
    con.execute("""CREATE TABLE IF NOT EXISTS config_folds (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filtration TEXT, vectorizer TEXT, classifier TEXT, fold INTEGER,
        accuracy REAL, balanced_accuracy REAL, macro_f1 REAL, status TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS config_summary (
        filtration TEXT, vectorizer TEXT, classifier TEXT,
        n_valid_folds INTEGER, mean_acc REAL, mean_balacc REAL,
        mean_macrof1 REAL, status TEXT)""")
    con.execute("""CREATE TABLE IF NOT EXISTS vectorizer_ci (
        vectorizer TEXT, n_valid_configs INTEGER, mean_acc REAL, sd_acc REAL,
        ci95_lo REAL, ci95_hi REAL, min_acc REAL, max_acc REAL)""")
    con.execute("""CREATE TABLE IF NOT EXISTS config_snapshot (
        id INTEGER PRIMARY KEY CHECK (id = 1), protocol TEXT, saved_at TEXT)""")
    for t_ in ("config_folds", "config_summary", "vectorizer_ci", "config_snapshot"):
        con.execute(f"DELETE FROM {t_}")

    protocol = (
        "ECG5000 balanced-metrics sweep. Grid identical to "
        "ecg5000_lean_sweep.py: 2 filtrations (vietoris_rips, weak_alpha) x "
        "3 vectorizers (persistence_entropy{normalize:True}, "
        "silhouette{n_bins:50}, betti_curve{n_bins:50}) x 2 classifiers "
        "(svm_rbf, random_forest) = 12 configs; Takens d=3 tau=1; "
        "5-fold stratified CV seed 43; stratified subsample cap 200/class "
        "rng=default_rng(42) -> 714 samples, counts {0:200,1:200,2:96,"
        "3:194,4:24}; FULL-DATA distribution 2919/1767/96/194/24 (n=5000, "
        "majority 58.38%); metrics per fold: accuracy, balanced_accuracy "
        "(mean per-class recall), macro_f1 (mean per-class F1); 2 of 12 "
        "configs NaN = silhouette on weak_alpha (both classifiers, giotto "
        "edge case) -> marginals/vectorizer-CIs over the 10 VALID configs."
    )
    con.execute("INSERT INTO config_snapshot VALUES (1,?,?)",
                (protocol, time.strftime("%Y-%m-%dT%H:%M:%S")))

    rows = []  # per-config summaries
    for fname, fkw in FILS:
        for vname, vkw in VECS:
            for cname, ckw in CLFS:
                pipe = Pipeline([
                    ("fil", FiltrationFactory.create(fname, **fkw)),
                    ("vec", VectorizationFactory.create(vname, **vkw)),
                    ("clf", ClassifierFactory.create(cname, **ckw)),
                ])
                ts = time.perf_counter()
                fold_metrics = []  # (acc, balacc, macrof1) per fold
                status = "ok"
                for fold, (tr, te) in enumerate(CV.split(Xb, yb), start=1):
                    try:
                        pipe.fit(Xb[tr], yb[tr])
                        pred = pipe.predict(Xb[te])
                        fold_metrics.append((
                            float(accuracy_score(yb[te], pred)),
                            float(balanced_accuracy_score(yb[te], pred)),
                            float(f1_score(yb[te], pred, average="macro")),
                        ))
                    except Exception as exc:  # noqa: BLE001 — NaN vectorizer case
                        status = f"failed: {type(exc).__name__}: {exc}"
                        fold_metrics.append((None, None, None))
                accs = np.array([m[0] for m in fold_metrics], dtype=float)
                bals = np.array([m[1] for m in fold_metrics], dtype=float)
                f1s = np.array([m[2] for m in fold_metrics], dtype=float)
                for fold, (a, b, f) in enumerate(fold_metrics, start=1):
                    con.execute(
                        "INSERT INTO config_folds (filtration, vectorizer, "
                        "classifier, fold, accuracy, balanced_accuracy, "
                        "macro_f1, status) VALUES (?,?,?,?,?,?,?,?)",
                        (fname, vname, cname, fold,
                         None if a != a else a,
                         None if b != b else b,
                         None if f != f else f,
                         "ok" if status == "ok" else status))
                n_valid = int(np.isfinite(accs).sum())
                row = {
                    "filtration": fname, "vectorizer": vname,
                    "classifier": cname,
                    "mean_acc": float(np.nanmean(accs)) if n_valid else None,
                    "mean_balacc": float(np.nanmean(bals)) if n_valid else None,
                    "mean_macrof1": float(np.nanmean(f1s)) if n_valid else None,
                    "status": status, "n_valid_folds": n_valid,
                    "folds_acc": accs.tolist(), "folds_bal": bals.tolist(),
                    "folds_f1": f1s.tolist(),
                    "wall": time.perf_counter() - ts,
                }
                rows.append(row)
                con.execute(
                    "INSERT INTO config_summary (filtration, vectorizer, "
                    "classifier, n_valid_folds, mean_acc, mean_balacc, "
                    "mean_macrof1, status) VALUES (?,?,?,?,?,?,?,?)",
                    (fname, vname, cname, n_valid, row["mean_acc"],
                     row["mean_balacc"], row["mean_macrof1"], status))
                acc_s = "  nan" if row["mean_acc"] is None else f"{row['mean_acc']*100:6.2f}%"
                bal_s = "  nan" if row["mean_balacc"] is None else f"{row['mean_balacc']*100:6.2f}%"
                f1_s = "  nan" if row["mean_macrof1"] is None else f"{row['mean_macrof1']*100:6.2f}%"
                print(f"  {fname:14s} {vname:20s} {cname:12s} acc={acc_s} "
                      f"bal={bal_s} f1={f1_s}  [{time.perf_counter()-ts:.1f}s]")
    print(f"done in {time.perf_counter()-t0:.0f}s, {len(rows)} configs")

    valid = [r for r in rows if r["mean_acc"] is not None]
    print(f"\nvalid configs: {len(valid)}/12 (NaN excluded: "
          f"{[ (r['filtration'], r['vectorizer'], r['classifier']) for r in rows if r['mean_acc'] is None ]})")

    # ── stage-impact marginal ranges per metric (valid configs only) ──────
    for metric in ("mean_acc", "mean_balacc", "mean_macrof1"):
        from collections import defaultdict
        print(f"\n--- stage marginal ranges ({metric}) ---")
        for stage in ("filtration", "vectorizer", "classifier"):
            g = defaultdict(list)
            for r in valid:
                g[r[stage]].append(r[metric])
            means = {k: float(np.mean(v)) for k, v in g.items()}
            rng_pp = (max(means.values()) - min(means.values())) * 100
            print(f"  {stage:12s} range {rng_pp:6.2f}pp  " +
                  ", ".join(f"{k}={v*100:.2f}%" for k, v in
                            sorted(means.items(), key=lambda kv: -kv[1])))

    # ── per-vectorizer CI over valid config means ─────────────────────────
    print("\n--- per-vectorizer CI (over valid config means) ---")
    from collections import defaultdict
    g = defaultdict(list)
    for r in valid:
        g[r["vectorizer"]].append(r["mean_acc"])
    for vname in ("persistence_entropy", "silhouette", "betti_curve"):
        vals = np.array(g.get(vname, []))
        if len(vals) == 0:
            continue
        mean, sd = float(vals.mean()), float(vals.std(ddof=1)) if len(vals) > 1 else 0.0
        t = T_975.get(len(vals) - 1, 2.0)
        half = t * sd / np.sqrt(len(vals)) if len(vals) > 1 else 0.0
        con.execute(
            "INSERT INTO vectorizer_ci VALUES (?,?,?,?,?,?,?,?)",
            (vname, len(vals), mean, sd, mean - half, mean + half,
             float(vals.min()), float(vals.max())))
        print(f"  {vname:20s} n={len(vals)} mean={mean*100:6.2f}% "
              f"SD={sd*100:5.2f}pp tCI=[{(mean-half)*100:6.2f}, "
              f"{(mean+half)*100:6.2f}]% range=[{vals.min()*100:6.2f}, "
              f"{vals.max()*100:6.2f}]%")

    con.commit()
    con.close()
    print(f"\nwrote {DB_PATH}")


if __name__ == "__main__":
    sys.exit(main())
