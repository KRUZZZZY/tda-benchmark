#!/usr/bin/env python3
"""Generate the paper's six figures from the results database + synthetic data.

Usage: python generate_figures.py [db_path]
Output: figures/*.pdf (vector, pdflatex-friendly)

Figures produced:
  fig_pipeline_diagram.pdf      — schematic three-stage pipeline
  fig_vectorization_comparison.pdf — vectorisers applied to one diagram
  fig_stage_impact.pdf          — ECG200 marginal accuracy by stage (from DB)
  fig_noise_pds.pdf             — sphere/torus persistence diagrams clean vs noisy
  fig_noise_curves.pdf          — accuracy vs sigma (from DB)
  fig_pareto.pdf                — wall time vs accuracy scatter (from DB)
"""
import os
import sqlite3
import sys

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

# Deterministic PDF output (reproducible builds): matplotlib embeds the
# current time in PDF metadata unless SOURCE_DATE_EPOCH is set.
if "SOURCE_DATE_EPOCH" not in os.environ:
    os.environ["SOURCE_DATE_EPOCH"] = "1755676800"  # 2026-08-20T00:00:00Z

REPO = os.path.dirname(os.path.abspath(__file__))
DB = sys.argv[1] if len(sys.argv) > 1 else os.path.join(REPO, "..", "..", "data", "tda", "expanded_results.db")
OUT = os.path.join(REPO, "figures")
os.makedirs(OUT, exist_ok=True)

ORANGE = "#e08f20"
BLACK = "#1c1c1c"
GREY = "#888888"
LIGHT = "#dddddd"


