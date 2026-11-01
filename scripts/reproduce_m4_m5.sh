#!/usr/bin/env bash
# Rebuild every M4/M5 output from a clean state.
# Needs the frozen results/baseline/ CSVs; the image-level M5 step also uses the
# official NLM images under data/raw/ (fetched and hash-checked if absent).
# Manual inputs (milestones/M5/image_review_labels.csv) are kept.
set -euo pipefail
cd "$(dirname "$0")/.."
PY=.venv/bin/python
mkdir -p logs

rm -rf -- results/m4 results/m5 paper/generated paper/figures paper/main.pdf presentation/M4_M5/slides.pdf presentation/M4_M5/slides.html presentation/M4_M5/assets/charts

$PY -m src.run_m4 | tee logs/m4_run.log
$PY -m src.run_m5 | tee logs/m5_run.log
(cd notebooks && ../.venv/bin/jupyter nbconvert --to notebook --execute --inplace m4_patient_stratified.ipynb)
$PY -m pytest -q | tee logs/tests.log
$PY -m src.render_reports
$PY paper/make_tables.py
(cd paper && tectonic -X compile main.tex)
$PY presentation/M4_M5/build_slides.py

git diff --exit-code --stat -- results/baseline milestones/M3
echo "Frozen M2 baseline and M3 pre-registration unchanged."
