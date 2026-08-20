# TDA BENCHMARK PAPER — HANDOFF PROMPT (2026-08-20)

## ROLE
You are picking up the TDA benchmark paper revision project mid-cycle. The paper has
completed a full audit-revision-reaudit cycle and reached "accept with minor revision"
consensus. Your job is to execute the remaining limitation-fixes (detailed below),
following the established process. Read everything before acting.

## PROJECT LOCATION
- Paper + code: /home/kruzzzzy/Documents/AI_KOS_PROJECT/projects/tda-benchmark
  (repo: github.com/KRUZZZZY/tda-benchmark, branch main)
- Current HEAD: 61d0a1d "fix: round-2 review responses — integrity, EVT arithmetic, disclosures"
- Paper: dissertation.tex (~2080 lines, 50pp, compiles clean, 0 undefined refs, 0 multiply-defined)
- Venv: /home/kruzzzzy/Documents/AI_KOS_PROJECT/.venv-tda/bin/python
  (giotto-tda 0.6.2, sklearn 1.3.2, numpy 1.26.4, ripser 0.6.15, gudhi 3.13.0)
- Results DBs: /home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda/
  (expanded_results.db = ground truth 616/672 runs; repeated_cv.db = 560 runs/5 reps;
   baseline_experiments.db; ecg5000 files; synthetic_matched/)
- Package is hyphenated (tda-benchmark): import via importlib shim registering it as
  'tda_benchmark' (see run_all.sh / scripts for the pattern). Run sweeps from CWD
  /home/kruzzzzy/Documents/AI_KOS_PROJECT (runner resolves paths relative to project root).
- IMPORTANT: verify every number against the DBs yourself (sqlite3). Never trust a
  number from prose or a prior agent's report without re-deriving it.

## WHAT HAS BEEN DONE (verified, do not re-litigate)
Round-1 academic review (3 reviewers) = MAJOR REVISION. Fixed via:
1. New experiments (all DB-verified): repeated 5-fold CV (5 reps, seeds 43-47) with
   corrected CIs [5.84,6.34]/[0.35,1.04]/[2.57,3.78]; eta^2 variance decomposition
   (ECG200 vec 0.217 vs fil 0.003; MNIST vec 0.302 > fil 0.166); MNIST marginal ranges
   (vec 3.22pp > fil 1.65pp); non-topological baselines (raw-pixel logistic 99.75% vs
   TDA 98.0% MNIST; raw-signal 85.5% vs 83.0% ECG200); matched genus-1/genus-2 torus
   synthetic (norms at chance 48-58%, TDA 99.75% clean/95.83% at sigma=0.30);
   measured bottleneck distances (max 0.434 vs corrected bound ~1.82); true GUDHI alpha
   vs weak-alpha parity (0-0.8pp at 2-5x cost); ECG5000 second time-series (vec 24.89pp
   vs fil 3.60pp).
2. Thesis reframed: "vectorization dominates classification-accuracy variance on both
   real datasets" (NOT "filtration dominates on images"). Conti et al. reframed as
   complementary case study (18% was their H0-only naive cubical; 94% joint
   filtration+vectorization redesign; no general principle claimed; 10-class MNIST,
   10-split CV, grid search, no time series). Abstract condensed to ~242 words.
3. Bibliography fixed: conti2022/sulowska2026/telyatnikov2024 corrected; hatwar2026
   (unverifiable) removed -> ali2023 + hensel2021; graf2025 authors fixed;
   chazal2014 split into chazalSilh2014 + chazalDesilvaOudot2015.
4. Stability bound: re-attributed to Chazal-de Silva-Oudot (Thm 5.2) for d_B <= 2 d_GH,
   CEH 2007 for function-level/cubical; EVT made honest (d=3 correction 1.16x,
   threshold exceeded ~93% in d=3); exact Friedman Q=10 > 6.40 p~0.0008 for the stage
   ordering; fold-level F re-scoped to descriptive (fold dependence); bound 0.91/1.82.
5. Weak-alpha framing corrected (subcomplex of Rips, not alpha; Nerve Theorem does not
   apply). Cubical-on-ECG200 artifact disclosed (94x3 pixel images) with without-cubical
   robustness check (best 79.5%, hierarchy intact: vec 6.58pp vs fil 0.34pp).

