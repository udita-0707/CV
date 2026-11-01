"""M5 prediction-level failure analysis on the frozen M2 OOF predictions (pure functions)."""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats

from .patient_stratified import THRESHOLD

ERROR_KINDS = {
    # kind -> (error count column, cells-at-risk column, rate column)
    "FN": ("fn", "n_positive", "false_negative_rate"),
    "FP": ("fp", "n_negative", "false_positive_rate"),
}
CELL_COUNT_BINS = (1, 10, 25, 100, 300, np.inf)


def error_table(patients: pd.DataFrame, kind: str) -> pd.DataFrame:
    """Patient-IDs at risk of ``kind`` errors, ranked by error count, with shares of all such errors."""
    errors, cells, rate = ERROR_KINDS[kind]
    at_risk = patients[patients[cells] > 0].copy()
    at_risk = at_risk.sort_values([errors, "patient_id"], ascending=[False, True]).reset_index(drop=True)
    total = at_risk[errors].sum()
    return pd.DataFrame(
        {
            "error_type": kind,
            "rank": np.arange(1, len(at_risk) + 1),
            "fold": at_risk.fold,
            "patient_id": at_risk.patient_id,
            "cells_at_risk": at_risk[cells],
            "errors": at_risk[errors],
            "error_rate": at_risk[rate],
            "share_of_errors": at_risk[errors] / total,
            "cumulative_share_of_errors": at_risk[errors].cumsum() / total,
            "share_of_ids": np.arange(1, len(at_risk) + 1) / len(at_risk),
        }
    )


def concentration_summary(table: pd.DataFrame) -> dict:
    """How few Patient-IDs hold how much of one error type."""
    cumulative = table.cumulative_share_of_errors.to_numpy()
    return {
        "error_type": table.error_type.iloc[0],
        "total_errors": int(table.errors.sum()),
        "ids_at_risk": int(len(table)),
        "ids_with_any_error": int((table.errors > 0).sum()),
        "top1_share": float(cumulative[0]),
        "top5_share": float(cumulative[4]),
        "top10_share": float(cumulative[9]),
        "ids_for_50pct": int(np.searchsorted(cumulative, 0.5) + 1),
        "ids_for_80pct": int(np.searchsorted(cumulative, 0.8) + 1),
    }


def errors_by_fold(patients: pd.DataFrame) -> pd.DataFrame:
    """Error counts per fold and how much of each fold's FN/FP total its top Patient-ID holds."""
    rows = []
    for fold, group in patients.groupby("fold", sort=True):
        top_fn = group.loc[group.fn.idxmax()]
        top_fp = group.loc[group.fp.idxmax()]
        rows.append(
            {
                "fold": int(fold),
                "false_negatives": int(group.fn.sum()),
                "false_positives": int(group.fp.sum()),
                "pooled_fnr": float(group.fn.sum() / group.n_positive.sum()),
                "pooled_fpr": float(group.fp.sum() / group.n_negative.sum()),
                "top_fn_patient_id": top_fn.patient_id,
                "top_fn_count": int(top_fn.fn),
                "top_fn_share_of_fold": float(top_fn.fn / group.fn.sum()),
                "top_fn_n_positive": int(top_fn.n_positive),
                "top_fp_patient_id": top_fp.patient_id,
                "top_fp_count": int(top_fp.fp),
                "top_fp_share_of_fold": float(top_fp.fp / group.fp.sum()),
            }
        )
    return pd.DataFrame(rows)


def errors_vs_cells(patients: pd.DataFrame, edges: tuple = CELL_COUNT_BINS) -> pd.DataFrame:
    """Per-ID FNR by bins of Parasitized-cell count: pooled vs mean of per-ID rates."""
    at_risk = patients[patients.n_positive > 0].copy()
    labels = [f"{int(low)}-{int(high) - 1}" if np.isfinite(high) else f"{int(low)}+" for low, high in zip(edges[:-1], edges[1:])]
    at_risk["cells_bin"] = pd.cut(at_risk.n_positive, bins=list(edges), right=False, labels=labels)
    grouped = at_risk.groupby("cells_bin", observed=False)
    table = pd.DataFrame(
        {
            "n_ids": grouped.size(),
            "parasitized_cells": grouped.n_positive.sum(),
            "false_negatives": grouped.fn.sum(),
            "share_of_all_fn": grouped.fn.sum() / at_risk.fn.sum(),
            "pooled_fnr": grouped.fn.sum() / grouped.n_positive.sum(),
            "mean_id_fnr": grouped.false_negative_rate.mean(),
            "sd_id_fnr": grouped.false_negative_rate.std(ddof=1),
            "max_id_fnr": grouped.false_negative_rate.max(),
        }
    )
    return table.reset_index()


