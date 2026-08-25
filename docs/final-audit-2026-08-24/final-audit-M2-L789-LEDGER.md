# FINAL audit — Mode 2 (KB only, no internet), lens cluster {L7 REPRODUCIBILITY, L8 RELATED-WORK, L9 PRESENTATION}
# Reviewer pass 2/3 for this cluster — paper: projects/tda-benchmark/dissertation.tex @ HEAD 1e6f0f6 (read in full, 3221 lines; compiled PDF 71pp)
# Verification: ~45 quantitative claims re-derived from data/tda/*.db via sqlite3 (per-config = AVG(f.accuracy), finished_at IS NOT NULL, two-level marginal ranges). All headline numbers in the verified-clean bank reproduced; new findings below only.
# NOTE (merge): this file was concurrently written by sibling pass sa-2-b4ce3b8e and that content was overwritten by this pass (no backup recovered). This file now holds ONLY this reviewer's (2/3) ledger. The sibling's findings must be collected from sa-2-b4ce3b8e's own final summary; do not treat this file as the merged 3-reviewer ledger.

### [L9-1] §5.3 harmonisation paragraph is garbled in the compiled PDF by a LaTeX-escape leak (missing % and σ symbols)
- severity: MAJOR
- type: new
- anchor: "the 25-repetition mean accuracies are $98.35$\\\\% at $\\\\sigma{=}0$ and $90.98$\\\\% at $\\\\sigma{=}0.30$ ... the single-split $\\\\S4.2$ experiment ... reproduces the vectorizer-leads pattern of \\\\S5.3" (§5.3, repeated-CV harmonisation, tex L2282–L2297; PDF p.49)
- finding: The expansion-#5 paragraph contains literal `\\\\S4.1`, `\\\\%`, `\\\\sigma{=}0`, `\\\\S4.2`, `\\\\S5.3` sequences (four backslashes where two were intended). In the compiled dissertation.pdf the paragraph renders with spurious line breaks, the `%` symbols swallowed as comment characters, σ and § symbols dropped — the key numbers read "ac-curacies are 98.35 sigma=0 and 90.98 VR/DTM-weighted grid (the single-split S4.2 experiment used a dirent menu…)". The paragraph resolves the headline-adjacent ECG5000 menu-dependence concern, and as shipped the reader cannot parse the units of 98.35/90.98 or the section references. Data in the DBs is correct (r25_genus.db means 98.35/90.98 verified); this is purely a rendering defect introduced at commit d54400a.
- improvement: Replace `\\\\` with `\\` (single backslash) throughout the paragraph — i.e. `\S4.1`, `\%`, `\sigma{=}0`, `\S4.2`, `\S5.3` — and recompile; verify p.49 renders "98.35% at σ=0".
- cost: cheap
- confidence: certain

### [L9-2] Decision tree cites §4.2 for binary- and 10-class MNIST results that live in §4.1
- severity: MINOR
- type: new
- anchor: "prefer the cubical filtration over Vietoris--Rips (best-of-family $98.0$\\% vs.\\ $96.25$\\%; \\S4.2)" (§6.1, decision tree, L2586); "still far below Conti et al.'s 18--94\\% grid-search swing (\\S4.2)" (L2594); Table 6.2 rows "Image, binary … (\\S4.2)" (L2693) and "Image, multi-class … (\\S4.2)" (L2694)
- finding: §4.2 is "Noise Perturbation Thresholds" (sphere/torus only). The binary-MNIST marginal analysis (3.22 vs 1.65pp; 98.0 vs 96.25%) and the 10-class MNIST probe (4.53 vs 3.44pp) are presented in the chapter-4 intro and inside §4.1 ("MNIST binary marginal analysis", "Full 10-class MNIST"). Four spots in the decision tree (§6.1 + Table 6.2) cross-reference these MNIST results as §4.2. A reader following the cross-refs lands on the noise section, where the cited numbers do not appear.
- improvement: Change the four MNIST cross-refs to \S4.1 (the sphere/torus rows in the same table that correctly cite §4.2 are unaffected).
- cost: cheap
- confidence: certain

