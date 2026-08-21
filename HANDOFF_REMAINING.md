# TDA BENCHMARK — HANDOFF POINTER (for the next agent, 2026-08-21)

You are picking up the TDA benchmark paper mid-expansion, AFTER a model switch.
Read this first, then the authoritative detail in the KB plan:

  KB PLAN (authoritative remaining-work detail):
    ai_kos_read(slug="tda-benchmark-expansion-remaining-plan-2026-08-21")
  Prior KB results:
    tda-benchmark-expansion-phase1-2026-08-21
    tda-benchmark-expansion-b1-dtm-filtration-2026-08-21
  .hermes.md agent rules apply: check the KB first (ai_kos_search).

## PROJECT
- Repo: /home/kruzzzzy/Documents/AI_KOS_PROJECT/projects/tda-benchmark
  (github.com/KRUZZZZY/tda-benchmark), branch main. Paper: dissertation.tex.
- Venv: /home/kruzzzzy/Documents/AI_KOS_PROJECT/.venv-tda/bin/python
  (giotto-tda 0.6.2, gudhi 3.13.0, sklearn 1.3.2, pandas, numpy 1.26.4).
  Run everything with that python; CWD = /home/kruzzzzy/Documents/AI_KOS_PROJECT.
- Package dir is the HYPHENATED 'tda-benchmark': import via the importlib shim
  (see scripts/sweep_multidataset.py) or symlink projects/tda_benchmark ->
  tda-benchmark + sys.path.insert(0, 'projects'). Worker:
  `from tda_benchmark.runner import _run_one_worker`.

## STATE
- HEAD d289e6d (Phase-1 + B1 + B2 + B3 + B4 committed; NOT yet pushed).
  Paper 58pp, 0 undefined refs, 0 errors (B2/B3/B4 paragraphs inserted via
  line-surgery at d289e6d, compiled clean in /tmp). DONE: #3 interaction-ANOVA,
  A1 (#2 equal-footing), A3 (#7a 10-class MNIST), A4 (#14 beyond-accuracy),
  B1 (#1 DTM-weighted-Rips crux), B2 (#4 stage-capable panel), B3 (#10
  hyperparameter arm), B4 (#12 FPS ablation).
- B5 (#7b n>=10^3) sweep_large_n.py RUNNING (serial, n_jobs=1, single-CPU;
  est. many hours — sparse_rips@n=1000 alone ~50+ min/config, VR@1000 and
  sparse@3000 slower). large_n_sweep.db created; resumable (skips finished).
- Untracked scripts remaining: sweep_large_n.py, analysis_large_n.py
  (committed with the B5 result). Drivers for B2/B3/B4 committed (30dba49).

## IMMEDIATE FIRST STEP
Read the KB plan (slug above) fully, then START by REVIEWING the untracked
driver scripts (check importlib shim, __main__ guard, no side effects on
import, additive-only) — prefer porting the verified pattern from
scripts/sweep_multidataset.py / scripts/sweep_mnist10.py. Fix/validate, then
run the sweeps.

## HARD PROCESS RULES
- SINGLE-CPU: n_jobs=1, serial loop, one sim at a time, NO delegation of
  compute. Do NOT re-dispatch B2/B3/B4 in parallel (a parallel dispatch this
  session was discarded). Only the READ-ONLY 3-agent audit waves are delegated.
- ADDITIVE-ONLY: new DBs (data/tda/, gitignored), new arrays, new scripts.
  Never modify existing DBs/datasets/committed code.
- VERIFY every number yourself with sqlite3 (finished_at IS NOT NULL;
  per-config = AVG(f.accuracy) per run_id, never MAX; marginal = stage-level
  mean of per-config means). Subagent reports are self-reports, not facts.
- LaTeX edits via Python line-surgery (exact-string replace, assert count==1),
  NEVER the patch tool; pdflatex x2 in a pristine /tmp copy; check 0 undefined
  refs / multiply-defined; commit per logical unit.
- Logistic stalls on unscaled betti features — use random_forest/svm_rbf.
  weak_alpha crashes on quantized UCR series — use vietoris_rips + weighted_rips
  (DTM) for time series. Sparse Rips slow at large n; VR at n=3000 infeasible.
- Deferred (out of scope): #6/#8/#9/#11/#13/#15/#20.
- After any result, grep the WHOLE paper for stale headline numbers (abstract/
  intro/contributions/tables) — a number must match the DB it cites.

## REMAINING (in order) — full detail in the KB plan
1. B5 (#7b) n>=10^3 — RUNNING serially; write the B5 LaTeX paragraph from
   large_n_sweep.db results when it completes (Sparse Rips at its design point,
   n=1000/3000).
2. PAPER: insert the B2/B3/B4/B5 LaTeX paragraphs via Python line-surgery
   (B2 -> /tmp/B2_panel_paper.md, B3 -> /tmp/B3_hyperparam_paper.md,
   B4 -> /tmp/B4_fps_paper.md; B5 -> write after its sweep). pdflatex x2,
   verify 0 undefined refs, copy PDF, commit + push. B2/B3/B4 paragraphs are
   already written and verified against the DBs; B5's must be written from the
   B5 DB results. Place B3 in the vectorization-dominance section AFTER the
   headline ranges.
3. 3-WAVE audit: 3 read-only auditors per wave, IDENTICAL prompts
   (multi-sweep-adversarial-audit-prompts), merge by 2-of-3, orchestrator
   re-verifies each finding vs the DBs, re-sweep. 3 waves.
4. Tracker + KB: update EXPANSION_PLAN.md; KB research-note per unit; restore
   the tda-experiments skill pointer line ("Full numbers + recipes: ...")
   if still missing (it was confirmed intact 2026-08-21).
