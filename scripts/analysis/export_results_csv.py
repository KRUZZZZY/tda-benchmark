#!/usr/bin/env python3
"""Export the core result tables to flat CSVs (nobody needs SQLite to check
a number). Additive-only: reads the DBs, writes CSVs next to them.

Outputs (in data/tda/):
  exports/expanded_results_full.csv    — the main sweep runs table (672 rows;
                                        the paper's 616 = finished_at IS NOT NULL)
  exports/repeated_cv_r25_full.csv     — the ECG200 r=25 runs table (2105 rows;
                                        2100 finished = the paper's 84x25)
Usage: .venv-tda/bin/python scripts/export_results_csv.py
"""
from __future__ import annotations

import csv
import sqlite3
from pathlib import Path

DATA = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda")
OUT = DATA / "exports"


def dump(db: str, table: str, out_name: str) -> int:
    conn = sqlite3.connect(str(DATA / db))
    rows = conn.execute(f"SELECT * FROM {table}").fetchall()
    cols = [d[0] for d in conn.execute(f"PRAGMA table_info({table})").fetchall()]
    conn.close()
    with open(OUT / out_name, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    return len(rows)


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    n1 = dump("expanded_results.db", "runs", "expanded_results_full.csv")
    n2 = dump("expanded_results.db", "fold_results", "expanded_results_folds.csv")
    n3 = dump("repeated_cv_r25.db", "runs", "repeated_cv_r25_full.csv")
    n4 = dump("repeated_cv_r25.db", "fold_results", "repeated_cv_r25_folds.csv")
    print(f"expanded runs: {n1}, folds: {n2}")
    print(f"r25 runs: {n3}, folds: {n4}")
    print(f"exports in {OUT}")


if __name__ == "__main__":
    main()
