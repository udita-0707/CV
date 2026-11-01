"""Patient-ID-stratified re-aggregation of the frozen M2 out-of-fold predictions (M4).

Every function is pure: it takes DataFrames/arrays and returns new ones. The
grouping key is the official NLM mapping key in ``patient_id``; nothing is
parsed from filenames. No function changes a probability, label, fold or the
0.5 threshold; only the aggregation of existing rows differs.
"""
from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd
from scipy import stats

from .evaluation import binary_metrics

EXPECTED_ROWS = 27_558
N_FOLDS = 5
THRESHOLD = 0.5
DECISION_THRESHOLD_PP = 1.68  # as written in milestones/m3/hypothesis.md
MIN_DIRECTIONAL_FOLDS = 4
POOLED_METRICS = ("accuracy", "sensitivity_recall", "specificity", "auc", "f1")
COUNT_COLUMNS = ("true_negative", "false_positive", "false_negative", "true_positive")
IDENTITY_COLUMNS = ("filename", "class_name", "label", "patient_id", "fold")

# metric -> (numerator, denominator) over per-ID confusion counts
RATIO_PARTS = {
    "sensitivity": ("tp", "n_positive"),
    "specificity": ("tn", "n_negative"),
    "accuracy": ("n_correct", "n_cells"),
}
POOLED_NAME = {"sensitivity": "sensitivity_recall", "specificity": "specificity", "accuracy": "accuracy"}


class ReuseAssertionError(AssertionError):
    """A frozen M2 artifact no longer matches what M4 is allowed to reuse."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ReuseAssertionError(message)


def check_reuse(
    predictions: pd.DataFrame,
    assignments: pd.DataFrame,
    fold_results: pd.DataFrame,
    baseline_results: pd.DataFrame,
    expected_rows: int = EXPECTED_ROWS,
    n_folds: int = N_FOLDS,
    tolerance: float = 1e-9,
) -> dict:
    """Fail loudly unless the OOF rows are exactly the saved M2 rows, folds and metrics."""
    checks: dict[str, object] = {}
    _require(len(predictions) == expected_rows, f"predictions has {len(predictions)} rows, expected {expected_rows}")
    _require(len(assignments) == expected_rows, f"fold_assignments has {len(assignments)} rows, expected {expected_rows}")
    checks["row_count"] = expected_rows

    _require(not predictions.relative_path.duplicated().any(), "relative_path is not unique in predictions")
    _require(not assignments.relative_path.duplicated().any(), "relative_path is not unique in fold_assignments")
    checks["unique_relative_path"] = True

    merged = predictions.merge(assignments, on="relative_path", how="outer", suffixes=("", "_m2"), indicator=True)
    _require(bool((merged._merge == "both").all()), "predictions and fold_assignments do not cover the same images")
    for column in IDENTITY_COLUMNS:
        mismatched = int((merged[column].astype(str) != merged[f"{column}_m2"].astype(str)).sum())
        _require(mismatched == 0, f"{mismatched} rows differ from fold_assignments in {column!r}")
    checks["identical_to_fold_assignments"] = list(IDENTITY_COLUMNS)

    _require(set(predictions.fold) == set(range(1, n_folds + 1)), f"folds are {sorted(set(predictions.fold))}")
    folds_per_id = predictions.groupby("patient_id").fold.nunique()
    _require(bool((folds_per_id == 1).all()), f"Patient-IDs in more than one fold: {list(folds_per_id[folds_per_id > 1].index)}")
    checks["patient_ids_in_one_fold"] = int(len(folds_per_id))

    label_matches_class = predictions.label.eq(predictions.class_name.eq("Parasitized").astype(int))
    _require(bool(label_matches_class.all()), "label does not match class_name (Parasitized = 1)")
    probability = predictions.probability_parasitized.to_numpy(dtype=float)
    _require(bool(np.isfinite(probability).all() and (probability >= 0).all() and (probability <= 1).all()), "probabilities outside [0, 1]")
    thresholded = (probability >= THRESHOLD).astype(int)
    _require(bool((thresholded == predictions.prediction.to_numpy()).all()), "saved prediction != (probability >= 0.5)")
    checks["prediction_equals_threshold_0_5"] = True

    recomputed = pooled_fold_metrics(predictions).set_index("fold")
    saved = fold_results.set_index("fold")
    max_abs = 0.0
    for fold in range(1, n_folds + 1):
        for metric in POOLED_METRICS:
            difference = abs(recomputed.at[fold, metric] - saved.at[fold, metric])
            max_abs = max(max_abs, difference)
            _require(difference <= tolerance, f"fold {fold} {metric} differs from fold_results.csv by {difference:.3e}")
        for column in COUNT_COLUMNS:
            _require(int(recomputed.at[fold, column]) == int(saved.at[fold, column]), f"fold {fold} {column} differs")
        _require(int(recomputed.at[fold, "test_samples"]) == int(saved.at[fold, "test_samples"]), f"fold {fold} size differs")
    checks["pooled_metrics_equal_fold_results"] = {"tolerance": tolerance, "max_abs_difference": max_abs}

    summary = baseline_results.set_index("metric")
    for metric in POOLED_METRICS:
        mean_difference = abs(saved[metric].mean() - summary.at[metric, "mean"])
        sd_difference = abs(saved[metric].std(ddof=1) - summary.at[metric, "standard_deviation"])
        _require(mean_difference <= tolerance and sd_difference <= tolerance, f"{metric} mean/SD differ from baseline_results.csv")
    checks["fold_mean_sd_equal_baseline_results"] = True
    return checks


def pooled_fold_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """M2's pooled, cell-weighted metrics per fold, computed with ``src.evaluation.binary_metrics``."""
    rows = []
    for fold, group in predictions.groupby("fold", sort=True):
        metrics = binary_metrics(group.label.to_numpy(), group.probability_parasitized.to_numpy())
        metrics.update({"fold": int(fold), "test_samples": len(group)})
        rows.append(metrics)
    return pd.DataFrame(rows)


