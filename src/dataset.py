from __future__ import annotations

import ast
import csv
import hashlib
import json
import re
import shutil
import urllib.request
import zipfile
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from PIL import Image

from .config import raw_data_dir, results_dir

DATASET_URL = "https://data.lhncbc.nlm.nih.gov/public/Malaria/cell_images.zip"
PARASITIZED_MAPPING_URL = (
    "https://data.lhncbc.nlm.nih.gov/public/Malaria/"
    "patientid_cellmapping_parasitized.csv"
)
UNINFECTED_MAPPING_URL = (
    "https://data.lhncbc.nlm.nih.gov/public/Malaria/"
    "patientid_cellmapping_uninfected.csv"
)
EXPECTED_PER_CLASS = 13_779
EXPECTED_TOTAL = 27_558
CLASS_TO_LABEL = {"Uninfected": 0, "Parasitized": 1}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as response, temporary.open("wb") as out:
        shutil.copyfileobj(response, out)
    temporary.replace(destination)


def ensure_official_dataset(root: Path, fetch_missing: bool = True) -> dict:
    """Fetch only NLM's stated cell archive and mapping files, or verify local copies."""
    raw = raw_data_dir(root)
    raw.mkdir(parents=True, exist_ok=True)
    required = {
        "archive": (raw / "cell_images.zip", DATASET_URL),
        "parasitized_mapping": (
            raw / "patientid_cellmapping_parasitized.csv", PARASITIZED_MAPPING_URL
        ),
        "uninfected_mapping": (
            raw / "patientid_cellmapping_uninfected.csv", UNINFECTED_MAPPING_URL
        ),
    }
    absent = [name for name, (path, _) in required.items() if not path.exists()]
    if absent and not fetch_missing:
        raise FileNotFoundError(
            "Missing official NLM file(s): " + ", ".join(absent) + ". Run with fetch_missing=True."
        )
    for _, (path, url) in required.items():
        if not path.exists():
            _download(url, path)

    image_root = raw / "cell_images"
    if not image_root.exists():
        with zipfile.ZipFile(required["archive"][0]) as archive:
            archive.extractall(raw)

    source = {
        "dataset_name": "NLM-Falciparum-Thin-Cell-Images",
        "official_datasheet": "https://lhncbc.nlm.nih.gov/LHC-research/LHC-projects/image-processing/malaria-datasheet.html",
        "archive_url": DATASET_URL,
        "archive_sha256": sha256(required["archive"][0]),
        "parasitized_mapping_url": PARASITIZED_MAPPING_URL,
        "parasitized_mapping_sha256": sha256(required["parasitized_mapping"][0]),
        "uninfected_mapping_url": UNINFECTED_MAPPING_URL,
        "uninfected_mapping_sha256": sha256(required["uninfected_mapping"][0]),
        "verified_utc": datetime.now(timezone.utc).isoformat(),
        "archive_path": str(required["archive"][0].relative_to(root)),
    }
    (results_dir(root) / "dataset_source.json").write_text(json.dumps(source, indent=2) + "\n")
    return source


def _read_official_mapping(path: Path) -> dict[str, list[str]]:
    """Read NLM's one-patient-per-line list syntax (it is not RFC-style quoted CSV)."""
    mapping: dict[str, list[str]] = {}
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        patient_id, delimiter, payload = raw_line.partition(",")
        match = re.search(r"\[.*\]", payload)
        if not delimiter or not patient_id or match is None:
            raise ValueError(f"Cannot parse NLM mapping line {line_number} in {path.name}")
        filenames = ast.literal_eval(match.group(0))
        if not isinstance(filenames, list) or not all(isinstance(item, str) for item in filenames):
            raise ValueError(f"Unexpected filename list on line {line_number} in {path.name}")
        if patient_id in mapping:
            raise ValueError(f"Duplicate patient mapping key {patient_id!r} in {path.name}")
        mapping[patient_id] = filenames
    return mapping


def _mapping_inverse(mapping: dict[str, list[str]], class_name: str) -> tuple[dict[str, str], list[dict]]:
    inverse: dict[str, str] = {}
    duplicated: list[dict] = []
    for patient_id, filenames in mapping.items():
        for filename in filenames:
            if filename in inverse:
                duplicated.append(
                    {
                        "class_name": class_name,
                        "filename": filename,
                        "patient_id_first": inverse[filename],
                        "patient_id_second": patient_id,
                    }
                )
            else:
                inverse[filename] = patient_id
    return inverse, duplicated


