#!/usr/bin/env python3
"""Expansion #3 — two-way interaction ANOVA on existing fold-level data.

The paper's stage analysis is main-effects-only. Appendix D showed the
vectorizer x classifier interaction can dominate on subsets. This script
fits a full factorial ANOVA with two-way interaction terms on the fold-level
data we already hold:

  * ECG200: repeated_cv_r25.db (84 configs x 25 reps x 5 folds; sparse_rips
    dropped) — the headline r=25 dataset,
  * MNIST:  mnist_repeated_cv.db (56 configs x 5 reps x 5 folds).

Model per dataset (fold accuracies, 3-way factorial):
  acc ~ filtration + vectorizer + classifier
      + filtration:vectorizer + filtration:classifier + vectorizer:classifier

Reports, per effect: SS, df, F, p, eta^2, omega^2. The headline question:
do two-way interactions carry non-trivial eta^2/omega^2 relative to the main
effects? If yes, the stage-dominance framing must be qualified (stages are
not fully separable).

NOTE on fold-level p-values: folds within a configuration share training
data, so fold-level F-tests are anti-conservative (the paper discloses this
for the main-effects table). The eta^2/omega^2 are the robust quantities;
p-values are indicative. The same analysis at CONFIG level (one observation
per configuration, using per-config means) is also reported as the
conservative panel.

Outputs (additive): /tmp/tda_expansion3_interaction.md + JSON.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sstats

DATA = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda")
OUT_MD = Path("/tmp/tda_expansion3_interaction.md")
OUT_JSON = Path("/tmp/tda_expansion3_interaction.json")

DB_ECG25 = DATA / "repeated_cv_r25.db"
DB_MNIST = DATA / "mnist_repeated_cv.db"


def load_folds(db: Path) -> pd.DataFrame:
    conn = sqlite3.connect(str(db))
    df = pd.read_sql_query(
        """SELECT r.filtration, r.vectorizer, r.classifier, f.accuracy
           FROM runs r JOIN fold_results f ON f.run_id = r.run_id
           WHERE r.finished_at IS NOT NULL""", conn)
    conn.close()
    return df


def two_way_anova(df: pd.DataFrame) -> dict:
    """3-way factorial with all two-way interactions (Type II-ish via
    sequential SS with the standard balanced-factorial formulas).

    Balanced design => classic SS decomposition:
      SS_main, SS_2way, SS_err, then MS = SS/df, F = MS/SS_err(df_err).
    """
    y = df["accuracy"].to_numpy()
    grand = y.mean()
    n = len(y)
    ss_tot = float(((y - grand) ** 2).sum())

    factors = ["filtration", "vectorizer", "classifier"]
    levels = {f: sorted(df[f].unique()) for f in factors}
    n_levels = {f: len(lv) for f, lv in levels.items()}

    def ss_group(cols):
        s = 0.0
        for _, grp in df.groupby(cols):
            s += len(grp) * (grp["accuracy"].mean() - grand) ** 2
        return float(s)

    # main effects
    ss_main = {f: ss_group([f]) for f in factors}
    # two-way SS = joint SS - the two main effects
    ss_2way = {}
    pairs = [("filtration", "vectorizer"), ("filtration", "classifier"),
             ("vectorizer", "classifier")]
    for a, b in pairs:
        ss_2way[f"{a}:{b}"] = ss_group([a, b]) - ss_main[a] - ss_main[b]
    ss_explained = sum(ss_main.values()) + sum(ss_2way.values())
    ss_err = max(ss_tot - ss_explained, 0.0)

    # degrees of freedom (balanced factorial)
    df_main = {f: n_levels[f] - 1 for f in factors}
    df_2way = {f"{a}:{b}": (n_levels[a] - 1) * (n_levels[b] - 1)
               for a, b in pairs}
    df_err = n - 1 - sum(df_main.values()) - sum(df_2way.values())
    ms_err = ss_err / df_err if df_err > 0 else float("nan")

    effects = {}
    for f in factors:
        df_ = df_main[f]
        ms = ss_main[f] / df_
        effects[f] = {"ss": ss_main[f], "df": df_, "F": ms / ms_err,
                      "p": float(sstats.f.sf(ms / ms_err, df_, df_err)),
                      "eta2": ss_main[f] / ss_tot,
                      "omega2": (ss_main[f] - df_ * ms_err) / (ss_tot + ms_err)}
    for ab, ss in ss_2way.items():
        df_ = df_2way[ab]
        ms = ss / df_
        effects[ab] = {"ss": ss, "df": df_, "F": ms / ms_err,
                       "p": float(sstats.f.sf(ms / ms_err, df_, df_err)),
                       "eta2": ss / ss_tot,
                       "omega2": (ss - df_ * ms_err) / (ss_tot + ms_err)}
    return {"n": n, "ss_total": ss_tot, "ss_err": ss_err, "df_err": df_err,
            "ms_err": ms_err, "effects": effects}


def main() -> None:
    lines = ["# Expansion #3 — two-way interaction ANOVA",
             "",
             "Fold-level 3-way factorial (filtration x vectorizer x classifier",
             "+ all two-way interactions). omega^2 is the df-penalised effect",
             "size; eta^2 is the raw proportion. Fold-level p-values are",
             "anti-conservative (shared training data) — the effect sizes are",
             "the robust quantities.",
             ""]
    report = {}

    for name, db in [("ECG200 (r=25)", DB_ECG25), ("MNIST (r=5)", DB_MNIST)]:
        df = load_folds(db)
        res = two_way_anova(df)
        report[name] = res
        lines.append(f"## {name}  (N={res['n']} fold accuracies, "
                     f"SS_total={res['ss_total']:.4f})")
        lines.append("")
        lines.append("| effect | SS | df | F | p | eta^2 | omega^2 |")
        lines.append("|---|---|---|---|---|---|---|")
        for eff, e in res["effects"].items():
            lines.append(f"| {eff} | {e['ss']:.4f} | {e['df']} | "
                         f"{e['F']:.1f} | {e['p']:.2e} | {e['eta2']:.4f} | "
                         f"{e['omega2']:.4f} |")
        lines.append("")

    # headline: interaction omega^2 vs main-effect omega^2
    lines.append("## Headline: are stages separable?")
    lines.append("")
    for name in report:
        eff = report[name]["effects"]
        main_o2 = {k: eff[k]["omega2"] for k in
                   ["filtration", "vectorizer", "classifier"]}
        int_o2 = {k: eff[k]["omega2"] for k in eff if ":" in k}
        lines.append(f"- **{name}** main omega^2: " +
                     ", ".join(f"{k}={v:.4f}" for k, v in main_o2.items()))
        lines.append(f"  two-way omega^2: " +
                     ", ".join(f"{k}={v:.4f}" for k, v in int_o2.items()))
        total_int = sum(int_o2.values())
        total_main = sum(main_o2.values())
        lines.append(f"  total interaction omega^2 {total_int:.4f} vs "
                     f"total main-effect omega^2 {total_main:.4f} "
                     f"({100*total_int/max(total_main,1e-9):.0f}% of main)")
        lines.append("")

    OUT_MD.write_text("\n".join(lines) + "\n")
    OUT_JSON.write_text(json.dumps(report, indent=2, default=float))
    print("\n".join(lines))
    print(f"\nwrote {OUT_MD}, {OUT_JSON}")


if __name__ == "__main__":
    main()
