#!/usr/bin/env python3
"""Phase B — insert B2/B3/B4 expansion paragraphs into dissertation.tex.

Uses the richer, DB-verified paragraphs from the previous session
(/tmp/B2_panel_paper.md, /tmp/B3_hyperparam_paper.md, /tmp/B4_fps_paper.md)
with LaTeX hygiene fixes:
  * B3: '\emph{\`{a}}t' typo -> 'at'
  * B4: literal backticks -> \texttt{}; inline SQL block removed;
        'Limitation~1' reference reworded (the paper has no numbered
        limitation 1 about subsampling — that number came from the
        external feedback, not the paper's own list).
Line-surgery per the hard process rule: exact-string replace, assert
count == 1, NEVER the patch tool. Reversible: run --dry-run to preview.

Usage:
  .venv-tda/bin/python projects/tda-benchmark/scripts/paper_insert_expansions.py [--dry-run]
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/projects/tda-benchmark/dissertation.tex")

# ── B2 paragraph — inserted before the TDA+raw paragraph in S4.5 ────────────
B2_TEXT = (
    "\\textbf{Panel with a diverse filtration set.} We re-ran the\n"
    "nine-dataset panel with more than one \\emph{working} filtration per\n"
    "modality so that the filtration stage and the vectorization stage could\n"
    "be compared on equal footing (each stage now has at least two\n"
    "alternatives). For the seven time-series datasets the two filtrations\n"
    "were Vietoris--Rips and the DTM-weighted Rips filtration\n"
    "(\\texttt{WeightedRipsPersistence} with \\texttt{weights='DTM'}, a\n"
    "genuinely non-Rips construction); weak alpha was excluded from the\n"
    "time-series arm because it does not complete on the quantized series\n"
    "(Wafer, ElectricDevices, ECG5000), which is itself a portability result.\n"
    "For the two image datasets the filtrations were cubical and\n"
    "Vietoris--Rips. The four vectorizers (persistence image, persistence\n"
    "landscape, Betti curve, silhouette) and two classifiers (RBF-SVM,\n"
    "random forest) were unchanged, and evaluation used the same 5-fold\n"
    "stratified CV with seed 42 (rep 1). Across the nine datasets the\n"
    "filtration marginal range and the vectorization marginal range (each\n"
    "computed as the spread of stage-level means of per-config fold-mean\n"
    "accuracies) are summarized as follows. The vectorization range exceeds\n"
    "the filtration range on $7$ of the $9$ datasets; only HandOutlines\n"
    "($1.90$ vs.\\ $4.22$ pp) and mnist10 ($2.80$ vs.\\ $4.41$ pp) favour\n"
    "filtration. Across datasets the filtration range spans a minimum of\n"
    "$0.31$ pp, a median of $1.37$ pp, and a maximum of $4.41$ pp (mean\n"
    "$2.17$ pp), while the vectorization range spans a minimum of $0.62$ pp,\n"
    "a median of $3.32$ pp, and a maximum of $15.00$ pp (mean $5.11$ pp).\n"
    "Vectorization therefore still dominates on average, roughly $2.4\\times$\n"
    "the filtration range; however the comparison is now built on a genuinely\n"
    "diverse non-Rips filtration rather than Vietoris--Rips alone, and the\n"
    "filtration range is no longer negligible (the previous single-filtration\n"
    "panel fixed that stage, making its contribution invisible). The\n"
    "vectorization lead is concentrated in the range's upper tail: removing\n"
    "the single largest value (fmnist10, $15.00$ pp) lowers the vectorization\n"
    "mean to $3.87$ pp, still above the filtration mean ($2.17$ pp) but by a\n"
    "narrower margin ($1.8\\times$), so the headline that vectorization\n"
    "dominates is robust to the outlier while the magnitude of the lead is\n"
    "sensitive to it.\n"
)

# ── B3 paragraph — appended after B2 (same S4.5 location) ────────────────────
B3_TEXT = (
    "\\paragraph{Hyperparameter sensitivity (expansion B3).}\n"
    "To test whether the vectorizer effect is an artefact of the manuscript's\n"
    "default hyperparameters, we re-ran the two headline datasets (ECG200, Takens\n"
    "$d{=}3,\\tau{=}1 \\to$ Vietoris--Rips; binary MNIST at cubical),\n"
    "sweeping each of the four vectorizers' key hyperparameter one-parameter-at-a-time\n"
    "over a small grid with all other vectorizer parameters fixed at the manuscript\n"
    "defaults: persistence\\_image $\\sigma \\in \\{0.05,0.1,0.2,0.5\\}$ and\n"
    "$n_{\\textrm{bins}} \\in \\{10,20,50\\}$; persistence\\_landscape\n"
    "$n_{\\textrm{layers}} \\in \\{1,3,5\\}$ and $n_{\\textrm{bins}} \\in \\{20,50,100\\}$;\n"
    "silhouette and betti\\_curve $n_{\\textrm{bins}} \\in \\{10,20,50,100\\}$, under\n"
    "random\\_forest and svm\\_rbf with 5-fold CV (seed 42, single split).\n"
    "\\textbf{Tuning each vectorizer to its best setting on its own grid narrows\n"
    "rather than eliminates the vectorizer marginal range.} On ECG200 the range falls\n"
    "from $5.75$pp (defaults; vectorizer means $70.75$--$76.50\\%$) to $4.75$pp\n"
    "(best-tuned; $71.75$--$76.50\\%$)---a $1.00$pp ($\\approx 17\\%$) contraction---because\n"
    "tuning lifts the \\emph{weakest} vectorizers: persistence\\_image improves\n"
    "$70.75 \\to 73.00$ (best at $\\sigma{=}0.5$), overtaking betti\\_curve ($71.75$),\n"
    "while the winner silhouette is already at its default ($76.50$). On binary MNIST\n"
    "the corresponding range is small throughout: $1.75$pp ($95.25$--$97.00\\%$) at\n"
    "defaults vs $1.62$pp ($95.88$--$97.50\\%$) best-tuned, and tuning reorders the\n"
    "family---persistence\\_image jumps from worst ($95.25\\%$) to best ($97.50\\%$,\n"
    "$\\sigma{=}0.5$), displacing betti\\_curve ($97.38\\%$).\n"
    "\\textbf{Vectorizer dominance is therefore not a default-settings artefact: the\n"
    "$\\approx 5$--$6$pp ECG200 vectorizer spread survives each vectorizer being tuned,\n"
    "and tuning neither creates nor destroys the small ($\\lesssim 2$pp) MNIST spread;\n"
    "what it does do is compress the field from below, pulling the weakest vectorizers\n"
    "up toward the leader.} The best-tuned hyperparameters are persistence\\_image\n"
    "$\\{\\sigma{=}0.5,\\, n_{\\textrm{bins}}{=}20\\}$, persistence\\_landscape\n"
    "$\\{n_{\\textrm{layers}}{=}5,\\, n_{\\textrm{bins}}{=}50\\}$ (ECG200) /\n"
    "$\\{n_{\\textrm{layers}}{=}1,\\, n_{\\textrm{bins}}{=}50\\}$ (MNIST), silhouette\n"
    "$\\{n_{\\textrm{bins}}{=}50\\}$ (ECG200, already default) /\n"
    "$\\{n_{\\textrm{bins}}{=}100\\}$ (MNIST), and betti\\_curve\n"
    "$\\{n_{\\textrm{bins}}{=}50\\}$ (ECG200, already default) /\n"
    "$\\{n_{\\textrm{bins}}{=}100\\}$ (MNIST). These ranges are computed over a reduced\n"
    "configuration space (four vectorizers $\\times$ one filtration $\\times$ two\n"
    "classifiers), so their absolute values are not directly comparable to the\n"
    "headline $6.39$pp (ECG200) / $3.22$pp (MNIST) ranges; the default-vs-tuned\n"
    "contrast, however, holds the configuration space fixed. Best-tuned values carry\n"
    "mild selection optimism (each is selected on the same folds that score the\n"
    "range), which would tend to \\emph{inflate} the tuned range, so the observed\n"
    "contraction is conservative.\n"
)

# ── B4 paragraph — replaces the FPS future-work sentence in S3.5 ─────────────
B4_OLD = ("geometry as well as farthest-point sampling would; we use it for\n"
          "simplicity and reproducibility, and note that an FPS variant is a\n"
          "natural ablation for future work (its stability benefit is\n"
          "well documented).\n")
B4_NEW = (
    "geometry as well as farthest-point sampling would; we use it for\n"
    "simplicity and reproducibility. We tested whether the choice matters:\n"
    "greedy farthest-point sampling (FPS) was compared against this\n"
    "uniform-random scheme on the synthetic sphere/torus clouds, reduced to\n"
    "$k \\in \\{50, 15\\}$ points (the native clouds carry 100 points, so the\n"
    "runner's \\texttt{subsample\\_points} knob never fires and the\n"
    "subsampling choice must be made below the native resolution to be\n"
    "nontrivial), under both noise levels and over\n"
    "$\\{$\\texttt{vietoris\\_rips}, \\texttt{weighted\\_rips}(DTM)$\\} \\times$\n"
    "$\\{$\\texttt{betti\\_curve}, \\texttt{persistence\\_landscape}$\\} \\times$\n"
    "$\\{$\\texttt{random\\_forest}, \\texttt{svm\\_rbf}$\\}$\n"
    "(8 configurations per arm, stratified 5-fold CV, seed 42, rep 1;\n"
    "\\texttt{fps\\_ablation.db}). At the design resolution ($k{=}50$) both\n"
    "methods attain 100.00\\% mean accuracy at both $\\sigma{=}0$ and\n"
    "$\\sigma{=}0.30$ --- the task saturates and the two arms are\n"
    "indistinguishable. In the only regime where a difference emerges\n"
    "($k{=}15$), FPS is \\emph{not} better: at $\\sigma{=}0$ FPS scores\n"
    "99.88\\% vs.\\ uniform 100.00\\% ($-0.12$\\,pp), and at $\\sigma{=}0.30$\n"
    "FPS scores 98.94\\% vs.\\ uniform 99.81\\% ($-0.88$\\,pp). Across all 64\n"
    "runs the minimum configurational accuracy is 98.5\\%, even after a\n"
    "$7\\times$ reduction in point count. We therefore do not find support\n"
    "for the premise underlying the earlier deferral: uniform-random\n"
    "subsampling is not materially inferior to FPS on these point clouds ---\n"
    "if anything it is marginally \\emph{better} once the task is pushed\n"
    "below saturation. Because the sphere/torus problem is robustly\n"
    "separable under even aggressive subsampling, it does not expose a\n"
    "regime where sampling density matters; a dataset with fragile or\n"
    "heterogeneously sampled topology would be needed to observe a gap. The\n"
    "subsampling-method choice is therefore immaterial for the synthetic\n"
    "class, and the earlier FPS-future-work note is withdrawn.\n"
)


def line_surgery(tex: str, old: str, new: str, tag: str) -> str:
    n = tex.count(old)
    assert n == 1, f"{tag}: anchor found {n} times (expected 1): {old[:60]!r}"
    return tex.replace(old, new)


def main() -> None:
    dry = "--dry-run" in sys.argv
    tex = TEX.read_text()
    if dry:
        print("DRY RUN — no changes written")
        for tag, old in (("B4", B4_OLD),):
            print(f"  [dry] {tag}: anchor count = {tex.count(old)}")
        b2_target = "\\textbf{TDA and raw features are complementary.}"
        print(f"  [dry] B2/B3 placement anchor count = {tex.count(b2_target)}")
        return
    tex = line_surgery(tex, B4_OLD, B4_NEW, "B4")
    b2_target = "\\textbf{TDA and raw features are complementary.}"
    tex = line_surgery(tex, b2_target, B2_TEXT + B3_TEXT + b2_target, "B2+B3")
    TEX.write_text(tex)
    print(f"  written {TEX} ({len(tex)} chars)")


if __name__ == "__main__":
    main()
