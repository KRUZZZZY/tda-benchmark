# EXECUTION-READY RESTRUCTURE PLAN — TDA Dissertation (grounded audit, v2)

**Source:** `/home/kruzzzzy/Documents/AI_KOS_PROJECT/projects/tda-benchmark/dissertation.tex` (3271 lines, read in full).
**Basis:** `RESTRUCTURE_PLAN.md` (117 lines) verified line-by-line against the actual text.
**Status:** READ-ONLY analysis. No file edited. All anchors are exact line numbers in the current file.
**Rendered structure verified via `dissertation.toc`:** Ch5 title p.35 "Vectorization Dominance and Theoretical Synthesis"; §5.1 p.35, §5.2 p.37, §5.3 p.39, §5.3.1 Generalisation p.40, §5.3.2 Robustness p.43, §5.3.3 Mechanism p.46, §5.4 p.48, §5.5 p.49 (5.5.1/5.5.2/5.5.3), Ch6 p.54, §6.1 p.55.

**Reference keys used below**
- Section homes (CURRENT numbering): §4.1 = Stage Variance Analysis (L1051), §4.2 = Noise (L1483), §4.3 = Pareto (L1569), §5.1–§5.5, §6.1 = Decision Tree (L2589), App. D (L2974).
- TARGET numbering (after restructure): new §4.1 Stage variance · §4.2 Robustness of the ordering · §4.3 Generalisation and conditions · §4.4 Mechanism · §4.5 Computational costs · Ch5 Conditions, Limitations, Guidance · Ch6 Conclusion.
- Classification: **KEEP** = abstract / authoritative results section / conclusion (the one full statement). **KEEP-same-section** = another mention inside the same results section (not a cross-section repetition; part of the one statement). **KEEP-REF** = guidance/reference table or decision-tree row that restates the number WITH an explicit §ref (functionally a cross-reference; recommended to keep). **TABLE-MOVE** = number lives in a table being relocated within Ch4 (Table 5.1). **REMOVE→ref** = redundant cross-section restatement; replace with the cross-reference.

---

## A. REPETITION DEDUP TARGETS (per headline number)

### A1. 6.39pp — 17 occurrences (ECG200 vectorizer marginal range)

| Line | Verbatim quote (fragment) | Action |
|---|---|---|
| 140 | "the vectorizer marginal range is 6.39pp (95\% CI [6.13, 6.65]; $\eta^2 = 0.217$)" | **KEEP** — abstract |
| 196 | "vectorizer--filtration gap is 6.39pp (95\% CI [6.13, 6.65]) versus 0.69pp..." | **REMOVE→(§4.1)** — §1.2 preview; keep qualitative "vectorization dominates" |
| 267 | "a 6.39pp marginal range across 7 vectorizers (95\% CI [6.13, 6.65])" | **REMOVE→(§4.1)** — §1.3 contribution 2; keep "largest contributor" |
| 1072 | Table 4.1 row "Vectorizer & Landscapes & 75.32\% & 6.39pp [6.13, 6.65]" | **KEEP** — authoritative results table |
| 1094 | "The full menu favours vectorization: its range (6.39pp across 7 vectorizers)" | **KEEP** — authoritative results prose |
| 1122 | "To test whether the 6.39pp (ECG200) and 24.89pp (ECG5000) vectorizer ranges are an artefact" | **KEEP-same-section** (§4.1 equal-footing; may drop numerals) |
| 1134 | "cuts the ECG200 vectorizer range from 6.39pp to 3.10pp" | **KEEP-same-section** (§4.1 equal-footing result) |
| 1153 | "the published 6.39pp and 24.89pp numbers are substantially inflated by degenerate scalar vectorizers" | **KEEP-same-section** (§4.1; strip the word "published" — see B5) |
| 1723 | "The gap is 6.39pp versus 0.69pp on ECG200 and 24.89pp versus 3.60pp on ECG5000" | **REMOVE→(§4.1)** — §5.1 deleted; reword "the ECG200/ECG5000 gaps (§4.1)" |
| 1754 | Table 5.1 row "Time series (embedded) & Vectorizer & 6.39pp; 24.89pp" | **TABLE-MOVE** — Table 5.1 relocates to new §4.3 (see C1); keep as-is there |
| 2148 | "not directly comparable to the headline $6.39$pp (ECG200) / $3.22$pp (MNIST) ranges" | **REMOVE→(§4.1)** — §5.3.2 hyperparameter block; reword "the headline ECG200/MNIST ranges (§4.1)" |
| 2362 | §5.4 guideline table row "Vectorization dominates variance (6.39pp on ECG200; 24.89pp on ECG5000)" | **REMOVE→(§4.1)** — merged guidance (see C3); "Vectorization dominates variance (§4.1)" |
| 2410 | "the ECG200 vectorizer range contracts from 6.39pp to 3.10pp but remains the largest stage; §4.1" | **REMOVE→(§4.1)** — §5.5 construct item 2; "contracts to 3.10pp (§4.1)" |
| 2414 | "the headline 6.39pp includes the floor effect by design; §4.1 discloses this" | **REMOVE→(§4.1)** — "the headline range includes the floor effect by design (§4.1)" |
| 2551 | "vectorization produced a 6.39pp marginal accuracy range across 7 vectorizers (95\% CI [6.13, 6.65])" | **KEEP** — conclusion summary |
| 2607 | "Vectorization is the dominant stage (ECG200 marginal range $6.39$pp, 95\% CI [6.13, 6.65] over 25 repetitions..." | **KEEP-REF** — §6.1 decision-tree branch (moves to Ch5 guidance; keep number WITH ref) |
| 2732 | decision-tree summary table "ECG200 6.39pp [6.13, 6.65] $r{=}25$" | **KEEP-REF** — same as 2607 |

**A1 tally:** 17 total → KEEP 3 places (abstract L140 · §4.1 L1072+L1094 · conclusion L2551), plus 5 KEEP-same-section (L1122/1134/1153 + within-§4.1 table) = 8; KEEP-REF 2 (L2607, 2732); TABLE-MOVE 1 (L1754); REMOVE 7 (L196, 267, 1723, 2148, 2362, 2410, 2414).

### A2. 3.22pp / 1.65pp — 16 unique lines (25 mentions) (binary-MNIST stage ranges)

| Line | Verbatim quote (fragment) | Action |
|---|---|---|
| 142–143 | "on binary MNIST it is 3.22pp ($\eta^2 = 0.302$) versus 1.65pp" | **KEEP** — abstract |
| 198 | "the vectorizer range (3.22pp) is twice the filtration range (1.65pp)" | **REMOVE→(§4.1)** — §1.2 preview |
| 273 | "the vectorizer again accounts for most of the accuracy variance (marginal range 3.22pp versus 1.65pp...)" | **REMOVE→(§4.1)** — §1.3; also fix "again" (B9) |
| 1019–1020 | "the vectorizer moves accuracy more than the filtration on this dataset (3.22pp versus 1.65pp)" | **KEEP** — §4.1 MNIST-binary intro (authoritative) |
| 1191 | "gives a vectorizer range of 3.22pp versus a filtration range of 1.65pp" | **KEEP** — §4.1 MNIST marginal analysis (authoritative) |
| 1195 | "vectorizer 2.91--3.22pp vs. filtration 1.49--1.65pp, pooled 3.03pp vs. 1.55pp" | **KEEP-same-section** (§4.1) |
| 1685–1686 | "the marginal range is 3.22pp for vectorizers versus 1.65pp for filtrations (§4.1)" | **REMOVE→(§4.1)** — §5.1 deleted |
| 1736 | "the vectorizer gap is larger (3.22pp)" | **REMOVE→(§4.1)** — §5.1 deleted |
| 1755 | Table 5.1 row "Images (binary MNIST) & Vectorizer & 3.22pp vs.~1.65pp" | **TABLE-MOVE** — with Table 5.1 → new §4.3 |
| 1763–1764 | Table 5.1 footnote "the vectorizer range (3.22pp) exceeds the filtration range (1.65pp)" | **TABLE-MOVE** — with Table 5.1 |
| 2148 | "headline $6.39$pp (ECG200) / $3.22$pp (MNIST) ranges" | **REMOVE→(§4.1)** — as A1 L2148 |
| 2557 | "vectorizer range 3.22pp versus filtration 1.65pp, with cubical beating Vietoris-Rips by $\sim$1.75pp" | **KEEP** — conclusion |
| 2623 | "MNIST binary $3.22$pp vs. filtration $1.65$pp, single split; pooled ... $3.03$pp vs. $1.55$pp" | **KEEP-REF** — §6.1 branch 1b |
| 2733 | decision-tree table "MNIST 3.22 vs. 1.65pp; 98.0 vs. 96.25\% (§4.1)" | **KEEP-REF** |

