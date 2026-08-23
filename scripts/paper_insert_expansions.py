#!/usr/bin/env python3
r"""Insert expansion paragraphs #13/#15 and Tier-5 sections #17/#18 into
dissertation.tex (prep-batch deliverables, all numbers re-verified).

Placements (anchors re-verified 2026-08-23 against HEAD 2422ab2):
  - #13 + #15: end of §5.3 (Multi-Dataset Generalisation), after the B5
    paragraph, right before the '\section{Operational Guidelines...}'
    line. They qualify the panel analysis, so they belong at the end of
    the section that houses B2/B3/B4/B5.
  - #18: new §5.5 'Threats to Validity' — after the §5.4 closing
    ('\noindent Chapter~6 synthesizes these findings into a single
    conditional thesis.') and before the '\newpage' that precedes Ch6.
  - #17: new §6.1 'A Decision Tree for Practitioners' — end of Chapter 6,
    after the closing paragraph ('...artefacts of this specific sweep.')
    and before the '\newpage' preceding Appendix A. Promoted from the
    draft's \subsection to \section (Ch6 has no section structure; a
    bare \subsection would number 6.0.1).

Corrections applied to the drafts (orchestrator-verified):
  - #17: two '\S5.4' B5 cross-refs -> '\S5.3' (B5 lives in §5.3; same
    error the wave-3 auditors caught in my own text).
  - #17: weak-alpha fragility attributed to 'expansion #11' -> the B2
    panel (§5.3). #11 is cross-library replication, still deferred; the
    fragility was found by the stage-capable panel.

Verification: each anchor occurs exactly once; --dry-run prints counts.
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path(__file__).resolve().parent.parent / "dissertation.tex"

# ---- #13 + #15 paragraphs (from /tmp/p13_predictive_paper.md, /tmp/p15_hierarchical_paper.md) ----
P13 = r"""
\paragraph{Predictive theory (expansion 13).} The stability review of
\S2.4 and the vectorization review of \S2.5 assign each vectorizer a
Lipschitz constant with respect to the bottleneck distance: landscape,
Betti curve, amplitude and (by assumption) silhouette are $1$-Lipschitz;
persistence image carries $2\sqrt{2}\,\sigma\|\mathbf{w}\|_\infty =
0.283$ at $\sigma{=}0.1$ \cite{adams2017}; persistence entropy and
statistics admit no finite bound. If stability governed dispersion,
smaller constants should predict smaller empirical accuracy ranges.
Correlating each constant with the vectorizer's empirical range
(max$-$min of per-config fold-mean accuracies, the \S4.1 per-config
convention) on ECG200 (25-repetition repeated CV) and binary MNIST,
pooled over $n{=}14$ vectorizer-dataset units, gives Spearman
$\rho = -0.129$ with 95\% percentile-bootstrap CI $[-0.672, +0.469]$,
which includes zero; per panel, $\rho = -0.482$ (ECG200) and $-0.040$
(MNIST). The sign matches the hypothesis, but the data provide no
evidence that the Ch.2 stability constants predict the range structure
of \S4.1 or the panel ordering of \S5.3. We therefore report a null:
the theory did not predict the sweep. With only seven vectorizers per
panel the CIs are wide and the test is exploratory.
"""

P15 = r"""
\paragraph{Hierarchical stage model (expansion 15).} We fit a linear
mixed model to the stage-capable panel of \S5.3 --- per-config mean
accuracy (pp) as outcome, random intercept per dataset, sum-coded
vectorizer/filtration/classifier fixed effects plus modality covariate
(REML; 144 runs, 9 datasets). The population spread of the level
effects is largest for the classifier ($1.81$\,pp; 95\% CI
$[1.16, 2.47]$), then filtration ($1.71$\,pp; $[0.50, 3.04]$), then
vectorizer ($1.18$\,pp; $[0.66, 1.94]$), with fixed-effects variance
shares $43.2$/$38.5$/$18.3$\%; the random-intercept variance
($209.8$\,pp$^2$) dwarfs the residual ($16.4$\,pp$^2$), ICC $0.927$,
and the image-modality shift is $-17.6$\,pp. The older-sweep robustness
pass reproduces the ordering (classifier $1.82$ > vectorizer $1.48$ >
filtration $1.24$\,pp; ICC $0.929$). This ordering is the opposite of
the within-dataset marginal ranges of \S4.1 and \S5.3 (vec $>$ fil $>$
clf): the two measure different quantities --- population level-effect
SD with dataset variance removed versus within-dataset stage means ---
and the classifier's size is inflated by the SVM-RBF majority-class
collapse on TDA features. ``Vectorization dominates'' is therefore a
within-dataset-range statement, not a population-level one.
"""

# ---- #18: Threats to Validity (§5.5) ----
P18 = r"""
\section{Threats to Validity}
\label{sec:threats}

