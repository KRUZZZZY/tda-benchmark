#!/usr/bin/env python3
"""Expansion A1 (#2) — equal-footing stage statistics.

The paper's headline stage comparisons (ECG200 vectorizer 6.39pp vs
filtration 0.69pp; ECG5000 vectorizer 24.89pp vs filtration 3.60pp)
compare ranges over DIFFERENT numbers of levels (7 vectorizers vs
3 filtrations) and include "degenerate" scalar vectorizers
(persistence_entropy, amplitude) that produce a single number per
diagram and are structurally handicapped. This script re-reports the
stage contribution on an EQUAL FOOTING:

  1. omega^2 lead: main-effect omega^2 (df-penalised) per stage over
     per-configuration means — the design-penalised effect size.
  2. Marginal ranges (pooled per-config means): all levels.
  3. Vectorizer range EXCLUDING degenerate scalar vectorizers.
  4. Levels-matched: best-3 vectorizers vs 3 filtrations (ECG200) /
     best-2 vs 2 (MNIST).
  5. Swap-one-stage-hold-others-at-best deltas: for each stage, hold
     the other two at their marginal-best level and sweep this stage.

Datasets (repeated-CV, the headline ones):
  * ECG200 r=25 : data/tda/repeated_cv_r25.db  (3 fil x 7 vec x 4 clf)
  * MNIST  r=5  : data/tda/mnist_repeated_cv.db (2 fil x 7 vec x 4 clf)
  * ECG5000 single-split: data/tda/ecg5000_balanced.db (2 fil x 3 vec
    x 2 clf, 2 cells failed) — the 24.89pp headline.

Additive-only: new script, writes /tmp/tda_A1_equal_footing.md + JSON.
No DBs or committed code are touched.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats as sstats

DATA = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda")
OUT_MD = Path("/tmp/tda_A1_equal_footing.md")
OUT_JSON = Path("/tmp/tda_A1_equal_footing.json")

DEGENERATE_SCALARS = {"amplitude", "persistence_entropy"}


def load_std(db: Path) -> pd.DataFrame:
    conn = sqlite3.connect(str(db))
    df = pd.read_sql_query(
        """SELECT r.filtration, r.vectorizer, r.classifier, r.repetition,
                  f.accuracy
           FROM runs r JOIN fold_results f ON f.run_id = r.run_id
           WHERE r.finished_at IS NOT NULL""", conn)
    conn.close()
    return df


def pooled_per_config(df: pd.DataFrame) -> pd.DataFrame:
    """Per-configuration mean accuracy, pooling folds AND reps."""
    return (df.groupby(["filtration", "vectorizer", "classifier"],
                       as_index=False)["accuracy"].mean())


def marginal(df: pd.DataFrame, stage: str) -> pd.Series:
    """Stage-level mean accuracy (per-config means grouped by level)."""
    return df.groupby(stage)["accuracy"].mean()


def stage_range(series: pd.Series) -> float:
    return round(float((series.max() - series.min()) * 100), 2)


def main_omega2(df: pd.DataFrame) -> dict:
    """Main-effect omega^2 per stage over per-config means (3-way)."""
    y = df["accuracy"].to_numpy()
    grand = y.mean()
    n = len(y)
    ss_tot = float(((y - grand) ** 2).sum())
    factors = ["filtration", "vectorizer", "classifier"]
    levels = {f: sorted(df[f].unique()) for f in factors}
    nlev = {f: len(v) for f, v in levels.items()}

    def ss_group(cols):
        s = 0.0
        for _, grp in df.groupby(cols):
            s += len(grp) * (grp["accuracy"].mean() - grand) ** 2
        return float(s)

    ss_main = {f: ss_group([f]) for f in factors}
    ss_explained = sum(ss_main.values())
    ss_err = max(ss_tot - ss_explained, 0.0)
    df_err = n - 1 - sum(nlev[f] - 1 for f in factors)
    ms_err = ss_err / df_err if df_err > 0 else float("nan")
    out = {}
    for f in factors:
        df_ = nlev[f] - 1
        ms = ss_main[f] / df_
        out[f] = {
            "omega2": round((ss_main[f] - df_ * ms_err) / (ss_tot + ms_err), 4),
            "eta2": round(ss_main[f] / ss_tot, 4),
            "F": round(ms / ms_err, 2) if ms_err > 0 else float("nan"),
            "p": float(sstats.f.sf(ms / ms_err, df_, df_err)) if ms_err > 0
            else float("nan"),
            "df": df_,
        }
    return out


def swap_one_stage(pc: pd.DataFrame, stage: str,
                   others: list) -> dict:
    """Hold the other two stages at their marginal-best level, sweep this
    stage, and report the resulting accuracy range + level values."""
    # marginal-best level = highest marginal accuracy among the OTHER stages
    res = {}
    for other in others:
        marg = marginal(pc, other)
        best_level = float(marg.idxmax())
        # filter to configs where the other stages are at their best
        mask = pd.Series(True, index=pc.index)
        for o in others:
            mask &= pc[o] == marg.idxmax() if False else True
        # build masked frame: keep configs where 'others' are at best level
        sub = pc.copy()
        for o in others:
            best_o = marginal(pc, o).idxmax()
            sub = sub[sub[o] == best_o]
        if len(sub) == 0:
            res[stage] = {"range": None, "levels": {}}
            continue
        m = sub.groupby(stage)["accuracy"].mean()
        res = {"range": stage_range(m),
               "levels": {lv: round(float(a) * 100, 2)
                          for lv, a in m.items()},
               "held": {o: marginal(pc, o).idxmax() for o in others}}
    return res


def analyze(name: str, df: pd.DataFrame,
            fil_levels_expected: int) -> dict:
    pc = pooled_per_config(df)
    out = {"name": name, "n_configs": len(pc), "per_config": pc}

    # 1. omega^2 lead
    out["omega2"] = main_omega2(pc)

    # 2. marginal ranges, all levels
    out["marginal_ranges"] = {}
    for s in ["filtration", "vectorizer", "classifier"]:
        out["marginal_ranges"][s + "_all"] = stage_range(marginal(pc, s))
    # level values
    out["level_values"] = {}
    for s in ["filtration", "vectorizer", "classifier"]:
        m = marginal(pc, s)
        out["level_values"][s] = {str(lv): round(float(a) * 100, 2)
                                  for lv, a in m.items()}

    # 3. vectorizer range excluding degenerate scalars
    pc_nd = pc[~pc.vectorizer.isin(DEGENERATE_SCALARS)]
    out["vec_nondegenerate_range"] = stage_range(marginal(pc_nd, "vectorizer"))
    out["n_vec_nondegenerate"] = pc_nd.vectorizer.nunique()
    out["degenerate_scalars"] = sorted(
        DEGENERATE_SCALARS & set(pc.vectorizer.unique()))

    # 4. levels-matched: best-3 vectorizers vs N filtrations
    vm = marginal(pc, "vectorizer").sort_values(ascending=False)
    best3 = vm.head(3)
    out["best3_vec"] = {str(k): round(float(v) * 100, 2)
                        for k, v in best3.items()}
    out["best3_vec_range"] = stage_range(best3)
    fm = marginal(pc, "filtration")
    out["fil_range"] = stage_range(fm)
    out["fil_n"] = len(fm)
    out["levels_matched_n"] = min(3, len(fm))
    # best-N vectorizers (N = number of filtrations) vs all filtrations
    bestN = vm.head(out["fil_n"])
    out[f"bestN_vec_range"] = stage_range(bestN)
    out["bestN_vec"] = {str(k): round(float(v) * 100, 2)
                        for k, v in bestN.items()}

    # 5. swap-one-stage-hold-others-at-best deltas (equal-footing:
    #    exclude degenerate scalar vectorizers so the vectorizer arm is
    #    not dominated by a scalar floor; "best" level = marginal-best
    #    on the non-degenerate data).
    pc_eq = pc[~pc.vectorizer.isin(DEGENERATE_SCALARS)]
    out["swap"] = {}
    for stage, others in [("filtration", ["vectorizer", "classifier"]),
                          ("vectorizer", ["filtration", "classifier"]),
                          ("classifier", ["filtration", "vectorizer"])]:
        sub = pc_eq.copy()
        for o in others:
            best_o = marginal(pc_eq, o).idxmax()
            sub = sub[sub[o] == best_o]
        out["swap"][stage] = {"held": {
            o: marginal(pc_eq, o).idxmax() for o in others},
            "range": stage_range(marginal(sub, stage)),
            "levels": {str(lv): round(float(a) * 100, 2)
                       for lv, a in marginal(sub, stage).items()}}
    return out


def main() -> None:
    results = {}
    # ECG200 r=25
    df = load_std(DATA / "repeated_cv_r25.db")
    results["ECG200 (r=25)"] = analyze("ECG200 (r=25)", df, 3)
    # MNIST r=5
    dfm = load_std(DATA / "mnist_repeated_cv.db")
    results["MNIST (r=5)"] = analyze("MNIST (r=5)", dfm, 2)

    # ECG5000 single-split (different schema)
    conn = sqlite3.connect(str(DATA / "ecg5000_balanced.db"))
    e5 = pd.read_sql_query(
        "SELECT filtration,vectorizer,classifier,mean_acc "
        "FROM config_summary WHERE status='ok'", conn)
    conn.close()
    e5 = e5.rename(columns={"mean_acc": "accuracy"})
    e5 = e5.groupby(["filtration", "vectorizer", "classifier"],
                    as_index=False)["accuracy"].mean()
    results["ECG5000 (single-split)"] = analyze("ECG5000", e5, 2)

    # ---- render markdown ----
    L = ["# Expansion A1 (#2) — Equal-footing stage statistics", ""]
    L.append("Stage dominance re-measured on an equal footing: omega^2 lead, "
             "marginal ranges over per-config means, ranges EXCLUDING "
             "degenerate scalar vectorizers "
             "(persistence_entropy, amplitude), levels-matched (best-N "
             "vectorizers vs all filtrations), and swap-one-stage-hold-"
             "others-at-best deltas.")
    L.append("")
    L.append("Method: per-configuration accuracy = mean accuracy over all "
             "folds (and reps, for repeated CV). Marginal = stage-level "
             "mean of per-config means. omega^2 is the df-penalised main-"
             "effect effect size over per-config means.")
    L.append("")

    for name, res in results.items():
        L.append(f"## {name}  (N={res['n_configs']} configs)")
        L.append("")
        L.append("**omega^2 lead (main effects, per-config means):**")
        L.append("")
        L.append("| stage | omega^2 | eta^2 | F | p | df |")
        L.append("|---|---|---|---|---|---|")
        for s, e in res["omega2"].items():
            L.append(f"| {s} | {e['omega2']} | {e['eta2']} | {e['F']} | "
                     f"{e['p']:.2e} | {e['df']} |")
        L.append("")
        L.append("**Marginal ranges (pooled per-config means):**")
        L.append("")
        L.append("| stage | all levels | #levels |")
        L.append("|---|---|---|")
        for s in ["filtration", "vectorizer", "classifier"]:
            L.append(f"| {s} | {res['marginal_ranges'][s+'_all']}pp | "
                     f"{len(res['level_values'][s])} |")
        L.append("")

        L.append("**Vectorizer range excluding degenerate scalars** "
                 f"(dropped: {', '.join(res['degenerate_scalars']) or 'none'}): "
                 f"**{res['vec_nondegenerate_range']}pp** "
                 f"over {res['n_vec_nondegenerate']} vectorizers "
                 f"(all-levels range {res['marginal_ranges']['vectorizer_all']}pp).")
        L.append("")
        L.append("**Vectorizer marginal accuracies (per-config mean, %):**  ")
        L.append("`" + "; ".join(
            f"{k}={v}" for k, v in res["level_values"]["vectorizer"].items()) + "`")
        L.append("")

        L.append("**Levels-matched:**")
        L.append(f"- best-{res['fil_n']} vectorizers "
                 f"({', '.join(res['bestN_vec'])}) range "
                 f"**{res['bestN_vec_range']}pp** vs all {res['fil_n']} "
                 f"filtrations range **{res['fil_range']}pp**.")
        L.append("")
        L.append("**Swap-one-stage-hold-others-at-best deltas:**")
        L.append("")
        L.append("| swapped stage | held at best (marginal) | range |")
        L.append("|---|---|---|")
        for s, sw in res["swap"].items():
            held = ", ".join(f"{k}={v}" for k, v in sw["held"].items())
            L.append(f"| {s} | {held} | {sw['range']}pp |")
        L.append("")

    OUT_MD.write_text("\n".join(L) + "\n")
    # JSON: keep only the summary (drop heavy per_config frame)
    slim = {}
    for name, res in results.items():
        slim[name] = {k: v for k, v in res.items() if k != "per_config"}
    OUT_JSON.write_text(json.dumps(slim, indent=2, default=float))
    print("\n".join(L))
    print(f"\nwrote {OUT_MD}, {OUT_JSON}")


if __name__ == "__main__":
    main()