**A2 tally:** 16 lines → KEEP 3 places (abstract · §4.1 L1019-1020+L1191 · conclusion L2557) + 1 KEEP-same-section (L1195); KEEP-REF 2 (L2623, 2733); TABLE-MOVE 2 (L1755, 1763-1764); REMOVE 6 (L198, 273, 1685-1686, 1736, 2148).

### A3. 24.89pp — 13 occurrences (ECG5000 single-split vectorizer range)

| Line | Verbatim quote (fragment) | Action |
|---|---|---|
| 144 | "ECG5000 shows the menu dependence directly: 24.89pp versus 3.60pp on the raw single-split menu" | **KEEP** — abstract |
| 276 | "a second time-series dataset (ECG5000) shows the raw-menu replication (24.89pp versus 3.60pp, §4.1)" | **REMOVE→(§4.1)** — §1.3 (already carries the ref; delete the numerals) |
| 1122 | "the 6.39pp (ECG200) and 24.89pp (ECG5000) vectorizer ranges are an artefact" | **KEEP-same-section** (§4.1 equal-footing) |
| 1135 | "the 24.89pp range collapses to 0.24pp" | **KEEP-same-section** (§4.1 equal-footing — the 0.24pp collapse is a RESULT here, not backtracking) |
| 1153 | "the published 6.39pp and 24.89pp numbers are substantially inflated" | **KEEP-same-section** (strip "published") |
| 1365 | "replicates the hierarchy: vectorizer marginal range 24.89pp versus filtration 3.60pp (plain accuracy, point estimate, single split)" | **KEEP** — §4.1 ECG5000 probe (authoritative single-split datum) |
| 1724 | "24.89pp versus 3.60pp on ECG5000. These full-range figures are prior to the equal-footing re-analysis" | **REMOVE→(§4.1)** — §5.1 deleted |
| 1754 | Table 5.1 "Time series (embedded) & Vectorizer & 6.39pp; 24.89pp" | **TABLE-MOVE** |
| 2246 | "the single-split $24.89$pp range collapsed to $0.24$pp under level matching (§4.1)" | **REMOVE** — §5.3.2 old-protocol story (see B15); final protocol = 4.30pp |
| 2362 | §5.4 guideline row "(6.39pp on ECG200; 24.89pp on ECG5000)" | **REMOVE→(§4.1)** |
| 2560 | "a second time-series dataset (ECG5000) shows the raw-menu ordering again (24.89pp versus 3.60pp, single split, 3-vectorizer menu; §4.1)" | **KEEP** — conclusion (fix "again" → "reproduces", B9) |
| 2608 | "$24.89$pp single split (§4.1, Table \ref{tab:stage_impact})" | **KEEP-REF** — §6.1 branch 1a; NOTE: drop the "Table tab:stage_impact" pointer — Table 4.1 is ECG200-only (plan correction E7) |
| 2732 | decision-tree table "ECG5000 24.89pp single split (§4.1) and 4.30pp [4.02, 4.57] $r{=}25$ (§5.3)" | **KEEP-REF** (re-point §5.3 → new §4.1) |

**A3 tally:** 13 → KEEP 3 (abstract · §4.1 L1365 · conclusion L2560) + 3 KEEP-same-section (L1122/1135/1153); KEEP-REF 2 (L2608, 2732); TABLE-MOVE 1; REMOVE 4 (L276, 1724, 2246, 2362).

### A4. 3.60pp — 8 occurrences (ECG5000 filtration range, single split)

| Line | Verbatim quote | Action |
|---|---|---|
| 145 | "3.60pp on the raw single-split menu, but 4.30pp versus 0.96pp with disjoint CIs under 25-repetition repeated CV" | **KEEP** — abstract |
| 276 | "replication (24.89pp versus 3.60pp, §4.1)" | **REMOVE→(§4.1)** — §1.3 |
| 1142 | "falls below the filtration range (3.60pp)" | **KEEP-same-section** (§4.1 equal-footing) |
| 1366 | "filtration 3.60pp (plain accuracy, point estimate, single split)" | **KEEP** — §4.1 probe (authoritative) |
| 1725 | "24.89pp versus 3.60pp on ECG5000" | **REMOVE→(§4.1)** — §5.1 |
| 2362 | §5.4 row "(6.39pp on ECG200; 24.89pp on ECG5000)" | **REMOVE→(§4.1)** (3.60 not stated here; the row keeps 24.89 only — reword covers both) |
| 2560 | "the raw-menu ordering again (24.89pp versus 3.60pp, single split...)" | **KEEP** — conclusion |
| 2732 | (no 3.60 in table row) | — |

**A4 tally:** 8 → KEEP 3 (abstract, §4.1 L1366, conclusion L2560), 1 KEEP-same-section (L1142), REMOVE 3 (L276, 1725, 2362).

### A5. 4.30pp — 7 occurrences (ECG5000 repeated-CV vectorizer range)

| Line | Verbatim quote | Action |
|---|---|---|
| 145 | "but 4.30pp versus 0.96pp with disjoint CIs under 25-repetition repeated CV" | **KEEP** — abstract |
| 277 | "the repeated-CV harmonisation of §5.3 confirms the ordering there (vectorizer 4.30pp versus filtration 0.96pp, disjoint CIs)" | **REMOVE→(new §4.1)** — §1.3 (re-point §5.3 → §4.1) |
| 2242 | "marginal ranges put the vectorizer first at $4.30$~pp (95\% CI [4.02, 4.57])" | **KEEP** — §5.3.2 harmonisation → new §4.1 (authoritative r25 ECG5000 result) |
| 2251 | "the vectorizer again leads, at $3.89$~pp ([3.49, 4.30])" | **KEEP-same-section** (matched-genus CI bound; fix "again" → "leads") |
| 2562 | "the vectorizer dominates again with disjoint CIs (4.30pp versus 0.96pp; §5.3)" | **KEEP** — conclusion (fix "again"; re-point §5.3 → §4.1) |
| 2609 | "$4.30$pp, 95\% CI [4.02, 4.57], vs. filtration $0.96$pp under $r{=}25$ repeated CV (§5.3)" | **KEEP-REF** (re-point → §4.1) |
| 2732 | "4.30pp [4.02, 4.57] $r{=}25$ (§5.3)" | **KEEP-REF** (re-point → §4.1) |

**A5 tally:** 7 → KEEP 3 (abstract, §4.1-new L2242, conclusion L2562), 1 KEEP-same-section (L2251), KEEP-REF 2, REMOVE 1 (L277).

### A6. 0.96pp — 5 occurrences (ECG5000 r25 filtration range)

| Line | Verbatim quote | Action |
|---|---|---|
| 145 | "4.30pp versus 0.96pp with disjoint CIs" | **KEEP** — abstract |
| 278 | "versus filtration 0.96pp, disjoint CIs" | **REMOVE→(new §4.1)** — §1.3 |
| 2244 | "the filtration stage ($0.96$~pp [0.80, 1.13])" | **KEEP** — authoritative (new §4.1) |
| 2562 | "CIs (4.30pp versus 0.96pp; §5.3)" | **KEEP** — conclusion |
| 2609 | "vs. filtration $0.96$pp under $r{=}25$" | **KEEP-REF** |

**A6 tally:** 5 → KEEP 3, KEEP-REF 1, REMOVE 1 (L278).

### A7. 616 / 672 — 9 + 5 occurrences (sweep size)

| Line | Verbatim quote | Action |
|---|---|---|
| 133 | "controlled factorial sweep of 616 configurations (6 dataset instances, 4 filtrations, 7 vectorizers, 4 classifiers; 56 runs failed...)" | **KEEP** — abstract |
| 205 | "672 possible, 616 completed, with the 56 exclusions... as disclosed in the abstract" | **REMOVE→(§3.3)** — §1.2; keep "the factorial sweep (§3.3)" |
| 257–258 | "executed in a 616-configuration factorial sweep (of 672 possible; the 56 exclusions of §1.1)" | **REMOVE→(§3.3)** — §1.3 |
| 961–967 | "The sweep comprises 616 completed configurations from a full factorial of 6 dataset instances ... 672 possible, 56 runs failed" | **KEEP** — Ch4 intro (authoritative protocol statement of the results chapter) |
| 1862 | "The full 616-configuration sweep was executed on a single consumer workstation" | **KEEP** — Compute block → new §4.5 (unique; see C2) |
| 1864 | "Summed wall-clock time across all 616 configurations was 2.0 hours" | **KEEP-same-block** — dedupe to one 616 mention in the Compute block |
| 2492–2494 | "the 56/672 excluded configurations ... (616 finished runs of 672 in expanded_results.db)" | **REMOVE→(§4.1)** — §5.5 internal item 7; reword "the 56 exclusions are counted and disclosed (§4.1)" |
| 2583 | "a modular, YAML-configurable, factory-pattern architecture with normalised SQLite storage executing a 616-configuration factorial sweep" | **KEEP** — conclusion (may drop numeral → "the factorial sweep") |
| 3041 | "The 616-configuration sweep reported in Chapter~4 exercises 4, 7, and 4 of these" | **KEEP** — Appendix D (reference material) |

