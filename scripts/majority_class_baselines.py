#!/usr/bin/env python3
"""A9 — Majority-class baseline accuracy for every dataset in the paper.

A trivial classifier that always predicts the majority class achieves
max(class counts)/n accuracy. This is the floor every reported accuracy must
be read against. Computed for every dataset used in the paper:

  * ecg200              (expected 66.5% = 133/200; executed y is {-1,1})
  * mnist_01            (expected 50%   = 200/400)
  * sphere_torus_n0/n5/n15/n30 (expected 50%; executed y is 99/101 ->
    50.5% — see discrepancy note)
  * ecg5000             (computed exactly from the 5000-sample y)
  * fashion_mnist       (present in data/tda/images/ but NOT used in any
    results DB / paper sweep — reported for completeness with
    used_in_paper=false)

Output: data/tda/majority_class_baselines.json (NEW) + printed table.
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent  # AI_KOS_PROJECT
DATA = PROJECT_ROOT / "data" / "tda"
OUT = DATA / "majority_class_baselines.json"

# datasets used in the paper's sweep (from expanded_results.db) + ecg5000
try:
    con = sqlite3.connect(DATA / "expanded_results.db")
    swept = {r[0] for r in con.execute("SELECT DISTINCT dataset FROM runs")}
    con.close()
except Exception:  # pragma: no cover
    swept = set()


def majority_stats(y: np.ndarray) -> dict:
    classes, counts = np.unique(y, return_counts=True)
    i = int(np.argmax(counts))
    n = int(len(y))
    return {
        "n": n,
        "n_classes": int(len(classes)),
        "class_labels": [int(c) for c in classes.tolist()],
        "class_counts": [int(c) for c in counts.tolist()],
        "majority_class": int(classes[i]),
        "majority_share_pct": round(100.0 * counts[i] / n, 4),
    }


def main() -> None:
    specs = [
        ("ecg200", DATA / "ucr" / "ecg200_y.npy", 66.5,
         "executed y is {-1,1}; 133/200 class +1"),
        ("mnist_01", DATA / "images" / "mnist_01_y.npy", 50.0,
         "400 samples, 200 per class"),
        ("sphere_torus_n0", DATA / "synthetic" / "sphere_torus_noise0_y.npy",
         50.0, "executed y is 99 spheres / 101 tori (not 100/100)"),
        ("sphere_torus_n5", DATA / "synthetic" / "sphere_torus_noise5_y.npy",
         50.0, "executed y is 99 spheres / 101 tori (not 100/100)"),
        ("sphere_torus_n15", DATA / "synthetic" / "sphere_torus_noise15_y.npy",
         50.0, "executed y is 99 spheres / 101 tori (not 100/100)"),
        ("sphere_torus_n30", DATA / "synthetic" / "sphere_torus_noise30_y.npy",
         50.0, "executed y is 99 spheres / 101 tori (not 100/100)"),
        ("ecg5000", DATA / "ucr2" / "ecg5000_y.npy", None,
         "computed exactly; full 5000-sample distribution 2919/1767/96/194/24"),
        ("fashion_mnist", DATA / "images" / "fashion_mnist_y.npy", 10.0,
         "10 balanced classes x 7000; NOT used in any results DB"),
    ]

    results = {}
    print(f"{'dataset':22s} {'n':>6s} {'classes':>8s} {'maj class':>10s} "
          f"{'share':>9s} {'expected':>9s} {'used':>5s}")
    print("-" * 78)
    for name, path, expected, note in specs:
        y = np.load(path)
        s = majority_stats(y)
        used = name in swept or name == "ecg5000"
        disc = None
        if expected is not None and abs(s["majority_share_pct"] - expected) > 1e-9:
            disc = (f"executed majority share {s['majority_share_pct']}% "
                    f"!= expected {expected}%")
        results[name] = {
            **s,
            "expected_pct": expected,
            "used_in_paper": used,
            "discrepancy_vs_expected": disc,
            "note": note,
        }
        print(f"{name:22s} {s['n']:6d} {s['n_classes']:8d} "
              f"{s['majority_class']:10d} {s['majority_share_pct']:8.2f}% "
              f"{str(expected) if expected is not None else '-':>8s} "
              f"{str(used):>5s}")
        if disc:
            print(f"  ! {disc}")

    OUT.write_text(json.dumps(results, indent=2) + "\n")
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    sys.exit(main())
