#!/usr/bin/env python3
"""Analysis for expansion B3 (#10) — hyperparameter-sensitivity arm.

Reads data/tda/hyperparam_sweep.db and computes, per dataset:
  - per-config mean accuracy (AVG over folds),
  - per-vectorizer classifier-averaged mean accuracy at the PAPER DEFAULT
    hyperparameters,
  - per-vectorizer classifier-averaged mean accuracy at each vectorizer's
    BEST-TUNED hyperparameter (argmax over its one-at-a-time grid),
  - the VECTORIZER marginal range (max - min) at defaults vs at best-tuned.

The vectorizer marginal range = range of stage-level means of per-config means
(1 filtration, 2 classifiers per vectorizer here; vectorizer mean = avg of the
per-config means over the classifiers).

Selection-bias note: "best-tuned" is chosen on the SAME CV folds used to score
the range, so each vectorizer's best value carries mild selection optimism
(stronger for vectorizers with more grid variants). Reported as such.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

DB = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda/hyperparam_sweep.db")

PAPER_DEFAULTS = {
    "persistence_image": {"sigma": 0.1, "n_bins": 20},
    "persistence_landscape": {"n_layers": 3, "n_bins": 50},
    "silhouette": {"n_bins": 50},
    "betti_curve": {"n_bins": 50},
}

GRID_VARIANTS = {
    "persistence_image": [
        {"sigma": 0.05, "n_bins": 20}, {"sigma": 0.1, "n_bins": 20},
        {"sigma": 0.2, "n_bins": 20}, {"sigma": 0.5, "n_bins": 20},
        {"sigma": 0.1, "n_bins": 10}, {"sigma": 0.1, "n_bins": 50},
    ],
    "persistence_landscape": [
        {"n_layers": 1, "n_bins": 50}, {"n_layers": 3, "n_bins": 50},
        {"n_layers": 5, "n_bins": 50}, {"n_layers": 3, "n_bins": 20},
        {"n_layers": 3, "n_bins": 100},
    ],
    "silhouette": [{"n_bins": 10}, {"n_bins": 20}, {"n_bins": 50}, {"n_bins": 100}],
    "betti_curve": [{"n_bins": 10}, {"n_bins": 20}, {"n_bins": 50}, {"n_bins": 100}],
}


def connect() -> sqlite3.Connection:
    return sqlite3.connect(str(DB))


def per_config_mean(conn, dataset):
    """{(vectorizer, clf, vec_kwargs_json): mean_acc_pct}"""
    rows = conn.execute(
        "SELECT r.vectorizer, r.classifier, r.vectorizer, m.pipeline_params, "
        "AVG(f.accuracy) FROM runs r "
        "JOIN run_metadata m ON r.run_id = m.run_id "
        "JOIN fold_results f ON f.run_id = r.run_id "
        "WHERE r.dataset=? AND r.finished_at IS NOT NULL "
        "GROUP BY r.run_id", (dataset,)).fetchall()
    out = {}
    for vec_name, clf_name, _v2, pparams, avg in rows:
        kwargs = {k: v for k, v in json.loads(pparams)["vectorizer"].items() if k != "name"}
        key = (vec_name, clf_name, json.dumps(kwargs, sort_keys=True))
        out[key] = avg * 100.0
    return out


def vec_mean_at(pconfig, vec_name, kwargs):
    """Classifier-averaged vectorizer mean (over random_forest, svm_rbf)."""
    sig = json.dumps(kwargs, sort_keys=True)
    cls = ("random_forest", "svm_rbf")
    vals = [pconfig[(vec_name, c, sig)] for c in cls if (vec_name, c, sig) in pconfig]
    return sum(vals) / len(vals) if vals else None


def main():
    conn = connect()
    datasets = ["ecg200", "mnist_01"]
    for dataset in datasets:
        pconfig = per_config_mean(conn, dataset)
        print("=" * 78)
        print(f"DATASET: {dataset}   (n per-config cells = {len(pconfig)})")
        print("=" * 78)
        print(f"{'vectorizer':<24}{'setting':<22}{'RF':>8}{'svm':>8}{'mean':>8}")
        # Defaults
        default_means = {}
        for v in GRID_VARIANTS:
            d = PAPER_DEFAULTS[v]
            m = vec_mean_at(pconfig, v, d)
            default_means[v] = m
            sig = json.dumps(d, sort_keys=True)
            rf = pconfig.get((v, "random_forest", sig))
            sv = pconfig.get((v, "svm_rbf", sig))
            print(f"  {v:<22}{json.dumps(d):<22}{rf and round(rf,2):>8}"
                  f"{sv and round(sv,2):>8}{m and round(m,2):>8}  [DEFAULT]")
        dmin, dmax = min(default_means.values()), max(default_means.values())
        print(f"  -> vectorizer marginal range @ default: {dmax-dmin:.2f} pp "
              f"[{dmin:.2f}, {dmax:.2f}]")
        print()
        # Best-tuned per vectorizer
        best_means = {}
        best_cfg = {}
        print(f"{'vectorizer':<24}{'best setting':<24}{'best mean':>10}   variant means")
        for v in GRID_VARIANTS:
            means = {}
            for kw in GRID_VARIANTS[v]:
                m = vec_mean_at(pconfig, v, kw)
                means[json.dumps(kw, sort_keys=True)] = m
            # pick best
            bkey = max(means, key=lambda k: means[k] if means[k] is not None else -1)
            best_means[v] = means[bkey]
            best_cfg[v] = json.loads(bkey)
            allstr = ", ".join(f"{kk}={mm:.2f}" if mm is not None else f"{kk}=NA"
                               for kk, mm in sorted(means.items()))
            print(f"  {v:<22}{json.dumps(best_cfg[v]):<24}{best_means[v]:>10.2f}   {allstr}")
        bmin, bmax = min(best_means.values()), max(best_means.values())
        print(f"  -> vectorizer marginal range @ best-tuned: {bmax-bmin:.2f} pp "
              f"[{bmin:.2f}, {bmax:.2f}]")
        print(f"  -> RANGE change (tuned - default): {(bmax-bmin)-(dmax-dmin):+.2f} pp")
        print()
        # Per-classifier marginal ranges (default vs best-tuned) for transparency
        print("  PER-CLASSIFIER vectorizer marginal range:")
        for clf in ("random_forest", "svm_rbf"):
            def_vals = []
            best_vals = []
            for v in GRID_VARIANTS:
                sig = json.dumps(PAPER_DEFAULTS[v], sort_keys=True)
                def_vals.append(pconfig.get((v, clf, sig)))
                # best for this classifier only
                cv = {}
                for kw in GRID_VARIANTS[v]:
                    s = json.dumps(kw, sort_keys=True)
                    cv[s] = pconfig.get((v, clf, s))
                bkey = max(cv, key=lambda k: cv[k] if cv[k] is not None else -1)
                best_vals.append(cv[bkey])
            dv = [x for x in def_vals if x is not None]
            bv = [x for x in best_vals if x is not None]
            print(f"    {clf:<10} default range={max(dv)-min(dv):.2f} pp  "
                  f"best-tuned range={max(bv)-min(bv):.2f} pp")
        print()
    conn.close()


if __name__ == "__main__":
    main()
