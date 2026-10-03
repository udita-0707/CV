from __future__ import annotations

import random
from pathlib import Path

import numpy as np
import torch
from torch import nn
from torch.utils.data import DataLoader, TensorDataset

from .model import FrozenFeatureClassifier


def set_seed(seed: int) -> None:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def fit_classifier(
    train_features: np.ndarray,
    train_labels: np.ndarray,
    test_features: np.ndarray,
    *,
    device: torch.device,
    seed: int,
    hidden_units: int,
    dropout: float,
    learning_rate: float,
    momentum: float,
    weight_decay: float,
    epochs: int,
    batch_size: int,
) -> tuple[np.ndarray, float, dict]:
    """Train a fresh classifier per test fold; test samples are never used for selection."""
    set_seed(seed)
    model = FrozenFeatureClassifier(hidden_units, dropout).to(device)
    optimizer = torch.optim.SGD(
        model.parameters(), lr=learning_rate, momentum=momentum, weight_decay=weight_decay
    )
    criterion = nn.BCEWithLogitsLoss()
    generator = torch.Generator().manual_seed(seed)
    dataset = TensorDataset(
        torch.from_numpy(train_features).float(), torch.from_numpy(train_labels).float()
    )
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True, generator=generator, num_workers=0)
    final_loss = float("nan")
    for _ in range(epochs):
        model.train()
        loss_total = 0.0
        count = 0
        for features, labels in loader:
            features, labels = features.to(device), labels.to(device)
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(features), labels)
            loss.backward()
            optimizer.step()
            loss_total += float(loss.item()) * len(labels)
            count += len(labels)
        final_loss = loss_total / count
    model.eval()
    probabilities = []
    with torch.inference_mode():
        for start in range(0, len(test_features), batch_size):
            batch = torch.from_numpy(test_features[start : start + batch_size]).float().to(device)
            probabilities.append(torch.sigmoid(model(batch)).cpu().numpy())
    run_info = {"final_train_bce": final_loss, "epochs": epochs, "test_threshold": 0.5}
    return np.concatenate(probabilities), final_loss, {key: value.cpu() for key, value in model.state_dict().items()}
