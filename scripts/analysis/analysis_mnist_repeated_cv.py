#!/usr/bin/env python3
"""Reviewer-revision analysis A3: MNIST 0/1 repeated-CV statistics + ANOVA.

Reads data/tda/mnist_repeated_cv.db (56 configs = 2 filtrations x 7
vectorizers x 4 classifiers, 5 reps x 5 folds = 280 runs) and computes:
  * per-repetition stage marginal ranges (vec/fil: range of stage-level means
    of per-config mean accuracies, in pp),
  * repeated-measures CIs (mean +/- t_{0.975, R-1} * SD/sqrt(R), R = 5 reps)
    and Nadeau-Bengio corrected CIs (SE^2 = (1/R + n2/n1) * s^2_R;
    MNIST: 400 samples, 5-fold => n2/n1 = 80/320 = 0.25) for each stage,
  * pooled marginals over all reps,
  * 3-way ANOVA on per-config means (mean over the 25 fold accuracies) ->
    classic eta^2 per stage; fold-level ANOVA over all 25 folds per config,
  * comparison vs the single-split bootstrap CIs [2.00, 6.14] (vec) /
    [0.74, 2.69] (fil) and the expanded_results.db marginals (3.22pp / 1.65pp).

Outputs (additive): /tmp/tda_A3_mnist_report.md and JSON.

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_mnist_repeated_cv.py
"""

from __future__ import annotations

import json
import math
import sqlite3
import statistics as st
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats as sstats

DATA_DIR = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda")
DB = DATA_DIR / "mnist_repeated_cv.db"
OUT_MD = Path("/tmp/tda_A3_mnist_report.md")
OUT_JSON = Path("/tmp/tda_A3_mnist_stats.json")

N2_N1 = 80.0 / 320.0   # MNIST 400 samples, 5-fold: 80 test / 320 train
REPS = range(1, 6)


def load_rows() -> list[tuple]:
    conn = sqlite3.connect(str(DB))
    q = """SELECT r.repetition, r.filtration, r.vectorizer, r.classifier,
                  AVG(f.accuracy)
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL
           GROUP BY r.run_id"""
    rows = conn.execute(q).fetchall()
    conn.close()
    return rows


def stage_range_for_rep(rows: list[tuple], rep: int, idx: int) -> float:
    d: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r[0] != rep:
            continue
        d[r[idx + 1]].append(r[4])
    means = {k: st.mean(v) for k, v in d.items()}
    return (max(means.values()) - min(means.values())) * 100.0


def ci_rm(vals: list[float], alpha: float = 0.05) -> tuple:
    m = st.mean(vals)
    s = st.stdev(vals) if len(vals) > 1 else 0.0
    t = sstats.t.ppf(1 - alpha / 2, len(vals) - 1)
    hw = t * s / math.sqrt(len(vals))
    return m, s, hw, m - hw, m + hw


def ci_nb(vals: list[float], n2_n1: float, alpha: float = 0.05) -> tuple:
    m = st.mean(vals)
    s = st.stdev(vals) if len(vals) > 1 else 0.0
    se = math.sqrt((1.0 / len(vals) + n2_n1) * s * s)
    t = sstats.t.ppf(1 - alpha / 2, len(vals) - 1)
    return m, se, t * se, m - t * se, m + t * se


def pooled_marginals(rows: list[tuple]) -> dict[str, dict]:
    per_cfg: dict[tuple, list[float]] = defaultdict(list)
    for r in rows:
        per_cfg[(r[1], r[2], r[3])].append(r[4])
    cfg_means = {k: st.mean(v) for k, v in per_cfg.items()}
    out = {}
    for idx, name in [(0, "fil"), (1, "vec"), (2, "clf")]:
        d: dict[str, list[float]] = defaultdict(list)
        for k, acc in cfg_means.items():
            d[k[idx]].append(acc)
        m = {k: st.mean(v) for k, v in d.items()}
        out[name] = {"levels": m, "range_pp": (max(m.values()) - min(m.values())) * 100.0}
    return out


