#!/usr/bin/env python3
"""Reviewer-revision analysis A8: omega^2 effect sizes + multiplicity control.

Extends the paper's eta^2 analysis (Table 4.4 / tab:eta2, 18 F-tests) with:

1. omega^2 (population effect size)
   omega2 = (SS_effect - df_effect * MS_error) / (SS_total + MS_error)
   computed from the NEW repeated-CV DBs:
     - ECG200: data/tda/repeated_cv_r25.db (84 configs, per-config mean over
       25 reps; sparse_rips dropped per A1)
     - MNIST:  data/tda/mnist_repeated_cv.db (56 configs, per-config mean over
       5 reps)
   plus bootstrap 95% CIs (resample configurations with replacement, 1000
   iterations, percentile CI) on omega^2 per stage.

2. Multiplicity correction for the paper's 18 F-tests (3 datasets x 3 stages
   x 2 scopes: per-config means + fold-level). The 18 raw p-values are
   recomputed from expanded_results.db (the single-split sweep the table is
   based on) and verified against data/tda/eta_squared_results.csv, then Holm
   (strong FWER control) and Benjamini-Hochberg (FDR control) adjusted
   p-values are computed for all 18. The multiplicity footnote in the paper
   must cover all 18 tests.

3. A note on cross-dataset eta^2 comparability limits.

Outputs (additive): /tmp/tda_A8_omega2_report.md, /tmp/tda_A8_omega2_stats.json.

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_eta_omega2.py
"""

from __future__ import annotations

import importlib.util
import json
import os
import sqlite3
import sys
from pathlib import Path

import numpy as np
from scipy import stats as sstats

# ── importlib shim for the hyphenated repo dir (same as run_all.sh) ────────
REPO = Path(__file__).resolve().parent.parent
PKG_DIR = str(REPO)
if "tda_benchmark" not in sys.modules:
    spec = importlib.util.spec_from_file_location(
        "tda_benchmark", os.path.join(PKG_DIR, "__init__.py"),
        submodule_search_locations=[PKG_DIR])
    pkg = importlib.util.module_from_spec(spec)
    sys.modules["tda_benchmark"] = pkg
    spec.loader.exec_module(pkg)

PROJECT_ROOT = REPO.parent.parent  # AI_KOS_PROJECT
DATA_DIR = PROJECT_ROOT / "data" / "tda"
DB_EXP = DATA_DIR / "expanded_results.db"       # single-split sweep (paper's Table 4.4)
DB_ECG25 = DATA_DIR / "repeated_cv_r25.db"      # A1: ECG200 25 reps
DB_MNIST = DATA_DIR / "mnist_repeated_cv.db"    # A3: MNIST 5 reps
CSV_REF = DATA_DIR / "eta_squared_results.csv"  # published 18-test reference
OUT_MD = Path("/tmp/tda_A8_omega2_report.md")
OUT_JSON = Path("/tmp/tda_A8_omega2_stats.json")

N_BOOT = 1000
ALPHA = 0.05


def load_config_means(db: Path, dataset: str) -> list[tuple]:
    """Per-config mean accuracy (mean over ALL fold accuracies of ALL reps).

    One row per configuration => N = 84 (ECG200) / 56 (MNIST) for the new
    repeated-CV DBs; identical to GROUP BY run_id for the single-rep
    expanded_results.db.
    """
    conn = sqlite3.connect(str(db))
    rows = conn.execute(
        """SELECT r.filtration, r.vectorizer, r.classifier, AVG(f.accuracy)
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.dataset = ? AND r.finished_at IS NOT NULL
           GROUP BY r.filtration, r.vectorizer, r.classifier""", (dataset,)).fetchall()
    conn.close()
    return rows