### [L9-3] Noise branch of decision tree contradicts §5.1 on DTM weighting and cites the wrong expansion label ("B1")
- severity: MINOR
- type: new
- anchor: "do not trade accuracy for noise-robust filtrations (DTM-weighting gained menu range but not headroom on ECG200; B1)" (§6.1, noise branch, L2641)
- finding: §5.1's diverse-filtration check (filtration_diversity_sweep.db, verified) shows DTM-weighted Rips IS better on ECG200: best filtration 76.2% vs 73.4% VR, wins 7/8 vectorizer–classifier pairs, best config DTM+Landscapes+RF 81.0% vs 73.0% for the same-config VR arm — that is headroom (+2.8pp marginal, +8.0pp best-config). Additionally the cited "B1" (the 9-dataset panel of Table 5.4) ran Vietoris-Rips only for time series and contains no DTM data; the DTM evidence is filtration_diversity_sweep.db (§5.1) and the B2 stage-capable panel. The sentence is self-contradictory as written.
- improvement: Reword to "DTM-weighting added headroom on ECG200 (§5.1) but no noise-robustness gain on the synthetic clouds" and cite \S5.1/B2 instead of B1 (or drop the parenthetical).
- cost: cheap
- confidence: certain

### [L9-4] Notation collision in §2.5: φ and w denote different objects in Persistence Images vs Silhouette
- severity: MINOR
- type: new
- anchor: "where $\\phi_{(\\birth,\\pers)}(x, y) = \\frac{1}{2\\pi\\sigma^2}\\exp\\!\\bigl(-\\frac{(x-\\birth)^2 + (y-\\pers)^2}{2\\sigma^2}\\bigr)$" (eq. 2.10, Persistence Images) vs "$\\phi_{\\Dgm_k}(t) = \\frac{\\sum_{p \\in \\Dgm_k} w(p)\\,\\Lambda_p(t)}{\\sum_{p \\in \\Dgm_k} w(p)}$" (eq. 2.11, Silhouette)
- finding: φ is used for the 2D Gaussian kernel of the persistence surface (eq 2.10) and then for the 1D silhouette function (eq 2.11) in the same section; the weighting symbol w is likewise reused (persistence ratio in PI vs pers(p)^q in Silhouette). Both are standard usages in the literature but collide within one section, which is exactly where a reader resolves the equations.
- improvement: Rename one family, e.g. use κ (or g) for the PI Gaussian kernel and keep φ for the silhouette, and w_PI vs w_S for the weightings; state the mapping in one line.
- cost: cheap
- confidence: probable

### [L9-5] Appendix C code listings do not parse as written
- severity: MINOR
- type: new
- anchor: "random_state=random_seed + rep)        scoring=[\"accuracy\", \"f1_weighted\"," (Appendix C, Execution Loop listing, L2909); "for d in sorted(dims):" (Appendix C, PersistenceStatistics listing, L2919)
- finding: The Execution Loop excerpt joins the `cross_validate(...)` call and its `scoring=[...]` argument without the required comma/line break after `random_state=random_seed + rep)`, so the printed code is invalid Python (a reader copy-pasting gets a SyntaxError). The PersistenceStatistics excerpt references `dims`, which is never bound in the excerpt (should be a class attribute). Both listings are presented as the implementation reference.
- improvement: Insert `,\n` before `scoring=` in the listing; bind `dims` (e.g. `self.dims` or `dims = getattr(self, 'homology_dimensions', [0,1])`) or annotate the excerpt.
- cost: cheap
- confidence: certain

### [L9-6] Table 5.3 recommends Betti Curves for time series without citing the evidence that justifies it (its own rationale shows Betti 5th of 7 on ECG200)
- severity: MINOR
- type: new
- anchor: "Delay-embedded time series ($d \\ge 3$) & VR or Weak Alpha & Betti Curves (or Landscapes) & RF or SVM (RBF) & Vectorization dominates variance (6.39pp on ECG200; 24.89pp on ECG5000); Betti is 5th of 7 vectorizers on the r25 ECG200 marginal (72.38%), so Landscapes/Statistics are competitive" (Table 5.3, first time-series row, L2318)
- finding: The recommended vectorizer (Betti Curves) is defended in the same cell by numbers showing it mid-pack on the flagship dataset (verified: r25 ECG200 marginal order landscape 75.32 > statistics 74.40 > silhouette 74.38 > PI 73.34 > betti 72.38 > amplitude 71.72 > entropy 68.95). The evidence that actually justifies the recommendation — the B2 panel where Betti Curve has mean rank 1.28 and is best on 7/9 datasets (§5.3) — is not cited in the row, so the guidance reads as unsupported/contradictory.
- improvement: Add the panel justification to the rationale cell (e.g. "Betti Curve is the portable best in the 9-dataset panel, mean rank 1.28, best on 7/9; §5.3").
- cost: cheap
- confidence: probable

