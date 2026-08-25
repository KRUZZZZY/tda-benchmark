# FINAL AUDIT — Mode 2 (KB only, no internet), L1 DESIGN-CONFOUNDS + L2 STATS + L3 EVIDENCE-STRENGTH
> NOTE (append-collision): per the system write warning, sibling subagent sa-0-d8859c45 (likely Mode-2 reviewer 1/3 for this cluster) had written to this path before this pass's write_file replaced it; no backup recoverable. This file holds ONLY reviewer 2/3's complete, DB-verified ledger (10 findings + verdict). The sibling's findings must be collected from sa-0-d8859c45's own final summary; do not treat this file as the merged 3-reviewer ledger.
Reviewer 2 of 3 (lens cluster pass). Paper: projects/tda-benchmark/dissertation.tex @ HEAD 1e6f0f6 (3221 lines read in full incl. appendices/tables/footnotes). All quoted numbers re-derived via sqlite3 (SELECT-only) from data/tda/*.db with the brief's conventions (finished_at IS NOT NULL; per-config = AVG(f.accuracy) per run_id; stage-level means; per-rep ranges where the paper uses them).
NEW findings only; verified-clean bank and known-open items not restated.

### [L1-1] The "10-class MNIST flip" is confounded with menu composition — the paper's own equal-footing analysis shows the same reversal at binary scale
- severity: MAJOR
- type: new
- anchor: "We therefore read the binary-MNIST result (vectorization dominant) as a binary-scale phenomenon: at 10-class scale, filtration becomes the larger marginal stage." (S4.2); decision tree "Images, multi-class (>=10 classes): the ordering flips" (S6.1, Grade B)
- finding: mnist10's vectorizer menu is {Betti, PI, Landscape, Silhouette} — no scalar vectorizers (verified from mnist10_sweep.db: 80 finished runs) — while the binary-MNIST 3.22pp range is over the full 7-vectorizer menu including Amplitude/Entropy. The paper's own equal-footing analysis reverses the binary ordering once scalars are excluded: best-2 vectorizer range 0.44pp < 2-filtration range 1.55pp (verified from mnist_repeated_cv.db). So the reversal is a menu-composition/level-matching phenomenon present at BOTH scales, not a 10-class boundary condition; the "binary-scale phenomenon" reading (and the clean binary->vectorizer / multiclass->filtration dichotomy in the decision tree) is contradicted by the paper's own level-matched binary result, which the tree omits.
- improvement: rewrite the S4.2 reading and the S6.1 "Image, multi-class" branch to state that the flip tracks scalar-vectorizer exclusion / level matching (present at binary scale too, S4.1 equal-footing), and grade the boundary condition accordingly; cite the 0.44 vs 1.55pp level-matched binary numbers next to the mnist10 numbers.
- cost: cheap
- confidence: probable

### [L1-2] Appendix D Takens-sweep reversal is uninterpretable: the reduced subset's composition is never stated and it engineers the classifier-dominates result
- severity: MINOR
- type: new
- anchor: "On this reduced subset the classifier is the largest stage (3.88--9.63pp; driven by SVM-RBF collapsing to the 66.5% majority class on Persistence Entropy features)" (Appendix D, Table D.1 row (3,1): fil 1.12 / vec 1.38 / clf 9.62)
- finding: the subset is {VR, weak_alpha} x {persistence_image, persistence_entropy} x {random_forest, svm_rbf} (verified from takens_sweep.db, 72 finished runs). At (3,1) the vectorizer range collapses to 1.37pp because PI (70.6) and Entropy (72.0) nearly tie on this subset, while the classifier range explodes because the subset contains exactly the RBF-on-Entropy majority collapse (66.5 vs RF 76.1). The paper names the RBF driver but never states which vectorizers/classifiers are in the subset, so the "vectorization-dominance does not transfer to this reduced subset" contrast reads as an embedding-parameter effect when it is largely a subset-composition artefact; the (d,tau) sweep cannot be compared against S4.1 without that information.
- improvement: one sentence stating the 2x2x2 subset composition (and ideally add one mid/high vectorizer per arm so the (d,tau) contrast is not dominated by the PI-vs-Entropy tie).
- cost: cheap
- confidence: certain

### [L1-3] "The subset spans the strongest and weakest vectorizers from ECG200" misstates the ECG5000 menu
- severity: MINOR
- type: new
- anchor: "a pipeline subset (2 filtrations, 3 vectorizers, 2 classifiers; the subset spans the strongest and weakest vectorizers from ECG200 to bound the range)" (S4.1, ECG5000 probe)
- finding: the ECG5000 vectorizer menu is {persistence_entropy, silhouette, betti_curve} (verified from ecg5000_balanced.db). On the ECG200 r25 marginal, Entropy is weakest (68.95) but Silhouette is 3rd (74.38) and Betti 5th (72.38); the strongest ECG200 vectorizers (Landscape 75.32, Statistics 74.40) are absent. The menu spans the weakest plus two mid-ranked vectorizers; the 24.89pp range is bounded by Entropy vs mid vectorizers, not by the true extremes, so the "bound the range" justification overstates the menu's coverage.
- improvement: correct the parenthetical to "spans the weakest ECG200 vectorizer plus two mid-ranked ones" or add Landscape to the probe.
- cost: cheap
- confidence: certain

### [L2-1] Abstract/conclusion ECG5000 "level-matched reversal" rests on a filtration range inflated by the 2 failed cells, and the "menu-dependent" framing contradicts the paper's own r25 harmonisation (S5.3)
- severity: MAJOR
- type: new
- anchor: "the level-matched comparison reverses there (filtration 3.60pp vs. vectorizer 0.24pp), so the ECG5000 ordering is menu-dependent" (Abstract; repeated in Conclusion); versus "This resolves the earlier menu-dependence concern for this dataset: ... the vectorizer dominates with disjoint confidence intervals; the magnitude depends on the menu, the ordering does not." (S5.3, expansion 5)
- finding: (a) the 3.60pp filtration range is computed over non-matching menus (WA marginal over 4 configs excluding the failed silhouette cells, VR over 6 including silhouette — disclosed only in S4.1). Imputing the two failed WA+silhouette cells at VR-silhouette level (~61.8%) drops the WA-vs-VR gap from 3.60pp to ~0.5pp, so the quoted reversal magnitude is largely an artefact of the missing cells. (b) The paper's own r25 fixed-grid estimate (vec 4.30pp [4.02,4.57] > fil 0.96pp [0.80,1.13], ordering in 24/25 reps, verified in bank) is presented in S5.3 as resolving the menu-dependence concern, yet the abstract and conclusion still headline the single-split "reverses there / menu-dependent" narrative. Abstract and conclusion are stale relative to S5.3.
- improvement: re-lead the ECG5000 evidence in abstract/conclusion with the r25 fixed-grid numbers (vec 4.30 [4.02,4.57] vs fil 0.96 [0.80,1.13], 24/25 reps) and relegate the 24.89/3.60/0.24 single-split story to a footnote with the failed-cell caveat.
- cost: cheap
- confidence: probable (imputation is an estimate; the stale-framing half is certain)

### [L2-2] Table 4.3 reports a highly significant vectorizer effect on saturated sphere/torus sigma=0 while S4.1/S6.1 say "no stage dominates" — unreconciled
- severity: MINOR
- type: new
- anchor: Table 4.3 (Sphere/Torus sigma=0.00, Vectorizer: per-config eta2=0.165, F=3.67, p=0.002; fold-level F=3.10, p=0.005) vs "No stage dominates --- the signal is strong enough that every pipeline separates it nearly perfectly" (S4.1) and "every stage range is below 0.1pp (vectorizer 0.09...) Grade A for saturation" (S6.1)
- finding: verified from expanded_results.db / eta_squared_results.csv: the vectorizer per-config F-test on sphere_torus_n0 is p=0.0025 with eta2=0.165 although the marginal range is 0.094pp (all configs 99.5-100%). Both statements are individually true (significant tiny effect vs negligible range) but the paper never reconciles them; a reader citing Table 4.3 would conclude a real vectorizer effect on clean point clouds, contradicting the "no stage matters / saturation" narrative in the same chapter and the decision tree.
- improvement: add one clause to the S4.1 sphere/torus paragraph (or the Table 4.3 footnote) explaining that on the saturated datasets the F-tests detect a statistically non-zero but practically negligible (<0.1pp) effect, so the decision-tree "no stage dominates" refers to magnitude.
- cost: cheap
- confidence: certain

### [L2-3] Threats-to-validity mis-cites the r=5 79.6%/rank-4 number to the r25 database
- severity: POLISH
- type: new
- anchor: "the headline 83.0% configuration drops to 79.6% at r=5 (rank 4 of 84; repeated_cv_r25.db)" (S5.4, Construct validity item 3)
- finding: verified: 79.6% (SD 1.98), rank 4 is the r=5 result from repeated_cv.db over 112 configs; repeated_cv_r25.db is the 25-repetition DB where the same configuration is 79.30% (SD 1.57), rank 3 of 84. The parenthetical attributes an r=5 number to the r25 DB and "of 84" matches neither (r5 has 112 configs; the r25 rank is 3).
- improvement: cite repeated_cv.db for the r=5 number and correct to "rank 4 of 112", or cite repeated_cv_r25.db for 79.30%/rank 3.
- cost: cheap
- confidence: certain

### [L2-4] "Beyond accuracy" sentence mixes per-vectorizer marginals (balanced accuracy) with per-config values (macro-F1)
- severity: POLISH
- type: new
- anchor: "balanced accuracy per vectorizer is 0.46--0.47 (Betti Curve, Silhouette) versus 0.28 (Persistence Entropy) and macro-F1 0.50--0.51 versus 0.12--0.38" (S4.1, Beyond accuracy)
- finding: verified from beyond_accuracy_ecg5000.db: per-vectorizer marginal balanced accuracy is 0.462/0.469 vs 0.281 (correct), but per-vectorizer marginal macro-F1 is 0.430/0.448 vs 0.240; the quoted 0.50-0.51 are the Random-Forest-only config rows (0.506/0.498) and 0.12-0.38 is a config range. The sentence implies both metrics are per-vectorizer marginals; they are computed on different bases.
- improvement: state the macro-F1 basis ("best-config (Random Forest) macro-F1 0.50-0.51; per-vectorizer marginal 0.43-0.45") or compute the marginal.
- cost: cheap
- confidence: certain

### [L3-1] Decision tree grades the time-series branch with the inflated single-split 24.89pp instead of the r25 fixed-grid estimate the paper itself defends
- severity: MAJOR
- type: new
- anchor: Table 6.1 (tab:decision_tree) "Time series | tune vectorizer | ECG200 6.39pp [6.13, 6.65] r=25; ECG5000 24.89pp (S4.1, Table 4.2) | A"; S6.1 item 1(a) "ECG5000 24.89pp, single split, 3-vectorizer menu"
- finding: the 24.89pp is a single-split point estimate on a 10-config grid (2 failures, unbalanced menus) that the paper itself calls "substantially inflated by degenerate scalar vectorizers" and whose level-matched version reverses (L2-1). The Grade-A evidence for the ECG5000 ordering is the r25 fixed-grid result (vec 4.30 [4.02,4.57] vs fil 0.96 [0.80,1.13], ordering in 24/25 reps), which is cited nowhere in the decision tree or S6.1. The tree's Grade-A time-series branch therefore leans on the weakest of the three ECG5000 estimates, and S6.1's "The ordering survives; the size does not" is asserted for a dataset where the level-matched comparison reverses.
- improvement: replace the ECG5000 evidence in Table 6.1 and S6.1 with the r25 fixed-grid numbers (with CI and 24/25-rep stability), and add the level-matched caveat to the "ordering survives" sentence.
- cost: cheap
- confidence: certain

### [L3-2] "Betti Curve as the portable best vectorizer" inverts the ECG200 r25 ordering without reconciliation
- severity: MAJOR
- type: new
- anchor: "the best vectorizer is data-set stable (Betti Curve)" (S5.3 panel analysis); "the robust conclusions --- Betti Curve as the portable best vectorizer..." (S5.3 MIT-BIH); "the vectorizer family ordering (Betti Curve 2.83, Persistence Image 4.22, Silhouette 4.69, Persistence Landscape 6.25 mean rank ...) is stable" (S5.3)
- finding: verified from repeated_cv_r25.db and the panel: on ECG200 r25, Betti Curve is 5th of 7 (72.38%) and Persistence Landscape is 1st (75.32%), while on the 9-dataset panel and MIT-BIH, Betti is best and Landscape worst (mean rank 6.25; 27.65% on MIT-BIH). The paper claims the vectorizer family ordering is "stable" and Betti "portable" without reconciling the complete inversion on the paper's own headline dataset; the only acknowledgment is a Table 5.4 rationale footnote ("Betti is 5th of 7 vectorizers on the r25 ECG200 marginal"). The ordering that is stable is the panel's internal ordering, not the ECG200 ordering — "the vectorizer effect generalises" overstates, and the Table 5.4 recommendation of Betti Curves for time series conflicts with Betti being mid-ranked on ECG200.
- improvement: add an explicit reconciliation paragraph (why Landscape wins ECG200's 7-vectorizer menu but ranks last on 8 other datasets — e.g., menu composition, hyperparameter defaults, dataset geometry), and soften "portable"/"stable" to "panel-stable".
- cost: cheap (edit) / expensive (if a follow-up experiment is required)
- confidence: certain

### [L3-3] Threats-to-validity (S5.4) and decision-tree branch 6 list expansions #6/#9/#11 and MIT-BIH as planned/missing/pending although S5.3 reports them completed
- severity: MAJOR
- type: new
- anchor: "Mitigation (planned): cross-library replication in GUDHI-native and Ripser-native paths (expansion #11)" (S5.4 internal 1); "Mitigation (planned): Alpha complex in 3D for H2 (expansion #9)" (S5.4 internal 2); "Planned: topology-wins datasets (#6), further UCR coverage, multi-patient ECG (MIT-BIH)" (S5.4 external 1); "Missing method families. No learned vectorizers (PersLay, Hofer; #8), no H2 features (#9), no cross-library replication (#11)..." (S5.4 external 4); "The topology-wins regime (expansion #6) ... until it runs, treat this branch as Grade C." (S6.1 item 6)
- finding: S5.3 reports expansions #6 (topology-wins, 80 runs), #9 (H2 via true Alpha, 12 runs) and #11 (cross-library, 90 runs) and the MIT-BIH multi-patient sweep as completed with results (all verified in the clean bank), and S5.2's own limitation (3) cites the MIT-BIH panel as covered. Yet the immediately-following S5.4 still lists #9/#11 as "missing" and #6/MIT-BIH as "planned", and S6.1 branch 6 says "until it runs" for #6. The threat severities and "planned mitigation" language are therefore stale and misstate the current evidence base: e.g., external-validity item 4's "no H2 features" is contradicted by S5.3's H2-alpha results two pages earlier, and the Grade-C topology branch ignores the completed topology-wins sweep.
- improvement: sweep S5.4 and S6.1 to mark #6/#9/#11/MIT-BIH as done (cite the S5.3 subsections), downgrade those threat items, and regrade decision-tree branch 6 (topology-wins data now exists: vectorizer 3.75-13.75pp vs fil 1.04-5.10pp on 3 dynamical datasets).
- cost: cheap
- confidence: certain

VERDICT: On my lens cluster (L1 design-confound, L2 statistics, L3 evidence-strength) the paper's core headline — vectorization is the largest stage main effect on ECG200 (6.39pp [6.13,6.65] vs fil 0.69pp, 25/25 reps, verified) and the equal-footing/omega^2/interaction-ANOVA scaffolding around it — is sound, honestly disclosed, and every headline number I re-derived checked out (including the 93% Monte Carlo, the interaction omega^2 decomposition, the isolated contributions, the cubical-grid ablation, and the beyond-accuracy panel). The paper is NOT yet submission-ready on this cluster, because a cluster of presentation-level inconsistencies materially weakens the evidence as readers will encounter it: (1) the abstract/conclusion/decision-tree ECG5000 story still leads with the single-split 24.89pp and the "reversal/menu-dependent" framing that the paper's own r25 harmonisation (S5.3) resolves and that rests on a filtration range inflated by two failed cells; (2) the "10-class flip" is presented as a scale boundary condition when the paper's own level-matched analysis shows the same reversal at binary scale — a menu confound; (3) "Betti Curve is the portable best vectorizer" inverts the ECG200 ordering without reconciliation; and (4) S5.4/S6.1 list expansions #6/#9/#11 and MIT-BIH as planned/missing that S5.3 reports as completed. The single highest-leverage fix: one consistency pass updating the abstract, conclusion, decision tree (Table 6.1, S6.1) and Threats-to-validity (S5.4) to the current evidence state — lead ECG5000 with the r25 fixed-grid numbers, state the binary-scale equal-footing reversal alongside the mnist10 flip, reconcile the Betti/Landscape inversion, and mark the completed expansions — all cheap edits that remove four MAJOR findings without new experiments.