We structure the limitations of \S5.2 into the three standard validity
categories. The purpose is not to multiply caveats but to make explicit,
for each threat, what was done to mitigate it and which expansion item
closes the residual gap. Threat severity follows the usual qualitative
scale; every empirical mitigation cites the database and configuration
count it rests on.

\subsection{Construct Validity}
\label{sec:threats_construct}

Construct validity asks whether the measured quantity --- the marginal
accuracy range of a pipeline stage --- actually captures ``stage
importance'' as claimed.

\begin{enumerate}
  \item \textbf{Range is confounded by the number of stage levels.} The
    headline comparison (7 vectorizers vs.\ 3--4 filtrations) stacks the
    deck: a stage with more levels can span a larger range by chance.
    \emph{Severity: moderate.} \emph{Mitigation (done):} the $\omega^2$
    population effect size corrects for level counts (ECG200 vectorizer
    $\omega^2{=}0.165$, bootstrap CI [0.063, 0.423], vs.\ filtration
    $-0.017$; MNIST vectorizer 0.214 vs.\ filtration 0.143 --- the
    vectorizer CI excludes zero on both real datasets, the ECG200
    filtration CI straddles it; Table \ref{tab:eta2}); the equal-footing
    analysis matches best-3 vectorizers against 3 filtrations (ECG200
    1.21pp vs.\ 0.69pp, re-derived from
    \texttt{repeated\_cv\_r25.db}); and the two-way interaction ANOVA
    (\S4.1) shows the stage decomposition is not an artefact of
    main-effects-only modelling. \emph{Residual:} the levels-matched
    analysis still compares the \emph{best} three vectorizers, which is
    mildly favourable to the vectorizer stage.
  \item \textbf{Scalar vectorizers create a floor effect.} Persistence
    Entropy and Amplitude are single scalars; their poor accuracy inflates
    the vectorizer range from the bottom. \emph{Severity: moderate.}
    \emph{Mitigation (done):} ranges are also reported excluding the
    degenerate scalar vectorizers (ECG200 vectorizer range contracts from
    6.39pp to 3.10pp but remains the largest stage; \S4.1; re-derived
    from \texttt{repeated\_cv\_r25.db}, per-repetition mean method).
    \emph{Residual:} the exclusion rule was applied post hoc, so the
    headline 6.39pp includes the floor effect by design and the paper
    says so.
  \item \textbf{Single-split point estimates are noisy.}
    Per-configuration accuracy varies by 1.09pp on average across the
    five repetitions (sample SD; maximum 3.11pp; 50 of 112
    configurations exceed 1pp; \texttt{repeated\_cv.db}), and the
    headline 83.0\% configuration drops to 79.6\% at $r{=}5$ (rank 4 of
    84; \texttt{repeated\_cv\_r25.db}). \emph{Severity: high for any
    single-split number.} \emph{Mitigation (done):} all headline claims
    rest on the $r{=}25$ repeated-CV protocol with corrected CIs
    (repeated-measures: vectorizer [6.13, 6.65], classifier [3.28,
    3.71], filtration [0.57, 0.81], all excluding zero; Nadeau--Bengio
    corrected: [5.69, 7.10], [2.92, 4.07], [0.37, 1.01]) and
    Friedman/sign-test inference on the repetition-level ordering
    (vectorizer $>$ classifier $>$ filtration in 25/25 repetitions);
    single-split numbers are labelled as such throughout. \emph{Residual:}
    MNIST binary is $r{=}5$; ECG5000 and the panel were single-split at
    the time of writing (expansion \#5r closes this).
  \item \textbf{Accuracy is the only outcome for most of the sweep.} F1,
    precision, and recall are stored per fold but the analysis is
    accuracy-centric. \emph{Severity: low-to-moderate.} \emph{Mitigation
    (done):} beyond-accuracy analysis on ECG5000 (balanced accuracy,
    per-class precision/recall/F1, AUROC, Brier; \texttt{beyond\_accuracy\_ecg5000.db};
    expansion \#14). \emph{Residual:} calibration and AUROC are not
    uniform across datasets.
\end{enumerate}

\subsection{Internal Validity}
\label{sec:threats_internal}

Internal validity concerns confounds and measurement artefacts within the
study.

\begin{enumerate}
  \item \textbf{Single implementation library.} Every filtration and
    vectorizer runs through giotto-tda. \emph{Severity: moderate} --- the
    weak-Alpha fragility (\texttt{IndexError} on quantized UCR series;
    one unfinished run in \texttt{panel\_stagecapable.db},
    ElectricDevices/weighted\_rips/landscape/RF) proves implementation
    dependence is real. \emph{Mitigation (planned):} cross-library
    replication in GUDHI-native and Ripser-native paths (expansion
    \#11), with the fragility reported as a first-class result.
  \item \textbf{Homology capped at $H_1$.} $H_2$ requires $O(n^4)$
    simplices for Vietoris--Rips; the torus's $\beta_2$ is never
    measured. \emph{Severity: moderate.} \emph{Mitigation (planned):}
    Alpha complex in 3D for $H_2$ (expansion \#9).
  \item \textbf{Binary-only classification.} All datasets except ECG5000
    (5 classes) are binary. \emph{Severity: moderate} --- the 10-class
    MNIST probe shows the stage ordering flips at multi-class scale
    (filtration 4.53pp vs.\ vectorizer 3.44pp, $r{=}5$,
    \texttt{mnist10\_sweep.db}), so the binary result is a boundary
    condition, not a law (\S4.2). \emph{Mitigation (done):} the flip is
    reported; \emph{planned:} multi-class breadth (expansion \#6
    datasets).
  \item \textbf{Fixed hyperparameters.} No grid search on any stage, by
    design. \emph{Severity: low} --- the hyperparameter arm (B3,
    \texttt{hyperparam\_sweep.db}) shows vectorizer dominance contracts
    but persists under one-parameter-at-a-time tuning (ECG200
    5.75$\rightarrow$4.75pp; MNIST 1.75$\rightarrow$1.62pp), so dominance
    is not a default-settings artefact. \emph{Residual:} best-tuned
    values carry mild selection optimism (selected on the same folds that
    score the range), which would \emph{inflate} the tuned range --- the
    observed contraction is therefore conservative.
  \item \textbf{Subsampling choices.} Uniform random subsampling caps
    point clouds; farthest-point sampling was deferred. \emph{Severity:
    low.} \emph{Mitigation (done):} the FPS ablation (B4,
    \texttt{fps\_ablation.db}) finds no benefit ($-0.25$pp overall;
    uniform wins at $k{=}15$, $\sigma{=}0.30$: 99.81\% vs.\ 98.94\%).
  \item \textbf{The sphere/torus norm confound.} The classes differ in
    scale as well as topology. \emph{Severity: moderate.} \emph{Mitigation
    (done):} the matched genus-1/genus-2 control (identical norm
    distributions) shows TDA retains 95.83\% where norm features collapse
    to 48--58\% at $\sigma{=}0.30$ (\texttt{baseline\_experiments.db},
    60 fold accuracies). \emph{Residual caveat:} the matched pair is still
    linearly separable in raw coordinates (logistic 100\% at both noise
    levels, \texttt{baseline\_experiments.db}) --- the control isolates
    the norm/scale confound, not linear separability in general.
  \item \textbf{Determinism and exclusion discipline.} Seeds are fixed
    (base 42; per-repetition 43--67; per-dataset CRC32 subsampling in
    \texttt{runner.py}), and the 56/672 excluded configurations
    (point-cloud filtrations on image data) are counted and disclosed
    rather than silently dropped (616 finished runs of 672 in
    \texttt{expanded\_results.db}). ECG200 is energy-normalised (sum of
    squares constant at 95.00 across all 200 signals), so the
    trivial-separator concern does not apply to the executed data
    (\S4.1). \emph{Residual:} five interrupted runs in
    \texttt{repeated\_cv\_r25.db} (silhouette/RF, reps 5--9) were re-run
    under new run IDs; the orphaned rows carry no fold results and do not
    enter any analysis.
\end{enumerate}

\subsection{External Validity}
\label{sec:threats_external}

External validity asks how far the findings generalise beyond the studied
configuration space.

\begin{enumerate}
  \item \textbf{Dataset breadth.} Two time series (ECG200, ECG5000), one
    image pair (binary MNIST), and synthetic point clouds. \emph{Severity:
    high.} \emph{Mitigation (done):} the 9-dataset panel (B2,
    \texttt{panel\_stagecapable.db}) replicates the vectorizer $>$
    filtration ordering on 7/9 datasets (median 3.3pp vs.\ 1.4pp;
    re-derived median 3.33 vs.\ 1.37), and the within-filtration
    vectorizer span remains large even where filtration leads (10-class
    MNIST: 9--10pp). \emph{Planned:} topology-wins datasets (\#6),
    further UCR coverage, multi-patient ECG (MIT-BIH).
  \item \textbf{Single-patient ECG5000.} ECG5000 is BIDMC chf07 --- one
    patient. The time-series result could be patient-specific.
    \emph{Severity: moderate.} \emph{Mitigation (planned):} multi-patient
    MIT-BIH arrhythmia sweep; the panel adds ECG200/ECG5000 diversity but
    not patient diversity.
  \item \textbf{Hardware dependence of runtime results.} Wall-clock
    numbers come from one workstation (8-core, 16GB). \emph{Severity: low
    for ordering claims} (the 3--27\% filtration speed gap is structural:
    simplex counts differ by construction, \S4.3), \emph{moderate for
    absolute numbers}. \emph{Mitigation:} per-configuration wall times and
    peak memory are stored in the results DBs; peak memory was not
    measured per stage.
  \item \textbf{Missing method families.} No learned vectorizers
    (PersLay, Hofer; \#8), no $H_2$ features (\#9), no cross-library
    replication (\#11), no protein/graph modalities. \emph{Severity:
    moderate} --- each is a named boundary of the current claim, and each
    maps to a registered expansion. The paper's contribution is scoped
    accordingly: the internal stage-importance decomposition and the
    framework, not an absolute-accuracy win over classical methods (raw
    baselines beat TDA on the studied sets; \S4.3, \S5.2).
\end{enumerate}
"""

# ---- #17: Decision Tree (§6.1, promoted from draft's \subsection) ----
P17 = r"""
\section{A Decision Tree for Practitioners}
\label{sec:decision_tree}

The conditionality established in this dissertation collapses into a
small decision tree. Each branch names the evidence that supports it and
the grade of that evidence: A = verified under the 25-repetition
repeated-CV protocol with corrected confidence intervals, or replicated
across datasets; B = measured at $r{=}5$ or single-split with consistent
replication; C = single observation or a sweep that has not yet run. The
tree is deliberately conservative --- where the evidence is thin, the
branch says so rather than pretending otherwise.

\begin{enumerate}
  \item \textbf{Modality.} The first question is the data modality.
    \begin{enumerate}
      \item \emph{Time series (after Takens embedding, $d{=}3$, $\tau{=}1$):}
        spend your design budget on the \textbf{vectorizer}, not the
        filtration. Vectorization is the dominant stage (ECG200 marginal
        range $6.39$pp, 95\% CI [6.13, 6.65] over 25 repetitions; ECG5000
        $24.89$pp, single split, 3-vectorizer menu; \S4.1, Table
        \ref{tab:stage_impact}), while filtration contributes $0.69$pp
        (CI [0.57, 0.81]) and classifiers $3.50$pp (CI [3.28, 3.71]).
        \emph{Grade A} for the \emph{ordering}: the vectorizer is the only
        stage whose CI excludes zero, the ordering holds in 25/25
        repetitions, and the $\omega^2$ population effect size (ECG200
        vectorizer $0.165$, CI [0.063, 0.423], vs.~filtration $-0.017$,
        Table \ref{tab:eta2}) confirms it is not a level-count artefact.
        \emph{Caveat:} the measured \emph{margin} is menu-sensitive ---
        excluding the scalar vectorizers cuts it to $3.10$pp, and matching
        level counts (best-3 vectorizers vs.\ 3 filtrations) narrows it to
        $1.21$pp vs.\ $0.69$pp (\S4.1). The ordering survives; the size
        does not.
      \item \emph{Images, binary:} vectorization still leads (MNIST binary
        $3.22$pp vs.\ filtration $1.65$pp, single split; pooled over the
        five repetitions $3.03$pp vs.\ $1.55$pp), but filtration is no
        longer negligible --- prefer the \textbf{cubical} filtration over
        Vietoris--Rips (best-of-family $98.0$\% vs.\ $96.25$\%; \S4.2).
        \emph{Grade B} ($r{=}5$; the vectorizer $>$ filtration ordering
        holds in all five repetitions).
      \item \emph{Images, multi-class ($\ge 10$ classes):} the ordering
        flips. Filtration becomes the larger marginal stage (10-class
        MNIST: $4.53$pp vs.\ vectorizer $3.44$pp; classifier $2.03$pp;
        cubical $29.1$\% vs.\ Vietoris--Rips $33.7$\% within filtration),
        with a $9$--$10$pp span within a single filtration --- still far
        below Conti et al.'s 18--94\% grid-search swing (\S4.2).
        \emph{Grade B} ($r{=}5$, 1000 samples).
      \item \emph{Point clouds:} on saturated topology tasks no stage
        matters: at $\sigma{=}0$ all 112 configurations score
        $\ge 99.5$\% (mean 99.99\%) and every stage range is below
        $0.1$pp (vectorizer $0.09$, filtration $0.02$, classifier $0.05$);
        at $\sigma{=}0.30$ the largest stage range is $0.66$pp
        (vectorizer). \emph{Grade A} for saturation. Where the classes
        differ in genus or component count, TDA separates them nearly
        perfectly and the matched-genus control shows the topological
        signal survives $\sigma{=}0.30$ (TDA $95.83$\% vs.\ norm features
        $48$--$58$\%; \S4.2). \emph{Grade A}.
    \end{enumerate}

  \item \textbf{Budget: accuracy vs.\ runtime.} If wall-clock time is the
    constraint:
    \begin{enumerate}
      \item \emph{Large $n$ ($\ge 10^3$ points):} Sparse Rips is the only
        filtration whose design point applies, and only with an
        implementation-level benchmark at the target $n$: at $n{=}1000$ it
        reaches the same 100.00\% as Vietoris--Rips (8/8 configurations)
        at $\approx 30\times$ the cost ($\sim$1.8h vs.\ $\sim$3.6min), and
        at $n{=}3000$ it did not finish in $\sim$42h on this hardware
        (\S5.3). Vietoris--Rips at $n{=}3000$ is likewise infeasible
        ($O(n^3)$ 2-simplices). \emph{Grade B} (B5 large-$n$ sweep,
        $n{=}1000$: 8/8 finished runs; $n{=}3000$: 0/2 finished).
      \item \emph{Small $n$:} any of Vietoris--Rips, weak Alpha, or
        Cubical; the 3--27\% wall-clock gap between them (\S4.3) rarely
        justifies accuracy risk. Avoid weak Alpha on quantized UCR series
        (giotto-tda raises \texttt{IndexError}; the fragility is a
        first-class result of the B2 panel, \S5.3). \emph{Grade A}
        (wall-clock recorded per configuration in the results DBs).
      \item \emph{Classifier:} prefer Random Forest or logistic regression
        on TDA features. SVM-RBF collapses to the majority class on ECG200
        (66.5\%) in both the TDA-only and the concatenated arms (\S5.2).
        \emph{Grade B}.
    \end{enumerate}

  \item \textbf{Noise level.} In the studied regime ($\sigma \le 0.30$
    additive spatial Gaussian noise, $n{=}100$), noise robustness is not a
    differentiator: mean accuracy across the 112 configurations at
    $\sigma{=}0.30$ is 99.85\% (minimum 98.5\%), and the measured
    bottleneck distances (maximum 0.434) sit far below the corrected
    stability bound ($2\sigma\sqrt{2\ln n} \approx 1.82$) --- the bound is
    conservative, not tight (\S4.2). If your application lives in this
    regime, do not trade accuracy for noise-robust filtrations
    (DTM-weighting gained menu range but not headroom on ECG200; B1).
    \emph{Grade A}.

  \item \textbf{Which vectorizer?} Prefer \emph{distributional} vectorizers
    over scalar summaries:
    \begin{enumerate}
      \item Persistence Entropy --- the single-scalar-per-dimension
        representation --- is the weakest vectorizer on ECG200 (68.95\%
        under $r{=}25$) and catastrophic on ECG5000 (36.87\% vs.\ 61.5\%/
        61.8\% for Betti Curve/Silhouette). \emph{Grade A}.
      \item Top performers by dataset: Persistence Landscapes (ECG200,
        75.32\%), Betti Curve and Silhouette (ECG5000, 61.5\%/61.8\%),
        Betti Curve (10-class MNIST, 33.4\%). \emph{Grade B}.
      \item Persistence Statistics is a zero-parameter, cheap default:
        within 0.3pp of Landscapes on ECG200 at $r{=}5$ (74.8\% vs.\
        75.1\%) and within 2.1pp of the best MNIST configuration (95.9\%
        vs.\ 98.0\%; \S4.1). \emph{Grade B}.
    \end{enumerate}

  \item \textbf{Raw features vs.\ TDA.} On the datasets studied, raw
    features beat TDA alone (ECG200 raw logistic 85.28\% and raw RF
    86.30\% under $r{=}25$ vs.\ 83.0\% single-split best TDA, whose
    repeated-CV mean is 79.6\%; MNIST raw-pixel logistic 99.65\% vs.\
    98.0\%; \S4.3). Do not use TDA as your \emph{only} feature source on
    such data. If you want the geometric signal, \textbf{concatenate}:
    $[\text{raw} \| \text{TDA}]$ adds 0.35--1.72pp over the 25-repetition
    raw baselines (ECG200 87.0\% vs.\ 85.28\%; MNIST 100.0\% vs.\ 99.65\%),
    never hurts with logistic or Random Forest, and the benefit is confined
    to those two classifiers (\S5.2). \emph{Grade B} (single protocol,
    both datasets).

  \item \textbf{Is topology the target?} If the scientific question is
    about shape --- cycle structure, genus, component counts (dynamical
    systems, shape/geometry benchmarks) --- TDA is not a feature extractor
    to be benchmarked against raw baselines; it is the object of study.
    The matched-genus experiment is the proof of concept: TDA retains
    95.83\% where norm/scale features fail (48--58\%). The topology-wins
    regime (expansion \#6) is designed to map this branch with the full
    stage decomposition; until it runs, treat this branch as \emph{Grade
    C}.
\end{enumerate}

\begin{table}[H]
  \centering
  \caption{Decision tree summary with evidence grades.}
  \label{tab:decision_tree}
  \begin{tabularx}{\textwidth}{@{}l l X c@{}}
    \toprule
    Branch & Decision & Evidence (paper) & Grade \\
    \midrule
    Time series & tune vectorizer & ECG200 6.39pp [6.13, 6.65] $r{=}25$; ECG5000 24.89pp (\S4.1, Table \ref{tab:stage_impact}) & A \\
    Image, binary & vectorizer first; cubical $>$ VR & MNIST 3.22 vs.\ 1.65pp; 98.0 vs.\ 96.25\% (\S4.2) & B \\
    Image, multi-class & filtration first & 10-class MNIST 4.53 vs.\ 3.44pp (\S4.2) & B \\
    Point cloud & no stage dominates & all stage ranges $<$ 1pp at $\sigma \le 0.30$; 99.85\% mean at $\sigma{=}0.30$ (\S4.2) & A \\
    Speed, large $n$ & Sparse Rips only with impl.\ benchmark & B5: parity at $n{=}1000$ at $\sim$30$\times$ cost; $n{=}3000$ infeasible (\S5.3) & B \\
    Speed, small $n$ & VR/weak Alpha/Cubical; no weak Alpha on quantized UCR & wall-clock in DBs (\S4.3); fragility finding (B2, \S5.3) & A \\
    Classifier & RF / logistic; not SVM-RBF on TDA features & 66.5\% majority-class collapse, both arms (\S5.2) & B \\
    Noise $\le 0.30$ & no robustness trade-off needed & 99.85\% mean; bottleneck 0.434 $\ll$ 1.82 (\S4.2) & A \\
    Vectorizer & distributional $>$ scalar; entropy last & entropy 68.95\%/36.87\%; landscape 75.32\% (Tables \ref{tab:stage_impact}, \S4.1--\S4.2) & A \\
    Raw available & concat $[\text{raw}\|\text{TDA}]$ with RF/logistic & +0.35--1.72pp over 25-rep raw baselines (\S5.2) & B \\
    Topology is the target & TDA as object of study & matched-genus 95.83 vs.\ 48--58\% (\S4.2); \#6 pending & C \\
    \bottomrule
  \end{tabularx}
\end{table}
"""


def main() -> None:
    src = TEX.read_text()
    dry = "--dry-run" in sys.argv

    # anchor: end of B5 paragraph -> start of §5.4 (insert #13 + #15 there)
    b5_end = "monotone-friendly in giotto-tda 0.6.2 --- a portability finding in\nits own right)."
    sec54 = "\\section{Operational Guidelines for Pipeline Selection}"
    # anchor: end of §5.4 -> \newpage before Ch6 (insert #18)
    sec54_end = "\\noindent Chapter~6 synthesizes these findings into a single\nconditional thesis."
    # anchor: end of Ch6 -> \newpage before Appendix A (insert #17)
    ch6_end = "and which are artefacts of this specific sweep."

    ops = [
        ("#13/#15 after B5 (before §5.4)", b5_end + "\n\n\n" + sec54,
         b5_end + "\n\n" + P13 + "\n" + P15 + "\n\n" + sec54),
        ("#18 as §5.5 (after §5.4 closing)", sec54_end,
         sec54_end + "\n\n" + P18),
        ("#17 as §6.1 (end of Ch6)", ch6_end,
         ch6_end + "\n\n" + P17),
    ]
    n_fail = 0
    for name, old, new in ops:
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
        print(f"\ndry-run: {len(ops)} insertions, {n_fail} anchor failures.")
        return
    if n_fail:
        print(f"\n{n_fail} anchors failed; NOT writing.")
        sys.exit(1)
    TEX.write_text(src)
    print(f"\nwritten: {len(ops) - n_fail} insertions applied to dissertation.tex")


if __name__ == "__main__":
    main()