Round-2 review (3 reviewers) = MINOR REVISION consensus (B: accept-with-minor, C: minor,
A: major-borderline-minor). All 12 headline numbers independently re-verified. All
findings fixed in 61d0a1d.

## REPORTS AVAILABLE (read these first)
- /tmp/tda_experiment_stats.md — repeated CV, eta^2, MNIST marginals
- /tmp/tda_experiment_baselines.md — baselines, matched synthetic, bottleneck
- /tmp/tda_experiment_alpha_data.md — true alpha, cubical artifact, ECG5000
- /tmp/tda_research_R1.md, R2.md, R3.md — deep research (literature validation,
  statistical conventions, TDA theory)
- /tmp/tda_round2_A.md, B.md, C.md — round-2 reviews
- /tmp/alpha_experiment_results.json, /tmp/cubical_artifact_results.json,
  /tmp/ecg5000_lean_results.json
- KB articles (AI-KOS): tda-benchmark-audit-round4-2026-08-20,
  tda-benchmark-academic-review-2026-08-20, tda-benchmark-round2-acceptance-2026-08-20

## PROCESS RULES (established, non-negotiable)
1. ADDITIVE-ONLY for data/code: never delete or modify existing DBs, datasets, or
   committed code. New experiments write NEW DBs/scripts. dissertation.tex IS editable.
2. The user's standing rule: additive systems only, never destroy real data. Deletes
   need explicit confirmation. Don't rm anything without asking.
3. Verify every number yourself against the DBs (sqlite3) — subagent reports are
   self-reports, not facts.
4. For multi-agent work: 3-agent consensus waves (identical prompts), merge by
   2-of-3 consensus, verify decisive claims yourself before acting.
5. LaTeX edits: use Python line-surgery, NOT the patch tool (backslash-doubling
   corrupts \item, \%, \cite). After edits: pdflatex TWICE, check 0 undefined refs,
   grep multiply-defined, note page count.
6. Commit + push to main after each logical unit. Commit messages must be specific.
7. After ANY dev task, write a KB article (AI-KOS) documenting what changed.
8. User preference: plan first, then execute. Fan out subagents during implementation.
9. Sparse Rips is slow (~41s/config). For repeated runs, drop it or accept runtime.
10. The user cares about mathematical rigor and evidence over claims.

## REMAINING WORK — THE LIMITATION FIXES (prioritized)

### BATCH A — CHEAP, CLOSE EVERY REMAINING "UNDER-POWERED/MISMATCHED" OBJECTION
A1. Repeated CV r=5 -> r>=25 on ECG200 (112 configs x 25 reps, drop sparse_rips or
    accept ~4-5h at 20 workers). Recompute Nadeau-Bengio CIs; update the paper's CIs
    and the "r=5 was a compute trade-off" statement. Reference: Schulz-Kumpel et al.
    2024 (arXiv:2409.18836) recommends >=25 reps for corrected resampled CI.
A2. Re-run the 4 non-topological baselines (MNIST raw-pixel logistic/RF, ECG200
    raw-signal logistic/RF) under the SAME 25-repetition protocol so baseline CIs are
    directly comparable to TDA repeated-CV numbers (fixes round-2 F4 protocol mismatch).
A3. MNIST repeated CV (56 configs x 5+ reps) — currently single-split with overlapping
    bootstrap CIs [2.00,6.14] vs [0.74,2.69]; repeated CV settles whether vectorizer >
    filtration on images is real.
A4. ECG5000: re-run with balanced accuracy + macro-F1 (classes 2919/1767/96/194/24,
    severely imbalanced); disclose the 714-sample subsample and 2 NaN exclusions in the
    paper; add per-vectorizer CI.
A5. Appendix D (d,tau) sensitivity: actually run it through the runner and store a DB
    (currently flagged as unreproducible/illustrative — make it real).
A6. peak_memory_mb: measure with resource/tracemalloc instead of the dead 0.0 column.
A7. Cubical shuffle ablation (round-2 M6): row/column-shuffle the 94x3 grids; if the
    signal collapses, the cubical result is grid-structure-driven (strengthens the
    disclosure).
