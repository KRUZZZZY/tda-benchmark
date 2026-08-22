# Pre-Registration Protocol — TDA Pipeline Benchmark Expansion Sweeps

- **Filed:** 2026-08-22
- **Status:** informal, repo-level protocol file (expansion item #19). Filed *before*
  the results of the deferred expansion sweeps (B5 large-n, #6, #8, #9, #11) are
  analysed; the completed sweeps (B1–B4) were registered after the fact and are
  listed for completeness with their commits.
- **Applies to:** `github.com/KRUZZZZY/tda-benchmark` — "A Systematic Benchmark of
  Persistent Homology Pipelines for Classification" (`dissertation.tex`, 6 chapters
  + 5 appendices).
- **Author:** Zachariah Markusson (independent researcher).
- **Scope:** all expansion sweeps and analyses in `EXPANSION_PLAN.md` that produce
  numbers cited in the dissertation.

This file fixes, in advance, the hypotheses, the analysis decisions, and the
exclusion/disclosure rules for every sweep registered below. Any post-hoc change
to these decisions must be recorded in the Deviation Log (§5) — a benchmarking
paper's credibility rests on the analysis being pinned down before the results
are inspected, not on the results being correct.

---

## 1. Primary hypotheses

| ID | Hypothesis | Status of evidence at filing |
|----|-----------|------------------------------|
| H1 | **Vectorization dominates accuracy variance.** Across datasets and modalities, the vectorization stage produces the largest marginal accuracy range (max−min over stage levels, percentage points), exceeding both filtration and classifier ranges. | Supported on ECG200 (r=25), MNIST binary (r=5); test at scale in B5/#6/#11. |
| H2 | **The stage ordering is portable across datasets.** The ordering vectorizer > classifier > filtration (measured on ECG200) replicates on ECG5000, MNIST binary, and the 9-dataset panel; deviations are reported as boundary conditions, not failures. | Supported on ECG200/ECG5000/MNIST-binary; panel partially; 10-class MNIST is a *known* deviation (filtration > vectorizer). |
| H3 | **Topological signal survives noise.** Sphere/torus accuracy stays ≥ 98.5% at σ = 0.30 across configurations; measured bottleneck distances stay far below the corrected stability bound. | Supported at σ ∈ {0.05, 0.15, 0.30}, n = 100; B5 tests n ∈ {1000, 3000}. |
| H4 | **Regime shift (exploratory).** On topology-wins datasets (dynamical systems, textures, shapes, protein proxies) the dominant stage changes: filtration and/or the point-cloud construction matter more than on the current panel (#6). | Unsupported — no evidence yet; primary novelty candidate. |
| H5 | **Learned vectorizers (exploratory).** PersLay / Hofer deep-set entries beat all fixed vectorizers when trained in-domain (#8). | Unsupported — factory stubs only; no torch in the production venv at filing. |

Secondary: the stability/Lipschitz constant of a vectorizer correlates positively
with its empirical marginal accuracy range (#13); a hierarchical stage model
(datasets as random effects) reproduces the per-dataset stage ordering with
population-level uncertainty (#15).

## 2. Analysis decisions fixed in advance

Applied identically by every driver/analysis listed in §4 (matches
`analysis_repeated_cv_r25.py`, `analysis_multidataset_friedman.py`, and the
EXPANSION_PREP conventions):

1. **Per-configuration accuracy = mean over folds** of stratified 5-fold CV
   (`AVG(f.accuracy)` per `run_id`), never max over folds, never a single split
   unless explicitly labelled single-split.
2. **Marginal accuracy for a stage level = mean over all configurations sharing
   that level** (averaging over the other two stages). Marginal range = max − min
   over the stage's levels, in percentage points (pp).
3. **Ranges are reported with uncertainty:** 95% CIs over the per-repetition
   ranges (repeated-measures t-interval across r repetitions); Nadeau–Bengio
   corrected resampled CIs are reported as the conservative variant for r = 25.
4. **Non-parametric inference:** Friedman test with tie-averaged ranks across
   repetitions; exact permutation p-values where feasible; one-sided sign test on
   the repetition-level stage ordering.
5. **Effect sizes:** η² (variance explained) is the primary ordering statistic;
   ω² (population-corrected) is reported alongside to penalise unequal stage-level
   counts. Equal-footing sensitivity: best-3 vectorizers vs 3 filtrations, and
   ranges excluding the degenerate scalar vectorizers (entropy, amplitude).
6. **Seeds:** base 42; per-repetition CV seeds 42 + rep (43–67 for r = 25);
   per-dataset subsampling seeded deterministically via CRC32 of the dataset name.
   No seed is tuned to any result.
7. **No grid search** on any stage; every configuration is a fixed parameter set.
   Hyperparameter sensitivity is a *separate* registered sweep (B3) and is never
   folded into the main factorial design.
8. **Repeated CV everywhere a headline claim is made:** r = 25 for ECG200, r = 5
   for MNIST binary; single-split numbers are labelled as such and never support
   a headline claim on their own.

## 3. Exclusion and disclosure rules

1. **Modality incompatibility (disclosed, not silent):** point-cloud filtrations
   (weak Alpha, Sparse Rips) are incompatible with image data; the 56/672
   configurations affected are excluded with the count and reason reported in the
   paper (§4.1), never silently dropped.
2. **Weak-alpha fragility (first-class result):** giotto-tda's
   `WeakAlphaPersistence` raises `IndexError` on quantized UCR series
   (FordA/FordB/Wafer/ElectricDevices). Crashes are reported as a fragility
   finding (expansion #11 makes this a first-class result), and affected datasets
   are excluded from the panel only with this disclosure.
3. **Sub-sample caps:** `max_samples` and `subsample_points` are fixed per dataset
   at registration time (see EXPANSION_PLAN); caps are never lowered to rescue a
   failed configuration. Uniform random subsampling is the default; FPS is a
   registered comparison arm (B4), not a silent alternative.
4. **Additive-only data policy:** every sweep writes a NEW database; existing DBs,
   datasets, and committed code are never modified. Drivers refuse to run while
   another sweep holds the canonical data lock (documented in driver headers).
5. **Single-CPU serial execution:** one sweep at a time, `n_jobs=1`, no delegation
   of compute (user directive; protects the single workstation).
6. **Reporting of failure:** failed configurations carry their exception text in
   the results DB and are counted in the paper; they are never replaced by
   re-runs with different settings.

## 4. Sweep registry

| ID | Expansion | Driver | DB (all under `data/tda/`) | Status at filing |
|----|-----------|--------|---------------------------|------------------|
| B1 | #1 Filtration diversity (DTM-weighted Rips; residual: lower-star + signed-distance cubical) | `scripts/sweep_filtration_diversity.py` (+ `_more.py` residual) | `filtration_diversity_sweep.db` | B1 done (commit 4c48a5c); residual prepared, not run |
| B2 | #4 Stage-capable multi-dataset panel (9 datasets) | `scripts/sweep_panel_stagecapable.py` | `panel_stagecapable.db` | Done (commit 30dba49) |
| B3 | #10 Hyperparameter-sensitivity arm | `scripts/sweep_hyperparam.py` | `hyperparam_sweep.db` | Done (commit 30dba49) |
| B4 | #12 FPS vs uniform subsampling | `scripts/sweep_fps_ablation.py` | `fps_ablation.db` | Done (commit 30dba49) |
| B5 | #7b Sparse Rips at design point, n ∈ {1000, 3000} | `scripts/sweep_large_n.py` | `large_n_sweep.db` | **RUNNING** (2026-08-22) |
| #5r | #5 r=25 repeated CV residuals (ECG5000 subset, matched-genus, panel subset) | `scripts/sweep_r25_ecg5000.py`, `sweep_r25_genus.py`, `sweep_r25_panel.py` (pattern: `sweep_repeated_cv_r25.py`) | `repeated_cv_r25.db` (extended) | Prepared (not run) |
| #6 | #6 Topology-wins regime (Lorenz/Rössler/double-well, Outex, ModelNet10, protein proxy) | `scripts/sweep_topology_wins.py` + `generate_dynamical_systems.py`, `download_outex.py`, `download_modelnet.py` | `topology_wins.db` (planned) | Prepared (not run) |
| #8 | #8 Learned vectorizers (PersLay, Hofer deep-set) | `scripts/sweep_learned_vectorizers.py` (factory stubs already in `factories.py`, torch NOT in venv) | `learned_vectorizers.db` (planned) | Stubs prepared; sweep not run |
| #9 | #9 H₂ homology (Alpha complex in 3D, sphere/torus β₂) | `scripts/sweep_h2_alpha.py` | `h2_alpha.db` (planned) | Prepared (not run) |
| #11 | #11 Cross-library replication (gudhi-native, ripser-native, giotto) | `scripts/sweep_cross_library.py` | `cross_library.db` (planned) | Prepared (not run) |
| #13 | #13 Predictive theory: stability constant vs empirical range (Spearman ρ + bootstrap CI) | `scripts/analysis_predictive_theory.py` (analysis-only, existing DBs) | reads `repeated_cv_r25.db`, `expanded_results.db`, `panel_stagecapable.db` | Script written (uncommitted); not run |
| #15 | #15 Hierarchical stage model (statsmodels MixedLM; datasets = random effects) | `scripts/analysis_hierarchical_stage.py` (analysis-only) | reads `panel_stagecapable.db` | Script written (uncommitted); not run |

DB names marked "(planned)" are the names fixed at driver creation; they are
listed here so that results can be located unambiguously.

## 5. Deviation log

| Date | Sweep | Deviation from this protocol | Reason |
|------|-------|------------------------------|--------|
| — | — | (none at filing) | — |

Any deviation must be appended here by the orchestrator before the affected
numbers are written into `dissertation.tex`.

## 6. Sign-off

The undersigned confirm that the hypotheses, analysis decisions, and exclusion
rules above were fixed on 2026-08-22, before the deferred sweeps were executed
and analysed.

- [ ] Zachariah Markusson (author)
- [ ] Orchestrator (Hermes, default profile) — applies patches to `dissertation.tex` after B5
