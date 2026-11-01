# M5 — Failure analysis

**Status:** complete (1 November 2026). Code: `src/failure_analysis.py`,
`src/image_review.py`, `src/run_m5.py`
(`.venv/bin/python -m src.run_m5`). Outputs: `results/m5/`.

**Scope.** Everything below describes the errors of the frozen M2 classifier
(frozen ImageNet ResNet-50 features + FC head, threshold 0.5) on the public
NIH/NLM segmented-cell release, under the five official-Patient-ID-grouped
folds. "Patient-ID" is the official NLM mapping key. No result here is a
clinical or diagnostic claim. Prediction-level results use only the saved
CSVs; image-level observations come from a blind, single-reviewer,
non-expert look at the images and are **observations, not established
causes**.

## 1. Which Patient-IDs hold the errors?

False negatives (FN) are concentrated. {{fn_total}} FN fall in
{{fn_ids_any}} of the {{fn_ids_at_risk}} IDs that have Parasitized cells.
The top ID ({{fn_top1_id}}, fold {{fn_top1_fold}}) holds {{fn_top1_share}}
of all FN. The top 10 IDs hold {{fn_top10_share}}, {{fn_ids_50}} IDs reach
50%, and {{fn_ids_80}} reach 80%. False positives (FP) are more diffuse:
{{fp_total}} FP across {{fp_ids_any}} of {{fp_ids_at_risk}} IDs. The top ID
({{fp_top1_id}}) holds {{fp_top1_share}}, the top 10 hold
{{fp_top10_share}}, and {{fp_ids_50}} IDs are needed for 50%.

**Top 10 Patient-IDs by false negatives**

{{table:top10_fn}}

**Top 10 Patient-IDs by false positives**

{{table:top10_fp}}

Figure: `results/m5/figures/error_concentration.png` (cumulative share of
errors vs share of IDs).

## 2. Errors vs cells per ID, and vs fold

{{table:errors_vs_cells}}

IDs with fewer than 10 Parasitized cells ({{small_ids}} IDs) contribute
{{small_ids_fn_share}} of all FN. The {{n_big_ids}} IDs with ≥ 100
Parasitized cells contribute {{fn_share_big_ids}}. Per-ID rate and cell count
are only weakly rank-correlated (Spearman ρ = {{rho_fn}} for FNR vs
Parasitized cells, {{rho_fp}} for FPR vs Uninfected cells; descriptive, no
test). Uninfected cells per ID are nearly constant ({{nneg_min}}–{{nneg_max}}),
which is why weighting can move sensitivity but hardly moves specificity.
Figure: `results/m5/figures/error_rates_vs_cells.png`.

{{table:errors_by_fold}}

Fold {{positive_fold}}, the only fold where macro − pooled sensitivity is
positive, has the most FN ({{posfold_fn}}). It also contains
{{fn_top10_in_posfold}} of the 10 IDs with the most FN, and its top ID
({{posfold_top_fn_id}}, {{posfold_top_fn_npos}} Parasitized cells) alone
holds {{posfold_top_fn_share}} of that fold's FN. Large, hard IDs pull the
cell-weighted pooled sensitivity *below* the per-ID macro: the masking
mechanism of the hypothesis, running in reverse.

## 3. Confidently wrong cells

{{conf_fn}} FN have p < 0.1 ({{conf_fn_share}} of all FN; {{conf_fn_ids}}
Patient-IDs; the most frequent is {{conf_fn_top_id}} with
{{conf_fn_top_count}}, {{conf_fn_top_share}} of them). {{conf_fp}} FP have
p > 0.9 ({{conf_fp_share}} of all FP; {{conf_fp_ids}} Patient-IDs). About a
quarter of errors are therefore not borderline cases near the 0.5 threshold.
List: `results/m5/confident_errors.csv`.

## 4. Calibration

Brier score {{brier}}, expected calibration error (10 equal-width bins)
{{ece}}. Per fold, Brier ranges from {{brier_best}} to {{brier_worst}} (worst
in fold {{brier_worst_fold}}). {{cal_extreme_share}} of cells fall in the two
extreme bins (p < 0.1 or p ≥ 0.9). The largest gap between mean predicted
probability and observed Parasitized fraction in any bin is
{{cal_max_gap}}, in the mid-range bins, where the predicted probability sits
above the observed Parasitized fraction. Figure: `results/m5/figures/reliability_diagram.png`. No
recalibration was done; it would be a second intervention.

## 5. Does one Patient-ID drive the fold with the largest sensitivity SD?

Fold {{sd_fold}} has the largest per-ID sensitivity SD ({{sd_value}}), with
fold {{sd_second_fold}} almost tied ({{sd_second_value}}). The single most
influential ID in fold {{sd_fold}} is {{sd_driver}} (sensitivity
{{sd_driver_sens}} on {{sd_driver_npos}} cells). Removing it lowers the SD
to {{sd_without}} (reduction: {{sd_reduction_share}}). So it contributes,
but **no single ID drives the spread**: the most any one deletion removes
in any fold is {{sd_reduction_share_max}}.

{{table:sd_drivers}}

## 6. Image-level review