def per_patient_metrics(predictions: pd.DataFrame) -> pd.DataFrame:
    """One row per (fold, Patient-ID). Undefined ratios are NaN with an explicit flag, never dropped."""
    predicted = (predictions.probability_parasitized.to_numpy(dtype=float) >= THRESHOLD).astype(int)
    label = predictions.label.to_numpy(dtype=int)
    frame = pd.DataFrame(
        {
            "fold": predictions.fold.to_numpy(),
            "patient_id": predictions.patient_id.to_numpy(),
            "tp": (label == 1) & (predicted == 1),
            "fn": (label == 1) & (predicted == 0),
            "tn": (label == 0) & (predicted == 0),
            "fp": (label == 0) & (predicted == 1),
            "probability": predictions.probability_parasitized.to_numpy(dtype=float),
        }
    )
    grouped = frame.groupby(["fold", "patient_id"], sort=True)
    patients = grouped[["tp", "fn", "tn", "fp"]].sum().astype(int)
    patients["mean_probability"] = grouped.probability.mean()
    patients = patients.reset_index()
    patients["n_positive"] = patients.tp + patients.fn
    patients["n_negative"] = patients.tn + patients.fp
    patients["n_cells"] = patients.n_positive + patients.n_negative
    patients["n_correct"] = patients.tp + patients.tn
    patients["n_errors"] = patients.fn + patients.fp
    patients["sensitivity_defined"] = patients.n_positive > 0
    patients["specificity_defined"] = patients.n_negative > 0
    patients["accuracy"] = patients.n_correct / patients.n_cells
    patients["sensitivity"] = (patients.tp / patients.n_positive).where(patients.sensitivity_defined)
    patients["false_negative_rate"] = 1 - patients.sensitivity
    patients["specificity"] = (patients.tn / patients.n_negative).where(patients.specificity_defined)
    patients["false_positive_rate"] = 1 - patients.specificity
    order = [
        "fold", "patient_id", "n_cells", "n_positive", "n_negative", "tp", "fn", "tn", "fp",
        "n_correct", "n_errors", "accuracy", "sensitivity_defined", "sensitivity", "false_negative_rate",
        "specificity_defined", "specificity", "false_positive_rate", "mean_probability",
    ]
    return patients[order]


