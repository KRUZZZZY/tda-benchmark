#!/usr/bin/env python3
"""Expansion #9 — analysis of data/tda/h2_alpha_sweep.db (H2 homology).

Reads the H2 sweep DB produced by scripts/sweep_h2_alpha.py (gudhi true
Alpha complex, homology_dimensions=[0,1,2], on sphere/torus noise0 +
noise30) and reports:

  * Empirical beta2 check (read-only, cheap): recompute H2 generator
    counts on a few sample clouds from the shipped arrays with
    gudhi.AlphaComplex — the sphere should show beta2=0 and the torus
    beta2=1 in the clean data. This grounds the "beta2 is the
    distinguishing feature" claim before the accuracy numbers.
  * Accuracy by dataset x vectorizer x classifier (filtration is fixed
    = gudhi_alpha_h2 across the whole DB).
  * Stage marginal ranges: dataset (noise level) and vectorizer levels
    over per-config mean accuracies, in pp.
  * Beta2-relevant comparison: clean (noise0) sphere-vs-torus
    classification accuracy — if H2 features carry the signal, clean
    separation should be near-perfect and survive into noise30.
  * Any failed/missing cells (finished_at IS NULL) are listed.

Outputs (all additive): /tmp/tda_h2_report.md (full report),
data/tda/h2_alpha_summary.csv (per-config accuracy), and a printed
table.

Usage:
  cd /home/kruzzzzy/Documents/AI_KOS_PROJECT
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_h2.py

Expected runtime: ~1-2 min (no sweep; only a handful of alpha complexes).
Additive-only: reads the DB read-only; writes a CSV + /tmp report.
"""
from __future__ import annotations

import csv
import sqlite3
import statistics as st
from collections import defaultdict
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent  # AI_KOS_PROJECT
DATA_DIR = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA_DIR / "h2_alpha_sweep.db"
OUT_CSV = DATA_DIR / "h2_alpha_summary.csv"
OUT_MD = Path("/tmp/tda_h2_report.md")

CLEAN_X = DATA_DIR / "synthetic" / "sphere_torus_noise0_X.npy"
CLEAN_Y = DATA_DIR / "synthetic" / "sphere_torus_noise0_y.npy"
N_CHECK_CLOUDS = 8  # per class, cheap


def empirical_beta2() -> dict:
    """beta2 generator counts on the clean arrays (read-only, ~seconds)."""
    import gudhi
    X = np.load(CLEAN_X)
    y = np.load(CLEAN_Y)
    counts = {"sphere": [], "torus": []}
    for cls_idx, label in [(0, "sphere"), (1, "torus")]:
        idx = np.where(y == cls_idx)[0][:N_CHECK_CLOUDS]
        for i in idx:
            ac = gudhi.AlphaComplex(points=X[i])
            st_ = ac.create_simplex_tree()
            pers = st_.persistence()
            n_h2 = sum(1 for d, _ in pers if d == 2)
            counts[label].append(n_h2)
    out = {}
    for label, vals in counts.items():
        out[label] = {"n_clouds": len(vals), "h2_counts": vals,
                      "mean_beta2": float(np.mean(vals))}
    return out


def per_config_accs() -> tuple[list[dict], list[tuple]]:
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    rows = conn.execute(
        """SELECT r.dataset, r.filtration, r.vectorizer, r.classifier,
                  AVG(f.accuracy) AS acc, r.wall_time_s
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL
           GROUP BY r.run_id
           ORDER BY r.dataset, r.vectorizer, r.classifier""").fetchall()
    unfinished = conn.execute(
        "SELECT dataset, vectorizer, classifier FROM runs "
        "WHERE finished_at IS NULL").fetchall()
    conn.close()
    cfg = [{"dataset": r[0], "filtration": r[1], "vectorizer": r[2],
            "classifier": r[3], "acc": r[4], "wall_time_s": r[5]}
           for r in rows]
    return cfg, unfinished


