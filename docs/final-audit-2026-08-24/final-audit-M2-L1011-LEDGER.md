# FINAL AUDIT — Mode 2 (KB only) — L10 STEELMAN-REVERSAL + L11 PROSE
Reviewer 2/3 · tda-benchmark dissertation @ HEAD 1e6f0f6 · 2026-08-24
Lenses: L10 steelman-reversal (argue the opposite of the central claim with the paper's own evidence);
L11 prose (readability/style; every claim counted; every style finding carries a BEFORE -> AFTER rewrite).
All numbers re-derived from data/tda/*.db with sqlite3, SELECT-only, finished_at IS NOT NULL,
per-config accuracy = AVG(f.accuracy) per run_id, stage means = stage-level mean of per-config means.

> PROVENANCE NOTE (reviewer 2/3): this file was written concurrently with sibling reviewer
> 'sa-3-48c96833' (likely Mode-2 reviewer 1/3 for this cluster). Their content was overwritten
> by this pass before it could be read (write_file clobbered the earlier write; no backup
> recoverable from /tmp or the session DB). The findings below are reviewer 2/3's complete,
> DB-verified pass. If reviewer 1/3's Mode-2 L10-L11 findings were only in this file, they must
> be re-run or recovered from the parent's per-reviewer outputs before the merge step.

================================================================================
L10 STEELMAN-REVERSAL
================================================================================

### [L10-1] Symmetric scalar-exclusion reverses the stage ordering — the classifier marginal range exceeds the vectorizer's in 20/25 repetitions
- severity: MAJOR
- type: new
- anchor: "ranges are also reported excluding the degenerate scalar vectorizers (ECG200 vectorizer range contracts from 6.39pp to 3.10pp but remains the largest stage; §4.1; re-derived from repeated_cv_r25.db, per-repetition mean method)" (§5.4 Threats to Validity, construct validity item 2) — and §4.1: "The honest reading is that vectorization is the largest single stage effect, but its measured margin is sensitive to the vectorizer menu..."
- finding: The paper's equal-footing defence is asymmetric: it re-derives only the VECTORIZER range under the exclusion of the degenerate scalars (Amplitude, Persistence Entropy) and then asserts the vectorizer "remains the largest stage". Re-applying the paper's own exclusion rule to ALL three stages on the paper's own cited DB (repeated_cv_r25.db, pooled per-config means, per-repetition marginal ranges) gives: vectorizer 3.10pp (reproduces the paper), classifier 3.90pp, filtration 1.90pp — the vectorizer is the LARGEST stage in only 4/25 repetitions, the classifier in 20/25 (mean range 3.9pp > 3.1pp; vec>clf in only 5/25 reps). The full-menu ordering vec>clf>fil (25/25) is an artefact of the floor effect in BOTH the vectorizer menu (scalars) and the classifier menu (SVM-RBF collapse): once the scalars are removed, the classifier's RF-vs-rest spread (RF 76.9% vs logistic 74.2 / svm_linear 73.2 / svm_rbf 73.0 marginal means, rep 1) dominates the vectorizer's spread (75.2 silhouette .. 72.8 betti). The paper's own reversal argument, run symmetrically, lands against the vectorizer: the headline claim survives only on the ω² metric and on the full-menu range, not on the equal-footing range.
- improvement: Re-run the equal-footing analysis on all three stages (cheap, one script over repeated_cv_r25.db) and report the symmetric numbers: "excluding the degenerate scalars yields vectorizer 3.10pp, classifier 3.90pp, filtration 1.90pp (classifier largest in 20/25 reps)". Rewrite the Threats item and the §4.1 "honest reading" sentence to say vectorization is the largest stage effect by ω² and by full-menu range, and that the ordering reverses to classifier>vectorizer under the exclusion rule; drop "remains the largest stage".
- cost: cheap (re-analysis + 2-sentence edit; no new compute)
- confidence: certain (re-derived with the paper's own convention; headline numbers reproduce exactly: vec 6.39/3.10, clf 3.50, fil 0.69, ordering 25/25 full menu)

### [L10-2] Decision tree Grade-A justification is factually false: "the vectorizer is the only stage whose CI excludes zero"
- severity: MINOR
- type: new
- anchor: "Grade A for the ordering: the vectorizer is the only stage whose CI excludes zero, the ordering holds in 25/25 repetitions, and the ω² population effect size ... confirms it is not a level-count artefact." (§6.1 decision tree, time-series branch) vs Table 4.1 footnote: "[5.69, 7.10], [2.92, 4.07], filtration [0.37, 1.01], all excluding zero"
- finding: The decision tree claims the vectorizer is the ONLY stage whose CI excludes zero — but the paper's own Table 4.1 CIs exclude zero for ALL THREE stages (repeated-measures: fil [0.57,0.81], clf [3.28,3.71], vec [6.13,6.65]; Nadeau-Bengio: [0.37,1.01], [2.92,4.07], [5.69,7.10] — the table footnote says "all excluding zero"). Under the ω² reading (the next clause in the same sentence), the classifier ω² CI [0.003, 0.246] also excludes zero, so the claim is false under either reading. The Grade-A justification for the ordering rests on the 25/25 stability and ω², not on CI exclusivity — the sentence is exactly backwards and a steelman reader can use the paper's own table to refute its own decision tree.
- improvement: Rewrite to: "the vectorizer's range CI is the widest and all three stage CIs exclude zero under repeated CV; the ordering holds in 25/25 repetitions and the ω² population effect size (ECG200 vectorizer 0.165, CI [0.063, 0.423], vs filtration −0.017, whose CI straddles zero) confirms the ordering is not a level-count artefact." (1-sentence edit)
- cost: cheap
- confidence: certain (direct contradiction of the paper's own table)

### [L10-3] Decision tree and guidelines table quote the menu-sensitive single-split 24.89pp while the paper's own r25 harmonisation (4.30pp, 24/25 reps) is the Grade-A-grade evidence and is not wired in
- severity: MINOR
- type: new
- anchor: "Vectorization is the dominant stage (ECG200 marginal range 6.39pp, 95% CI [6.13, 6.65] over 25 repetitions; ECG5000 24.89pp, single split, 3-vectorizer menu; §4.1, Table 4.1)" (§6.1, time-series branch) and Table 5.3 guidelines row: "Vectorization dominates variance (6.39pp on ECG200; 24.89pp on ECG5000)"
- finding: The decision tree's own Grade A definition is "verified under the 25-repetition repeated-CV protocol with corrected confidence intervals, or replicated across datasets" — and the paper's §5.3 "Repeated-CV harmonisation (expansion 5)" reports exactly that for ECG5000: vectorizer 4.30pp (95% CI [4.02, 4.57]), 24/25 repetitions, all CIs excluding zero. Yet the tree's time-series branch and the guidelines table both lead with the single-split, 3-vectorizer-menu 24.89pp — the figure the paper itself shows collapses to 0.24pp under level matching and which is superseded by the r25 estimate — and neither cites the r25 number. A practitioner reading only the decision-support artefacts takes away the menu-inflated magnitude; the paper's strongest countermeasure to the reversal is unused where it matters most.
- improvement: Replace 24.89pp with the r25 figure in §6.1 and Table 5.3 (and the decision-tree summary table row "Time series | tune vectorizer | ... 24.89pp"), citing §5.3 expansion-5r; keep the single-split figure only as a footnote explaining the menu sensitivity.
- cost: cheap (text edits, no compute — numbers already in the paper)
- confidence: certain (both figures present in the paper; cross-checked against r25_ecg5000.db conventions in the verified-clean bank)

### [L10-4] "The best vectorizer is data-set stable (Betti Curve)" overstates the panel: Betti is best on 5/9 datasets, not stable
- severity: MINOR
- type: new
- anchor: "The configuration-ranking analysis therefore supports vectorizer choice as the portable driver of the ranking: the best vectorizer is data-set stable (Betti Curve), with a Betti-to-Landscape rank gap exceeding the critical difference." (§5.3, B1 panel)
- finding: Re-deriving per-dataset best vectorizer from multidataset_sweep.db (finished runs, per-config fold-mean accuracies, rank within dataset over the 8 common VR-only configurations) gives: Betti best on 5/9 (ElectricDevices, FordA, Wafer, ECG5000, fmnist10), Silhouette on 2 (HandOutlines, ECG200), Persistence Image on 2 (FordB, mnist10); Betti's worst-case dataset rank is 5 of 8 (ECG200). "Data-set stable" overstates a plurality: the claim the data supports is "best on average (mean rank 2.89 vs 4.17/4.72/6.22, Betti-to-Landscape gap > CD)". A steelman reader can name two datasets (ECG200, HandOutlines) where following the "stable" recommendation picks the wrong vectorizer.
- improvement: Rewrite to: "the vectorizer family ordering is stable on average — Betti Curve is best on 5 of 9 datasets and best on mean rank (2.89 vs 4.17/4.72/6.22), with a Betti-to-Landscape gap exceeding the critical difference — though Silhouette wins on ECG200 and HandOutlines and Persistence Image on FordB and mnist10."
- cost: cheap (one-sentence edit)
- confidence: certain (re-derived from multidataset_sweep.db)

### [L10-5] ω² provenance parenthetical misattributes the MNIST ω² to the ECG200 sweep
- severity: POLISH
- type: new
- anchor: "The ω² population effect size (corrected for the number of levels; recomputed from the 25-repetition ECG200 sweep, 84 configurations) confirms the ordering under the design penalty: ECG200 vectorizer ω² = 0.165 ...; MNIST vectorizer 0.214 ..." (§4.1)
- finding: The parenthetical describes the recomputation source for the whole clause, but the MNIST ω² values (0.214 / 0.143 / 0.032) cannot come from the ECG200 sweep — the producer script (scripts/analysis_eta_omega2.py) computes MNIST ω² from mnist_repeated_cv.db (56 configs, 5 reps) and ECG200 from repeated_cv_r25.db (84 configs, 25 reps). The numbers themselves reproduce exactly (ECG200 vec 0.1646 CI [0.0632,0.4225]; MNIST vec 0.2139 CI [0.1030,0.5403]); only the provenance sentence is wrong/misleading, which is the statement a reproducing reviewer would follow first.
- improvement: Split the parenthetical: "...(corrected for the number of levels; ECG200 recomputed from the 25-repetition sweep, 84 configurations; MNIST from the 5-repetition mnist_repeated_cv.db, 56 configurations)..."
- cost: cheap
- confidence: certain (script inspected; report regenerated and matches the paper's numbers)

================================================================================
L11 PROSE
================================================================================

### [PROSE-1] Worst-sentence pathology: the ECG5000 generality sentence — 109 words, four nested parentheticals, ~12 statistics
- severity: MINOR
- type: new
- anchor: "The ECG200 result could be instance-specific, so the stage analysis was repeated on a second UCR recording, ECG5000 (UCR archive; 5 classes; 140 timesteps; single patient recording, BIDMC chf07) with the same 5-fold protocol on a stratified subsample of 714 samples (≤ 200 per class) drawn from the full 5000-sample recording (class counts 2919, 1767, 96, 194, 24; majority class 58.38% in the full recording; the executed 714-sample subsample is balanced to ≤ 200/class, so its majority share is 28.0%) and a pipeline subset (2 filtrations, 3 vectorizers, 2 classifiers; the subset spans the strongest and weakest vectorizers from ECG200 to bound the range)." (§4.1, "Generality probe: ECG5000")
- finding: This is the densest sentence in the document: subject-verb separation of ~20 words, three levels of parenthetical nesting inside one clause, and 10+ numbers (5 classes/140/714/200/5000/2919/1767/96/194/24/58.38/28.0/2/3/2). It forces re-reading even for a motivated examiner, and it opens the paper's second time-series result. Related heavy siblings: §2.4's stability sentence ("...extreme value theory gives ... E[max_i ‖η_i‖] ≈ σ√(2ln n) (the one-dimensional leading-order value; for the executed d=3 per-coordinate noise the expectation is larger by the dimension correction, ≈1.16 σ√(2ln n) at n=100; Monte Carlo gives ... ≈ 1.06 at σ=0.30)") and §3.2's FPS sentence (k∈{50,15} with the "knob never fires" aside).
- improvement: BEFORE -> AFTER (split into three sentences, zero information loss):
  BEFORE: "The ECG200 result could be instance-specific, so the stage analysis was repeated on a second UCR recording, ECG5000 (UCR archive; 5 classes; 140 timesteps; single patient recording, BIDMC chf07) with the same 5-fold protocol on a stratified subsample of 714 samples (≤ 200 per class) drawn from the full 5000-sample recording (class counts 2919, 1767, 96, 194, 24; majority class 58.38% in the full recording; the executed 714-sample subsample is balanced to ≤ 200/class, so its majority share is 28.0%) and a pipeline subset (2 filtrations, 3 vectorizers, 2 classifiers; the subset spans the strongest and weakest vectorizers from ECG200 to bound the range)."
  AFTER: "The ECG200 result could be instance-specific, so the stage analysis was repeated on a second UCR recording, ECG5000 (UCR archive, 5 classes, 140 timesteps; single patient, BIDMC chf07). The analysis used the same 5-fold protocol on a stratified subsample of 714 samples (≤ 200 per class) drawn from the full 5000-sample recording (class counts 2919, 1767, 96, 194, 24; majority class 58.38% in the full recording; 28.0% in the balanced subsample). The pipeline subset (2 filtrations, 3 vectorizers, 2 classifiers) spans the strongest and weakest ECG200 vectorizers to bound the range."
- cost: cheap (3 sentences rewritten)
- confidence: certain

### [PROSE-2] Number-crowding: sentences packing 12 statistics each (ω² and B2 range sentences)
- severity: MINOR
- type: new
- anchor: "The ω² population effect size (corrected for the number of levels; recomputed from the 25-repetition ECG200 sweep, 84 configurations) confirms the ordering under the design penalty: ECG200 vectorizer ω² = 0.165 (bootstrap 95% CI [0.063, 0.423]) versus classifier 0.077 ([0.003, 0.246]) and filtration −0.017 ([−0.017, 0.093]); MNIST vectorizer 0.214 ([0.103, 0.540]) versus filtration 0.143 ([0.040, 0.312]) and classifier 0.032 ([−0.015, 0.257])." (§4.1) and "Across datasets the filtration range spans a minimum of 0.31 pp, a median of 1.37 pp, and a maximum of 4.41 pp (mean 2.17 pp), while the vectorization range spans a minimum of 0.62 pp, a median of 3.32 pp, and a maximum of 15.00 pp (mean 5.11 pp)." (§5.3, B2)
- finding: Both sentences carry ~12 numbers and three CI brackets each; none of the numbers lands on first read. The ω² sentence is the load-bearing defence against the level-count confound — the reader should take away "vectorizer ω² largest; CI excludes zero on both datasets; filtration's ECG200 CI straddles zero" — but must disambiguate six brackets to do so. The B2 sentence's six descriptive stats (min/median/max/mean × 2 stages) belong in a table.
- improvement: BEFORE -> AFTER (ω² sentence): "The ω² population effect size (corrected for level counts; ECG200 from the 25-repetition sweep, MNIST from mnist_repeated_cv.db) confirms the ordering under the design penalty. The vectorizer is the largest stage effect on both datasets (ECG200 0.165, bootstrap 95% CI [0.063, 0.423]; MNIST 0.214, [0.103, 0.540]), ahead of the classifier (0.077 [0.003, 0.246]; 0.032 [−0.015, 0.257]) and the filtration (ECG200 −0.017 [−0.017, 0.093]; MNIST 0.143 [0.040, 0.312]); the vectorizer CI excludes zero on both datasets while the ECG200 filtration CI straddles zero. Full brackets are in Table 4.5." And for the B2 sentence: keep only "the filtration range averages 2.17pp (median 1.37pp, max 4.41pp) versus 5.11pp (median 3.32pp, max 15.00pp) for the vectorizer", moving the min/median/max grid to a one-line table.
- cost: cheap (2 rewrites; one small table)
- confidence: certain

### [PROSE-3] Verbatim clause repetition: "filtration effects are dataset-specific and modest" ×5, "modest" ×10
- severity: MINOR
- type: new
- anchor: five instances — §1.2 "Filtration effects are dataset-specific and modest on binary MNIST, not the governing stage"; §4.1 "filtration effects are dataset-specific and modest on binary MNIST, not the governing stage"; §4.1 "filtration effects are dataset-specific and modest. The ω² population effect size..."; §5.1 "filtration effects, while real, are dataset-specific and modest on binary MNIST"; §5.1 "Filtration effects are dataset-specific and modest on this binary subset; once a reasonable filtration is chosen..."
- finding: The same evaluative clause recurs five times (twice nearly verbatim in §1.2 and §4.1), and "modest" appears 10 times overall ("modest on binary MNIST", "modest (0.35--1.72pp...)", "filtration effects are real but modest"). The repeated hedge reads as the author's default assessment rather than a derived one, and the two near-duplicate sentences (intro vs results) are the same judgement at two sites where the reader is told the claim twice.
- improvement: BEFORE -> AFTER (keep one full statement; vary the rest):
  BEFORE (§5.1): "Yet even on binary MNIST the vectorizer moves accuracy more than the filtration: the marginal range is 3.22pp for vectorizers versus 1.65pp for filtrations (§4.1). Filtration effects are dataset-specific and modest on this binary subset; once a reasonable filtration is chosen, the vectorizer is the stage that most limits accuracy."
  AFTER: "Yet even on binary MNIST the vectorizer moves accuracy more than the filtration: 3.22pp marginal range versus 1.65pp (§4.1). On this subset the filtration gap is small and dataset-bound — cubical beats Vietoris-Rips by ~1.75pp best-of-family — so once a reasonable filtration is chosen, the vectorizer is the stage that most limits accuracy."
  In §1.2 and §4.1 replace the duplicated clause with the quantitative form ("the filtration range is 0.69pp on ECG200 and 1.65pp on binary MNIST, versus 6.39pp and 3.22pp for the vectorizer").
- cost: cheap
- confidence: certain (counts from grep: clause ×5, "modest" ×10)

### [PROSE-4] Vocabulary tics: "therefore" ×27, "artefact" ×20 (9× "not an artefact of"), "menu" ×21, "robust(ness)" ×30, "dominant(ce/ates)" ×28
- severity: MINOR
- type: new
- anchor: counts over the full prose (17k words): therefore 27; artefact 20 (the denial frame "not an artefact of" 9 times: lines 158, 296, 1130, 1362, 1543, 2090, 2235, 2359, 2532); menu 21; robust/robustness 30; dominant/dominates/dominates 28. Examples: "The topological signal is therefore not an artefact of the norm confound", "vectorization-dominance is therefore not an artefact of the decorative-topology regime", "the ordering is not an artefact of the 128-sample window", "dominance is not an artefact of level counts", "the robustness is not an artefact of the norm confound".
- finding: The paper's two favourite rhetorical moves are (a) the causal flourish "therefore" (1.6 per 1000 words; 6× "We therefore") and (b) the denial frame "X is not an artefact of Y", used 9 times — often for the same underlying concern (norm confound ×3, level counts ×2). Together with "menu" (21) and "robust/robustness" (30), the vocabulary is narrower than the content: the same words carry the argument at every site, and the "not an artefact" frame advertises the paper's own confound worries at the same frequency as their resolution. ~half of the "therefore" instances are deletable or replaceable.
- improvement: BEFORE -> AFTER (two representative rewrites):
  BEFORE: "The topological signal is therefore not an artefact of the norm confound: it survives the norm/scale confound control, and it is robust to noise at the levels tested." (§4.2)
  AFTER: "The topological signal survives the norm/scale confound control and holds up to σ=0.30 noise: it is not a by-product of the norm marginal."
  BEFORE: "Vectorization-dominance is therefore not an artefact of the decorative-topology regime: it persists where topology genuinely carries the classification signal" (§5.3, expansion 6)
  AFTER: "Vectorization-dominance persists where topology genuinely carries the classification signal — it is not an artefact of the decorative-topology regime."
  Replace roughly half of "therefore" (27) with "so"/"hence"/"consequently" or delete; vary 4 of the 9 "not an artefact of" frames with "cannot be explained by", "survives", "is not driven by".
- cost: cheap (find-replace pass + 2 rewrites)
- confidence: certain (counts from grep)

### [PROSE-5] Uniform end-of-chapter transition skeleton: "Chapter~N [verb]s ..." ×5
- severity: POLISH
- type: new
- anchor: five instances — §1.2 "Chapter~2 develops the mathematical machinery needed to understand why these pipeline stages interact as they do."; §2 "Chapter~3 translates this mathematical machinery into a software architecture that executes the factorial sweep."; §3 "Chapter~4 presents the empirical results of this sweep across six dataset instances and four analytical cuts."; §4 "Chapter~5 interprets why vectorization dominates on both real datasets and derives operational guidelines from these patterns."; §5 "Chapter~6 synthesizes these findings into a single conditional thesis."
- finding: Every chapter closes with the identical "Chapter N + verb + purpose" sentence. The skeleton is serviceable once; five times in a row the reader hears the routing announcement coming. Two of the five can be cut entirely (the transitions add no information beyond the TOC).
- improvement: BEFORE -> AFTER (rewrite two, delete one):
  BEFORE (§3 close): "Chapter~4 presents the empirical results of this sweep across six dataset instances and four analytical cuts."
  AFTER: "We now turn to the results: one sweep of 616 configurations, cut four ways (§4.1--§4.4)."
  BEFORE (§5 close): "Chapter~6 synthesizes these findings into a single conditional thesis."
  AFTER (delete — the chapter title and opening sentence already say this) or: "Section 6.1 collapses the conditionality into a graded decision tree for practitioners."
- cost: cheap
- confidence: certain (count from grep)

### [PROSE-6] Third-person self-reference: "the paper's"/"the manuscript's" ×7 in a first-person dissertation
- severity: POLISH
- type: new
- anchor: "the paper's headline 83.0% configuration (cubical + Silhouette + Random Forest) is a single-split point estimate" (§4.1); "the paper's best single-split ECG200 configuration (cubical + Silhouette + Random Forest, 83.0%) ranks third by 25-repetition mean" (§4.1); "the paper's scoped claim stands" (§5.3 concat); "the manuscript's default hyperparameters" (§5.3 B3); "the manuscript's limitations note" (§5.3 H2)
- finding: The text alternates between first person ("we", "our") and third-person self-reference as "the paper"/"the manuscript" — 7 instances. In a dissertation (which is not a paper and is authored by one person), "the paper's headline configuration" reads as external commentary; the oscillation is a voice inconsistency the reader registers without resolving.
- improvement: BEFORE -> AFTER:
  BEFORE: "Finally, the paper's headline 83.0% configuration (cubical + Silhouette + Random Forest) is a single-split point estimate: by r=5 repeated-CV mean it ranks fourth (79.6%, SD 1.98pp)"
  AFTER: "Finally, our headline 83.0% configuration (cubical + Silhouette + Random Forest) is a single-split point estimate: by r=5 repeated-CV mean it ranks fourth (79.6%, SD 1.98pp)"
  Likewise "the manuscript's default hyperparameters" -> "our default hyperparameters"; "the paper's scoped claim stands" -> "our scoped claim stands".
- cost: cheap
- confidence: certain (grep count 7)

### [PROSE-7] Register lurches: chatty metaphors in formal prose ("knob never fires", "stacks the deck", "compress the field from below")
- severity: POLISH
- type: new
- anchor: "the runner's \texttt{subsample\_points} knob never fires and the subsampling choice must be made below the native resolution to be nontrivial" (§3.2, FPS); "a stage with more levels can span a larger range by chance" / "stacks the deck" (§5.4, construct validity item 1: "the headline comparison (7 vectorizers vs. 3--4 filtrations) stacks the deck"); "what it does do is compress the field from below, pulling the weakest vectorizers up toward the leader" (§5.3, B3)
- finding: Three informal metaphors sit in otherwise textbook-formal prose. "Knob never fires" is engineering slang for a YAML flag that does not trigger; "stacks the deck" is a gambling idiom in the Threats section; "compress the field from below" is racing/finance imagery for a result that is really "tuning raises the weakest vectorizers' accuracy, narrowing the range from the bottom". Each is individually charming, together they mark the register as unstable — a reader of §3.2 (formal methods) and §5.4 (formal validity analysis) is not expecting idiom.
- improvement: BEFORE -> AFTER:
  BEFORE: "the runner's \texttt{subsample\_points} knob never fires and the subsampling choice must be made below the native resolution to be nontrivial"
  AFTER: "the runner's \texttt{subsample\_points} parameter is never applied (the native clouds already carry 100 points), so the subsampling choice must be exercised below the native resolution to be nontrivial"
  BEFORE: "the headline comparison (7 vectorizers vs. 3--4 filtrations) stacks the deck"
  AFTER: "the headline comparison (7 vectorizers vs. 3--4 filtrations) is unfavourably unbalanced"
  BEFORE: "what it does do is compress the field from below, pulling the weakest vectorizers up toward the leader"
  AFTER: "the effect is to narrow the range from below: the weakest vectorizers improve most under tuning"
- cost: cheap
- confidence: certain

### [PROSE-8] Repeated openers and the bold-label paragraph template: "On <dataset>" ×14, 56 bold run-in paragraph labels
- severity: MINOR
- type: new
- anchor: openers — "On ECG200" ×7 ("On ECG200, vectorization moves accuracy by 6.39pp", "On ECG200 the vectorizer explains 21.7% of the per-config variance", "On ECG200 the two-way interactions are not negligible", "On ECG200 the vectorizer range is 6.39pp versus 0.69pp for filtration"), "On binary MNIST" ×5, "On MNIST" ×2; paragraph labels — 56 \textbf{...} run-in topic labels across the paper, e.g. "\textbf{Equal-footing re-analysis.}", "\textbf{Simple versus complex.}", "\textbf{Full 10-class MNIST.}", "\textbf{Diverse-filtration check.}", "\textbf{Window-length sensitivity.}", "\textbf{Sparse Rips at its design point (expansion B5).}"
- finding: Results prose opens "On <dataset>" 14 times, and the results chapters are built as chains of bold run-in labelled paragraphs — 56 across the document, ~30 in §4.1/§5.3 — each running the same internal template: labelled claim, then numbers, then parenthetical caveat. The bold-label structure is a defensible expository choice, but at this density it reads as a slide deck: the topic sentence is always a label, so the reader never gets a prose lead that frames the result before the numbers arrive.
- improvement: BEFORE -> AFTER (two spots):
  BEFORE: "On ECG200 the two-way interactions are not negligible: the three interaction terms jointly carry ω² = 0.187, which is 147% of the main-effect total (0.127)." (§4.1)
  AFTER: "The stages are not cleanly separable on ECG200: the three two-way interaction terms jointly carry ω² = 0.187 — 147% of the main-effect total (0.127)."
  BEFORE: "\textbf{Simple versus complex.} Persistence Statistics matches kernel-based methods on ECG200: its r=5 marginal accuracy (74.8%) is within 0.3pp of Persistence Landscapes (75.1%)" (§4.1)
  AFTER: "\textbf{Simple versus complex.} On ECG200, the zero-parameter Persistence Statistics matches the kernel-based methods: its r=5 marginal accuracy (74.8%) sits within 0.3pp of Persistence Landscapes (75.1%)" — and convert 3-4 of the 56 bold labels into ordinary prose topic sentences in the most number-dense stretch (§5.3 expansion paragraphs) to vary the rhythm.
- cost: cheap
- confidence: certain (counts from grep)

================================================================================
VERDICT
================================================================================
VERDICT: Not yet submission-ready on this lens cluster, but close. L10 found one MAJOR: the paper's own equal-footing defence is asymmetric — applying its scalar-exclusion rule to all three stages (re-derived from repeated_cv_r25.db, exact reproduction of the paper's own numbers) makes the classifier the largest marginal range in 20/25 repetitions, directly contradicting the Threats-to-validity assertion that the vectorizer "remains the largest stage"; the central claim survives on ω² and full-menu range but its scoped defence is materially overstated and must be corrected. Four further L10 findings are cheap text fixes (decision-tree CI claim exactly backwards; decision tree/guidelines still quoting the menu-sensitive 24.89pp instead of the paper's own r25 4.30pp; "data-set stable" overstating a 5/9 plurality; ω² provenance sentence misattributed). L11 is healthy: no pervasive readability blocker — the prose is competent and honest — but the number-crowded ω²/B2 sentences, the 109-word ECG5000 opener, the ×5 verbatim "dataset-specific and modest" clause, and the 56-label bold-paragraph monotony are the highest-yield fixes. The single highest-leverage fix: L10-1 — rerun the equal-footing exclusion symmetrically and correct the "remains the largest stage" claim, because it is the paper's own published defence against its central confound and it is currently false on the range metric.

READER'S VERDICT (L11): Reading pages 20-35 cold (the §4.1--§5.3 stretch), the experience is: competent, honest, and predictable. The bold run-in labels carry you paragraph to paragraph without any need to parse transitions — which is good — but every paragraph then asks you to absorb 4-12 statistics in parenthetical chains, and the repeated assessment phrases ("filtration effects are dataset-specific and modest", "X is not an artefact of Y", "vectorization remains the dominant stage") recur often enough that by page 30 you are skimming for the number that changed rather than reading. The single highest-leverage habit to break: stop packing three brackets and six numbers into one sentence — move the CI grids and min/median/max spreads into tables and let each prose sentence argue one number.
