#!/usr/bin/env python3
"""Insert the #11 cross-library replication paragraph into dissertation.tex.

Finding (data/tda/cross_library_sweep.db, 90/90 runs, re-derived):
  - Sphere/torus (sigma=0 and 0.30): perfect parity — all four libraries
    (giotto VR, gudhi Alpha, gudhi Rips, Ripser VR) score 100.00% on
    every configuration.
  - ECG200 (Takens): giotto VR == gudhi Rips == Ripser VR exactly
    (77.0/75.0/73.0/76.0 vs the same), gudhi Alpha slightly lower on two
    configs (74.5/73.5 — a genuinely different complex), sub-pp
    landscape difference (76.0 vs 75.5).
  - svm_rbf majority collapse (66.5%) reproduces identically in ALL four
    libraries — a cross-library robustness of the collapse.
  - Conclusion: the paper's accuracy results are library-invariant;
    they do not rest on giotto-tda-specific behaviour (beyond the
    documented weak-alpha fragility on quantized series, which the
    sphere/torus + Takens-ECG200 arms here do not trigger).
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "dissertation.tex"

P11 = r"""
\paragraph{Cross-library replication (expansion 11).} The sweeps run
entirely through giotto-tda, so the accuracy results could in
principle be library-specific. A representative subset --- the
sphere/torus pair at $\sigma{=}0$ and $\sigma{=}0.30$ and the
Takens-embedded ECG200 clouds --- was therefore re-run through three
independent persistence engines: gudhi's true Alpha complex and Rips
complex, and Ripser's Vietoris--Rips, alongside the giotto reference
arm, sharing the same vectorizers, classifiers, folds, and diagram
format (5-fold CV seed 42 rep 1; three vectorizers $\times$ two
classifiers;
\texttt{data/tda/cross\_library\_sweep.db}, 90 finished runs). On the
synthetic clouds the results are exactly library-invariant: all four
arms score $100.00\%$ on every configuration at both noise levels. On
ECG200 the Vietoris--Rips arms agree to the decimal across libraries
(giotto, gudhi, and Ripser all give $77.0\%$/$75.0\%$/$73.0\%$/$76.0\%$
on the four RF/landscape configurations), and the only visible
deviation is the true gudhi Alpha complex --- a genuinely different
complex on Takens-embedded points --- at $74.5\%$/$73.5\%$ on two
configurations ($-2.5$/$-1.5$~pp), still within the single-split noise
band. The SVM-RBF majority-class collapse ($66.5\%$ on ECG200)
reproduces identically in all four libraries. The accuracy results are
therefore library-invariant: they do not rest on giotto-tda-specific
behaviour, and the previously documented filtration fragility
(weak-alpha on quantized series) is the library-dependence that
matters, not the accuracy outcomes.
"""


def main() -> None:
    src = TEX.read_text()
    dry = "--dry-run" in sys.argv
    # insert after the #6 topology-wins paragraph (end of the expansion
    # block, before the §5.5 Threats section)
    anchor = "the filtration stage's\ncontribution grows modestly rather than reversing the ordering.\n"
    n = src.count(anchor)
    print(f"[{'OK' if n==1 else 'FAIL'}] #6 paragraph end anchor: {n}")
    if n != 1:
        sys.exit(1)
    if dry:
        print("dry-run: anchor unique; no write.")
        return
    src = src.replace(anchor, anchor + "\n" + P11, 1)
    TEX.write_text(src)
    print("[APPLIED] cross-library paragraph inserted after #6")


if __name__ == "__main__":
    main()
