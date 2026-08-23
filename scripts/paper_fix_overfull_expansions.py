#!/usr/bin/env python3
"""Fix the 6 NEW overfull hboxes introduced by the #13/#15/#17/#18 insertions
(3 long \\texttt DB tokens + 3 tight prose lines). Each fix adds a break
opportunity or rewords; anchors verified exactly-once. Run with --dry-run.
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "dissertation.tex"

FIXES = [
    # O1: #15 paragraph — "$209.8$\,pp$^2$" unbreakable run; give the math a
    # break before the variance token
    ("O1 p15 variance token break",
     r"($209.8$\,pp$^2$) dwarfs the residual ($16.4$\,pp$^2$)",
     "($209.8$\\,pp$^2$) dwarfs the\nresidual ($16.4$\\,pp$^2$)"),
    # O2: threats — beyond_accuracy_ecg5000.db too long for its line
    ("O2 beyond_accuracy token",
     r"per-class precision/recall/F1, AUROC, Brier; \texttt{beyond\_accuracy\_ecg5000.db};",
     "per-class precision/recall/F1, AUROC, Brier;\n    \\texttt{beyond\\_accuracy\\_ecg5000.db};"),
    # O3: threats — fps_ablation.db token
    ("O3 fps_ablation token",
     r"\texttt{fps\_ablation.db}) finds no benefit",
     r"\texttt{fps\_ablation.db})\allowbreak\ finds no benefit"),
    # O4: threats — repeated_cv_r25.db token in the scalars item
    ("O4 repeated_cv_r25 token",
     r"from \texttt{repeated\_cv\_r25.db}, per-repetition mean method)",
     "from \\texttt{repeated\\_cv\\_r25.db},\\allowbreak\\ per-repetition\n    mean method)"),
    # O5: #17 speed-small item — long Decision text in X column now wraps,
    # but the wall-clock sentence overflows; reword slightly
    ("O5 p17 small-n sentence",
     "        Cubical; the 3--27\\% wall-clock gap between them (\\S4.3) rarely\n        justifies accuracy risk.",
     "        Cubical; the 3--27\\% wall-clock gap between them (\\S4.3)\n        rarely justifies accuracy risk."),
    # O6: #17 noise item — 0.434 token line
    ("O6 p17 noise token",
     "    bottleneck distances (maximum 0.434) sit far below the corrected\n    stability bound",
     "    bottleneck distances (maximum\n    0.434) sit far below the corrected\n    stability bound"),
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
        print(f"\ndry-run: {len(FIXES)} fixes, {n_fail} failures.")
        return
    if n_fail:
        sys.exit(1)
    TEX.write_text(src)
    print(f"\nwritten: {len(FIXES) - n_fail} overfull fixes applied.")


if __name__ == "__main__":
    main()
