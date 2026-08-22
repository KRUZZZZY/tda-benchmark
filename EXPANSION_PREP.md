# EXPANSION PREP PLAN — all 20 items made turnkey (2026-08-22)

Goal: bring ALL 20 expansion items to "ready to execute" state — drivers written, data
staging defined, analysis scripts present, execution instructions with cost estimates —
so that running them is turnkey. PREP ONLY: no compute sweeps are started here (B5
large-n owns the single CPU, and compute stays serial one-at-a-time per user directive).
Light verification (syntax/import checks) allowed; heavy runs deferred.

## Standing constraints (non-negotiable)
- SINGLE-CPU serial for ALL compute: n_jobs=1, one sweep at a time, NO delegation of compute.
- Additive-only: NEW scripts/DBs/arrays only; never modify existing DBs/datasets/committed code.
- Follow the VERIFIED driver pattern: `scripts/sweep_multidataset.py` / `sweep_mnist10.py`
  (importlib shim for tda_benchmark, `__main__` guard, no side effects on import).
- Venv: `.venv-tda` (sklearn 1.3.2, gudhi 3.13.0, ripser 0.6.15, statsmodels 0.14.6).
- Weak-alpha crashes on quantized UCR series (FordA/FordB/Wafer/ElectricDevices); logistic
  stalls on unscaled betti features (use random_forest/svm_rbf).
- B5 (sweep_large_n.py) is RUNNING — do not start anything else until it finishes.
- No git commits by subagents — orchestrator commits.

## Item-by-item prep

### DONE (no prep needed): #2 #3 #4 #10 #12 #14
Drivers + DBs + analysis + paper paragraphs all committed.

### PARTIAL → finish prep: #1 #5 #7
- #1 residual: lower-star cubical + signed-distance cubical on MNIST (binary) — extend the
  diversity sweep. Driver: `sweep_filtration_diversity_more.py` (copy B1 pattern from
  `sweep_filtration_diversity.py`). Compute: ~1-2h serial.
- #5 residual: r=25 repeated-CV drivers for (a) ECG5000 subset, (b) matched-genus
  sphere/torus, (c) panel subset — `sweep_r25_ecg5000.py`, `sweep_r25_genus.py`,
  `sweep_r25_panel.py` (copy `sweep_repeated_cv_r25.py` pattern, Nadeau-Bengio CIs).
  Compute: 1-2h each serial.
- #7: 10-class MNIST done; large-n = B5 running (already prepped).

### DEFERRED → prepare now: #6 #8 #9 #11 #13 #15 #20
- #6 TOPOLOGY-WINS REGIME (novelty candidate): driver `sweep_topology_wins.py` +
  `generate_dynamical_systems.py` (Lorenz/Rössler/double-well classifiers — self-contained,
  no download) + `download_outex.py` (Outex_TC_00000, documented source + fallback) +
  `download_modelnet.py` (ModelNet10, documented source) + protein via UCR-style proxy
  (document). Runs the full stage decomposition on topology-heavy sets. Compute: 3-8h serial.
- #8 LEARNED VECTORIZERS (novelty candidate): factory entries (PersLay + Hofer-style deep-set
  input layer) in the vectorizer factory + driver `sweep_learned_vectorizers.py` + env note
  (torch + perslay install commands; do NOT install into .venv-tda now). Compute: 2-4h after install.
- #9 H2 HOMOLOGY: driver `sweep_h2_alpha.py` — gudhi Alpha complex in 3D on sphere/torus
  (β2 distinguishes them), homology_dimensions=[0,1,2] + analysis `analysis_h2.py`.
  Compute: ~1-2h serial.
- #11 CROSS-LIBRARY REPLICATION: driver `sweep_cross_library.py` — same representative
  config subset through gudhi-native and ripser-native paths (both installed) vs giotto;
  include the known weak-alpha fragility as a first-class result. Compute: ~2-4h serial.
- #13 PREDICTIVE THEORY: analysis-only script `analysis_predictive_theory.py` on EXISTING
  DBs (expanded_results.db, repeated_cv_r25.db, multidataset_sweep.db): Lipschitz/stability
  constant of each vectorizer vs its empirical marginal accuracy range; Spearman rho + CI.
  Compute: minutes, no sweep.
- #15 HIERARCHICAL MODEL: analysis-only script `analysis_hierarchical_stage.py` using
  statsmodels MixedLM on multidataset_sweep.db (datasets = random effects, stages = fixed,
  per-config accuracy as outcome): population stage-importance estimate + uncertainty.
  Compute: minutes, no sweep.
- #20 FRAMEWORK PACKAGE: `pyproject.toml`, minimal test suite skeleton (pytest), CI workflow
  (GitHub Actions: lint + pytest + pdflatex check), README install section. Non-compute.

### HYGIENE: #16 #17 #18 #19
- #16: fix Figure 4.1 label legibility + Appendix A line-83 `\texttt{}` leak — direct small
  LaTeX edits (safe, no structure change). Draft prepared as patch notes.
- #17: Chapter 6 practitioner decision-tree — draft section `decision_tree_section.tex`
  (standalone, ready to insert after B5 + audit), with evidence-grade table.
- #18: threats-to-validity section draft `threats_to_validity_section.tex`
  (construct/internal/external categories, content pulled from §5.2).
- #19: pre-registration protocol file `PRE_REGISTRATION.md` in repo root (dated, lists the
  expansion sweeps + analysis plans + primary hypotheses + analysis decisions).

## Execution order (after B5)
1. Cheap analyses first: #13, #15 (minutes each, no sweeps).
2. Short sweeps: #9 H2, #1 residual, #5 residuals, #11 cross-library.
3. Long sweeps (one at a time): #6 topology-wins, #8 learned vectorizers (after torch install).
4. #20 packaging CI + #17/#18/#19 inserts + #16 fixes alongside.
5. Then the 3-wave 3-agent audit (multi-sweep-adversarial-audit-prompts), tracker + KB updates.

## Verification gates for every prepared artifact
- `python -m py_compile <script>` passes; import-shim pattern matches verified drivers.
- Driver refuses to run while B5's DB lock is active (document in header, don't implement lock).
- No existing file modified (git status shows only NEW files).
- Each driver has a header: purpose, usage, expected runtime, DB path, additive-only note.