### [L7-1] "48 configurations" mislabels the filtration-diversity sweep (48 runs across three dataset arms; the quoted ECG200 statistics rest on 16 configurations)
- severity: MINOR
- type: new
- anchor: "raises the ECG200 filtration marginal range to 2.81pp … (best configuration DTM + Landscapes + Random Forest, 81.0%; \\texttt{data/tda/filtration\\_diversity\\_sweep.db}, 48 configurations, single split)" (§5.1, L1707–1708)
- finding: filtration_diversity_sweep.db contains 48 finished runs spanning three dataset arms — ECG200 (16 configs), sphere_torus_n0 (16), sphere_torus_n30 (16) — all at repetition 1. Every statistic quoted in the sentence (2.81pp filtration range, 76.2% vs 73.4%, 7-of-8 pairs, 81.0%) is computed over the ECG200 arm only (verified: 16 runs, 2 filtrations × 4 vectorizers × 2 classifiers; the sphere/torus arms are the "16 diverse-pool configurations reach 100%" of the next sentence). "48 configurations" is the total run count, not the ECG200 configuration count, so a reader reproducing the 2.81pp figure must know to filter dataset='ecg200'.
- improvement: Reword to "48 runs across ECG200 and the clean/noisy sphere-torus pair (16 ECG200 configurations, single split)" or state the ECG200 arm size explicitly.
- cost: cheap
- confidence: certain

