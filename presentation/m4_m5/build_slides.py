"""Build the M4/M5 defence deck in the M2/M3 deck style: slides.html and slides.pdf.

Values and tables come from ``src.report_values`` (files under ``results/``), charts
from ``src.slide_figures``, and cell crops from the official images (copied into
``assets/cells/`` so the deck rebuilds without the dataset). The HTML is rendered
from ``slides.tmpl.html`` and printed to PDF with headless Chrome.
Run from the repository root: ``.venv/bin/python presentation/m4_m5/build_slides.py``.
"""
from __future__ import annotations

import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))

from src import slide_figures as sf  # noqa: E402
from src.patient_stratified import THRESHOLD  # noqa: E402
from src.report_values import Table, collect, fmt  # noqa: E402

ASSETS = HERE / "assets"
PLACEHOLDER = re.compile(r"\{\{\s*(table:|html:)?([A-Za-z0-9_]+)\s*\}\}")
CHROME_CANDIDATES = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
)


def table_html(table: Table) -> str:
    def cell(value: object, kind: str) -> str:
        if isinstance(value, float) and value != value:
            return ""
        if kind == "cell":
            value, kind = value
        return html.escape(fmt(value, kind, "md"))

    head = "".join(f"<th>{html.escape(name)}</th>" for name, _ in table.columns)
    rows = "".join("<tr>" + "".join(f"<td>{cell(v, k)}</td>" for v, (_, k) in zip(row, table.columns)) + "</tr>" for row in table.rows)
    return f"<table><thead><tr>{head}</tr></thead><tbody>{rows}</tbody></table>"


def render(template: str, values: dict, tables: dict, snippets: dict[str, str]) -> str:
    missing: list[str] = []

    def replace(match: re.Match) -> str:
        prefix, key = match.group(1), match.group(2)
        if prefix == "html:" and key in snippets:
            return snippets[key]
        if prefix == "table:" and key in tables:
            return table_html(tables[key])
        if prefix is None and key in values:
            return html.escape(fmt(*values[key], target="md"))
        missing.append(match.group(0))
        return match.group(0)

    rendered = PLACEHOLDER.sub(replace, template)
    if missing:
        raise KeyError(f"unresolved placeholders: {sorted(set(missing))}")
    return rendered


def copy_crop(relative_path: str, name: str) -> str:
    """Copy one official crop into assets/cells/ (kept if the dataset is absent) and return its src."""
    target = ASSETS / "cells" / name
    source = ROOT / "data" / "raw" / relative_path
    target.parent.mkdir(parents=True, exist_ok=True)
    if source.exists():
        shutil.copyfile(source, target)
    elif not target.exists():
        raise FileNotFoundError(f"{source} is missing and no copy exists in {target.parent}")
    return f"assets/cells/{name}"


def title_cells() -> str:
    """Three random correct Parasitized and three Uninfected crops from the blind-review key."""
    key = pd.read_csv(ROOT / "results" / "m5" / "image_review_key.csv").sort_values("review_id")
    blocks = []
    for group, label, color in (("random_true_positive", "Parasitized", "var(--coral)"), ("random_true_negative", "Uninfected", "var(--teal)")):
        rows = key[key.group == group].head(3)
        tiles = "".join(
            f'<img class="crop" src="{copy_crop(r.relative_path, f"title_{group}_{i}.png")}" alt="{label} cell">'
            for i, r in enumerate(rows.itertuples(), start=1)
        )
        blocks.append(
            f'<div class="k" style="color:{color}; margin-bottom:.06in;">{label}</div>'
            f'<div style="display:flex; gap:.08in; margin-bottom:.2in;">{tiles}</div>'
        )
    return "".join(blocks)


def error_tiles(predictions: pd.DataFrame, kind: str, n: int = 6) -> str:
    """The n most confident errors of one kind, same ordering as src/run_m5.py's grids."""
    p = predictions.probability_parasitized
    if kind == "fn":
        rows = predictions[(predictions.label == 1) & (p < THRESHOLD)].sort_values(["probability_parasitized", "relative_path"])
    else:
        rows = predictions[(predictions.label == 0) & (p >= THRESHOLD)].sort_values(["probability_parasitized", "relative_path"], ascending=[False, True])
    tiles = []
    for i, r in enumerate(rows.head(n).itertuples(), start=1):
        src = copy_crop(r.relative_path, f"{kind}_{i}.png")
        tiles.append(
            f'<div style="width:.8in;"><img class="crop" src="{src}" alt="{kind.upper()} cell">'
            f'<div class="small" style="text-align:center; margin-top:.02in; font-size:9pt;">p = {r.probability_parasitized:.3f}</div></div>'
        )
    return f'<div style="display:flex; gap:.1in;">{"".join(tiles)}</div>'


def make_charts() -> None:
    sf.use_deck_style(ASSETS / "fonts")
    charts = ASSETS / "charts"
    m4 = ROOT / "results" / "m4"
    patients = pd.read_csv(m4 / "per_patient_metrics.csv", dtype={"patient_id": str})
    folds = pd.read_csv(m4 / "fold_metrics.csv")
    verdict = json.loads((m4 / "primary_verdict.json").read_text())
    sf.per_id_strip(patients, folds, charts / "per_id_strip.png")
    sf.paired_differences(
        pd.read_csv(m4 / "fold_paired_differences.csv"),
        pd.read_csv(m4 / "ablations" / "a4_bootstrap.csv"),
        verdict["threshold_as_written_pp"],
        tuple(verdict["pre_registration"]["predicted_mean_difference_pp"]),
        charts / "paired_differences.png",
    )
    sf.concentration(pd.read_csv(ROOT / "results" / "m5" / "error_concentration.csv"), charts / "concentration.png")
    sf.inclusion_bars(pd.read_csv(ROOT / "results" / "m5" / "image_review_counts.csv"), charts / "inclusion_bars.png")


def find_chrome() -> str:
    for candidate in CHROME_CANDIDATES:
        if Path(candidate).exists() or shutil.which(candidate):
            return candidate
    raise FileNotFoundError("Google Chrome or Chromium is needed to print the deck to PDF")


def print_pdf(source: Path, target: Path) -> None:
    with tempfile.TemporaryDirectory() as profile:
        subprocess.run(
            [
                find_chrome(), "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                f"--user-data-dir={profile}", "--no-pdf-header-footer", "--virtual-time-budget=15000",
                f"--print-to-pdf={target}", source.as_uri(),
            ],
            check=True, capture_output=True, timeout=240,
        )


def main() -> None:
    values, tables = collect(ROOT)
    make_charts()
    predictions = pd.read_csv(ROOT / "results" / "baseline" / "per_sample_predictions.csv", dtype={"patient_id": str})
    snippets = {"title_cells": title_cells(), "fn_tiles": error_tiles(predictions, "fn"), "fp_tiles": error_tiles(predictions, "fp")}
    page = render((HERE / "slides.tmpl.html").read_text(), values, tables, snippets)
    (HERE / "slides.html").write_text(page)
    print_pdf(HERE / "slides.html", HERE / "slides.pdf")
    print(f"wrote {HERE / 'slides.html'} and {HERE / 'slides.pdf'}")


if __name__ == "__main__":
    main()
