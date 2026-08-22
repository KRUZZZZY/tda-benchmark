#!/usr/bin/env python3
"""#13 — Predictive theory: does vectorizer stability predict empirical accuracy range?

For every vectorizer executed in the sweeps, this script computes a
THEORY-side quantity — a stability / Lipschitz-constant estimate taken from
the literature already cited in the dissertation (Ch.2, §2.3 "Vectorization
Methods") — and correlates it (Spearman rho + 95% percentile-bootstrap CI)
with the vectorizer's EMPIRICAL marginal accuracy range:

  * ECG200 from data/tda/repeated_cv_r25.db (25 reps x 5 folds),
  * MNIST from data/tda/expanded_results.db (dataset mnist_01, rep=1).

Number-derivation conventions (identical to analysis_repeated_cv_r25.py /
analysis_multidataset_friedman.py):
  * per-config accuracy = AVG(f.accuracy) per run_id (never MAX over folds),
  * per-vectorizer empirical range = max - min over the per-config means of
    all configs sharing that vectorizer (i.e. across filtration x classifier),
    in percentage points (pp). For r25 the per-config mean pools ALL folds of
    ALL 25 reps; the rep-level SD across the 25 per-rep config means is
    reported as a secondary dispersion measure.
  * empirical mean = mean of the per-config means sharing that vectorizer.

Theory-side stability constants (literature values cited in the paper; the
paper's Ch.2 has no numeric table of constants, so each entry documents its
source and assumption):

  vectorizer              constant  meaning / source
  ----------------------  --------  -------------------------------------------
  persistence_landscape   1        1-Lipschitz in L-infinity / bottleneck
                                   (Bubenik 2015; dissertation: "each lambda_m
                                   is 1-Lipschitz")
  betti_curve             1        L1 Betti-function stability constant 1
                                   (Cohen-Steiner et al.; standard result)
  silhouette              1        L-infinity stability of the q-weighted
                                   silhouette, q=1, normalised (Chazal et al.
                                   2015; ASSUMED constant 1 — see caveat in
                                   report)
  amplitude               1        bottleneck distance to the empty diagram is
                                   1-Lipschitz w.r.t. bottleneck (triangle
                                   inequality; dissertation eq. amplitude)
  persistence_image       0.283    2*sqrt(2)*sigma*||w||_inf with sigma=0.1,
                                   ||w||_inf = 1 (Adams et al. 2017, Thm 2;
                                   linear in sigma — the paper's sigma=0.1)
  persistence_entropy     +inf     NO Lipschitz bound w.r.t. bottleneck
                                   (Rucco et al. 2016; continuous but not
                                   Lipschitz in general)
  persistence_statistics  +inf     no stability result for coordinate-wise
                                   summary statistics (ASSUMED none)

Interpretation of rho: a NEGATIVE rho(constant, empirical range) supports the
hypothesis "more stable vectorizers (smaller Lipschitz constant) have smaller
empirical dispersion across pipeline contexts"; a NEGATIVE rho(constant, mean
accuracy) would support "stability predicts higher typical accuracy". The
verdict sentence states the observed direction and whether the 95% CI
excludes zero (n=7 vectorizers per dataset — CIs are wide; treat as
exploratory).

Outputs (additive-only, read-only):
  * data/tda/predictive_theory_scatter.csv  (per-vectorizer theory + empirical)
  * /tmp/tda_predictive_theory_report.md    (full report + verdict)

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/analysis_predictive_theory.py

Expected runtime: ~1-2 min (pure SQLite aggregation + scipy; no sweeps, no
training, nothing written to the result DBs).
"""

from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

import numpy as np
from scipy import stats as sstats

DATA_DIR = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda")
DB_R25 = DATA_DIR / "repeated_cv_r25.db"     # ECG200, 84 configs x 25 reps
DB_EXP = DATA_DIR / "expanded_results.db"    # 616 configs incl. mnist_01 (56)
OUT_CSV = DATA_DIR / "predictive_theory_scatter.csv"
OUT_MD = Path("/tmp/tda_predictive_theory_report.md")

RNG_SEED = 42
N_BOOT = 10_000

