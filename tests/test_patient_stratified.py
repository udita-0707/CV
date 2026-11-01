"""Unit tests for the M4 Patient-ID-stratified aggregation, on small hand-checkable data."""
from __future__ import annotations

import math

import numpy as np
import pandas as pd
import pytest

from src import patient_stratified as ps


def _cells(fold: int, patient_id: str, tp: int = 0, fn: int = 0, tn: int = 0, fp: int = 0) -> list[dict]:
    """Rows with probabilities that land on the requested side of 0.5."""
    spec = [(1, 0.9, tp), (1, 0.1, fn), (0, 0.1, tn), (0, 0.9, fp)]
    rows = []
    for label, probability, count in spec:
        for index in range(count):
            rows.append(
                {
                    "relative_path": f"cell_images/{patient_id}_{label}_{probability}_{index}.png",
                    "filename": f"{patient_id}_{label}_{probability}_{index}.png",
                    "class_name": "Parasitized" if label else "Uninfected",
                    "label": label,
                    "patient_id": patient_id,
                    "fold": fold,
                    "probability_parasitized": probability,
                    "prediction": int(probability >= 0.5),
                }
            )
    return rows


@pytest.fixture
def toy() -> pd.DataFrame:
    # fold 1: A sens 1.0 (10 pos), B sens 0.5 (2 pos), C negative-only
    # fold 2: D sens 0.8 (5 pos), E sens 0.0 (1 pos)
    rows = (
        _cells(1, "A", tp=10, tn=4, fp=1)
        + _cells(1, "B", tp=1, fn=1, tn=3)
        + _cells(1, "C", tn=5, fp=1)
        + _cells(2, "D", tp=4, fn=1, tn=2)
        + _cells(2, "E", fn=1, tn=6)
    )
    return pd.DataFrame(rows)


def test_per_patient_counts_and_undefined_flags(toy):
    patients = ps.per_patient_metrics(toy).set_index("patient_id")
    assert patients.loc["A", ["tp", "fn", "tn", "fp"]].tolist() == [10, 0, 4, 1]
    assert patients.loc["B", "sensitivity"] == 0.5
    assert patients.loc["B", "false_negative_rate"] == 0.5
    assert not patients.loc["C", "sensitivity_defined"]
    assert math.isnan(patients.loc["C", "sensitivity"])
    assert patients.loc["C", "specificity"] == pytest.approx(5 / 6)
    assert patients.loc["E", "sensitivity"] == 0.0
    assert patients.loc["A", "accuracy"] == pytest.approx(14 / 15)
    assert len(patients) == 5  # no ID silently dropped


def test_fold_metrics_macro_and_pooled(toy):
    patients = ps.per_patient_metrics(toy)
    folds = ps.fold_metrics(toy, patients).set_index("fold")
    assert folds.at[1, "pooled_sensitivity_recall"] == pytest.approx(11 / 12)
    assert folds.at[1, "macro_sensitivity"] == pytest.approx((1.0 + 0.5) / 2)
    assert folds.at[1, "n_ids_sensitivity"] == 2
    assert folds.at[1, "n_ids_sensitivity_undefined"] == 1
    assert folds.at[1, "n_ids_specificity_undefined"] == 0
    assert folds.at[2, "macro_sensitivity"] == pytest.approx(0.4)
    assert folds.at[2, "pooled_sensitivity_recall"] == pytest.approx(4 / 6)
    assert folds.at[1, "macro_specificity"] == pytest.approx((0.8 + 1.0 + 5 / 6) / 3)


def test_paired_differences_sign_and_units(toy):
    patients = ps.per_patient_metrics(toy)
    diffs = ps.paired_differences(ps.fold_metrics(toy, patients), "sensitivity")
    assert diffs.difference_pp.iloc[0] == pytest.approx(100 * (0.75 - 11 / 12))
    assert diffs.direction.tolist() == ["negative", "negative"]


def test_distribution_summary():
    summary = ps.distribution([0.0, 0.5, 1.0, float("nan")])
    assert summary["n"] == 3
    assert summary["mean"] == pytest.approx(0.5)
    assert summary["sd"] == pytest.approx(0.5)
    assert summary["iqr"] == pytest.approx(0.5)
    assert (summary["min"], summary["max"]) == (0.0, 1.0)
    assert ps.distribution([float("nan")])["n"] == 0
    assert math.isnan(ps.distribution([0.3])["sd"])


@pytest.mark.parametrize(
    ("diffs", "expected"),
    [
        ([-2, -2, -2, -2, 1], "INCONCLUSIVE"),  # 4/5 negative but mean -1.4 pp
        ([-3, -3, -3, -3, 1], "SUPPORTED"),  # 4/5 negative, mean -2.2 pp
        ([-1.68] * 5, "SUPPORTED"),  # boundary: mean exactly -1.68 is supported
        ([-1.67] * 5, "INCONCLUSIVE"),  # right direction, too small
        ([-5, -5, -5, 1, 1], "INCONCLUSIVE"),  # only 3 negative
        ([2, 2, 2, 2, -1], "INCONCLUSIVE"),  # 4 positive, mean 1.4 < 1.68
        ([1.68] * 5, "UNSUPPORTED"),
        ([3, 3, 3, 3, -1], "UNSUPPORTED"),
        ([0, 0, 0, 0, 0], "INCONCLUSIVE"),
    ],
)
def test_decide_verdict_rule(diffs, expected):
    assert ps.decide_verdict(diffs)["verdict"] == expected


