"""M5 failure analysis: prediction-level (CSVs only) and image-level (official release only).

Run from the repository root: ``.venv/bin/python -m src.run_m5``. Reads
``results/baseline/`` and the official images under ``data/raw/``; writes only
``results/m5/``. Blind review labels are read from
``milestones/M5/image_review_labels.csv`` when that file exists.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from . import failure_analysis as fa
from . import image_review as ir
from . import patient_stratified as ps
from . import plots
from .config import project_root, raw_data_dir
from .run_m4 import load_frozen_inputs

TOP_N = 10
REVIEW_LABELS = Path("milestones") / "M5" / "image_review_labels.csv"


def m5_dir(root: Path) -> Path:
    return root / "results" / "m5"


def prediction_level(root: Path, predictions: pd.DataFrame, patients: pd.DataFrame) -> dict:
    out = m5_dir(root)
    tables = {kind: fa.error_table(patients, kind) for kind in fa.ERROR_KINDS}
    pd.concat(tables.values()).to_csv(out / "error_concentration.csv", index=False)
    for kind, table in tables.items():
        table.head(TOP_N).to_csv(out / f"top10_{kind.lower()}_patient_ids.csv", index=False)
    concentration = pd.DataFrame([fa.concentration_summary(table) for table in tables.values()])
    concentration.to_csv(out / "concentration_summary.csv", index=False)

    by_fold = fa.errors_by_fold(patients)
    by_fold.to_csv(out / "errors_by_fold.csv", index=False)
    vs_cells = fa.errors_vs_cells(patients)
    vs_cells.to_csv(out / "errors_vs_cells.csv", index=False)
    correlations = fa.rank_correlations(patients)
    correlations.to_csv(out / "errors_vs_cells_spearman.csv", index=False)

    confident, confident_summary = fa.confident_errors(predictions)
    confident.to_csv(out / "confident_errors.csv", index=False)
    confident_summary.to_csv(out / "confident_errors_summary.csv", index=False)

    y = predictions.label.to_numpy(dtype=float)
    p = predictions.probability_parasitized.to_numpy(dtype=float)
    bins = fa.calibration_bins(y, p)
    bins.to_csv(out / "calibration_bins.csv", index=False)
    calibration = fa.calibration_summary(predictions)
    calibration.to_csv(out / "calibration_summary.csv", index=False)

    drivers = fa.sd_drivers(patients)
    drivers.to_csv(out / "sensitivity_sd_drivers.csv", index=False)

    overall = calibration[calibration.fold == "all"].iloc[0]
    plots.reliability_diagram(bins, overall.brier, overall.ece, out / "figures" / "reliability_diagram.png")
    plots.error_concentration(pd.concat(tables.values()), out / "figures" / "error_concentration.png")
    plots.rates_vs_cells_panels(patients, out / "figures" / "error_rates_vs_cells.png")
    return {"concentration": concentration, "by_fold": by_fold, "confident": confident_summary, "calibration": calibration, "drivers": drivers}


def image_level(root: Path, predictions: pd.DataFrame, patients: pd.DataFrame) -> dict:
    out = m5_dir(root)
    verification = ir.verify_official_dataset(root, fetch_missing=True)
    (out / "dataset_verification.json").write_text(json.dumps(verification, indent=2) + "\n")
    if not verification["images_passed"]:
        return {"verification": verification, "skipped": "local images do not match the frozen manifest"}
    raw = raw_data_dir(root)
    figures = out / "figures"
    selected = ir.select_review_cells(predictions)
    selected.to_csv(out / "image_review_key.csv", index=False)
    ir.blind_review_grids(selected, raw, out / "blind_review")

    p = predictions.probability_parasitized
    fn = predictions[(predictions.label == 1) & (p < ps.THRESHOLD)].sort_values(["probability_parasitized", "relative_path"]).head(16)
    fp = predictions[(predictions.label == 0) & (p >= ps.THRESHOLD)].sort_values(["probability_parasitized", "relative_path"], ascending=[False, True]).head(16)
    ir.error_grid(fn, raw, figures / "grid_top_false_negatives.png")
    ir.error_grid(fp, raw, figures / "grid_top_false_positives.png")
    _, worst = ir.worst_id_grid(predictions, patients, raw, figures / "grid_worst_patient_ids.png")
    worst.to_csv(out / "worst_patient_ids.csv", index=False)

    result = {"verification": verification}
    labels_path = root / REVIEW_LABELS
    if labels_path.exists():
        labels = pd.read_csv(labels_path, keep_default_na=False)
        joined, counts = ir.summarise_review(labels, selected)
        joined.to_csv(out / "image_review_joined.csv", index=False)
        counts.to_csv(out / "image_review_counts.csv", index=False)
        result["counts"] = counts
    return result


def run_m5(root: Path | None = None) -> dict:
    root = (root or project_root()).resolve()
    (m5_dir(root) / "figures").mkdir(parents=True, exist_ok=True)
    inputs = load_frozen_inputs(root)
    predictions = inputs["predictions"]
    ps.check_reuse(predictions, inputs["assignments"], inputs["fold_results"], inputs["baseline_results"])
    patients = ps.per_patient_metrics(predictions)
    return {"prediction": prediction_level(root, predictions, patients), "image": image_level(root, predictions, patients)}


def main() -> None:
    result = run_m5()
    prediction = result["prediction"]
    print(prediction["concentration"].to_string(index=False))
    print(prediction["confident"].to_string(index=False))
    print(prediction["calibration"].round(4).to_string(index=False))
    print(prediction["drivers"].round(4).to_string(index=False))
    image = result["image"]
    verification = image["verification"]
    print("dataset verification passed:", verification["passed"], {k: v["matches_record"] for k, v in verification["files"].items()}, verification["images"])
    if "counts" in image:
        print(image["counts"].to_string(index=False))
    else:
        print("image review labels not found yet:", REVIEW_LABELS)


if __name__ == "__main__":
    main()
