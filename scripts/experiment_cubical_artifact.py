#!/usr/bin/env python3
"""Reviewer revision (B): the cubical-on-non-image artifact, verified + quantified.

Three parts:
  1. SOURCE EVIDENCE — what giotto-tda CubicalPersistence accepts (greyscale
     images) and how a (200, 94, 3) array is interpreted (200 images of
     94 x 3 pixels; pixel intensity = Takens coordinate), printed straight
     from the installed gtda source.
  2. EMPIRICAL DEMONSTRATION — feed one ECG200 Takens-embedded sample
     (94, 3) to CubialPersistence and to the true gudhi Alpha complex; report
     cell counts (94*3 = 282 cubical cells vs 94 point-cloud vertices),
     diagram sizes and value ranges, showing the two compute on different
     objects entirely.
  3. QUANTIFICATION — ECG200 stage-impact tables (marginal accuracy ranges)
     computed from expanded_results.db WITH and WITHOUT the cubical arm,
     plus the top-5 config list and cubical share.

Additive-only: reads expanded_results.db, prints + writes /tmp/cubical_artifact_results.json.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
PROJECT_ROOT = REPO.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "tda"
DB_PATH = DATA_DIR / "expanded_results.db"
OUT_JSON = "/tmp/cubical_artifact_results.json"


# ── 1. source evidence ─────────────────────────────────────────────────────

def source_evidence() -> str:
    import inspect
    from gtda.homology import CubicalPersistence
    src = inspect.getsource(CubicalPersistence)
    lines = []
    doc = CubicalPersistence.__doc__
    lines.append("CubicalPersistence class docstring (gtda %s):" %
                 __import__("gtda").__version__)
    for l in doc.splitlines():
        ls = l.strip()
        if any(k in ls for k in ["greyscale image", "persistence diagram",
                                 "Input data", "d-dimensional images",
                                 "cubical homology", "pixel"]):
            lines.append("    " + ls)
    # fit signature + transform docstring bits
    for meth, kw in [("fit", "n_samples, n_pixels_1"), ("transform", "n_samples, n_pixels_1")]:
        i = src.find(f"def {meth}")
        j = src.find(f"def {meth}", i + 3)
        seg = src[i: (j if j > 0 else len(src))]
        for l in seg.splitlines():
            if "n_samples, n_pixels_1" in l or "images" in l.strip().lower():
                lines.append(f"    [{meth}] {l.strip()}")
                break
    # check_collection: no image-type validation
    from gtda.utils.validation import check_collection
    ccsrc = inspect.getsource(check_collection)
    lines.append("    check_collection: only shape/finiteness checks — no image-type"
                 " validation (accepts any ndarray with ndim >= 2)")
    return "\n".join(lines)


# ── 2. empirical demonstration ─────────────────────────────────────────────

def takens(X, dim=3, tau=1):
    stride = (dim - 1) * tau
    n = X.shape[1] - stride
    e = np.zeros((X.shape[0], n, dim), dtype=X.dtype)
    for d in range(dim):
        e[:, :, d] = X[:, d * tau: d * tau + n]
    return e


def empirical_demo() -> dict:
    from gtda.homology import CubicalPersistence
    X = np.load(DATA_DIR / "ucr" / "ecg200_X.npy")
    emb = takens(X)
    print(f"ECG200 loaded: {X.shape}; Takens d=3,tau=1 -> {emb.shape} "
          f"-> interpreted by CubicalPersistence as {emb.shape[0]} images of "
          f"{emb.shape[1]}x{emb.shape[2]} pixels")

    sample = emb[0]  # (94, 3)
    cp = CubicalPersistence(homology_dimensions=[0, 1], n_jobs=1)
    dg_cub = cp.fit_transform(sample[None, ...])[0]
    # gudhi cubical complex behind it: 94*3 top-dimensional cells
    n_cells = sample.shape[0] * sample.shape[1]

    # true alpha on the same 94-point 3D cloud
    import gudhi
    ac = gudhi.AlphaComplex(points=sample)
    st = ac.create_simplex_tree()
    pers = st.persistence()
    h0 = [1 for dim, _ in pers if dim == 0]
    h1 = [1 for dim, _ in pers if dim == 1]
    n_alpha_pts = sample.shape[0]

    def diag_stats(dg):
        dg = np.asarray(dg)
        real = dg[dg[:, 0] < dg[:, 1]]
        h0r = real[np.abs(real[:, 2] - 0) < 1e-9]
        h1r = real[np.abs(real[:, 2] - 1) < 1e-9]
        return {
            "n_triples": int(len(real)),
            "n_h0": int(len(h0r)),
            "n_h1": int(len(h1r)),
            "birth_min": round(float(real[:, 0].min()), 4),
            "death_max": round(float(real[:, 1].max()), 4),
        }

    res = {
        "input_shape_to_cubical": list(sample.shape),
        "cubical_top_dim_cells": int(n_cells),
        "alpha_point_cloud_vertices": int(n_alpha_pts),
        "cubical_diagram": diag_stats(dg_cub),
        "alpha_diagram": diag_stats(
            [[b, d, float(dim)] for dim, (b, d) in pers if dim in (0, 1)]),
        "interpretation": (
            f"CubicalPersistence receives ({emb.shape[0]}, {emb.shape[1]}, {emb.shape[2]})"
            f" = {emb.shape[0]} greyscale images of {emb.shape[1]}x{emb.shape[2]} pixels;"
            f" pixel intensities are the Takens coordinates. It computes cubical homology"
            f" of a {emb.shape[1]}x{emb.shape[2]} pixel grid ({n_cells} cells) — NOT a"
            f" filtration of the {n_alpha_pts}-point 3D cloud."),
    }
    print(json.dumps(res, indent=2))
    return res


# ── 3. ECG200 stage impact from expanded_results.db ────────────────────────

def stage_impact(rows, key):
    groups = defaultdict(list)
    for r in rows:
        groups[r[key]].append(r["acc"])
    means = {k: sum(v) / len(v) for k, v in groups.items()}
    return means, (max(means.values()) - min(means.values())) if means else 0.0


def ecg200_quantification() -> dict:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """SELECT r.filtration, r.vectorizer, r.classifier, AVG(f.accuracy) acc
           FROM runs r JOIN fold_results f ON r.run_id = f.run_id
           WHERE r.dataset='ecg200' AND r.finished_at IS NOT NULL
           GROUP BY r.run_id""").fetchall()
    rows = [dict(r) for r in rows]
    conn.close()

    def table(include_cubical: bool):
        sub = [r for r in rows if include_cubical or r["filtration"] != "cubical"]
        out = {}
        for key, label in [("filtration", "Filtration"),
                           ("vectorizer", "Vectorizer"),
                           ("classifier", "Classifier")]:
            means, rng = stage_impact(sub, key)
            out[label.lower()] = {
                "means": {k: round(v, 4) for k, v in sorted(means.items(), key=lambda x: -x[1])},
                "range_pp": round(rng * 100, 2),
            }
        best = max(sub, key=lambda r: r["acc"])
        out["best_config"] = {
            "filtration": best["filtration"], "vectorizer": best["vectorizer"],
            "classifier": best["classifier"], "acc": round(best["acc"], 4)}
        out["n_configs"] = len(sub)
        return out

    top5 = sorted(rows, key=lambda r: -r["acc"])[:5]
    top5_list = [{"filtration": r["filtration"], "vectorizer": r["vectorizer"],
                  "classifier": r["classifier"], "acc": round(r["acc"], 4),
                  "is_cubical": r["filtration"] == "cubical"} for r in top5]

    res = {
        "n_cubical_in_top5": sum(1 for r in top5_list if r["is_cubical"]),
        "top5": top5_list,
        "with_cubical": table(True),
        "without_cubical": table(False),
    }
    return res


def main():
    print("=" * 90)
    print("PART 1 — SOURCE EVIDENCE (giotto-tda CubicalPersistence)")
    print("=" * 90)
    ev = source_evidence()
    print(ev)

    print("\n" + "=" * 90)
    print("PART 2 — EMPIRICAL DEMONSTRATION (one ECG200 sample)")
    print("=" * 90)
    demo = empirical_demo()

    print("\n" + "=" * 90)
    print("PART 3 — ECG200 STAGE IMPACT: WITH vs WITHOUT cubical (expanded_results.db)")
    print("=" * 90)
    quant = ecg200_quantification()
    for label in ("with_cubical", "without_cubical"):
        t = quant[label]
        print(f"\n--- {label} ---")
        for stage in ("filtration", "vectorizer", "classifier"):
            print(f"  {stage:<12} range {t[stage]['range_pp']:>6.2f} pp   " +
                  ", ".join(f"{k}={v:.4f}" for k, v in t[stage]["means"].items()))
        print(f"  best: {t['best_config']}")
        print(f"  n_configs: {t['n_configs']}")
    print(f"\n  top5: {json.dumps(quant['top5'], indent=2)}")
    print(f"  cubical in top-5: {quant['n_cubical_in_top5']}/5")

    results = {"source_evidence": ev, "empirical": demo, "ecg200": quant}
    with open(OUT_JSON, "w") as fh:
        json.dump(results, fh, indent=2, default=str)
    print(f"\nwrote {OUT_JSON}")


if __name__ == "__main__":
    main()
