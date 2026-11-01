"""M5 image-level review: verify the official release, select crops, render grids, count review labels."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

from .config import raw_data_dir
from .dataset import DATASET_URL, PARASITIZED_MAPPING_URL, UNINFECTED_MAPPING_URL, _download, sha256
from .patient_stratified import THRESHOLD

REVIEW_GROUPS = ("top_false_negative", "top_false_positive", "random_true_positive", "random_true_negative")
REVIEW_FLAGS = ("pale_or_atypical_stain", "blur_or_low_contrast", "segmentation_artefact")
BACKGROUND = (255, 255, 255)
INK = (11, 11, 11)
INK_SECONDARY = (82, 81, 78)


def verify_official_dataset(root: Path, fetch_missing: bool = True) -> dict:
    """Check the archive, both mappings and every PNG against the frozen M2 hash records.

    ``src.dataset.ensure_official_dataset`` is not called because, after the repository
    restructure, it would write a fresh ``results/dataset_source.json``; its URLs, download
    helper and hash function are reused instead and compared with the frozen record.
    """
    record = json.loads((root / "results" / "baseline" / "dataset_source.json").read_text())
    expected_urls = {"archive": DATASET_URL, "parasitized_mapping": PARASITIZED_MAPPING_URL, "uninfected_mapping": UNINFECTED_MAPPING_URL}
    raw = raw_data_dir(root)
    files = {
        "archive": raw / "cell_images.zip",
        "parasitized_mapping": raw / "patientid_cellmapping_parasitized.csv",
        "uninfected_mapping": raw / "patientid_cellmapping_uninfected.csv",
    }
    report: dict[str, object] = {
        "record": "results/baseline/dataset_source.json",
        "record_archive_path": record["archive_path"],
        "resolved_raw_dir": str(raw.relative_to(root)),
        "config_change_needed": False,
        "files": {},
    }
    for name, path in files.items():
        url = record[f"{name}_url"]
        if url != expected_urls[name]:
            raise ValueError(f"{name} URL in the record is not the official NLM URL: {url}")
        fetched = False
        if not path.exists() and fetch_missing:
            _download(url, path)
            fetched = True
        present = path.exists()
        digest = sha256(path) if present else None
        report["files"][name] = {
            "path": str(path.relative_to(root)),
            "url": url,
            "present": present,
            "fetched_this_run": fetched,
            "sha256": digest,
            "expected_sha256": record[f"{name}_sha256"],
            "matches_record": digest == record[f"{name}_sha256"],
        }

    manifest = pd.read_csv(root / "results" / "baseline" / "dataset_manifest.csv", keep_default_na=False)
    missing, mismatched = [], []
    for relative_path, expected in zip(manifest.relative_path, manifest.sha256):
        path = raw / relative_path
        if not path.exists():
            missing.append(relative_path)
        elif sha256(path) != expected:
            mismatched.append(relative_path)
    report["images"] = {
        "manifest_rows": int(len(manifest)),
        "verified": int(len(manifest) - len(missing) - len(mismatched)),
        "missing": len(missing),
        "sha256_mismatch": len(mismatched),
        "examples": (missing + mismatched)[:5],
    }
    report["passed"] = bool(
        all(entry["matches_record"] for entry in report["files"].values())
        and not missing
        and not mismatched
    )
    report["images_passed"] = bool(not missing and not mismatched)
    return report


def select_review_cells(predictions: pd.DataFrame, n_per_group: int = 24, seed: int = 42) -> pd.DataFrame:
    """Four fixed groups of crops, shuffled together and numbered R01.. for a blind review."""
    p = predictions.probability_parasitized
    fn = predictions[(predictions.label == 1) & (p < THRESHOLD)].sort_values(["probability_parasitized", "relative_path"])
    fp = predictions[(predictions.label == 0) & (p >= THRESHOLD)].sort_values(["probability_parasitized", "relative_path"], ascending=[False, True])
    tp = predictions[(predictions.label == 1) & (p >= THRESHOLD)].sort_values("relative_path")
    tn = predictions[(predictions.label == 0) & (p < THRESHOLD)].sort_values("relative_path")
    groups = [
        fn.head(n_per_group).assign(group="top_false_negative"),
        fp.head(n_per_group).assign(group="top_false_positive"),
        tp.sample(n_per_group, random_state=seed).assign(group="random_true_positive"),
        tn.sample(n_per_group, random_state=seed).assign(group="random_true_negative"),
    ]
    selected = pd.concat(groups, ignore_index=True)
    order = np.random.default_rng(seed).permutation(len(selected))
    selected = selected.iloc[order].reset_index(drop=True)
    width = len(str(len(selected)))
    selected.insert(0, "review_id", [f"R{index + 1:0{width}d}" for index in range(len(selected))])
    return selected[["review_id", "group", "relative_path", "patient_id", "fold", "label", "probability_parasitized"]]


def make_grid(paths: list[Path], captions: list[str], out: Path, columns: int, tile: int = 128,
              row_labels: list[str] | None = None, label_width: int = 0) -> Path:
    """Tile crops (resized, no colour change) with a caption under each tile."""
    font = ImageFont.load_default(size=max(11, tile // 10))
    caption_height = font.size + 8
    rows = int(np.ceil(len(paths) / columns))
    gap = 6
    width = label_width + columns * (tile + gap) + gap
    height = rows * (tile + caption_height + gap) + gap
    canvas = Image.new("RGB", (width, height), BACKGROUND)
    draw = ImageDraw.Draw(canvas)
    for index, (path, caption) in enumerate(zip(paths, captions)):
        row, column = divmod(index, columns)
        x = label_width + gap + column * (tile + gap)
        y = gap + row * (tile + caption_height + gap)
        with Image.open(path) as image:
            canvas.paste(image.convert("RGB").resize((tile, tile), Image.Resampling.LANCZOS), (x, y))
        draw.text((x + tile / 2, y + tile + 3), caption, fill=INK, font=font, anchor="ma")
    for row, label in enumerate(row_labels or []):
        y = gap + row * (tile + caption_height + gap) + tile / 2
        draw.multiline_text((gap, y), label, fill=INK_SECONDARY, font=font, anchor="lm", spacing=4)
    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out)
    return out


def blind_review_grids(selected: pd.DataFrame, raw: Path, out_dir: Path, per_grid: int = 24, columns: int = 6) -> list[Path]:
    paths = []
    for start in range(0, len(selected), per_grid):
        chunk = selected.iloc[start:start + per_grid]
        name = f"blind_review_{chunk.review_id.iloc[0]}_{chunk.review_id.iloc[-1]}.png"
        paths.append(make_grid([raw / p for p in chunk.relative_path], list(chunk.review_id), out_dir / name, columns, tile=160))
    return paths


def short_id(patient_id: str) -> str:
    """Display-only abbreviation: the official key up to its first 'thin' token (e.g. C116P77)."""
    lowered = patient_id.lower()
    cut = lowered.find("thin")
    return patient_id[:cut].rstrip("_") if cut > 0 else patient_id


def error_grid(cells: pd.DataFrame, raw: Path, out: Path, columns: int = 8) -> Path:
    captions = [f"p={row.probability_parasitized:.3f} {short_id(row.patient_id)}" for row in cells.itertuples()]
    return make_grid([raw / p for p in cells.relative_path], captions, out, columns, tile=128)


def worst_id_grid(predictions: pd.DataFrame, patients: pd.DataFrame, raw: Path, out: Path,
                  n_ids: int = 3, min_positive: int = 10, n_fn: int = 6, n_tp: int = 2) -> tuple[Path, pd.DataFrame]:
    """One row per worst-sensitivity Patient-ID (>= min_positive Parasitized cells): its most confident FNs, then TPs."""
    worst = patients[patients.n_positive >= min_positive].nsmallest(n_ids, ["sensitivity"]).reset_index(drop=True)
    paths, captions, labels = [], [], []
    for row in worst.itertuples():
        cells = predictions[(predictions.patient_id == row.patient_id) & (predictions.label == 1)]
        fns = cells[cells.probability_parasitized < THRESHOLD].sort_values(["probability_parasitized", "relative_path"]).head(n_fn)
        tps = cells[cells.probability_parasitized >= THRESHOLD].sort_values(["probability_parasitized", "relative_path"], ascending=[False, True]).head(n_tp)
        for kind, chosen in (("FN", fns), ("TP", tps)):
            paths.extend(raw / p for p in chosen.relative_path)
            captions.extend(f"{kind} p={p:.3f}" for p in chosen.probability_parasitized)
        labels.append(f"{short_id(row.patient_id)}\nfold {row.fold}\nsens {row.sensitivity:.2f}\n{row.n_positive} cells")
    path = make_grid(paths, captions, out, columns=n_fn + n_tp, tile=128, row_labels=labels, label_width=120)
    return path, worst


def summarise_review(labels: pd.DataFrame, key: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Join blind labels to the key and count each category per group."""
    expected = set(key.review_id)
    if set(labels.review_id) != expected:
        raise ValueError(f"review labels must cover exactly {len(expected)} review IDs")
    if not labels.inclusion_visible.isin(["yes", "no", "unclear"]).all():
        raise ValueError("inclusion_visible must be yes, no or unclear")
    joined = key.merge(labels, on="review_id", validate="one_to_one")
    joined["possible_label_noise"] = ((joined.label == 1) & (joined.inclusion_visible == "no")) | (
        (joined.label == 0) & (joined.inclusion_visible == "yes")
    )
    rows = []
    for group in REVIEW_GROUPS:
        subset = joined[joined.group == group]
        row = {"group": group, "n_cells": int(len(subset)), "n_patient_ids": int(subset.patient_id.nunique())}
        for value in ("yes", "no", "unclear"):
            row[f"inclusion_{value}"] = int((subset.inclusion_visible == value).sum())
        for flag in REVIEW_FLAGS + ("possible_label_noise",):
            row[flag] = int(subset[flag].astype(int).sum())
        rows.append(row)
    return joined, pd.DataFrame(rows)
