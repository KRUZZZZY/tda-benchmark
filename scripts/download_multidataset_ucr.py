#!/usr/bin/env python3
"""B1 — download 5 multi-dataset UCR time-series benchmarks as npy.

Mirrors the verified ECG5000 download pattern (scripts/download_ucr.py):
  * aeon-toolkit zip per dataset (timeseriesclassification.com),
  * parse the ARFF members (_TRAIN.arff, _TEST.arff): class label is the
    LAST comma-separated field after @data (UCR convention),
  * combine TRAIN+TEST (the repo's ECG200/ECG5000 npy are likewise combined),
  * map labels to 0..k-1 for sklearn,
  * save to data/tda/ucr3/<name>_X.npy / <name>_y.npy.

Datasets (B1 scope): FordA, FordB, Wafer, ElectricDevices, HandOutlines.

Additive-only: writes only new files under data/tda/ucr3/.
"""
from __future__ import annotations

import io
import sys
import urllib.request
import zipfile
from pathlib import Path

import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent  # AI_KOS_PROJECT (scripts/ needs FOUR parents)
OUT_DIR = PROJECT_ROOT / "data" / "tda" / "ucr3"

DATASETS = ["FordA", "FordB", "Wafer", "ElectricDevices", "HandOutlines"]

SOURCES = [
    "https://timeseriesclassification.com/aeon-toolkit/{name}.zip",
    "https://www.timeseriesclassification.com/aeon-toolkit/{name}.zip",
]

BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
}


def fetch(name: str) -> bytes:
    last = None
    for url_tpl in SOURCES:
        url = url_tpl.format(name=name)
        for attempt in range(3):
            try:
                req = urllib.request.Request(url, headers=BROWSER_HEADERS)
                with urllib.request.urlopen(req, timeout=180) as resp:
                    data = resp.read()
                print(f"  fetched {url} ({len(data)//1024} KB, attempt {attempt+1})")
                return data
            except Exception as exc:  # noqa: BLE001
                last = exc
                print(f"  retry {attempt+1} {url}: {exc}")
    raise RuntimeError(f"all sources failed for {name}: {last}")


def parse_arff(text: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (X float, y int) from an ARFF body. Class label = LAST field."""
    data_idx = text.index("@data")
    rows = []
    for line in text[data_idx:].splitlines():
        line = line.strip()
        if not line or line.startswith("%") or line.startswith("@"):
            continue
        parts = line.split(",")
        rows.append([float(v) for v in parts[:-1]] + [float(parts[-1])])
    arr = np.array(rows)
    return arr[:, :-1], arr[:, -1].astype(np.int64)


def process(name: str) -> None:
    print(f"== {name} ==")
    data = fetch(name)
    with zipfile.ZipFile(io.BytesIO(data)) as zf:
        members = [m for m in zf.namelist() if m.endswith(".arff")]
        if not members:
            raise RuntimeError(f"{name}: no arff members in zip: {zf.namelist()}")
        all_X, all_y = [], []
        for member in members:
            text = zf.read(member).decode("latin-1")
            X, y = parse_arff(text)
            print(f"  {member}: {X.shape} classes={sorted(set(y.tolist()))}")
            all_X.append(X)
            all_y.append(y)
    X = np.concatenate(all_X)
    y = np.concatenate(all_y)
    # map labels to 0..k-1 preserving order of first appearance
    uniq = sorted(set(y.tolist()))
    mapping = {v: i for i, v in enumerate(uniq)}
    y = np.array([mapping[v] for v in y.tolist()], dtype=np.int64)
    np.save(OUT_DIR / f"{name}_X.npy", X)
    np.save(OUT_DIR / f"{name}_y.npy", y)
    print(f"  saved {name}: X {X.shape} y {y.shape} classes {len(uniq)} "
          f"-> 0..{len(uniq)-1}")


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    for name in DATASETS:
        process(name)
    # ── SHA256 checksum verification (reproducibility; additive-only) ──────
    import _checksum_verify
    for name in DATASETS:
        _checksum_verify.verify(f"ucr3/{name}_X.npy", OUT_DIR.parent)
        _checksum_verify.verify(f"ucr3/{name}_y.npy", OUT_DIR.parent)


if __name__ == "__main__":
    sys.exit(main())
