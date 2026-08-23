#!/usr/bin/env python3
"""Insert the B5 large-n paragraph + fix the Sparse Rips guideline row.

B5 finding (data/tda/large_n_sweep.db, re-derived 2026-08-23):
  n=1000: sparse_rips == vietoris_rips == 100.00% on all 8 configs
          (accuracy parity, +0.00pp), but sparse_rips 1.83h/config vs
          VR 3.6min/config (~30x slower in giotto-tda 0.6.2).
  n=3000: sparse_rips infeasible - 0 completions in ~42h wall across two
          attempts (10.4h + 31.8h, both reboot-killed). No mid-config
          checkpoint in giotto; the design-point claim "Sparse Rips is the
          fast sparse approximation" does NOT hold in giotto-tda 0.6.2 at
          n in [1e3, 3e3].

Surgery is LINE-BASED on short unique markers (skill rule: never hardcode
multi-line anchors; the tex wraps unpredictably and uses literal backslash
pairs that repr doubles):
  - guideline row: find the line that STARTS with '    Large-scale clouds'
    (leading spaces + marker), replace the WHOLE line with the new row.
  - B5 paragraph: find the line '\\section{Operational Guidelines for
    Pipeline Selection}' and insert the paragraph + blank line before it.

Verification: each marker must occur exactly once; --dry-run prints counts
without writing.
"""
from __future__ import annotations

import sys
from pathlib import Path

TEX = Path("/home/kruzzzzy/Documents/AI_KOS_PROJECT/projects/tda-benchmark/dissertation.tex")

B5_PARAGRAPH = r"""\textbf{Sparse Rips at its design point (expansion B5).} The
guideline row for large-scale clouds rested on the untested premise
that Sparse Rips becomes advantageous at $n \ge 10^3$. To test this
directly, sphere/torus clouds at $n{=}1000$ and $n{=}3000$ points
(40 samples each, seed 42) were generated and Sparse Rips was run at
both scales, with a Vietoris--Rips control at $n{=}1000$
($n{=}3000$ Vietoris--Rips is infeasible: $C(3000,3)$ simplices);
four configurations per arm (Betti Curve / Persistence Landscape
$\times$ Random Forest / RBF-SVM), 5-fold stratified CV, seed 42,
rep 1 (\texttt{data/tda/large\_n\_sweep\-db}, 8 finished runs). At
$n{=}1000$ the two filtrations are accuracy-identical --- all eight
configurations score $100.00\%$ ($+0.00$~pp mean difference) --- but
Sparse Rips is roughly $30\times$ slower: $1.83$~h per configuration
versus $3.6$~min for Vietoris--Rips (giotto-tda 0.6.2, single CPU).
At $n{=}3000$ Sparse Rips did not complete a single configuration
within $42$~h of wall time across two attempts (interrupted by
hardware reboots; giotto-tda offers no mid-configuration
checkpointing, so each restart re-runs the configuration from
scratch). The design-point premise is therefore not supported in
this implementation: at the scale where Sparse Rips is intended to
pay off, giotto-tda 0.6.2's \texttt{SparseRipsPersistence} is
substantially \emph{slower} than Vietoris--Rips at $n{=}1000$ and
practically infeasible at $n{=}3000$ on this hardware. The guideline
row for large-scale clouds is revised accordingly: Vietoris--Rips
remains the pragmatic choice up to the largest $n$ at which it is
feasible, and Sparse Rips is recommended only with an
implementation-level benchmark at the target $n$ (its runtime is not
monotone-friendly in giotto-tda 0.6.2 --- a portability finding in
its own right).
"""

# New guideline row: single backslashes (LaTeX control space after "Pers.",
# \ge in math), row terminator is the literal two-backslash sequence "\\\\"
# in this file (a Python string containing two backslashes).
NEW_GUIDELINE_ROW = (
    "    Large-scale clouds ($n \\ge 10^3$) & Vietoris--Rips & Pers.\\ Images "
    "or Betti Curves & Random Forest & Sparse Rips designed for $n \\ge 10^3$; "
    "at $n{=}1000$ it is $30\\times$ slower than VR at identical accuracy, and "
    "at $n{=}3000$ it did not finish in $42$~h (giotto-tda 0.6.2, \\S5.4) --- "
    "benchmark the implementation before choosing it \\\\"
)

GUIDELINE_ROW_MARKER = "    Large-scale clouds"
SECTION_ANCHOR = "\\section{Operational Guidelines for Pipeline Selection}"


def main() -> None:
    src = TEX.read_text()
    lines = src.splitlines(keepends=True)
    dry = "--dry-run" in sys.argv

    row_idxs = [i for i, l in enumerate(lines) if l.startswith(GUIDELINE_ROW_MARKER)]
    sec_idxs = [i for i, l in enumerate(lines) if l.startswith(SECTION_ANCHOR)]
    print(f"[{'OK' if len(row_idxs)==1 else 'FAIL'}] guideline-row marker: {len(row_idxs)}")
    print(f"[{'OK' if len(sec_idxs)==1 else 'FAIL'}] section anchor: {len(sec_idxs)}")
    if len(row_idxs) != 1 or len(sec_idxs) != 1:
        sys.exit(1)

    old_row = lines[row_idxs[0]]
    print(f"old row bytes ({len(old_row)} chars): {old_row.strip()[:60]}...")
    # NEW_GUIDELINE_ROW already ends with the two-backslash row terminator;
    # just reattach the newline.
    new_row = NEW_GUIDELINE_ROW + "\n"
    print(f"new row terminator: {repr(new_row.rstrip()[-2:])}")

    if dry:
        print("dry-run: anchors unique; no write.")
        return

    # 1) replace the guideline row
    lines[row_idxs[0]] = new_row
    # 2) insert the B5 paragraph before the section anchor (with blank line)
    sec = sec_idxs[0]
    lines[sec:sec] = ["\n", B5_PARAGRAPH + "\n", "\n"]

    TEX.write_text("".join(lines))
    print("written: B5 paragraph inserted, guideline row fixed.")


if __name__ == "__main__":
    main()
