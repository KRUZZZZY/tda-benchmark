#!/usr/bin/env python3
"""Reviewer-revision analysis A1: ECG200 25-repetition repeated-CV statistics.

Reads data/tda/repeated_cv_r25.db (84 configs x 25 reps x 5 folds, sparse_rips
dropped) and computes:
  * per-repetition stage marginal ranges (vec/fil/clf: range of stage-level
    means of per-config mean accuracies, in pp),
  * stage range mean/SD over the 25 independent repetitions,
  * two 95% CIs per stage:
      - repeated-measures CI:  mean +/- t_{0.975, R-1} * SD/sqrt(R)
        (the direct analog of the r=5 CIs [5.84, 6.34] / [0.35, 1.04] /
        [2.57, 3.78]),
      - Nadeau-Bengio corrected resampled CI (CRT, Schulz-Kumpel et al. 2024
        arXiv:2409.18836, eqs. CRT.1-CRT.4): SE^2 = (1/R + n2/n1) * s^2_R
        where s^2_R is the sample variance of the R per-rep range estimates,
        n2/n1 = test/train ratio = 40/160 = 0.25 for ECG200 5-fold CV,
        CI = mean +/- t_{0.975, R-1} * SE.
  * pooled marginals (per-config means over all 25 reps),
  * ordering stability across reps, per-config SD across reps, top configs.
  * comparison vs the r=5 repeated_cv.db numbers (recomputed from that DB).

Outputs (all additive): data/tda/repeated_cv_r25_config_stats.csv and
/tmp/tda_A1_r25_report.md.

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_repeated_cv_r25.py
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
DB25 = DATA_DIR / "repeated_cv_r25.db"
DB5 = DATA_DIR / "repeated_cv.db"          # old r=5 reference (112 configs, incl. sparse_rips)
OUT_CSV = DATA_DIR / "repeated_cv_r25_config_stats.csv"
OUT_MD = Path("/tmp/tda_A1_r25_report.md")
OUT_JSON = Path("/tmp/tda_A1_r25_stats.json")

N_FOLDS = 5
N2_N1 = 40.0 / 160.0   # ECG200: 200 samples, 5-fold => 40 test / 160 train


def load_per_config_accs(db: Path, reps: range | None = None) -> list[tuple]:
    """Return rows (rep, filtration, vectorizer, classifier, mean_acc)."""
    conn = sqlite3.connect(str(db))
    q = """SELECT r.repetition, r.filtration, r.vectorizer, r.classifier,
                  AVG(f.accuracy)
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL
           GROUP BY r.run_id"""
    rows = conn.execute(q).fetchall()
    conn.close()
    if reps is not None:
        rows = [r for r in rows if r[0] in set(reps)]
    return rows


def stage_range_for_rep(rows: list[tuple], rep: int, idx: int) -> float:
    """Marginal range (pp) of stage idx (0=fil, 1=vec, 2=clf) for one rep."""
    d: dict[str, list[float]] = defaultdict(list)
    for r in rows:
        if r[0] != rep:
            continue
        d[r[idx + 1]].append(r[4])
    means = {k: st.mean(v) for k, v in d.items()}
    return (max(means.values()) - min(means.values())) * 100.0


def pooled_marginals(rows: list[tuple]) -> dict[str, dict]:
    """Stage-level means over per-config means pooled across all reps."""
    per_cfg: dict[tuple, list[float]] = defaultdict(list)
    for r in rows:
        per_cfg[(r[1], r[2], r[3])].append(r[4])
    cfg_means = {k: st.mean(v) for k, v in per_cfg.items()}
    out: dict[str, dict] = {}
    for idx, name in [(0, "fil"), (1, "vec"), (2, "clf")]:
        d: dict[str, list[float]] = defaultdict(list)
        for k, acc in cfg_means.items():
            d[k[idx]].append(acc)
        m = {k: st.mean(v) for k, v in d.items()}
        out[name] = {"levels": m, "range_pp": (max(m.values()) - min(m.values())) * 100.0}
    return out


def ci_repeated_measures(vals: list[float], alpha: float = 0.05) -> tuple:
    """mean +/- t_{0.975, R-1} * SD/sqrt(R) over the R independent reps."""
    m = st.mean(vals)
    s = st.stdev(vals) if len(vals) > 1 else 0.0
    t = sstats.t.ppf(1 - alpha / 2, len(vals) - 1)
    hw = t * s / math.sqrt(len(vals))
    return m, s, hw, m - hw, m + hw


def ci_nadeau_bengio(vals: list[float], n2_n1: float, alpha: float = 0.05) -> tuple:
    """CRT (Nadeau-Bengio corrected): SE^2 = (1/R + n2/n1) * s^2_R."""
    m = st.mean(vals)
    s = st.stdev(vals) if len(vals) > 1 else 0.0
    se = math.sqrt((1.0 / len(vals) + n2_n1) * s * s)
    t = sstats.t.ppf(1 - alpha / 2, len(vals) - 1)
    hw = t * se
    return m, se, hw, m - hw, m + hw


def per_config_stats(rows: list[tuple]) -> list[dict]:
    """Per-config mean/SD across reps + Nadeau-Bengio CI over all k*R folds."""
    conn = sqlite3.connect(str(DB25))
    q = """SELECT r.filtration, r.vectorizer, r.classifier, r.repetition, f.accuracy
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.finished_at IS NOT NULL"""
    raw = conn.execute(q).fetchall()
    conn.close()
    by_cfg: dict[tuple, list[float]] = defaultdict(list)  # all k*R folds
    for fil, vec, clf, rep, acc in raw:
        by_cfg[(fil, vec, clf)].append(acc)
    out = []
    for cfg, folds in by_cfg.items():
        m = st.mean(folds)
        s = st.stdev(folds) if len(folds) > 1 else 0.0
        # NB per-config SE over m = k*R folds: SE^2 = (1/m + n2/n1) * s^2
        m_ = len(folds)
        se = math.sqrt((1.0 / m_ + N2_N1) * s * s)
        t = sstats.t.ppf(0.975, m_ - 1)
        out.append({
            "filtration": cfg[0], "vectorizer": cfg[1], "classifier": cfg[2],
            "mean_acc": m, "sd_folds": s,
            "nb95_lo": m - t * se, "nb95_hi": m + t * se,
            "n_folds": m_,
        })
    return out


def main() -> None:
    assert DB25.exists(), f"missing {DB25}"
    rows25 = load_per_config_accs(DB25)
    reps = sorted({r[0] for r in rows25})
    print(f"DB25: {len(rows25)} per-rep config rows, reps {reps[0]}..{reps[-1]}")

    stages = {0: "filtration", 1: "vectorizer", 2: "classifier"}
    per_rep = {name: [] for name in stages.values()}
    for rep in reps:
        for idx, name in stages.items():
            per_rep[name].append(stage_range_for_rep(rows25, rep, idx))

    report = []
    report.append("# A1 — ECG200 repeated 5-fold CV, 25 repetitions\n")
    report.append(f"DB: `{DB25}` ({len(rows25)} per-rep config rows; 84 configs x 25 reps x 5 folds)\n")
    report.append("CV seeds: random_seed=42, reps 1..25 => StratifiedKFold(random_state=43..67).\n")
    report.append("Statistic: stage marginal range (pp) = max(stage-level mean) - min(stage-level mean), "
                  "stage-level mean = mean over configs of per-config mean accuracy.\n")
    report.append(f"n2/n1 (NB correction) = {N2_N1:.2f} (ECG200 5-fold: 40 test / 160 train).\n")

    report.append("\n## Per-repetition stage ranges (pp)\n")
    report.append("| rep | filtration | vectorizer | classifier |")
    report.append("|---|---|---|---|")
    for rep in reps:
        report.append(f"| {rep} | {per_rep['filtration'][rep-1]:.2f} | "
                      f"{per_rep['vectorizer'][rep-1]:.2f} | {per_rep['classifier'][rep-1]:.2f} |")

    stats_out = {}
    report.append("\n## Stage range: mean / SD / 95% CIs over 25 reps\n")
    report.append("| stage | mean | SD | CI (repeated-meas.) | CI (Nadeau-Bengio CRT) |")
    report.append("|---|---|---|---|---|")
    for name in stages.values():
        vals = per_rep[name]
        m, s, hw_rm, lo_rm, hi_rm = ci_repeated_measures(vals)
        m2, se, hw_nb, lo_nb, hi_nb = ci_nadeau_bengio(vals, N2_N1)
        stats_out[name] = {
            "mean": m, "sd": s,
            "ci_rm": [lo_rm, hi_rm], "ci_nb": [lo_nb, hi_nb],
            "per_rep": vals,
        }
        report.append(f"| {name} | {m:.2f} | {s:.2f} | [{lo_rm:.2f}, {hi_rm:.2f}] | [{lo_nb:.2f}, {hi_nb:.2f}] |")

    # pooled marginals
    pooled = pooled_marginals(rows25)
    report.append("\n## Pooled marginals (per-config means over all 25 reps)\n")
    for name in ["filtration", "vectorizer", "classifier"]:
        key = {"filtration": "fil", "vectorizer": "vec", "classifier": "clf"}[name]
        lev = pooled[key]["levels"]
        lev_s = ", ".join(f"{k} {v*100:.2f}%" for k, v in sorted(lev.items(), key=lambda x: -x[1]))
        report.append(f"- **{name}** range {pooled[key]['range_pp']:.2f} pp: {lev_s}")
        stats_out[name]["pooled_range_pp"] = pooled[key]["range_pp"]

    # ordering stability
    order_ok = 0
    for rep in reps:
        if per_rep["vectorizer"][rep-1] > per_rep["classifier"][rep-1] > per_rep["filtration"][rep-1]:
            order_ok += 1
    report.append(f"\n## Ordering stability: vectorizer > classifier > filtration in {order_ok}/{len(reps)} reps")
    stats_out["ordering_vcf"] = f"{order_ok}/{len(reps)}"

    # per-config stats
    cfg_stats = per_config_stats(rows25)
    sds = [c["sd_folds"] * 100 for c in cfg_stats]
    report.append(f"\n## Per-config stats across 25 reps (mean fold-level SD {st.mean(sds):.2f}pp, "
                  f"median {st.median(sds):.2f}pp, max {max(sds):.2f}pp)")
    top = sorted(cfg_stats, key=lambda c: -c["mean_acc"])[:8]
    report.append("\n### Top configs by repeated-CV mean\n")
    report.append("| config | mean acc | fold-SD | NB 95% CI |")
    report.append("|---|---|---|---|")
    for c in top:
        report.append(f"| {c['filtration']} + {c['vectorizer']} + {c['classifier']} | "
                      f"{c['mean_acc']*100:.2f}% | {c['sd_folds']*100:.2f}pp | "
                      f"[{c['nb95_lo']*100:.2f}, {c['nb95_hi']*100:.2f}] |")
    stats_out["top_configs"] = top[:8]

    # r=5 comparison from the old DB
    if DB5.exists():
        rows5 = load_per_config_accs(DB5, reps=range(1, 6))
        report.append("\n## Comparison vs r=5 (recomputed from repeated_cv.db, 112 configs)\n")
        report.append("| stage | r=5 mean | r=5 CI (t_4) | r=25 mean | r=25 CI (repeated-meas.) | r=25 CI (NB) | width r=5 -> r=25 |")
        report.append("|---|---|---|---|---|---|---|")
        cmp = {}
        for idx, name in stages.items():
            v5 = [stage_range_for_rep(rows5, r, idx) for r in range(1, 6)]
            m5, s5, hw5, lo5, hi5 = ci_repeated_measures(v5)
            v25 = per_rep[name]
            m25, s25, hw25, lo25, hi25 = ci_repeated_measures(v25)
            _, _, _, lo_nb, hi_nb = ci_nadeau_bengio(v25, N2_N1)
            cmp[name] = {"r5": [lo5, hi5], "r25_rm": [lo25, hi25], "r25_nb": [lo_nb, hi_nb]}
            w5 = hi5 - lo5
            w25 = hi25 - lo25
            report.append(f"| {name} | {m5:.2f} | [{lo5:.2f}, {hi5:.2f}] | {m25:.2f} | "
                          f"[{lo25:.2f}, {hi25:.2f}] | [{lo_nb:.2f}, {hi_nb:.2f}] | "
                          f"{w5:.2f} -> {w25:.2f} ({w25/w5:.2f}x) |")
        stats_out["r5_comparison"] = cmp
        # r=5 sanity: check vs published [5.84,6.34]/[0.35,1.04]/[2.57,3.78]
        report.append("\nPublished r=5 CIs: vec [5.84, 6.34], fil [0.35, 1.04], clf [2.57, 3.78].\n")

    # also: same-stage comparison using only reps 1..5 of the NEW DB (protocol fidelity)
    rows25_first5 = [r for r in rows25 if r[0] <= 5]
    report.append("\n## Protocol-fidelity check: reps 1..5 of the NEW DB (84-config subset)\n")
    report.append("| stage | r=5 mean (new DB) | r=5 CI (new DB) |")
    report.append("|---|---|---|")
    fid = {}
    for idx, name in stages.items():
        v = [stage_range_for_rep(rows25_first5, r, idx) for r in range(1, 6)]
        m5, s5, hw5, lo5, hi5 = ci_repeated_measures(v)
        fid[name] = {"mean": m5, "ci": [lo5, hi5]}
        report.append(f"| {name} | {m5:.2f} | [{lo5:.2f}, {hi5:.2f}] |")
    stats_out["fidelity_reps1_5"] = fid

    # write CSV
    import csv
    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["filtration", "vectorizer", "classifier",
                                           "mean_acc", "sd_folds", "nb95_lo", "nb95_hi", "n_folds"])
        w.writeheader()
        for c in sorted(cfg_stats, key=lambda c: -c["mean_acc"]):
            w.writerow(c)
    with open(OUT_JSON, "w") as fh:
        json.dump(stats_out, fh, indent=2, default=str)

    text = "\n".join(report)
    OUT_MD.write_text(text)
    print(text)
    print(f"\nwrote {OUT_CSV}, {OUT_MD}, {OUT_JSON}")


if __name__ == "__main__":
    main()