# ── theory-side table ─────────────────────────────────────────────────────────
# constant: stability/Lipschitz constant w.r.t. the bottleneck distance;
# +inf = no finite Lipschitz bound (documented assumption). `source` gives the
# literature anchor exactly as cited in the dissertation Ch.2 / this header.
THEORY = {
    "persistence_landscape": {
        "constant": 1.0,
        "source": "Bubenik 2015 (1-Lipschitz, L-inf)",
    },
    "betti_curve": {
        "constant": 1.0,
        "source": "Cohen-Steiner et al. (L1 Betti stability)",
    },
    "silhouette": {
        "constant": 1.0,
        "source": "Chazal et al. 2015 (assumed 1-Lipschitz, q=1)",
    },
    "amplitude": {
        "constant": 1.0,
        "source": "triangle inequality (bottleneck-to-empty)",
    },
    "persistence_image": {
        "constant": 2.0 * np.sqrt(2.0) * 0.1,  # 2*sqrt(2)*sigma*||w||_inf, sigma=0.1
        "source": "Adams et al. 2017 Thm 2 (sigma=0.1, ||w||_inf=1)",
    },
    "persistence_entropy": {
        "constant": np.inf,
        "source": "Rucco et al. 2016 (no Lipschitz bound)",
    },
    "persistence_statistics": {
        "constant": np.inf,
        "source": "assumed none (summary stats, no stability result)",
    },
}


def per_vectorizer_empirics(db: Path, dataset: str) -> dict[str, dict]:
    """Per-vectorizer empirical range (pp) + mean (%) + rep-SD from a DB.

    per-config mean = AVG(f.accuracy) per run_id (pooled over all reps/folds);
    per-vectorizer range = max - min over the per-config means of the configs
    that share the vectorizer; rep-SD (r25 only, when repetition>1) = SD of
    the per-vectorizer means computed within each repetition.
    """
    conn = sqlite3.connect(str(db))
    rows = conn.execute(
        "SELECT r.vectorizer, r.repetition, AVG(f.accuracy) "
        "FROM runs r JOIN fold_results f ON f.run_id = r.run_id "
        "WHERE r.dataset = ? AND r.finished_at IS NOT NULL "
        "GROUP BY r.run_id", (dataset,)).fetchall()
    conn.close()
    if not rows:
        return {}

    per_cfg: dict[str, list[float]] = {}          # vec -> [per-config means]
    per_rep: dict[str, dict[int, list[float]]] = {}  # vec -> rep -> [means]
    for vec, rep, acc in rows:
        per_cfg.setdefault(vec, []).append(acc)
        per_rep.setdefault(vec, {}).setdefault(rep, []).append(acc)

    out = {}
    for vec, means in per_cfg.items():
        rep_means = [np.mean(v) for v in per_rep[vec].values()]
        out[vec] = {
            "range_pp": (max(means) - min(means)) * 100.0,
            "mean_acc": np.mean(means) * 100.0,
            "sd_over_reps_pp": (np.std(rep_means) * 100.0
                                if len(rep_means) > 1 else np.nan),
            "n_configs": len(means),
            "n_reps": len(rep_means),
        }
    return out


def spearman_with_bootstrap(x: list, y: list, seed: int = RNG_SEED,
                            n_boot: int = N_BOOT) -> dict:
    """Spearman rho + 95% percentile bootstrap CI over units (vectorizers).

    inf constants rank naturally (scipy ranks internally). Bootstrap resamples
    the n units WITH replacement; draws with zero variance on either axis
    (degenerate — Spearman undefined) are dropped and counted. With n=7 the
    CIs are wide; report them as such.
    """
    rng = np.random.default_rng(seed)
    xa, ya = np.asarray(x, float), np.asarray(y, float)
    rho, p = sstats.spearmanr(xa, ya)
    n = len(xa)
    boots, dropped = [], 0
    for _ in range(n_boot):
        idx = rng.integers(0, n, size=n)
        bx, by = xa[idx], ya[idx]
        if np.unique(bx).size < 2 or np.unique(by).size < 2:
            dropped += 1
            continue
        boots.append(sstats.spearmanr(bx, by).statistic)
    boots = np.array(boots)
    lo, hi = np.percentile(boots, [2.5, 97.5]) if boots.size else (np.nan, np.nan)
    return {"rho": rho, "p": p, "ci95": (float(lo), float(hi)),
            "n": n, "n_boot": n_boot, "dropped": dropped}


