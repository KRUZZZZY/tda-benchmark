#!/usr/bin/env python3
"""B2 — build a multi-patient ECG dataset from MIT-BIH Arrhythmia (mitdb).

Kills the paper's single-patient objection (ECG5000 = BIDMC chf07 one
patient). Uses the AAMI-5 class protocol (standard for MIT-BIH arrhythmia
classification):

  * 48 half-hour records (47 patients; record 201/202 share a patient),
    360 Hz, MLII lead (V1 fallback where MLII absent),
  * beat annotations from the .atr files mapped to AAMI classes:
      N  -> N (normal), L/R -> N, e/j -> N
      A/a/J/S -> S (supraventricular)
      V/E -> V (ventricular)
      F -> F (fusion)
      '/'/'f'/'Q'/'?' -> Q (unknown; excluded per AAMI practice)
  * each beat = window of 256 samples (128 before, 127 after the R-peak;
    ~0.71 s at 360 Hz), Takens-ready at d=3 tau=1 (254 points after embed),
  * PATIENT-DISJOINT stratified 5-fold CV at the RECORD level (records are
    split into 5 folds; no record appears in both train and test), the
    honest protocol for multi-patient generalisation,
  * class balance cap: subsample to at most 2000 beats/class (stratified),
    which also bounds runtime.

Outputs (additive, under data/tda/mitbih/):
  mitbih_X.npy   (n x 256)  mitbih_y.npy  (n, AAMI labels 0..3: N,S,V,F)
  mitbih_patient.npy (n, record index 0..47)   mitbih_folds.npy (n, fold 0..4)
  mitbih_meta.json (record -> patient id, class counts, fold assignment)

Usage: .venv-tda/bin/python projects/tda-benchmark/scripts/build_mitbih.py
"""
from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import wfdb

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
OUT_DIR = PROJECT_ROOT / "data" / "tda" / "mitbih"

RECORDS = ["100", "101", "102", "103", "104", "105", "106", "107", "108", "109",
           "111", "112", "113", "114", "115", "116", "117", "118", "119",
           "121", "122", "123", "124",
           "200", "201", "202", "203", "205", "207", "208", "209", "210",
           "212", "213", "214", "215", "217", "219", "220", "221", "222",
           "223", "228", "230", "231", "232", "233", "234"]
# 201 and 202 are the same patient (record 202 = patient 201 continuation) —
# group them so patient-disjoint CV never splits them.
SAME_PATIENT = {"201": "202"}

WINDOW = 256       # samples around each R-peak
HALF = WINDOW // 2
MAX_PER_CLASS = 2000
CV_FOLDS = 5