**A7 tally:** 616: KEEP 5 (abstract, Ch4 intro, Compute×2→1, conclusion, App. D), REMOVE 2 (L205, 257). 672: KEEP 1 (Ch4 intro L966), REMOVE 4 (L205, 258, 2492, 2494) → all "(§4.1)/(§3.3)".

### A8. 99.85% — 6 occurrences (noise robustness headline)

| Line | Verbatim quote | Action |
|---|---|---|
| 150 | "mean accuracy 99.85\% at $\sigma = 0.30$" | **KEEP** — abstract |
| 1517 | "mean accuracy across the 112 sphere/torus configurations at that level remained at 99.85\%" | **KEEP** — §4.2 Noise (authoritative) |
| 2566 | "the combined geometric signal survives $\sigma = 0.30$ additive spatial Gaussian noise at 99.85\% mean accuracy" | **KEEP** — conclusion |
| 2675 | "mean accuracy across the 112 configurations at $\sigma{=}0.30$ is 99.85\% (minimum 98.5\%)" | **KEEP-REF** — §6.1 branch 3 |
| 2735 | decision-tree table "99.85\% mean at $\sigma{=}0.30$ (§4.2)" | **KEEP-REF** |
| 2739 | decision-tree table "99.85\% mean; bottleneck 0.434 $\ll$ 1.82 (§4.2)" | **KEEP-REF** |

**A8 tally:** 6 → KEEP 3, KEEP-REF 3, REMOVE 0.

### A9. 95.83% — 11 occurrences (matched-genus TDA accuracy)

| Line | Verbatim quote | Action |
|---|---|---|
| 151 | "matched-genus TDA 95.83\% versus 48--58\% for norm features" | **KEEP** — abstract |
| 288 | "the TDA pipeline sustains 95.83\% accuracy at $\sigma = 0.30$ noise" | **REMOVE→(§4.2)** — §1.3 contribution 3 |
| 1544 | "the TDA pipeline separates the pair at 99.75\% clean and 95.83\% at $\sigma=0.30$ (minimum 91\%...)" | **KEEP** — §4.2 matched-genus (authoritative) |
| 1549 | "The TDA result (95.83\% at $\sigma=0.30$) shows the topological signal survives" | **KEEP-same-section** (§4.2) |
| 1797 | "while TDA retains 95.83\% at $\sigma=0.30$" | **REMOVE→(§4.2)** — §5.2 limitation (1) |
| 2255 | "reported $95.83$\% at $\sigma{=}0.30$; the two are protocol- and menu-distinct" | **REMOVE→(§4.2)** — §5.3.2 harmonisation parenthetical; keep "(§4.2, single-split, VR/weak-alpha menu)" |
| 2484 | "shows TDA retains 95.83\% where norm features collapse to 48--58\%" | **REMOVE→(§4.2)** — §5.5 internal item 6 |
| 2571 | "the robustness is not an artefact of the norm confound (TDA 95.83\% versus 48--58\% for norm features at $\sigma=0.30$)" | **KEEP** — conclusion (rephrase "not an artefact" → "persists under the norm-confound control", B7) |
| 2644 | "the matched-genus control shows the topological signal survives $\sigma{=}0.30$ (TDA $95.83$\% vs. norm features $48$--$58$\%; §4.2)" | **KEEP-REF** — §6.1 branch 1d |
| 2717 | "TDA retains 95.83\% where norm/scale features fail (48--58\%)" | **KEEP-REF** — §6.1 branch 6 |
| 2742 | decision-tree table "matched-genus 95.83 vs. 48--58\% (§4.2)" | **KEEP-REF** |

**A9 tally:** 11 → KEEP 3 (abstract, §4.2 L1544, conclusion L2571) + 1 KEEP-same-section (L1549); KEEP-REF 3; REMOVE 4 (L288, 1797, 2255, 2484).

### A10. 0.434 — 10 occurrences (measured max bottleneck distance)

| Line | Verbatim quote | Action |
|---|---|---|
| 152 | "measured bottleneck distances (max 0.434) fall well below the corrected bound" | **KEEP** — abstract |
| 293 | "Measured bottleneck distances between clean and noisy diagrams (max $d_B = 0.434$ over 80 cloud/dimension pairs)" | **REMOVE→(§4.2)** — §1.3 contribution 4 |
| 612 | "at $\sigma=0.30$ the maximum is 0.434. The torus $H_1$ diagrams move by $d_B$ on average 0.283" | **REMOVE→(§4.2)** — §2.4: keep the DERIVED bound values (0.91/1.82, L606-607) and theory; measured values are results → "(measured in §4.2)" |
| 771 | "§4.2 confirms that classification survives this perturbation (measured $d_B$: max 0.300 at $\sigma=0.15$, max 0.434 at $\sigma=0.30$)" | **REMOVE→(§4.2)** — §2.6 mapping bullet (already has the ref; delete numerals) |
| 1496 | "max 0.434 at $\sigma{=}0.30$" | **KEEP** — §4.2 (authoritative) |
| 1521 | "the maximum measured bottleneck distance at this level is 0.434, less than a quarter of the corrected bound" | **KEEP-same-section** (§4.2) |
| 1562 | figure caption "measured bottleneck distances (max 0.434 at $\sigma=0.30$ versus the corrected bound $2\sigma\sqrt{2\ln n} \approx 1.82$)" | **KEEP-same-section** (§4.2, fig:noise_curves) |
| 2567 | "measured bottleneck distances (max 0.434 versus the corrected bound $2\sigma\sqrt{2\ln n} \approx 1.82$)" | **KEEP** — conclusion |
| 2677 | "the measured bottleneck distances (maximum 0.434) sit far below the corrected stability bound" | **KEEP-REF** — §6.1 branch 3 |
| 2739 | decision-tree table "bottleneck 0.434 $\ll$ 1.82 (§4.2)" | **KEEP-REF** |

**A10 tally:** 10 → KEEP 3 (abstract, §4.2 L1496, conclusion L2567) + 2 KEEP-same-section (L1521, 1562); KEEP-REF 2; REMOVE 3 (L293, 612, 771).

### A11. 1.82 — 10 occurrences (corrected stability bound; excludes mixed-model 1.82pp at L2300, a different quantity)

| Line | Verbatim quote | Action |
|---|---|---|
| 153 | "($2\sigma\sqrt{2\ln n}\approx 1.82$)" | **KEEP** — abstract |
| 295 | "worst-case bound $d_B \le 2\sigma\sqrt{2\ln n}$ ($\approx 1.82$ at $\sigma = 0.30$, $n = 100$)" | **REMOVE→(§2.4/§4.2)** — §1.3 (bound is derived in §2.4, measured in §4.2) |
| 607 | "$2\,\sigma\sqrt{2\ln 100} \approx 0.91$ at $\sigma = 0.15$ and $\approx 1.82$ at $\sigma = 0.30$" | **KEEP** — §2.4 (theory-derived bound values; home of the formula) |
| 767 | "predicts that $\sigma = 0.15$ noise perturbs diagrams by $\lesssim 0.91$ (and $\sigma=0.30$ by $\lesssim 1.82$)" | **REMOVE→(§4.2)** — §2.6 bullet (theory values may stay; measured part → §4.2) |
| 1497 | "the $2\sigma\sqrt{2\ln n}$ values are $0.91$ and $1.82$ for $n{=}100$" | **KEEP-same-section** (§4.2) |
| 1516 | "At $\sigma = 0.30$ (bound $\lesssim 1.82$)" | **KEEP-same-section** (§4.2) |
| 1563 | caption "the corrected bound $2\sigma\sqrt{2\ln n} \approx 1.82$" | **KEEP-same-section** (§4.2) |
| 2568 | "the corrected bound $2\sigma\sqrt{2\ln n} \approx 1.82$" | **KEEP** — conclusion |
| 2678 | "the corrected stability bound ($2\sigma\sqrt{2\ln n} \approx 1.82$)" | **KEEP-REF** — §6.1 |
| 2739 | "bottleneck 0.434 $\ll$ 1.82 (§4.2)" | **KEEP-REF** |

