#!/usr/bin/env python3
"""#15 — Hierarchical (mixed-effects) model of stage importance.

Fits a statsmodels MixedLM (linear mixed model) to the 9-dataset panel:
outcome = per-config mean accuracy (pp), random intercept per dataset,
fixed effects for the vectorizer / filtration / classifier categories
(contrast-coded, sum-to-zero) plus a modality covariate.

Primary DB: data/tda/panel_stagecapable.db (144 runs = 9 datasets x 16
configs, all finished; 2 filtrations x 4 vectorizers x 2 classifiers per
dataset — every stage has >1 alternative, so the stage effects are on equal
footing). Robustness pass: data/tda/multidataset_sweep.db (144 runs, but the
filtration menu differs: weak_alpha on time series, cubical on images).

Number-derivation conventions (identical to analysis_panel_stagecapable.py /
analysis_repeated_cv_r25.py):
  * per-config accuracy = AVG(f.accuracy) per run_id, x100 (pp) — NEVER MAX,
  * schema is FLAT: runs (dataset/filtration/vectorizer/classifier/...)
    JOIN fold_results (fold/accuracy/...); completion = finished_at IS NOT
    NULL. The script probes and prints the schema before fitting.

Reported quantities:
  * fixed-effects table (coef, SE, z, p) from the MixedLM summary,
  * per-effect spread = population SD of the sum-coded level effects for
    each factor (reconstructed reference level = -sum of the others), in pp,
    with a parametric-bootstrap 95% CI (1,000 draws from N(beta, cov)),
  * stage importance = share of the fixed-effects variance attributable to
    each factor (Var(effect_f) / sum_f Var(effect_f); approximate with the
    unbalanced design — stated as such),
  * random-intercept variance + residual variance + ICC,
  * per-dataset random intercepts (BLUPs).

Caveat handled explicitly: filtration is partially confounded with modality
(cubical only on images; weighted_rips only on time series), so the primary
model includes C(modality, Sum); a sensitivity model without it is also fit
and reported.

Outputs (additive-only, read-only):
  * /tmp/tda_hierarchical_stage_summary.txt  (full model summary, printed too)

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_hierarchical_stage.py

Expected runtime: ~1-3 min (144-row MixedLM + 1,000-draw parametric
bootstrap; no sweeps, no training, nothing written to the result DBs).
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda")
DB_PANEL = DATA_DIR / "panel_stagecapable.db"
DB_MULTI = DATA_DIR / "multidataset_sweep.db"
OUT_TXT = Path("/tmp/tda_hierarchical_stage_summary.txt")

IMG_DATASETS = {"mnist10", "fmnist10"}
N_BOOT = 1_000
BOOT_SEED = 42

FORMULA = ("acc_pp ~ C(vectorizer, Sum) + C(filtration, Sum) + "
           "C(classifier, Sum) + C(modality, Sum)")


def probe_schema(db: Path) -> None:
    """Print the actual schema (tables + columns) — the task's schema check."""
    conn = sqlite3.connect(str(db))
    tables = [r[0] for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
    print(f"[schema] {db.name}: tables = {tables}")
    for t in tables:
        cols = [r[1] for r in conn.execute(f"PRAGMA table_info({t})")]
        print(f"[schema]   {t}: {cols}")
    conn.close()


def load_panel(db: Path) -> pd.DataFrame:
    """Per-config mean accuracy (pp) per dataset, one row per config."""
    conn = sqlite3.connect(str(db))
    rows = conn.execute(
        "SELECT r.dataset, r.filtration, r.vectorizer, r.classifier, "
        "AVG(f.accuracy) * 100 "
        "FROM runs r JOIN fold_results f ON f.run_id = r.run_id "
        "WHERE r.finished_at IS NOT NULL "
        "GROUP BY r.run_id").fetchall()
    conn.close()
    df = pd.DataFrame(rows, columns=["dataset", "filtration", "vectorizer",
                                     "classifier", "acc_pp"])
    df["modality"] = np.where(df["dataset"].isin(IMG_DATASETS),
                              "image", "time_series")
    return df


def effect_spreads(model, factors: list[str]) -> dict[str, float]:
    """Population SD (pp) of each sum-coded factor's full level effects.

    Sum coding: k-1 coefficients in model.params; the reference level's
    effect = -sum of the others. Spread = std over the reconstructed k
    level effects.
    """
    spreads = {}
    for f in factors:
        prefix = f"C({f}, Sum)["
        coefs = {k: v for k, v in model.params.items() if k.startswith(prefix)}
        if not coefs:
            continue
        vals = list(coefs.values())
        vals.append(-sum(vals))  # reference level
        spreads[f] = float(np.std(vals))
    return spreads


def bootstrap_spread_cis(model, factors: list[str],
                         n: int = N_BOOT, seed: int = BOOT_SEED) -> dict:
    """Parametric bootstrap of per-effect spreads: draw beta ~ N(beta, cov)."""
    rng = np.random.default_rng(seed)
    names = list(model.params.index)
    beta = model.params.values.astype(float)
    cov = np.asarray(model.cov_params(), dtype=float)
    cis = {f: [] for f in factors}
    for _ in range(n):
        b = rng.multivariate_normal(beta, cov)
        pm = dict(zip(names, b))
        for f in factors:
            prefix = f"C({f}, Sum)["
            vals = [v for k, v in pm.items() if k.startswith(prefix)]
            if not vals:
                continue
            vals.append(-sum(vals))
            cis[f].append(float(np.std(vals)))
    return {f: (float(np.percentile(v, 2.5)), float(np.percentile(v, 97.5)))
            for f, v in cis.items() if v}


def fit_and_report(df: pd.DataFrame, db_name: str, label: str) -> str:
    """Fit MixedLM on df and return the report section as text."""
    from statsmodels.formula.api import mixedlm

    lines = [f"\n{'=' * 78}", f"Model: {label} (data from {db_name})",
             f"rows: {len(df)} per-config means | datasets: "
             f"{df['dataset'].nunique()} | "
             f"formula: {FORMULA}"]
    model = mixedlm(FORMULA, df, groups=df["dataset"])
    fit = model.fit(reml=True)
    lines.append(str(fit.summary()))

    factors = ["vectorizer", "filtration", "classifier"]
    spreads = effect_spreads(fit, factors)
    cis = bootstrap_spread_cis(fit, factors)
    lines.append("\n## Stage importance — per-effect spread (pp) + 95% CI")
    lines.append("| factor | level-effect SD (pp) | 95% CI |")
    lines.append("|---|---|---|")
    for f in factors:
        s = spreads.get(f)
        ci = cis.get(f)
        if s is None:
            continue
        ci_s = (f"[{ci[0]:.2f}, {ci[1]:.2f}]" if ci else "—")
        lines.append(f"| {f} | {s:.2f} | {ci_s} |")

    # share of fixed-effects variance per factor (approximate, unbalanced)
    tot = sum(spreads.values())
    if tot > 0:
        lines.append("\n## Share of fixed-effects variance (approximate)")
        for f in factors:
            if f in spreads:
                lines.append(f"- {f}: {spreads[f] ** 2 / sum(s ** 2 for s in spreads.values()) * 100:.1f}%")

    # variance components
    vc = float(fit.cov_re.iloc[0, 0])  # single random intercept -> 1x1
    resid = float(fit.scale)
    icc = vc / (vc + resid) if (vc + resid) > 0 else float("nan")
    lines.append(f"\n## Variance components")
    lines.append(f"- random intercept (dataset) variance: {vc:.3f} "
                 f"(SD {np.sqrt(vc):.2f} pp)")
    lines.append(f"- residual variance: {resid:.3f} (SD {np.sqrt(resid):.2f} pp)")
    lines.append(f"- ICC (dataset share of total variance): {icc:.3f}")

    # per-dataset BLUPs
    re = fit.random_effects
    lines.append("\n## Per-dataset random intercepts (BLUPs, pp)")
    for ds in sorted(re, key=lambda k: -re[k].iloc[0, 0]):
        lines.append(f"- {ds:<18} {re[ds].iloc[0, 0]:+.2f}")
    return "\n".join(lines)


def main() -> None:
    probe_schema(DB_PANEL)

    df_panel = load_panel(DB_PANEL)
    print(f"[data] panel_stagecapable.db: {len(df_panel)} rows, "
          f"{df_panel['dataset'].nunique()} datasets, "
          f"{df_panel['vectorizer'].nunique()} vectorizers, "
          f"{df_panel['filtration'].nunique()} filtrations, "
          f"{df_panel['classifier'].nunique()} classifiers")

    sections = [fit_and_report(df_panel, "panel_stagecapable.db",
                               "primary (panel_stagecapable, with modality)")]
    # sensitivity: same panel, no modality covariate
    from statsmodels.formula.api import mixedlm
    formula_no_mod = ("acc_pp ~ C(vectorizer, Sum) + C(filtration, Sum) + "
                      "C(classifier, Sum)")
    m2 = mixedlm(formula_no_mod, df_panel, groups=df_panel["dataset"]).fit(reml=True)
    sections.append("\n## Sensitivity: same panel WITHOUT the modality covariate\n"
                    "(filtration is partially confounded with modality — "
                    "cubical only on images, weighted_rips only on time series)\n"
                    + str(m2.summary()))

    # robustness pass on the older multidataset sweep (different filtration menu)
    if DB_MULTI.exists():
        df_multi = load_panel(DB_MULTI)
        print(f"[data] multidataset_sweep.db: {len(df_multi)} rows, "
              f"{df_multi['dataset'].nunique()} datasets")
        sections.append(fit_and_report(df_multi, "multidataset_sweep.db",
                                       "robustness (multidataset_sweep, with modality)"))

    text = "\n".join(sections) + "\n"
    OUT_TXT.write_text(text)
    print(text)
    print(f"\nwrote {OUT_TXT}")


if __name__ == "__main__":
    main()
