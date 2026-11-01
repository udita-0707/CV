"""Static figures for M4/M5, sized for an IEEE two-column page (3.5 in / 7.16 in)."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

BLUE = "#2a78d6"  # categorical slot 1
ORANGE = "#eb6834"  # categorical slot 2
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e4e3df"
AXIS = "#b9b8b2"
BAND = "#fbe1d6"
SINGLE_COLUMN = 3.5
DOUBLE_COLUMN = 7.16
SMALL_ID_CELLS = 10  # hollow markers below this many cells, matching ablation A2

plt.rcParams.update(
    {
        "font.size": 7.5,
        "axes.titlesize": 8,
        "axes.labelsize": 7.5,
        "xtick.labelsize": 7,
        "ytick.labelsize": 7,
        "legend.fontsize": 6.5,
        "axes.edgecolor": AXIS,
        "axes.labelcolor": INK,
        "axes.titlecolor": INK,
        "xtick.color": INK_SECONDARY,
        "ytick.color": INK_SECONDARY,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.grid.axis": "y",
        "grid.color": GRID,
        "grid.linewidth": 0.5,
        "grid.linestyle": "-",
        "axes.axisbelow": True,
        "legend.frameon": False,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "figure.facecolor": "white",
    }
)


def _save(figure: plt.Figure, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(path)
    plt.close(figure)
    return path


def _jitter(n: int, seed: int, width: float = 0.16) -> np.ndarray:
    return np.random.default_rng(seed).uniform(-width, width, n)


def per_id_sensitivity_by_fold(patients: pd.DataFrame, folds: pd.DataFrame, path: Path) -> Path:
    """Per-Patient-ID sensitivity in each test fold, with the pooled and macro values marked."""
    figure, axis = plt.subplots(figsize=(DOUBLE_COLUMN, 2.5))
    eligible = patients[patients.sensitivity_defined]
    labels = []
    for position, (fold, group) in enumerate(eligible.groupby("fold", sort=True), start=1):
        values = group.sensitivity.to_numpy()
        axis.boxplot(
            values, positions=[position], widths=0.5, showfliers=False, patch_artist=False,
            boxprops={"color": AXIS, "linewidth": 0.8}, whiskerprops={"color": AXIS, "linewidth": 0.8},
            capprops={"color": AXIS, "linewidth": 0.8}, medianprops={"color": INK_SECONDARY, "linewidth": 0.8},
        )
        x = position + _jitter(len(group), seed=int(fold))
        large = group.n_positive.to_numpy() >= SMALL_ID_CELLS
        axis.scatter(x[large], values[large], s=12, color=BLUE, edgecolors="white", linewidths=0.4, zorder=3)
        axis.scatter(x[~large], values[~large], s=12, facecolors="white", edgecolors=BLUE, linewidths=0.8, zorder=3)
        row = folds.loc[folds.fold == fold].iloc[0]
        axis.hlines(row.pooled_sensitivity_recall, position - 0.3, position + 0.3, color=ORANGE, linewidth=2, zorder=4)
        axis.scatter([position + 0.38], [row.macro_sensitivity], marker="D", s=16, color=INK, zorder=4)
        labels.append(f"Fold {fold}\n{len(group)} IDs")
    axis.set_xticks(range(1, len(labels) + 1), labels)
    axis.set_ylim(-0.03, 1.03)
    axis.set_ylabel("Sensitivity per Patient-ID")
    handles = [
        Line2D([], [], marker="o", linestyle="", color=BLUE, markeredgecolor="white", markersize=4.5, label=f"Patient-ID, >= {SMALL_ID_CELLS} Parasitized cells"),
        Line2D([], [], marker="o", linestyle="", markerfacecolor="white", markeredgecolor=BLUE, markersize=4.5, label=f"Patient-ID, < {SMALL_ID_CELLS} Parasitized cells"),
        Line2D([], [], color=ORANGE, linewidth=2, label="Pooled (cell-weighted, M2)"),
        Line2D([], [], marker="D", linestyle="", color=INK, markersize=4, label="Patient-ID macro (M4)"),
    ]
    axis.legend(handles=handles, loc="lower left", ncols=2)
    return _save(figure, path)


def rate_vs_cells(patients: pd.DataFrame, path: Path, which: str = "fnr", annotate: int = 1, axis=None) -> Path | None:
    """FNR vs Parasitized cells per ID (``fnr``) or FPR vs Uninfected cells per ID (``fpr``), log x."""
    count, rate, defined, label_x, label_y = {
        "fnr": ("n_positive", "false_negative_rate", "sensitivity_defined", "Parasitized cells per Patient-ID", "False-negative rate"),
        "fpr": ("n_negative", "false_positive_rate", "specificity_defined", "Uninfected cells per Patient-ID", "False-positive rate"),
    }[which]
    own_figure = axis is None
    if own_figure:
        figure, axis = plt.subplots(figsize=(SINGLE_COLUMN, 2.4))
    rows = patients[patients[defined]]
    large = rows[count] >= SMALL_ID_CELLS
    axis.scatter(rows.loc[large, count], rows.loc[large, rate], s=12, color=BLUE, edgecolors="white", linewidths=0.4, zorder=3)
    axis.scatter(rows.loc[~large, count], rows.loc[~large, rate], s=12, facecolors="white", edgecolors=BLUE, linewidths=0.8, zorder=3)
    errors = rows.fn if which == "fnr" else rows.fp
    pooled = errors.sum() / rows[count].sum()
    axis.axhline(pooled, color=ORANGE, linewidth=1)
    axis.annotate(f"pooled {100 * pooled:.1f}%", (rows[count].min(), pooled), xytext=(0, 3),
                  textcoords="offset points", ha="left", va="bottom", color=INK_SECONDARY, fontsize=6.5)
    labelled = rows.assign(_errors=errors).nlargest(annotate, "_errors").sort_values(rate, ascending=False)
    for _, row in labelled.iterrows():
        axis.annotate(f"{row.patient_id}\n{int(row._errors)} errors", (row[count], row[rate]), xytext=(-12, 22), textcoords="offset points",
                      ha="right", va="bottom", fontsize=6, color=INK_SECONDARY,
                      arrowprops={"arrowstyle": "-", "color": INK_SECONDARY, "linewidth": 0.5, "shrinkA": 0, "shrinkB": 3})
    if which == "fnr":  # Parasitized counts span 1-600+; Uninfected counts are nearly constant, so stay linear
        axis.set_xscale("log")
    axis.set_ylim(-0.03, 1.03)
    axis.set_xlabel(label_x)
    axis.set_ylabel(label_y)
    axis.grid(True, axis="both")
    if own_figure:
        return _save(figure, path)
    return None


def paired_differences_panels(differences: pd.DataFrame, bootstrap: pd.DataFrame, threshold_pp: float, prediction_band: tuple[float, float], path: Path) -> Path:
    """Macro-minus-pooled differences per fold with 95% cluster-bootstrap CIs; sensitivity is primary."""
    metrics = [("sensitivity", "Sensitivity (primary)"), ("specificity", "Specificity (secondary)"), ("accuracy", "Accuracy (secondary)")]
    figure, axes = plt.subplots(1, 3, figsize=(DOUBLE_COLUMN, 2.4), sharey=True)
    for axis, (metric, title) in zip(axes, metrics):
        observed = differences[differences.metric == metric].sort_values("fold")
        ci = bootstrap[bootstrap.metric == metric].set_index("fold")
        folds = [str(f) for f in observed.fold]
        x = np.arange(len(folds))
        y = observed.difference_pp.to_numpy()
        low = np.array([ci.at[f, "ci_low_pp"] for f in folds])
        high = np.array([ci.at[f, "ci_high_pp"] for f in folds])
        if metric == "sensitivity":
            axis.axhspan(*prediction_band, color=BAND, zorder=0, linewidth=0)
            for sign in (-1, 1):
                axis.axhline(sign * threshold_pp, color=INK_SECONDARY, linewidth=0.8, linestyle=(0, (4, 2)))
        axis.axhline(0, color=INK_SECONDARY, linewidth=0.8)
        axis.errorbar(x, y, yerr=[y - low, high - y], fmt="o", color=BLUE, ecolor=INK_SECONDARY, elinewidth=0.8, capsize=2, markersize=4, zorder=3)
        mean_x = len(folds)
        mean_y = ci.at["mean", "observed_difference_pp"]
        axis.errorbar([mean_x], [mean_y], yerr=[[mean_y - ci.at["mean", "ci_low_pp"]], [ci.at["mean", "ci_high_pp"] - mean_y]],
                      fmt="D", color=INK, ecolor=INK, elinewidth=1, capsize=2.5, markersize=4.5, zorder=3)
        axis.set_xticks(list(x) + [mean_x], [f"F{f}" for f in folds] + ["Mean"])
        axis.set_xlim(-0.6, mean_x + 0.6)
        axis.set_title(title)
    axes[0].set_ylabel("Macro minus pooled (pp)")
    low, high = prediction_band
    handles = [
        Line2D([], [], marker="o", linestyle="", color=BLUE, markersize=4, label="Fold difference, 95% cluster-bootstrap CI"),
        Line2D([], [], marker="D", linestyle="", color=INK, markersize=4, label="Mean of 5 folds"),
        Patch(color=BAND, label=f"M3 predicted range ({low:g} to {high:g} pp)"),
        Line2D([], [], color=INK_SECONDARY, linewidth=0.8, linestyle=(0, (4, 2)), label=f"M3 decision threshold (+/-{threshold_pp} pp)"),
    ]
    figure.legend(handles=handles, loc="lower center", ncols=4, bbox_to_anchor=(0.5, -0.02))
    figure.tight_layout(rect=(0, 0.08, 1, 1))
    return _save(figure, path)


def reliability_diagram(bins: pd.DataFrame, brier: float, ece: float, path: Path) -> Path:
    """Observed Parasitized fraction vs mean predicted probability (10 equal-width bins), with bin counts."""
    figure, (top, bottom) = plt.subplots(2, 1, figsize=(SINGLE_COLUMN, 3.3), sharex=True, gridspec_kw={"height_ratios": [3, 1.2]})
    top.plot([0, 1], [0, 1], color=INK_SECONDARY, linewidth=0.8, linestyle=(0, (4, 2)))
    top.plot(bins.mean_probability, bins.fraction_parasitized, color=BLUE, linewidth=2, marker="o", markersize=4)
    top.set_ylabel("Observed Parasitized fraction")
    top.set_ylim(-0.02, 1.02)
    top.text(0.03, 0.95, f"Brier {brier:.4f}\nECE {ece:.4f}", va="top", fontsize=6.5, color=INK_SECONDARY)
    top.grid(True, axis="both")
    centres = (bins.bin_low + bins.bin_high) / 2
    bottom.bar(centres, bins.n_cells, width=0.096, color=BLUE)
    bottom.set_yscale("log")
    bottom.set_ylabel("Cells")
    bottom.set_xlabel("Predicted probability of Parasitized")
    bottom.set_xlim(0, 1)
    figure.tight_layout()
    return _save(figure, path)


def error_concentration(curves: pd.DataFrame, path: Path) -> Path:
    """Cumulative share of errors held by Patient-IDs ranked from most to fewest errors."""
    figure, axis = plt.subplots(figsize=(SINGLE_COLUMN, 2.5))
    axis.plot([0, 1], [0, 1], color=INK_SECONDARY, linewidth=0.8, linestyle=(0, (4, 2)))
    for kind, color, name in (("FN", BLUE, "False negatives"), ("FP", ORANGE, "False positives")):
        curve = curves[curves.error_type == kind]
        x = np.concatenate([[0], curve.share_of_ids.to_numpy()])
        y = np.concatenate([[0], curve.cumulative_share_of_errors.to_numpy()])
        axis.plot(x, y, color=color, linewidth=2, label=name)
    axis.set_xlabel("Share of eligible Patient-IDs (ranked by errors)")
    axis.set_ylabel("Cumulative share of errors")
    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1.02)
    axis.grid(True, axis="both")
    axis.legend(loc="lower right")
    return _save(figure, path)


def rates_vs_cells_panels(patients: pd.DataFrame, path: Path) -> Path:
    figure, axes = plt.subplots(1, 2, figsize=(DOUBLE_COLUMN, 2.4), sharey=True)
    rate_vs_cells(patients, path, "fnr", axis=axes[0])
    rate_vs_cells(patients, path, "fpr", axis=axes[1])
    axes[1].set_ylabel("False-positive rate")
    axes[1].tick_params(labelleft=True)
    figure.tight_layout()
    return _save(figure, path)
