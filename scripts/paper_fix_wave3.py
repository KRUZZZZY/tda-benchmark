#!/usr/bin/env python3
"""Apply wave-3 audit consensus fixes (3 identical auditors x {L10,L11,L9} +
the 8 deferred wave-2 items; merged 2-of-3, every item re-verified by the
orchestrator with sqlite3 + pdftotext before writing).

Every edit is an exact-string replace with assert count==1. --dry-run prints
anchor counts without writing. Run: python3 scripts/paper_fix_wave3.py [--dry-run]

NOTE: multi-line anchors MUST use non-raw strings (real \\n), never r"" —
raw strings keep backslash-n literal and the tex has real newlines.
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "dissertation.tex"

FIXES: list[tuple[str, str, str]] = [
    # ---- W3-A. My own B5 defects (3/3 auditors) ----
    # A1: B5 paragraph lives in S5.3 (Multi-Dataset Generalisation), not S5.4
    ("A1 complexity ref S5.4->S5.3",
     r"infeasible at $n{=}3000$ (\S5.4). Both speed multipliers",
     r"infeasible at $n{=}3000$ (\S5.3). Both speed multipliers"),
    # A2: guideline row ref S5.4->S5.3
    ("A2 guideline ref S5.4->S5.3",
     r"it did not finish in $42$~h (giotto-tda 0.6.2, \S5.4)",
     r"it did not finish in $42$~h (giotto-tda 0.6.2, \S5.3)"),
    # A3: fix the \texttt{-} typo that corrupts the DB filename render
    ("A3 db filename typo",
     r"rep 1 (\texttt{data/tda/large\_n\_sweep\-db}, 8 finished runs)",
     r"rep 1 (\texttt{data/tda/large\_n\_sweep.db}, 8 finished runs)"),

    # ---- W3-B. L9 render bugs (2-3/3 auditors, verified in PDF) ----
    # B1: bare % at line ~1106 silently deletes "within 0.41pp" from output
    ("B1 bare percent deletes text",
     r"and Weak Alpha (72.74%) within 0.41pp.",
     r"and Weak Alpha (72.74\%) within 0.41pp."),
    # B2: broken sentence from wave-2 pooled-recall fix ("over the ,")
    ("B2 broken sentence 'over the ,'",
     "per-class recalls over the\n, the minor classes are largely",
     "per-class recalls; the minor classes are largely"),

    # ---- W3-C. Guidelines-table contradictions (3/3 auditors) ----
    # C1+C3 (same row): Betti 5th of 7 on the r25 marginal the row cites;
    # SVM-RBF collapse absent. One replacement covers both.
    ("C1+C3 TS-row Betti rank + SVM collapse",
     "    Delay-embedded time series ($d \\ge 3$) & VR or Weak Alpha & Betti Curves & RF or SVM (RBF) & Vectorization dominates variance (6.39pp on ECG200; 24.89pp on ECG5000) \\\\",
     "    Delay-embedded time series ($d \\ge 3$) & VR or Weak Alpha & Betti Curves (or Landscapes) & RF or SVM (RBF) & Vectorization dominates variance (6.39pp on ECG200; 24.89pp on ECG5000); Betti is 5th of 7 vectorizers on the r25 ECG200 marginal (72.38\\%), so Landscapes/Statistics are competitive; SVM-RBF collapses to the majority class on TDA features (66.5\\%) \\\\"),
    # C2: high-noise row >=98.5% is the confounded combined-signal figure
    ("C2 high-noise row scoped to combined signal",
     "    High-noise clouds ($\\sigma \\ge 0.15$) & Weak Alpha or VR & Betti Curves & SVM (RBF) & All vectorizers maintain $\\ge 98.5\\%$ at $\\sigma=0.30$ (minimum over configurations); measured $d_B$ far below the stability bound \\\\",
     "    High-noise clouds ($\\sigma \\ge 0.15$) & Weak Alpha or VR & Betti Curves & SVM (RBF) & All vectorizers maintain $\\ge 98.5\\%$ at $\\sigma=0.30$ on the combined geometric signal (minimum over configurations); the confound-controlled matched-genus floor is 91\\%; measured $d_B$ far below the stability bound \\\\"),

    # ---- W3-D. Reproducibility (3/3 auditors) ----
    # D1: "seven further time series" -> five (panel adds 5 UCR series)
    ("D1 seven->five further time series",
     "the\n\\S5.3 panel adds seven further time series and two 10-class image\ndatasets.",
     "the\n\\S5.3 panel adds five further time series and two 10-class image\ndatasets."),
    # D2: disclose the ECG5000 subsample draw seed (rng 42)
    ("D2 ECG5000 subsample seed disclosed",
     r"ECG5000 & time series & 714 (subsample) & 140 & 5 \\",
     r"ECG5000 & time series & 714 (subsample, rng seed 42) & 140 & 5 \\"),
    # D3: disclose the panel pre-subsample seed (fixed-seed uniform draw)
    ("D3 panel pre-subsample seed disclosed",
     "pre-subsampled to 100 points with a fixed-seed uniform draw; this\nwas necessary",
     "pre-subsampled to 100 points with a fixed-seed uniform draw (seed 42); this\nwas necessary"),
    # D4: GUDHI-Alpha parity claim has no retained artefact — soften to
    # "dedicated run" and point at the producer script
    ("D4 GUDHI-Alpha artefact provenance",
     "reproduces weak-alpha classification accuracy (mean\ndifference 0.0--0.8pp) at 2--5$\\times$ the runtime cost, so the\napproximation is faithful on these tasks.",
     "reproduces weak-alpha classification accuracy (mean\ndifference 0.0--0.8pp, measured in a dedicated GUDHI-vs-giotto run,\nscripts/experiment\\_alpha.py) at 2--5$\\times$ the runtime cost, so the\napproximation is faithful on these tasks."),
    # D5: config snapshot claim — expansion DBs retain no snapshot; scope it
    ("D5 config_snapshot scope note",
     "SQLite database (Appendix~B) with a config snapshot for\nreproducibility.",
     "SQLite database (Appendix~B) with a config snapshot for\nreproducibility (retained for the main sweep; the expansion\nDBs --- panel, hyperparameter, large-n, MNIST-10 --- do not\nretain one; their provenance is the driver scripts in\nscripts/)."),

    # ---- W3-E. Internal consistency (1-3/3 auditors, verified in PDF) ----
    # E1: "three analytical cuts" vs "four" (PDF p.1327 vs p.1334)
    ("E1 three->four analytical cuts",
     r"across six dataset instances and three analytical cuts.",
     r"across six dataset instances and four analytical cuts."),
    # E2: baselines cross-ref S4.3 -> S4.1.1 (Classical Baselines subsection)
    ("E2 baselines S4.3->S4.1.1",
     "The classical\nbaselines of \\S4.3 beat TDA alone on both real datasets.",
     "The classical\nbaselines of \\S4.1.1 beat TDA alone on both real datasets."),
    # E3: Anai et al. uncited (DTM-weighted Rips provenance)
    ("E3 Anai citation",
     r"edge weights from a distance-to-measure estimate; Anai et al.), robust",
     r"edge weights from a distance-to-measure estimate; Anai et al.~\cite{anai2019}), robust"),
]


def main() -> None:
    src = TEX.read_text()
    dry = "--dry-run" in sys.argv
    n_fail = 0
    for name, old, new in FIXES:
        n = src.count(old)
        if n != 1:
            print(f"[FAIL({n})] {name}")
            n_fail += 1
            continue
        if dry:
            print(f"[OK] {name}")
        else:
            src = src.replace(old, new, 1)
            print(f"[APPLIED] {name}")
    if dry:
        print(f"\ndry-run: {len(FIXES)} fixes, {n_fail} anchor failures.")
        return
    if n_fail:
        print(f"\n{n_fail} anchors failed; NOT writing.")
        sys.exit(1)
    TEX.write_text(src)
    print(f"\nwritten: {len(FIXES) - n_fail} fixes applied to dissertation.tex")


if __name__ == "__main__":
    main()
