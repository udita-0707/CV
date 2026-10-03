from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class RunConfig:
    """Fixed choices for the M2 baseline; choices absent from paper1 are logged."""

    seed: int = 42
    n_splits: int = 5
    image_size: int = 224
    batch_size: int = 32
    classifier_batch_size: int = 128
    epochs: int = 20
    learning_rate: float = 0.01
    momentum: float = 0.9
    weight_decay: float = 1e-4
    hidden_units: int = 512
    dropout: float = 0.5
    positive_class: str = "Parasitized"
    pretrained_weights: str = "ResNet50_Weights.IMAGENET1K_V2"


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def reproduction_root(root: Path | None = None) -> Path:
    return root or project_root()


def raw_data_dir(root: Path | None = None) -> Path:
    return reproduction_root(root) / "data" / "raw"


def results_dir(root: Path | None = None) -> Path:
    return reproduction_root(root) / "results"


def logs_dir(root: Path | None = None) -> Path:
    return reproduction_root(root) / "logs"