# ── 1. Pipeline diagram (schematic) ────────────────────────────────────
def fig_pipeline_diagram():
    fig, ax = plt.subplots(figsize=(9, 2.2))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 2.2)
    ax.axis("off")
    boxes = [
        ("Raw data", 0.3, "point cloud /\ntime series /\nimage"),
        ("Filtration", 2.6, "Vietoris--Rips\nAlpha, Cubical\nSparse Rips"),
        ("Persistence\ndiagram", 5.0, "multiset of\n(birth, death)"),
        ("Vectorization", 6.9, "Persistence Image\nLandscape, Betti\nStatistics, ..."),
        ("Classifier", 9.0, "SVM, Random\nForest, Logistic"),
    ]
    for i, (title, x, sub) in enumerate(boxes):
        color = ORANGE if i in (1, 3) else BLACK
        box = FancyBboxPatch((x, 0.55), 1.5, 1.1, boxstyle="round,pad=0.05",
                             fc=color, ec="none", alpha=0.92)
        ax.add_patch(box)
        ax.text(x + 0.75, 1.4, title, ha="center", va="center", fontsize=8,
                color="white", weight="bold")
        ax.text(x + 0.75, 0.95, sub, ha="center", va="center", fontsize=6,
                color="white")
        if i < len(boxes) - 1:
            ax.annotate("", xy=(x + 1.62, 1.1), xytext=(x + 1.5, 1.1),
                        arrowprops=dict(arrowstyle="->", color=BLACK, lw=1.5))
    ax.set_title("The three-stage persistent homology classification pipeline",
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_pipeline_diagram.pdf"), bbox_inches="tight")
    plt.close(fig)


# ── 2. Vectorization comparison (schematic, one synthetic diagram) ──────
def fig_vectorization_comparison():
    rng = np.random.default_rng(42)
    fig, axes = plt.subplots(2, 2, figsize=(8, 6))
    # one noisy persistence diagram: H0 points near diagonal, one long H1 pair
    births = rng.uniform(0, 1, 40)
    deaths = births + rng.exponential(0.05, 40)
    h1_b, h1_d = 0.2, 0.85  # the torus's long-lived H1 feature
    axes[0][0].plot([0, 1], [0, 1], color=GREY, lw=0.8, ls="--")
    axes[0][0].scatter(births, deaths, s=8, color=BLACK, alpha=0.7)
    axes[0][0].scatter([h1_b], [h1_d], s=40, color=ORANGE, zorder=3)
    axes[0][0].set_title("Persistence diagram", fontsize=9)
    axes[0][0].set_xlabel("birth"); axes[0][0].set_ylabel("death")
    axes[0][0].set_xlim(0, 1); axes[0][0].set_ylim(0, 1)

    t = np.linspace(0, 1.05, 200)
    # landscape: tent functions
    for b, d in [(0.2, 0.85), (0.1, 0.5), (0.4, 0.75), (0.6, 0.9)]:
        tent = np.maximum(0, np.minimum(t - b, d - t))
        axes[0][1].plot(t, tent, color=BLACK, lw=1.2)
    axes[0][1].set_title("Persistence landscape", fontsize=9)
    axes[0][1].set_xlabel("t"); axes[0][1].set_ylabel("$\\lambda_k(t)$")

    # Betti curve
    eps = np.linspace(0, 1.05, 200)
    betti = np.zeros_like(eps)
    for b, d in zip(births, deaths):
        betti += ((eps >= b) & (eps < d)).astype(float)
    axes[1][0].plot(eps, betti, color=BLACK, lw=1.2)
    axes[1][0].set_title("Betti curve", fontsize=9)
    axes[1][0].set_xlabel("$\\varepsilon$"); axes[1][0].set_ylabel("$\\beta_1$")

    # persistence image (Gaussian blobs on birth-persistence grid)
    pers = deaths - births
    grid = np.zeros((20, 20))
    for b, p in zip(births, pers):
        bi, pi = int(b * 19), int(p * 19)
        bi, pi = min(19, bi), min(19, pi)
        grid[pi, bi] += 1
    grid[19, int(h1_b * 19)] += 3
    axes[1][1].imshow(grid, origin="lower", cmap="Oranges", aspect="auto")
    axes[1][1].set_title("Persistence image", fontsize=9)
    axes[1][1].set_xlabel("birth"); axes[1][1].set_ylabel("persistence")
    fig.suptitle("Vectorization methods applied to one diagram", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_vectorization_comparison.pdf"), bbox_inches="tight")
    plt.close(fig)


# ── DB helpers ─────────────────────────────────────────────────────────
def config_means(cur, dataset=None):
    """Return list of (dataset, filtration, vectorizer, classifier, mean_acc)."""
    q = """SELECT r.dataset, r.filtration, r.vectorizer, r.classifier,
                  AVG(f.accuracy)
           FROM runs r JOIN fold_results f ON f.run_id = r.run_id"""
    if dataset:
        q += f" WHERE r.dataset = '{dataset}'"
    q += " GROUP BY r.run_id"
    return cur.execute(q).fetchall()


# ── 3. Stage impact on ECG200 ──────────────────────────────────────────
def fig_stage_impact(cur):
    rows = [r for r in config_means(cur, "ecg200")]
    stages = {
        "Filtration": {},
        "Vectorizer": {},
        "Classifier": {},
    }
    for _, fil, vec, clf, acc in rows:
        stages["Filtration"][fil] = stages["Filtration"].get(fil, []) + [acc]
        stages["Vectorizer"][vec] = stages["Vectorizer"].get(vec, []) + [acc]
        stages["Classifier"][clf] = stages["Classifier"].get(clf, []) + [acc]

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


# ── 4. Persistence diagrams clean vs noisy (from the actual .npy files) ──
def fig_noise_pds():
    data_root = os.path.join(REPO, "..", "..", "data", "tda", "synthetic")
    try:
        import ripser
        have_ripser = True
    except ImportError:
        have_ripser = False

    # The executed benchmark stores all 200 samples per noise level
    # (100 spheres label 0, 100 tori label 1). Plot the first sample of
    # each class from the actual data files — the geometry shown is the
    # geometry the sweep ran on (torus R=2, r=1; sphere S^2).
    fig, axes = plt.subplots(2, 2, figsize=(7, 6.5))
    for row, sigma in enumerate([0.00, 0.15]):
        tag = f"noise{int(sigma * 100)}"
        X = np.load(os.path.join(data_root, f"sphere_torus_{tag}_X.npy"))
        y = np.load(os.path.join(data_root, f"sphere_torus_{tag}_y.npy"))
        for col, (label, name) in enumerate([(0, "sphere"), (1, "torus")]):
            ax = axes[row][col]
            pts = X[y == label][0]
            if have_ripser:
                dgms = ripser.ripser(pts, maxdim=1)["dgms"]
                dg1 = dgms[1]
                ax.scatter(dg1[:, 0], dg1[:, 1], s=10, color=ORANGE if col else BLACK,
                           alpha=0.85)
            ax.plot([0, 2], [0, 2], color=GREY, lw=0.8, ls="--")
            ax.set_title(f"{name.capitalize()}, $\\sigma$={sigma:.2f}", fontsize=9)
            ax.set_xlim(0, 1.2); ax.set_ylim(0, 1.2)
            ax.set_xlabel("birth"); ax.set_ylabel("death")
            ax.set_aspect("equal")
    fig.suptitle("Persistence diagrams under clean and noisy conditions", fontsize=11)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_noise_pds.pdf"), bbox_inches="tight")
    plt.close(fig)


# ── 5. Accuracy vs noise ───────────────────────────────────────────────
def fig_noise_curves(cur):
    fig, ax = plt.subplots(figsize=(7, 4.2))
    sigmas = [0.00, 0.05, 0.15, 0.30]
    means, mins, maxs = [], [], []
    for s in sigmas:
        rows = [r for r in config_means(cur, f"sphere_torus_n{int(s*100)}")]
        accs = [r[4] * 100 for r in rows]
        means.append(np.mean(accs))
        mins.append(np.min(accs))
        maxs.append(np.max(accs))
    ax.plot(sigmas, means, "o-", color=ORANGE, lw=2, label="mean")
    ax.fill_between(sigmas, mins, maxs, color=ORANGE, alpha=0.15, label="min--max")
    ax.axhline(50, color=GREY, lw=0.8, ls="--", label="chance")
    ax.set_xlabel("$\\sigma$ (Gaussian noise)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Accuracy vs. noise across all sphere/torus configurations", fontsize=10)
    ax.set_ylim(40, 102)
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_noise_curves.pdf"), bbox_inches="tight")
    plt.close(fig)


# ── 6. Pareto scatter ─────────────────────────────────────────────────
def fig_pareto(cur):
    rows = cur.execute("""SELECT r.dataset, r.filtration, r.vectorizer,
                                 r.classifier, AVG(f.accuracy), AVG(r.wall_time_s)
                          FROM runs r JOIN fold_results f ON f.run_id = r.run_id
                          GROUP BY r.run_id""").fetchall()
    fig, ax = plt.subplots(figsize=(8, 5))
    fil_colors = {
        "vietoris_rips": BLACK, "weak_alpha": ORANGE,
        "sparse_rips": "#7aa6c2", "cubical": "#c25e5e",
    }
    for ds, fil, vec, clf, acc, wt in rows:
        ax.scatter(wt, acc * 100, s=14, color=fil_colors.get(fil, GREY),
                   alpha=0.55, edgecolors="none")
    # Pareto frontier (per dataset, accuracy vs time)
    for ds in sorted({r[0] for r in rows}):
        sub = [r for r in rows if r[0] == ds]
        sub.sort(key=lambda r: r[5])  # by wall time
        frontier, best = [], -1
        for r in sub:
            if r[4] * 100 > best:
                frontier.append(r)
                best = r[4] * 100
        if len(frontier) > 1:
            ax.plot([r[5] for r in frontier], [r[4] * 100 for r in frontier],
                    color=GREY, lw=1, ls=":", alpha=0.7)
    ax.set_xscale("log")
    ax.set_xlabel("Wall time (s, log scale)")
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Runtime vs. accuracy across all 616 configurations", fontsize=10)
    from matplotlib.lines import Line2D
    handles = [Line2D([0], [0], marker="o", ls="", color=c, label=n)
               for n, c in fil_colors.items()]
    ax.legend(handles=handles, fontsize=8, title="Filtration")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_pareto.pdf"), bbox_inches="tight")
    plt.close(fig)


def fig_nemenyi_cd():
    """B1 — critical-difference diagram from data/tda/multidataset_nemenyi.csv.

    Horizontal bar chart: configs ordered by mean rank (1 = best), with a
    CD-length bracket over the best config marking the Nemenyi-significant
    cluster boundary (configs whose rank gap to the best exceeds CD are NOT
    in the top cluster). Rank axis reversed (best at top/left).
    """
    csv_path = os.path.join(REPO, "..", "..", "data", "tda", "multidataset_nemenyi.csv")
    if not os.path.exists(csv_path):
        print("  [skip] fig_nemenyi_cd: multidataset_nemenyi.csv not found")
        return
    import csv
    rows = list(csv.DictReader(open(csv_path)))
    rows.sort(key=lambda r: float(r["mean_rank"]))
    cd = float(rows[0]["cd"])
    names = [r["config"] for r in rows]
    ranks = [float(r["mean_rank"]) for r in rows]

    fig, ax = plt.subplots(figsize=(9, 4.2))
    y = np.arange(len(names))[::-1]  # best on top
    colors = [ORANGE if i == 0 else GREY for i in range(len(names))]
    ax.barh(y, ranks, height=0.55, color=colors, edgecolor=BLACK, linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.invert_xaxis()  # rank 1 at right
    ax.set_xlabel("Mean rank across 9 datasets (1 = best)")
    ax.set_xlim(len(names) + 0.8, 0.2)
    # CD bracket over the best config's rank
    best = ranks[0]
    ax.plot([best, best + cd], [y[0] + 0.45, y[0] + 0.45], color=BLACK,
            linewidth=1.4, solid_capstyle="butt")
    ax.plot([best, best], [y[0] + 0.35, y[0] + 0.55], color=BLACK, linewidth=1.2)
    ax.plot([best + cd, best + cd], [y[0] + 0.35, y[0] + 0.55], color=BLACK, linewidth=1.2)
    ax.text(best + cd / 2, y[0] + 0.62, f"CD = {cd:.2f}", ha="center",
            va="bottom", fontsize=8)
    ax.set_title("Nemenyi critical difference: config mean ranks across 9 datasets",
                 fontsize=10)
    ax.grid(axis="x", color=LIGHT, linewidth=0.5)
    ax.set_axisbelow(True)
    fig.tight_layout()
    fig.savefig(os.path.join(OUT, "fig_nemenyi_cd.pdf"))
    plt.close(fig)
    print("  fig_nemenyi_cd.pdf")


def main():
    con = sqlite3.connect(DB)
    cur = con.cursor()
    fig_pipeline_diagram()
    fig_vectorization_comparison()
    fig_stage_impact(cur)
    fig_noise_pds()
    fig_noise_curves(cur)
    fig_pareto(cur)
    fig_nemenyi_cd()
    con.close()
    made = sorted(os.listdir(OUT))
    print(f"Wrote {len(made)} figures to {OUT}:")
    for f in made:
        print("  ", f)


if __name__ == "__main__":
    main()
