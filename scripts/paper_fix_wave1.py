#!/usr/bin/env python3
"""Wave-1 audit fixes — apply 2-of-3-consensus findings via line-surgery.

Every finding below was re-verified by the orchestrator against the DBs
before inclusion (audit flags are hypotheses, not facts). Exact-string
replace, assert count==1. Deferred to later waves: ECG5000 per-class recall
recompute (needs pooled-count estimator decision), Sparse Rips guideline row
(pending B5 completion), Table D.1 0.01-0.02pp drift (regenerate from DB),
torus H1 range [0.556,1.156] (needs storing in baseline_experiments.db),
Takens d>2d_M justification (L6-3, 1-of-3), Conti H0-only qualifier (L8-2,
1-of-3).

Usage: .venv-tda/bin/python scripts/paper_fix_wave1.py [--dry-run]
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/projects/tda-benchmark/dissertation.tex")

# ── 1. Abstract: equal-footing caveat + ECG5000 single-split label ──────────
F1_OLD = ("vectorization stage dominates classification-accuracy variance on both\n"
          "real datasets: on ECG200 time series (Takens-embedded) it has a\n"
          "marginal range of 6.39pp across 7 vectorizers (95\\% CI [6.13, 6.65];\n"
          "$\\eta^2 = 0.217$) versus 0.69pp for filtration (95\\% CI [0.57, 0.81]),\n"
          "and on binary MNIST it again leads (3.22pp; $\\eta^2 = 0.302$) while\n"
          "the filtration effect is modest (cubical 98.0\\% vs.\\ Vietoris--Rips\n"
          "96.25\\% best of family, 1.75pp). A second time series, ECG5000,\n"
          "replicates the hierarchy (24.89pp vs.\\ 3.60pp).")
F1_NEW = ("vectorization stage is the largest single main effect on\n"
          "classification-accuracy variance on both real datasets: on ECG200 time\n"
          "series (Takens-embedded) it has a marginal range of 6.39pp across 7\n"
          "vectorizers (95\\% CI [6.13, 6.65]; $\\eta^2 = 0.217$) versus 0.69pp for\n"
          "filtration (95\\% CI [0.57, 0.81]). The raw margin is sensitive to the\n"
          "vectorizer menu: excluding the two single-scalar vectorizers\n"
          "(Amplitude, Persistence Entropy) cuts it to 3.10pp, and under\n"
          "level-matched comparison it narrows further (\\S4.1). On binary MNIST it\n"
          "again leads (3.22pp; $\\eta^2 = 0.302$) while the filtration effect is\n"
          "modest (cubical 98.0\\% vs.\\ Vietoris--Rips 96.25\\% best of family,\n"
          "1.75pp). A second time series, ECG5000, shows the raw-menu replication\n"
          "(24.89pp vs.\\ 3.60pp, single split, 3-vectorizer menu; \\S4.1), but the\n"
          "level-matched comparison reverses there (filtration 3.60pp vs.\\\n"
          "vectorizer 0.24pp), so the ECG5000 ordering is menu-dependent.")

# ── 2. §4.1 "order of magnitude" → qualified ────────────────────────────────
F2_OLD = ("Vectorization dominates: its range (6.39pp across 7 vectorizers)\n"
          "is an order of magnitude larger than filtration (0.69pp across 3")
F2_NEW = ("Vectorization dominates on the full menu: its range (6.39pp across 7\n"
          "vectorizers) is roughly nine times larger than filtration (0.69pp across 3")

# ── 3. §4.1 PS "wins or ties in most of 16" → 3/16 verified ─────────────────
F3_OLD = ("within 0.3pp of Persistence Landscapes (75.1\\%), and it wins or ties\n"
          "in most of the 16 $r{=}5$ filtration--classifier cells.")
F3_NEW = ("within 0.3pp of Persistence Landscapes (75.1\\%), and it is best or\n"
          "tied in 3 of the 16 $r{=}5$ filtration--classifier cells (all under\n"
          "SVM-linear), ranking above the median vectorizer in most cells.")

# ── 4. §4.1 mnist10 spans: label the mixed statistics ───────────────────────
F4_OLD = ("filtration the vectorizer span is larger --- cubical 10.40pp,\n"
          "Vietoris-Rips 9.10pp --- so the stage-dominance question is")
F4_NEW = ("filtration the configuration span (vectorizer $\\times$\n"
          "classifier) is larger --- cubical 10.40pp (max over repetitions,\n"
          "SVM-RBF), Vietoris-Rips 9.10pp (pooled, random forest) --- so the\n"
          "stage-dominance question is")

# ── 5. §4.1 ECG5000: disclose 6-vs-4 cell imbalance ─────────────────────────
F5_OLD = ("Two of the\n"
          "twelve configurations fail on a technicality\n"
          "(silhouette-on-weak-alpha produces NaN features) and are excluded.")
F5_NEW = ("Two of the\n"
          "twelve configurations fail on a technicality\n"
          "(silhouette-on-weak-alpha produces NaN features) and are excluded.\n"
          "Both failures are weak-alpha cells, so the weak-alpha marginal is\n"
          "computed over 4 configurations while the Vietoris-Rips marginal uses\n"
          "6 including silhouette --- the filtration range is therefore computed\n"
          "on non-matching vectorizer menus.")

# ── 6. §4.1 Landscape "permutation-invariant" → grid-antagonistic ───────────
F6_OLD = ("Persistence Landscape is essentially permutation-invariant (72.5--80.0\\%\n"
          "unshuffled vs.\\ 79.0--83.5\\% shuffled).")
F6_NEW = ("Persistence Landscape is the only vectorizer whose accuracy \\emph{rises}\n"
          "under row shuffling (72.5--80.0\\% unshuffled, mean 75.5, vs.\\ 79.0--83.5\\%\n"
          "shuffled, mean 82.4; $+6.9$pp), so it is grid-antagonistic rather than\n"
          "grid-driven --- but it is not permutation-invariant.")

# ── 7. §4.2 "typically at most 2σ√(2ln n)" → probability direction ──────────
F7_OLD = ("we use the corrected probabilistic bound of \\S2.4\n"
          "(Equation~\\ref{eq:db_bound}): typically the bottleneck\n"
          "distance between clean and noisy diagrams is at most\n"
          "$2\\sigma\\sqrt{2\\ln n}$, i.e.\\ $d_B \\lesssim 0.91$ at\n"
          "$\\sigma=0.15$ and $\\lesssim 1.82$ at $\\sigma=0.30$ for $n=100$.")
F7_NEW = ("we use the corrected probabilistic bound of \\S2.4\n"
          "(Equation~\\ref{eq:db_bound}). That bound is a typical-scale\n"
          "estimate whose threshold the perturbation maximum exceeds with\n"
          "probability $\\approx 93\\%$ at $d{=}3$ (\\S2.4), so the empirical\n"
          "check is the measured $d_B$ itself, which stays far below the\n"
          "bound (max 0.300 at $\\sigma{=}0.15$, max 0.434 at $\\sigma{=}0.30$;\n"
          "the $2\\sigma\\sqrt{2\\ln n}$ values are $0.91$ and $1.82$ for $n{=}100$).")

# ── 8. §5.2 "dominant, portable stage" → two-part qualified ─────────────────
F8_OLD = ("result that vectorization moves accuracy more than the classifier.\n"
          "The cross-dataset ranking is therefore consistent with the\n"
          "within-dataset finding of \\S4.1: \\emph{vectorizer choice is the\n"
          "dominant, portable stage; the best vectorizer is data-set stable\n"
          "(Betti Curve), while filtration and classifier effects are\n"
          "secondary and dataset-specific.}")
F8_NEW = ("result that vectorization moves accuracy more than the classifier.\n"
          "The configuration-ranking analysis therefore supports \\emph{vectorizer\n"
          "choice as the portable driver of the ranking: the best vectorizer is\n"
          "data-set stable (Betti Curve), with a Betti-to-Landscape rank gap\n"
          "exceeding the critical difference}. The range analysis, however, is\n"
          "dataset-conditional: the vectorizer range exceeds the filtration range\n"
          "on 7 of the 9 panel datasets but not on HandOutlines or 10-class MNIST,\n"
          "where filtration leads (\\S5.3); and the level-matched comparison\n"
          "reverses on ECG5000 and MNIST (\\S4.1). Filtration and classifier\n"
          "effects are therefore not universally secondary.")

# ── 9. §5.2 concat "never harmful" → scoped to TDA-only arm ─────────────────
F9_OLD = ("but consistent and never harmful when the classifier handles TDA\n"
          "features; SVM-RBF collapses to the majority class on TDA features")
F9_NEW = ("and, relative to the TDA-only arm, never harmful (every concatenated\n"
          "configuration reaches or exceeds its TDA-only counterpart); against\n"
          "the raw baselines, however, the gain is configuration-dependent and\n"
          "sometimes negative (e.g.\\ ECG200 VR+PI+logistic concat 77.0\\% vs.\\ raw\n"
          "85.5\\%). SVM-RBF collapses to the majority class on TDA features")

# ── 10. §5.2 run-count claims → finished-runs disclosure ────────────────────
F10_OLD = ("\\path{data/tda/repeated_cv_r25.db} (2100 runs: 84 configurations")
F10_NEW = ("\\path{data/tda/repeated_cv_r25.db} (2100 finished runs: 84 configurations")

# ── 11. Bibliography: perea2022 title/year ──────────────────────────────────
F11_OLD = ("J.~A.~Perea, E.~Munch, and F.~Khasawneh.\n"
           "Template functions: Universal approximations for topological data\n"
           "analysis.\n"
           "\\textit{Foundations of Computational Mathematics}, 2022.")
F11_NEW = ("J.~A.~Perea, E.~Munch, and F.~Khasawneh.\n"
           "Approximating continuous functions on persistence diagrams using\n"
           "template functions.\n"
           "\\textit{Foundations of Computational Mathematics} 23(4):1215--1272, 2023.")

# ── 12. Appendix A YAML \texttt leak ───────────────────────────────────────
F12_OLD = "  db_path: \\texttt{data/tda/expanded\\_results.db}"
F12_NEW = "  db_path: data/tda/expanded_results.db"

# ── 13. §3.1 classifier enumeration: add SVM-linear ─────────────────────────
F13_OLD = ("\\item \\textbf{CLF}. A scikit-learn classifier (LogisticRegression,\n"
           "    SVC with RBF kernel, or RandomForestClassifier with 100 trees).")
F13_NEW = ("\\item \\textbf{CLF}. A scikit-learn classifier (LogisticRegression,\n"
           "    SVC with linear or RBF kernel, or RandomForestClassifier with 100 trees).")

# ── 14. Table 4.1 footnote "fold-level panel below" → Table ref ─────────────
F14_OLD = ("    $p$-values are $F$-test $p$-values from the per-configuration\n"
           "    three-way ANOVA (Table~\\ref{tab:eta2}); the fold-level panel\n"
           "    below is descriptive only, as folds within a configuration share")
F14_NEW = ("    $p$-values are $F$-test $p$-values from the per-configuration\n"
           "    three-way ANOVA (Table~\\ref{tab:eta2}); the fold-level panel of\n"
           "    that table is descriptive only, as folds within a configuration share")

# ── 15. L11: verbatim "Filtration effects are dataset-specific and modest on
#     binary MNIST, not the governing stage." — keep §1.1, rephrase §1.3 ────
F15_OLD = ("96.25\\%); a second time-series dataset (ECG5000) replicates the\n"
           "    hierarchy (24.89pp versus 3.60pp). Filtration effects are\n"
           "    dataset-specific and modest on binary MNIST, not the governing\n"
           "    stage. Conti et al.'s MNIST case study")
F15_NEW = ("96.25\\%); a second time-series dataset (ECG5000) shows the raw-menu\n"
           "    replication (24.89pp versus 3.60pp; the level-matched comparison\n"
           "    reverses, \\S4.1). Filtration choice is a second-order factor on\n"
           "    the datasets tested (exceptions in \\S4.1 and \\S5.3). Conti et\n"
           "    al.'s MNIST case study")

# ── 16. L11: "To test whether" opener variety in §4.1 ECG5000 ───────────────
F16_OLD = ("To test whether\n"
           "vectorization-dominance is specific to ECG200, the stage analysis was\n"
           "run on ECG5000")
F16_NEW = ("The ECG200 result could be instance-specific, so the stage analysis\n"
           "was repeated on a second UCR recording, ECG5000")

# ── 17. L11: split the 112-word B1 panel sentence ──────────────────────────
F17_OLD = ("To test whether the vectorization-dominance\n"
           "ordering is a general property rather than a property of these\n"
           "instances, the same pipeline machinery was run on a wider benchmark\n"
           "panel: five additional time-series datasets (FordA, FordB, Wafer,\n"
           "ElectricDevices, HandOutlines from the UCR archive) and two\n"
           "10-class image datasets (full MNIST and Fashion-MNIST, subsampled\n"
           "to 1000 stratified samples each for runtime), all through the\n"
           "repository's own runner with the paper's Takens embedding\n"
           "($d{=}3,\\tau{=}1$; long series pre-subsampled to 100 points, uniform\n"
           "random with a fixed seed, matching the runner's subsampling\n"
           "convention --- disclosed because the runner's\n"
           "\\texttt{subsample\\_points} knob only fires on 3-D point-cloud\n"
           "input, so series length was capped at data-preparation time).")
F17_NEW = ("To test whether the ordering is a general property rather than a\n"
           "property of these instances, the same machinery was run on a wider\n"
           "panel: five additional UCR time-series datasets (FordA, FordB, Wafer,\n"
           "ElectricDevices, HandOutlines) and two 10-class image datasets (full\n"
           "MNIST and Fashion-MNIST, subsampled to 1000 stratified samples each\n"
           "for runtime), all through the repository's own runner with the\n"
           "paper's Takens embedding ($d{=}3,\\tau{=}1$). Long series were\n"
           "pre-subsampled to 100 points with a fixed-seed uniform draw; this\n"
           "was necessary because the runner's \\texttt{subsample\\_points} knob\n"
           "fires only on 3-D point-cloud input and never caps 2-D series, so\n"
           "series length was capped at data-preparation time.")


FIXES = [
    ("F1 abstract equal-footing+ECG5000", F1_OLD, F1_NEW),
    ("F2 order-of-magnitude", F2_OLD, F2_NEW),
    ("F3 PS wins-or-ties", F3_OLD, F3_NEW),
    ("F4 mnist10 span labels", F4_OLD, F4_NEW),
    ("F5 ECG5000 cell imbalance", F5_OLD, F5_NEW),
    ("F6 landscape invariant", F6_OLD, F6_NEW),
    ("F7 db bound direction", F7_OLD, F7_NEW),
    ("F8 dominant-portable", F8_OLD, F8_NEW),
    ("F9 never-harmful", F9_OLD, F9_NEW),
    ("F10 run-count finished", F10_OLD, F10_NEW),
    ("F11 perea2022 bibitem", F11_OLD, F11_NEW),
    ("F12 appendix tex leak", F12_OLD, F12_NEW),
    ("F13 classifier enumeration", F13_OLD, F13_NEW),
    ("F14 table footnote below", F14_OLD, F14_NEW),
    ("F15 verbatim modest x3", F15_OLD, F15_NEW),
    ("F16 to-test-whether opener", F16_OLD, F16_NEW),
    ("F17 112-word B1 sentence", F17_OLD, F17_NEW),
]


def main() -> None:
    dry = "--dry-run" in sys.argv
    tex = TEX.read_text()
    for tag, old, new in FIXES:
        n = tex.count(old)
        if dry:
            print(f"  [dry] {tag}: anchor count = {n}")
            continue
        assert n == 1, f"{tag}: found {n} occurrences (expected 1): {old[:60]!r}"
        tex = tex.replace(old, new)
        print(f"  [ok] {tag}")
    if not dry:
        TEX.write_text(tex)
        print(f"  written {TEX} ({len(tex)} chars)")


if __name__ == "__main__":
    main()
