# FINAL AUDIT — Mode 1 (KB + internet + deep research), lens cluster L10 STEELMAN-REVERSAL + L11 PROSE
> NOTE (append-collision): per the system write warning, a sibling subagent (sa-2-bcc7aa80, the Mode-2 pass)
> had previously written to this file; this pass's write_file replaced it before the collision was noticed.
> The sibling's content is not recoverable from this agent's session store. The sibling's own Mode-2 ledger
> survives at /tmp/final-audit-M2-L1011-LEDGER.md. This file therefore contains ONLY this (Mode 1) pass's
> ledger. Parent orchestrator: collect the sibling's Mode-1 ledger from its own final response if needed.
Paper: projects/tda-benchmark/dissertation.tex @ HEAD 1e6f0f6 (3221 lines, 71pp compiled)
Auditor: subagent pass, 2026-08-24. New findings only (verified-clean bank and known-open items NOT restated).
All quoted numbers re-derived from data/tda/*.db unless marked "paper-reported" (per-config means over fold_results, finished_at IS NOT NULL; stage marginals = per-rep stage-level means).

---

## L10 STEELMAN-REVERSAL — the opposite of "vectorization dominates", argued from the paper's own evidence

### [L10-1] The surviving level-matched vectorizer edge is inside the paper's own noise floor, and the corrected ordering flips in 5/25 repetitions
- severity: MAJOR
- type: new
- anchor: "Matching the number of levels --- best-3 vectorizers versus 3 filtrations on ECG200 --- narrows the vectorizer edge to 1.21pp versus 0.69pp" (§4.1); "The ordering survives; the size does not." (§6 decision tree); "Per-configuration accuracy varies across repetitions with mean SD 1.09pp (max 3.11pp, $r{=}5$)" (Ch3 §3.3)
- finding: Under the paper's own equal-footing protocol I re-derived from repeated_cv_r25.db: mean level-matched gap = 0.52pp (best-3 vectorizer range 1.21pp minus 3-filtration range 0.69pp), but the per-repetition gap is positive in only 20/25 reps (min −0.87pp, SD 0.63pp; paired t=4.13). So the corrected "edge" is (a) smaller than the paper's own documented average per-config cross-repetition SD (1.09pp sample SD at r=5, 1.27pp at r=25 — verified 1.08/1.22pp with ddof=1), and (b) negative — filtration range larger than best-3 vectorizer range — in 5 of 25 repetitions. "The ordering survives" is true only for the unequal-footing full-menu comparison; under level matching the ordering itself is 20/25, and the mean margin is inside the single-configuration noise band.
- improvement: Report the per-repetition level-matched gap distribution (mean 0.52pp, SD 0.63pp, 20/25 positive) next to the 1.21/0.69 numbers in §4.1, and replace "The ordering survives; the size does not" with a statement that the corrected ordering holds in 20/25 repetitions with a mean margin below the per-config SD.
- cost: cheap — one paragraph + the statistics already computed
- confidence: certain (re-derived from the same DB the paper cites)

### [L10-2] Front matter discloses the ECG5000 level-matched reversal but withholds the MNIST best-2 reversal, which is negative in 5/5 repetitions
- severity: MAJOR
- type: new
- anchor: "On binary MNIST it again leads (3.22pp; $\eta^2 = 0.302$) while the filtration effect is modest" (Abstract); "but the level-matched comparison reverses there (filtration 3.60pp vs.\ vectorizer 0.24pp)" (Abstract, ECG5000 only); "on MNIST the best-2 vectorizer range (0.44pp) falls below the 2-filtration range (1.55pp)" (§4.1, body only)
- finding: The abstract and the Ch6 conclusion disclose the level-matched reversal for ECG5000 but never for MNIST — yet MNIST is one of the two "both real datasets" the headline rests on. Re-derived from mnist_repeated_cv.db: best-2 vectorizer range 0.44pp vs 2-filtration range 1.55pp, negative in ALL 5 repetitions (−1.28, −0.87, −0.82, −1.25, −1.33pp). Under the paper's own level-matching procedure, the "vectorization dominates on both real datasets" claim holds on 0 of 2 real datasets at matched footing (ECG200 by a sub-noise margin, MNIST reversed 5/5, ECG5000 reversed). The asymmetric disclosure makes the headline read stronger than the body supports.
- improvement: Add the MNIST best-2 reversal to the abstract and Ch6 in the same sentence that reports the ECG5000 reversal, and change "on both real datasets" to name the convention (full-menu, unequal footing) explicitly at first mention.
- cost: cheap — sentence-level edit
- confidence: certain (DB-verified)

### [L10-3] The paper's only population-level model ranks vectorizer LAST, yet the decision tree gives "tune the vectorizer" Grade A
- severity: MAJOR
- type: amends #15 (verified-clean bank: MixedLM "qualifies 'vectorization dominates' as within-dataset-range statement")
- anchor: "the population spread of the level effects is largest for the classifier ($1.81$\,pp; 95\% CI $[1.16, 2.47]$), then filtration ($1.71$\,pp; $[0.50, 3.04]$), then vectorizer ($1.18$\,pp; $[0.66, 1.94]$)" (§5.3, expansion 15); "spend your design budget on the \textbf{vectorizer}, not the filtration ... \emph{Grade A} for the \emph{ordering}" (§6 decision tree); "Vectorization is the dominant pipeline stage on both real datasets in this study." (Ch6 opening)
- finding: The bank records the MixedLM as a qualification, but the paper never propagates it: the abstract, Ch6 opening, and the decision tree all state or act on the unconditional claim. The decision tree's practitioner advice "spend your design budget on the vectorizer" is contradicted by the paper's own REML result — across datasets, the classifier (1.81pp) and filtration (1.71pp) have LARGER population level-effect SDs than the vectorizer (1.18pp) — which is the quantity that matters for a practitioner choosing a pipeline for a new dataset. The only place the two are reconciled is a single §5.3 sentence ("the two measure different quantities"); Ch6 never cites expansion 15.
- improvement: In the decision-tree branch and Table 6.2, downgrade "tune vectorizer" to Grade B and add one sentence: "across datasets (MixedLM, §5.3), the classifier and filtration show larger population-level effect spreads than the vectorizer; the within-dataset vectorizer lead does not transfer to new datasets." Optionally add the MixedLM ordering to the abstract's scope sentence.
- cost: cheap — text edits
- confidence: certain (paper-reported numbers internally consistent; the omission is verifiable by reading)

### [L10-4] "Betti Curve is the data-set-stable best vectorizer" is contradicted by the paper's own highest-precision dataset, where Betti is 5th of 7
- severity: MINOR
- type: new
- anchor: "the best vectorizer is data-set stable (Betti Curve), with a Betti-to-Landscape rank gap exceeding the critical difference" (§5.3, emphasized); "Betti is 5th of 7 vectorizers on the r25 ECG200 marginal (72.38\%), so Landscapes/Statistics are competitive" (Table 5.2 guidelines row)
- finding: The flagship portability claim is made from the single-split 9-dataset panel, while the paper's only 25-repetition dataset contradicts it: re-derived from repeated_cv_r25.db, the r25 ECG200 vectorizer marginal ordering is Landscapes 75.32 > Silhouette/Statistics ≈74.4 > PI ≈73.4 > Betti 72.38 > Amplitude ≈72.1 > Entropy 68.95 — Betti 5th of 7, a 2.94pp gap behind Landscapes. On single-split ECG200 Silhouette leads; on MIT-BIH the best configuration is Persistence Image + RF at both window lengths. "Betti portable" rests on the panel (VR-only time-series arm, single split) and is contradicted by every repeated-CV and best-config data point the paper itself reports; the paper reconciles only inside a table cell.
- improvement: Replace "data-set stable" with "best mean rank on the single-split panel, but not on the repeated-CV ECG200 marginal (5th of 7)" and soften the emphasized conclusion to "no single vectorizer is uniformly best; Betti has the best panel mean rank".
- cost: cheap — text edit
- confidence: certain (DB-verified 72.38% and 5th-of-7)

### [L10-5] "Filtration choice is a second-order factor" is contradicted by the paper's own DTM diverse-filtration arm, where filtration moves 2.81pp and wins 7/8 pairs
- severity: MINOR
- type: new
- anchor: "Filtration choice is a second-order factor on the datasets tested (exceptions in \S4.1 and \S5.3)" (Ch1 contributions); "raises the ECG200 filtration marginal range to 2.81pp and makes DTM the best filtration (76.2\% versus 73.4\% for Vietoris-Rips), winning 7 of 8 vectorizer--classifier pairs" (§5.1)
- finding: The contributions list still calls filtration "second-order" and the decision tree says "spend your design budget on the vectorizer, not the filtration", but the paper's own §5.1 check shows that once the filtration menu is genuinely diverse (VR + DTM), the filtration range (2.81pp) is comparable to the vectorizer range after scalar exclusion (3.10pp), DTM is the best filtration, and the best configuration changes. The steelman reading: "filtration barely matters (0.69pp)" is an artefact of a menu of three near-identical Rips-type filtrations — the paper says exactly this ("'filtration barely matters' is partly an artefact of that menu") yet the front matter language ("second-order factor") was never updated.
- improvement: Update the contributions bullet and decision-tree time-series branch to: "filtration effects are menu-dependent — 0.69pp across Rips-type filtrations, 2.81pp once a non-Rips filtration (DTM) is included, where DTM outperforms VR (76.2 vs 73.4\%)".
- cost: cheap — text edits
- confidence: certain (paper-reported, internally consistent)

### [L10-6] The decision tree's "proof of concept" for topology-as-target overstates what the matched-genus control can show, by the paper's own baseline
- severity: MINOR
- type: new
- anchor: "The matched-genus experiment is the proof of concept: TDA retains 95.83\% where norm/scale features fail (48--58\%)." (§6, branch 6); "the matched pair is still linearly separable in raw coordinates (logistic regression on raw coordinates achieves 100\% at both $\sigma=0.00$ and $\sigma=0.30$)" (§4.2 caveat)
- finding: The decision tree promotes the matched-genus experiment to "the proof of concept" that TDA captures the topological signal, but the paper's own disclosed baseline shows a raw-coordinate linear classifier separates the matched pair at 100\% at both noise levels. The control isolates the norm marginal only; it cannot distinguish "topology is carrying the classification" from "some raw-coordinate geometry is". A steelman reader concludes the experiment shows TDA survives the norm confound (the scoped §4.2 claim) but provides no evidence that topology, rather than linear geometry, is the operative signal — the decision-tree entry claims more than the scoped claim.
- improvement: Rewrite branch 6 as: "the matched-genus experiment shows TDA is robust to the norm/scale confound (95.83\% vs 48--58\%); it does not isolate topology from other raw-coordinate geometry, since the pair is linearly separable in raw coordinates" and mark the branch Grade B rather than using it as proof-of-concept.
- cost: cheap — text edit
- confidence: probable (framing judgement; all numbers paper-reported and verified in bank)

### [L10-7] The paper's own interaction ANOVA makes the filtration×vectorizer interaction the largest single effect in the model — the data support "stages are entangled" at least as well as "vectorizer dominates"
- severity: MINOR
- type: new
- anchor: "the filtration--vectorizer interaction ($\omega^2 = 0.092$) is the \emph{largest single effect in the model}, exceeding the vectorizer main effect ($0.086$); the vectorizer--classifier interaction ($0.089$) rivals it" (§4.1); "the three interaction terms jointly carry $\omega^2 = 0.187$, which is \emph{147\% of the main-effect total} ($0.127$)"
- finding: On ECG200, the largest identifiable effect is NOT the vectorizer main effect — it is the filtration×vectorizer interaction, and interactions jointly outweigh the main effects (147\%). The paper frames this as "an explicit boundary condition", but the steelman reading is stronger: a three-way ANOVA in which the largest single term is an interaction involving filtration does not support "the vectorization stage is the largest single main effect on classification-accuracy variance" as the abstract's answer to "which stage matters most?" — the honest model summary is that stage effects are inseparable, and the vectorizer main effect (0.086) is numerically smaller than two interaction terms.
- improvement: Add one sentence to the abstract/Ch6: "two-way interactions (notably filtration×vectorizer, ω²=0.092) jointly exceed the main effects on ECG200 (ω²=0.187 vs 0.127), so 'which stage matters' is partly a property of the other stages' settings." Optionally report the interaction ω² in Table 4.3's caption.
- cost: cheap — text edits
- confidence: probable (paper-reported; internally consistent: 0.187/0.127 = 1.47)

### [L10-8] Bibliography: three entries misidentify their venues/titles (chung2022 wrong journal; perea2015 wrong title and venue; barnes2021 wrong article number)
- severity: MINOR
- type: new
- anchor: "\bibitem{chung2022} ... \textit{Journal of Machine Learning Research}, 23:1--62, 2022"; "\bibitem{perea2015} Sliding windows and persistence: An overview of topological techniques for time series analysis. In \textit{Applied and Computational Topology}, AMS, 2015."; "\bibitem{barnes2021} ... \textit{Frontiers in Artificial Intelligence}, 4:1--16, 2021"
- finding: Primary-source verification: (1) Chung & Lawson, "Persistence Curves: A canonical framework for summarizing persistence diagrams", was published in Advances in Computational Mathematics 48(1), art. 3, 2022 (DOI 10.1007/s10444-021-09893-4), NOT JMLR. (2) Perea & Harer's paper is titled "Sliding Windows and Persistence: An Application of Topological Methods to Signal Analysis" and appeared in Foundations of Computational Mathematics 15(3):799–838, 2015 (DOI 10.1007/s10208-014-9206-z, arXiv:1307.6188) — both the title and the venue in the bibitem are wrong. (3) Barnes, Polanco & Perea 2021 is Frontiers in Artificial Intelligence 4:681174 (article number, not pages 1–16). Sulowska 2026's journal name carries an en-dash ("Advances in Science and Technology – Research Journal"). Verified OK: adams2017, ali2023, bubenik2015, carriere2020, chazalSilh2014, cohen2007, conti2022 (Mathematics 10(17):3086 + arXiv:2309.15276), dechazal2004, graf2025 (arXiv:2509.22432, NeurIPS 2025), hofer2017, leray1945, rucco2016, somasundaram2021 (5-author list matches R Journal 13(1):184–193), takens1981, tauzin2021, telyatnikov2024, turkes2022, umed2017, kennel1992, fraserswinney1986, dau2019, lecun1998, chazalDesilvaOudot2014.
- improvement: Correct chung2022 (Advances in Computational Mathematics 48:3, 2022), perea2015 (title + FoCM 15(3):799–838, 2015), barnes2021 (4:681174), sulowska2026 (en-dash), and align the perea2022 key with its printed year 2023.
- cost: cheap — bibliography edits
- confidence: certain (all three verified against Springer/arXiv/Frontiers primary pages)

### [L10-9] Missing related work: Pun–Lee–Xia survey and comparative study, TSC-TDA prior work, and an uncited "~75--90%" inter-patient accuracy comparison
- severity: MINOR
- type: new
- anchor: "comparative studies include Barnes et al.\ \cite{barnes2021}, Perea et al.\ \cite{perea2022}, and Sulowska \cite{sulowska2026}" (§2.5); "Our absolute accuracy (27--42\%) is lower than published inter-patient arrhythmia classifiers ($\sim$75--90\%)" (§5.3)
- finding: Two gaps a well-read reviewer would flag. (1) The §2.5 comparative-studies sentence omits Pun, Lee & Xia, "Persistent-Homology-based Machine Learning and its Applications — A Survey" (arXiv:1811.00252; Artificial Intelligence Review 55, 2022) and its comparative-study follow-up ("Persistent-homology-based machine learning: a survey and a comparative study"), the closest direct prior art for vectorizer comparison in classification; it also cites Perea–Munch–Khasawneh (2023) as a "comparative study", which it is not (it is a template-function approximation framework with experiments). (2) The delay-embedding-TSC citations (perea2015, umed2017) omit the TSC-TDA comparison literature (e.g., Seversky et al., ICCS 2016; Karan & Kaygun, ESWA 2021), against which the paper's "TDA does not beat raw features" result could be positioned. (3) The "~75--90%" published inter-patient accuracy figure has no citation.
- improvement: Add Pun–Lee–Xia (and the TSC-TDA entries) to §2.5, recategorise perea2022 ("template-function featurization", not comparative study), and cite a primary source (e.g., de Chazal et al. 2004 results table, or a review) for the 75–90% inter-patient range.
- cost: cheap — 3 citations + one sentence
- confidence: probable (existence of Pun–Lee–Xia and Karan & Kaygun verified via arXiv/Crossref; Seversky et al. 2016 recalled as ICCS/Procedia CS — verify exact venue before adding)

---

## L11 PROSE — readability and style (counts from full 3221-line source, ~490 prose sentences)

### [PROSE-1] Parenthetical-forest sentence pathology: the five worst sentences
- severity: MAJOR
- type: new
- anchor: (count: 5 documented) (1) §3.2 FPS: "We tested whether the choice matters: greedy farthest-point sampling (FPS) was compared against this uniform-random scheme on the synthetic sphere/torus clouds, reduced to $k \in \{50, 15\}$ points (the native clouds carry 100 points, so the runner's \texttt{subsample\_points} knob never fires and the subsampling choice must be made below the native resolution to be nontrivial), under both noise levels and over $\{$...$\} \times \{$...$\} \times \{$...$\}$ (8 configurations per arm, stratified 5-fold CV, seed 42, rep 1; \texttt{fps\_ablation.db})." (2) §4.1 ECG5000: "ECG5000 (UCR archive; 5 classes; 140 timesteps; single patient recording, BIDMC chf07) with the same 5-fold protocol on a stratified subsample of 714 samples ($\le 200$ per class) drawn from the full 5000-sample recording (class counts 2919, 1767, 96, 194, 24; majority class 58.38\% in the full recording; the executed 714-sample subsample is balanced to $\le 200$/class, so its majority share is 28.0\%) and a pipeline subset (2 filtrations, 3 vectorizers, 2 classifiers; ...)" (3) §2.4 stability: "This theorem is applied in \S4.2: for $n$ points with additive Gaussian noise ... (the one-dimensional leading-order value; for the executed $d{=}3$ per-coordinate noise the expectation is larger by the dimension correction, $\approx 1.16\,\sigma\sqrt{2\ln n}$ at $n=100$; Monte Carlo gives $\E[\max_i\|\eta_i\|] \approx 1.06$ at $\sigma=0.30$)." (4) §5.3 B3: "sweeping each of the four vectorizers' key hyperparameter one-parameter-at-a-time over a small grid with all other vectorizer parameters fixed at the manuscript defaults: persistence\_image $\sigma \in \{0.05,0.1,0.2,0.5\}$ and $n_{\textrm{bins}} \in \{10,20,50\}$; persistence\_landscape ..." (5) §4.1 menu: "The sweep comprises 616 completed configurations from a full factorial of 6 dataset instances $\times$ 4 filtrations (Vietoris-Rips, weak Alpha, Sparse Rips, Cubical) $\times$ 7 vectorizers (Persistence Image, Persistence Landscape, Betti Curve, Persistence Statistics, Silhouette, Amplitude, Persistence Entropy) $\times$ 4 classifiers (SVM-RBF, SVM-linear, Random Forest, Logistic Regression) --- 672 possible, 56 runs failed ..."
- finding: The document's default sentence carries 2–4 parenthetical interruptions containing further numbers, so the reader must hold an open clause across 20–90 words of embedded data. Sentence (2) above packs ~7 parenthetical groups and 12 numbers into one sentence; sentence (1) embeds a set-product grid plus a method-justification parenthetical inside the main clause; sentence (3) nests three parenthetical alternatives inside a colon-clause. This is the single largest reading-friction source in Ch4–5, and it clusters exactly in the results sections an examiner reads most carefully.
- improvement: BEFORE (2): "ECG5000 is a second UCR recording (5 classes, 140 timesteps, single patient, BIDMC chf07). From the full 5000-sample recording we drew a stratified subsample of 714 samples, capped at 200 per class (original class counts 2919, 1767, 96, 194, 24; executed majority share 28.0\%). We used the same 5-fold protocol and a pipeline subset of 2 filtrations, 3 vectorizers and 2 classifiers." AFTER keeps every datum but one sentence per fact. BEFORE (3) → "This theorem is applied in \S4.2. For $n$ points with additive Gaussian noise $\eta_i \sim \mathcal{N}(0,\sigma^2 I_3)$, extreme value theory gives the typical maximum perturbation as $\E[\max_i \|\eta_i\|] \approx \sigma\sqrt{2\ln n}$ for the one-dimensional leading order; the executed $d{=}3$ per-coordinate noise raises this by a dimension correction to $\approx 1.16\,\sigma\sqrt{2\ln n}$ ($n=100$), and Monte Carlo gives $\approx 1.06$ at $\sigma=0.30$."
- cost: moderate — ~2 hours of surgical rewrites across ~12 paragraphs
- confidence: certain (verbatim quotes, word counts: sentences of 79, 76, 66, 64, 64 words respectively)

### [PROSE-2] Changelog voice: the paper narrates its own revision history
- severity: MAJOR
- type: new
- anchor: (count: ≥15) "the earlier FPS-future-work note is withdrawn" (§3.2); "we do not find support for the premise underlying the earlier deferral" (§3.2); "the paper's headline 83.0\% configuration" (§4.1); "Notably, the paper's best single-split ECG200 configuration" (§4.1); "the paper says so" (§5.4); "the manuscript's default hyperparameters" (§5.3); plus 17 occurrences of "expansion" — "(expansion \#14)", "(expansion \#11)", "(expansion \#9)", "(expansion \#6 datasets)", "(expansion \#5r closes this)" (§5.2/§5.4) — and the internal labels "B1 sweep" (§5.3), "(B2, panel\_stagecapable.db)", "(B3, hyperparam\_sweep.db)", "(B4, fps\_ablation.db)", "(B5 large-n sweep)" (threats §5.4 and §6)
- finding: The prose repeatedly steps out of the dissertation voice into a project-changelog voice: "the paper says so", "the earlier deferral", "the note is withdrawn", "at the time of writing" (§5.4: "ECG5000 and the panel were single-split at the time of writing (expansion \#5r closes this)"). The "expansion \#N" and B1–B5 codes are internal plan-tracker identifiers that an examiner cannot resolve — they appear in the threats-to-validity section precisely where clarity matters most. The register lurch (formal results prose ↔ project-management memo) forces the reader to re-parse who is speaking.
- improvement: BEFORE: "Per-configuration accuracy varies by 1.09pp on average across the five repetitions ... (expansion \#5r closes this)." AFTER: "Per-configuration accuracy varies by 1.09pp on average across the five repetitions; the single-split panel and ECG5000 analyses are being re-run under the 25-repetition protocol." Replace "the earlier FPS-future-work note is withdrawn" with "uniform random subsampling is therefore retained"; delete or gloss every "expansion \#N" and B-label with its content.
- cost: cheap — ~1 hour of global find-replace + 10 sentence rewrites
- confidence: certain (tallied)

### [PROSE-3] Repeated sentence skeletons: the factorial menu, the stable-ordering claim, and the "dataset-specific and modest" triplet
- severity: MINOR
- type: new
- anchor: (counts) "672 possible" ×3 + "616-configuration" ×3 + "616 completed" ×2 — the menu enumeration recurs ~5× near-verbatim (Abstract; §1.1; Ch1 contributions; §4.1 opening; Ch6); "ordering ... stable across all 25" ×3 (Abstract, contributions, §4.1) plus "stable in all 25 repetitions" (§4.1 repeated-CV); "Filtration effects are dataset-specific and modest on binary MNIST" ×3 (Ch1, §4.1, §5.1) with "dataset-specific and modest" ×5 total; "not an artefact of the norm/scale confound" ×3 (Abstract, contributions, §5.2); "We therefore do not claim that TDA features are competitive" ×2 (Ch4, §5.2)
- finding: The reader hears the rhythm coming: the same full-menu enumeration, the same "ordering stable across all 25 repetitions" claim, and the same three-word qualifier recur at the same sentence positions in the abstract, contributions, chapter openings, and conclusion. Because the repeats are near-verbatim, each instance reads as boilerplate rather than emphasis, and the document loses the "one claim, one best phrasing" effect.
- improvement: BEFORE (§4.1 opening): "The sweep comprises 616 completed configurations from a full factorial of 6 dataset instances × 4 filtrations (Vietoris-Rips, weak Alpha, Sparse Rips, Cubical) × 7 vectorizers (Persistence Image, Persistence Landscape, Betti Curve, Persistence Statistics, Silhouette, Amplitude, Persistence Entropy) × 4 classifiers (SVM-RBF, SVM-linear, Random Forest, Logistic Regression) — 672 possible, 56 runs failed (weak_alpha/sparse_rips on MNIST) and were excluded." AFTER: "The sweep is the full factorial over 6 dataset instances, 4 filtrations, 7 vectorizers, and 4 classifiers (Table 4.1). Of the 672 configurations, 616 completed; the 56 failures are the point-cloud filtrations (weak Alpha, Sparse Rips) applied to image data." Then delete the other four enumerations, citing the first.
- cost: cheap — 1 hour of deduplication
- confidence: certain (tallied)

### [PROSE-4] Word-frequency tics: menu (21), ordering (40), therefore (27), dominat- (20), artefact (20), modest (10)
- severity: MINOR
- type: new
- anchor: (counts) "menu" ×21 — "on the full menu", "vectorizer menu", "filtration menu", "menu-dependent", "menu-distinct"; "ordering" ×40 — "the ordering", "stage ordering", "the raw-menu ordering"; "therefore" ×27 incl. "We therefore" ×6 and the duplicated "We therefore do not claim that TDA features are competitive" (Ch4 §4.1 vs §5.2); "dominat-" ×20 — "dominates/dominant/dominance"; "artefact" ×20 of which ×9 are the construction "not an artefact of X"; "modest" ×10 attached to filtration effects
- finding: "ordering" and "menu" are doing the work of "ranking/relative order" and "set of methods/choices", and their frequency makes the prose self-referential ("the honest reading", "the ordering survives", "menu-distinct"). "Not an artefact of" is the paper's default way of saying "not caused by/explained by", and its 9 uses (artefact of the handicap / level counts / the norm confound / the ECG200 instance / the 128-sample window / the decorative-topology regime / default settings / the norm marginal...) blur distinct claims into one idiom.
- improvement: Replace "ordering" with "ranking" or "relative order" where a specific ranking is meant (~15 sites); replace "menu" with "set of methods" or "candidate set" at first use and keep "menu" only for the contrast it names; rewrite "not an artefact of X" as "not explained by X"/"not caused by X" at 5+ sites. BEFORE: "The ordering survives; the size does not." AFTER: "The ranking survives equal footing; the measured margin does not."
- cost: cheap — 1 hour
- confidence: certain (tallied)

### [PROSE-5] Every chapter closes with the same "Chapter N <verb> ..." preview, and three sections open with rhetorical questions
- severity: MINOR
- type: new
- anchor: (5 instances) "\noindent Chapter~2 develops the mathematical machinery needed to" (line 306); "Chapter~3 translates this mathematical machinery into a software architecture" (789); "Chapter~4 presents the empirical results of this sweep" (957); "Chapter~5 interprets why vectorization dominates on both" (1638); "Chapter~6 synthesizes these findings into a single conditional thesis" (2325); plus question openers "Which stage matters most?" (Abstract, §1.1), "Which pipeline stage contributes the largest variance?" (§4.1), "Does topological signal survive additive spatial noise?" (§4.2)
- finding: The chapter-end move is a fixed skeleton (5 identical constructions), and the rhetorical-question opener is used three times. Both are fine once; five times each, the reader anticipates the pattern, which undercuts the very signposting the previews are for. The §5.4 threats introduction ("The purpose is not to multiply caveats but to make explicit...") shows the author can vary the move — the previews should too.
- improvement: BEFORE: "\noindent Chapter~5 interprets why vectorization dominates on both real datasets and derives operational guidelines from these patterns." AFTER: "\noindent Chapter~5 assembles the mechanism behind the stage effects and converts them into selection guidelines (Table 5.2); Chapter~6 states the resulting conditional thesis." Vary the remaining four by pointing at a specific table/result instead of the generic verb.
- cost: cheap — 30 minutes
- confidence: certain (tallied)

### [PROSE-6] Number-crowding: statistics paragraphs that read as prose tables
- severity: MINOR
- type: new
- anchor: (counts) §4.1 "Beyond accuracy" paragraph packs ~20 statistics into 5 sentences: "the vectorizer AUROC marginal range is 19.38pp (Betti Curve 77.6\%, Silhouette 77.5\%, Persistence Entropy 58.2\%) versus 11.90pp for the classifier and 3.31pp for filtration"; "class 2, 96 samples, 16.3\% recall; class 3, 194 samples, 31.8\%; class 4, 24 samples, 1.7\%, with Betti Curve and Silhouette at 0\%), while the majority classes 0 and 1 are recovered at 73.9\% and 71.8\%"; §5.3 B3 best-tuned paragraph: "The best-tuned hyperparameters are persistence\_image $\{\sigma{=}0.5,\, n_{\textrm{bins}}{=}20\}$, persistence\_landscape $\{n_{\textrm{layers}}{=}5,\, n_{\textrm{bins}}{=}50\}$ (ECG200) / $\{n_{\textrm{layers}}{=}1,\, n_{\textrm{bins}}{=}50\}$ (MNIST), silhouette $\{n_{\textrm{bins}}{=}50\}$ (ECG200, already default) / $\{n_{\textrm{bins}}{=}100\}$ (MNIST), and betti\_curve ..." (a table written as a sentence); §5.3 MixedLM paragraph: 12 numbers in 4 sentences
- finding: In each of these paragraphs the key claim (vectorizer dominance under AUROC; tuning contracts the range; the population ordering) is surrounded by so many companion statistics that the claim does not land on first read — the reader must choose which number is the finding. The B3 best-tuned sentence is the worst case: a 6-cell grid serialised inline.
- improvement: Keep one number per sentence: "The vectorizer AUROC range (19.38pp) again exceeds the classifier (11.90pp) and filtration (3.31pp) ranges (Table X)." Move the per-class recall block and the best-tuned hyperparameter grid to tables; in the text keep "tuning lifts the weakest vectorizers (persistence\_image 70.75 → 73.00\%) rather than the leader".
- cost: cheap — 1–2 hours, mostly table extraction
- confidence: certain (counted)

### [PROSE-7] LaTeX leak: the Filt bullet in §3.1's pipeline list lost its \item — the four-stage pipeline renders as three labelled bullets
- severity: POLISH
- type: new
- anchor: "Constructs a filtration $\{K_\varepsilon\}$ from $Y$ and computes the persistence diagram $\mathcal{D} = \Dgm_0 \cup \Dgm_1$ (homology dimensions 0 and 1). Implemented via giotto-tda's VietorisRipsPersistence, WeakAlphaPersistence, SparseRipsPersistence, or CubicalPersistence transformers." (§3.1, lines 840–845)
- finding: In the itemized list of the four pipeline mappings (eq:pipeline_map: Embed → Filt → Vec → CLF), the Filt description has no \item command: the text is orphaned inside the itemize and renders as an unlabelled continuation of the Embed bullet. The printed list therefore shows three bold labels (Embed, Vec, CLF) for a four-stage pipeline, exactly where the paper defines its core object. This is a genuine rendering defect, not a style choice.
- improvement: Insert "\item \textbf{Filt}. " before "Constructs a filtration" (line 840).
- cost: cheap — one-line fix
- confidence: certain (read directly in source; verified \item count: the list has 3 \item for 4 stages)

### [PROSE-8] Spelling and notation drift: artifact/artefact, H0/$H_0$, undefined PI/PL abbreviations
- severity: POLISH
- type: new
- anchor: "This is not a single-split artifact:" (§4.1, line 1187) vs 21× "artefact" elsewhere (e.g., §4.1 "not an artefact of level counts"); "H0-only naive cubical-binary pipeline" (Abstract, §1.1, §5.1 — 3× "H0") vs "$\Betti_1 = 0$" notation used elsewhere; "11 vectorizers (PI, PL, Betti, Silhouette, Entropy, ...)" (Appendix D) — "PI"/"PL" are never expanded anywhere in the document
- finding: One US spelling ("artifact") among 21 British "artefact"s; plain-text "H0" for the homology-dimension-0 subscript that is otherwise typeset as $\Betti_0$/$H_0$; and Appendix D introduces the abbreviations PI and PL (Persistence Image, Persistence Landscape) which appear nowhere else — the body always spells them out, so a reader meeting "PI, PL" in Appendix D cannot resolve them from the document.
- improvement: "artifact" → "artefact"; "H0-only" → "$\Betti_0$-only" (or "$H_0$-only") in all three sites; expand "(PI, PL" → "(Persistence Image, Persistence Landscape" in Appendix D.
- cost: cheap — 5 minutes
- confidence: certain (tallied)

---

## READER'S VERDICT (L11)
Reading pages 20–35 (the §4.1 stretch: stage-variance analysis through ECG5000, beyond-accuracy, cubical ablations) cold, the honest experience is: each paragraph states its claim in the first sentence, then buries the reader under parentheticals and companion statistics before the claim is allowed to resolve. The numbers are almost always the right numbers — the friction is structural, not factual: sentences of 60–90 words with 3–6 embedded (like this) (and this) (with these numbers) groups, a recurring "the ordering... the menu... the artefact..." vocabulary, and the occasional changelog voice ("the earlier deferral", "expansion #11"). A tired examiner can still extract the headline per section, but rarely the magnitude that qualifies it. The single highest-leverage habit to break: **one clause, one parenthetical, one number per sentence** — when a sentence needs a second parenthetical, it needs a second sentence; when it needs a third number, the numbers belong in a table.

## VERDICT (L10+L11)
The paper is NOT submission-ready on this lens cluster as it stands, but it is close, and nothing here threatens the data layer. On L10, the steelman-reversal lands on framing, not facts: every counter-argument (level-matched reversal on 2 of 3 real datasets, a surviving ECG200 edge of 0.52pp inside the paper's own 1.09pp noise floor, the population-level MixedLM ranking vectorizer last, interactions exceeding main effects, Betti's 5th-of-7 on the only 25-rep dataset) is constructed from the paper's own reported or DB-verified numbers — the paper's honesty is precisely what makes it vulnerable, and the front matter (abstract, Ch6, decision tree) has not caught up with the body's own corrections. The single highest-leverage fix: rewrite the abstract and decision tree so the "vectorization dominates" headline carries its corrections in the same breath — report the MNIST best-2 reversal (5/5 reps) alongside the ECG5000 reversal, state that the level-matched ECG200 margin (0.52pp) is below the per-config noise floor, and demote the "tune the vectorizer" Grade-A branch with one sentence citing the MixedLM population ordering. On L11, the parenthetical-forest habit (PROSE-1) is the one change that would transform the reading experience of Ch4–5; the changelog voice (PROSE-2), the missing \item (PROSE-7), and the three bibliographic errors (L10-8) are cheap and should be fixed before any external reader sees the document. Cost to resolve all 17 findings: ~half a day of writing/editing, zero new compute.
