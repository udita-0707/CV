"""Charts for the M4/M5 defence deck, in the M2/M3 deck palette (navy / teal / coral).

Same data as the paper figures in ``src/plots.py``, restyled and resized for
10 x 5.625 in slides. Teal and coral are the two data series; navy is ink only.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager
from matplotlib.lines import Line2D

NAVY = "#14213D"
INK = "#1E2430"
TEAL = "#1B998B"
CORAL = "#E4572E"
CORAL_TINT = "#FBE3DB"
MUTED = "#6B7280"
GRID = "#E5E7EB"
SMALL_ID_CELLS = 10


def use_deck_style(font_dir: Path) -> None:
    for path in sorted(font_dir.glob("carlito_*.ttf")):
        font_manager.fontManager.addfont(str(path))
    plt.rcParams.update(
        {
            "font.family": "Carlito",
            "font.size": 11,
            "axes.labelsize": 11,
            "xtick.labelsize": 10.5,
            "ytick.labelsize": 10.5,
            "legend.fontsize": 10,
            "axes.edgecolor": GRID,
            "axes.labelcolor": INK,
            "xtick.color": MUTED,
            "ytick.color": MUTED,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "axes.grid.axis": "y",
            "grid.color": GRID,
            "grid.linewidth": 0.8,
            "axes.axisbelow": True,
            "legend.frameon": False,
            "savefig.dpi": 300,
            "figure.facecolor": "white",
        }
    )


def _save(figure: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path, bbox_inches="tight", pad_inches=0.04)
    plt.close(figure)
    return path


def per_id_strip(patients: pd.DataFrame, folds: pd.DataFrame, path: Path, size=(5.3, 3.35)) -> Path:
    """Per-Patient-ID sensitivity per fold: teal dots, coral pooled bar, navy macro diamond."""
    figure, axis = plt.subplots(figsize=size)
    eligible = patients[patients.sensitivity_defined]
    labels = []
    for position, (fold, group) in enumerate(eligible.groupby("fold", sort=True), start=1):
        values = group.sensitivity.to_numpy()
        x = position + np.random.default_rng(int(fold)).uniform(-0.17, 0.17, len(group))
        large = group.n_positive.to_numpy() >= SMALL_ID_CELLS
        axis.scatter(x[large], values[large], s=22, color=TEAL, edgecolors="white", linewidths=0.5, zorder=3)
        axis.scatter(x[~large], values[~large], s=22, facecolors="white", edgecolors=TEAL, linewidths=1.1, zorder=3)
        row = folds.loc[folds.fold == fold].iloc[0]
        axis.hlines(row.pooled_sensitivity_recall, position - 0.32, position + 0.32, color=CORAL, linewidth=3, zorder=4)
        axis.scatter([position + 0.42], [row.macro_sensitivity], marker="D", s=34, color=NAVY, zorder=5)
        labels.append(f"Fold {fold}\n{len(group)} IDs")
    axis.set_xticks(range(1, len(labels) + 1), labels)
    axis.set_ylim(0.33, 1.03)
    axis.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    axis.set_ylabel("Sensitivity per Patient-ID")
    axis.tick_params(axis="x", length=0)
    handles = [
        Line2D([], [], marker="o", linestyle="", color=TEAL, markeredgecolor="white", markersize=6, label="Patient-ID"),
        Line2D([], [], marker="o", linestyle="", markerfacecolor="white", markeredgecolor=TEAL, markersize=6, label=f"< {SMALL_ID_CELLS} Parasitized cells"),
        Line2D([], [], color=CORAL, linewidth=3, label="Pooled (M2)"),
        Line2D([], [], marker="D", linestyle="", color=NAVY, markersize=5.5, label="Macro (M4)"),
    ]
    axis.legend(handles=handles, loc="lower left", bbox_to_anchor=(0, 1.0), ncols=4, handletextpad=0.3, columnspacing=1.0, borderaxespad=0.1)
    return _save(figure, path)


def paired_differences(primary: pd.DataFrame, bootstrap: pd.DataFrame, threshold_pp: float, band: tuple[float, float], path: Path, size=(5.6, 3.35)) -> Path:
    """Macro minus pooled sensitivity per fold and mean, with 95% cluster-bootstrap CIs."""
    figure, axis = plt.subplots(figsize=size)
    ci = bootstrap[bootstrap.metric == "sensitivity"].assign(fold=lambda f: f.fold.astype(str)).set_index("fold")
    folds = [str(f) for f in primary.sort_values("fold").fold]
    x = np.arange(len(folds))
    y = primary.sort_values("fold").difference_pp.to_numpy()
    low = np.array([ci.at[f, "ci_low_pp"] for f in folds])
    high = np.array([ci.at[f, "ci_high_pp"] for f in folds])
    axis.axhspan(min(band), max(band), color=CORAL_TINT, zorder=0, linewidth=0)
    for sign in (-1, 1):
        axis.axhline(sign * threshold_pp, color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    axis.axhline(0, color=INK, linewidth=0.9)
    axis.errorbar(x, y, yerr=[y - low, high - y], fmt="o", color=TEAL, ecolor=MUTED, elinewidth=1.2, capsize=3, markersize=7, zorder=3)
    mean_x = len(folds) + 0.3
    mean = ci.at["mean", "observed_difference_pp"]
    axis.errorbar([mean_x], [mean], yerr=[[mean - ci.at["mean", "ci_low_pp"]], [ci.at["mean", "ci_high_pp"] - mean]],
                  fmt="D", color=NAVY, ecolor=NAVY, elinewidth=1.6, capsize=4, markersize=8, zorder=4)
    axis.set_xticks(list(x) + [mean_x], [f"Fold {f}" for f in folds] + ["Mean"])
    axis.set_xlim(-0.6, mean_x + 0.55)
    axis.set_ylabel("Macro − pooled sensitivity (pp)")
    axis.tick_params(axis="x", length=0)
    right = matplotlib.transforms.blended_transform_factory(axis.transAxes, axis.transData)
    axis.text(1.01, threshold_pp, f"+{threshold_pp} pp", transform=right, va="center", fontsize=9.5, color=MUTED)
    axis.text(1.01, -threshold_pp, f"−{threshold_pp} pp", transform=right, va="center", fontsize=9.5, color=MUTED)
    axis.text(1.01, min(band) - 0.2, "M3\npredicted", transform=right, va="top", fontsize=9.5, color=CORAL, linespacing=0.95)
    return _save(figure, path)


def concentration(curves: pd.DataFrame, path: Path, top_n: int = 10, size=(4.5, 3.35)) -> Path:
    """Cumulative share of errors held by Patient-IDs ranked by errors; direct labels, no legend."""
    figure, axis = plt.subplots(figsize=size)
    axis.plot([0, 1], [0, 1], color=MUTED, linewidth=1, linestyle=(0, (4, 3)))
    for kind, color, name in (("FN", TEAL, "False negatives"), ("FP", CORAL, "False positives")):
        curve = curves[curves.error_type == kind]
        x = np.concatenate([[0], curve.share_of_ids.to_numpy()])
        y = np.concatenate([[0], curve.cumulative_share_of_errors.to_numpy()])
        axis.plot(x, y, color=color, linewidth=2.6, label=name)
    axis.legend(loc="lower right", handlelength=1.6)
    fn = curves[curves.error_type == "FN"].iloc[top_n - 1]
    axis.scatter([fn.share_of_ids], [fn.cumulative_share_of_errors], s=40, color=NAVY, zorder=5)
    axis.annotate(f"top {top_n} IDs hold\n{100 * fn.cumulative_share_of_errors:.1f}% of FN", (fn.share_of_ids, fn.cumulative_share_of_errors),
                  xytext=(0.2, 0.1), textcoords="data", fontsize=10, color=NAVY, va="center",
                  arrowprops={"arrowstyle": "-", "color": NAVY, "linewidth": 0.8, "shrinkB": 4})
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1.03)
    axis.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    axis.yaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0, decimals=0))
    axis.set_xlabel("Share of Patient-IDs, ranked by errors")
    axis.set_ylabel("Cumulative share of errors")
    axis.grid(True, axis="both")
    return _save(figure, path)


def inclusion_bars(counts: pd.DataFrame, path: Path, size=(3.3, 1.8)) -> Path:
    """Crops with a visible stained inclusion, per blind-review group (errors coral, controls teal)."""
    order = [
        ("top_false_negative", "Confident FN", CORAL),
        ("random_true_positive", "Random TP", TEAL),
        ("top_false_positive", "Confident FP", CORAL),
        ("random_true_negative", "Random TN", TEAL),
    ]
    table = counts.set_index("group")
    figure, axis = plt.subplots(figsize=size)
    y = np.arange(len(order))[::-1]
    for row, (group, label, color) in zip(y, order):
        n = int(table.at[group, "n_cells"])
        yes = int(table.at[group, "inclusion_yes"])
        axis.barh(row, yes / n, color=color, height=0.62)
        axis.barh(row, 1, color=GRID, height=0.62, zorder=0)
        axis.text(1.03, row, f"{yes}/{n}", va="center", fontsize=12, color=INK)
    axis.set_yticks(y, [label for _, label, _ in order])
    axis.set_xlim(0, 1)
    axis.set_xticks([])
    axis.grid(False)
    for side in ("left", "bottom"):
        axis.spines[side].set_visible(False)
    axis.tick_params(axis="y", length=0, labelcolor=INK, labelsize=12)
    return _save(figure, path)