def distribution(values: Sequence[float] | pd.Series) -> dict[str, float]:
    """N, mean, SD (ddof=1), quartiles, IQR, min and max of the defined (non-NaN) values."""
    array = np.asarray(values, dtype=float)
    array = array[~np.isnan(array)]
    if array.size == 0:
        return {key: float("nan") for key in ("mean", "sd", "q1", "median", "q3", "iqr", "min", "max")} | {"n": 0}
    q1, median, q3 = np.percentile(array, [25, 50, 75])
    return {
        "n": int(array.size),
        "mean": float(array.mean()),
        "sd": float(array.std(ddof=1)) if array.size > 1 else float("nan"),
        "q1": float(q1),
        "median": float(median),
        "q3": float(q3),
        "iqr": float(q3 - q1),
        "min": float(array.min()),
        "max": float(array.max()),
    }


def macro_metric(patients: pd.DataFrame, metric: str, min_cells: int = 1) -> tuple[float, int]:
    """Unweighted mean over Patient-IDs whose denominator for ``metric`` is at least ``min_cells``."""
    numerator, denominator = RATIO_PARTS[metric]
    eligible = patients[patients[denominator] >= min_cells]
    if eligible.empty:
        return float("nan"), 0
    return float((eligible[numerator] / eligible[denominator]).mean()), int(len(eligible))


def weighted_by_cells(patients: pd.DataFrame, metric: str) -> float:
    """Per-ID ratio weighted by that ID's denominator; algebraically the pooled value (A1 check)."""
    numerator, denominator = RATIO_PARTS[metric]
    eligible = patients[patients[denominator] > 0]
    ratios = eligible[numerator] / eligible[denominator]
    return float(np.average(ratios, weights=eligible[denominator]))


def fold_metrics(predictions: pd.DataFrame, patients: pd.DataFrame) -> pd.DataFrame:
    """Per fold: pooled metrics, Patient-ID-macro metrics, per-ID distributions and undefined counts."""
    pooled = pooled_fold_metrics(predictions).set_index("fold")
    rows = []
    for fold, group in patients.groupby("fold", sort=True):
        row: dict[str, object] = {"fold": int(fold)}
        for metric in POOLED_METRICS + COUNT_COLUMNS + ("test_samples",):
            row[f"pooled_{metric}" if metric in POOLED_METRICS else metric] = pooled.at[fold, metric]
        for metric in RATIO_PARTS:
            row[f"macro_{metric}"], row[f"n_ids_{metric}"] = macro_metric(group, metric)
        row["n_ids_total"] = int(len(group))
        row["n_ids_sensitivity_undefined"] = int((~group.sensitivity_defined).sum())
        row["n_ids_specificity_undefined"] = int((~group.specificity_defined).sum())
        for column in ("sensitivity", "false_negative_rate", "specificity", "accuracy"):
            for key, value in distribution(group[column]).items():
                row[f"id_{column}_{key}"] = value
        rows.append(row)
    return pd.DataFrame(rows)


def paired_differences(folds: pd.DataFrame, metric: str = "sensitivity") -> pd.DataFrame:
    """Per-fold macro-minus-pooled difference for one metric, in proportion and percentage points."""
    pooled = folds[f"pooled_{POOLED_NAME[metric]}"]
    macro = folds[f"macro_{metric}"]
    difference = macro - pooled
    return pd.DataFrame(
        {
            "fold": folds.fold.astype(int),
            "metric": metric,
            "n_ids_eligible": folds[f"n_ids_{metric}"].astype(int),
            "pooled": pooled,
            "macro": macro,
            "difference": difference,
            "difference_pp": 100 * difference,
            "direction": np.select([difference < 0, difference > 0], ["negative", "positive"], "zero"),
        }
    )


