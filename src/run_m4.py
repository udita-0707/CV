"""M4: Patient-ID-stratified re-aggregation of the frozen M2 OOF predictions.

Run from the repository root: ``.venv/bin/python -m src.run_m4``. Reads only
``results/baseline/*.csv`` and writes only ``results/m4/``.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import patient_stratified as ps
from . import plots
from .config import project_root
from .dataset import sha256

FROZEN_INPUTS = ("per_sample_predictions.csv", "fold_assignments.csv", "fold_results.csv", "baseline_results.csv")
PREDICTION_BAND_PP = (-3.0, -1.0)  # milestones/m3/hypothesis.md: "approximately -1 to -3 percentage points"
BOOTSTRAP_RESAMPLES = 2_000
BOOTSTRAP_SEED = 42
ELIGIBILITY_MINIMUMS = (1, 10, 25)


def baseline_dir(root: Path) -> Path:
    return root / "results" / "baseline"


def m4_dir(root: Path) -> Path:
    return root / "results" / "m4"


def input_hashes(root: Path) -> dict[str, str]:
    return {name: sha256(baseline_dir(root) / name) for name in FROZEN_INPUTS}


def load_frozen_inputs(root: Path) -> dict[str, pd.DataFrame]:
    """Read the frozen M2 artifacts with Patient-IDs kept as strings."""
    base = baseline_dir(root)
    return {
        "predictions": pd.read_csv(base / "per_sample_predictions.csv", dtype={"patient_id": str}),
        "assignments": pd.read_csv(base / "fold_assignments.csv", dtype={"patient_id": str}),
        "fold_results": pd.read_csv(base / "fold_results.csv"),
        "baseline_results": pd.read_csv(base / "baseline_results.csv"),
    }


def _write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2, default=lambda value: value.item() if isinstance(value, np.generic) else str(value)) + "\n")


def run_m4(root: Path | None = None) -> dict:
    root = (root or project_root()).resolve()
    out = m4_dir(root)
    (out / "ablations").mkdir(parents=True, exist_ok=True)
    (out / "figures").mkdir(parents=True, exist_ok=True)

    hashes_before = input_hashes(root)
    inputs = load_frozen_inputs(root)
    predictions = inputs["predictions"]
    checks = ps.check_reuse(predictions, inputs["assignments"], inputs["fold_results"], inputs["baseline_results"])

    patients = ps.per_patient_metrics(predictions)
    folds = ps.fold_metrics(predictions, patients)
    patients.to_csv(out / "per_patient_metrics.csv", index=False)
    folds.to_csv(out / "fold_metrics.csv", index=False)

    # ---- primary result and verdict (fixed before any ablation is computed)
    primary = ps.paired_differences(folds, "sensitivity")
    primary.to_csv(out / "fold_paired_differences.csv", index=False)
    denominators = bool((folds.n_ids_sensitivity > 0).all())
    verdict = ps.decide_verdict(primary.difference_pp, reuse_passed=True, denominators_available=denominators)
    m2_sd_pp = 100 * float(inputs["baseline_results"].set_index("metric").at["sensitivity_recall", "standard_deviation"])
    exact_threshold = m2_sd_pp / 2
    verdict_exact = ps.decide_verdict(primary.difference_pp, threshold_pp=exact_threshold, denominators_available=denominators)
    interval = ps.t_interval(primary.difference_pp)

    secondary = pd.DataFrame(
        {
            "fold": folds.fold,
            "id_sensitivity_sd": folds.id_sensitivity_sd,
            "id_sensitivity_iqr": folds.id_sensitivity_iqr,
            "id_sensitivity_range": folds.id_sensitivity_max - folds.id_sensitivity_min,
            "id_fnr_sd": folds.id_false_negative_rate_sd,
            "id_fnr_iqr": folds.id_false_negative_rate_iqr,
            "id_fnr_min": folds.id_false_negative_rate_min,
            "id_fnr_max": folds.id_false_negative_rate_max,
            "id_accuracy_sd": folds.id_accuracy_sd,
            "id_accuracy_iqr": folds.id_accuracy_iqr,
            "n_ids_total": folds.n_ids_total,
            "n_ids_no_positive_cells": folds.n_ids_sensitivity_undefined,
            "n_ids_no_negative_cells": folds.n_ids_specificity_undefined,
        }
    )
    secondary.to_csv(out / "secondary_heterogeneity.csv", index=False)

    # ---- exploratory ablations (milestones/m4/ablation_plan.md); none of them feeds the verdict
    a1 = ps.a1_weighting(patients, folds)
    a1.to_csv(out / "ablations" / "a1_weighting.csv", index=False)
    a2 = ps.a2_eligibility(patients, folds, ELIGIBILITY_MINIMUMS)
    a2.to_csv(out / "ablations" / "a2_eligibility.csv", index=False)
    a2_summary = ps.summarise_by(a2, "min_positive_cells").merge(
        a2.groupby("min_positive_cells").agg(ids_kept=("n_ids_kept", "sum"), ids_excluded=("n_ids_excluded", "sum"),
                                             share_positive_cells_kept=("share_positive_cells_kept", "mean")).reset_index(),
        on="min_positive_cells",
    )
    a2_summary.to_csv(out / "ablations" / "a2_summary.csv", index=False)
    a3 = ps.a3_leave_one_id_out(patients, primary)
    a3.to_csv(out / "ablations" / "a3_leave_one_id_out.csv", index=False)
    a3_summary = ps.a3_summary(a3)
    a3_summary.to_csv(out / "ablations" / "a3_summary.csv", index=False)
    a4, _ = ps.a4_bootstrap(patients, n_resamples=BOOTSTRAP_RESAMPLES, seed=BOOTSTRAP_SEED)
    a4.to_csv(out / "ablations" / "a4_bootstrap.csv", index=False)
    a5 = ps.a5_secondary(folds, a4)
    a5.to_csv(out / "ablations" / "a5_secondary_metrics.csv", index=False)

    all_differences = pd.concat([ps.paired_differences(folds, metric) for metric in ("sensitivity", "specificity", "accuracy")])
    plots.per_id_sensitivity_by_fold(patients, folds, out / "figures" / "per_id_sensitivity_by_fold.png")
    plots.rate_vs_cells(patients, out / "figures" / "fnr_vs_positive_cells.png", "fnr")
    plots.paired_differences_panels(all_differences, a4, ps.DECISION_THRESHOLD_PP, PREDICTION_BAND_PP, out / "figures" / "paired_differences.png")

    boot_mean = a4[(a4.metric == "sensitivity") & (a4.fold == "mean")].iloc[0]
    by_fold = primary.merge(
        a4[(a4.metric == "sensitivity") & (a4.fold != "mean")].assign(fold=lambda f: f.fold.astype(int))[["fold", "ci_low_pp", "ci_high_pp"]],
        on="fold",
    )
    hashes_after = input_hashes(root)
    if hashes_after != hashes_before:
        raise AssertionError("A frozen M2 input changed while M4 was running")
    payload = {
        "intervention": "Patient-ID-stratified re-aggregation of the frozen M2 out-of-fold predictions (evaluation/reporting only)",
        "pre_registration": {
            "source": "milestones/m3/hypothesis.md",
            "recorded": "3 October 2026 (Asia/Kolkata)",
            "primary_metric": "per-fold Patient-ID-macro sensitivity (IDs with >= 1 Parasitized cell) minus pooled cell-level sensitivity",
            "predicted_mean_difference_pp": list(PREDICTION_BAND_PP),
            "supported_if": "at least 4 of 5 paired differences negative and mean <= -1.68 pp",
            "unsupported_if": "at least 4 of 5 paired differences positive and mean >= +1.68 pp",
            "inconclusive_if": "neither directional rule is met, or a reuse assertion fails, or a denominator is unavailable",
        },
        "reuse_assertions": {"passed": True, **checks},
        "folds": by_fold[["fold", "n_ids_eligible", "pooled", "macro", "difference_pp", "ci_low_pp", "ci_high_pp"]].to_dict("records"),
        **verdict,
        "mean_within_predicted_range": bool(PREDICTION_BAND_PP[0] <= verdict["mean_difference_pp"] <= PREDICTION_BAND_PP[1]),
        "threshold_as_written_pp": ps.DECISION_THRESHOLD_PP,
        "threshold_exact_half_m2_sd_pp": exact_threshold,
        "verdict_under_exact_threshold": verdict_exact["verdict"],
        "t_interval_95_pp": interval,
        "bootstrap_95_pp_exploratory_a4": {
            "ci_low_pp": float(boot_mean.ci_low_pp),
            "ci_high_pp": float(boot_mean.ci_high_pp),
            "n_resamples": BOOTSTRAP_RESAMPLES,
            "seed": BOOTSTRAP_SEED,
        },
        "significance_testing": {
            "performed": False,
            "reason": "n = 5 paired folds; no test was pre-registered",
            "min_two_sided_exact_wilcoxon_p": ps.min_two_sided_wilcoxon_p(len(primary)),
        },
        "inputs_sha256": hashes_before,
    }
    _write_json(out / "reuse_checks.json", {"passed": True, **checks, "inputs_sha256": hashes_before})
    _write_json(out / "primary_verdict.json", payload)
    return {"patients": patients, "folds": folds, "primary": primary, "verdict": payload, "a2": a2_summary, "a3": a3_summary, "a4": a4, "a5": a5}


def main() -> None:
    result = run_m4()
    verdict = result["verdict"]
    print("M4 reuse assertions: PASS")
    print(result["primary"][["fold", "n_ids_eligible", "pooled", "macro", "difference_pp"]].to_string(index=False))
    print(f"mean difference: {verdict['mean_difference_pp']:+.3f} pp; negative folds: {verdict['n_negative']}/5")
    print(f"VERDICT (M3 rule as written): {verdict['verdict']} — {'; '.join(verdict['reasons'])}")


if __name__ == "__main__":
    main()