def audit_dataset(root: Path, fetch_missing: bool = True) -> dict:
    """Build a sample manifest and prove the exact official release is usable for M2."""
    source = ensure_official_dataset(root, fetch_missing=fetch_missing)
    raw = raw_data_dir(root)
    result = results_dir(root)
    result.mkdir(parents=True, exist_ok=True)
    image_root = raw / "cell_images"

    official_maps = {
        "Parasitized": _read_official_mapping(raw / "patientid_cellmapping_parasitized.csv"),
        "Uninfected": _read_official_mapping(raw / "patientid_cellmapping_uninfected.csv"),
    }
    inverse_maps: dict[str, dict[str, str]] = {}
    mapping_duplicates: list[dict] = []
    for class_name, mapping in official_maps.items():
        inverse_maps[class_name], duplicates = _mapping_inverse(mapping, class_name)
        mapping_duplicates.extend(duplicates)

    rows: list[dict] = []
    found_filenames: dict[str, set[str]] = {name: set() for name in CLASS_TO_LABEL}
    corrupt: list[dict] = []
    dimensions = Counter()
    content_hashes: dict[str, list[dict]] = defaultdict(list)
    for class_name, label in CLASS_TO_LABEL.items():
        class_dir = image_root / class_name
        if not class_dir.is_dir():
            raise FileNotFoundError(f"Expected class directory missing: {class_dir}")
        for path in sorted(class_dir.glob("*.png")):
            found_filenames[class_name].add(path.name)
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    dimensions[f"{image.width}x{image.height}"] += 1
            except Exception as error:  # audit must report every invalid image rather than conceal it
                corrupt.append({"relative_path": str(path.relative_to(raw)), "error": repr(error)})
                continue
            file_hash = sha256(path)
            patient_id = inverse_maps[class_name].get(path.name)
            rows.append(
                {
                    "relative_path": str(path.relative_to(raw)),
                    "filename": path.name,
                    "class_name": class_name,
                    "label": label,
                    "patient_id": patient_id or "",
                    "sha256": file_hash,
                }
            )
            content_hashes[file_hash].append(rows[-1])

    mapping_missing: list[dict] = []
    unmapped: list[dict] = []
    for class_name in CLASS_TO_LABEL:
        expected = set(inverse_maps[class_name])
        actual = found_filenames[class_name]
        mapping_missing.extend(
            {"issue": "mapping_references_absent_image", "class_name": class_name, "filename": name}
            for name in sorted(expected - actual)
        )
        unmapped.extend(
            {"issue": "image_absent_from_official_mapping", "class_name": class_name, "filename": name}
            for name in sorted(actual - expected)
        )
    duplicate_files = [entries for entries in content_hashes.values() if len(entries) > 1]
    duplicate_summary = []
    cross_label_duplicates = []
    for entries in duplicate_files:
        labels = {entry["label"] for entry in entries}
        summary = {
            "sha256": entries[0]["sha256"],
            "copies": len(entries),
            "classes": ";".join(sorted({entry["class_name"] for entry in entries})),
            "paths": ";".join(entry["relative_path"] for entry in entries),
        }
        duplicate_summary.append(summary)
        if len(labels) > 1:
            cross_label_duplicates.append(summary)

    manifest = pd.DataFrame(rows).sort_values(["class_name", "filename"]).reset_index(drop=True)
    manifest.to_csv(result / "dataset_manifest.csv", index=False)
    pd.DataFrame(
        [
            {"class_name": class_name, "label": label, "image_count": int((manifest.label == label).sum())}
            for class_name, label in CLASS_TO_LABEL.items()
        ]
    ).to_csv(result / "dataset_class_counts.csv", index=False)
    patient_summary = (
        manifest.groupby(["patient_id", "class_name"], dropna=False)
        .size()
        .rename("cell_count")
        .reset_index()
        .sort_values(["patient_id", "class_name"])
    )
    patient_summary.to_csv(result / "patient_cell_mapping_summary.csv", index=False)
    mapping_issue_rows = mapping_missing + unmapped + [
        {"issue": "duplicate_mapping_assignment", **row} for row in mapping_duplicates
    ]
    pd.DataFrame(
        mapping_issue_rows,
        columns=["issue", "class_name", "filename", "patient_id_first", "patient_id_second"],
    ).to_csv(result / "dataset_mapping_issues.csv", index=False)
    pd.DataFrame(
        duplicate_summary, columns=["sha256", "copies", "classes", "paths"]
    ).to_csv(result / "duplicate_images.csv", index=False)
    pd.DataFrame(corrupt, columns=["relative_path", "error"]).to_csv(
        result / "corrupt_images.csv", index=False
    )

    class_counts = {name: int((manifest.class_name == name).sum()) for name in CLASS_TO_LABEL}
    unknown_patient_ids = int((manifest.patient_id == "").sum())
    expected_counts_ok = class_counts == {"Uninfected": EXPECTED_PER_CLASS, "Parasitized": EXPECTED_PER_CLASS}
    passed = bool(
        expected_counts_ok
        and len(manifest) == EXPECTED_TOTAL
        and not corrupt
        and not mapping_missing
        and not unmapped
        and not mapping_duplicates
        and unknown_patient_ids == 0
        and not cross_label_duplicates
    )
    audit = {
        "passed": passed,
        "expected_total": EXPECTED_TOTAL,
        "observed_total": len(manifest),
        "expected_per_class": EXPECTED_PER_CLASS,
        "class_counts": class_counts,
        "official_mapping_entries": {key: len(value) for key, value in official_maps.items()},
        "unique_official_patient_ids_across_classes": int(manifest.patient_id.nunique()),
        "cells_with_no_official_patient_id": unknown_patient_ids,
        "corrupt_images": len(corrupt),
        "mapping_references_absent_images": len(mapping_missing),
        "images_absent_from_mapping": len(unmapped),
        "duplicate_mapping_assignments": len(mapping_duplicates),
        "byte_identical_duplicate_sets": len(duplicate_summary),
        "cross_label_duplicate_sets": len(cross_label_duplicates),
        "image_dimensions": dict(sorted(dimensions.items())),
        "source": source,
    }
    (result / "dataset_audit.json").write_text(json.dumps(audit, indent=2) + "\n")
    report = f"""# Official NIH/NLM dataset audit

**Status:** {'PASS' if passed else 'FAIL'}

The audited release is NLM-Falciparum-Thin-Cell-Images from the official NLM
Malaria Screener datasheet. The archive SHA-256 is
`{source['archive_sha256']}`. Retrieval URLs and all three SHA-256 values are
in `dataset_source.json`.

| Check | Result |
|---|---:|
| PNG images | {len(manifest)} (expected {EXPECTED_TOTAL}) |
| Parasitized | {class_counts['Parasitized']} (expected {EXPECTED_PER_CLASS}) |
| Uninfected | {class_counts['Uninfected']} (expected {EXPECTED_PER_CLASS}) |
| Official mapping entries: Parasitized / Uninfected | {len(official_maps['Parasitized'])} / {len(official_maps['Uninfected'])} |
| Unique official mapping IDs across all cells | {manifest.patient_id.nunique()} |
| Cells missing an official mapping ID | {unknown_patient_ids} |
| Corrupt PNGs | {len(corrupt)} |
| Mapping references to absent images | {len(mapping_missing)} |
| Images absent from mappings | {len(unmapped)} |
| Duplicate mapping assignments | {len(mapping_duplicates)} |
| Byte-identical duplicate sets | {len(duplicate_summary)} |
| Cross-label duplicate sets | {len(cross_label_duplicates)} |

Directory structure is `cell_images/Parasitized/*.png` and
`cell_images/Uninfected/*.png`. Observed decoded image dimensions are recorded
in `dataset_audit.json`.

## Patient/cell mapping decision

The grouping field is the **exact Patient-ID key in the official NLM mapping
CSV**, not a randomly created or filename-inferred ID. The official datasheet
states that these CSV files map Patient IDs to cells; it also notes 151
Parasitized mapping entries (one source patient has images from two microscope
models) and 201 Uninfected entries because normal cells from infected slides
also appear in that class. The supplied paper1/M1 narrative describes 150
infected plus 50 healthy patients. These are not treated as a claim that the
archive has 200 unique mapping keys or that its IDs reproduce the paper's
unpublished five fold assignments. `patient_cell_mapping_summary.csv` is the
auditable mapping used for the grouped split.

## Files

- `dataset_manifest.csv`: one row per verified PNG, label, official Patient-ID,
  and content hash.
- `patient_cell_mapping_summary.csv`: cells per official Patient-ID and class.
- `dataset_mapping_issues.csv`, `corrupt_images.csv`, `duplicate_images.csv`:
  audit exceptions (empty files mean no exceptions of that type).
"""
    (result / "dataset_audit.md").write_text(report)
    return audit


def load_manifest(root: Path) -> pd.DataFrame:
    manifest_path = results_dir(root) / "dataset_manifest.csv"
    if not manifest_path.exists():
        audit = audit_dataset(root, fetch_missing=True)
        if not audit["passed"]:
            raise RuntimeError("Dataset audit failed; see results/baseline/dataset_audit.md")
    return pd.read_csv(manifest_path, keep_default_na=False)
