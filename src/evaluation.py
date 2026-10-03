from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    confusion_matrix,
    f1_score,
    roc_auc_score,
    roc_curve,
)


def binary_metrics(y_true: np.ndarray, probability: np.ndarray) -> dict[str, float | int]:
    prediction = (probability >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_true, prediction, labels=[0, 1]).ravel()
    return {
        "accuracy": float(accuracy_score(y_true, prediction)),
        "sensitivity_recall": float(tp / (tp + fn)) if tp + fn else float("nan"),
        "specificity": float(tn / (tn + fp)) if tn + fp else float("nan"),
        "auc": float(roc_auc_score(y_true, probability)),
        "f1": float(f1_score(y_true, prediction, zero_division=0)),
        "true_negative": int(tn),
        "false_positive": int(fp),
        "false_negative": int(fn),
        "true_positive": int(tp),
    }


def save_figures(y_true: np.ndarray, probability: np.ndarray, figure_dir: Path) -> None:
    figure_dir.mkdir(parents=True, exist_ok=True)
    prediction = (probability >= 0.5).astype(int)
    matrix = confusion_matrix(y_true, prediction, labels=[0, 1])
    display = ConfusionMatrixDisplay(matrix, display_labels=["Uninfected", "Parasitized"])
    figure, axis = plt.subplots(figsize=(5, 4))
    display.plot(ax=axis, colorbar=False, values_format="d")
    axis.set_title("Out-of-fold confusion matrix (patient-grouped CV)")
    figure.tight_layout()
    figure.savefig(figure_dir / "baseline_confusion_matrix.png", dpi=180)
    plt.close(figure)

    fpr, tpr, _ = roc_curve(y_true, probability)
    auc = roc_auc_score(y_true, probability)
    figure, axis = plt.subplots(figsize=(5, 4))
    axis.plot(fpr, tpr, label=f"OOF ROC (AUC = {auc:.3f})")
    axis.plot([0, 1], [0, 1], linestyle="--", color="grey", label="Chance")
    axis.set_ylabel("True positive rate")
    axis.set_title("Out-of-fold ROC curve")
    axis.set_xlabel("False positive rate", labelpad=12)
    axis.xaxis.set_label_coords(0.5, -0.12)
    axis.legend(loc="lower right")
    figure.tight_layout()
    figure.savefig(figure_dir / "baseline_roc_curve.png", dpi=180)
    plt.close(figure)
