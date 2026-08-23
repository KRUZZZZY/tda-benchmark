#!/usr/bin/env python3
"""Insert the #9 H2-homology honest-negative paragraph + correct the driver
docstring premise.

Finding (data/tda/h2_alpha_sweep.db, 12/12 runs, re-derived + independently
re-probed 2026-08-23):
  - True gudhi Alpha complex with homology_dimensions=[0,1,2] on the
    existing sphere/torus clouds classifies 100.00% at BOTH sigma=0 and
    sigma=0.30 (3 vectorizers x 2 classifiers, 5-fold CV seed 42 rep 1).
  - BUT both classes carry beta_2 = 1 (closed surfaces: sphere S^2 and
    torus T^2 each enclose one void), so H2 is NOT the discriminator:
    measured max H2 lifetimes sphere 0.63-0.79 > torus 0.11-0.30 (clean),
    the OPPOSITE of a separating signal. The separator is H1 (torus
    beta_1=2: 0.75-0.89 vs sphere 0.13-0.20).
  - Honest conclusion: the H1 cap did NOT throw away class information on
    this pair; H2 computation is feasible and cheap (~5-17 s/config) and
    adds neither signal nor harm. The paper's 'the torus's beta_2 is
    exactly what is thrown away' framing must be corrected: both classes
    have beta_2=1, so the H1 cap was not discarding a discriminative
    feature here.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TEX = REPO / "dissertation.tex"

P9 = r"""
\paragraph{Second homology via the true Alpha complex (expansion 9).}
The sweeps cap homology at $H_1$ for cost, and the manuscript's
limitations note that the torus's second homology is then unmeasured.
To test whether the $H_1$ cap discards class information, the
sphere/torus clouds were re-run with a true Alpha complex
(\texttt{gudhi.AlphaComplex}, radius parameterization, reduced
homology, \texttt{homology\_dimensions=[0,1,2]}) on the same folds
(seed 42, rep 1; three vectorizers $\times$ two classifiers;
\texttt{data/tda/h2\_alpha\_sweep.db}, 12 finished runs). All twelve
configurations score $100.00\%$ at both $\sigma{=}0$ and
$\sigma{=}0.30$, matching the $H_1$-only result. This is not evidence
that $H_2$ carries the signal: both classes are closed surfaces
($\beta_2{=}1$ for the sphere and the torus alike --- each encloses a
single void), so the pair does not differ in second homology. Measured
max-$H_2$ lifetimes are in fact \emph{longer} for the sphere than the
torus ($0.63$--$0.79$ vs.\ $0.11$--$0.30$, clean; overlapping under
$\sigma{=}0.30$), the opposite of a separating feature, whereas the
$H_1$ signature separates cleanly (torus $\beta_1{=}2$: max lifetime
$0.75$--$0.89$ vs.\ sphere $0.13$--$0.20$). The $H_1$ cap therefore did
not discard a discriminative feature on this pair; $H_2$ computation
via the true Alpha complex is feasible and cheap ($\sim$5--17~s per
configuration) and adds neither signal nor harm. A dataset whose
classes differ in $\beta_2$ (e.g.\ solid vs.\ hollow, or higher-genus
shapes) would be the appropriate test of whether second homology ever
matters for classification.
"""

OLD_DOC = """The paper's sweeps cap homology at H1 for cost. The sphere/torus pair
differs in beta2 structure (sphere beta2 = 0, torus beta2 = 1) — the
torus's second homology is exactly what is thrown away at H1."""
NEW_DOC = """The paper's sweeps cap homology at H1 for cost. NOTE (corrected
2026-08-23 after the run): the sphere/torus pair does NOT differ in
beta2 — both classes are closed surfaces with beta2 = 1 (each encloses
one void). The H2-augmented sweep still classifies 100% at both noise
levels, confirming H2 adds neither signal nor harm; the discriminator
is H1 (torus beta1=2 vs sphere beta1=0). See the paper paragraph."""


def main() -> None:
    src = TEX.read_text()
    dry = "--dry-run" in sys.argv
    # insert P9 after the #15 paragraph (end of the expansion block, before
    # the §5.5 Threats section)
    anchor = "within-dataset-range statement, not a population-level one.\n"
    n = src.count(anchor)
    print(f"[{'OK' if n==1 else 'FAIL'}] #15 paragraph end anchor: {n}")
    if n != 1:
        sys.exit(1)
    if not dry:
        src = src.replace(anchor, anchor + "\n" + P9, 1)
        TEX.write_text(src)
        print("[APPLIED] H2 paragraph inserted after #15")

    # fix the driver docstring premise (committed script)
    drv = REPO / "scripts" / "sweep_h2_alpha.py"
    dsrc = drv.read_text()
    m = dsrc.count(OLD_DOC)
    print(f"[{'OK' if m==1 else 'FAIL'}] driver docstring premise: {m}")
    if m == 1 and not dry:
        drv.write_text(dsrc.replace(OLD_DOC, NEW_DOC, 1))
        print("[APPLIED] driver docstring corrected")


if __name__ == "__main__":
    main()
