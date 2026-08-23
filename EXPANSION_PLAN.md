# TDA Benchmark Paper — Expansion Plan (external feedback)

- **Date received:** 2026-08-21
- **Applies to:** `dissertation.tex` — "A Systematic Benchmark of Persistent Homology Pipelines for Classification" (54 pp, 6 chapters + 5 appendices)
- **Repo:** github.com/KRUZZZZY/tda-benchmark
- **Status:** Recorded for planning; execution not started (see status tracker at the bottom)
- **Provenance:** External review feedback on the dissertation, transcribed verbatim below. Prior audit/completion state documented in `HANDOFF_PROMPT.md`.

---

## Preamble

> Here's a comprehensive expansion plan, ordered roughly by how much each item strengthens the central claim. The paper's own limitations section already names some of these — the difference between naming a gap and closing it is exactly the gap between a strong dissertation and a publishable paper.

---

## Tier 1 — Fixes the core scientific vulnerability

### 1. Diversify the filtration menu

This is the single most important change. Right now three of four filtrations (VR, weak Alpha, Sparse Rips) approximate the same Rips-type geometry, so "filtration barely matters" is partly baked in. Add filtrations that see genuinely different structure:

- DTM (distance-to-measure) filtration — robust to outliers, behaves very differently under noise
- Weighted/kernel-density Rips
- Lower-star filtrations on different scalar functions (height, curvature estimates)
- For images: sublevel vs superlevel vs signed-distance cubical, and radial/erosion filtrations (the family Conti et al. actually varied — this directly tests whether their 18–94% swing reproduces under your protocol)

If vectorization still dominates with a genuinely diverse filtration pool, the claim becomes robust instead of menu-dependent. If it doesn't, you've discovered the real boundary condition — equally publishable.

### 2. Report the stage comparison on an equal footing

The 7-vs-3-level range comparison is confounded by level counts. Lead with ω² (you already compute it), and add a levels-matched analysis: best-3 vectorizers vs 3 filtrations, or pairwise "swap one stage, hold others at best" deltas. Also report ranges excluding the degenerate scalar vectorizers (entropy, amplitude), since much of the 6.39pp/24.89pp is a floor effect from a single-number representation being bad — an unsurprising result that inflates the headline.

### 3. Add interaction effects to the ANOVA

The current model is main-effects-only, but Appendix D shows the vectorizer×classifier interaction can dominate on subsets. A full factorial ANOVA with two-way interaction terms (you have the data already) tells you whether "stages" are even separable — if interactions carry large η², the whole stage-dominance framing needs qualifying, and finding that yourself is far better than a reviewer finding it.

---

## Tier 2 — Broadens the evidence base

### 4. Scale the multi-dataset panel and make it stage-capable

The 9-dataset panel currently runs VR-only on time series, so it can't compare filtration vs vectorization at all. Run at least 2–3 (working) filtrations across the full panel, and grow it: the UCR archive has 128 datasets — 20–30 stratified across lengths/classes is feasible with your runner and turns "two real datasets" into a real distribution of stage effects. Report the distribution of vectorizer-range vs filtration-range across datasets, not just point results.

### 5. Repeated CV everywhere the claims are

ECG200 got 25 repetitions; MNIST got 5; ECG5000, the matched-genus experiment, and the panel are single-split. Bring everything supporting a headline claim to the same protocol so no result rests on a point estimate you've elsewhere shown carries ±1–3pp noise.

### 6. Test the regime where topology actually wins

Everything is currently measured where TDA loses to raw baselines, so stage importance is measured in a regime where topological features are decorative. Add datasets where topology is known to carry the signal (e.g. Outex textures, dynamical-system classification, graph/point-cloud shape benchmarks like ModelNet slices, protein conformations) and run the same decomposition. "Does the dominant stage change when topology matters?" is the natural and important follow-up — and your matched-genus setup is already halfway there: give it the full stage-decomposition treatment.

### 7. Multiclass and scale

Run full 10-class MNIST with your protocol — this directly tests whether Conti et al.'s catastrophic filtration swing appears at scale under controlled conditions (your paper explicitly flags this as the open question). Add larger-n clouds (n ≥ 10³) where Sparse Rips' design point actually applies, so that row in your recommendation table stops being untestable.

---

## Tier 3 — Deepens the method space

### 8. Learned vectorizers

