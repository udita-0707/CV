# M5 image-review protocol

**Written:** 1 November 2026, before any cell crop was viewed for M5.

## Purpose and status

Describe visible properties of misclassified cells next to correctly
classified controls. Every finding is an **observation, not an established
cause**. The review cannot show why the classifier failed, and it cannot
re-label the dataset.

## Who labels and how

- **Reviewer:** one reviewer, the AI assistant (Claude) used to run this
  project's M4/M5 analysis. It is **not a microscopist** and has no
  parasitology training. There is no second reviewer and no adjudication.
- **Blinding:** 96 crops (24 per group) are shuffled with a fixed seed and
  shown as four numbered grids (`R01`–`R96`). The grids show no class, model
  probability, Patient-ID or group. The key linking `R##` to a cell lives in
  `results/m5/image_review_key.csv` and is not opened until all 96 labels are
  saved.
- **Groups (fixed before viewing):**
  1. 24 false negatives with the lowest P(Parasitized);
  2. 24 false positives with the highest P(Parasitized);
  3. 24 true positives drawn at random (seed 42);
  4. 24 true negatives drawn at random (seed 42).
- **Display:** each crop resized to 160 × 160 px (Lanczos) from the original
  PNG in the hash-verified official release. No colour or contrast change.
- **Labels:** written to `image_review_labels.csv` in this folder, one row per
  `R##`. Counts per group are computed by `src/run_m5.py`, not by hand.

## Categories (fixed before viewing)

| Field | Values | Meaning |
|---|---|---|
| `inclusion_visible` | yes / no / unclear | A distinct, darker purple/magenta stained inclusion (dot, ring or irregular body) is visible on or in the cell. |
| `pale_or_atypical_stain` | 0 / 1 | The whole crop's colour is clearly paler, darker, or a different hue than most crops in the same grid. |
| `blur_or_low_contrast` | 0 / 1 | The cell outline or interior looks out of focus or washed out. |
| `segmentation_artefact` | 0 / 1 | The crop is cut off, contains part of a neighbouring cell or debris, or the cell is badly off-centre or misshapen. |
| `note` | free text | Brief description, optional. |

**Derived by code, not judged:** `possible_label_noise` = a Parasitized-labelled
cell with `inclusion_visible = no`, or an Uninfected-labelled cell with
`inclusion_visible = yes`. This flag means only "the visible content does not
match the label as seen by a non-expert"; a faint or out-of-plane parasite,
a platelet or stain debris over a cell, or reviewer error are all equally
possible explanations.

## Limitations stated in advance

Single non-expert reviewer; small crops; 24 cells per group; the top-error
groups are selected by the model's own confidence, so they are not a random
sample of errors; correct-prediction controls are random and therefore not
matched to the errors by Patient-ID or fold.