**A11 tally:** 10 → KEEP 4 (abstract, §2.4 L607, §4.2 L1497, conclusion L2568) + 2 KEEP-same-section (L1516, 1563); KEEP-REF 2; REMOVE 2 (L295, 767).

### A12. "extensible to 7 filtrations / 11 vectorizers" — 4 occurrences

| Line | Verbatim quote | Action |
|---|---|---|
| 154 | "YAML-configurable and extensible to 7 filtrations, 11 vectorizers, and 4 classifiers" | **KEEP** — abstract |
| 207–209 | "The framework is extensible via YAML-only configuration changes to the wider method families of Appendix~D (7 filtrations, 11 vectorizers, and 4 classifiers)" | **REMOVE→(Appendix D)** — §1.2; keep "extensible via YAML-only changes (Appendix D)" |
| 260–262 | "the framework extends to the full method families of Appendix~D (7 filtrations, 11 vectorizers, and 4 classifiers)" | **REMOVE→(Appendix D)** — §1.3 (same reword) |
| 3037–3041 | "The framework supports 7 filtrations (VR, Alpha, Sparse Rips, Čech, Cubical, Weighted Rips, Flagser), 11 vectorizers (PI, PL, Betti, ...)" | **KEEP** — Appendix D (authoritative) |

**A12 tally:** 4 → KEEP 2 (abstract, App. D), REMOVE 2 → "(Appendix D)".

**A-combined verification gate (prose, cross-section):** after execution the cross-section prose counts are: 6.39 ≤ 4 (abstract, §4.1, conclusion, guidance), 3.22/1.65 ≤ 3, 24.89 ≤ 3, 4.30/0.96 ≤ 3, 616 ≤ 4, 99.85 ≤ 3, 95.83 ≤ 4, 0.434 ≤ 3, 1.82 ≤ 4, "extensible" ≤ 1. All 13 headline values preserved exactly (13-key baseline unchanged).

---

## B. BACKTRACKING / SELF-DISCOVERY INVENTORY (line · quote · action)

B1. **L856–888 — FPS ablation framed as correcting a past decision.**
- L878: "We therefore do not find support for the premise underlying the earlier deferral: uniform-random subsampling is not materially inferior to FPS"
- L888: "the earlier FPS-future-work note is withdrawn."
**Action:** REPHRASE as direct finding; DELETE the process clauses. Replacement for L878: "Uniform random subsampling is not materially inferior to farthest-point sampling on these clouds: at $k{=}15$ FPS scores 98.94\% vs uniform 99.81\% at $\sigma{=}0.30$ ($-0.88$\,pp), and uniform wins at $\sigma{=}0$ (100.00\% vs 99.88\%)." L888 → DELETE "and the earlier FPS-future-work note is withdrawn." (keep "The subsampling-method choice is immaterial for the synthetic class").

B2. **L998–1002 — "the paper's headline 83.0% configuration ... ranks fourth"** (Ch4 intro).
Quote: "Finally, the paper's headline 83.0\% configuration (cubical + Silhouette + Random Forest) is a single-split point estimate: by $r{=}5$ repeated-CV mean it ranks fourth (79.6\%, SD 1.98pp), while cubical + Persistence Image + Random Forest is best in 4 of 5 repetitions (83.2\% mean, $r{=}5$; §4.1)."
**Action:** REPHRASE to final-protocol-only: "The repeated-CV-stable best configuration is cubical + Persistence Image + Random Forest (83.2\% mean, $r{=}5$; 82.82\% at $r{=}25$; §4.1). The single-split point estimate for cubical + Silhouette + Random Forest is 83.0\% (Table 4.2)." Delete "the paper's headline", "ranks fourth", the correction narrative. (Same pattern at B3, B4, B13, B14, B22 — consolidate to ONE statement in §4.1.)

B3. **L1340–1345 — "Notably, the paper's best single-split ECG200 configuration ... ranks third by 25-repetition mean (79.30\%, SD 1.57pp), while cubical + Persistence Image + Random Forest is best overall (82.82\% mean, $r{=}25$)."**
**Action:** REPHRASE (this is the authoritative spot): "By 25-repetition mean, cubical + Persistence Image + Random Forest is the best configuration (82.82\%, SD …), and the single-split point estimate for cubical + Silhouette + Random Forest is 83.0\% (Table 4.2), within the $\pm$1–3pp split-to-split noise band. Differences below $\sim$1pp between individual configurations should not be over-interpreted." Drop "Notably," and "the paper's". Delete B2's and B14's repetitions of this correction.

B4. **L1638–1640 — "the originally-reported best configuration (cubical + Silhouette + Random Forest, 83.0\% single-split) ranks fourth by $r{=}5$ repeated-CV mean (79.6\%, SD 1.98pp)"** (§4.3 Pareto).
**Action:** DELETE the correction clause; keep the positive statement: "The repeated-CV-stable default for ECG200 is cubical + Persistence Image + Random Forest (best in 4 of 5 repetitions, $r{=}5$; 83.2\% repeated-CV mean): this is the strongest Pareto row we can defend." (L1635–1637 stays; L1638–1640 deleted.)

B5. **L1150–1156 — "the published 6.39pp and 24.89pp numbers are substantially inflated by degenerate scalar vectorizers"** (§4.1 equal-footing).
**Action:** REPHRASE (keep the result, strip process voice): "the 6.39pp and 24.89pp ranges are substantially inflated by degenerate scalar vectorizers; once those are excluded and the stage counts are matched the vectorizer-vs-filtration gap narrows substantially (ECG200) or reverses (MNIST, ECG5000)."

B6. **L1192–1193 — "The ordering is not a single-split artifact: repeated 5-fold CV (5 repetitions, seeds 43--47) reproduces the ordering in all five repetitions"** (§4.1 MNIST).
**Action:** REPHRASE positive: "The ordering persists under repeated 5-fold CV (5 repetitions, seeds 43–47): it is reproduced in all five repetitions (vectorizer 2.91–3.22pp vs filtration 1.49–1.65pp, pooled 3.03pp vs 1.55pp)."

B7. **L2078–2081 — "Vectorization-dominance is therefore not an artefact of the decorative-topology regime: it persists where topology genuinely carries the classification signal"** (§5.3.1 topology-wins).
**Action:** REPHRASE positive (per plan): "The ordering persists in the topology-wins regime: where topology genuinely carries the classification signal, the vectorizer remains the dominant stage, and the filtration stage's contribution grows modestly (1.04–5.10pp) rather than reversing the ordering."

B8. **L2134–2138 — "Vectorizer dominance is therefore not a default-settings artefact: the $\approx 5$–$6$pp ECG200 vectorizer spread survives each vectorizer being tuned, and tuning neither creates nor destroys the small ($\lesssim 2$pp) MNIST spread."** (§5.3.2 hyperparameters).
**Action:** REPHRASE per plan: "The ordering is insensitive to per-vectorizer tuning: the ECG200 vectorizer spread survives tuning (5.75→4.75pp), and tuning neither creates nor destroys the small ($\lesssim 2$pp) MNIST spread."

B9. **"again" — 5 occurrences:**
- L272 "On binary MNIST the vectorizer again accounts for most of the accuracy variance" → "the vectorizer accounts for most of the accuracy variance".
- L1205 "on MNIST the vectorizer again leads (0.302)" → "the vectorizer leads (0.302)".
- L2250 "On the matched-genus control the vectorizer again leads, at $3.89$~pp" → "the vectorizer leads, at $3.89$~pp".
- L2559 "shows the raw-menu ordering again (24.89pp versus 3.60pp...)" → "reproduces the raw-menu ordering".
- L2561 "the vectorizer dominates again with disjoint CIs (4.30pp versus 0.96pp; §5.3)" → "the vectorizer dominates with disjoint CIs".
**Action:** all REPHRASE as above ("again" → none/leads/reproduces).

B10. **L1705–1706 — "'filtration barely matters' is partly an artefact of that menu"** (§5.1 diverse-filtration check).
**Action:** KEEP content (it is a conditionality FINDING, not backtracking) but soften scare quotes in the move to §4.2: "the empirical filtration range is sensitive to the filtration menu: adding the DTM-weighted Rips raises the ECG200 filtration marginal range to 2.81pp...". The phrase "partly an artefact of that menu" is retained as a finding about menu composition.

B11. **L1725–1729 — "These full-range figures are prior to the equal-footing re-analysis of §4.1, which shows they are substantially inflated..."** (§5.1).
**Action:** REPHRASE (section deleted; content to §4.1): "The full-range figures are inflated by the degenerate scalar vectorizers (Amplitude, Persistence Entropy): excluding them reduces the ECG200 vectorizer range to 3.10pp and the ECG5000 range to 0.24pp (§4.1)."

