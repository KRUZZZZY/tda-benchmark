#!/usr/bin/env python3
"""B2 (#4) — stage-capable 9-dataset panel analysis.

Reads data/tda/panel_stagecapable.db (2 filtrations x 4 vectorizers x 2
classifiers on 7 time-series + 2 image datasets, 5-fold CV seed 42 rep=1) and
reports, PER DATASET:

  * per-config mean accuracy (AVG over folds),
  * vectorizer stage-level means (mean of per-config means over filtration x
    classifier), and the vectorizer RANGE (max - min, pp),
  * filtration stage-level means (mean over vectorizer x classifier), and the
    filtration RANGE (pp),
  * the distribution of vectorizer-range vs filtration-range across the 9
    datasets (the B2 deliverable).

Both stages now have >1 alternative per dataset, so the ranges are on equal
footing. All numbers are re-derived from the DB (finished_at IS NOT NULL;
per-config = AVG(f.accuracy) per run_id; stage-level mean = two nesting
levels). Additive-only, read-only.

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_panel_stagecapable.py
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

DB = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda/panel_stagecapable.db")

TS_DATASETS = ["ecg200", "ecg5000", "FordA", "FordB", "Wafer",
               "ElectricDevices", "HandOutlines"]
IMG_DATASETS = ["mnist10", "fmnist10"]
ALL_DATASETS = TS_DATASETS + IMG_DATASETS


def per_config_means(conn, dataset: str) -> dict[tuple[str, str, str], float]:
    """{(filtration, vectorizer, classifier): mean accuracy %} — one row per run."""
    rows = conn.execute(
        "SELECT r.filtration, r.vectorizer, r.classifier, AVG(f.accuracy) * 100 "
        "FROM runs r JOIN fold_results f ON f.run_id = r.run_id "
        "WHERE r.dataset = ? AND r.finished_at IS NOT NULL "
        "GROUP BY r.run_id", (dataset,)).fetchall()
    return {(r[0], r[1], r[2]): r[3] for r in rows}


def stage_level_mean(pc: dict, stage: str, level: str) -> float:
    """Mean over per-config means at a fixed stage level (two nesting levels)."""
    vals = [m for (f, v, c), m in pc.items()
            if (f == level if stage == "filtration" else
                v == level if stage == "vectorizer" else c == level)]
    return sum(vals) / len(vals)


def main() -> None:
    conn = sqlite3.connect(str(DB))
    # completion sanity: every dataset must have a full matrix
    for ds in ALL_DATASETS:
        n_fin = conn.execute(
            "SELECT COUNT(*) FROM runs WHERE dataset=? AND finished_at IS NOT NULL",
            (ds,)).fetchone()[0]
        expected = 16  # 2 fil x 4 vec x 2 clf
        status = "OK" if n_fin == expected else f"MISSING ({n_fin}/{expected})"
        print(f"[completion] {ds:<18} {status}")
    print()

    print(f"{'dataset':<18}{'vec range':>10}{'fil range':>10}{'winner':>12}")
    print("-" * 52)
    vec_ranges, fil_ranges = {}, {}
    for ds in ALL_DATASETS:
        pc = per_config_means(conn, ds)
        fil_levels = sorted({f for f, _, _ in pc})
        vec_levels = sorted({v for _, v, _ in pc})
        vec_means = {v: stage_level_mean(pc, "vectorizer", v) for v in vec_levels}
        fil_means = {f: stage_level_mean(pc, "filtration", f) for f in fil_levels}
        vr = max(vec_means.values()) - min(vec_means.values())
        fr = max(fil_means.values()) - min(fil_means.values())
        vec_ranges[ds], fil_ranges[ds] = vr, fr
        winner = "vec" if vr > fr else ("fil" if fr > vr else "tie")
        print(f"{ds:<18}{vr:>10.2f}{fr:>10.2f}{winner:>12}")
        for f in fil_levels:
            print(f"    fil {f:<20} {fil_means[f]:.2f}")
        for v in vec_levels:
            print(f"    vec {v:<20} {vec_means[v]:.2f}")
    print("-" * 52)
    print(f"{'MEDIAN':<18}{sorted(vec_ranges.values())[4]:>10.2f}"
          f"{sorted(fil_ranges.values())[4]:>10.2f}")
    print(f"vec range > fil range on {sum(1 for d in ALL_DATASETS if vec_ranges[d] > fil_ranges[d])}/9 datasets")
    print(f"fil range > vec range on {sum(1 for d in ALL_DATASETS if fil_ranges[d] > vec_ranges[d])}/9 datasets")
    conn.close()


if __name__ == "__main__":
    main()
