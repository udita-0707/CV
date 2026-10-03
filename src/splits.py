from __future__ import annotations

from pathlib import Path

import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

from .config import results_dir


def make_grouped_folds(manifest: pd.DataFrame, root: Path, n_splits: int, seed: int) -> pd.DataFrame:
    """Create deterministic patient-grouped, sample-label-stratified five-fold assignments."""
    if manifest.patient_id.eq("").any():
        raise ValueError("Cannot split: one or more samples lack an official Patient-ID")
    splitter = StratifiedGroupKFold(n_splits=n_splits, shuffle=True, random_state=seed)
    assignments = manifest[["relative_path", "filename", "class_name", "label", "patient_id"]].copy()
    assignments["fold"] = 0
    for fold, (_, test_index) in enumerate(
        splitter.split(manifest, manifest["label"], groups=manifest["patient_id"]), start=1
    ):
        assignments.loc[test_index, "fold"] = fold

    if (assignments.fold == 0).any() or len(assignments) != len(manifest):
        raise AssertionError("Every sample must be assigned to exactly one test fold")
    summaries = []
    for fold in range(1, n_splits + 1):
        test = assignments[assignments.fold == fold]
        train = assignments[assignments.fold != fold]
        overlap = set(test.patient_id) & set(train.patient_id)
        if overlap:
            raise AssertionError(f"Patient overlap in fold {fold}: {sorted(overlap)[:5]}")
        if test.label.nunique() != 2:
            raise AssertionError(f"Fold {fold} has only one class")
        summaries.append(
            {
                "fold": fold,
                "train_samples": len(train),
                "test_samples": len(test),
                "train_parasitized": int(train.label.sum()),
                "train_uninfected": int((train.label == 0).sum()),
                "test_parasitized": int(test.label.sum()),
                "test_uninfected": int((test.label == 0).sum()),
                "train_patients": int(train.patient_id.nunique()),
                "test_patients": int(test.patient_id.nunique()),
                "patient_overlap": len(overlap),
            }
        )
    out = results_dir(root)
    assignments.to_csv(out / "fold_assignments.csv", index=False)
    pd.DataFrame(summaries).to_csv(out / "fold_summary.csv", index=False)
    return assignments
