# Computer Vision Research Project

Literature review, baseline reproduction (M2), pre-registered hypothesis (M3), Patient-ID–stratified re-evaluation with ablations (M4), and failure analysis, IEEE paper and defence (M5) for malaria parasite classification on the public NIH/NLM segmented-cell dataset. No clinical claims are made.

## Structure

- `src/`: baseline implementation (M2), Patient-ID–stratified analysis (M4), failure analysis and image review (M5), report and figure generation
- `tests/`: unit and integration tests (`.venv/bin/python -m pytest`)
- `scripts/reproduce_m4_m5.sh`: rebuilds every M4/M5 output, the paper and the deck from a clean state
- `notebooks/`: M2 reproduction notebook and the M4 notebook
- `results/baseline/`: frozen M2 artifacts (never edited after M2)
- `results/m4/`, `results/m5/`: M4 and M5 outputs (CSV, JSON, figures)
- `paper/`: IEEE conference paper (`main.tex`, `main.pdf`, `references.bib`; `make_tables.py` writes `generated/`, figures are read from `results/`)
- `presentation/m1/`: M1 slides (`slides.pdf`) and outline
- `presentation/m4_m5/`: M4/M5 defence deck (`slides.pdf`, built by `build_slides.py` from `slides.tmpl.html`) and outline
- `milestones/m1` … `milestones/m5`: milestone write-ups and status
- `literature/`, `papers/`: survey synthesis and per-paper reading notes
- `docs/`: project specification and runtime notes
- `data/`: the official NLM release, fetched and hash-checked by `src/dataset.py` (not committed)

## Milestone status

| Milestone | Status | Where |
|---|---|---|
| M1 survey + base paper + checklist | complete | `milestones/m1/`, `presentation/m1/` |
| M2 baseline reproduced | complete | `milestones/m2/`, `results/baseline/` |
| M3 hypothesis + prediction + introduction | complete (recorded 3 Oct 2026, before M4) | `milestones/m3/` |
| M4 implementation + ablations | complete; pre-registered verdict **INCONCLUSIVE** | `milestones/m4/README.md`, `results/m4/` |
| M5 failure analysis + IEEE paper + defence | complete | `milestones/m5/`, `paper/main.pdf`, `presentation/m4_m5/` |

Numbers in the M4/M5 write-ups, paper and slides are generated from `results/` by `src/render_reports.py`, `paper/make_tables.py` and `presentation/m4_m5/build_slides.py`; edit the `*.tmpl.*` templates or `paper/main.tex`, not the rendered files.

## Notes

- `results/baseline/` and `milestones/m3/` are frozen and never edited. The M3 hypothesis still links to the pre-rename path `presentation/M1/SLIDES.md`, which is now `presentation/m1/slides_outline.md`.
- Study material (viva preparation, the course handout, draft decks) is kept locally and excluded by `.gitignore`.