def marginals(cfg: list[dict], stage: str) -> dict:
    d: dict[str, list[float]] = defaultdict(list)
    for c in cfg:
        d[c[stage]].append(c["acc"])
    means = {k: st.mean(v) for k, v in d.items()}
    return {"levels": means,
            "range_pp": (max(means.values()) - min(means.values())) * 100.0}


def main() -> None:
    if not DB_PATH.exists():
        print(f"missing {DB_PATH} — run scripts/sweep_h2_alpha.py first")
        return
    cfg, unfinished = per_config_accs()
    report = ["# Expansion #9 — H2 homology (gudhi true Alpha, dims 0-2)\n"]
    report.append(f"DB: `{DB_PATH}` ({len(cfg)} finished per-config rows, "
                  f"filtration fixed = gudhi_alpha_h2)\n")

    # empirical beta2 grounding
    report.append("\n## Empirical beta2 on the clean arrays (noise0)\n")
    try:
        b2 = empirical_beta2()
        for label, info in b2.items():
            report.append(f"- {label}: beta2 counts {info['h2_counts']} "
                          f"(mean {info['mean_beta2']:.2f})")
    except Exception as exc:  # noqa: BLE001 — report shouldn't die on this
        report.append(f"- beta2 check failed: {type(exc).__name__}: {exc}")
    report.append("\nExpectation: sphere beta2 = 0, torus beta2 = 1 in "
                  "clean data; the H2 arm should separate them cleanly.\n")

    # accuracy table
    report.append("\n## Per-config mean accuracy\n")
    report.append("| dataset | filtration | vectorizer | classifier | acc | wall_s |")
    report.append("|---|---|---|---|---|---|")
    for c in sorted(cfg, key=lambda c: (-c["acc"], c["dataset"])):
        report.append(f"| {c['dataset']} | {c['filtration']} | {c['vectorizer']} | "
                      f"{c['classifier']} | {c['acc']*100:.2f}% | "
                      f"{c['wall_time_s']:.1f} |")

    # stage marginals
    report.append("\n## Stage marginal ranges (pp)\n")
    for stage in ["dataset", "vectorizer", "classifier"]:
        m = marginals(cfg, stage)
        lev = ", ".join(f"{k} {v*100:.2f}%" for k, v in
                        sorted(m["levels"].items(), key=lambda x: -x[1]))
        report.append(f"- **{stage}** range {m['range_pp']:.2f} pp: {lev}")

    # beta2-relevant headline comparison
    clean = [c for c in cfg if c["dataset"] == "sphere_torus_n0"]
    noisy = [c for c in cfg if c["dataset"] == "sphere_torus_n30"]
    if clean:
        mean_clean = st.mean(c["acc"] for c in clean)
        report.append(f"\n## Beta2-relevant comparison\n"
                      f"- clean (noise0) mean accuracy across all 6 configs: "
                      f"{mean_clean*100:.2f}% (sphere beta2=0 vs torus beta2=1)\n")
    if noisy:
        mean_noisy = st.mean(c["acc"] for c in noisy)
        report.append(f"- noisy (noise30) mean accuracy across all 6 configs: "
                      f"{mean_noisy*100:.2f}% (does the beta2 signal survive?)\n")

    if unfinished:
        report.append("\n## Unfinished / failed cells\n")
        for u in unfinished:
            report.append(f"- {u[0]} | {u[1]} | {u[2]} (finished_at IS NULL)")

    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["dataset", "filtration", "vectorizer",
                                           "classifier", "acc", "wall_time_s"])
        w.writeheader()
        for c in sorted(cfg, key=lambda c: -c["acc"]):
            w.writerow(c)

    text = "\n".join(report)
    OUT_MD.write_text(text)
    print(text)
    print(f"\nwrote {OUT_CSV} and {OUT_MD}")


if __name__ == "__main__":
    main()
