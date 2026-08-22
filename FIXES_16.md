# FIXES_16.md — expansion item #16: precise patch notes (Figure 4.1 labels + Appendix A `\texttt` leak)

**Status:** DRAFT patch notes for the orchestrator. NOT applied — `dissertation.tex` was
not edited. Both fixes are safe, local, and change no document structure.

**Repro facts (verified 2026-08-22):**

- Figure 4.1 = `fig:stage_impact` ("Stage impact on ECG200. Error bars show ±1 SE"),
  confirmed via `dissertation.aux` (`\newlabel{fig:stage_impact}{{4.1}...}`) and
  `dissertation.lof`. Its caption and `\label` in the tex are correct; there are no
  in-text `\ref{fig:...}` references at all (all figures are cited only via caption).
- Appendix A starts at tex line 2144 (`\appendix`) / 2145 (`\chapter{Full YAML
  Configuration}`); the YAML `lstlisting` block spans tex lines 2148–2233. The
  reviewer's "line 83" is the 83rd line of that listing block (the `db_path:` line,
  file line 2231).

---

## Fix 1 — Figure 4.1's illegible labels (root cause is in `generate_figures.py`, NOT the tex)

The illegibility is generated, not typeset: `fig_stage_impact()` draws 15 bars whose
tick labels are **two-line `stage\nsnake_case_name` strings at `fontsize=6.5`** with no
rotation (e.g. `Vectorizer\npersistence_statistics`, `Classifier\nrandom_forest`).
At figsize (9, 3.4) the long labels collide/overlap and are unreadable in print.
No `dissertation.tex` edit is needed for this issue; the figure must be regenerated.

### File: `generate_figures.py`, function `fig_stage_impact`, lines 147–167

**BEFORE (exact):**

```python
    fig, ax = plt.subplots(figsize=(9, 3.4))
    labels, means, errs, colors = [], [], [], []
    palette = [ORANGE, BLACK, GREY, LIGHT]
    for si, (stage, groups) in enumerate(stages.items()):
        order = sorted(groups.items(), key=lambda kv: -np.mean(kv[1]))
        for gi, (name, accs) in enumerate(order):
            labels.append(f"{stage}\n{name}")
            means.append(np.mean(accs) * 100)
            errs.append(np.std(accs) * 100 / np.sqrt(len(accs)))
            colors.append(palette[gi % len(palette)])
    x = np.arange(len(labels))
    ax.bar(x, means, yerr=errs, capsize=3, color=colors, alpha=0.9,
           edgecolor="black", linewidth=0.4)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=6.5)
    ax.set_ylabel("Marginal accuracy (%)")
    ax.set_title("Stage impact on ECG200 (marginal accuracy, $\\pm$1 SE)", fontsize=10)
    ax.axhline(50, color=GREY, lw=0.8, ls="--")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_stage_impact.pdf"), bbox_inches="tight")
    plt.close(fig)
```

**AFTER (exact):** single-line labels (snake_case → spaces), rotation 30° right-aligned,
fontsize 8; bars coloured by stage (not by rank position) with a stage legend; dotted
separators between the three stage blocks.

```python
    fig, ax = plt.subplots(figsize=(9, 3.8))
    labels, means, errs, colors = [], [], [], []
    palette = [ORANGE, BLACK, GREY, LIGHT]
    for si, (stage, groups) in enumerate(stages.items()):
        order = sorted(groups.items(), key=lambda kv: -np.mean(kv[1]))
        for gi, (name, accs) in enumerate(order):
            # Single-line tick labels; the stage name moves to the legend.
            # Long snake_case names at 6.5pt were the legibility killer.
            labels.append(name.replace("_", " "))
            means.append(np.mean(accs) * 100)
            errs.append(np.std(accs) * 100 / np.sqrt(len(accs)))
            colors.append(palette[si % len(palette)])
    x = np.arange(len(labels))
    ax.bar(x, means, yerr=errs, capsize=3, color=colors, alpha=0.9,
           edgecolor="black", linewidth=0.4)
    # Separators between the Filtration / Vectorizer / Classifier blocks
    for cut in np.cumsum([len(g) for g in stages.values()])[:-1]:
        ax.axvline(cut - 0.5, color=GREY, lw=0.8, ls=":")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, rotation=30, ha="right")
    ax.set_ylabel("Marginal accuracy (%)")
    ax.set_title("Stage impact on ECG200 (marginal accuracy, $\\pm$1 SE)", fontsize=10)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(facecolor=palette[i], label=stage)
                       for i, stage in enumerate(stages)],
              loc="upper right", fontsize=8, frameon=False)
    ax.axhline(50, color=GREY, lw=0.8, ls="--")
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_stage_impact.pdf"), bbox_inches="tight")
    plt.close(fig)
```

**After the edit, regenerate + recompile (from the repo root):**

```bash
.venv-tda/bin/python generate_figures.py            # rewrites figures/fig_stage_impact.pdf
pdflatex -interaction=nonstopmode dissertation.tex  # x2 for refs/TOC
```

Note: `generate_figures.py` reads `data/tda/expanded_results.db` by default — read-only,
safe to run while a sweep owns the CPU (a few seconds).

---

## Fix 2 — Appendix A `\texttt` leak (tex line 2231)

The YAML listing block (`\begin{lstlisting}[style=yaml]`, tex lines 2148–2233) contains

```
db_path: \texttt{data/tda/expanded\_results.db}
```

`style=yaml` has **no `escapeinside`** (verified in the preamble, lines 67–75), so
`\texttt{...}` is NOT interpreted inside the listing: it is typeset verbatim and the
raw LaTeX markup literally leaks into the compiled PDF
(`db_path: \texttt{data/tda/expanded\_results.db}` appears in the listing output).
This is the only `\texttt` inside any listing block in the document (the matches at
tex lines 2375 and 2437 are prose in Appendix D, where `\texttt` is correct).

### File: `dissertation.tex`, line 2231

**BEFORE (exact string on line 2231):**

```latex
  db_path: \texttt{data/tda/expanded\_results.db}
```

**AFTER (exact replacement):**

```latex
  db_path: data/tda/expanded_results.db
```

**Why it is correct:** inside a verbatim listing the backslash and braces serve no
purpose — the listing already renders in typewriter face (`basicstyle = \ttfamily\footnotesize`).
The `\_` escapes were also leaking (they print literally); the plain `expanded_results.db`
is the true YAML value (matches `run_all.sh` and the README).

**Apply:** single-line replace at tex line 2231; then recompile
(`pdflatex -interaction=nonstopmode dissertation.tex` ×2) and eyeball page ~57
(Appendix A listing) — the line should read `db_path: data/tda/expanded_results.db`.

---

## Verification checklist for the orchestrator

- [ ] `generate_figures.py` patched with Fix 1 and `figures/fig_stage_impact.pdf` regenerated.
- [ ] `dissertation.tex` line 2231 patched with Fix 2 (no other tex edits).
- [ ] `git diff` on the two files shows exactly the blocks above.
- [ ] `pdflatex` run twice; no new warnings; `dissertation.pdf` rebuilt.
- [ ] Optional follow-up (out of scope for #16): figures are never `\ref`'d in the
      text; adding `as shown in Figure~\ref{fig:stage_impact}` would tie the caption
      into the narrative.