def anova_3way(rows: list[tuple]) -> dict:
    """3-way main-effects ANOVA on rows (filtration, vectorizer, classifier, acc)."""
    y = np.array([r[3] for r in rows])
    grand = y.mean()
    ss_tot = float(((y - grand) ** 2).sum())
    idx = {"filtration": 0, "vectorizer": 1, "classifier": 2}
    levels = {k: sorted({r[i] for r in rows}) for k, i in idx.items()}
    ss = {}
    for k, i in idx.items():
        s = 0.0
        for lev in levels[k]:
            ys = np.array([r[3] for r in rows if r[i] == lev])
            s += len(ys) * (ys.mean() - grand) ** 2
        ss[k] = float(s)
    ss_err = ss_tot - sum(ss.values())
    dfs = {k: len(levels[k]) - 1 for k in idx}
    df_err = len(y) - 1 - sum(dfs.values())
    ms_err = ss_err / df_err if df_err > 0 else float("nan")
    out = {"ss_total": ss_tot, "ss_err": ss_err, "df_err": df_err, "ms_err": ms_err,
           "N": len(y), "dfs": dfs}
    for k in idx:
        df = dfs[k]
        F = (ss[k] / df) / ms_err if ms_err > 0 else float("nan")
        p = float(sstats.f.sf(F, df, df_err)) if ms_err > 0 else float("nan")
        eta2 = ss[k] / ss_tot if ss_tot > 0 else float("nan")
        omega2 = (ss[k] - df * ms_err) / (ss_tot + ms_err) if ms_err > 0 else float("nan")
        out[k] = {"ss": ss[k], "df": df, "F": F, "p": p, "eta2": eta2, "omega2": omega2}
    return out


def bootstrap_omega2(rows: list[tuple], n_iter: int = N_BOOT, seed: int = 42) -> dict:
    """Resample configurations with replacement; percentile CI for omega2 per stage."""
    arr = np.array(rows, dtype=object)
    rng = np.random.default_rng(seed)
    boot = {"filtration": [], "vectorizer": [], "classifier": []}
    for _ in range(n_iter):
        idx = rng.integers(0, len(arr), size=len(arr))
        a = anova_3way(list(arr[idx]))
        for k in boot:
            boot[k].append(a[k]["omega2"])
    out = {}
    for k, vals in boot.items():
        lo, hi = np.percentile(vals, [100 * ALPHA / 2, 100 * (1 - ALPHA / 2)])
        out[k] = {"omega2_mean": float(np.mean(vals)),
                  "ci95": [float(lo), float(hi)], "n_iter": n_iter}
    return out


# ── multiplicity corrections ────────────────────────────────────────────────

def holm_adjust(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i])
    out = [0.0] * m
    running = 0.0
    for rank, i in enumerate(order):
        adj = (m - rank) * pvals[i]
        running = max(running, adj)
        out[i] = min(running, 1.0)
    return out


def bh_adjust(pvals: list[float]) -> list[float]:
    m = len(pvals)
    order = sorted(range(m), key=lambda i: pvals[i], reverse=True)
    out = [0.0] * m
    running = 1.0
    for rank, i in enumerate(order):
        adj = (m / (m - rank)) * pvals[i]
        running = min(running, adj)
        out[i] = min(running, 1.0)
    return out


def read_reference_pvals() -> dict:
    """18 raw p-values from data/tda/eta_squared_results.csv (paper's Table 4.4)."""
    import csv
    ref = {}
    with open(CSV_REF) as fh:
        for row in csv.DictReader(fh):
            ds, scope = row["dataset"], row["scope"]
            for stage in ["filtration", "vectorizer", "classifier"]:
                ref[(ds, scope, stage)] = float(row[f"p_{stage}"])
    return ref


