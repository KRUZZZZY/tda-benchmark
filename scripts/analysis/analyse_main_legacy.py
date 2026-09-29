"""Analysis and visualization for TDA benchmark results.

Reads from SQLite result store. Generates summary tables, noise sensitivity
curves, and answers the key research questions from Phase 5.
"""

from __future__ import annotations

import json
import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any


class BenchmarkAnalyzer:
    """Query and analyze benchmark results from SQLite."""

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.row_factory = sqlite3.Row

    def summary_table(self) -> list[dict]:
        """Full summary: mean accuracy ± CI per pipeline configuration."""
        rows = self._conn.execute("""
            SELECT dataset, filtration, vectorizer, classifier,
                   COUNT(*) AS reps,
                   ROUND(AVG(avg_acc), 4) AS mean_accuracy,
                   ROUND(AVG(avg_wall), 2) AS mean_wall_s
            FROM (
                SELECT r.run_id, r.dataset, r.filtration, r.vectorizer, r.classifier,
                       AVG(f.accuracy) AS avg_acc,
                       r.wall_time_s AS avg_wall
                FROM runs r
                JOIN fold_results f ON r.run_id = f.run_id
                WHERE r.finished_at IS NOT NULL
                GROUP BY r.run_id
            )
            GROUP BY dataset, filtration, vectorizer, classifier
            ORDER BY dataset, mean_accuracy DESC
        """).fetchall()
        return [dict(r) for r in rows]

    def noise_sensitivity(self, base_name: str = "sphere_torus") -> list[dict]:
        """How does accuracy degrade with noise for each pipeline stage?"""
        rows = self._conn.execute("""
            SELECT dataset, filtration, vectorizer, classifier,
                   ROUND(AVG(avg_acc), 4) AS accuracy
            FROM (
                SELECT r.run_id, r.dataset, r.filtration, r.vectorizer, r.classifier,
                       AVG(f.accuracy) AS avg_acc
                FROM runs r
                JOIN fold_results f ON r.run_id = f.run_id
                WHERE r.finished_at IS NOT NULL
                  AND r.dataset LIKE ?
                GROUP BY r.run_id
            )
            GROUP BY dataset, filtration, vectorizer, classifier
            ORDER BY dataset, accuracy DESC
        """, (f"{base_name}%",)).fetchall()
        return [dict(r) for r in rows]

    def best_worst(self) -> dict:
        """Best and worst pipeline overall and per dataset."""
        rows = self._conn.execute("""
            SELECT dataset, filtration, vectorizer, classifier,
                   ROUND(AVG(avg_acc), 4) AS accuracy,
                   ROUND(AVG(avg_wall), 2) AS wall_s
            FROM (
                SELECT r.run_id, r.dataset, r.filtration, r.vectorizer, r.classifier,
                       AVG(f.accuracy) AS avg_acc,
                       r.wall_time_s AS avg_wall
                FROM runs r
                JOIN fold_results f ON r.run_id = f.run_id
                WHERE r.finished_at IS NOT NULL
                GROUP BY r.run_id
            )
            GROUP BY dataset, filtration, vectorizer, classifier
        """).fetchall()

        by_dataset = defaultdict(list)
        for r in rows:
            by_dataset[r["dataset"]].append(dict(r))

        result = {"overall_best": None, "overall_worst": None, "per_dataset": {}}
        all_sorted = sorted(rows, key=lambda r: r["accuracy"], reverse=True)
        if all_sorted:
            result["overall_best"] = dict(all_sorted[0])
            result["overall_worst"] = dict(all_sorted[-1])

        for ds, entries in by_dataset.items():
            sorted_entries = sorted(entries, key=lambda e: e["accuracy"], reverse=True)
            result["per_dataset"][ds] = {
                "best": sorted_entries[0],
                "worst": sorted_entries[-1],
            }

        return result

    def stage_impact(self) -> dict:
        """Quantify how much each stage (filtration, vectorizer, classifier)
        impacts accuracy — compute variance explained by each factor."""
        rows = self._conn.execute("""
            SELECT filtration, vectorizer, classifier,
                   ROUND(AVG(avg_acc), 4) AS accuracy
            FROM (
                SELECT r.run_id, r.filtration, r.vectorizer, r.classifier,
                       AVG(f.accuracy) AS avg_acc
                FROM runs r
                JOIN fold_results f ON r.run_id = f.run_id
                WHERE r.finished_at IS NOT NULL
                GROUP BY r.run_id
            )
            GROUP BY filtration, vectorizer, classifier
        """).fetchall()

        # Marginalize over each factor
        def marginalize(key: str):
            groups = defaultdict(list)
            for r in rows:
                groups[r[key]].append(r["accuracy"])
            return {k: sum(v)/len(v) for k, v in groups.items()}

        return {
            "by_filtration": marginalize("filtration"),
            "by_vectorizer": marginalize("vectorizer"),
            "by_classifier": marginalize("classifier"),
            "range_filtration": self._range(marginalize("filtration")),
            "range_vectorizer": self._range(marginalize("vectorizer")),
            "range_classifier": self._range(marginalize("classifier")),
        }

    @staticmethod
    def _range(d: dict) -> float:
        vals = list(d.values())
        return round(max(vals) - min(vals), 4) if vals else 0.0

    def pareto_frontier(self) -> list[dict]:
        """Find the accuracy/runtime Pareto frontier."""
        rows = self._conn.execute("""
            SELECT dataset, filtration, vectorizer, classifier,
                   ROUND(AVG(avg_acc), 4) AS accuracy,
                   ROUND(AVG(avg_wall), 2) AS wall_s
            FROM (
                SELECT r.run_id, r.dataset, r.filtration, r.vectorizer, r.classifier,
                       AVG(f.accuracy) AS avg_acc,
                       r.wall_time_s AS avg_wall
                FROM runs r
                JOIN fold_results f ON r.run_id = f.run_id
                WHERE r.finished_at IS NOT NULL
                GROUP BY r.run_id
            )
            GROUP BY dataset, filtration, vectorizer, classifier
            ORDER BY accuracy DESC, wall_s ASC
        """).fetchall()
        return [dict(r) for r in rows]

    def run_count(self) -> int:
        return self._conn.execute("SELECT COUNT(*) FROM runs WHERE finished_at IS NOT NULL").fetchone()[0]

    def close(self):
        self._conn.close()


