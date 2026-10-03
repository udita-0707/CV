from __future__ import annotations

import numpy as np
import torch
from PIL import Image
from torch import nn
from torch.utils.data import Dataset
from torchvision.models import ResNet50_Weights, resnet50
from torchvision.transforms import InterpolationMode
from torchvision.transforms import v2 as transforms


class CellImageDataset(Dataset):
    def __init__(self, manifest, data_root, image_size: int):
        self.manifest = manifest.reset_index(drop=True)
        self.data_root = data_root
        self.transform = transforms.Compose(
            [
                transforms.Resize((image_size, image_size), interpolation=InterpolationMode.BILINEAR),
                transforms.ToImage(),
                transforms.ToDtype(torch.float32, scale=True),
                transforms.Normalize(
                    mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)
                ),
            ]
        )

    def __len__(self):
        return len(self.manifest)

    def __getitem__(self, index):
        row = self.manifest.iloc[index]
        with Image.open(self.data_root / row.relative_path) as image:
            tensor = self.transform(image.convert("RGB"))
        return tensor, int(row.label), index


def select_device() -> torch.device:
    if torch.backends.mps.is_available():
        return torch.device("mps")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


def build_feature_extractor(device: torch.device) -> nn.Module:
    weights = ResNet50_Weights.IMAGENET1K_V2
    model = resnet50(weights=weights)
    model.fc = nn.Identity()  # 2,048-dimensional global-average-pooled convolutional feature vector
    model.eval().to(device)
    for parameter in model.parameters():
        parameter.requires_grad = False
    return model


class FrozenFeatureClassifier(nn.Module):
    def __init__(self, hidden_units: int, dropout: float):
        super().__init__()
        self.layers = nn.Sequential(
            nn.Linear(2048, hidden_units),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_units, 1),
        )

    def forward(self, features: torch.Tensor) -> torch.Tensor:
        return self.layers(features).squeeze(1)
