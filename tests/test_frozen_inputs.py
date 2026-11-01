"""Integration tests on the real frozen M2 artifacts (CSV only; no images or GPU needed)."""
from __future__ import annotations

import json

import numpy as np
import pytest

from src import patient_stratified as ps
from src.config import project_root
from src.run_m4 import load_frozen_inputs

ROOT = project_root()


@pytest.fixture(scope="module")
def inputs():
    return load_frozen_inputs(ROOT)


@pytest.fixture(scope="module")
def patients(inputs):
    return ps.per_patient_metrics(inputs["predictions"])


def test_reuse_assertions_pass_on_frozen_m2(inputs):
    checks = ps.check_reuse(inputs["predictions"], inputs["assignments"], inputs["fold_results"], inputs["baseline_results"])
    assert checks["row_count"] == 27_558
    assert checks["patient_ids_in_one_fold"] == 201
    assert checks["pooled_metrics_equal_fold_results"]["max_abs_difference"] <= 1e-9


def test_patient_id_census(patients):
    assert patients.patient_id.nunique() == 201
    assert int(patients.sensitivity_defined.sum()) == 151
    assert int((~patients.sensitivity_defined).sum()) == 50
    assert int(patients.n_cells.sum()) == 27_558


def test_a1_identity_on_real_folds(inputs, patients):
    folds = ps.fold_metrics(inputs["predictions"], patients)
    a1 = ps.a1_weighting(patients, folds)
    assert np.allclose(a1.per_id_weighted_by_positive_cells, a1.pooled_cell_weighted, atol=1e-12)


def test_saved_verdict_matches_recomputation(inputs, patients):
    path = ROOT / "results" / "m4" / "primary_verdict.json"
    if not path.exists():
        pytest.skip("run `python -m src.run_m4` first")
    saved = json.loads(path.read_text())
    folds = ps.fold_metrics(inputs["predictions"], patients)
    recomputed = ps.decide_verdict(ps.paired_differences(folds).difference_pp)
    assert saved["verdict"] == recomputed["verdict"]
    assert saved["mean_difference_pp"] == pytest.approx(recomputed["mean_difference_pp"], abs=1e-12)
    assert [row["difference_pp"] for row in saved["folds"]] == pytest.approx(
        ps.paired_differences(folds).difference_pp.tolist(), abs=1e-12
    )