def decide_verdict(
    differences_pp: Sequence[float],
    threshold_pp: float = DECISION_THRESHOLD_PP,
    min_directional: int = MIN_DIRECTIONAL_FOLDS,
    reuse_passed: bool = True,
    denominators_available: bool = True,
) -> dict:
    """Apply the M3 decision rule exactly: SUPPORTED, UNSUPPORTED or INCONCLUSIVE."""
    values = np.asarray(differences_pp, dtype=float)
    n_negative = int((values < 0).sum())
    n_positive = int((values > 0).sum())
    mean_pp = float(values.mean()) if values.size and np.isfinite(values).all() else float("nan")
    # compare at 1e-9 pp so float summation error cannot move a mean of exactly -1.68 across the line
    supported_rule = n_negative >= min_directional and round(mean_pp, 9) <= -threshold_pp
    unsupported_rule = n_positive >= min_directional and round(mean_pp, 9) >= threshold_pp
    reasons = []
    if not reuse_passed:
        reasons.append("a reuse assertion for the M2 folds/predictions failed")
    if not denominators_available or not np.isfinite(values).all():
        reasons.append("a group denominator was unavailable")
    if reasons:
        verdict = "INCONCLUSIVE"
    elif supported_rule:
        verdict = "SUPPORTED"
        reasons.append(f"{n_negative}/{values.size} differences negative and mean {mean_pp:+.3f} pp <= -{threshold_pp} pp")
    elif unsupported_rule:
        verdict = "UNSUPPORTED"
        reasons.append(f"{n_positive}/{values.size} differences positive and mean {mean_pp:+.3f} pp >= +{threshold_pp} pp")
    else:
        verdict = "INCONCLUSIVE"
        if n_negative < min_directional and n_positive < min_directional:
            reasons.append(f"mixed signs: {n_negative} negative, {n_positive} positive (need >= {min_directional} in one direction)")
        if abs(mean_pp) < threshold_pp:
            reasons.append(f"|mean| {abs(mean_pp):.3f} pp < {threshold_pp} pp")
        if n_negative >= min_directional and mean_pp > -threshold_pp:
            reasons.append("direction negative but magnitude below the threshold")
        if n_positive >= min_directional and mean_pp < threshold_pp:
            reasons.append("direction positive but magnitude below the threshold")
    return {
        "verdict": verdict,
        "n_folds": int(values.size),
        "n_negative": n_negative,
        "n_positive": n_positive,
        "mean_difference_pp": mean_pp,
        "threshold_pp": threshold_pp,
        "supported_rule_met": bool(supported_rule),
        "unsupported_rule_met": bool(unsupported_rule),
        "reasons": reasons,
    }


def t_interval(values: Sequence[float], confidence: float = 0.95) -> dict[str, float]:
    """Across-fold t-interval for the mean (df = n - 1); a crude interval for n = 5."""
    array = np.asarray(values, dtype=float)
    mean = float(array.mean())
    sd = float(array.std(ddof=1))
    half_width = float(stats.t.ppf(0.5 + confidence / 2, df=array.size - 1) * sd / np.sqrt(array.size))
    return {"mean": mean, "sd": sd, "low": mean - half_width, "high": mean + half_width, "df": int(array.size - 1)}


def min_two_sided_wilcoxon_p(n: int) -> float:
    """Smallest attainable exact two-sided signed-rank p-value with n non-zero pairs: 2 / 2**n."""
    return 2.0 / 2**n


# --------------------------------------------------------------------------- ablations