A8. eta^2: add omega^2 + bootstrap CIs; extend the multiplicity footnote (Holm/BH) to
    all 18 F-tests in Table 4.4; state cross-dataset eta^2 comparability limits.
A9. Add a trivial majority-class baseline row to every dataset table (benchmark hygiene).

### BATCH B — HIGHER-VALUE SCIENTIFIC LIFTS (recommended)
B1. THE BIG ONE — multi-dataset sweep. The thesis "vectorization dominates on time
    series" rests on n=2 datasets. Add 5-10 UCR time-series datasets (FordA, FordB,
    Wafer, ElectricDevices, HandOutlines, etc.) + 2-3 image datasets (FMNIST subset,
    etc.) through the existing framework (YAML config). Run the canonical DemSar
    cross-dataset test: Friedman + Nemenyi ACROSS datasets. This upgrades the paper
    from "2-dataset case study" to "multi-dataset benchmark" — the exact objection
    round-2 reviewers raised (family-level claims need a sample of datasets).
B2. Multi-patient ECG: MIT-BIH arrhythmia or PhysioNet 2017 (ECG5000 is single-patient
    BIDMC chf07). One download + run kills the single-patient objection.
B3. TDA+raw concatenation ablation: does TDA add value ON TOP of raw features? The
    baselines beat TDA alone (99.75 vs 98.0); concatenated features may show
    complementarity — the honest positive story. Round-2 flagged as "small, high value".

### NOT SOLVABLE (do NOT attempt)
- "TDA beats raw features": the data says raw features win; fabricating a win would be
  fraud. The honest framing (contribution = stage-importance decomposition + framework,
  not beating raw features) is correct and already in the paper.

## EXECUTION ORDER
1. Read all reports in /tmp + the paper + the DB schemas.
2. Plan Batch A (A1-A9) as a delegation batch: 3 agents (stats/repeated-CV,
   baselines+metrics, appendix/ablation/memory), additive-only, verify outputs yourself.
3. Apply text updates to dissertation.tex for each completed fix (Python line-surgery,
   pdflatex twice after).
4. Ask the user before starting Batch B (B1-B3) — B1 is a multi-hour compute + download
   decision; confirm scope first.
5. Commit + push after each batch. Write KB articles documenting outcomes.

## KEY NUMBERS TO RE-VERIFY (ground truth, from the DBs)
- ECG200: vec 6.09pp [5.84,6.34], fil 0.70pp [0.35,1.04], clf 3.18pp [2.57,3.78];
  eta^2 0.217/0.098/0.003; ordering stable 5/5; Friedman Q=10, p~0.0008
- MNIST: vec 3.22pp, fil 1.65pp; eta^2 0.302 vs 0.166; best cubical 98.0 vs VR 96.25
- sigma=0.30: mean 99.85% (112 configs), min 98.5%
- Bottleneck: max 0.434 vs bound 2*sigma*sqrt(2 ln 100) ~ 1.82 (0.91 at sigma=0.15)
- Baselines: MNIST raw-pixel logistic 99.75%, RF 99.0%; ECG200 raw-signal 85.5%, RF 85.0%
- Matched genus-1/2: norms 48-58%, TDA 99.75% clean / 95.83% sigma=0.30 (min 91%)
- ECG5000: vec 24.89pp, fil 3.60pp (10 valid configs of 12; 2 NaN silhouette-on-weak-alpha)
- Without-cubical ECG200: best 79.5%, vec 6.58pp, fil 0.34pp
- Per-config SD across reps: mean 1.09pp, max 3.11pp; 83.0% best is 4th by repeated-CV
  mean (79.6%, SD 1.98pp); cubical+PI+RF best in 4/5 reps (83.2%)

## DELIVERABLE WHEN DONE
- All Batch A fixes applied + verified + committed + pushed
- Paper compiles clean, all CIs updated, disclosures complete
- Batch B scoped with the user and executed if approved
- KB articles written for each work unit
- A final summary of what was solved and what remains (with reasons)