B12. **L2176–2177 & L2197–2198 — "The guideline row for large-scale clouds rested on the untested premise that Sparse Rips becomes advantageous at $n \ge 10^3$" / "The guideline row for large-scale clouds is revised accordingly"** (§5.3.2 Sparse Rips).
**Action:** REPHRASE as direct result (→ new §4.5): "At its design scale Sparse Rips does not pay off in giotto-tda 0.6.2: at $n{=}1000$ it matches Vietoris–Rips accuracy (100.00\%, 8/8) at $\approx 30\times$ the cost (1.83h vs 3.6min per configuration), and at $n{=}3000$ it did not complete within 42h. Vietoris–Rips remains the pragmatic choice up to the largest feasible $n$; Sparse Rips requires an implementation-level benchmark at the target $n$ (a portability finding in its own right)." Delete both "guideline row ... untested premise / revised accordingly" clauses.

B13. **L1467, L2702–2703 — "83.0\% (single-split point estimate) versus 85.28\%... " / "83.0\% single-split best TDA, whose repeated-CV mean is 79.6\%".**
**Action:** KEEP the numbers (baselines comparison is a result, §4.1.1, and guidance); DELETE the "whose repeated-CV mean is 79.6\%" correction in guidance (L2703) → "83.0\% single-split best TDA (§4.1)". Keep L1467 as-is (it is a raw-vs-TDA comparison, not a correction narrative).

B14. **L2416–2431 — §5.5 construct item 3 ("Single-split point estimates are noisy ... the headline 83.0\% configuration drops to 79.6\% at $r{=}5$ (rank 4 of 84) ... single-split numbers are labelled as such throughout ... ECG5000 and the panel are now harmonised to the $r{=}25$ protocol of §5.3, closing this residual.").**
**Action:** reframe to boundary-condition statement: "Boundary: single-split point estimates carry $\pm$1–3pp split-to-split noise (per-configuration SD 1.09pp, max 3.11pp; 50 of 112 configurations exceed 1pp); headline claims rest on the $r{=}25$ protocol (§4.1). ECG5000, the matched-genus control, and the panel follow the same $r{=}25$ protocol (§4.1)." Delete "drops to ... rank 4 of 84", "now harmonised ... closing this residual".

B15. **L2231–2249 — §5.3.2 "Repeated-CV harmonisation" (the core backtracking passage).**
- L2231–2234: "The headline ECG200 analysis used 25 cross-validation repetitions, while ECG5000, the matched-genus control, and the panel were single-split. To bring every supporting claim to the same protocol, the three were re-run with 25 repetitions (5-fold, seeds 43--67; ...)" 
- L2245–2249: "This resolves the earlier menu-dependence concern for this dataset: the single-split $24.89$pp range collapsed to $0.24$pp under level matching (§4.1), but under the fixed panel grid and repeated CV the vectorizer dominates with disjoint confidence intervals; the magnitude depends on the menu, the ordering does not."
**Action:** DELETE L2245–2247's process sentence; REPHRASE L2231–2234 to final-protocol: "ECG5000, the matched-genus control, and the panel were evaluated under the same 25-repetition protocol (5-fold, seeds 43–67; fixed panel grid: Vietoris–Rips and DTM-weighted Rips × three vectorizers × two classifiers; 1,500 runs)." KEEP the final-protocol result sentence: "the vectorizer dominates with disjoint confidence intervals (ECG5000: 4.30pp [4.02, 4.57] vs filtration 0.96pp [0.80, 1.13]); the magnitude depends on the menu, the ordering does not." (The 0.24pp collapse survives only as the §4.1 equal-footing result, L1135.)

B16. **L2250–2257 — "On the matched-genus control the vectorizer again leads ... (the single-split §4.2 experiment used a different menu --- VR/weak-alpha --- and reported $95.83$\% at $\sigma{=}0.30$; the two are protocol- and menu-distinct, and the r25 numbers are the fixed-grid estimate)."**
**Action:** fix "again" (B9); compress parenthetical to "(the single-split matched-genus analysis of §4.2 used a different menu, VR/weak-alpha; 95.83\% at $\sigma{=}0.30$)". Keep both protocols' numbers (they are menu-distinct results; 13-key baseline preserved).

B17. **L2299–2300 — "The older-sweep robustness pass reproduces the ordering (classifier $1.82$ $>$ vectorizer $1.48$ $>$ filtration $1.24$\,pp; ICC $0.929$)."**
**Action:** REPHRASE: "A robustness refit reproduces the population ordering (classifier 1.82 > vectorizer 1.48 > filtration 1.24pp; ICC 0.929)."

B18. **L2306–2312 — "A sensitivity refit excluding SVM-RBF (whose majority-class collapse is diagnosed in §5.2) reverses the population ordering: ... The population-level reversal is therefore driven by the SVM-RBF collapse, confirming the diagnosis rather than contradicting the within-dataset headline."**
**Action:** REPHRASE: "Excluding SVM-RBF (majority-class collapse, §4.1) reverses the population ordering: vectorizer (1.55pp [0.86, 2.49]) leads filtration (1.29pp [0.24, 2.93]), the classifier effect vanishing by construction (ICC 0.948). The reversal is driven by the SVM-RBF collapse." DELETE "confirming the diagnosis rather than contradicting the within-dataset headline". Fix cross-ref §5.2 → §4.1 (the collapse diagnosis is at L1387–1389 and L2100–2102; §5.2 is the limitations chapter — current ref is wrong, E7).

B19. **L2317–2319 — "the manuscript's limitations note that the torus's second homology is then unmeasured."**
**Action:** REPHRASE: "the $H_1$ cap leaves the torus's second homology unmeasured." (drop "the manuscript's").

B20. **L2227 — "the previously documented filtration fragility (weak-alpha on quantized series)"**
**Action:** REPHRASE: "the filtration fragility (weak-alpha on quantized series) is the library-dependence that matters, not the accuracy outcomes."

B21. **L710, L721–723, L734 — §2.5 vectorization results-touches:** L710 "Silhouette is the top-performing vectorizer on ECG200 in the single-split marginal (§4.1)"; L721–723 "On ECG200 it is among the weaker representations (§4.1), an early hint that representation capacity is dataset-dependent"; L734 "Entropy is the weakest vectorizer on ECG200 (single-split marginal 69.3\%, §4.1)".
**Action:** strip result numerals from §2.5 (keep qualitative + ref): L710 → "Silhouette is the top-performing vectorizer on ECG200 (§4.1)"; L721–723 → "…among the weaker representations (§4.1)"; L734 → "Entropy is the weakest vectorizer on ECG200 (§4.1)". Delete "an early hint that" (self-discovery).

B22. **L1635–1637 — "The repeated-CV-stable default for ECG200 is cubical + Persistence Image + Random Forest (best in 4 of 5 repetitions, $r{=}5$; 83.2\% repeated-CV mean): this is the strongest Pareto row we can defend"** (§4.3).
**Action:** KEEP (positive final-protocol statement; home of the 83.2\% figure) — after B4 removes the contrast.

B23. **L2012 — "consistent with the population-level mixed model below and with the conditionality thesis of Chapter~6"** (§5.3.1 diverse panel).
**Action:** KEEP; re-point to new §4.4 and Ch6 after restructure.

B24. **§5.5 Threats — "Mitigation (done)" process language, 12 instances:** L2392, L2408, L2422, L2434–2435, L2454, L2458, L2465, L2478, L2482–2483, L2513, L2522, and L2529 "Mitigation:".
**Action:** REPHRASE every "\emph{Mitigation (done):}" → "\emph{Boundary:}" (or "\emph{Addressed by:}") and rewrite in result tense with the analysis named: e.g. L2392 → "Boundary: the $\omega^2$ population effect size corrects for level counts (ECG200 vectorizer $\omega^2{=}0.165$, bootstrap CI [0.063, 0.423], vs filtration $-0.017$; §4.1); the equal-footing analysis matches best-3 vectorizers against 3 filtrations (ECG200 1.21pp vs 0.69pp; §4.1)." L2529 → "Boundary: per-configuration wall times and peak memory are stored in the results DBs; peak memory was not measured per stage." Also L2429–2431 "now harmonised … closing this residual" (see B14). The section header "Threats to Validity" → "Boundary Conditions" (or keep three validity buckets retitled as conditions). L2374–2379 intro ("We structure the limitations of §5.2 into the three standard validity categories…") must be rewritten once §5.2 merges (see C2).

B25. **L2499–2501 — "Residual: five interrupted runs in repeated_cv_r25.db ... were re-run under new run IDs; the orphaned rows carry no fold results and do not enter any analysis."**
**Action:** KEEP as a data-quality disclosure (not self-discovery); keep under "Boundary/Disclosure".