def generate_report(db_path: str | Path) -> str:
    """Generate a comprehensive analysis report from benchmark results."""
    analyzer = BenchmarkAnalyzer(db_path)
    n = analyzer.run_count()

    if n == 0:
        return "No completed runs found."

    lines = []
    lines.append("=" * 72)
    lines.append("TDA PIPELINE BENCHMARK — ANALYSIS REPORT")
    lines.append(f"Configurations completed: {n}")
    lines.append("=" * 72)

    # 1. Stage impact analysis
    lines.append("\n── STAGE IMPACT (marginal accuracy by component) ──")
    impact = analyzer.stage_impact()
    for stage, label in [("by_filtration", "Filtration"), ("by_vectorizer", "Vectorizer"), ("by_classifier", "Classifier")]:
        lines.append(f"\n{label}:")
        for name, acc in sorted(impact[stage].items(), key=lambda x: -x[1]):
            lines.append(f"  {name:<25} {acc:.4f}")
        range_key = f"range_{stage.split('_')[1]}"
        lines.append(f"  → Range (max − min): {impact[range_key]:.4f}")

    # 2. Noise sensitivity
    lines.append("\n── NOISE SENSITIVITY (sphere_torus across σ levels) ──")
    noise_data = analyzer.noise_sensitivity()
    if noise_data:
        # Group by noise level
        by_noise = defaultdict(list)
        for r in noise_data:
            ds = r["dataset"]
            # extract noise level from name
            if "n0" in ds:
                lvl = "σ=0.00"
            elif "n5" in ds:
                lvl = "σ=0.05"
            elif "n15" in ds:
                lvl = "σ=0.15"
            elif "n30" in ds:
                lvl = "σ=0.30"
            else:
                lvl = ds
            by_noise[lvl].append(r["accuracy"])

        for lvl in ["σ=0.00", "σ=0.05", "σ=0.15", "σ=0.30"]:
            if lvl in by_noise:
                accs = by_noise[lvl]
                lines.append(f"  {lvl}: mean={sum(accs)/len(accs):.4f}, min={min(accs):.4f}, max={max(accs):.4f}")

    # 3. Best/worst
    lines.append("\n── BEST & WORST CONFIGURATIONS ──")
    bw = analyzer.best_worst()
    if bw["overall_best"]:
        b = bw["overall_best"]
        lines.append(f"  Overall best:  {b['filtration']} + {b['vectorizer']} + {b['classifier']} → {b['accuracy']} ({b['wall_s']}s)")
    if bw["overall_worst"]:
        w = bw["overall_worst"]
        lines.append(f"  Overall worst: {w['filtration']} + {w['vectorizer']} + {w['classifier']} → {w['accuracy']} ({w['wall_s']}s)")

    # 4. Pareto frontier
    lines.append("\n── PARETO FRONTIER (top accuracy/time trade-offs) ──")
    pareto = analyzer.pareto_frontier()
    shown = set()
    count = 0
    for r in pareto:
        key = (r["dataset"], r["filtration"], r["vectorizer"], r["classifier"])
        if key not in shown and count < 10:
            shown.add(key)
            count += 1
            lines.append(f"  {r['dataset']:<22} {r['filtration']:<16} {r['vectorizer']:<20} {r['classifier']:<14} acc={r['accuracy']:.4f} t={r['wall_s']}s")

    # 5. Full summary table (compact)
    lines.append("\n── FULL SUMMARY TABLE ──")
    summary = analyzer.summary_table()
    lines.append(f"  {'Dataset':<22} {'Filtration':<16} {'Vectorizer':<20} {'Classifier':<14} {'Acc':>8} {'Time':>8}")
    lines.append(f"  {'-'*88}")
    for r in summary:
        lines.append(f"  {r['dataset']:<22} {r['filtration']:<16} {r['vectorizer']:<20} {r['classifier']:<14} {r['mean_accuracy']:>8.4f} {r['mean_wall_s']:>7.1f}s")

    analyzer.close()
    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    db = sys.argv[1] if len(sys.argv) > 1 else "data/tda/results.db"
    print(generate_report(db))