def main() -> None:
    panels = {
        "ecg200_r25": (DB_R25, "ecg200"),
        "mnist_01_exp": (DB_EXP, "mnist_01"),
    }
    rows_out, report = [], []
    report.append("# #13 — Predictive theory: stability vs empirical range\n")
    report.append("Theory constant: stability/Lipschitz bound w.r.t. bottleneck "
                  "(smaller = more stable; +inf = no finite bound).\n"
                  "Empirical range: max - min (pp) of per-config means over the "
                  "configs sharing the vectorizer (per-config = AVG(f.accuracy) "
                  "per run_id).\n"
                  "Spearman rho + 95% percentile bootstrap CI (10,000 draws, "
                  "seed 42, degenerate draws dropped).\n")

    for panel_name, (db, ds) in panels.items():
        empir = per_vectorizer_empirics(db, ds)
        vecs = [v for v in THEORY if v in empir]
        if not vecs:
            report.append(f"\n## {panel_name}: NO vectorizers found in {db.name} "
                          f"for dataset {ds} — skipping.\n")
            continue
        consts = [THEORY[v]["constant"] for v in vecs]
        ranges = [empir[v]["range_pp"] for v in vecs]
        means = [empir[v]["mean_acc"] for v in vecs]

        report.append(f"\n## {panel_name} ({db.name}, dataset={ds})\n")
        report.append("| vectorizer | theory const | emp. range (pp) | "
                      "mean acc (%) | rep-SD (pp) | n_cfg |")
        report.append("|---|---|---|---|---|---|")
        for v in vecs:
            c = THEORY[v]["constant"]
            c_s = "inf" if np.isinf(c) else f"{c:.3f}"
            sds = empir[v]["sd_over_reps_pp"]
            sds_s = "—" if np.isnan(sds) else f"{sds:.2f}"
            report.append(f"| {v} | {c_s} | {empir[v]['range_pp']:.2f} | "
                          f"{empir[v]['mean_acc']:.2f} | {sds_s} | "
                          f"{empir[v]['n_configs']} |")

        for _, y, yname in [("range_pp", ranges, "empirical range"),
                            ("mean_acc", means, "mean accuracy")]:
            res = spearman_with_bootstrap(consts, y)
            report.append(
                f"- Spearman rho(theory const, {yname}) = {res['rho']:+.3f} "
                f"(p={res['p']:.3f}), 95% CI [{res['ci95'][0]:+.3f}, "
                f"{res['ci95'][1]:+.3f}] — {res['n_boot'] - res['dropped']}/"
                f"{res['n_boot']} usable bootstrap draws.\n")
        for v, c in zip(vecs, consts):
            rows_out.append({
                "panel": panel_name, "vectorizer": v,
                "theory_constant": c,
                "empirical_range_pp": empir[v]["range_pp"],
                "mean_acc_pct": empir[v]["mean_acc"],
                "source": THEORY[v]["source"],
            })

    # verdict across panels (pooled units: 14 = 7 vecs x 2 datasets)
    pooled_consts, pooled_ranges = [], []
    for panel_name, (db, ds) in panels.items():
        empir = per_vectorizer_empirics(db, ds)
        for v in THEORY:
            if v in empir:
                pooled_consts.append(THEORY[v]["constant"])
                pooled_ranges.append(empir[v]["range_pp"])
    res_pooled = spearman_with_bootstrap(pooled_consts, pooled_ranges)
    rho, (lo, hi) = res_pooled["rho"], res_pooled["ci95"]
    excl_zero = not (lo <= 0.0 <= hi)
    direction = ("negative" if rho < 0 else "positive")
    support = ("supports" if (rho < 0 and excl_zero) else
               "does NOT support" if (rho > 0 and excl_zero) else
               "provides NO clear evidence for/against")
    verdict = (
        f"Pooled across ECG200 (r25) and MNIST (expanded_results), "
        f"Spearman rho(stability constant, empirical range) = {rho:+.3f} "
        f"(95% CI [{lo:+.3f}, {hi:+.3f}], n={res_pooled['n']} vectorizer-"
        f"dataset units). The association is {direction} and the CI "
        f"{'excludes' if excl_zero else 'includes'} zero: the data "
        f"{support} the hypothesis that stability (a smaller Lipschitz "
        f"constant) predicts a smaller empirical accuracy range. Caveat: "
        f"n=7 vectorizers per dataset makes the CIs wide; the two +inf "
        f"entries (entropy, statistics) carry the least-stable ranks, so "
        f"the result is driven by the landscape/image/amplitude spread."
    )
    report.append("\n## Verdict\n" + verdict + "\n")

    with open(OUT_CSV, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["panel", "vectorizer",
                                           "theory_constant",
                                           "empirical_range_pp",
                                           "mean_acc_pct", "source"])
        w.writeheader()
        for r in rows_out:
            w.writerow(r)

    text = "\n".join(report)
    OUT_MD.write_text(text + "\n")
    print(text)
    print(f"\nwrote {OUT_CSV}, {OUT_MD}")


if __name__ == "__main__":
    main()