B26. **L1769–1771 — "This table summarises initial evidence, not a settled taxonomy. Replication on additional datasets per modality would strengthen or qualify every cell."**
**Action:** KEEP (honest scoping); drop "initial" → "This table summarises the evidence, not a settled taxonomy." (minor).

B27. **L2105–2107 — "the paper's scoped claim stands"** → REPHRASE "the scoped claim stands". L989 "we therefore do \emph{not} claim that TDA features are competitive" → KEEP (scoping statement, not backtracking). L1240–1243 "We therefore read the binary-MNIST result ... as a binary-scale phenomenon" → REPHRASE "The binary-MNIST ordering is a binary-scale phenomenon: at 10-class scale, filtration becomes the larger marginal stage." L1325–1328 "We therefore read the stage-dominance claim as \emph{dominance in main effect}" → REPHRASE "The stage-dominance claim is therefore a claim of dominance in main effect, with the interaction structure an explicit boundary condition on that claim."

B28. **"surprisingly" / "initially" / "at first" — 0 occurrences in the text.** Plan principle 3 lists them; no action needed (verified absent).

B29. **L992–996 — "Note also that ECG200 is energy-normalised ... so the trivial-separator concern that would attach to an un-normalised signal does not apply"** → KEEP (analysis point; also disclosed at L2495–2498; keep ONE — recommend the §5.5 internal item 7 version, drop the Ch4-intro duplicate or vice versa; see C2).

B30. **L1361–1362 — "the filtration range is computed on non-matching vectorizer menus"; L1552–1555 "the comparison is single-split, seed 43, 12 configurations"; L1602–1603 footnote "Times are single-split measurements; the 83.0\% ECG200 figure is a single-split point estimate --- see §4.1 for repeated-CV means."; L1446 footnote "TDA best rows are single-split point estimates."** → **KEEP** all four (protocol labels on tables/results, final-protocol factual disclosure; the "single-split ≤ 3" gate in the plan must exclude table footnotes — E4).

---

## C. MERGE OPERATIONS — verification and exact ranges

### C1. §5.1 "Why Vectorization Dominates on Both Datasets" (L1656–1773, header → line before §5.2 header)

**Confirmation of duplication vs §4.1:**
- L1659–1662 (dominance claim) ↔ L1094–1096, L1210–1212 — duplicate.
- L1675–1682 (cubical 1.75pp; Conti 18–94\%) ↔ L1017, L1022–1025 — duplicate.
- L1684–1689 (3.22 vs 1.65) ↔ L1191–1200 — duplicate.
- L1721–1729 (6.39/0.69, 24.89/3.60, equal-footing 3.10/0.24) ↔ L1094–1096, L1122–1156 — duplicate.
- L1731–1737 (Conti complementary; binary vs 10-class) ↔ L1236–1243 — duplicate.
- L1738–1743 (weak-alpha/nerve-theorem parenthetical) ↔ §2.2 remark L401–414 and §4.3 L1616–1627 — triplicate.