def a1_weighting(patients: pd.DataFrame, folds: pd.DataFrame, tolerance: float = 1e-12) -> pd.DataFrame:
    """Pooled vs Patient-ID macro vs cell-count-weighted per-ID sensitivity (must equal pooled)."""
    rows = []
    for fold, group in patients.groupby("fold", sort=True):
        pooled = float(folds.loc[folds.fold == fold, "pooled_sensitivity_recall"].iloc[0])
        weighted = weighted_by_cells(group, "sensitivity")
        if abs(weighted - pooled) > tolerance:
            raise AssertionError(f"fold {fold}: cell-weighted per-ID sensitivity {weighted} != pooled {pooled}")
        macro, n_ids = macro_metric(group, "sensitivity")
        rows.append(
            {
                "fold": int(fold),
                "n_ids_with_positive_cells": n_ids,
                "pooled_cell_weighted": pooled,
                "patient_id_macro": macro,
                "per_id_weighted_by_positive_cells": weighted,
                "weighted_minus_pooled": weighted - pooled,
                "macro_minus_pooled_pp": 100 * (macro - pooled),
            }
        )
    return pd.DataFrame(rows)


def a2_eligibility(patients: pd.DataFrame, folds: pd.DataFrame, minimums: Sequence[int] = (1, 10, 25)) -> pd.DataFrame:
    """Macro sensitivity using only IDs with at least k Parasitized cells, against the unchanged pooled value."""
    rows = []
    for fold, group in patients.groupby("fold", sort=True):
        pooled = float(folds.loc[folds.fold == fold, "pooled_sensitivity_recall"].iloc[0])
        with_positive = group[group.n_positive > 0]
        for minimum in minimums:
            kept = with_positive[with_positive.n_positive >= minimum]
            macro, n_kept = macro_metric(group, "sensitivity", min_cells=minimum)
            pooled_kept = float(kept.tp.sum() / kept.n_positive.sum()) if n_kept else float("nan")
            rows.append(
                {
                    "fold": int(fold),
                    "min_positive_cells": int(minimum),
                    "n_ids_kept": n_kept,
                    "n_ids_excluded": int(len(with_positive) - n_kept),
                    "positive_cells_kept": int(kept.n_positive.sum()),
                    "share_positive_cells_kept": float(kept.n_positive.sum() / with_positive.n_positive.sum()),
                    "macro_sensitivity": macro,
                    "pooled_sensitivity_all": pooled,
                    "difference_pp": 100 * (macro - pooled),
                    "pooled_sensitivity_kept_ids": pooled_kept,
                }
            )
    return pd.DataFrame(rows)


def summarise_by(frame: pd.DataFrame, key: str, value: str = "difference_pp") -> pd.DataFrame:
    """Five-fold mean, SD and sign counts of ``value`` for each level of ``key``."""
    grouped = frame.groupby(key, sort=True)[value]
    return pd.DataFrame(
        {
            "mean_pp": grouped.mean(),
            "sd_pp": grouped.std(ddof=1),
            "n_negative": grouped.apply(lambda s: int((s < 0).sum())),
            "n_positive": grouped.apply(lambda s: int((s > 0).sum())),
        }
    ).reset_index()


