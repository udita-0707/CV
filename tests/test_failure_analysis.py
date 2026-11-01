"""Unit tests for M5 failure-analysis and image-review helpers on small synthetic data."""
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src import failure_analysis as fa
from src import image_review as ir
from src import patient_stratified as ps
from tests.test_patient_stratified import _cells


@pytest.fixture
def toy() -> pd.DataFrame:
    rows = (
        _cells(1, "A", tp=8, fn=6, tn=5, fp=0)
        + _cells(1, "B", tp=10, fn=2, tn=4, fp=1)
        + _cells(2, "C", tn=6, fp=3)
        + _cells(2, "D", tp=5, fn=2, tn=6)
    )
    return pd.DataFrame(rows)


def test_error_table_shares_and_ranking(toy):
    table = fa.error_table(ps.per_patient_metrics(toy), "FN")
    assert table.patient_id.tolist() == ["A", "B", "D"]  # C has no Parasitized cells: not at risk
    assert table.share_of_errors.iloc[0] == pytest.approx(0.6)
    assert table.cumulative_share_of_errors.iloc[-1] == pytest.approx(1.0)
    fp = fa.error_table(ps.per_patient_metrics(toy), "FP")
    assert len(fp) == 4 and fp.patient_id.iloc[0] == "C"


def test_concentration_summary():
    table = pd.DataFrame(
        {
            "error_type": "FN",
            "errors": [50, 30, 10, 5, 3, 1, 1, 0, 0, 0, 0],
        }
    )
    table["cumulative_share_of_errors"] = table.errors.cumsum() / table.errors.sum()
    summary = fa.concentration_summary(table)
    assert summary["top1_share"] == pytest.approx(0.5)
    assert summary["ids_for_50pct"] == 1
    assert summary["ids_for_80pct"] == 2
    assert summary["ids_with_any_error"] == 7


def test_errors_by_fold_top_share(toy):
    by_fold = fa.errors_by_fold(ps.per_patient_metrics(toy)).set_index("fold")
    assert by_fold.at[1, "false_negatives"] == 8
    assert by_fold.at[1, "top_fn_patient_id"] == "A"
    assert by_fold.at[1, "top_fn_share_of_fold"] == pytest.approx(6 / 8)


def test_errors_vs_cells_bins_cover_all_ids(toy):
    table = fa.errors_vs_cells(ps.per_patient_metrics(toy))
    assert table.n_ids.sum() == 3
    assert table.false_negatives.sum() == 10


def test_confident_errors_thresholds():
    frame = pd.DataFrame(
        {
            "relative_path": list("abcdef"),
            "patient_id": ["X", "X", "Y", "Y", "Z", "Z"],
            "label": [1, 1, 0, 0, 1, 0],
            "probability_parasitized": [0.05, 0.3, 0.95, 0.6, 0.97, 0.02],
        }
    )
    cells, summary = fa.confident_errors(frame)
    assert sorted(cells.relative_path) == ["a", "c"]
    summary = summary.set_index("error_type")
    assert summary.at["FN", "all_errors"] == 2 and summary.at["FN", "confident_errors"] == 1
    assert summary.at["FP", "share_of_errors"] == pytest.approx(0.5)


def test_calibration_and_brier():
    y = np.array([0, 0, 1, 1], dtype=float)
    p = np.array([0.0, 0.2, 0.8, 1.0])
    assert fa.brier_score(y, p) == pytest.approx((0 + 0.04 + 0.04 + 0) / 4)
    bins = fa.calibration_bins(y, p, n_bins=2)
    assert bins.n_cells.tolist() == [2, 2]  # p = 1.0 lands in the last bin
    assert fa.expected_calibration_error(bins) == pytest.approx(0.1)


def test_sd_driver_finds_outlier():
    patients = pd.DataFrame(
        {
            "fold": [1] * 5,
            "patient_id": list("ABCDE"),
            "sensitivity_defined": [True] * 5,
            "sensitivity": [1.0, 0.98, 0.99, 0.97, 0.2],
            "n_positive": [10, 10, 10, 10, 10],
            "fn": [0, 0, 0, 0, 8],
        }
    )
    drivers = fa.sd_drivers(patients)
    assert drivers.driver_patient_id.iloc[0] == "E"
    assert drivers.sd_reduction_share.iloc[0] > 0.9


def test_select_review_cells_is_deterministic_and_balanced():
    rng = np.random.default_rng(0)
    n = 400
    frame = pd.DataFrame(
        {
            "relative_path": [f"cell_images/x/{i}.png" for i in range(n)],
            "patient_id": [f"P{i % 7}" for i in range(n)],
            "fold": 1,
            "label": np.repeat([0, 1], n // 2),
            "probability_parasitized": rng.uniform(0, 1, n),
        }
    )
    first = ir.select_review_cells(frame, n_per_group=5)
    second = ir.select_review_cells(frame, n_per_group=5)
    pd.testing.assert_frame_equal(first, second)
    assert first.group.value_counts().tolist() == [5, 5, 5, 5]
    fn = first[first.group == "top_false_negative"]
    assert (fn.label == 1).all() and (fn.probability_parasitized < 0.5).all()
    assert first.review_id.tolist()[:2] == ["R01", "R02"]


def test_summarise_review_derives_label_noise_flag():
    key = pd.DataFrame(
        {
            "review_id": ["R1", "R2", "R3", "R4"],
            "group": ["top_false_negative", "top_false_positive", "random_true_positive", "random_true_negative"],
            "relative_path": list("abcd"),
            "patient_id": list("WXYZ"),
            "fold": 1,
            "label": [1, 0, 1, 0],
            "probability_parasitized": [0.01, 0.99, 0.9, 0.1],
        }
    )
    labels = pd.DataFrame(
        {
            "review_id": ["R1", "R2", "R3", "R4"],
            "inclusion_visible": ["no", "yes", "yes", "unclear"],
            "pale_or_atypical_stain": [1, 0, 0, 0],
            "blur_or_low_contrast": [0, 0, 0, 0],
            "segmentation_artefact": [0, 1, 0, 0],
            "note": "",
        }
    )
    _, counts = ir.summarise_review(labels, key)
    counts = counts.set_index("group")
    assert counts.at["top_false_negative", "possible_label_noise"] == 1
    assert counts.at["top_false_positive", "possible_label_noise"] == 1
    assert counts.at["random_true_positive", "possible_label_noise"] == 0
    assert counts.at["random_true_negative", "inclusion_unclear"] == 1
    with pytest.raises(ValueError):
        ir.summarise_review(labels.iloc[:3], key)


def test_short_id_is_display_only():
    assert ir.short_id("C116P77ThinF") == "C116P77"
    assert ir.short_id("C47P8thin_Original_Motic") == "C47P8"
    assert ir.short_id("XYZ") == "XYZ"
