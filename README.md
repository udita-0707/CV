# Computer Vision Research Project

This repository contains the literature review, M2 baseline reproduction, M3 research design, M4 Patient-ID–stratified re-evaluation with ablations, and M5 failure analysis, IEEE paper and defence for patient-level evaluation of malaria parasite classification on the public NIH/NLM segmented-cell dataset. No clinical claims are made.

## Structure

- `data/`: source data and mapping files (official NLM release; not committed)
- `src/`: baseline implementation (M2), Patient-ID–stratified analysis (M4), failure analysis and image review (M5), report rendering
- `tests/`: unit and integration tests (`.venv/bin/python -m pytest`)
- `notebooks/`: M2 reproduction notebook and `m4_patient_stratified.ipynb`
- `results/baseline/`: frozen M2 artifacts (never edited after M2)
- `results/m4/`, `results/m5/`: M4 and M5 outputs (CSV, JSON, figures)
- `paper/`: IEEE conference paper (`main.tex`, `main.pdf`, `references.bib`, `make_tables.py`)
- `papers/`: literature summaries
- `milestones/`: milestone documents and status
- `presentation/`: slides, scripts, and updates (`M4_M5/` holds the defence deck and viva preparation)
- `reports/`: submitted literature-review report
- `docs/`: project and runtime documentation
- `scripts/reproduce_m4_m5.sh`: rebuilds every M4/M5 output from a clean state

## Milestone status

| Milestone | Status | Where |
|---|---|---|
| M1 survey + base paper + checklist | complete | `milestones/M1/`, `presentation/M1/` |
| M2 baseline reproduced | complete | `milestones/M2/`, `results/baseline/` |
| M3 hypothesis + prediction + introduction | complete (recorded 3 Oct 2026, before M4) | `milestones/M3/` |
| M4 implementation + ablations | complete; pre-registered verdict **INCONCLUSIVE** | `milestones/M4/README.md`, `results/m4/` |
| M5 failure analysis + IEEE paper + defence | complete | `milestones/M5/`, `paper/main.pdf`, `presentation/M4_M5/` |

Numbers in the M4/M5 write-ups, paper and slides are generated from `results/` by `src/render_reports.py` and `paper/make_tables.py`; edit the `*.tmpl.md` templates or `paper/main.tex`, not the rendered files.