def a3_leave_one_id_out(patients: pd.DataFrame, primary: pd.DataFrame, threshold_pp: float = DECISION_THRESHOLD_PP) -> pd.DataFrame:
    """Remove one Patient-ID (all its cells) at a time; recompute that fold's paired difference and the verdict."""
    observed = primary.set_index("fold").difference_pp
    observed_verdict = decide_verdict(observed.to_numpy(), threshold_pp)["verdict"]
    rows = []
    for fold, group in patients.groupby("fold", sort=True):
        for patient_id in group.loc[group.n_positive > 0, "patient_id"]:
            remaining = group[group.patient_id != patient_id]
            with_positive = remaining[remaining.n_positive > 0]
            pooled = float(with_positive.tp.sum() / with_positive.n_positive.sum())
            macro, n_ids = macro_metric(remaining, "sensitivity")
            difference_pp = 100 * (macro - pooled)
            differences = observed.copy()
            differences.loc[fold] = difference_pp
            verdict = decide_verdict(differences.to_numpy(), threshold_pp)
            removed = group[group.patient_id == patient_id].iloc[0]
            rows.append(
                {
                    "fold": int(fold),
                    "removed_patient_id": patient_id,
                    "removed_n_positive": int(removed.n_positive),
                    "removed_sensitivity": float(removed.sensitivity),
                    "n_ids_remaining": n_ids,
                    "pooled_without": pooled,
                    "macro_without": macro,
                    "difference_pp_without": difference_pp,
                    "observed_difference_pp": float(observed.loc[fold]),
                    "change_pp": difference_pp - float(observed.loc[fold]),
                    "mean_difference_pp_if_removed": verdict["mean_difference_pp"],
                    "verdict_if_removed": verdict["verdict"],
                    "verdict_changes": verdict["verdict"] != observed_verdict,
                }
            )
    return pd.DataFrame(rows)


def a3_summary(loo: pd.DataFrame) -> pd.DataFrame:
    """Per fold: range of the paired difference under single-ID deletion and the most influential ID."""
    rows = []
    for fold, group in loo.groupby("fold", sort=True):
        top = group.loc[group.change_pp.abs().idxmax()]
        rows.append(
            {
                "fold": int(fold),
                "n_deletions": int(len(group)),
                "observed_difference_pp": float(group.observed_difference_pp.iloc[0]),
                "min_difference_pp_without": float(group.difference_pp_without.min()),
                "max_difference_pp_without": float(group.difference_pp_without.max()),
                "max_abs_change_pp": float(abs(top.change_pp)),
                "most_influential_patient_id": top.removed_patient_id,
                "most_influential_n_positive": int(top.removed_n_positive),
                "most_influential_sensitivity": float(top.removed_sensitivity),
                "deletions_changing_verdict": int(group.verdict_changes.sum()),
            }
        )
    return pd.DataFrame(rows)


def bootstrap_resample_weights(n_ids: int, n_resamples: int, rng: np.random.Generator) -> np.ndarray:
    """Multiplicity of each Patient-ID in each cluster-bootstrap resample, shape (n_resamples, n_ids)."""
    draws = rng.integers(0, n_ids, size=(n_resamples, n_ids))
    return (draws[:, :, None] == np.arange(n_ids)[None, None, :]).sum(axis=1)


def bootstrap_differences(group: pd.DataFrame, weights: np.ndarray, metric: str) -> np.ndarray:
    """Macro-minus-pooled difference (pp) on each resample; NaN when a resample has no eligible ID."""
    numerator_name, denominator_name = RATIO_PARTS[metric]
    numerator = group[numerator_name].to_numpy(dtype=float)
    denominator = group[denominator_name].to_numpy(dtype=float)
    eligible = denominator > 0
    ratio = np.divide(numerator, denominator, out=np.zeros_like(numerator), where=eligible)
    with np.errstate(invalid="ignore", divide="ignore"):
        pooled = (weights @ numerator) / (weights @ denominator)
        eligible_weights = weights * eligible
        macro = (eligible_weights @ ratio) / eligible_weights.sum(axis=1)
    return 100 * (macro - pooled)