**Dataset.** Only NLM's official archive and mapping CSVs (URLs from
`results/baseline/dataset_source.json`) were used. The archive was fetched
again with the project's downloader. The archive and both mapping files
match their recorded SHA-256 (archive `{{archive_sha_short}}…`), and all
{{images_verified}} local PNGs match their manifest SHA-256 (status
{{dataset_verified}}; `results/m5/dataset_verification.json`).
`src/config.raw_data_dir` resolves to `data/raw/`; the frozen record's
`archive_path` still says `reproduction/data/raw/…` and was left unedited.
`src.dataset.ensure_official_dataset` was not called directly, because it
rewrites the frozen `results/baseline/dataset_source.json` with a new
timestamp. Its URLs, download helper and hash function were reused instead.

**Protocol** (`image_review_protocol.md`, written before viewing). One
reviewer labelled {{rev_total}} crops: the AI assistant running this
analysis, **not a microscopist**. The crops were 24 lowest-p FN, 24
highest-p FP, 24 random TP and 24 random TN, shuffled and shown blind (no
class, probability or ID) in numbered grids. Categories were fixed in
advance. Labels are in `image_review_labels.csv`; the counts below are
computed by `src/run_m5.py`. For the stain flag, the working rule applied to
every grid was: crop overall grey/blue/green-tinged rather than the
pink-tan majority, or unusually saturated magenta. "Possible label noise" is
derived by code: visible content disagrees with the label.

{{table:image_review}}

**Observations (not causes):**

- The reviewer's inclusion judgement agreed with the label in every random
  correct control where it was not "unclear" ({{rev_rtp_inclusion_yes}}/24 TP
  show an inclusion; {{rev_rtn_inclusion_yes}}/24 TN do). That is a weak
  check that the category is usable at all.
- Among the most confident FN (all labelled Parasitized), {{rev_tfn_inclusion_no}}/24
  show **no** visible inclusion and {{rev_tfn_inclusion_unclear}} are unclear.
  Among the most confident FP (all labelled Uninfected),
  {{rev_tfp_inclusion_yes}}/24 **do** show a stained inclusion. The model's
  most confident errors are mostly cells whose visible content a non-expert
  would call the other class.
- Grey/blue-tinged crops are over-represented among confident FN
  ({{rev_tfn_pale_or_atypical_stain}}/24) relative to random TP
  ({{rev_rtp_pale_or_atypical_stain}}/24).
- Segmentation artefacts (cut-off cells, objects protruding at the border)
  appear in {{rev_tfp_segmentation_artefact}}/24 FP vs
  {{rev_rtn_segmentation_artefact}}/24 random TN. Several FP inclusions sit on
  the crop border and could be a neighbouring cell, platelet or stain debris.
- Blur was almost never flagged; at this crop size the reviewer could not
  judge focus reliably.

Grids: `results/m5/figures/grid_top_false_negatives.png`,
`grid_top_false_positives.png`, `grid_worst_patient_ids.png` (worst three
IDs with ≥ 10 Parasitized cells: {{worst_ids}}). In the two worst IDs, the
missed cells look like uniformly stained cells without a visible inclusion,
while the same IDs' correctly detected cells show one. In the third, the
missed cells have small inclusions at the crop edge.

## 7. What the evidence supports vs what is speculation

**Supported by the saved predictions:**

- False negatives are concentrated in a small number of Patient-IDs; false
  positives are more spread out.
- The sign of macro − pooled sensitivity in a fold follows whether that
  fold's large-cell-count IDs are easier or harder than its small ones. The
  verdict is sensitive to single IDs (M4 ablation A3).
- About a quarter of errors are confident (p < 0.1 or p > 0.9); calibration
  is otherwise reasonable.
- No single Patient-ID explains the spread of per-ID sensitivity in the
  largest-SD fold.

**Observation only (single non-expert reviewer, small sample):**

- Most of the confident errors look like cells whose visible content
  disagrees with the dataset label. This is *consistent with* label noise in
  the segmented-cell labels (as Wilm et al. report for border cells in the
  same smears), but also with faint or out-of-plane parasites, platelets or
  debris over a cell, or reviewer error.
- Grey/blue-tinged crops among confident FN may reflect stain or acquisition
  differences between source slides. This is not tested here.

**Speculation (not tested):** stain normalisation, recalibration, or
cleaning the labels would change these errors. Each would be a new
intervention and is out of scope for this one-change study.

## 8. Threats to validity

- **One review, one non-expert reviewer:** no microscopist and no
  inter-rater agreement. The categories are coarse, and the stain flag is
  relative to each grid.
- **Selection:** the reviewed errors are the most confident ones, not a
  random sample of errors. Controls are random, not matched by Patient-ID
  or fold.
- **Five folds, one seed, one fold assignment:** all fold-level statements
  rest on n = 5. A different `StratifiedGroupKFold` seed would regroup the
  IDs and could change the sign of a fold's difference (fold
  {{positive_fold}} is one such case).
- **Patient-ID is the official mapping key, not a slide:** some Uninfected
  cells come from infected patients' slides. One source patient appears
  under two microscope-specific keys (the official datasheet notes this).
- **Approximate reproduction:** M2 differs from paper1 in folds, feature
  layer, normalisation and classifier details, so these failure modes
  describe *this* reproduction, not paper1's model.
- **Public segmented-cell data only:** no external dataset, no
  whole-slide or patient-level diagnosis, no clinical claim.
