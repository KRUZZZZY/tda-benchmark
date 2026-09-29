#!/usr/bin/env python3
"""B4 (#12) — FPS vs uniform-random subsampling ablation analysis.

Reads data/tda/fps_ablation.db (arms: sphere_torus_{noise0,noise30}_{fps,uniform}{50,15}
x {vietoris_rips, weighted_rips} x {betti_curve, persistence_landscape} x
{random_forest, svm_rbf}, 5-fold CV seed 42 rep=1) and reports, per (noise, k):

  * mean accuracy over the 8 configs for the FPS arm vs the uniform arm,
  * per-config detail table,
  * the FPS - uniform delta (pp) per (noise, k) and overall.

Closes the paper's limitation #1 (uniform-random subsampling vs FPS) on the
synthetic point clouds. All numbers re-derived from the DB (finished_at IS
NOT NULL; per-config = AVG(f.accuracy) per run_id). Additive-only, read-only.

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_fps_ablation.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda/fps_ablation.db")

ARMS = ["fps", "uniform"]
NOISES = ["noise0", "noise30"]
KS = [50, 15]


def per_config_means(conn, dataset: str) -> dict[tuple[str, str, str], float]:
    rows = conn.execute(
        "SELECT r.filtration, r.vectorizer, r.classifier, AVG(f.accuracy) * 100 "
        "FROM runs r JOIN fold_results f ON f.run_id = r.run_id "
        "WHERE r.dataset = ? AND r.finished_at IS NOT NULL "
        "GROUP BY r.run_id", (dataset,)).fetchall()
    return {(r[0], r[1], r[2]): r[3] for r in rows}


def main() -> None:
    conn = sqlite3.connect(str(DB))
    print(f"{'dataset':<42}{'arm':<9}{'mean acc':>9}{'n cfg':>6}")
    print("-" * 70)
    results = {}
    for noise in NOISES:
        for k in KS:
            for arm in ARMS:
                ds = f"sphere_torus_{noise}_{arm}{k}"
                pc = per_config_means(conn, ds)
                mean = sum(pc.values()) / len(pc) if pc else float("nan")
                results[(noise, k, arm)] = mean
                print(f"{ds:<42}{arm:<9}{mean:>9.2f}{len(pc):>6}")
    print("-" * 70)
    for noise in NOISES:
        for k in KS:
            d = results[(noise, k, "fps")] - results[(noise, k, "uniform")]
            print(f"{noise} k={k}: FPS - uniform = {d:+.2f} pp")
    d_all = (sum(results[(n, k, "fps")] for n in NOISES for k in KS) -
             sum(results[(n, k, "uniform")] for n in NOISES for k in KS)) / 4
    print(f"overall FPS - uniform = {d_all:+.2f} pp")
    conn.close()


if __name__ == "__main__":
    main()
