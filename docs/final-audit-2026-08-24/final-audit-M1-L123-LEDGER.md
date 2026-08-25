# FINAL AUDIT — Mode 1 (KB + internet + deep research) — Lens cluster {L1 DESIGN-CONFOUNDS, L2 STATS, L3 EVIDENCE-STRENGTH}
Paper: tda-benchmark dissertation.tex @ HEAD 1e6f0f6 (3221 lines, read in full). DBs re-derived read-only per brief conventions (per-config = AVG(f.accuracy) per run_id, finished_at IS NOT NULL, stage-level means). KB audit history consulted (wave-0..4 notes). Deep citation verification against primary sources on the web.
Date: 2026-08-24. Auditor: subagent M1-L123.

---

### [L1-1] §5.1 mechanism overstates what the Takens embedding "captures" — the measured H1 of the embedded clouds is noise-born, so the near-zero filtration range is partly a design artefact, not a discovered fact
- severity: MINOR
- type: new
- anchor: "The embedding captures the dynamical structure; the filtration merely reads it out." (Ch. 5, §5.1 "Why Vectorization Dominates on Both Datasets")
- finding: With d=3, τ=1 on 96-sample ECG200 heartbeats the pipeline feeds a 94-point 1-D curve in R³ into the filtrations. I measured the diagrams directly (ripser on 5 sampled clouds, same Takens parameters): each cloud yields 14–26 H1 features with max persistence 0.11–0.64 — short-lived, noise-born features of a discretized curve, not attractor topology (the paper itself declines to assert Takens' d>2d_M condition, §3.1). Because all three Rips-type filtrations read near-identical noise-dominated diagrams, the filtration stage is near-inert *by construction* on this data (0.69pp range), and the vectorizer stage's dominance on time series is substantially a statement about how each vectorizer encodes a noisy near-empty diagram. The paper's own diverse-filtration check (DTM raises the filtration range to 2.81pp) and topology-wins results (filtration 1.04–5.10pp where real structure exists) confirm the mechanism, but the §5.1 "reads it out" sentence asserts the conclusion without stating the trivial-diagram premise.
- improvement: Add one diagnostic sentence to §5.1 reporting the embedded clouds' H1 feature structure (counts/persistence, computed with the shipped ripser) and state explicitly that on delay-embedded 96-sample heartbeats the filtration's output is noise-dominated, so "filtration barely matters" here is a regime property; then note the DTM/topology-wins results as the counter-regime. ~5 lines + a 10-line script; no new sweeps.
- cost: cheap
- confidence: probable (H1 measured on 5 sampled clouds; the "noise-born, not class-informative" inference is standard for curves in R³ but not class-correlation-tested)

### [L1-2] Panel time-series arm: random uniform subsampling of long series (500→100, 152→100, 2709→100) caps the panel's time series at ~100-point clouds, and HandOutlines is precisely where the ordering flips
- severity: MINOR
- type: new
- anchor: "Long series were pre-subsampled to 100 points with a fixed-seed uniform draw (seed 42); this was necessary because the runner's subsample_points knob fires only on 3-D point-cloud input and never caps 2-D series" (§5.3, Multi-Dataset Generalisation)
- finding: Four of the seven panel time series (FordA/FordB 500→100, Wafer 152→100, HandOutlines 2709→100) are reduced to ~98 embedded points (3.7% of HandOutlines' samples). The disclosure explains the mechanism but not the consequence: the panel's "time series" arm measures TDA on heavily undersampled curves whose fine structure is gone, so the panel's vectorizer-portability claim (Betti best on 7/9) is partly a statement about coarse-resolution inputs; HandOutlines — the most aggressively subsampled series — is exactly the dataset where the panel's ordering flips (filtration 4.22pp > vectorizer 1.90pp, verified in panel_stagecapable.db). The stage-dominance comparison across the panel is thus confounded with the subsampling ratio (each dataset has a different retained fraction).
- improvement: Either (a) report the retained fraction per dataset in Table 5.2 and note the confound, or (b) re-run the two most-subsampled series at a fixed higher cap (e.g. 300–500 points) to test whether the panel ordering survives resolution; one sentence now, an optional cheap re-run later.
- cost: cheap (text); moderate (optional re-run)
- confidence: probable (subsampling ratios verified from the paper's own table; the causal reading is an interpretation)

---

### [L2-1] Nemenyi critical difference is computed with 12N instead of Demšar's 6N — CD should be 3.50, not 2.48, and the "Betti-to-Landscape gap exceeding the CD" claim fails
- severity: MAJOR
- type: new
- anchor: "the Nemenyi critical difference is 2.48 mean rank units" and "with a Betti-to-Landscape rank gap exceeding the critical difference" (§5.3); "Nemenyi critical-difference diagram … The bracket marks the CD at α=0.05" (Fig. 5.1 caption); producer: scripts/analysis_multidataset_friedman.py line 129: `cd = q_alpha * np.sqrt(n_cfg * (n_cfg + 1) / (12 * n_ds))`
- finding: The script implements CD = q·√(k(k+1)/(12N)). Demšar (2006), "Statistical Comparisons of Classifiers over Multiple Data Sets", JMLR 7:1–30 (primary source extracted from jmlr.org PDF), defines CD = q_α·√(k(k+1)/(6N)). With k=8, N=9, q_{0.05,8}=3.031 (Demšar Table A3), the correct CD is 3.50; the paper's 2.475 is √2 too small. Consequences, re-derived from data/tda/multidataset_nemenyi.csv: (a) the Betti-to-Landscape rank gap (6.25−2.83 = 3.42) does NOT exceed the correct CD (3.50) — the §5.3 significance claim "Betti-to-Landscape gap exceeding the critical difference" fails; (b) the CD diagram's bracket is too tight — under CD=3.50, VR+Betti+SVM (mean rank 4.389, gap 3.11 from best 1.278) is no longer significantly worse than the best, so the set of "significantly worse" configurations changes (5 of 7 → 4 of 7); (c) "separated from the four weakest configurations by more than the CD" survives only marginally (smallest gap 3.61 > 3.50). The Friedman omnibus χ²(7)=32.41 and Iman–Davenport F=8.47 are unaffected (formula verified correct). Note for the record: prior audit waves (KB wave-0) corrected the q value (3.163→3.031) and tie-averaged ranks but never checked the denominator against Demšar; the brief's verified-clean bank replicates the paper's own convention, so this is a new finding about the convention itself.
- improvement: Fix the script (`12 * n_ds` → `6 * n_ds`), regenerate CD = 3.50, re-derive the §5.3 post-hoc statements and Fig. 5.1; replace "with a Betti-to-Landscape rank gap exceeding the critical difference" with the (still true) descriptive ordering + note the gap is within the CD, or run a more powerful post-hoc (Bergmann–Hommel/García–Herrera) if significance is wanted.
- cost: cheap
- confidence: certain (formula verified against the Demšar 2006 PDF primary source; all ranks re-derived from the CSV)

### [L2-2] Chapter-6 conclusion misattributes the 25-repetition protocol to the single-split TDA baseline numbers
- severity: MINOR
- type: new
- anchor: "TDA features do not beat raw features on the datasets studied (raw-signal logistic 85.28% vs.~83.0% TDA on ECG200 under the 25-repetition protocol; raw-pixel logistic 99.65% vs.~98.0% TDA on MNIST)" (Ch. 6, Conclusion)
- finding: The 83.0% and 98.0% TDA figures are single-split point estimates (the 83.0% configuration's own r=25 mean is 79.6%, rank 3–4; §4.1), while 85.28% and 99.65% are 25-repetition means. "Under the 25-repetition protocol" grammatically covers the whole comparison, so the conclusion overstates TDA's repeated-CV performance by ~3.4pp on ECG200. §4.1.1, §5.2, and the decision tree label the same numbers correctly ("83.0% (single-split best)"), so this is a single-site framing slip in the most-read paragraph of the dissertation.
- improvement: Either "(raw-signal logistic 85.28% vs. 83.0% single-split TDA on ECG200; raw-pixel logistic 99.65% vs. 98.0% single-split TDA on MNIST)" or quote the r25 means (79.6% vs. 85.28/86.30).
- cost: cheap
- confidence: certain (r25 mean 79.6% re-verified in repeated_cv_r25.db via the equal-footing analysis)

### [L2-3] The per-config ANOVA panel shares the non-independence the Table 2 footnote attributes only to the fold-level panel
- severity: MINOR
- type: new
- anchor: "the fold-level panel of that table is descriptive only, as folds within a configuration share training data, so its p-values are anti-conservative" (Table 2 footnote, §4.1); "The variance decomposition of Table 2 is the primary evidence for this ordering" (§4.1)
- finding: The per-config panel (one mean per configuration; N=112 ECG200 / N=56 MNIST) treats 112 configurations evaluated on the SAME 200/400 samples as independent observations. Configurations share sampling noise (a hard split drags every configuration's mean down), so the per-config F/p values are also anti-conservative — the footnote's implied contrast (fold-level untrustworthy, per-config trustworthy) overstates. The effect sizes (η²) and the Friedman/sign-test corroboration on repetition-level orderings carry the claim, so the conclusion is unaffected; this is a labeling/transparency issue on the primary evidence table.
- improvement: Extend the footnote: "per-config means also reuse the same samples across configurations; their p-values are likewise anti-conservative — η² and the repeated-CV corroboration are the robust quantities."
- cost: cheap
- confidence: probable (dependence is structural; its magnitude on per-config means is smaller than at fold level but nonzero)

### [L2-4] Abstract juxtaposes the r=25 marginal range with a single-split η² without attribution
- severity: MINOR
- type: new
- anchor: "it has a marginal range of 6.39pp across 7 vectorizers (95% CI [6.13, 6.65]; η² = 0.217)" (Abstract); Table 2 footnote: "the 18 F-tests … were recomputed from data/tda/expanded_results.db"
- finding: The 6.39pp range and its CI are the r=25 repeated-CV quantities (Table 1), but η² = 0.217 is the per-config ANOVA on the single-split sweep (expanded_results.db, per Table 2's own footnote; the r25 sweep has 84 configurations with Sparse Rips dropped). Presenting them in one parenthetical without attribution mixes protocols; the paper elsewhere computes the design-penalised ω² from the 25-repetition sweep (0.165, Table 2 text), so the machinery exists to make the abstract internally coherent.
- improvement: Attribute the η² ("single-split η²") or recompute η² from the r25 per-config means and update the abstract/Table 2 accordingly.
- cost: cheap
- confidence: certain (both quantities re-derived; protocol sources confirmed from the footnotes)

### [L2-5] Appendix D text says 9.63pp where its own table (and the DB) say 9.62pp
- severity: POLISH
- type: new
- anchor: "the classifier is the largest stage (3.88--9.63pp; driven by SVM-RBF collapsing to the 66.5% majority class on Persistence Entropy features)" (Appendix D) vs Table D.1 row (3,1) "9.62pp"
- finding: Re-derived from takens_sweep.db: the (d=3, τ=1) classifier stage-level range is exactly 9.62pp (all nine table rows match the DB to 0.01pp). The prose's 9.63 is a one-digit typo.
- improvement: 9.63 → 9.62.
- cost: cheap
- confidence: certain

---

### [L3-1] ECG5000 macro-F1 "0.50–0.51" is the best-classifier-cell value, not the vectorizer marginal (0.43–0.45) — same sentence's balanced-accuracy numbers ARE marginals
- severity: MINOR
- type: new (previously raised in wave-1 audit as a 1-of-3 unresolved item; still in the paper)
- anchor: "balanced accuracy per vectorizer is 0.46--0.47 (Betti Curve, Silhouette) versus 0.28 (Persistence Entropy) and macro-$F_1$ 0.50--0.51 versus 0.12--0.38" (§4.1, Generality probe: ECG5000)
- finding: Re-derived from beyond_accuracy_ecg5000.db: balanced-accuracy vectorizer marginals are Betti 0.462 / Silhouette 0.469 / Entropy 0.281 — the "0.46–0.47 vs 0.28" is a fair marginal comparison. But macro-F1 marginals are Betti 0.430 / Silhouette 0.448 / Entropy 0.28; "0.50–0.51" matches only the Random-Forest cells (Betti+RF 0.506, Silhouette+RF 0.498). The sentence therefore switches from marginal means (balanced accuracy) to best-cell values (macro-F1) mid-sentence, flattering the vectorizer contrast, while entropy's "0.12–0.38" is the full cell range.
- improvement: Report the marginal means ("macro-F1 0.43–0.45 versus 0.28") or label the F1 numbers "best-config".
- cost: cheap
- confidence: certain

### [L3-2] Protocol and dataset sources used without citation: Nadeau–Bengio, Demšar, Fashion-MNIST, ModelNet10, Outex
- severity: MINOR
- type: new
- anchor: "Nadeau--Bengio corrected resampled estimator" (§3.1); "This is the canonical Dem\\v{s}ar multi-dataset protocol: one accuracy estimate per (dataset, configuration), ranked within each dataset, Friedman test across configurations, Nemenyi post-hoc critical difference" (§5.3); panel table (Fashion-MNIST, Table 5.2); "ModelNet10 point clouds and Outex textures" (§5.3, topology-wins)
- finding: The paper invokes Nadeau–Bengio (2003, Machine Learning 52:239–281) by name with no bibitem, and describes the Demšar (2006, JMLR 7:1–30) protocol by name with no bibitem — the only named statistical procedures in the paper that lack citations. Fashion-MNIST (Xiao, Rasul & Vollgraf, arXiv:1708.07747, 2017), ModelNet10 (Wu et al., 3D ShapeNets, 2015) and Outex (Ojala et al., 2002) are used as benchmark datasets without bibitems. All verified to exist; given the dissertation's otherwise complete 24-item bibliography (and that the L2-1 CD finding shows the Demšar protocol is followed imperfectly), citing the primary sources is due diligence.
- improvement: Add 5 bibitems and cite at the three sites.
- cost: cheap
- confidence: certain (existence verified on the web; absence in thebibliography verified by reading the full bibliography)

### [L3-3] No ECG/time-series TDA prior work cited; the "most cited answer" framing ignores a directly relevant literature the headline case studies sit inside
- severity: MINOR
- type: new
- anchor: "The literature's most cited answer to ``which stage matters most?'' comes from Conti et al." (§1.1); the delay-embedding paragraph (§3.1) cites only perea2015/umed2017/kennel1992/fraserswinney1986
- finding: Persistent homology applied to heartbeat/ECG classification and time-series signals is an established subfield the dissertation neither cites nor engages, even though both headline real datasets are heartbeats (e.g., Gholizadeh & Zadrozny, "A short survey of topological data analysis in time series and systems", arXiv:1809.10745, 2018, and their temporal-filtration ECG work; Khasawneh & Munch, "Chatter detection in turning using persistent homology", MSSP, 2016). Wave-1 audit flagged a related gap (Garin–Tauzin, Pun/Lee/Xia, Loiseaux) that remains open; this extends that list to the ECG-specific literature. The "vectorization dominates" claim would be better positioned (and harder to attack) with 2–3 sentences locating it against prior TDA-on-ECG results.
- improvement: Add 2–3 citations and one positioning paragraph in §1 or §5.2.
- cost: cheap
- confidence: probable (works verified to exist; the "should cite" judgement is the reviewer's)

---

## VERDICT
On the L1/L2/L3 cluster the dissertation is close to submission-ready: the headline numbers (6.39pp/0.69pp/3.50pp, η², ω², Friedman Q=50, equal-footing re-analyses, matched-genus, bottleneck, r25 harmonisation, panel statistics) all re-derived exactly from the DBs under the brief's conventions, the equal-footing caveats are disclosed with correct conventions, and the evidence-strength labelling is exemplary for a dissertation (single-split vs r25 marked at every site). The one genuine statistical defect is L2-1: the Nemenyi CD uses 12N instead of Demšar's 6N, understating the critical difference by √2 (2.48 vs 3.50), which invalidates the single post-hoc significance claim "Betti-to-Landscape rank gap exceeding the critical difference" and mis-draws the CD diagram — the highest-leverage fix is to correct the denominator in scripts/analysis_multidataset_friedman.py, regenerate CD=3.50, and soften that one §5.3 sentence (everything else in the panel section survives). The remaining findings are text-level (conclusion protocol mislabel, per-config ANOVA footnote, abstract η² attribution, macro-F1 summary convention, Appendix D typo, five missing citations) and one interpretive gap in the §5.1 mechanism (the embedded curves' H1 is noise-born, which is why filtration is near-inert on time series — worth one honest sentence). None of the findings change the direction or magnitude of the central claim; with the CD correction and the L2-2/L2-4 labelling fixes the paper is defensible as-is.
