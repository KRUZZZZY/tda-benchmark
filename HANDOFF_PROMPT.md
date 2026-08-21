# TDA BENCHMARK PAPER — HANDOFF PROMPT (2026-08-21, expansion-plan pause point)

## ROLE
You are picking up the TDA benchmark paper mid-expansion. The paper completed a
full audit-revision-reaudit cycle (data audit + 2 project-audit waves + 2
academic-audit waves, 3-agent consensus each) and converged to **accept-with-
minor-revision at dissertation standards** (54pp, 0 undefined refs, all numbers
DB-verified). The user then received EXTERNAL FEEDBACK (20-item expansion plan)
and approved executing all of A+B+C, deferring #6/#8/#9/#11/#13/#15/#20.
**The session was paused mid-Phase-1** (one expansion item done, #3). Your job:
continue the expansion execution per this handoff.

## PROJECT LOCATION
- Paper + code: /home/kruzzzzy/Documents/AI_KOS_PROJECT/projects/tda-benchmark
  (repo: github.com/KRUZZZZY/tda-benchmark, branch main)
- HEAD: dd51349 "feat(expansion #3): two-way interaction ANOVA ..."
  (UNPUSHED — push it, then continue)
- Paper: dissertation.tex (~2330 lines, 54pp, compiles clean, 0 undefined refs)
- Venv: /home/kruzzzzy/Documents/AI_KOS_PROJECT/.venv-tda/bin/python
  (giotto-tda 0.6.2, sklearn 1.3.2, numpy 1.26.4, ripser 0.6.15, gudhi 3.13.0,
  pandas installed for interaction ANOVA)
- Results DBs: /home/kruzzzzy/Documents/AI_KOS_PROJECT/data/tda/
- Expansion plan (verbatim feedback + status tracker): EXPANSION_PLAN.md
  (committed b93cfa7); KB mirror: tda-benchmark-expansion-plan-2026-08-21
- Execution plan (approved scope + cost map): .hermes/plans/2026-08-21_143000-tda-expansion-execution.md
- Package gotcha: hyphenated dir 'tda-benchmark' — import via importlib shim as
  'tda_benchmark', or symlink projects/tda_benchmark -> tda-benchmark +
  sys.path.insert(0, 'projects'). Run sweeps from CWD=AI_KOS_PROJECT root.
- IMPORTANT: verify every number against the DBs yourself (sqlite3). Never
  trust prose or prior agent reports without re-deriving.

## WHAT HAS BEEN DONE (verified, do not re-litigate)
1. **Batch A** (limitation fixes, commits 2f0d57d + 088946e): ECG200 r=25
   repeated CV (2100 cells, vec 6.39pp [6.13,6.65] / fil 0.69 [0.57,0.81] /
   clf 3.50 [3.28,3.71], ordering stable 25/25, Friedman Q=50 p=1.4e-11,
   Nadeau-Bengio + repeated-measures CIs); baselines at 25-rep parity; MNIST
   repeated CV; ECG5000 balanced-acc + macro-F1 + disclosures; real Appendix D
   (d,tau) sweep; peak memory; cubical shuffle ablation; omega^2 + bootstrap
   CIs + Holm/BH multiplicity; majority-class rows.
2. **Batch B** (multi-dataset lifts, commits ca8112d + a5f6c61 + c5e649f):
   9-dataset Friedman/Nemenyi panel (tie-averaged chi2(7)=32.41 p=3.4e-5,
   Iman-Davenport F(7,56)=8.47 p=4.9e-7, CD=2.48, betti_curve best rank 1.28
   on 7/9 datasets, vectorizer family 2.83/4.22/4.69/6.25); MIT-BIH
   multi-patient ECG (48 patients, patient-disjoint CV, betti 38.75 > PI
   36.08 > sil 30.55 > land 27.65, chance 25%); TDA+raw concat ablation
   (best concat beats both arms: MNIST 100.0 vs 99.75/98.0, ECG200 87.0 vs
   85.28/72.5); weak-alpha fragility finding (giotto IndexError on quantized
   series).
3. **Audit cycle** (8 commits 1392486..b0e9818): all numbers DB-verified by
   3+ independent auditors per wave. Key fixes: tie-averaged Friedman/
   Nemenyi; Appendix D d=2 rows + provenance honesty; peak-memory DB values;
   abstract/intro/conclusions r=25 harmonisation; run_all.sh 2 CRITICAL bugs
   (heredoc SyntaxError + DB-path mismatch — now genuinely reproducible);
   README/AGENTS/ESSAY/HANDOFF sync; CdSO bibitem corrected (Geometriae
   Dedicata 173(1):193-214, 2014); matched-genus raw-coordinate 100% baseline
   disclosed; MIT-BIH 4-class + de Chazal framing; guidelines table now
   recommends Betti Curve per the panel; 'typically' vs 'with high
   probability' bound; per-config p-values; r5/r25 labels everywhere.
4. **a99d4f8**: analysis_multidataset_friedman.py fixed to regenerate the
   paper's published stats (tie-averaged ranks, q=3.031 for k=8); CD figure
   regenerated (CD 2.48).
5. **2ed6f8b**: MIT-BIH window-length sensitivity check (256-sample windows;
   betti top + landscape bottom robust, PI/silhouette middle order window-
   sensitive; disclosed in paper).
6. **dd51349 (expansion #3, DONE but UNPUSHED)**: two-way interaction ANOVA
   (scripts/analysis_interaction_anova.py, /tmp/tda_expansion3_interaction.md).
   FINDING: on ECG200 (r=25 fold-level) two-way interactions carry
   omega^2=0.1874 = **147% of main effects (0.1271)**; filtration:vectorizer
   (0.0924) is the LARGEST effect in the model, vectorizer:classifier
   (0.0889) rivals vectorizer main (0.0858). MNIST: interactions 50% of main.
   => Stages are NOT cleanly separable; the paper's stage-dominance framing
   needs qualification (vectorizer still largest MAIN effect, but 'which
   stage matters' depends on other stages). **The paper text has NOT yet been
   updated for this finding** — that is the next step for #3.

## REPORTS AVAILABLE (read first)
- /tmp/tda_expansion3_interaction.md — interaction ANOVA (expansion #3)
- /tmp/tda_A8_omega2_report.md — omega^2 + bootstrap CIs + Holm/BH (18 tests)
- /tmp/tda_A1_r25_report.md — r=25 repeated-CV stats + Nadeau-Bengio CIs
- /tmp/tda_B1_friedman_report.md — 9-dataset Friedman/Nemenyi
- /tmp/mitbih_w256.log, /tmp/mitbih_sweep_fast.log — MIT-BIH sweeps
- KB articles (AI-KOS): tda-benchmark-batch-a-limitation-fixes-2026-08-21,
  tda-benchmark-batch-b-multidataset-lifts-2026-08-21,
  tda-benchmark-audit-cycle-2026-08-21,
  tda-benchmark-expansion-plan-2026-08-21

## PROCESS RULES (established, non-negotiable)
1. ADDITIVE-ONLY for data/code: never delete/modify existing DBs, datasets, or
   committed code. New experiments write NEW scripts + NEW DBs. dissertation.tex
   IS editable (line-surgery only).
2. Verify every number yourself against the DBs (sqlite3) — subagent reports
   are self-reports, not facts. Verify decisive findings independently before
   acting.
3. Multi-agent work: 3-agent consensus waves (identical prompts), merge by
   2-of-3, verify claims yourself.
4. LaTeX edits: Python line-surgery (exact-string replace, assert count==1),
   NEVER the patch tool. pdflatex TWICE after; check 0 undefined refs /
   multiply-defined; note page count.
5. Commit + push after each logical unit; specific messages.
6. KB article after ANY dev task (AI-KOS, creation protocol).
7. Plan first, then execute. Fan out subagents during implementation.
8. **Single-CPU constraint (user directive): one sim at a time, serial,
   n_jobs=1, no delegation for compute.** Background sweeps with
   notify_on_complete; verify DB after.
9. Sparse Rips is slow (~41s/config shipped). VR on 254-point Takens clouds
   ~6 min/config serial (126-point ~1 min).
10. User cares about mathematical rigor and evidence over claims. Honest
    results only — never fabricate a win.

## REMAINING WORK — THE EXPANSION PLAN (approved scope A+B+C)
Deferred (do NOT attempt): #6 (topology-wins regime), #8 (learned
vectorizers), #9 (H2 homology), #11 (cross-library replication), #13
(predictive theory), #15 (hierarchical model), #20 (package+CI+companion).

### PHASE 1 — Batch A: analysis of existing data (no new sweeps, hours)
- A1 (#2) equal-footing stats: lead with omega^2; levels-matched analysis
  (best-3 vectorizers vs 3 filtrations; swap-one-stage-hold-others-at-best
  deltas); report ranges EXCLUDING degenerate scalar vectorizers (entropy,
  amplitude) — tests whether 6.39pp/24.89pp headline is a single-number-
  representation floor effect. (analysis_equal_footing.py)
- A2 (#3) interaction ANOVA — **DONE (dd51349), script committed; paper text
  NOT yet updated.** Next: write the qualification paragraph into the paper
  (interactions 147% of main on ECG200; fil:vec largest effect; stages not
  cleanly separable; vectorizer still largest main effect), pdflatex x2,
  push.
- A3 (#7a) full 10-class MNIST under paper protocol — data ALREADY BUILT
  (data/tda/images/mnist10_1000_{X,y}.npy: 1000 samples, 100/class). Run
  cubical+VR x 4 vec x 2 clf, r=5 repeated CV → mnist10_sweep.db (~15 min
  serial). Direct Conti et al. 10-class test at scale.
- A4 (#14) beyond accuracy: AUROC (OvR), per-class precision/recall/F1,
  Brier calibration on ECG5000 + MIT-BIH from existing fold predictions.
  (analysis_beyond_accuracy.py)

### PHASE 2 — Batch B: new sweeps (serial, one at a time, hours-day)
- B1 (#1) DIVERSE FILTRATIONS — the scientific crux: 3 of 4 current
  filtrations (VR, weak Alpha, Sparse Rips) approximate the same Rips-type
  geometry, so 'filtration barely matters' is partly baked in. Add DTM
  filtration, lower-star on height/curvature, weighted/kernel-density Rips,
  signed-distance cubical (Conti family). Sweep ECG200 + sphere/torus x 4 vec
  x 2 clf → filtration_diversity_sweep.db. Either outcome publishable.
- B2 (#4) stage-capable panel: rerun 9-dataset panel with 2-3 WORKING
  filtrations (VR + weak_alpha where it works + cubical where applicable),
  report DISTRIBUTION of vectorizer-range vs filtration-range across datasets.
  → multidataset_sweep_fil2.db (~2-3h).
- B3 (#10) hyperparameter arm: tune each vectorizer's key hyperparameter per
  dataset (PI sigma/n_bins, landscape n_layers, silhouette power, betti
  n_bins); report how stage ranges change. Answers 'is dominance a
  default-settings artefact?' → hyperparam_sweep.db (~1-2h).
- B4 (#12) FPS ablation: farthest-point sampling vs uniform-random on
  point-cloud datasets; closes limitation #1 → fps_ablation.db (~30-60 min).
- B5 (#7b) n >= 10^3 clouds: Sparse Rips design point (sphere/torus at
  n=1000/3000) → large_n_sweep.db (~1-2h).

### PHASE 3 — Batch C (#5): repeated CV everywhere claims are
- ECG5000 r>=5 (12 configs, ~40-60 min), matched-genus r>=5 (~10 min),
  panel r=5 (~1h). No headline claim should rest on a single-split estimate.

### PHASE 4 — Batch D: paper surgery
- #16 Fig 4.1 label legibility + Appendix A line-83 \texttt leak.
- #17 Ch. 6 practitioner decision tree with evidence grades per branch.
- #18 threats-to-validity (construct/internal/external; content scattered
  in §5.2).
- #19 pre-registration protocol file (dated) in repo.
- Update EXPANSION_PLAN.md status tracker per item.

## KEY NUMBERS TO RE-VERIFY (ground truth, from the DBs)
- ECG200 r=25: vec 6.39pp [6.13,6.65], fil 0.69pp [0.57,0.81], clf 3.50pp
  [3.28,3.71]; NB CIs vec [5.69,7.10] fil [0.37,1.01] clf [2.92,4.07];
  ordering stable 25/25; Friedman Q=50 p=1.4e-11 (exact perm p ~2e-19).
- Interaction ANOVA (NEW, expansion #3): ECG200 fold-level two-way omega^2
  total 0.1874 = 147% of main 0.1271; fil:vec 0.0924 largest effect;
  vec:clf 0.0889; MNIST interactions 50% of main.
- Panel: chi2(7)=32.41 p=3.4e-5; F(7,56)=8.47 p=4.9e-7; CD=2.48 (q=3.031);
  betti_curve rank 1.28 best 7/9; family 2.83/4.22/4.69/6.25; clf RF 3.51
  vs svm 5.49.
- MIT-BIH: 48 patients, patient-disjoint CV, chance 25%; 128-window
  betti 38.75 > PI 36.08 > sil 30.55 > land 27.65; 256-window betti 38.48 >
  sil 36.1 > PI 31.2 > land 30.1 (middle order window-sensitive);
  weak_alpha fails (giotto IndexError).
- Baselines r=25: MNIST 99.65 [99.60,99.70] / 99.29 [99.19,99.39];
  ECG200 85.28 [84.92,85.64] / 86.30 [85.68,86.92].
- MNIST: vec 3.03pp > fil 1.55pp (r=5 pooled); best cubical/betti/logistic
  98.0% (97.5-98.0 across reps).
- sigma=0.30: mean 99.85% min 98.5% (112 configs); bottleneck max 0.434 vs
  bound 1.82; matched-genus TDA 95.83% vs norms 48-58% (raw-coords 100% —
  disclosed).
- Concat: MNIST 100.0 vs raw 99.65 vs TDA 98.0; ECG200 87.0 vs 85.28 vs
  72.5 (same-config).

## DELIVERABLE WHEN DONE
- All approved expansion items (A+B+C) executed, verified, committed, pushed.
- Paper updated per item (interactions qualification FIRST for #3),
  compiles clean with updated stats and disclosures.
- EXPANSION_PLAN.md tracker updated (17 open -> done/partial per item).
- KB articles per work unit + final summary of solved vs remaining
  (deferred items #6/#8/#9/#11/#13/#15/#20 with reasons).