**UNIQUE content in §5.1 (must be preserved):**
1. Image-data mechanism narrative (L1664–1674): cubical captures grid adjacency; VR applied to MNIST sees 28 rows as a 28-point cloud in R²⁸ and does not see grid adjacency. → move to **end of new §4.1** (interpretive close of the MNIST marginal analysis).
2. Time-series mechanism narrative (L1691–1700): "The embedding captures the dynamical structure; the filtration merely reads it out." (VR vs full Alpha interleaved, bounded bottleneck.) → move to **end of new §4.1** (interpretive close of ECG200 analysis).
3. Diverse-filtration (DTM) check (L1702–1719): DTM-weighted Rips raises ECG200 filtration range to 2.81pp, DTM best (76.2\% vs 73.4\%), vectorizer still largest (5.62pp); 48-config sweep. → move to **new §4.2 Robustness** (this is the "diverse filtrations" item in the plan's §4.2 brief).
4. Table 5.1 "Stage importance by data modality" (L1745–1767) + its caveat (L1769–1771). → move to **new §4.3 Generalisation and conditions** (modality-conditional summary); optionally add a 10-class row (filtration 4.53pp) so the table matches the conditionality thesis. Footnote (L1760–1766) stays with table.
5. Conti complementarity sentence (L1677–1682) → already covered in §4.1 (L1022–1025, L1237–1243); DELETE from §5.1.

**Action:** delete §5.1 shell; distribute the 5 items above; everything else is a duplicate of §4.1 and is dropped with a §4.1 cross-ref. Net unique content ≈ 70 lines.

### C2. §5.2 "Non-Topological Context and Limitations" (L1774–1875) + §5.5 "Threats to Validity" (L2371–2540, incl. 5.5.1 L2381–2441, 5.5.2 L2442–2502, 5.5.3 L2504–2539)

**Overlap map (§5.2 limitation → §5.5 threat):**
| §5.2 item (lines) | §5.5 counterpart (lines) | Verdict |
|---|---|---|
| Baselines/scope (L1777–1788) | §4.1.1 (L1465–1480); §5.5 ext-4 (L2537–2538) | triplicate → keep §4.1.1 + one scoping sentence in Ch5 |
| (1) norm confound (L1790–1799) | int-6 (L2481–2489) | duplicate; §5.5 version has the numbers — keep §5.5, delete §5.2 (1) |
| (1a) linear-separability caveat (L1799–1804) | int-6 residual (L2486–2489) | duplicate → keep §5.5 residual |
| (2) H1 cap (L1804–1805) | int-2 (L2456–2459) | duplicate → keep §5.5 |
| (3) binary-only (L1805–1807) | int-3 (L2460–2466) | duplicate → keep §5.5 |
| (4) small evidence base (L1807–1810) | ext-1 (L2511–2519) | duplicate → keep §5.5 |
| (5) single library (L1811–1812) | int-1 (L2449–2455) | duplicate → keep §5.5 |
| (6) no learned vectorizers (L1812–1813) | ext-4 (L2532–2538) | duplicate → keep §5.5 |
| (7) n=200 wide CIs (L1813–1815) | con-3 (L2416–2431) | duplicate → keep §5.5 |
| future-work list (L1816–1822): Flood/H2, Outex, second UCR family, cross-library, PersLay, larger-n | ext-4 "each names a clear follow-up" (L2534–2535) | **UNIQUE detail** (named concrete items) → fold into merged Ch5 as "Future work" paragraph |
| Availability block (L1824–1860) | none | **UNIQUE — preserve verbatim** → new **§3.4 "Reproducibility and Availability"** (fits plan's Ch3 title "Framework and Reproducibility") |
| Compute block (L1862–1873) | none | **UNIQUE — preserve** → **new §4.5 Computational costs** (616-config 2.0h, Sparse Rips ≈1.6h, 2100 r25 runs, memory caveat) |
| Energy-normalisation note (L992–996) | int-7 (L2495–2498) | duplicate → keep §5.5 int-7 only |

**Proposed merged Ch5 outline ("Conditions, Limitations, and Operational Guidance"):**
1. §5.1 Scope and contribution (one paragraph from §5.2 L1777–1788: TDA below raw baselines; contribution is the internal stage comparison; TDA features complement raw features).
2. §5.2 Boundary conditions — keep the three validity buckets as subsubsections, retitled "Measurement conditions" (5.5.1), "Design conditions" (5.5.2), "Generalisation conditions" (5.5.3); every "Mitigation (done)" → "Boundary:" (B24); every process clause deleted; add the §5.2 future-work paragraph (L1816–1822) as "§5.2.4 Future work".
3. §5.3 Operational guidance — merged §5.4 table + §6.1 decision tree (see C3).
4. Availability moves to Ch3 §3.4; Compute moves to Ch4 §4.5 (both UNIQUE, preserved).

### C3. §5.4 "Operational Guidelines for Pipeline Selection" (L2342–2370) + §6.1 "A Decision Tree for Practitioners" (L2589–2745)

**Overlap map:** §5.4 Table 5.4 rows ↔ §6.1 branches:
- "Low-dim point clouds (≤3D, clean) — Weak Alpha, Statistics/Landscapes, SVM/Logistic" (L2361) ↔ branch 1d (L2636–2645) + budget branch 2b (L2660–2665). Unique facts in L2361: Weak Alpha 3–27\% faster than VR at identical accuracy; full-complex fidelity verified empirically (0.0–0.8pp at 2–5× cost).
- "Delay-embedded time series — VR or Weak Alpha, Betti Curves (or Landscapes), RF/SVM" (L2362) ↔ branch 1a (L2604–2621). **UNIQUE fact in L2362:** "Betti is 5th of 7 vectorizers on the r25 ECG200 marginal (72.38\%), so Landscapes/Statistics are competitive" — the 72.38\% figure appears ONLY here; must be preserved.
- "High-noise clouds (σ ≥ 0.15) — Weak Alpha or VR, Betti Curves, SVM(RBF)" (L2363) ↔ branch 3 (L2672–2682). **UNIQUE fact in L2363:** "the confound-controlled matched-genus floor is 91\%".
- "Large-scale clouds (n ≥ 10³) — VR, Images or Betti, RF" (L2364) ↔ branch 2a (L2651–2659). Duplicate; keep §6.1 version.
- SVM-RBF collapse warning (L2362, L2668) ↔ branch 2c (L2666–2669). Duplicate; keep §6.1.

**Proposed merged guidance section (Ch5 §5.3):**
1. Scoping sentence (L2345–2347, kept).
2. Decision tree (from §6.1, L2592–2721): rubric A/B/C + 6 branches, verbatim with re-pointed refs.
3. Evidence-grade summary table (Table 6.1, L2723–2745), verbatim with re-pointed refs.
4. Compact configuration table (Table 5.4, L2350–2367) kept as the "cheat sheet", with the two unique facts (72.38\% note; 91\% matched-genus floor) folded into its rationale column (they are already there — preserve the table as-is).
5. §6.1's "grade" language stays; delete the duplicated §6.1-vs-§5.4 rows from the decision tree where Table 5.4 covers them, or keep both (tables are reference material; the plan's no-duplication principle applies to prose).

**Ch6 after merge:** Conclusion only (L2547–2586 content minus §6.1). Ch6 currently opens with a full results recap (L2550–2576) — per plan keep as the conclusion summary (each number once, KEEP classification above), then the conditionality thesis (L2578–2586) as the final paragraph. Retitle chapter "Conclusion".

### C4. §5.3.1–5.3.3 block mapping (block = header line → line before next header)

**§5.3 intro + Table 5.2 (L1876–1926)** → **new §4.3 intro** (panel description + table).

**§5.3.1 Generalisation (L1927–2108):**
| Block | Lines | Destination |
|---|---|---|
| Weak-alpha fragility finding | L1929–1938 | **new §4.3** (panel portability result) |
| Fig. 5.1 nemenyi CD + Friedman/Nemenyi text | L1940–1971 | **new §4.3** (canonical Demsar protocol) |
| Panel with a diverse filtration set | L1973–2019 | **new §4.2** (diverse filtrations; level-matched 2-vs-2, 2.4×→0.93×) |
| Multi-patient ECG (MIT-BIH) | L2021–2049 | **new §4.3** |
| The topology-wins regime | L2051–2081 | **new §4.3** |
| TDA and raw features are complementary (concat) | L2083–2107 | **new §4.2** (concat) |

**§5.3.2 Robustness (L2109–2265):**
| Block | Lines | Destination |
|---|---|---|
| Hyperparameter sensitivity | L2111–2152 | **new §4.2** |
| Window-length sensitivity (MIT-BIH 256-window) | L2154–2170 | **new §4.2** (alternative: keep beside MIT-BIH in §4.3) |
| Sparse Rips at its design point | L2175–2203 | **new §4.5** (computational cost result; contains runtime data) |
| Cross-library replication | L2205–2229 | **new §4.2** |
| Repeated-CV harmonisation | L2231–2264 | **new §4.1** (ECG5000 4.30/0.96 + matched-genus r25 + panel note are stage-variance results; narrative stripped per B15) |

**§5.3.3 Mechanism (L2266–2340):**
| Block | Lines | Destination |
|---|---|---|
| Predictive theory (null) | L2268–2286 | **new §4.4** |
| Hierarchical stage model (mixed model) | L2288–2314 | **new §4.4** |
| Second homology via true Alpha | L2316–2340 | **new §4.4** |

### C5. Chapter 5 title — does "Vectorization Dominance and Theoretical Synthesis" overclaim?

**Yes, it overclaims on both counts:**
1. "Vectorization Dominance" — contradicted by the paper's own settled findings: the equal-footing analysis (L1150–1156: "the vectorizer-vs-filtration gap narrows substantially (ECG200) or reverses (MNIST, ECG5000)"); the 10-class inversion (L1240–1243: "at 10-class scale, filtration becomes the larger marginal stage"); the mixed model (L2313–2314: "'Vectorization dominates' is a within-dataset-range statement, not a population-level one"); and the abstract's own thesis (L135–136: "the stage ordering is robust while its magnitude is menu-dependent"). The chapter title states the magnitude claim the paper explicitly rejects.
2. "Theoretical Synthesis" — the theory test produced a NULL (L2282–2285: "We therefore report a null: the theory did not predict the sweep"), so "synthesis" overstates.

**Proposed title:** "Boundary Conditions and Operational Guidance" (or "Generalisation, Limitations, and Guidance" per plan). Consistent with the conditionality thesis (L2578–2586) and with the target Ch5 content (conditions + limitations + decision tree). Also fix the §5.1 opening line (L1659–1660: "The central empirical result is that vectorization is the dominant pipeline stage on both real datasets") → "The central empirical result is that the vectorizer is the dominant stage on both binary datasets, while the magnitude of the gap is menu-dependent and the ordering is conditional on scale and modality (§4.1, §4.3)."

---

## D. CROSS-REFERENCE INSERTION LIST (every REMOVE site → ref to insert)

All refs use CURRENT numbering for locating; the parenthetical gives the TARGET ref after renumbering.

| REMOVE site (line) | Replace numerals with |
|---|---|
| L196 (§1.2) | "(§4.1)" |
| L198 (§1.2) | "(§4.1)" |
| L205 (§1.2, 616/672) | "the factorial sweep (§3.3)" |
| L207–209 (§1.2, extensible) | "(Appendix D)" |
| L257–258 (§1.3, 616/672) | "the factorial sweep (§3.3)" |
| L260–262 (§1.3, extensible) | "(Appendix D)" |
| L267 (§1.3, 6.39) | "(§4.1)" |
| L272–274 (§1.3, 3.22/1.65) | "(§4.1)" |
| L276–278 (§1.3, 24.89/3.60/4.30/0.96) | "(§4.1)" (re-point §5.3 → §4.1) |
| L288 (§1.3, 95.83) | "(§4.2)" |
| L293–295 (§1.3, 0.434/1.82) | "(§2.4; §4.2)" |
| L612 (§2.4, measured d_B) | "(measured in §4.2)" — keep derived 0.91/1.82 |
| L710/721–723/734 (§2.5) | "(§4.1)" — drop 69.3\% and "early hint" |
| L767–771 (§2.6) | "(§4.2)" |
| L1004–1010 (Ch4 intro cubical robustness) | merge into §4.2 block with L1403–1410; ref "(§4.2)" |
| L1135 (§4.1 equal-footing 0.24) | KEEP (result) |
| L1467 (§4.1.1) | KEEP (baseline comparison) |
| L1638–1640 (§4.3, 79.6/83.0 correction) | delete; ref "(§4.1)" for repeated-CV means |
| L1723–1729 (§5.1) | "(§4.1)" |
| L1754/1755/1763–1764 (Table 5.1) | table moves to §4.3; numbers stay in table |
| L1797 (§5.2 lim 1) | "(§4.2)" |
| L1862–1873 (Compute) | moves to §4.5; no ref needed |
| L2148 (§5.3.2) | "(§4.1)" |
| L2246–2247 (§5.3.2 old-protocol) | delete; final protocol "(§4.1)" |
| L2255 (§5.3.2 parenthetical) | "(§4.2)" |
| L2362–2364 (§5.4 table) | "(§4.1)"/"(§4.5)" per row |
| L2410/2414 (§5.5) | "(§4.1)" |
| L2484 (§5.5 int-6) | "(§4.2)" |
| L2492–2494 (§5.5 int-7, 616/672) | "(§4.1)"/"(§3.3)" |
| L2562/2560 (conclusion, §5.3 ref) | re-point "§5.3" → "§4.1" |
| L2607–2609 (§6.1, keep numbers) | keep numbers + "(§4.1)"; fix "Table \ref{tab:stage_impact}" pointer (E7) |
| L2634 (§6.1, 10-class ref) | fix "(§4.2)" → "(§4.1)" → target "(§4.3)" |
| L2732–2742 (Table 6.1 refs) | re-point: §5.3→§4.1/§4.2, §5.3.1→§4.3, §5.2→§4.2, §5.3.2→§4.2, §5.3.3→§4.4 |

**Existing cross-ref re-pointing map (after restructure):** L2455 "§5.3.2"→§4.2 · L2459 "§5.3.3"→§4.4 · L2465 "(§4.2)"→§4.1 (10-class flip lives at L1223) · L2518 "§5.3.1"→§4.3 · L2523 "§5.3.1"→§4.3 · L2664 "§5.3"→§4.3 · L2668 "§5.2"→§4.2 (concat analysis is §5.3.1 L2083–2107; §5.2 is limitations — current ref WRONG) · L2307 "§5.2"→§4.1 (SVM-RBF collapse diagnosed at L1387–1389, L2100–2102) · L1969 "(§5.3)" self-ref→§4.3 · L2741 "§5.2"→§4.2 · L2742 "§5.3.1"→§4.3 · L2608 "Table \ref{tab:stage_impact}" for ECG5000 24.89pp → wrong table (Table 4.1 is ECG200-only); re-point to "(§4.1)".

---

## E. CORRECTIONS TO RESTRUCTURE_PLAN.md

E1. **§5.1 disposition is wrong as "DELETE — unique insights folded into §4.1/§4.4".** The DTM diverse-filtration check (L1702–1719) is a robustness-of-ordering result → **§4.2**, not §4.1/§4.4; Table 5.1 → **§4.3**; mechanism narratives → §4.1 close; weak-alpha parenthetical (L1738–1743) → DELETE (triplicate of §2.2 remark and §4.3). §5.1 is *dismantled*, not deleted wholesale.

E2. **"not an artefact of | 2" is wrong — there are 4 instances:** L2078 (topology-wins), L2134 (default-settings), L2571 (norm confound), plus L1193 "not a single-split artifact" (US spelling). All four get the positive rephrase (B6–B8, B7-conclusion).

E3. **"extensible to 7/11/4 | 3" is wrong — 4 instances** (L154 abstract, L207–209 §1.2, L260–262 §1.3, L3037–3041 App. D). Keep 2 (abstract + App. D); remove 2 → "(Appendix D)". Appendix-D repetition is explicitly fine per plan principle 6.

E4. **Verification gate "single-split ≤ 3" and "6.39 ≤ 4" are infeasible as worded.** Single-split must survive in ≥4 places that are NOT backtracking: §3.3 protocol note (L940–941), Table 4.4 footnote (L1446), Table 4.2 footnote (L1602–1603), ECG5000 probe label (L1366), matched-genus protocol note (L1555), threats con-3 (L2429). Recommend: gate counts backtracking usage only; table-footnote and protocol-label uses are excluded (like appendix repetition). 6.39 has 8 legitimate occurrences in §4.1 alone (Table 4.1 + prose + equal-footing mentions); the gate should be per-section (≤1 section outside abstract/conclusion/guidance), not a global occurrence count.

E5. **"24.89pp | keep ~2" → keep 3** (abstract L144, §4.1 probe L1365, conclusion L2560) + 2 guidance citations, consistent with principle 1 ("abstract + results + conclusion"). The plan's "it is the single-split datum; r25 4.30 is the result" is correct — but the conclusion restates 24.89 (L2560), so 3 not 2.

E6. **Plan principle 3 lists "surprisingly" — 0 occurrences in the text** (verified by grep). No action required; remove from the inventory or keep as a guard pattern for the rewrite.

E7. **Existing cross-reference bugs the plan must fix (found in audit):** L2465 and L2634 cite "(§4.2)" for the 10-class MNIST flip, which lives in §4.1 (L1223–1243) → §4.1 (target §4.3); L2608 cites "Table \ref{tab:stage_impact}" for the ECG5000 24.89pp (that table is ECG200-only) → drop the table pointer; L2307 and L2668 cite "§5.2" for the SVM-RBF collapse / concat analysis, which live at L1387–1389/L2100–2102 (→§4.1) and L2083–2107 (→§4.2) respectively. Also L1868 "The repeated-CV verification of §4.1 added 2100 further runs" — fine.

E8. **Plan's Ch3 "consolidated protocol block (CV scheme, seeds, level-matched conventions)" — "level-matched conventions" is a misnomer.** Level matching is an analysis choice made in §4.1 equal-footing (L1117–1156), not a protocol convention. The protocol block should consolidate: CV scheme (5-fold, base seed 42, repetition seeds 43–67 r25 / 43–47 r5), CI estimators (repeated-measures t-interval + Nadeau–Bengio corrected resampled), η²/ω² analysis conventions, per-dataset CRC32 subsampling seeds, exclusion discipline (56/672). Level-matching stays in results.

E9. **Plan's §5.3 mapping "content moves into Ch4.3/4.4" — needs refinement to a 4-way split:** §5.3.1 blocks go to §4.3 (fragility, Friedman/Nemenyi, MIT-BIH, topology-wins) and §4.2 (diverse panel, concat); §5.3.2 blocks go to §4.2 (hyperparameters, window-length, cross-library), §4.1 (repeated-CV harmonisation), §4.5 (Sparse Rips large-n); §5.3.3 → §4.4. Exact ranges in C4.

E10. **Plan's "616/672 | keep ~2 (abstract, §3 protocol)" — Ch4 intro (L961–968) also states it authoritatively.** Recommend keeps: abstract, §3.3 protocol, Ch4 intro (or Ch4 intro → "(§3.3)"), Compute block (one mention), App. D; removes at §1.2/§1.3/§5.5 as listed in A7. The gate "616 ≤ 3" then holds for prose.

E11. **Plan line anchors all verified correct:** §5.1 ≈1656 (actual 1656), §5.2 ≈1774 (1774), §5.4 ≈2342 (2342), §5.5 ≈2371 (2371), §6.1 ≈2589 (2589), Ch5 title ≈1652 (1652). No line-number corrections needed.

E12. **Plan's backtracking inventory quotes all verified verbatim** (L2245–2249 "under level matching (§4.1), but under the fixed panel grid…", L2246 "collapsed to 0.24pp", L2134 "default-settings artefact", L2250 "dominates again" → actual "leads, at"). One addition: the inventory misses the three "83.0\% … ranks fourth/third" correction narratives (L998–1002, L1340–1345, L1638–1640) and the FPS "earlier deferral … withdrawn" pair (L878, L888) — these are the most visible self-discovery passages in the paper and are covered in B1–B4.

E13. **Plan principle 6 ("Appendices are reference material — repetition there is fine") is consistent with Appendix D's 616/7/11/4 restatement (L3037–3041) — no change needed, but the "extensible" KEEP should be Appendix D, not §3.3.**

E14. **Ch6 title in plan ("Conclusion", thesis only) is feasible; §6.1's 92-line decision tree moves to Ch5.** Note the plan's target says Ch6 "~1–2 pages, no re-listed numbers" — but the current conclusion recap (L2550–2576) is the one sanctioned full summary per principle 1 (abstract + results + conclusion each state the numbers once). Keep the recap; strip only the guidance.

E15. **Plan execution step 2 says "delete §5.1" — change to "dismantle §5.1"** (see E1): the Python line-surgery should extract the 5 unique items, then delete the section shell. Similarly "merge §5.2+§5.5" must first move the Availability block (L1824–1860) to §3.4 and the Compute block (L1862–1873) to §4.5, or those unique blocks are lost.

E16. **Gate "grep: 0 instances of the backtracking-phrase inventory" — after B-execution the remaining allowed survivors are:** "single-split" (protocol labels, ≤6 incl. footnotes), "collapsed to" (only as SVM-RBF majority-class / norm-features findings: L1388, 1419, 1541, 1797→§4.2, 2100, 2484, 2667 — these are results, keep), "artefact" (only as menu/level-count findings: L1123, 1705→§4.2, 2009, 2049; and thesis L2586). The gate should enumerate the specific deleted strings, not blanket-banish words that also occur as findings.

---

## Execution order (revised from plan step 2)
1. Dismantle §5.1 (C1) → distribute 5 unique items; delete shell.
2. Move §5.3.1–5.3.3 blocks per C4; strip B7/B8/B9/B12/B15/B17/B18/B19/B20 prose during moves.
3. Merge §5.2+§5.5 → Ch5 conditions (C2); relocate Availability → §3.4, Compute → §4.5.
4. Merge §5.4+§6.1 → Ch5 guidance (C3); retitle Ch5 (C5); delete §5.1/§5.2 remnants; retitle Ch6 "Conclusion"; strip §6.1 from Ch6.
5. Insert cross-refs per D; fix pre-existing ref bugs (E7).
6. Strip remaining backtracking per B1–B30; fix Ch4-intro duplicates (L1004–1010 ↔ L1403–1410).
7. Compile 2×; verify 13-key number baseline, section renumbering, 0 undefined refs; vision pass on changed pages.
