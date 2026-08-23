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
- HEAD 4f0b521 (PUSHED to origin/main). Paper 61pp, 0 undefined refs, 0 errors.
  B2/B3/B4 expansion paragraphs + B5 pending. Audit waves 1-2 COMPLETE:
  wave-1 (17 fixes, 976bbd3) + wave-1 deferred (5 fixes + 4 bibitems, 527f963)
  + wave-2 L3/L4/L7 (12 fixes, 4f0b521). All committed + pushed.
- B5 (#7b n>=10^3) sweep_large_n.py RUNNING serially (pid varies; resumable).
  Config 9 of 12 (sparse_rips@n=3000) has consumed ~21h wall time across two
  attempts and is STILL unfinished — giotto sparse@n=3000 is brutal. DB
  large_n_sweep.db: 8 finished configs (4 sparse@1000 ~1.8h each, 4 VR@1000
  ~3.6min each) + config 9 in-flight. Resume = rerun sweep_large_n.py (skips
  finished). The Sparse Rips guideline row in Table 5.x depends on B5's
  outcome.
- Deferred audit items (wave-3 targets): guidelines-table rows (Weak-Alpha
  crash portability, high-noise matched-genus scoping 95.83/91, Betti
  menu-conditionality 5th-of-7, SVM-RBF collapse note), GUDHI-Alpha parity
  artefact (experiment_alpha.py writes /tmp only), empty config_snapshot in
  mnist10/hyperparam DBs, producer-list expansion (~10 of ~18 DBs named),
  '7 of 9 not HandOutlines' sentence misattributed to VR-only panel (it's
  8/9 there; belongs to the stage-capable panel).
- KB: articles created for dissertation entity, expansion-prep, #13/#15,
  audit waves 1-2; vault pushed (505814e).

## IMMEDIATE FIRST STEP
Read the KB plan (slug above) fully, then check B5: if large_n_sweep.db has
<12 finished configs, restart sweep_large_n.py (resumable, skips finished).
Then write the B5 paper paragraph + settle the Sparse Rips guideline row,
pdflatex x2, commit. Then run audit wave 3 (3 agents x L10/L11/L9 + the
deferred wave-2 items listed above), merge 2-of-3, re-verify vs DBs, fix.

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