def test_decide_verdict_failed_reuse_is_inconclusive():
    result = ps.decide_verdict([-5] * 5, reuse_passed=False)
    assert result["verdict"] == "INCONCLUSIVE"
    assert result["supported_rule_met"]
    assert ps.decide_verdict([-5, -5, -5, -5, float("nan")])["verdict"] == "INCONCLUSIVE"


def test_min_wilcoxon_p_for_five_pairs():
    assert ps.min_two_sided_wilcoxon_p(5) == pytest.approx(0.0625)


def test_t_interval_contains_mean():
    interval = ps.t_interval([-1.0, -2.0, -3.0, -2.0, -2.0])
    assert interval["mean"] == pytest.approx(-2.0)
    assert interval["low"] < interval["mean"] < interval["high"]
    assert interval["df"] == 4


def test_a1_weighted_equals_pooled(toy):
    patients = ps.per_patient_metrics(toy)
    folds = ps.fold_metrics(toy, patients)
    a1 = ps.a1_weighting(patients, folds)
    assert np.allclose(a1.per_id_weighted_by_positive_cells, a1.pooled_cell_weighted, atol=1e-12)


def test_a2_eligibility_counts(toy):
    patients = ps.per_patient_metrics(toy)
    a2 = ps.a2_eligibility(patients, ps.fold_metrics(toy, patients), minimums=(1, 5)).set_index(["fold", "min_positive_cells"])
    assert a2.at[(1, 1), "n_ids_kept"] == 2
    assert a2.at[(1, 5), "n_ids_kept"] == 1  # only A has >= 5 positive cells
    assert a2.at[(1, 5), "macro_sensitivity"] == 1.0
    assert a2.at[(2, 5), "n_ids_excluded"] == 1


def test_a3_leave_one_out(toy):
    patients = ps.per_patient_metrics(toy)
    primary = ps.paired_differences(ps.fold_metrics(toy, patients))
    loo = ps.a3_leave_one_id_out(patients, primary)
    assert set(loo.removed_patient_id) == {"A", "B", "D", "E"}  # C has no positive cells
    without_b = loo.set_index("removed_patient_id").loc["B"]
    assert without_b.difference_pp_without == pytest.approx(0.0)  # only A remains in fold 1
    summary = ps.a3_summary(loo)
    assert summary.n_deletions.tolist() == [2, 2]


def test_bootstrap_weights_and_identity_resample(toy):
    rng = np.random.default_rng(0)
    weights = ps.bootstrap_resample_weights(4, 50, rng)
    assert weights.shape == (50, 4)
    assert (weights.sum(axis=1) == 4).all()
    patients = ps.per_patient_metrics(toy)
    fold1 = patients[patients.fold == 1]
    identity = np.ones((1, len(fold1)), dtype=int)
    observed = 100 * (0.75 - 11 / 12)
    assert ps.bootstrap_differences(fold1, identity, "sensitivity")[0] == pytest.approx(observed)


def test_a4_bootstrap_is_seeded(toy):
    patients = ps.per_patient_metrics(toy)
    first, _ = ps.a4_bootstrap(patients, n_resamples=200, seed=7)
    second, _ = ps.a4_bootstrap(patients, n_resamples=200, seed=7)
    pd.testing.assert_frame_equal(first, second)
    assert set(first.fold) == {"1", "2", "mean"}
    assert (first.ci_low_pp <= first.ci_high_pp).all()


def test_check_reuse_passes_and_fails(toy):
    assignments = toy.drop(columns=["probability_parasitized", "prediction"])
    pooled = ps.pooled_fold_metrics(toy)
    pooled["train_final_bce"] = 0.0
    baseline = pd.DataFrame(
        [{"metric": m, "mean": pooled[m].mean(), "standard_deviation": pooled[m].std(ddof=1)} for m in ps.POOLED_METRICS]
    )
    checks = ps.check_reuse(toy, assignments, pooled, baseline, expected_rows=len(toy), n_folds=2)
    assert checks["patient_ids_in_one_fold"] == 5

    moved = assignments.copy()
    moved.loc[moved.index[0], "fold"] = 2
    with pytest.raises(ps.ReuseAssertionError, match="fold"):
        ps.check_reuse(toy, moved, pooled, baseline, expected_rows=len(toy), n_folds=2)

    shifted = pooled.copy()
    shifted.loc[0, "sensitivity_recall"] += 1e-6
    with pytest.raises(ps.ReuseAssertionError, match="sensitivity_recall"):
        ps.check_reuse(toy, assignments, shifted, baseline, expected_rows=len(toy), n_folds=2)

    with pytest.raises(ps.ReuseAssertionError, match="rows"):
        ps.check_reuse(toy, assignments, pooled, baseline, n_folds=2)

    leaked = toy.copy()
    leaked.loc[leaked.patient_id == "E", "patient_id"] = "A"
    with pytest.raises(ps.ReuseAssertionError):
        ps.check_reuse(leaked, assignments, pooled, baseline, expected_rows=len(toy), n_folds=2)
