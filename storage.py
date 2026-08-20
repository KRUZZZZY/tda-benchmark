"""SQLite result storage with normalized schema for TDA benchmark."""

from __future__ import annotations

import json
import sqlite3
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (
    run_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    dataset    TEXT    NOT NULL,
    filtration TEXT    NOT NULL,
    vectorizer TEXT    NOT NULL,
    classifier TEXT    NOT NULL,
    repetition INTEGER NOT NULL,
    started_at TEXT,
    finished_at TEXT,
    wall_time_s REAL,
    peak_memory_mb REAL
);

CREATE TABLE IF NOT EXISTS fold_results (
    fold_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id     INTEGER NOT NULL REFERENCES runs(run_id),
    fold       INTEGER NOT NULL,
    accuracy   REAL,
    f1         REAL,
    precision  REAL,
    recall     REAL
);

CREATE TABLE IF NOT EXISTS config_snapshot (
    id         INTEGER PRIMARY KEY CHECK (id = 1),
    yaml_text  TEXT    NOT NULL,
    saved_at   TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS run_metadata (
    run_id     INTEGER PRIMARY KEY REFERENCES runs(run_id),
    pipeline_params TEXT,  -- JSON: filtration/vectorizer/classifier kwargs
    n_train    INTEGER,
    n_test     INTEGER,
    n_features INTEGER
);

CREATE INDEX IF NOT EXISTS idx_runs_dataset ON runs(dataset);
CREATE INDEX IF NOT EXISTS idx_runs_filtration ON runs(filtration);
CREATE INDEX IF NOT EXISTS idx_fold_run ON fold_results(run_id);
"""


class ResultStore:
    """Normalized SQLite store for benchmark results.

    Schema:
      runs:         one row per (dataset × filtration × vectorizer × classifier × rep)
      fold_results: one row per CV fold within a run
      config_snapshot: stores the YAML config used
      run_metadata:   stores pipeline params and data dimensions
    """

    def __init__(self, db_path: str | Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.executescript(SCHEMA)
        self._conn.commit()

    def save_config(self, yaml_text: str):
        self._conn.execute(
            "INSERT OR REPLACE INTO config_snapshot (id, yaml_text, saved_at) VALUES (1, ?, ?)",
            (yaml_text, datetime.now(timezone.utc).isoformat()),
        )
        self._conn.commit()

    def start_run(
        self,
        dataset: str,
        filtration: str,
        vectorizer: str,
        classifier: str,
        repetition: int,
        pipeline_params: dict | None = None,
        n_train: int = 0,
        n_test: int = 0,
        n_features: int = 0,
    ) -> int:
        """Insert a run row and return its run_id."""
        cur = self._conn.execute(
            """INSERT INTO runs (dataset, filtration, vectorizer, classifier, repetition, started_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (dataset, filtration, vectorizer, classifier, repetition,
             datetime.now(timezone.utc).isoformat()),
        )
        run_id: int = cur.lastrowid  # type: ignore[assignment]
        self._conn.execute(
            """INSERT INTO run_metadata (run_id, pipeline_params, n_train, n_test, n_features)
               VALUES (?, ?, ?, ?, ?)""",
            (run_id, json.dumps(pipeline_params or {}), n_train, n_test, n_features),
        )
        self._conn.commit()
        return run_id

    def save_fold(
        self,
        run_id: int,
        fold: int,
        metrics: dict[str, float],
    ):
        """Save a single CV fold result."""
        self._conn.execute(
            """INSERT INTO fold_results (run_id, fold, accuracy, f1, precision, recall)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                run_id,
                fold,
                metrics.get("accuracy"),
                metrics.get("f1"),
                metrics.get("precision"),
                metrics.get("recall"),
            ),
        )
        self._conn.commit()

    def finish_run(self, run_id: int, wall_time_s: float, peak_memory_mb: float = 0.0):
        """Mark a run as complete with timing info."""
        self._conn.execute(
            """UPDATE runs SET finished_at = ?, wall_time_s = ?, peak_memory_mb = ?
               WHERE run_id = ?""",
            (datetime.now(timezone.utc).isoformat(), wall_time_s, peak_memory_mb, run_id),
        )
        self._conn.commit()

    def summary(self) -> list[dict]:
        """Return aggregate statistics across all runs with CIs.

        CI uses the t-distribution critical value (df = n_folds - 1)
        on the per-configuration fold accuracies. This is a reporting
        convenience for the console; the paper's headline CIs are
        computed separately in the analysis pipeline.
        """
        # t_{0.975, df} for df = 4..8 (n_folds 5..9); fallback 1.96 for large df.
        tcrit_for_df = {4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365, 8: 2.306}
        df = self._conn.execute(
            "SELECT CAST(COUNT(DISTINCT fold) AS INTEGER) FROM fold_results"
        ).fetchone()[0]
        tcrit = tcrit_for_df.get(max(1, df - 1), 1.96)
        cur = self._conn.execute("""
            SELECT dataset, filtration, vectorizer, classifier,
                   COUNT(*) AS reps,
                   AVG(avg_acc) AS mean_accuracy,
                   AVG(avg_acc - ? * (std_acc / SQRT(n_folds))) AS ci_lower,
                   AVG(avg_acc + ? * (std_acc / SQRT(n_folds))) AS ci_upper,
                   AVG(avg_wall_time) AS mean_wall_time
            FROM (
                SELECT r.run_id, r.dataset, r.filtration, r.vectorizer, r.classifier,
                       AVG(f.accuracy) AS avg_acc,
                       CASE WHEN COUNT(f.fold_id) > 1
                            THEN 1.0 * (MAX(f.accuracy) - MIN(f.accuracy)) / 2
                            ELSE 0 END AS std_acc,
                       CAST(COUNT(f.fold_id) AS REAL) AS n_folds,
                       r.wall_time_s AS avg_wall_time
                FROM runs r
                JOIN fold_results f ON r.run_id = f.run_id
                WHERE r.finished_at IS NOT NULL
                GROUP BY r.run_id
            )
            GROUP BY dataset, filtration, vectorizer, classifier
            ORDER BY mean_accuracy DESC
        """, (tcrit, tcrit))
        columns = [d[0] for d in cur.description]
        return [dict(zip(columns, row)) for row in cur.fetchall()]

    def close(self):
        self._conn.close()