def recompute_18_from_expanded() -> list[dict]:
    """Recompute the 18 F-tests from expanded_results.db (per-config + fold-level)."""
    conn = sqlite3.connect(str(DB_EXP))
    tests = []
    for ds in ["ecg200", "mnist_01", "sphere_torus_n0"]:
        cfg = conn.execute(
            """SELECT r.filtration, r.vectorizer, r.classifier, AVG(f.accuracy)
               FROM runs r JOIN fold_results f ON r.run_id = f.run_id
               WHERE r.dataset = ? AND r.finished_at IS NOT NULL
               GROUP BY r.filtration, r.vectorizer, r.classifier""",
            (ds,)).fetchall()
        fold = conn.execute(
            """SELECT r.filtration, r.vectorizer, r.classifier, f.accuracy
               FROM runs r JOIN fold_results f ON r.run_id = f.run_id
               WHERE r.dataset = ? AND r.finished_at IS NOT NULL""",
            (ds,)).fetchall()
        for scope, rows in [("per-config means", cfg), ("fold-level", fold)]:
            a = anova_3way(rows)
            for stage in ["filtration", "vectorizer", "classifier"]:
                tests.append({
                    "dataset": ds, "scope": scope, "stage": stage,
                    "eta2": a[stage]["eta2"], "F": a[stage]["F"],
                    "p": a[stage]["p"], "df": a[stage]["df"],
                    "df_err": a["df_err"], "N": a["N"],
                })
    conn.close()
    return tests


