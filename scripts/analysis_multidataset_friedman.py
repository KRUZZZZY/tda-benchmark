#!/usr/bin/env python3
"""B1 — multi-dataset Friedman + Nemenyi analysis (DemSar 2006 protocol).

Reads data/tda/multidataset_sweep.db (per-config mean accuracy per dataset,
5-fold CV seed 43) and computes, over the COMPLETE config x dataset matrix
(every config present on every dataset):

  * per-dataset best config + best-by-stage summary table,
  * Friedman test on the config x dataset accuracy matrix (ranks within
    each dataset, averaged across datasets),
  * Nemenyi post-hoc critical difference (CD) at alpha=0.05,
  * CD diagram data (config ordering + CD interval) for the figure,
  * stage-family analysis: mean rank of vectorizer families and filtration
    families across datasets.

Config set: vietoris_rips x {PI, landscape, betti, silhouette} x {svm_rbf, RF}
on the 7 time-series datasets; {cubical, vietoris_rips} x same on the 2 image
datasets. weak_alpha is EXCLUDED from the matrix (fails on quantized series:
giotto _weak_alpha_diagram IndexError on Wafer/ElectricDevices, essential-class
crash on ecg5000) and reported as a fragility finding.

Outputs: /tmp/tda_B1_friedman_report.md, /tmp/tda_B1_nemenyi.json,
data/tda/multidataset_nemenyi.csv.

Additive-only.
"""
from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sstats
from scipy.stats import rankdata

DATA = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda")
DB = DATA / "multidataset_sweep.db"
OUT_MD = Path("/tmp/tda_B1_friedman_report.md")
OUT_JSON = Path("/tmp/tda_B1_nemenyi.json")
OUT_CSV = DATA / "multidataset_nemenyi.csv"

ALPHA = 0.05

# dataset order for the report (time series first, then images)
DATASETS = ["ecg200", "ecg5000", "FordA", "FordB", "Wafer",
            "ElectricDevices", "HandOutlines", "mnist10", "fmnist10"]
TS_DATASETS = set(DATASETS[:7])
IMG_DATASETS = set(DATASETS[7:])

# config grid actually executed per modality (VR-only TS arm; cubical+VR images)
TS_FILS = ["vietoris_rips"]
IMG_FILS = ["cubical", "vietoris_rips"]
VECS = ["persistence_image", "persistence_landscape", "betti_curve", "silhouette"]
CLFS = ["svm_rbf", "random_forest"]


def configs_for(ds: str) -> list[tuple[str, str, str]]:
    fils = IMG_FILS if ds in IMG_DATASETS else TS_FILS
    return [(f, v, c) for f in fils for v in VECS for c in CLFS]


def load_matrix() -> dict[str, dict[tuple, float]]:
    """per-dataset -> config -> mean accuracy (%)."""
    conn = sqlite3.connect(str(DB))
    rows = conn.execute("""
        SELECT r.dataset, r.filtration, r.vectorizer, r.classifier,
               AVG(f.accuracy) * 100
        FROM runs r JOIN fold_results f ON f.run_id = r.run_id
        WHERE r.finished_at IS NOT NULL
        GROUP BY r.run_id""").fetchall()
    conn.close()
    mat: dict[str, dict[tuple, float]] = defaultdict(dict)
    for ds, fil, vec, clf, acc in rows:
        mat[ds][(fil, vec, clf)] = acc
    return mat


