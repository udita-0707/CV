from __future__ import annotations

import json
import importlib.metadata
import platform
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from torch.utils.data import DataLoader

from .config import RunConfig, raw_data_dir, results_dir
from .dataset import audit_dataset, load_manifest
from .evaluation import binary_metrics, save_figures
from .model import CellImageDataset, build_feature_extractor, select_device
from .splits import make_grouped_folds
from .training import fit_classifier, set_seed


def _system_value(command: list[str]) -> str | None:
    try:
        return subprocess.run(command, capture_output=True, text=True, check=True).stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def collect_environment(cfg: RunConfig, device: torch.device, elapsed_seconds: float) -> dict:
    packages = ("numpy", "pandas", "scikit-learn", "Pillow", "matplotlib", "torch", "torchvision")
    return {
        "python": sys.version,
        "platform": platform.platform(),
        "libraries": {name: importlib.metadata.version(name) for name in packages},
        "hardware": {
            "compute_device": str(device),
            "mps_available": bool(torch.backends.mps.is_available()),
            "cuda_available": bool(torch.cuda.is_available()),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "cpu_brand": _system_value(["sysctl", "-n", "machdep.cpu.brand_string"]),
            "memory_bytes": _system_value(["sysctl", "-n", "hw.memsize"]),
        },
        "config": cfg.__dict__,
        "runtime_seconds_this_run": elapsed_seconds,
        "completed_utc": datetime.now(timezone.utc).isoformat(),
    }


def _extract_features(manifest: pd.DataFrame, root: Path, cfg: RunConfig, device: torch.device) -> np.ndarray:
    output = results_dir(root) / "resnet50_imagenet_features.npy"
    if output.exists():
        features = np.load(output)
        if len(features) == len(manifest) and features.shape[1] == 2048:
            return features
        output.unlink()
    dataset = CellImageDataset(manifest, raw_data_dir(root), cfg.image_size)
    loader = DataLoader(dataset, batch_size=cfg.batch_size, shuffle=False, num_workers=0)
    extractor = build_feature_extractor(device)
    feature_batches = []
    observed_indices = []
    with torch.inference_mode():
        for images, _, indices in loader:
            feature_batches.append(extractor(images.to(device)).cpu().numpy().astype(np.float32))
            observed_indices.extend(indices.tolist())
    if observed_indices != list(range(len(manifest))):
        raise AssertionError("Feature extraction changed manifest order")
    features = np.concatenate(feature_batches)
    np.save(output, features)
    return features


def _published_baseline(root: Path) -> None:
    pd.DataFrame(
        [
            {
                "source": "Rajaraman et al. 2018, supplied paper1 summary",
                "paper_location": "Table 6, proposed model, patient level",
                "protocol": "patient-level 5-fold CV",
                "metric": "accuracy",
                "published_value": 0.959,
            },
            {
                "source": "Rajaraman et al. 2018, supplied paper1 summary",
                "paper_location": "Table 6, proposed model, patient level",
                "protocol": "patient-level 5-fold CV",
                "metric": "sensitivity_recall",
                "published_value": 0.947,
            },
            {
                "source": "Rajaraman et al. 2018, supplied paper1 summary",
                "paper_location": "Table 6, proposed model, patient level",
                "protocol": "patient-level 5-fold CV",
                "metric": "specificity",
                "published_value": 0.972,
            },
            {
                "source": "Rajaraman et al. 2018, supplied paper1 summary",
                "paper_location": "Table 6, proposed model, patient level",
                "protocol": "patient-level 5-fold CV",
                "metric": "auc",
                "published_value": 0.991,
            },
            {
                "source": "Rajaraman et al. 2018, supplied paper1 summary",
                "paper_location": "Table 6, proposed model, cell level",
                "protocol": "cell-level comparison",
                "metric": "accuracy",
                "published_value": 0.986,
            },
            {
                "source": "Rajaraman et al. 2018, supplied paper1 summary",
                "paper_location": "Table 6, proposed model, cell level",
                "protocol": "cell-level comparison",
                "metric": "sensitivity_recall",
                "published_value": 0.981,
            },
            {
                "source": "Rajaraman et al. 2018, supplied paper1 summary",
                "paper_location": "Table 6, proposed model, cell level",
                "protocol": "cell-level comparison",
                "metric": "specificity",
                "published_value": 0.992,
            },
            {
                "source": "Rajaraman et al. 2018, supplied paper1 summary",
                "paper_location": "Table 6, proposed model, cell level",
                "protocol": "cell-level comparison",
                "metric": "auc",
                "published_value": 0.999,
            },
        ]
    ).to_csv(results_dir(root) / "published_baseline.csv", index=False)


