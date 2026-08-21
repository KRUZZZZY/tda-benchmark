#!/usr/bin/env python3
"""Phase B — insert B2/B3/B4/B5 expansion paragraphs into dissertation.tex.

Line-surgery per the hard process rule: exact-string replace, assert
count == 1, NEVER the patch tool. Reversible: run --dry-run to preview.

Verified numbers (all re-derived from the DBs by the orchestrator):
  B2 panel_stagecapable.db (144 runs): vec range > fil range on 7/9
     datasets; median vec 3.32pp vs fil 1.37pp; ecg200 fil 2.81pp
     (reproduces B1); HandOutlines fil 4.22pp (DTM 75.74 vs VR 71.51);
     mnist10 fil 4.41pp (VR 33.61 vs cubical 29.20).
  B3 hyperparam_sweep.db (76 runs): ecg200 vec range 5.75 -> 4.75pp
     (best-tuned); mnist_01 1.75 -> 1.62pp.
  B4 fps_ablation.db (64 runs): FPS - uniform = -0.25pp overall;
     noise30 k=15: 98.94 vs 99.81 (-0.88pp); k=50 both 100.00.
  B5 large_n_sweep.db: filled in after the sweep completes.

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/paper_insert_expansions.py [--dry-run]
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/projects/tda-benchmark/dissertation.tex")

# ── B2 paragraph — append after the Friedman/Nemenyi closing sentence ────────
B2_ANCHOR = ("secondary and dataset-specific.}\n")
B2_TEXT = (
    "\n"
    "\\textbf{Stage-capable panel (two working filtrations per dataset).}\n"
    "The panel above ran a single filtration (Vietoris-Rips) on the\n"
    "time-series arm, so it could rank configurations but not compare the\n"
    "filtration stage against the vectorization stage on equal footing.\n"
    "To make the panel stage-capable, the same 9 datasets were re-run with\n"
    "two genuinely different working filtrations per modality ---\n"
    "Vietoris-Rips and the DTM-weighted Rips (giotto-tda\n"
    "\\texttt{WeightedRipsPersistence}, weights $=$ DTM; Anai et al.)\n"
    "for the seven time series, cubical and Vietoris-Rips for the two image\n"
    "datasets --- across the same 4 vectorizers $\\times$ 2 classifiers\n"
    "(16 configurations per dataset, 5-fold CV, seed as the sweep;\n"
    "\\texttt{panel\\_stagecapable.db}). The vectorizer stage still shows the\n"
    "larger range on seven of the nine datasets: the median vectorizer\n"
    "range is 3.32pp versus 1.37pp for the filtration stage. The\n"
    "filtration stage wins on the other two, and by comparable margins:\n"
    "HandOutlines (filtration range 4.22pp, driven by DTM at 75.74\\%\n"
    "versus Vietoris-Rips 71.51\\%) and 10-class MNIST (4.41pp, with\n"
    "Vietoris-Rips 33.61\\% beating cubical 29.20\\%). ECG200 reproduces the\n"
    "\\S4.6 diverse-filtration result exactly (filtration range 2.81pp;\n"
    "DTM 76.19\\% vs.~73.38\\%), so the two sweeps are internally\n"
    "consistent. The stage ordering is therefore dataset-dependent: on\n"
    "most of the panel the vectorizer remains the binding constraint, but\n"
    "the filtration choice can matter as much on specific datasets, and\n"
    "this is visible only when the panel carries more than one genuinely\n"
    "different filtration per modality.\n"
)

# ── B3 paragraph — after the B2 paragraph (same anchor chain) ────────────────
B3_TEXT = (
    "\n"
    "\\textbf{Hyperparameter-sensitivity: dominance is not a\n"
    "default-settings artefact.} The vectorizers differ in how many knobs\n"
    "they expose, so the marginal ranges above could in principle reflect\n"
    "unlucky defaults rather than representational capacity. To test\n"
    "this, each vectorizer's key hyperparameter (PersistenceImage\n"
    "$\\sigma$/$n_\\text{bins}$, PersistenceLandscape\n"
    "$n_\\text{layers}$/$n_\\text{bins}$, Silhouette and Betti\n"
    "$n_\\text{bins}$) was swept one-parameter-at-a-time around the paper\n"
    "default on ECG200 (Vietoris-Rips) and binary MNIST (cubical), all\n"
    "other parameters held at the default, with the same\n"
    "$\\{ \\text{random\\_forest}, \\text{svm\\_rbf} \\}$ classifiers\n"
    "(\\texttt{hyperparam\\_sweep.db}). Giving every vectorizer its best\n"
    "tuned setting shrinks the vectorizer marginal range only slightly:\n"
    "5.75pp to 4.75pp on ECG200 and 1.75pp to 1.62pp on binary MNIST\n"
    "(classifier-averaged means). The dominance ordering survives at the\n"
    "per-vectorizer optimum on both datasets, and the best-tuned setting\n"
    "is often the default itself (Silhouette and Betti Curve on ECG200;\n"
    "three of four on MNIST). The reported stage ranges are therefore not\n"
    "an artefact of default hyperparameters; the one-parameter-at-a-time\n"
    "grid is a mild lower bound on tuning benefit because it does not\n"
    "search interactions, which favours the null hypothesis we reject.\n"
)

# ── B4 paragraph — replaces the FPS future-work sentence in §3.5 ─────────────
B4_OLD = ("geometry as well as farthest-point sampling would; we use it for\n"
          "simplicity and reproducibility, and note that an FPS variant is a\n"
          "natural ablation for future work (its stability benefit is\n"
          "well documented).\n")
B4_NEW = ("geometry as well as farthest-point sampling would; we use it for\n"
          "simplicity and reproducibility. We measured whether the choice\n"
          "matters: farthest-point sampling (FPS) was compared against this\n"
          "uniform-random scheme on the synthetic sphere/torus clouds at\n"
          "two reduced resolutions ($k \\in \\{50, 15\\}$ points per cloud)\n"
          "under both noise levels, over 2 filtrations $\\times$ 2\n"
          "vectorizers $\\times$ 2 classifiers (\\texttt{fps\\_ablation.db}).\n"
          "FPS provides no accuracy benefit on this task: the arms are\n"
          "indistinguishable at $k{=}50$ (100.00\\% both), and at the\n"
          "degraded $k{=}15$ resolution uniform-random actually scores\n"
          "higher under $\\sigma{=}0.30$ noise (99.81\\% vs.~98.94\\%); the\n"
          "overall FPS $-$ uniform delta is $-0.25$pp. On these\n"
          "classification tasks the uniform-random subsampling is\n"
          "adequate, so the paper's headline results are not an artefact\n"
          "of the subsampling scheme.\n")


def line_surgery(tex: str, old: str, new: str, tag: str) -> str:
    n = tex.count(old)
    assert n == 1, f"{tag}: anchor found {n} times (expected 1): {old[:60]!r}"
    tex = tex.replace(old, new)
    print(f"  [ok] {tag}: replaced 1 occurrence")
    return tex


def main() -> None:
    dry = "--dry-run" in sys.argv
    tex = TEX.read_text()
    if dry:
        print("DRY RUN — no changes written")
    # B2: anchor after the Friedman/Nemenyi section, before the TDA+raw para.
    # The paragraph starting with \textbf{TDA and raw features are complementary.}
    # is our B2 placement point — insert B2 before it.
    b2_target = "\\textbf{TDA and raw features are complementary.}"
    assert tex.count(b2_target) == 1, "B2 placement anchor"
    # B3 goes after B2's inserted text; we chain by inserting B3 right after B2.
    if dry:
        print(f"  [dry] {len(B2_TEXT)} chars B2 before {b2_target[:40]!r}")
        print(f"  [dry] {len(B3_TEXT)} chars B3 after B2")
    else:
        tex = line_surgery(tex, b2_target,
                           B2_TEXT + B3_TEXT + b2_target, "B2+B3")
    tex = line_surgery(tex, B4_OLD, B4_NEW, "B4") if not dry else tex
    if not dry:
        TEX.write_text(tex)
        print(f"  written {TEX} ({len(tex)} chars)")


if __name__ == "__main__":
    main()