def anova_3way(values: list[tuple], level_idx: dict[str, int]) -> dict:
    """values: rows (filtration, vectorizer, classifier, acc)."""
    y = np.array([r[3] for r in values])
    grand = y.mean()
    ss_tot = float(((y - grand) ** 2).sum())
    levels = {name: sorted({r[idx] for r in values}) for name, idx in level_idx.items()}
    ss = {}
    for name, idx in level_idx.items():
        s = 0.0
        for lev in levels[name]:
            ys = np.array([r[3] for r in values if r[idx] == lev])
            s += len(ys) * (ys.mean() - grand) ** 2
        ss[name] = float(s)
    ss_err = ss_tot - sum(ss.values())
    dfs = {name: len(levels[name]) - 1 for name in level_idx}
    df_err = len(y) - 1 - sum(dfs.values())
    ms_err = ss_err / df_err if df_err > 0 else float("nan")
    out = {}
    for name in level_idx:
        df = dfs[name]
        F = (ss[name] / df) / ms_err if ms_err > 0 else float("nan")
        p = float(sstats.f.sf(F, df, df_err)) if ms_err > 0 else float("nan")
        eta2 = ss[name] / ss_tot if ss_tot > 0 else float("nan")
        omega2 = ((ss[name] - df * ms_err) / (ss_tot + ms_err)) if ms_err > 0 else float("nan")
        out[name] = {"eta2": eta2, "omega2": omega2, "F": F, "p": p,
                     "df": df, "ss": ss[name]}
    out["_"] = {"ss_total": ss_tot, "ss_err": ss_err, "df_err": df_err,
                "ms_err": ms_err, "N": len(y)}
    return out


