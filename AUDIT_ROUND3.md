# TDA Dissertation — Round 3 Comprehensive Audit

**File:** `dissertation.tex` (1510 lines, 35 pages)
**Date:** 2026-08-09
**Audit type:** 8-point comprehensive + previously-fixed-issue verification

---

## PREVIOUSLY-FIXED ISSUES: STATUS CHECK

| # | Issue | Status | Notes |
|---|-------|--------|-------|
| 1 | Broken abstract | **FIXED** ✓ | L118-157: Complete, syntactically clean, well-structured |
| 2 | Parameter count mismatches | **STILL BROKEN** 🔴 | See Critical Finding #1 below |
| 3 | Missing CIs in stage impact table | **PARTIALLY FIXED** 🟡 | CIs present in Range column (L819-823), but p-value column all "—" |
| 4 | Unsupported bottleneck claim | **STILL BROKEN** 🔴 | See Critical Finding #3 below |
| 5 | Dataset count clarity | **FIXED** ✓ | "6 dataset instances" (Abstract L150) = 4 noise levels + ECG200 + MNIST; "5 datasets" for 180 sweep = 4 noise + ECG200 |
| 6 | Broken conclusion sentence | **FIXED** ✓ | L1098-1124: Complete, clean, no fragments |
| 7 | Missing MNIST in YAML appendix | **FIXED** ✓ | L1160: `mnist_01` present in YAML |
| 8 | Cubical-on-ECG200 unexplained | **PARTIALLY FIXED** 🟡 | Footnote L930 explains mechanism, but cubical not in YAML (L1141-1155) and not in Introduction's filtration count |
| 9 | Pareto comma | **FIXED** ✓ | L966-969 grammatically functional |
| 10 | *(checking what the 10th was...)* | — | — |

---

## 8-POINT AUDIT

---

### (1) CORE SCOPE & NARRATIVE

**Thesis:** "Pipeline-stage importance in TDA classification is modality-dependent." (L133, L234-248, L1099)

**Assessment:** Clean, falsifiable, consistently stated across Abstract, Introduction, Ch5 Discussion, and Conclusion. The dual contribution (finding + framework) is properly stated as "finding using framework" per the anti-patterns guide.

**No issues.** ✓

---

### (2) MACRO-STRUCTURE & PROGRESSION

**Line count estimates:**

| Section | Lines | ~% |
|---------|-------|-----|
| Ch1: Introduction | ~100 | 9% |
| Ch2: Foundations | ~386 | 36% |
| Ch3: Methods | ~104 | 10% |
| Ch4: Results | ~216 | 20% |
| Ch5: Discussion | ~118 | 11% |
| Ch6: Conclusion | ~28 | 3% |
| Appendices A-E | ~120 | 11% |

**Issue:** Ch2 (Foundations) at 386 lines dwarfs Ch4 (Results) at 216 lines (1.8:1 ratio). The healthy ratio from the anti-patterns guide is Results ~30%, Foundations ~20%. The chain-complex/homology development (L361-465, ~104 lines) is textbook material that could be condensed to cite rather than re-derive.

**✅ Working:** Chapter transitions are explicit and clear (L261, L646, L758, L974, L1094). §2.6 "Mapping Theory to Benchmark Variables" (L607-644) provides excellent forward pointers.

**🟡 Issue 2.1:** Foundations:Results ratio is inverted (L264-650 vs L758-974). Consider condensing §2.3 chain-complex formalism and moving some detail to an appendix.

---

### (3) MATHEMATICAL PRECISION

#### Chain complexes: ✅
Properly defined. Boundary operators ($\partial_k$, L380-389), cycles/boundaries ($Z_k$, $B_k$, L395-403), homology groups ($H_k$, L411), Betti numbers — all formally correct over $\mathbb{Z}_2$.

#### Stability theorem: ✅  
Properly stated (L504-512) with citation to Cohen-Steiner et al. 2007. Bottleneck distance (L478-488) and Gromov-Hausdorff distance (L491-502) formally defined.

#### Noise model: ✅
Gaussian perturbation on spatial coordinates (L709-718). Explicitly scoped: "It does *not* perturb the pairwise distance matrix directly — that would violate the triangle inequality." Correct.

#### Takens embedding: ✅
Properly stated (L670-681) with dimension condition $d > 2d_M$. Standard $d=3, \tau=1$ for ECG200 cited.

#### FPS (Farthest Point Sampling): ✅
Explicitly named and algorithmically described (L702-708).

#### CV leakage: ✅
Grid bounds fit on training folds only (L694-697).