Add PersLay and/or Hofer-style deep sets input layers (you cite both). This is the strongest version of the vectorization-dominance question: if a learned vectorizer beats all fixed ones by a wide margin, vectorization dominance is confirmed and quantified at its ceiling; needs the new factory entry you already scoped.

### 9. H₂ homology

Currently capped at H₁ for cost. Use Alpha complexes in 3D (cheap for H₂) or the Flood Complex you cite; the sphere/torus pair differs in β₂ structure and the torus's second homology is exactly what's being thrown away.

### 10. Hyperparameter-sensitivity arm

You deliberately excluded grid search to avoid conflation — sound, but add a separate small study: tune each vectorizer's key hyperparameters per dataset and report how stage ranges change. This answers "is vectorizer dominance a default-settings artefact?" — a question a strong reviewer will certainly ask, since vectorizers differ hugely in how many knobs they expose.

### 11. Cross-library replication

Rerun a representative configuration subset in GUDHI-native and Ripser-native pipelines. You already found one library-specific fragility (giotto's weak-alpha IndexError crashes on quantized series) — establish whether the accuracy results are library-invariant too.

### 12. Farthest-point sampling ablation

You note uniform random subsampling is inferior to FPS and defer it — actually run it. It's cheap, it touches every point-cloud result, and it closes your own limitation #1 on preprocessing.

---

## Tier 4 — Statistical and theoretical polish

### 13. Predictive theory, not just descriptive results

Chapter 2 is textbook material. A top-level version derives something: e.g., a bound or estimate relating a vectorizer's stability constant / feature dimension to its achievable accuracy range, then tests the prediction against the sweep. Even a rough "Lipschitz constant of vectorization map vs empirical marginal range" correlation would convert the maths chapter from background to contribution.

### 14. Beyond accuracy

Add calibration, AUROC, and per-class breakdowns on the imbalanced sets; you started this with ECG5000's balanced accuracy — make it uniform.

### 15. Bayesian or hierarchical model of stage effects

A hierarchical model (datasets as random effects, stages as fixed) over the full panel would give a principled "population" estimate of stage importance with uncertainty, replacing the per-dataset patchwork of η²/ω²/Friedman.

---

## Tier 5 — Presentation and rigour hygiene

### 16. Fix Figure 4.1's illegible labels; fix the \texttt{} leak in Appendix A line 83.

### 17. Expand Chapter 6 into a genuine synthesis: a decision tree for practitioners with the evidence grade behind each branch.

### 18. Add a threats-to-validity section using standard categories (construct/internal/external) — you have all the content scattered through §5.2; structuring it that way reads as deliberate methodology.

### 19. Pre-register the expansion sweeps (even informally, via a dated protocol file in the repo) — for a benchmarking paper this is a cheap, high-credibility move.

### 20. Package the framework as an installable library with CI and a small test suite, and consider a short companion "benchmark framework" submission (TopoBench-style venues, NeurIPS D&B track) separate from the findings paper.

---

## What I'd actually do first

If the constraint is bachelor's-timeline-plus-some, the highest ratio of grade/publishability per week is: **#1 (diverse filtrations) + #2 (equal-footing stats) + #4 (panel with multiple filtrations) + #10 (hyperparameter arm)**.

Those four together convert the thesis from "careful measurement with a menu-shaped conclusion" to "robust claim with its boundary conditions mapped" — which is the actual difference between a strong dissertation and a paper that survives review at a good venue. **Items #6 and #8** are the two that could turn it into something genuinely novel rather than confirmatory.

---

## Status tracker

Statuses reflect the repo state at the time of recording (HEAD `c3ae98b`). "Partial" = the feedback itself acknowledges work already in the paper/repo.

| # | Tier | Item | Status | Notes |
|---|---|---|---|---|
| 1 | 1 | Diversify the filtration menu (DTM, weighted Rips, lower-star, cubical variants) | 🟡 Partial | DTM-weighted Rips done (B1, 4c48a5c): filtration range 0.69->2.81pp, DTM beats VR on ECG200; lower-star/signed-distance-cubical pending |
| 2 | 1 | Equal-footing stage stats (ω² lead, levels-matched, exclude degenerate scalars) | ✅ Done | 7-vs-3 confound; committed 28cc16e |
| 3 | 1 | Two-way interaction ANOVA | ✅ Done | Data already in hand; committed dd51349 + 736a634 |
| 4 | 2 | Scale panel + make it stage-capable | ✅ Done | B2 (30dba49): 9-dataset panel with 2 working filtrations per modality; vec range > fil range on 7/9 (median 3.32 vs 1.37pp); fil wins on HandOutlines + 10-class MNIST |
| 5 | 2 | Repeated CV everywhere claims are | 🟡 Partial | ECG200 r=25 ✅; MNIST r=5; ECG5000/genus/panel single-split |
| 6 | 2 | Topology-wins regime (Outex, dynamical systems, ModelNet, proteins) | ✅ Done | #6 (1fff5a1): topology_wins_sweep.db 80/80 — VEC 3.75-13.75pp vs FIL 1.04-5.10pp on Lorenz/Roessler, double-well, circle-torus (86-99% acc); ModelNet10/Outex 10-class reproduce ordering at ~23-24%; vectorization-dominance survives where topology carries the signal |
| 7 | 2 | Full 10-class MNIST + n≥10³ clouds | 🟡 Partial | 10-class MNIST ✅ (A3, 6f32a23); n≥10³ = B5 (ac1162d): n=1000 8/8 configs 100.00% both filtrations, sparse 1.83h vs VR 3.6min (~30×); n=3000 INFEASIBLE on this hardware — 0 completions in ~42h across 2 reboot-killed attempts, no giotto mid-config checkpoint; guideline row revised to VR + benchmark-implementation-first |
| 8 | 3 | Learned vectorizers (PersLay / Hofer) | 🟡 Prepared-not-run | Driver sweep_learned_vectorizers.py validated + resume bug fixed (b5522e8); needs torch+perslay in separate .venv-perslay (1-2 GB, driver self-guards); deferred on env decision |
| 9 | 3 | H₂ homology (Alpha-3D / Flood Complex) | ✅ Done | #9 (870046f): h2_alpha_sweep.db 12/12 — 100% both noise levels BUT honest negative: both classes β₂=1 (closed surfaces), sphere H2 lifetimes LONGER (0.63-0.79 vs 0.11-0.30); H1 cap did not discard discriminative info; H2 feasible/cheap (~5-17s/config) |
| 10 | 3 | Hyperparameter-sensitivity arm | ✅ Done | B3 (30dba49): one-param-at-a-time grids; vec range 5.75→4.75pp (ECG200), 1.75→1.62pp (MNIST); dominance not a default-settings artefact |
| 11 | 3 | Cross-library replication (GUDHI/Ripser-native) | ✅ Done | #11 (f95f441): cross_library_sweep.db 90/90 — sphere/torus exact parity across giotto/gudhi-alpha/gudhi-rips/ripser (100.00%); ECG200 VR arms agree to the decimal; svm_rbf collapse identical in all 4; results library-invariant |
| 12 | 3 | FPS ablation | ✅ Done | B4 (30dba49): FPS vs uniform at k=50/15 on sphere/torus n0/n30; no benefit (−0.25pp overall; uniform wins at k=15/σ=0.30); limitation #1 closed |
| 13 | 4 | Predictive theory (stability constant vs range) | ✅ Done | NULL result rho=−0.129 CI [−0.672,+0.469]; honest-null paragraph inserted (08db71b) |
| 14 | 4 | Calibration / AUROC / per-class | ✅ Done | ECG5000 beyond-accuracy (92da848) |
| 15 | 4 | Hierarchical model of stage effects | ✅ Done | MixedLM clf-largest; paragraph inserted with both-orderings framing (08db71b) |
| 16 | 5 | Fig 4.1 labels + Appendix A \texttt leak | ✅ Done | Appendix A leak already fixed (976bbd3); fig_stage_impact renderer fixed (rotation=30, fontsize=8, stage legend, block separators) + regenerated 2026-08-23 |
| 17 | 5 | Ch. 6 practitioner decision tree | ✅ Done | §6.1 decision tree with A/B/C evidence grades + summary table (08db71b) |
| 18 | 5 | Threats-to-validity section (§5.2 → construct/internal/external) | ✅ Done | §5.5 threats-to-validity with DB-verified mitigations (08db71b) |
| 19 | 5 | Pre-register expansion sweeps (dated protocol file) | 🔲 Open | |
| 20 | 5 | Installable framework package + CI; companion framework paper | 🔲 Open | TopoBench-style / NeurIPS D&B |

**Recommended first four (per feedback):** #1 + #2 + #4 + #10 — "careful measurement with a menu-shaped conclusion" → "robust claim with its boundary conditions mapped."
**Novelty candidates:** #6 and #8.