def main() -> None:
    assert DB.exists(), f"missing {DB}"
    rows = load_rows()
    reps = sorted({r[0] for r in rows})
    print(f"DB: {len(rows)} per-rep config rows, reps {reps}")

    stages = {0: "filtration", 1: "vectorizer", 2: "classifier"}
    per_rep = {name: [] for name in stages.values()}
    for rep in reps:
        for idx, name in stages.items():
            per_rep[name].append(stage_range_for_rep(rows, rep, idx))

    rep_lines = []
    for rep in reps:
        rep_lines.append(f"| {rep} | {per_rep['filtration'][rep-1]:.2f} | "
                         f"{per_rep['vectorizer'][rep-1]:.2f} | {per_rep['classifier'][rep-1]:.2f} |")

    ci_lines = []
    stats_out = {}
    for name in stages.values():
        vals = per_rep[name]
        m, s, hw_rm, lo_rm, hi_rm = ci_rm(vals)
        m2, se, hw_nb, lo_nb, hi_nb = ci_nb(vals, N2_N1)
        stats_out[name] = {"mean": m, "sd": s, "ci_rm": [lo_rm, hi_rm], "ci_nb": [lo_nb, hi_nb]}
        ci_lines.append(f"| {name} | {m:.2f} | {s:.2f} | [{lo_rm:.2f}, {hi_rm:.2f}] | "
                        f"[{lo_nb:.2f}, {hi_nb:.2f}] |")

    pooled = pooled_marginals(rows)
    pooled_lines = []
    for name, key in [("filtration", "fil"), ("vectorizer", "vec"), ("classifier", "clf")]:
        lev = pooled[key]["levels"]
        lev_s = ", ".join(f"{k} {v*100:.2f}%" for k, v in sorted(lev.items(), key=lambda x: -x[1]))
        pooled_lines.append(f"- **{name}** range {pooled[key]['range_pp']:.2f} pp: {lev_s}")
        stats_out[name]["pooled_range_pp"] = pooled[key]["range_pp"]

    # ANOVA: per-config means (mean over all 25 fold accs) and fold-level (all folds)
    conn = sqlite3.connect(str(DB))
    cfg_rows = conn.execute(
        """SELECT r.filtration, r.vectorizer, r.classifier, AVG(f.accuracy)
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL
           GROUP BY r.filtration, r.vectorizer, r.classifier""").fetchall()
    fold_rows = conn.execute(
        """SELECT r.filtration, r.vectorizer, r.classifier, f.accuracy
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL""").fetchall()
    conn.close()

    anova_cfg = anova_3way(cfg_rows, {"filtration": 0, "vectorizer": 1, "classifier": 2})
    anova_fold = anova_3way(fold_rows, {"filtration": 0, "vectorizer": 1, "classifier": 2})
    stats_out["anova_per_config"] = {k: v for k, v in anova_cfg.items() if k != "_"}
    stats_out["anova_per_config"]["_"] = anova_cfg["_"]
    stats_out["anova_fold_level"] = {k: v for k, v in anova_fold.items() if k != "_"}
    stats_out["anova_fold_level"]["_"] = anova_fold["_"]

    anova_cfg_lines = []
    for name in ["filtration", "vectorizer", "classifier"]:
        a = anova_cfg[name]
        anova_cfg_lines.append(f"| {name} | {a['eta2']:.4f} | {a['omega2']:.4f} | "
                               f"F({a['df']},{anova_cfg['_']['df_err']}) = {a['F']:.2f} | {a['p']:.2e} |")
    anova_fold_lines = []
    for name in ["filtration", "vectorizer", "classifier"]:
        a = anova_fold[name]
        anova_fold_lines.append(f"| {name} | {a['eta2']:.4f} | {a['omega2']:.4f} | "
                                f"F({a['df']},{anova_fold['_']['df_err']}) = {a['F']:.2f} | {a['p']:.2e} |")

    report = "\n".join([
        "# A3 — MNIST 0/1 repeated 5-fold CV (5 reps, CV seeds 43..47)\n",
        f"DB: `{DB}` ({len(rows)} per-rep config rows; 56 configs x 5 reps x 5 folds).\n",
        "Statistic: stage marginal range (pp), stage-level mean = mean over configs of per-config mean accuracy.\n",
        f"n2/n1 (NB correction) = {N2_N1:.2f} (400 samples: 80 test / 320 train).\n",
        "\n## Per-repetition stage ranges (pp)\n",
        "| rep | filtration | vectorizer | classifier |",
        "|---|---|---|---|",
        *rep_lines,
        "\n## Stage range: mean / SD / 95% CIs over 5 reps\n",
        "| stage | mean | SD | CI (repeated-meas.) | CI (Nadeau-Bengio) |",
        "|---|---|---|---|---|",
        *ci_lines,
        "\n## Pooled marginals (per-config means over all 5 reps)\n",
        *pooled_lines,
        "\n**Comparison vs single-split bootstrap CIs** (expanded_results.db): "
        "vectorizer [2.00, 6.14] / filtration [0.74, 2.69]; "
        "single-split pooled marginals vec 3.22pp / fil 1.65pp.\n",
        "\n## 3-way ANOVA (new repeated-CV DB)\n",
        "\n### Per-config means scope (N = 56, y = mean over 25 fold accs)\n",
        "| stage | eta^2 | omega^2 | F | p |",
        "|---|---|---|---|---|",
        *anova_cfg_lines,
        f"\nSS_total = {anova_cfg['_']['ss_total']:.6f}, df_err = {anova_cfg['_']['df_err']}\n",
        "\n### Fold-level scope (N = 1400 fold accs, descriptive)\n",
        "| stage | eta^2 | omega^2 | F | p |",
        "|---|---|---|---|---|",
        *anova_fold_lines,
        f"\nSS_total = {anova_fold['_']['ss_total']:.6f}, df_err = {anova_fold['_']['df_err']}\n",
    ])
    OUT_MD.write_text(report)
    with open(OUT_JSON, "w") as fh:
        json.dump(stats_out, fh, indent=2, default=str)
    print(report)
    print(f"\nwrote {OUT_MD}, {OUT_JSON}")


if __name__ == "__main__":
    main()