def run_baseline(root: Path, cfg: RunConfig | None = None) -> dict:
    root = root.resolve()
    cfg = cfg or RunConfig()
    started = time.monotonic()
    set_seed(cfg.seed)
    audit = audit_dataset(root, fetch_missing=True)
    if not audit["passed"]:
        raise RuntimeError("Dataset audit failed. Baseline training is intentionally blocked.")
    manifest = load_manifest(root)
    assignments = make_grouped_folds(manifest, root, cfg.n_splits, cfg.seed)
    device = select_device()
    features = _extract_features(manifest, root, cfg, device)
    labels = manifest.label.to_numpy(dtype=np.int64)
    all_predictions = []
    fold_rows = []
    for fold in range(1, cfg.n_splits + 1):
        test_mask = assignments.fold.to_numpy() == fold
        test_indices = np.flatnonzero(test_mask)
        train_indices = np.flatnonzero(~test_mask)
        probabilities, final_loss, state = fit_classifier(
            features[train_indices],
            labels[train_indices],
            features[test_indices],
            device=device,
            seed=cfg.seed + fold,
            hidden_units=cfg.hidden_units,
            dropout=cfg.dropout,
            learning_rate=cfg.learning_rate,
            momentum=cfg.momentum,
            weight_decay=cfg.weight_decay,
            epochs=cfg.epochs,
            batch_size=cfg.classifier_batch_size,
        )
        torch.save(state, results_dir(root) / f"fold_{fold}_classifier_state.pt")
        metrics = binary_metrics(labels[test_indices], probabilities)
        metrics.update({"fold": fold, "train_final_bce": final_loss, "test_samples": len(test_indices)})
        fold_rows.append(metrics)
        prediction_rows = assignments.loc[test_mask].copy()
        prediction_rows["probability_parasitized"] = probabilities
        prediction_rows["prediction"] = (probabilities >= 0.5).astype(int)
        all_predictions.append(prediction_rows)

    output = results_dir(root)
    fold_results = pd.DataFrame(fold_rows).sort_values("fold")
    fold_results.to_csv(output / "fold_results.csv", index=False)
    predictions = pd.concat(all_predictions).sort_values("relative_path").reset_index(drop=True)
    if len(predictions) != len(manifest) or predictions.relative_path.duplicated().any():
        raise AssertionError("Out-of-fold predictions must contain each image exactly once")
    predictions.to_csv(output / "per_sample_predictions.csv", index=False)
    metrics = ["accuracy", "sensitivity_recall", "specificity", "auc", "f1"]
    baseline_rows = [
        {
            "run_id": "m2_rajaraman_resnet50_feature_extractor",
            "protocol": "patient-grouped stratified 5-fold CV (official mapping IDs)",
            "positive_class": cfg.positive_class,
            "metric": metric,
            "mean": fold_results[metric].mean(),
            "standard_deviation": fold_results[metric].std(ddof=1),
            "n_folds": cfg.n_splits,
            "measured_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        for metric in metrics
    ]
    baseline = pd.DataFrame(baseline_rows)
    baseline.to_csv(output / "baseline_results.csv", index=False)
    _published_baseline(root)
    published = pd.read_csv(output / "published_baseline.csv")
    comparison = published[published.protocol == "patient-level 5-fold CV"].merge(
        baseline[["metric", "mean", "standard_deviation"]], on="metric", how="left"
    )
    comparison.rename(columns={"mean": "measured_mean", "standard_deviation": "measured_fold_sd"}, inplace=True)
    comparison["measured_minus_published"] = comparison.measured_mean - comparison.published_value
    comparison.to_csv(output / "published_vs_measured.csv", index=False)
    save_figures(
        predictions.label.to_numpy(), predictions.probability_parasitized.to_numpy(), output / "figures"
    )
    environment = collect_environment(cfg, device, time.monotonic() - started)
    (output / "run_environment.json").write_text(json.dumps(environment, indent=2) + "\n")
    return {
        "fold_results": fold_results,
        "baseline": baseline,
        "comparison": comparison,
        "environment": environment,
    }


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    result = run_baseline(root)
    print("M2 baseline complete")
    for row in result["baseline"].itertuples(index=False):
        print(f"{row.metric}: {row.mean:.4f} ± {row.standard_deviation:.4f}")
    print(f"runtime_seconds: {result['environment']['runtime_seconds_this_run']:.1f}")


if __name__ == "__main__":
    main()
