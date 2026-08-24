#!/usr/bin/env python3
"""Download a second UCR time-series dataset (ECG5000) and save as npy.

Task C of the reviewer-revision experiments for tda-benchmark:

  * Fetches ECG5000 (UCR archive) as ARFF from timeseriesclassification.com
    (primary) with fallback mirrors.
  * Parses the ARFF (class label is the LAST comma-separated field after
    @data; UCR labels {1..5} are mapped to {0..4} for sklearn).
  * Combines the UCR TRAIN + TEST splits (ECG200 in this repo was likewise
    the combined 100+100 = 200 samples; ECG5000 combined = 500 + 4500 = 5000).
  * Saves  data/tda/ucr2/ecg5000_X.npy  (5000 x 140 float64)
          data/tda/ucr2/ecg5000_y.npy  (5000      int64, labels 0..4)

Additive-only: writes only new files under data/tda/ucr2/.
"""

from __future__ import annotations

import argparse
import io
import os
import sys
import urllib.request
import zipfile

# Primary + mirrors. The UCR 2018 per-dataset arff pages (cs.ucr.edu) are
# retired; timeseriesclassification.com hosts the aeon-toolkit archives.
SOURCES = [
    "https://timeseriesclassification.com/aeon-toolkit/ECG5000.zip",
    "https://www.timeseriesclassification.com/aeon-toolkit/ECG5000.zip",
    "https://raw.githubusercontent.com/uea-machine-learning/tsml-data/main/ECG5000/ECG5000.zip",  # mirror (may not exist)
]

ARFF_MEMBERS = ("ECG5000_TRAIN.arff", "ECG5000_TEST.arff")


BROWSER_HEADERS = {
    "User-Agent": ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                   "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"),
    "Accept": "application/zip,application/octet-stream,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://timeseriesclassification.com/description.php?Dataset=ECG5000",
}


def fetch_zip(url: str, timeout: int = 120) -> bytes:
    """Fetch via urllib with browser headers; fall back to curl (the server
    returns 403 to bare Python/urllib User-Agents)."""
    try:
        req = urllib.request.Request(url, headers=BROWSER_HEADERS)
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read()
    except Exception as urllib_exc:  # noqa: BLE001
        import subprocess
        print(f"  urllib failed ({urllib_exc}); trying curl")
        out = subprocess.run(
            ["curl", "-sSL", "--max-time", str(timeout), "-A", BROWSER_HEADERS["User-Agent"],
             "-e", BROWSER_HEADERS["Referer"], url],
            capture_output=True, check=False)
        if out.returncode != 0 or not out.stdout:
            raise RuntimeError(f"curl also failed: rc={out.returncode} {out.stderr[:200]}")
        return out.stdout


def parse_arff(text: str):
    """Parse an ARFF body; class label is the LAST comma-separated field."""
    lines = text.splitlines()
    data_start = None
    for i, l in enumerate(lines):
        if l.strip().lower().startswith("@data"):
            data_start = i
            break
    if data_start is None:
        raise ValueError("no @data section in ARFF")
    X_rows, y_rows = [], []
    for l in lines[data_start + 1:]:
        l = l.strip()
        if not l or l.startswith("%"):
            continue
        parts = l.split(",")
        if len(parts) < 2:
            continue
        X_rows.append([float(x) for x in parts[:-1]])
        y_rows.append(int(float(parts[-1])))
    import numpy as np
    return np.asarray(X_rows, dtype=np.float64), np.asarray(y_rows, dtype=np.int64)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data-dir", default=os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "data", "tda"))
    ap.add_argument("--keep-zip", action="store_true", help="keep the downloaded zip in /tmp")
    args = ap.parse_args()

    out_dir = os.path.join(args.data_dir, "ucr2")
    os.makedirs(out_dir, exist_ok=True)
    x_path = os.path.join(out_dir, "ecg5000_X.npy")
    y_path = os.path.join(out_dir, "ecg5000_y.npy")
    if os.path.exists(x_path) and os.path.exists(y_path):
        import numpy as np
        print(f"already present: {x_path} ({np.load(x_path).shape}) — skipping download")
        return

    zip_bytes = None
    used = None
    for url in SOURCES:
        try:
            print(f"[download] trying {url}")
            zip_bytes = fetch_zip(url)
            used = url
            print(f"[download] OK ({len(zip_bytes)} bytes)")
            break
        except Exception as exc:  # noqa: BLE001
            print(f"[download] failed: {exc}")
    if zip_bytes is None:
        print("ERROR: all download sources failed. Place ECG5000_TRAIN.arff / "
              "ECG5000_TEST.arff manually in data/tda/ucr2/ and re-run.")
        sys.exit(1)

    zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    names = zf.namelist()
    missing = [m for m in ARFF_MEMBERS if m not in names]
    if missing:
        print(f"ERROR: zip lacks expected members {missing}; got {names}")
        sys.exit(1)

    import numpy as np
    all_X, all_y = [], []
    for member in ARFF_MEMBERS:
        text = zf.read(member).decode("utf-8", errors="replace")
        X, y = parse_arff(text)
        print(f"  {member}: {X.shape}, classes={sorted(set(y.tolist()))}")
        all_X.append(X)
        all_y.append(y)

    X = np.concatenate(all_X, axis=0)
    y = np.concatenate(all_y, axis=0)
    # UCR labels {1..5} -> {0..4} for sklearn
    y = y - 1
    np.save(x_path, X)
    np.save(y_path, y)
    print(f"[save] {x_path} {X.shape}")
    print(f"[save] {y_path} {y.shape} classes={sorted(set(y.tolist()))}")
    print(f"[save] class counts: {dict(zip(*np.unique(y, return_counts=True)))}")
    print(f"[save] source: {used}")
    if args.keep_zip:
        with open("/tmp/ECG5000.zip", "wb") as fh:
            fh.write(zip_bytes)
    # ── SHA256 checksum verification (reproducibility; additive-only) ──────
    import _checksum_verify
    _checksum_verify.verify("ucr2/ecg5000_X.npy", args.data_dir)
    _checksum_verify.verify("ucr2/ecg5000_y.npy", args.data_dir)


if __name__ == "__main__":
    main()