def a4_bootstrap(
    patients: pd.DataFrame,
    metrics: Sequence[str] = ("sensitivity", "specificity", "accuracy"),
    n_resamples: int = 2_000,
    seed: int = 42,
    confidence: float = 0.95,
) -> tuple[pd.DataFrame, dict[str, np.ndarray]]:
    """Cluster bootstrap over Patient-IDs within each fold; the same resamples serve every metric."""
    rng = np.random.default_rng(seed)
    tail = 100 * (1 - confidence) / 2
    fold_weights = {
        int(fold): bootstrap_resample_weights(len(group), n_resamples, rng)
        for fold, group in patients.groupby("fold", sort=True)
    }
    rows = []
    replicates: dict[str, np.ndarray] = {}
    for metric in metrics:
        per_fold = []
        for fold, group in patients.groupby("fold", sort=True):
            draws = bootstrap_differences(group, fold_weights[int(fold)], metric)
            per_fold.append(draws)
            observed_macro, _ = macro_metric(group, metric)
            numerator, denominator = RATIO_PARTS[metric]
            observed = 100 * (observed_macro - group[numerator].sum() / group[denominator].sum())
            rows.append(_bootstrap_row(metric, str(int(fold)), observed, draws, tail, n_resamples, seed))
        stacked = np.vstack(per_fold)
        mean_draws = stacked.mean(axis=0)
        observed_mean = float(np.mean([row["observed_difference_pp"] for row in rows if row["metric"] == metric]))
        rows.append(_bootstrap_row(metric, "mean", observed_mean, mean_draws, tail, n_resamples, seed))
        replicates[metric] = stacked
    return pd.DataFrame(rows), replicates


def _bootstrap_row(metric: str, fold: str, observed: float, draws: np.ndarray, tail: float, n_resamples: int, seed: int) -> dict:
    valid = draws[np.isfinite(draws)]
    low, high = np.percentile(valid, [tail, 100 - tail])
    return {
        "metric": metric,
        "fold": fold,
        "observed_difference_pp": float(observed),
        "bootstrap_mean_pp": float(valid.mean()),
        "bootstrap_se_pp": float(valid.std(ddof=1)),
        "ci_low_pp": float(low),
        "ci_high_pp": float(high),
        "share_resamples_below_zero": float((valid < 0).mean()),
        "n_valid_resamples": int(valid.size),
        "n_resamples": int(n_resamples),
        "seed": int(seed),
    }


def a5_secondary(folds: pd.DataFrame, bootstrap: pd.DataFrame) -> pd.DataFrame:
    """Macro-vs-pooled comparison for specificity and accuracy (M3 secondary metrics), with distributions."""
    rows = []
    for metric in ("specificity", "accuracy"):
        differences = paired_differences(folds, metric)
        ci = bootstrap[bootstrap.metric == metric].set_index("fold")
        for _, row in differences.iterrows():
            fold = int(row.fold)
            stats_row = folds.loc[folds.fold == fold].iloc[0]
            rows.append(
                {
                    "metric": metric,
                    "fold": str(fold),
                    "n_ids_eligible": int(row.n_ids_eligible),
                    "pooled": float(row.pooled),
                    "macro": float(row.macro),
                    "difference_pp": float(row.difference_pp),
                    "ci_low_pp": float(ci.at[str(fold), "ci_low_pp"]),
                    "ci_high_pp": float(ci.at[str(fold), "ci_high_pp"]),
                    "id_sd": float(stats_row[f"id_{metric}_sd"]),
                    "id_iqr": float(stats_row[f"id_{metric}_iqr"]),
                    "id_min": float(stats_row[f"id_{metric}_min"]),
                    "id_max": float(stats_row[f"id_{metric}_max"]),
                }
            )
        rows.append(
            {
                "metric": metric,
                "fold": "mean",
                "n_ids_eligible": int(differences.n_ids_eligible.sum()),
                "pooled": float(differences.pooled.mean()),
                "macro": float(differences.macro.mean()),
                "difference_pp": float(differences.difference_pp.mean()),
                "ci_low_pp": float(ci.at["mean", "ci_low_pp"]),
                "ci_high_pp": float(ci.at["mean", "ci_high_pp"]),
                "id_sd": float("nan"),
                "id_iqr": float("nan"),
                "id_min": float("nan"),
                "id_max": float("nan"),
            }
        )
    return pd.DataFrame(rows)
