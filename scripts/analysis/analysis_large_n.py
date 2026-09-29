#!/usr/bin/env python3
"""B5 (#7b) — Sparse Rips at its design point (large n) analysis.

Reads data/tda/large_n_sweep.db (sphere_torus_n{1000,3000}: sparse_rips at
both n, vietoris_rips control at n=1000 only; x {betti_curve,
persistence_landscape} x {random_forest, svm_rbf}, 5-fold CV seed 42 rep=1)
and reports per (n, filtration):

  * per-config mean accuracy (AVG over folds),
  * mean over the 4 configs per (n, filtration) arm,
  * sparse vs VR delta at n=1000,
  * Sparse Rips accuracy at n=3000 (its design point).

All numbers re-derived from the DB (finished_at IS NOT NULL; per-config =
AVG(f.accuracy) per run_id). Additive-only, read-only.

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_large_n.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda/large_n_sweep.db")


def per_config_means(conn, dataset: str) -> dict[tuple[str, str, str], float]:
    rows = conn.execute(
        "SELECT r.filtration, r.vectorizer, r.classifier, AVG(f.accuracy) * 100 "
        "FROM runs r JOIN fold_results f ON f.run_id = r.run_id "
        "WHERE r.dataset = ? AND r.finished_at IS NOT NULL "
        "GROUP BY r.run_id", (dataset,)).fetchall()
    return {(r[0], r[1], r[2]): r[3] for r in rows}


def main() -> None:
    conn = sqlite3.connect(str(DB))
    for n in (1000, 3000):
        ds = f"sphere_torus_n{n}"
        pc = per_config_means(conn, ds)
        print(f"== {ds} ({len(pc)} configs) ==")
        for (fil, vec, clf), m in sorted(pc.items()):
            print(f"  {fil:<14}{vec:<24}{clf:<14}{m:>8.2f}")
        by_fil: dict[str, list[float]] = {}
        for (fil, _, _), m in pc.items():
            by_fil.setdefault(fil, []).append(m)
        for fil, vals in by_fil.items():
            print(f"  -> {fil}: mean over {len(vals)} configs = "
                  f"{sum(vals)/len(vals):.2f}%")
        if n == 1000 and "vietoris_rips" in by_fil and "sparse_rips" in by_fil:
            d = sum(by_fil["vietoris_rips"])/len(by_fil["vietoris_rips"]) - \
                sum(by_fil["sparse_rips"])/len(by_fil["sparse_rips"])
            print(f"  -> n=1000 VR - sparse = {d:+.2f} pp")
        print()
    conn.close()


if __name__ == "__main__":
    main()
