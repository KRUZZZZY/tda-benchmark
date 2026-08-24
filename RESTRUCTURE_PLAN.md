# RESTRUCTURE PLAN — dissertation.tex, forward-only, no repetition

**Goal:** restructure the paper so (a) every result appears exactly once, at its
final protocol, (b) there is no narrative of self-discovery/correction, and
(c) the thesis is the end conclusion. Preserve every number exactly — only
locations change.

**Status:** PLAN ONLY — not executed. All audit fixes remain in place; this
plan moves/merges/deletes prose, never results.

---

## Principles (non-negotiable)

1. **One statement per result.** The headline numbers (6.39pp [6.13,6.65],
   3.22pp, 24.89pp→4.30pp r25, 99.85%, 0.434/1.82, 616/672) appear in full in
   exactly ONE place (the Results chapter) plus ONE summary sentence each in
   the abstract and conclusion. Everywhere else: cross-reference (§4.1).
2. **Final protocol only.** The paper currently narrates protocol evolution
   ("single-split showed X, repeated CV shows Y", "this resolves the earlier
   menu-dependence concern", "under level matching it collapsed to 0.24pp").
   Delete all of it. §3 states THE protocol (repeated 25-fold CV, corrected
   CIs, level-matched analyses) once; results are reported at that protocol.
3. **No self-discovery.** Remove: "we first/initially", "surprisingly",
   "this resolves/confirms the earlier concern", "again", "not an artefact
   of" (reframe positively: "the ordering persists under X"), "the magnitude
   is menu-dependent, the ordering is not" (fold into the thesis statement
   ONLY). Corrections fold silently into the final numbers.
4. **No duplicate sections.** Merge the overlapping pairs (below).
5. **Thesis is the end.** Chapter 6 is short and ends with the thesis.
6. **Appendices are reference material** — repetition there is fine; untouched.

---

## Current structure → target structure

| Current | Problem | Target |
|---|---|---|
| Ch1 Introduction (1.1 gap, 1.2 pipeline, 1.3 contributions) | thesis preview absent | Ch1 + one-sentence thesis preview at end of 1.3 |
| Ch2 Foundations (6 sections) | fine (math) | Ch2 unchanged |
| Ch3 Framework (3.1 mappings, 3.2 preprocessing, 3.3 software) | protocol scattered | Ch3 + consolidated protocol block (CV scheme, seeds, level-matched conventions) |
| Ch4 Results (4.1 stage variance, 4.2 noise, 4.3 Pareto) | core results; some backtracking in 4.1 | **Ch4 Results** — 4.1 Stage variance (triplet ONCE), 4.2 Robustness of the ordering (noise, matched-genus, diverse filtrations, hyperparameters, cross-library, concat), 4.3 Generalisation and conditions (panel, MIT-BIH, topology-wins, 10-class inversion), 4.4 Mechanism (predictive-theory null, mixed model, H2), 4.5 Computational costs |
| **§5.1 Why Vectorization Dominates** | restates §4.1 (duplicate) | **DELETE** — unique insights folded into §4.1/§4.4 |
| §5.2 Non-Topological Context & Limitations | overlaps §5.5 | merge with §5.5 |
| §5.3 Multi-Dataset Generalisation (5.3.1-5.3.3) | good content; backtracking prose inside | content moves into Ch4.3/4.4; backtracking stripped |
| §5.4 Operational Guidelines | duplicates Ch6 decision tree | merge with §6.1 → one guidance section |
| §5.5 Threats to Validity | second limitations section; process-language ("mitigation (done)") | → **Ch5 Limitations and Boundary Conditions** (reframed as conditions, not process) |
| Ch6 Conclusion & Operational Guidelines | operational guidance dilutes the thesis | **Ch6 Conclusion** — guidance section moved to Ch5; Ch6 = thesis only |
| Appendices A–E | fine | unchanged |

## Target structure (6 chapters)

1. **Introduction** — gap (prior benchmarks fix a dimension), question (which
   stage matters, and under what conditions), contributions, thesis preview.
2. **Mathematical Foundations** — unchanged.
3. **Framework and Reproducibility** — pipeline, preprocessing, software,
   consolidated protocol block.
4. **Results** — the settled findings, each stated once (subsections above).
5. **Conditions, Limitations, and Guidance** — boundary conditions
   (from §5.2+§5.5, reframed), the decision tree + operational guidance
   (from §5.4+§6.1).
6. **Conclusion** — the thesis as the answer to the research question
   (~1-2 pages, no re-listed numbers, ends with the thesis statement).

---

## Repetition inventory (what to deduplicate)

| Item | Count now | Action |
|---|---|---|
| 6.39pp triplet | 17 | keep ~3 (abstract, §4.1, conclusion) |
| 3.22/1.65 MNIST | 15 | keep ~3 |
| 24.89pp ECG5000 | 13 | keep ~2 (it is the single-split datum; r25 4.30 is the result) |
| 616/672 | 9 | keep ~2 (abstract, §3 protocol) |
| "extensible to 7/11/4" | 3 | keep 1 |
| 99.85% / 0.434 / 1.82 | 5-11 | keep abstract + the §4.2 result once |
| "single-split" | 31 | reduce to ~2 (the matched-genus + ECG5000 protocol notes that genuinely need it) |
| "not an artefact of" | 2 | rephrase positively |
| "earlier"/"again"/"resolves" | ~8 | delete (self-discovery) |

## Backtracking-phrase inventory (delete/rephrase)

- "under level matching (\\S4.1), but under the fixed panel grid and repeated
  CV the vectorizer dominates" → report only the repeated-CV result.
- "This resolves the earlier menu-dependence concern for this dataset" → delete.
- "the single-split ... collapsed to ..." → delete (the collapse is the
  old-protocol story; the final protocol gives 4.30pp).
- "Vectorization dominance is therefore not a default-settings artefact" →
  "The ordering is insensitive to per-vectorizer tuning (§4.2)".
- "the vectorizer dominates again" → "the vectorizer leads".
- Threats entries "Mitigation (planned/done)" → boundary-condition statements
  ("Boundary: ...", no process tense).

## Execution steps (when approved)

1. Inventory pass: script-locate every instance of the repetition/backtracking
   patterns above (grep manifest → checklist).
2. Restructure by moving whole blocks (Python line-surgery): build Ch4
   subsections from §4.1+§5.3 content; merge §5.2+§5.5; merge §5.4+§6.1;
   delete §5.1; strip backtracking prose.
3. Insert cross-references (§4.1, §4.2, …) where full numbers were removed.
4. Rewrite Ch5/Ch6 openings/closings to remove the process narrative.
5. Compile 2×, check 0 undefined/multiply-defined, page count, number
   integrity (13-key baseline unchanged).
6. Vision pass on changed pages.
7. 3-agent audit (L5 internal-consistency + L11 prose) on the restructured
   doc; apply consensus fixes.
8. Commit + push; KB article; regenerate exports/release if structure changes
   affect REPRODUCING.md.

## Verification gates

- Number baseline (13 headline values) identical after restructure.
- grep: 0 instances of the backtracking-phrase inventory.
- Headline counts: 6.39 ≤ 4, 616 ≤ 3, "single-split" ≤ 3, "extensible" ≤ 1.
- Each result's full statement appears in exactly one chapter.
- Compile clean; 0 undefined; vision pass on changed pages.
