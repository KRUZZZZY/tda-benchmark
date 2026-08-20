#!/usr/bin/env python3
"""A7 — Cubical-on-Takens-grid shuffle ablation (round-2 finding M6).

The paper's top ECG200 configs are cubical on Takens-embedded (200, 94, 3)
arrays — executed as 200 greyscale 94x3 images (the disclosed artifact). This
ablation destroys the grid structure while keeping the exact same multiset of
values per sample:
  * row_shuffle  — independently permute the 94 rows of each sample's grid
  * col_shuffle  — independently permute the 3 columns of each sample's grid
(labels intact; each sample shuffled independently; fixed rng seed).

Re-runs ALL 28 cubical configs from the executed sweep (7 vectorizers x 4
classifiers, hyperparameters from expanded_config.yaml) on each variant with
the paper's exact CV folds (StratifiedKFold(5, shuffle=True, random_state=43)).
The unshuffled arm must reproduce expanded_results.db (ground truth: e.g.
silhouette+RF 83.0%, persistence_image+RF 82.0%, betti_curve+svm_rbf 80.5%).

Verdict rule: if accuracy collapses under either shuffle, the cubical signal is
grid-structure-driven; if it survives, the topology is encoded redundantly.

Output: data/tda/cubical_shuffle.db (table ablation: variant, filtration,
vectorizer, classifier, fold, accuracy; table ground_truth: same schema from
expanded_results.db for comparison).

Additive-only: creates only this script + cubical_shuffle.db.
"""
from __future__ import annotations

import sqlite3
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from itertools import product
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent          # projects/tda-benchmark
PROJECT_ROOT = REPO.parent.parent                      # AI_KOS_PROJECT
sys.path.insert(0, str(PROJECT_ROOT / "projects"))     # symlink tda_benchmark -> tda-benchmark

from tda_benchmark.factories import ClassifierFactory, FiltrationFactory, VectorizationFactory  # noqa: E402

DATA_DIR = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA_DIR / "cubical_shuffle.db"
SRC_DB = DATA_DIR / "expanded_results.db"

VARIANTS = ["unshuffled", "row_shuffle", "col_shuffle"]
SHUFFLE_SEED = 2026

# The 7 vectorizers x 4 classifiers of the executed cubical arm (expanded_config.yaml)
VECS = [
    ("persistence_image", {"sigma": 0.1, "n_bins": 20}),
    ("persistence_landscape", {"n_layers": 3, "n_bins": 50}),
    ("betti_curve", {"n_bins": 50}),
    ("silhouette", {"n_bins": 50}),
    ("persistence_entropy", {"normalize": True}),
    ("amplitude", {"metric": "bottleneck"}),
    ("persistence_statistics", {}),
]
CLFS = [
    ("svm_rbf", {}), ("random_forest", {}), ("logistic", {}), ("svm_linear", {}),
]
CV_FOLDS = 5
RANDOM_STATE = 43  # random_seed 42 + rep 1 (paper's executed folds)
N_JOBS = 1  # serial — single-CPU constraint (2026-08-21, user directive)

CONFIGS = list(product(VECS, CLFS))


def load_and_embed() -> tuple[np.ndarray, np.ndarray]:
    """Load ECG200 and Takens-embed d=3, tau=1 — bit-identical to runner.py."""
    X = np.load(DATA_DIR / "ucr" / "ecg200_X.npy")
    y = np.load(DATA_DIR / "ucr" / "ecg200_y.npy")
    dim, delay = 3, 1
    stride = (dim - 1) * delay
    n_points = X.shape[1] - stride
    embedded = np.zeros((X.shape[0], n_points, dim), dtype=X.dtype)
    for d in range(dim):
        embedded[:, :, d] = X[:, d * delay : d * delay + n_points]
    return embedded, y


def make_variants(emb: np.ndarray) -> dict[str, np.ndarray]:
    """Build the three grid variants: original, row-shuffled, col-shuffled.

    Each sample is shuffled independently; only within-sample permutations are
    applied, so every sample keeps its label and its exact multiset of 94x3
    values. Row shuffle permutes the 94 time-window rows; col shuffle permutes
    the 3 Takens coordinates.
    """
    rng = np.random.default_rng(SHUFFLE_SEED)
    row = emb.copy()
    col = emb.copy()
    n, r, c = emb.shape
    for i in range(n):
        row[i] = emb[i][rng.permutation(r), :]
        col[i] = emb[i][:, rng.permutation(c)]
    return {"unshuffled": emb, "row_shuffle": row, "col_shuffle": col}