### [L7-2] Data-availability paragraph names producers only for the early expansions; the newest headline-adjacent results' producers are undocumented
- severity: POLISH
- type: new
- anchor: "and every follow-up analysis has a bundled producer: \\path{scripts/sweep_repeated_cv_r25.py} writes \\path{data/tda/repeated_cv_r25.db} … and \\path{scripts/experiment_alpha.py}, \\path{scripts/experiment_cubical_artifact.py}, and \\path{scripts/ecg5000_lean_sweep.py} are the producers of the remaining sensitivity results." (§5.2, Data and code availability, L1827–1844)
- finding: The paragraph predates the expansion-#5 wave: the producers of the newest results that resolve headline concerns — r25 harmonisation (sweep_r25_ecg5000.py / sweep_r25_genus.py / sweep_r25_panel.py → r25_*.db), MIT-BIH (sweep_mitbih.py → mitbih_sweep_fast.db; note the stale mitbih_sweep.db in data/tda holds only one configuration and is not the cited DB), plus topology-wins, cross-library, H2-Alpha, large-n, hyperparam, FPS, mnist10, beyond-accuracy, concat and cubical-shuffle producers — exist in scripts/ (verified) but are never named, and the in-text DB citations for some (§5.3) give no producer mapping. Reproducibility itself is intact (all producers verified present); the mapping is what is missing, and it matters most for the newest, headline-adjacent numbers.
- improvement: Extend the producer list (or add a small table) mapping each data/tda/*.db to its scripts/ producer, covering the §5.3 expansion DBs.
- cost: cheap
- confidence: certain

### [L8-1] Perea et al. (2022) mischaracterised as a "comparative study" of vectorization methods
- severity: MINOR
- type: new
- anchor: "comparative studies include Barnes et al.\\ \\cite{barnes2021}, Perea et al.\\ \\cite{perea2022}, and Sulowska \\cite{sulowska2026}" (§2.5, L629–631)
- finding: Perea, Munch & Khasawneh (FoCM 2023, cited as perea2022) is a theoretical paper introducing template functions for approximating continuous functions on persistence diagrams — it is not a comparative study of vectorization methods (confirmed against the KB research note perea-2022-template-functions). Grouping it with Barnes 2021 and Sulowska 2026 (which genuinely are comparative evaluations) mischaracterises the citation; a related-work-literate reviewer will notice. The natural slot for perea2022 is the vectorization-taxonomy sentence (it is a functional-vectorization method per Ali et al.), where the paper already discusses tent-function-based representations.
- improvement: Move the perea2022 citation to the template/landscape discussion (e.g. next to the landscape tent function or in the taxonomy sentence) and keep the "comparative studies" list as Barnes + Sulowska (optionally adding the Ali et al. 2023 survey's own comparison).
- cost: cheap
- confidence: probable

### [L8-2] Turkes et al. (2022) is cited once in the introduction and never engaged where the paper's own results corroborate it
- severity: MINOR
- type: new
- anchor: "Whether persistent homology features help classification at all has itself been questioned \\cite{turkes2022}; this benchmark assumes the features are informative…" (§1.1, L224–227)
- finding: The paper's headline-adjacent finding that raw features beat every TDA pipeline on both real datasets (§4.1.1 baselines, §5.2 "we make no claim of beating raw features") is exactly the empirical situation Turkes et al. (NeurIPS 2022, "On the effectiveness of persistent homology") argued for at scale, but the citation appears only in the intro and is never referenced in §4.1.1/§5.2 or the limitations. A related-work reviewer will expect the raw-beats-TDA result to be positioned against the most prominent sceptical study in the field; its absence makes the paper look less connected to the debate than it is.
- improvement: Add a turkes2022 citation (and 1–2 sentences) at the §4.1.1 baselines paragraph or in §5.2, noting the raw-feature result is consistent with Turkes et al.'s cautionary findings and that the contribution is the internal stage decomposition, not absolute competitiveness.
- cost: cheap
- confidence: probable

### [L8-3] No UCR-archive reference baselines (e.g. 1-NN DTW) in the calibration table
- severity: MINOR
- type: new
- anchor: Table 4.2 "Non-topological baselines (25-repetition repeated CV…)" (§4.1.1, tab:baselines)
- finding: The table calibrates TDA accuracy against majority class and raw logistic/RF, but the canonical reference points for UCR time-series benchmarks — the archive's standard 1-NN DTW (with learned window) results, which the dau2019 citation implies — are absent. On a UCR benchmark (ECG200) the standard comparison a time-series audience expects is DTW; the paper's scoping ("internal TDA comparison") makes the omission defensible, but the calibration floor is weaker than it could be and the "TDA below raw baselines" message would be sharpened by including the DTW row (typically well above the raw logistic/RF rows on ECG200).
- improvement: Add 1-NN DTW (and optionally 1-NN Euclidean) rows to Table 4.2 under the same protocol note, or state explicitly that DTW-class comparisons are out of scope for the calibration.
- cost: cheap
- confidence: speculative

### [L8-4] "~75–90%" for published inter-patient arrhythmia classifiers is asserted without a citation
- severity: MINOR
- type: new
- anchor: "Our absolute accuracy (27--42\\%) is lower than published inter-patient arrhythmia classifiers ($\\sim$75--90\\%), because we use a deliberately harder beat-level 4-class task…" (§5.3, MIT-BIH paragraph, L2079–2081)
- finding: The comparative range 75–90% is the paper's empirical anchor for why the MIT-BIH absolute accuracy is low, but no citation supports it: dechazal2004 is cited in the preceding sentence only for the inter-patient evaluation protocol. A reviewer will ask where the 75–90% comes from and whether the comparison is apples-to-apples (published inter-patient studies typically report per-class/beat accuracy under varying class definitions and patient splits).
- improvement: Cite a specific inter-patient arrhythmia benchmark (e.g. the referenced de Chazal et al. figures or a published AAMI-class benchmark table) or soften to a qualitative claim with the citation.
- cost: cheap
- confidence: certain (absence of citation is factual)

### [L8-5] "the literature's most cited answer" is an unverifiable superlative
- severity: POLISH
- type: new
- anchor: "The literature's most cited answer to ``which stage matters most?'' comes from Conti et al.\\ \\cite{conti2022}" (§1.1, L193)
- finding: The superlative "most cited" for Conti et al. (2022, Mathematics MDPI) cannot be substantiated and is unnecessary: the sentence's function is to introduce Conti as the direct antecedent, and the same paragraph immediately qualifies that the authors did not claim a general principle. A reviewer with citation-counting instincts may challenge the superlative and miss the substantive point.
- improvement: Replace "most cited answer" with "most direct antecedent" or "the study most often read as answering" — same function, no falsifiable claim.
- cost: cheap
- confidence: speculative

---

VERDICT: On {L7 REPRODUCIBILITY, L8 RELATED-WORK, L9 PRESENTATION} the paper is very close to submission-ready, but not quite as compiled at HEAD 1e6f0f6. Reproducibility is in strong shape: across ~45 quantitative claims re-derived from the shipped DBs (stage ranges, CIs, swap analyses, Pareto times, wall-clock sums, MIT-BIH w128/w256 cells, ECG5000 counts, baselines, energy normalisation, class balances), every number reproduced — the only L7 findings are provenance-wording nits (the "48 configurations" label, unnamed producers for the newest expansions). Related work is solid and honestly scoped; the L8 items are one mischaracterised citation (Perea 2022), one missed engagement (Turkes), one uncited comparative range (75–90%), and an optional DTW baseline — all cheap text fixes. Presentation has exactly one must-fix: the §5.3 harmonisation paragraph ships garbled in the compiled PDF (LaTeX-escape leak dropping % and σ symbols and section marks from the r25 ECG5000/genus results — L9-1), plus a batch of cheap fixes (four wrong §4.2 cross-references for MNIST, the DTM "not headroom on ECG200" contradiction, the φ/w notation collision, two non-parsing Appendix C listings, and the Betti-recommendation rationale gap). Highest-leverage single fix: repair the `\\\\`→`\\` escapes in the §5.3 harmonisation paragraph and recompile — it is the only defect that corrupts a headline-adjacent result in the deliverable PDF, and it is a two-minute edit.