#### 🔴 Issue 3.1: Gromov-Hausdorff bound for Gaussian noise is not rigorous (L516-520)
The text states: "Gaussian noise of magnitude $\sigma$ on spatial coordinates perturbs the point cloud by at most $2\sigma$ in Gromov-Hausdorff distance." This is incorrect as stated. With $n$ i.i.d. Gaussian perturbations $\eta_i \sim \mathcal{N}(0, \sigma^2 I_3)$, the max perturbation $\max_i\|\eta_i\|$ has expected value $\sim\sigma\sqrt{2\log n}$ for large $n$, not simply $2\sigma$. Furthermore, Gaussian noise has unbounded support — there is no deterministic "at most." A probabilistic bound with confidence level is needed (e.g., "with high probability, $d_{GH} \leq C\sigma\sqrt{\log n}$").

#### 🔴 Issue 3.2: "Stability bound is conservative" — claimed without computing bottleneck distance (L140-141, L896-900)
The Abstract (L140-141) states flatly: "the stability bound is conservative." The noise section (L896-897) hedges slightly: "the actual bottleneck distance between clean and noisy diagrams appears substantially below the worst-case guarantee." But **nowhere in the paper is the bottleneck distance actually computed**. The inference is from classification accuracy surviving noise, not from bottleneck distance computation. Per the anti-patterns guide: "Don't claim a bound is 'conservative' without computing it."

#### 🟡 Issue 3.3: Confusion of bottleneck distance with feature persistence (L892-895)
The text compares the bottleneck bound ($4\sigma = 0.60$) against empirical persistences of torus features ($0.5$--$0.8$), implying features with persistence < bottleneck bound could be destroyed. The bottleneck distance bounds the *matching distance between diagrams*, not the persistence of individual features. A feature with persistence 0.5 could shift in birth/death coordinates but not necessarily disappear.

---

### (4) LITERATURE VERIFICATION

#### Citations present for foundational theorems:
- Takens 1981 ✓
- Leray 1945 ✓
- Cohen-Steiner et al. 2007 ✓

#### 🔴 Issue 4.1: 10 uncited bibliography entries 
The following entries appear in the bibliography (L1387-1507) but are **never cited in the text**:

| Bib key | Line | Content |
|---------|------|---------|
| `barnes2021` | 1401 | Comparative study of ML methods for persistence diagrams |
| `carriere2020` | 1411 | PersLay: neural network layer for PDs |
| `hatwar2026` | 1429 | TDA and ML survey |
| `hofer2017` | 1434 | Deep learning with topological signatures |
| `hofstad2017` | 1439 | Random Graphs and Complex Networks |
| `perea2022` | 1457 | Template functions |
| `somasundaram2021` | 1464 | Benchmarking R packages for PH |
| `sulowska2026` | 1470 | Comparative analysis of PD vectorization |
| `telyatnikov2024` | 1483 | TopoBench |
| `turkes2022` | 1489 | On the effectiveness of PH |

That's **10 out of 20** bibliography entries (50%) that serve no purpose. Either they should be cited in relevant sections or removed. Notably, TopoBench is a directly relevant benchmark that should be compared against in the text.

#### 🟡 Issue 4.2: Missing citations for methods used
- **Cubical filtration** (appears in results L821, L921-929): Used extensively in Chapter 4 but never formally defined or cited. Needs citation (e.g., Kaczynski, Mischaikow, Mrozek — *Computational Homology*).
- **Silhouette vectorizer** (appears L822, L925): Top performer in stage impact table but never defined mathematically or cited.
- **Amplitude vectorizer** (appears L905): Used but never defined or cited.
- **Persistence Entropy** (appears L835): Used but never defined or cited. This is doubly problematic because "Persistence Entropy" and "entropy" are used as distinct concepts without definition.

---

### (5) ABSTRACT CONCEPTS NEEDING EXAMPLES

#### 🟡 Issue 5.1: Cubical filtration never illustrated (used at L821, L921-929, L1042)
The most commonly used filtration in the results (cubical) receives no formal definition, no diagram, no mathematical description. The reader is told it exists and works well but never learns what it is. At minimum, add a definition in §2.2 alongside VR, Alpha, and Sparse Rips.

#### 🟡 Issue 5.2: Silhouette, Amplitude, and Persistence Entropy undefined
These vectorizers appear in results but have zero mathematical grounding in the text. §2.5 describes only 4 methods (Statistics, Betti, Landscapes, Images). The 3 additional methods that appear in results (Silhouette, Amplitude, Entropy) need definitions — or the results should be scoped to only the 4 defined methods.