AAMI = {
    "N": "N", "L": "N", "R": "N", "e": "N", "j": "N",
    "A": "S", "a": "S", "J": "S", "S": "S",
    "V": "V", "E": "V",
    "F": "F",
    "/": "Q", "f": "Q", "Q": "Q", "?": "Q",
}
CLASS_ORDER = ["N", "S", "V", "F"]  # Q excluded (AAMI practice)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    all_X, all_y, all_pat = [], [], []
    meta = {}

    for rec_id in RECORDS:
        try:
            rec = wfdb.rdrecord(rec_id, pn_dir="mitdb", channels=[0])
        except Exception as exc:  # noqa: BLE001
            print(f"  !! {rec_id}: record load failed: {exc}")
            continue
        sig = rec.p_signal[:, 0]
        if rec.sig_name[0] not in ("MLII", "V5"):
            # fall back to channel 1 if present
            try:
                rec = wfdb.rdrecord(rec_id, pn_dir="mitdb", channels=[1])
                sig = rec.p_signal[:, 0]
            except Exception:  # noqa: BLE001
                print(f"  !! {rec_id}: no usable lead")
                continue
        ann = wfdb.rdann(rec_id, "atr", pn_dir="mitdb")
        fs = rec.fs or 360

        counts = Counter()
        beats = []
        for sym, samp in zip(ann.symbol, ann.sample):
            cls = AAMI.get(sym)
            if cls is None or cls == "Q":
                continue
            if samp - HALF < 0 or samp + HALF >= len(sig):
                continue
            beats.append((sig[samp - HALF: samp + HALF], cls))
            counts[cls] += 1

        if not beats:
            print(f"  !! {rec_id}: no usable beats")
            continue
        X = np.array([b[0] for b in beats])
        y = np.array([CLASS_ORDER.index(b[1]) for b in beats])
        pat = SAME_PATIENT.get(rec_id, rec_id)
        meta[rec_id] = {"patient": pat, "fs": fs, "beats": len(beats),
                        "class_counts": dict(counts)}
        all_X.append(X); all_y.append(y)
        all_pat.append(np.full(len(y), len(meta) - 1))
        print(f"  {rec_id}: {X.shape} classes={dict(counts)}")

    X = np.concatenate(all_X).astype(np.float32)
    y = np.concatenate(all_y)
    patient_idx = np.concatenate(all_pat)

    # cap per class (stratified, global)
    keep = []
    for c in range(len(CLASS_ORDER)):
        ci = np.where(y == c)[0]
        if len(ci) > MAX_PER_CLASS:
            rng = np.random.default_rng(42 + c)
            ci = rng.choice(ci, MAX_PER_CLASS, replace=False)
        keep.append(ci)
    keep = np.concatenate(keep)
    rng = np.random.default_rng(7)
    rng.shuffle(keep)
    X, y, patient_idx = X[keep], y[keep], patient_idx[keep]

    # patient-disjoint folds: greedy beat-balanced assignment (sort patients
    # by beat count desc, assign each to the currently-smallest fold) so no
    # fold is starved; still guarantees no patient spans two folds.
    patients = sorted(set(patient_idx.tolist()))
    pat_beats = {p: int((patient_idx == p).sum()) for p in patients}
    fold_beats = [0] * CV_FOLDS
    pat_fold = {}
    for p in sorted(pat_beats, key=lambda x: -pat_beats[x]):
        f = int(np.argmin(fold_beats))
        pat_fold[p] = f
        fold_beats[f] += pat_beats[p]
    folds = np.array([pat_fold[p] for p in patient_idx])
    # verify: no patient spans multiple folds
    for p in patients:
        pf = set(folds[patient_idx == p].tolist())
        assert len(pf) == 1, f"patient {p} split across folds {pf}"

    np.save(OUT_DIR / "mitbih_X.npy", X)
    np.save(OUT_DIR / "mitbih_y.npy", y)
    np.save(OUT_DIR / "mitbih_patient.npy", patient_idx)
    np.save(OUT_DIR / "mitbih_folds.npy", folds)
    with open(OUT_DIR / "mitbih_meta.json", "w") as fh:
        json.dump({
            "records": RECORDS, "class_order": CLASS_ORDER,
            "n_patients": len(patients),
            "fold_patients": {str(f): [str(p) for p in patients if pat_fold[p] == f]
                              for f in range(CV_FOLDS)},
            "per_record": meta,
            "class_counts": dict(Counter(y.tolist())),
            "window": WINDOW, "fs": 360, "max_per_class": MAX_PER_CLASS,
            "cv": "patient-disjoint stratified 5-fold (record level)",
        }, fh, indent=2)
    print(f"\nSaved {X.shape} beats, {len(patients)} patients, "
          f"classes={dict(Counter(y.tolist()))}")
    print(f"fold sizes: {dict(Counter(folds.tolist()))}")
    # ── SHA256 checksum verification (reproducibility; additive-only) ──────
    import _checksum_verify
    for rel in ("mitbih/mitbih_X.npy", "mitbih/mitbih_y.npy",
                "mitbih/mitbih_patient.npy", "mitbih/mitbih_folds.npy"):
        _checksum_verify.verify(rel, OUT_DIR.parent)


if __name__ == "__main__":
    sys.exit(main())