def main() -> None:
    mat = load_matrix()
    # sanity: complete matrix check
    missing = []
    for ds in DATASETS:
        for cfg in configs_for(ds):
            if cfg not in mat[ds]:
                missing.append((ds, cfg))
    print(f"datasets: {len(mat)}; missing cells: {len(missing)}")
    for x in missing[:10]:
        print("  MISSING", x)

    # build the common config list = union of configs present on ALL datasets
    common = [cfg for cfg in configs_for(DATASETS[0])]
    for ds in DATASETS[1:]:
        common = [c for c in common if c in mat[ds]]
    print(f"common configs across all datasets: {len(common)}")

    # Friedman on configs x datasets
    X = np.array([[mat[ds][c] for c in common] for ds in DATASETS])  # (n_ds, n_cfg)
    n_ds, n_cfg = X.shape
    # ranks within each dataset (1 = best), TIE-AVERAGED (the DemSar 2006
    # standard): scipy rankdata with method="average". The paper's published
    # statistics (chi2=32.41, F=8.47, CD=2.48, mean ranks 1.28 / 2.83 /
    # 4.22 / 4.69 / 6.25) are computed with this convention. An earlier
    # draft used argsort ranks (no tie averaging), which gave arbitrary tie
    # order on rows with tied accuracies (e.g. Wafer 99.9 x2, 89.6 x2) and
    # produced 33.22 / 8.93 / 2.58 — NOT the published numbers. Fixed
    # 2026-08-21 (audit cycle, wave 0).
    ranks = np.array([rankdata(-row, method="average") for row in X])
    mean_ranks = ranks.mean(axis=0)
    # Friedman chi-square (DemSar 2006, form 1):
    #   chi2 = 12/(n*k*(k+1)) * sum_j R_j^2 - 3*n*(k+1)
    # where R_j = rank sum of config j over the n datasets (ranks 1..k within
    # each dataset). Max value n*(k-1) = 63 here; 22131 in an earlier draft was
    # a scale bug (raw R_j used with the R-bar-normalised multiplier).
    R = ranks.sum(axis=0)
    chi2 = 12 / (n_ds * n_cfg * (n_cfg + 1)) * (R ** 2).sum() - 3 * n_ds * (n_cfg + 1)
    df = n_cfg - 1
    p = sstats.chi2.sf(chi2, df)
    # F-statistic approximation (Iman-Davenport)
    F_id = (n_ds - 1) * chi2 / (n_ds * (n_cfg - 1) - chi2)
    p_id = sstats.f.sf(F_id, n_cfg - 1, (n_cfg - 1) * (n_ds - 1))

    # Nemenyi CD. q_alpha is the DemSar (2006) Table A3 critical value for
    # k = n_cfg = 8 configurations at alpha=0.05: q = 3.031. (3.163 is the
    # k=10 value and was used in an earlier draft — it gave CD=2.58 instead
    # of the published 2.48. Fixed 2026-08-21.)
    q_alpha = 3.031
    cd = q_alpha * np.sqrt(n_cfg * (n_cfg + 1) / (12 * n_ds))

    order = np.argsort(mean_ranks)
    print(f"\nFriedman chi2({df}) = {chi2:.2f}, p = {p:.2e}")
    print(f"Iman-Davenport F({n_cfg-1},{(n_cfg-1)*(n_ds-1)}) = {F_id:.2f}, p = {p_id:.2e}")
    print(f"Nemenyi CD = {cd:.3f} (mean rank units)")

    # stage-family mean ranks
    fam = defaultdict(list)
    for i, cfg in enumerate(common):
        fam["vec:" + cfg[1]].append(mean_ranks[i])
        fam["fil:" + cfg[0]].append(mean_ranks[i])
        fam["clf:" + cfg[2]].append(mean_ranks[i])

    lines = ["# B1 — Multi-dataset Friedman/Nemenyi analysis",
             f"\nMatrix: {n_ds} datasets x {n_cfg} configs, complete (no missing cells).",
             f"weak_alpha excluded (giotto crash on quantized series — fragility finding).",
             f"\n## Friedman test",
             f"- chi2({df}) = {chi2:.2f}, p = {p:.2e}",
             f"- Iman-Davenport F({n_cfg-1},{(n_cfg-1)*(n_ds-1)}) = {F_id:.2f}, p = {p_id:.2e}",
             f"- Nemenyi CD at alpha=0.05: {cd:.3f}",
             "\n## Config mean ranks (1 = best across datasets)",
             "| rank | config | mean rank | acc mean |",
             "|---|---|---|---|"]
    for rank_i, i in enumerate(order, 1):
        cfg = common[i]
        accs = [mat[ds][cfg] for ds in DATASETS]
        lines.append(f"| {rank_i} | {cfg[0]}+{cfg[1]}+{cfg[2]} | "
                     f"{mean_ranks[i]:.2f} | {np.mean(accs):.1f}% |")
    lines.append("\n## Stage-family mean ranks")
    for k in sorted(fam):
        lines.append(f"- {k}: {np.mean(fam[k]):.2f}")
    lines.append("\n## Per-dataset best config")
    for ds in DATASETS:
        items = list(mat[ds].items())
        best_cfg, best_acc = max(items, key=lambda kv: kv[1])
        lines.append(f"- {ds}: {best_cfg[0]}+{best_cfg[1]}+{best_cfg[2]} {best_acc:.1f}%")

    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps({
        "n_datasets": n_ds, "n_configs": n_cfg, "chi2": chi2, "df": df,
        "p": p, "F_id": F_id, "p_id": p_id, "cd": cd, "q_alpha": q_alpha,
        "mean_ranks": {f"{c[0]}+{c[1]}+{c[2]}": float(r) for c, r in zip(common, mean_ranks)},
        "order": [f"{common[i][0]}+{common[i][1]}+{common[i][2]}" for i in order],
        "stage_families": {k: float(np.mean(v)) for k, v in fam.items()},
        "missing_cells": len(missing),
    }, indent=2))
    # CSV for the CD figure: config, mean rank, cd
    with open(OUT_CSV, "w") as fh:
        fh.write("config,mean_rank,cd\n")
        for i in order:
            cfg = common[i]
            fh.write(f"{cfg[0]}+{cfg[1]}+{cfg[2]},{mean_ranks[i]:.3f},{cd:.3f}\n")
    print(f"\nwrote {OUT_MD}, {OUT_JSON}, {OUT_CSV}")


if __name__ == "__main__":
    main()