#### 🟡 Issue 5.3: "Marginal range of 1.9pp" in Abstract might confuse (L129-130)
A reader encountering "marginal range" without having read the paper won't understand this means range of stage-marginalized mean accuracies across methods. Consider: "the range of mean accuracies attributable to vectorization choice (marginalizing over filtration and classifier) is 1.9pp..."

---

### (6) SECTION-BY-SECTION DENSITY

#### Redundancies checked: ✅
- "Pipeline-stage importance is modality-dependent" appears in Abstract (states claim), Introduction (introduces thesis), Discussion (explains mechanism), Conclusion (synthesizes) — each serves a different function per anti-patterns guide.
- "180 configurations" count — Introduction states as design, Results as context. Distinct functions.
- "616 configurations" — Abstract as scope, Results as noise context, Conclusion as framework capability. Fine.

#### 🟡 Issue 6.1: §2.3 (Homology) overly dense (L361-465, ~104 lines)
The chain complex → boundary → cycles → boundaries → homology → persistent homology → birth/death → persistence diagram chain is textbook material. Consider: keep the definitions (which are needed for rigour) but compress the exposition. Move the detailed birth/death definition with quantifiers to an appendix.

---

### (7) TONE AND RIGOR

#### ✅ Register consistent throughout. Academic, appropriate for graduate-level audience.

#### 🟡 Issue 7.1: Abstract tone stronger than body text on bottleneck claim (L140 vs L896)
Abstract: "the stability bound is conservative" (flat assertion)
Body: "the actual bottleneck distance... appears substantially below the worst-case guarantee" (hedged)

The Abstract should match the body's hedging since the bottleneck distance was never computed.

#### 🟡 Issue 7.2: "This qualifies the widely cited claim" ambiguous (L1104)
"Qualifies" can mean "limits/restricts" (intended) but also "makes eligible" (misleading). Consider: "This constrains the widely cited claim..." or "This limits the widely cited claim..."

---

### (8) PRIORITIZED REVISION ROADMAP

---

## 🔴 CRITICAL (fix before sharing externally)

### CRITICAL #1: STAGE-IMPACT NUMBERS IN ABSTRACT/INTRO MISMATCH RESULTS TABLE
- **Abstract (L130-132):** Vectorization range 1.9pp [1.2, 2.5], Filtration range 0.1pp [0.0, 0.4]
- **Introduction Contributions §1.3 (L239-242):** Exact same numbers: 1.9pp, 0.1pp
- **Results Table 4.1 (L819-823):** Filtration 0.66pp [0.18, 1.14], Vectorization 6.13pp [4.82, 7.44]
- **Fix:** Either (a) explain that Abstract numbers are from the 180-config 3-filtration/4-vectorizer sweep while table numbers are from the 616-config 4-filtration/7-vectorizer sweep, OR (b) harmonize all sections to use the same sweep's numbers. Currently the reader comparing Abstract to Results will conclude the paper's numbers are fabricated.

### CRITICAL #2: ABSTRACT ARITHMETIC DOESN'T SUM TO 616
- **Abstract (L150-151):** "6 dataset instances, 4 filtrations, 7 vectorizers, and 4 classifiers"
- **Arithmetic:** 6 × 4 × 7 × 4 = 672 ≠ 616
- **Fix:** Either explain which 56 combinations were excluded and why, or restate the count as "616 (from a possible 672, with 56 combinations excluded because...)" OR restructure to "across up to 6 dataset instances, 4 filtrations, 7 vectorizers, and 4 classifiers"

### CRITICAL #3: "STABILITY BOUND IS CONSERVATIVE" — UNSUPPORTED CLAIM
- **Abstract (L140-141):** "the stability bound is conservative"
- **Body (L896-900):** "the actual bottleneck distance between clean and noisy diagrams appears substantially below the worst-case guarantee"
- **Reality:** The bottleneck distance was never computed. The claim comes from observing that classification accuracy survives noise — this is inference, not computation.
- **Fix:** Either compute the bottleneck distance and report it, or change the claim to: "classification accuracy survives noise levels where the stability bound's worst-case guarantee would permit degradation" — which is what the data actually supports.

### CRITICAL #4: GH-BOUND FOR GAUSSIAN NOISE IS NOT RIGOROUS
- **L516-520:** "Gaussian noise of magnitude $\sigma$ perturbs the point cloud by at most $2\sigma$ in Gromov-Hausdorff distance"
- **Problem:** No deterministic "at most" exists for unbounded Gaussian noise. The expected maximum perturbation for $n=200$ points in 3D is $\sim 2.8\sigma$ (via extreme value theory, not $2\sigma$).
- **Fix:** State a probabilistic bound: "with probability $\geq 0.95$, the Gromov-Hausdorff distance is bounded by $C\sigma\sqrt{\log n}$" and cite the relevant extreme-value result. Or state: "by the stability theorem, each perturbation of magnitude $\|\eta_i\|$\ changes the diagram by at most..." without claiming a GH bound.