def run_one(args: tuple) -> dict:
    variant, (vec_name, vec_kw), (clf_name, clf_kw), X, y = args
    from sklearn.model_selection import StratifiedKFold, cross_validate
    from sklearn.pipeline import Pipeline

    pipe = Pipeline([
        ("filtration", FiltrationFactory.create("cubical", homology_dimensions=[0, 1])),
        ("vectorizer", VectorizationFactory.create(vec_name, **vec_kw)),
        ("classifier", ClassifierFactory.create(clf_name, **clf_kw)),
    ])
    cv = StratifiedKFold(n_splits=CV_FOLDS, shuffle=True, random_state=RANDOM_STATE)
    scores = cross_validate(pipe, X, y, cv=cv, scoring="accuracy", n_jobs=1)
    # single-string scoring -> key is "test_score" (not test_accuracy); fixed 2026-08-21
    return {
        "variant": variant, "vectorizer": vec_name, "classifier": clf_name,
        "folds": [float(s) for s in scores["test_score"]],
        "acc": float(scores["test_score"].mean()),
    }


def main() -> None:
    print("A7 cubical shuffle ablation: loading ECG200 + Takens embedding (200, 94, 3)...")
    emb, y = load_and_embed()
    print(f"  embedded: {emb.shape}; variants: {VARIANTS}; "
          f"configs: {len(CONFIGS)} x 3 = {len(CONFIGS)*3} runs")

    variants = make_variants(emb)

    jobs = []
    for variant, (vec, clf) in product(VARIANTS, CONFIGS):
        jobs.append((variant, vec, clf, variants[variant], y))

    results = []
    t0 = time.perf_counter()
    ok = fail = 0
    try:
        with ProcessPoolExecutor(max_workers=N_JOBS) as ex:
            for i, res in enumerate(ex.map(run_one, jobs), 1):
                if "folds" in res:
                    ok += 1
                    results.append(res)
                    print(f"[{i}/{len(jobs)}] {res['variant']:11s} {res['vectorizer']:22s} "
                          f"{res['classifier']:12s} {res['acc']*100:5.2f}%")
                else:
                    fail += 1
                    print(f"[{i}/{len(jobs)}] FAIL {res}")
    except Exception as exc:
        print(f"ProcessPoolExecutor failed ({exc}); falling back to serial")
        for i, args in enumerate(jobs, 1):
            res = run_one(args)
            if "folds" in res:
                ok += 1
                results.append(res)
                print(f"[{i}/{len(jobs)}] {res['variant']:11s} {res['vectorizer']:22s} "
                      f"{res['classifier']:12s} {res['acc']*100:5.2f}%")
            else:
                fail += 1
                print(f"[{i}/{len(jobs)}] FAIL {res}")
    print(f"\nRuns done in {time.perf_counter()-t0:.0f}s: {ok} ok, {fail} failed")

    # ── write DB ──────────────────────────────────────────────────────────
    conn = sqlite3.connect(str(DB_PATH))
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS ablation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant TEXT NOT NULL,
            filtration TEXT NOT NULL,
            vectorizer TEXT NOT NULL,
            classifier TEXT NOT NULL,
            fold INTEGER NOT NULL,
            accuracy REAL
        );
        CREATE TABLE IF NOT EXISTS ground_truth (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            variant TEXT NOT NULL,
            vectorizer TEXT NOT NULL,
            classifier TEXT NOT NULL,
            fold INTEGER NOT NULL,
            accuracy REAL
        );
        CREATE INDEX IF NOT EXISTS idx_abl_variant ON ablation(variant);
    """)
    for r in results:
        for fi, acc in enumerate(r["folds"], 1):
            conn.execute(
                "INSERT INTO ablation (variant, filtration, vectorizer, classifier, fold, accuracy) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (r["variant"], "cubical", r["vectorizer"], r["classifier"], fi, acc),
            )
    # ground truth: unshuffled per-fold accs from expanded_results.db (cubical arm)
    src = sqlite3.connect(str(SRC_DB))
    gt = src.execute("""
        SELECT r.vectorizer, r.classifier, f.fold, f.accuracy
        FROM runs r JOIN fold_results f ON r.run_id = f.run_id
        WHERE r.dataset = 'ecg200' AND r.filtration = 'cubical'
          AND r.finished_at IS NOT NULL
        ORDER BY r.vectorizer, r.classifier, f.fold
    """).fetchall()
    src.close()
    for vec, clf, fold, acc in gt:
        conn.execute(
            "INSERT INTO ground_truth (variant, vectorizer, classifier, fold, accuracy) "
            "VALUES ('unshuffled', ?, ?, ?, ?)", (vec, clf, fold, acc),
        )
    conn.commit()
    conn.close()
    print(f"wrote {DB_PATH}: {len(results)} runs x 5 folds in ablation, "
          f"{len(gt)} rows in ground_truth")


if __name__ == "__main__":
    main()