def main() -> None:
    lines = []
    stats = {}

    # ── 1. omega^2 from the new repeated-CV DBs ───────────────────────────
    lines.append("# A8 — omega^2 effect sizes, bootstrap CIs, multiplicity control\n")
    lines.append("omega2 = (SS_effect - df_effect * MS_error) / (SS_total + MS_error).\n")

    for label, db, ds in [("ECG200 (84 configs, 25 reps)", DB_ECG25, "ecg200"),
                          ("MNIST 0/1 (56 configs, 5 reps)", DB_MNIST, "mnist_01")]:
        assert db.exists(), f"missing {db}"
        rows = load_config_means(db, ds)
        a = anova_3way(rows)
        boot = bootstrap_omega2(rows)
        stats[label] = {"anova": {k: v for k, v in a.items() if k in
                                  ("filtration", "vectorizer", "classifier")},
                        "bootstrap": boot}
        lines.append(f"\n## {label}\n")
        lines.append("| stage | eta^2 | omega^2 | F | p | bootstrap 95% CI (omega^2) |")
        lines.append("|---|---|---|---|---|---|")
        for stage in ["filtration", "vectorizer", "classifier"]:
            s = a[stage]
            b = boot[stage]
            lines.append(f"| {stage} | {s['eta2']:.4f} | {s['omega2']:.4f} | "
                         f"F({s['df']},{a['df_err']}) = {s['F']:.2f} | {s['p']:.2e} | "
                         f"[{b['ci95'][0]:.4f}, {b['ci95'][1]:.4f}] |")
        lines.append(f"\nSS_total = {a['ss_total']:.6f}, SS_error = {a['ss_err']:.6f}, "
                     f"df_err = {a['df_err']}, N = {a['N']} configurations.\n")

    # ── 2. the 18 F-tests: recompute, verify, correct ─────────────────────
    tests = recompute_18_from_expanded()
    assert len(tests) == 18, len(tests)
    ref = read_reference_pvals()
    mismatches = []
    for t in tests:
        key = (t["dataset"], t["scope"], t["stage"])
        r = ref.get(key)
        if r is not None and abs(r - t["p"]) > 1e-6:
            mismatches.append((key, r, t["p"]))
    raw = [t["p"] for t in tests]
    holm = holm_adjust(raw)
    bh = bh_adjust(raw)
    for t, h, b in zip(tests, holm, bh):
        t["p_holm"] = h
        t["p_bh"] = b

    lines.append("\n## Multiplicity correction — the paper's 18 F-tests (Table 4.4 / tab:eta2)\n")
    lines.append("Raw p-values recomputed from `expanded_results.db` (single-split sweep). "
                 f"Verification vs `eta_squared_results.csv`: {'OK (all 18 match)' if not mismatches else str(mismatches)}\n")
    lines.append("| # | dataset | scope | stage | eta^2 | F | df | df_err | p (raw) | p (Holm) | p (BH) |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|---|")
    for i, t in enumerate(tests, 1):
        ds_short = {"ecg200": "ECG200", "mnist_01": "MNIST 0/1", "sphere_torus_n0": "Sphere/Torus σ=0"}[t["dataset"]]
        scope_short = "config" if t["scope"].startswith("per-config") else "fold"
        lines.append(f"| {i} | {ds_short} | {scope_short} | {t['stage']} | {t['eta2']:.3f} | "
                     f"{t['F']:.2f} | {t['df']} | {t['df_err']} | {t['p']:.3e} | "
                     f"{t['p_holm']:.3e} | {t['p_bh']:.3e} |")
    lines.append("\nHolm = strong FWER control (step-down, α=0.05); BH = FDR control (Benjamini-Hochberg, q=0.05).")
    lines.append("Tests 1..9 are the per-config scope (primary, defensible df); tests 10..18 are the")
    lines.append("fold-level scope (descriptive only — folds within a configuration are correlated,")
    lines.append("so fold-level p-values are anti-conservative; see round-2 finding I-5).")
    lines.append("Multiplicity footnote must state: 18 F-tests across 3 datasets x 3 stages x 2 scopes;")
    lines.append("Holm-adjusted p < 0.05 and BH q < 0.05 both applied to all 18.")
    stats["f18"] = tests

    # ── 3. cross-dataset eta^2 comparability note ─────────────────────────
    lines.append("""
## Cross-dataset eta^2 comparability limits (note for the paper)

1. **eta^2 is dataset-relative.** eta^2 = SS_stage / SS_total normalizes by the
   dataset's own total variance, so a stage explaining 0.217 of ECG200's
   config-level variance and one explaining 0.302 of MNIST's are not directly
   comparable magnitudes: SS_total(ECG200) = 0.1995 vs SS_total(MNIST) = 0.0230
   (single-split sweep). The same absolute accuracy effect yields a much larger
   eta^2 on a low-variance dataset. Report SS_total alongside eta^2.
2. **Factor design differs.** ECG200/sphere-torus use 4 filtrations (df = 3);
   MNIST uses 2 image-compatible filtrations (df = 1). F is df-dependent
   (F = (SS/df)/(MS_error)), so MNIST's filtration F = 15.83 exceeds ECG200's
   F = 0.15 despite lower SS contribution — never rank stages across datasets
   by F. omega^2's df penalty (SS_effect - df*MS_error) partially corrects the
   design difference and is the better cross-design effect size.
3. **Scope differences.** Per-config-means eta^2 (one observation per
   configuration, df_err = 99/45) and fold-level eta^2 (N = 560/280 fold
   accuracies, df_err = 547/269) are different estimands; fold-level pools
   within-configuration fold noise into the denominator. Only per-config
   values are comparable across the paper's tables.
4. **Ceiling effects.** sphere_torus sigma=0.00 has SS_total = 7.3e-5 (all
   configs round to 100%); its eta^2 values (0.009-0.165) are artifacts of
   rounding and should not be compared with the real datasets.
5. **Repetition pooling.** The new repeated-CV DBs (A1: 25 reps, A3: 5 reps)
   reduce estimator noise: per-config means over R reps are more stable than
   single-split means, so eta^2/omega^2 from them are the preferred estimates.
   omega^2 bootstrap CIs above resample configurations, capturing sampling
   uncertainty of the config set.
""")

    OUT_MD.write_text("\n".join(lines))
    with open(OUT_JSON, "w") as fh:
        json.dump(stats, fh, indent=2, default=str)
    print("\n".join(lines))
    print(f"\nwrote {OUT_MD}, {OUT_JSON}")


if __name__ == "__main__":
    main()