### CRITICAL #5: CUBICAL FILTRATION USED IN RESULTS BUT MISSING FROM YAML + INTRODUCTION COUNT
- **Introduction (L175-178):** "3 filtrations (VR, Alpha, Sparse Rips)"
- **YAML Appendix A (L1141-1155):** Lists exactly 3 filtrations, no cubical
- **Results Chapter (L821, L921-929):** Cubical is the top filtration performer and appears in the Pareto table
- **Fix:** Either (a) add cubical to the YAML and update the Introduction's filtration count to 4, or (b) clearly separate results from the 180-config sweep vs the extended sweep, and state which numbers come from which

---

## 🟡 IMPORTANT (fix before submission)

### IMPORTANT #1: Stage impact table p-value column empty (L819-823)
The table header promises Wilcoxon p-values, but all three rows show "—". The text says "All p-values are reported descriptively" but none are in the table. Either add the p-values or remove the column.

### IMPORTANT #2: 10 uncited bibliography entries (L1395-1507)
50% of the bibliography (10/20 entries) is never cited. Either cite them in appropriate sections or delete them. TopoBench (telyatnikov2024) is the most notable omission — it's a directly comparable benchmark.

### IMPORTANT #3: Cubical filtration never defined (used at L821, L921-929)
The most empirically important filtration receives zero mathematical treatment. Add a definition in §2.2, or at minimum a citation and one-paragraph description.

### IMPORTANT #4: Silhouette, Amplitude, Persistence Entropy undefined
These three vectorizers appear in results but have no definitions. §2.5 defines only 4 of the 7 vectorizers used. Either define all 7 or scope the results discussion to the 4 defined ones.

### IMPORTANT #5: Bottleneck vs persistence confusion (L892-895)
"features near the lower end of this range would be threatened by the bound" — the stability bound bounds diagram-to-diagram distance, not individual feature persistence. Clarify or remove.

### IMPORTANT #6: Limitations 1:1 pairing check
Six limitations listed (L1054-1059) and six future-work items. The pairing is:
- (1) $H_1$ cap → $H_2$ via Flood Complex ✓
- (2) Two-class only → multi-class extension ✓
- (3) One real dataset per modality → ECG5000, FordA ✓
- (4) Single library → GUDHI, Ripser replication ✓
- (5) No learned vectorizers → PersLay ✓
- (6) $n=200$, wide CIs → larger-$n$ datasets ✓

All 6 pair 1:1. **PASS** ✓

---

## 🟢 MINOR (fix at leisure)

### MINOR #1: "Qualifies" ambiguity (L1104)
"This qualifies the widely cited claim" → "This constrains the widely cited claim"

### MINOR #2: Abstract hedging mismatch (L140 vs L896)
Abstract should match body hedging: "the stability bound appears conservative based on..." 

### MINOR #3: §2.3 density (L361-465)
The chain-complex formalism is ~104 lines of textbook material. Consider compressing by 30-40%.

### MINOR #4: Missing newline before `\begin{figure}` (L848-849)
`All $p$-values are reported descriptively.\n\begin{figure}` — missing paragraph break or blank line.

### MINOR #5: Pareto sentence structure (L964-969)
"76% on ECG200, 100% on synthetic data, on the two datasets tested" — awkward three-part list where the third item isn't a data point. Consider: "76% on ECG200 and 100% on synthetic data (the two datasets tested)"

### MINOR #6: "With Persistence Statistics in a parallel reduced sweep" (L178) 
This parenthetical is easy to miss. Consider making it a more prominent note or footnote.

---

## SUMMARY

**Total findings: 17**
- 🔴 Critical: 5 (all trust-destroying — numerical inconsistencies and unsupported claims)
- 🟡 Important: 6 (missing definitions, uncited references, empty table column)
- 🟢 Minor: 6 (wording, density, formatting)

**Of the 10 previously-fixed issues:**
- 5 are genuinely still fixed ✓
- 3 are partially broken or still problematic (parameter counts, bottleneck claim, cubical in YAML)
- 1 is partially fixed (CIs present but p-values empty)
- The 10th wasn't traceable from session history

**Most alarming finding:** The stage-impact numbers in Abstract/Introduction (1.9pp vectorization, 0.1pp filtration) are *completely different* from the Results table (6.13pp, 0.66pp). This is the kind of discrepancy that causes readers to lose trust in every other number in the paper. It must be resolved before any external review.