def rank_correlations(patients: pd.DataFrame) -> pd.DataFrame:
    """Descriptive Spearman correlations between per-ID error rate and cells at risk (no inference)."""
    rows = []
    for kind, (_, cells, rate) in ERROR_KINDS.items():
        at_risk = patients[patients[cells] > 0]
        rho = stats.spearmanr(at_risk[cells], at_risk[rate]).statistic
        rows.append({"error_type": kind, "n_ids": int(len(at_risk)), "spearman_rho": float(rho)})
    return pd.DataFrame(rows)


def confident_errors(predictions: pd.DataFrame, high: float = 0.9, low: float = 0.1) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Cells wrong with p > high (FP) or p < low (FN), and a summary per error type."""
    p = predictions.probability_parasitized
    wrong_fp = (predictions.label == 0) & (p >= THRESHOLD)
    wrong_fn = (predictions.label == 1) & (p < THRESHOLD)
    confident = predictions[(wrong_fp & (p > high)) | (wrong_fn & (p < low))].copy()
    confident["error_type"] = np.where(confident.label == 1, "FN", "FP")
    confident = confident.sort_values(["error_type", "probability_parasitized", "relative_path"])
    rows = []
    for kind, wrong, rule in (("FN", wrong_fn, f"p < {low}"), ("FP", wrong_fp, f"p > {high}")):
        subset = confident[confident.error_type == kind]
        counts = subset.patient_id.value_counts()
        rows.append(
            {
                "error_type": kind,
                "rule": rule,
                "confident_errors": int(len(subset)),
                "all_errors": int(wrong.sum()),
                "share_of_errors": float(len(subset) / wrong.sum()),
                "n_patient_ids": int(subset.patient_id.nunique()),
                "top_patient_id": counts.index[0] if len(counts) else "",
                "top_patient_id_count": int(counts.iloc[0]) if len(counts) else 0,
                "top_patient_id_share": float(counts.iloc[0] / len(subset)) if len(counts) else float("nan"),
            }
        )
    return confident, pd.DataFrame(rows)


def calibration_bins(label: np.ndarray, probability: np.ndarray, n_bins: int = 10) -> pd.DataFrame:
    """Equal-width reliability bins; the last bin includes p = 1."""
    edges = np.linspace(0, 1, n_bins + 1)
    index = np.clip(np.digitize(probability, edges[1:-1], right=False), 0, n_bins - 1)
    rows = []
    for b in range(n_bins):
        mask = index == b
        rows.append(
            {
                "bin_low": float(edges[b]),
                "bin_high": float(edges[b + 1]),
                "n_cells": int(mask.sum()),
                "mean_probability": float(probability[mask].mean()) if mask.any() else float("nan"),
                "fraction_parasitized": float(label[mask].mean()) if mask.any() else float("nan"),
            }
        )
    table = pd.DataFrame(rows)
    table["abs_gap"] = (table.mean_probability - table.fraction_parasitized).abs()
    return table


def expected_calibration_error(bins: pd.DataFrame) -> float:
    filled = bins[bins.n_cells > 0]
    return float((filled.abs_gap * filled.n_cells).sum() / filled.n_cells.sum())


def brier_score(label: np.ndarray, probability: np.ndarray) -> float:
    return float(np.mean((probability - label) ** 2))


def calibration_summary(predictions: pd.DataFrame, n_bins: int = 10) -> pd.DataFrame:
    """Brier score and ECE overall and per fold."""
    rows = []
    for fold, group in [("all", predictions), *predictions.groupby("fold", sort=True)]:
        y = group.label.to_numpy(dtype=float)
        p = group.probability_parasitized.to_numpy(dtype=float)
        rows.append(
            {
                "fold": str(fold),
                "n_cells": int(len(group)),
                "brier": brier_score(y, p),
                "ece": expected_calibration_error(calibration_bins(y, p, n_bins)),
                "mean_probability": float(p.mean()),
                "fraction_parasitized": float(y.mean()),
            }
        )
    return pd.DataFrame(rows)


def sd_drivers(patients: pd.DataFrame) -> pd.DataFrame:
    """Per fold: per-ID sensitivity SD, and the single ID whose removal lowers it most."""
    rows = []
    for fold, group in patients.groupby("fold", sort=True):
        eligible = group[group.sensitivity_defined]
        sd = float(eligible.sensitivity.std(ddof=1))
        without = {pid: float(eligible.loc[eligible.patient_id != pid, "sensitivity"].std(ddof=1)) for pid in eligible.patient_id}
        driver = min(without, key=without.get)
        row = eligible.set_index("patient_id").loc[driver]
        rows.append(
            {
                "fold": int(fold),
                "id_sensitivity_sd": sd,
                "driver_patient_id": driver,
                "sd_without_driver": without[driver],
                "sd_reduction": sd - without[driver],
                "sd_reduction_share": (sd - without[driver]) / sd,
                "driver_sensitivity": float(row.sensitivity),
                "driver_n_positive": int(row.n_positive),
                "driver_share_of_fold_fn": float(row.fn / eligible.fn.sum()),
            }
        )
    table = pd.DataFrame(rows)
    table["largest_sd_fold"] = table.id_sensitivity_sd == table.id_sensitivity_sd.max()
    return table
