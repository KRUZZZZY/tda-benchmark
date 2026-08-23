#!/usr/bin/env python3
"""Insert the #6 topology-wins paragraph into dissertation.tex.

Finding (data/tda/topology_wins_sweep.db, 80/80 runs, re-derived):
  - On 3 genuinely topology-carrying dynamical datasets (Lorenz-vs-Roessler
    Takens, double-well vs single-well, noisy circle vs torus; 86-99%
    accuracy) vectorization REMAINS the dominant stage: VEC range
    3.75-13.75pp vs FIL 1.04-5.10pp. The filtration stage is relatively
    larger than on ECG200 (FIL 0.66pp there) but never overtakes.
  - ModelNet10 + Outex (10-class, hard for TDA): low absolute accuracy
    (23-24%) but same VEC > FIL pattern.
  - Conclusion: vectorization-dominance is NOT an artefact of the
    decorative-topology regime; it survives where topology genuinely
    carries the signal. This is the #6 novelty-candidate result.
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "dissertation.tex"

P6 = r"""
\paragraph{The topology-wins regime (expansion 6).} The stage
decomposition above was measured where TDA loses to raw baselines, so
stage importance could in principle be an artefact of measuring a
regime where topological features are decorative. To test this, the
same decomposition (two filtrations $\times$ four vectorizers $\times$
two classifiers, 5-fold CV seed 42 rep 1) was run on datasets where
topology is known to carry the signal: Lorenz versus R\"ossler Takens
reconstructions (strange-attractor $\beta_1$ structure), a double-well
versus single-well Langevin pair (the persistent $H_0$ pair of the two
metastable wells), and a noisy circle versus torus cloud pair ($\beta_1
{=}1$ vs.\ $2$), plus two harder ten-class arms (ModelNet10 point
clouds and Outex textures) as a scale check
(\texttt{data/tda/topology\_wins\_sweep.db}, 80 finished runs). On the
three dynamical datasets, where TDA succeeds (mean accuracy
$86$--$99\%$), \textbf{vectorization remains the dominant stage}:
vectorizer marginal ranges span $3.75$--$13.75$~pp across datasets
against filtration ranges of only $1.04$--$5.10$~pp (double-well
$13.75$ vs.\ $5.10$; circle/torus $3.75$ vs.\ $1.56$; Lorenz/R\"ossler
$9.58$ vs.\ $1.04$). The filtration stage is \emph{relatively} larger
than in the original regime (where it was $0.66$~pp on ECG200) but
never overtakes vectorization. The two ten-class arms reproduce the
ordering at low absolute accuracy (ModelNet10 vectorizer $13.06$ vs.\
filtration $1.62$~pp at $\sim$24\%; Outex $9.11$ vs.\ $2.94$~pp at
$\sim$23\%), so the pattern is not confined to easy separations.
Vectorization-dominance is therefore not an artefact of the
decorative-topology regime: it persists where topology genuinely
carries the classification signal, and the filtration stage's
contribution grows modestly rather than reversing the ordering.
"""


def main() -> None:
    src = TEX.read_text()
    dry = "--dry-run" in sys.argv
    # insert after the #9 H2 paragraph (end of the expansion block, before
    # the §5.5 Threats section)
    anchor = "would be the appropriate test of whether second homology ever\nmatters for classification.\n"
    n = src.count(anchor)
    print(f"[{'OK' if n==1 else 'FAIL'}] #9 paragraph end anchor: {n}")
    if n != 1:
        sys.exit(1)
    if dry:
        print("dry-run: anchor unique; no write.")
        return
    src = src.replace(anchor, anchor + "\n" + P6, 1)
    TEX.write_text(src)
    print("[APPLIED] topology-wins paragraph inserted after #9")


if __name__ == "__main__":
    main()
