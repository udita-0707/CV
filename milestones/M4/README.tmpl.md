# M4 — Implementation and ablations

**Status:** complete (1 November 2026). Plan: [`plan.md`](plan.md). Ablation
plan, written before any ablation was computed: [`ablation_plan.md`](ablation_plan.md).

## What ran

- **One intervention:** Patient-ID–stratified re-aggregation of the frozen M2
  out-of-fold (OOF) predictions. This is an evaluation/reporting change, not a
  model improvement. No retraining, threshold change, new data, augmentation
  or model change. "Patient-ID" is the official NLM mapping key in
  `patient_id`; it is not a slide ID or a patient diagnosis.
- **Inputs (read-only):** `results/baseline/per_sample_predictions.csv`,
  `fold_assignments.csv`, `fold_results.csv`, `baseline_results.csv`. Their
  SHA-256 hashes are recorded in `results/m4/primary_verdict.json` and checked
  again at the end of the run.
- **Reuse assertions (all PASS):** {{n_rows}} rows; unique `relative_path`;
  folds, labels and Patient-IDs identical to `fold_assignments.csv`; each of
  the {{n_ids}} Patient-IDs in exactly one fold; saved predictions equal
  `p >= 0.5`; pooled per-fold metrics recomputed with
  `src.evaluation.binary_metrics` equal `fold_results.csv` (largest absolute
  difference {{reuse_max_abs}}, tolerance 1e-9); fold mean/SD equal
  `baseline_results.csv`. The pooled M2 numbers are unchanged.
- **Code:** `src/patient_stratified.py` (pure functions), `src/run_m4.py`
  (I/O), `src/plots.py`; tests in `tests/`. Command:
  `.venv/bin/python -m src.run_m4`. Notebook:
  `notebooks/m4_patient_stratified.ipynb` (runs top to bottom).

Of the {{n_ids}} Patient-IDs, {{n_ids_pos}} have at least one Parasitized
cell and {{n_ids_negonly}} have only Uninfected cells. Sensitivity is
undefined for those {{n_ids_negonly}} and they are counted, not dropped
(per fold: {{negonly_ids_per_fold}}). Every ID has Uninfected cells, so
specificity is defined for all of them.

## Verdict: {{verdict}}

Pre-registered rule (`../M3/hypothesis.md`, recorded 3 October 2026):
SUPPORTED if at least 4 of 5 paired differences (macro − pooled sensitivity)
are negative **and** their mean is ≤ −1.68 pp. UNSUPPORTED is the mirror
rule. Anything else is INCONCLUSIVE.

| | Predicted (M3) | Observed (M4) |
|---|---|---|
| Direction | negative | {{n_negative_folds}} of {{n_folds}} folds negative (fold {{positive_fold}} positive) |
| Mean macro − pooled | about {{pred_low_pp}} to {{pred_high_pp}} | {{mean_diff_pp}} ({{within_band}} the predicted range) |
| Decision threshold | mean ≤ −1.68 pp | not met: {{mean_diff_abs_pp}} < {{threshold_pp}} (short by {{shortfall_pp}}) |

The direction was right in {{n_negative_folds}} of {{n_folds}} folds, and the mean landed inside the
predicted range. But the magnitude did not reach the pre-registered
threshold, so the outcome is **{{verdict}}**. Applying the threshold's exact
source value (half of the M2 sensitivity fold SD, {{threshold_exact_pp}} pp)
gives the same verdict ({{verdict_exact_threshold}}).

{{table:primary}}

Pooled values are M2's cell-weighted sensitivities, unchanged. CIs are 95%
cluster-bootstrap percentile intervals over Patient-IDs within each fold
(ablation A4; {{boot_resamples}} resamples, seed {{boot_seed}}). The cruder
across-fold *t*-interval for the mean is {{t_ci}}. No significance test is
claimed: with five pairs, the smallest attainable two-sided exact Wilcoxon
p-value is {{min_wilcoxon_p}}, and no test was pre-registered.

## Secondary metrics (pre-registered as descriptive)

- **Specificity:** macro − pooled is {{a5_spec_mean}} on average (95% CI
  {{a5_spec_ci}}; largest single fold {{a5_spec_maxabs}}). Uninfected cells
  per Patient-ID are nearly constant ({{nneg_min}}–{{nneg_max}}, SD
  {{nneg_sd}}), so macro and cell-weighted specificity almost coincide by
  construction.
- **Accuracy:** macro − pooled is {{a5_acc_mean}} (95% CI {{a5_acc_ci}}).
- **Heterogeneity:** per-ID sensitivity SD ranges {{id_sens_sd_min}}–{{id_sens_sd_max}}
  across folds, versus {{id_acc_sd_min}}–{{id_acc_sd_max}} for per-ID
  accuracy. Sensitivity is the more variable of the two in
  {{folds_sens_sd_gt_acc_sd}} of 5 folds. Parasitized cells per Patient-ID
  range from {{npos_min}} to {{npos_max}} (median {{npos_median}}).

{{table:heterogeneity}}

## Ablation summary (exploratory; they do not change the primary verdict)

{{table:ablations}}

- **A1:** weighting each ID's sensitivity by its Parasitized-cell count
  reproduces the pooled value exactly, as it must. The whole
  macro-vs-pooled gap is the change of weighting.
- **A2:** restricting the macro to IDs with ≥ 10 Parasitized cells moves the
  mean to {{a2_k10_mean}}; ≥ 25 moves it to {{a2_k25_mean}}. The result
  depends on the eligibility rule in both directions, and neither variant
  replaces the pre-registered ≥ 1 rule.
- **A3:** deleting one Patient-ID at a time ({{a3_deletions}} deletions)
  keeps the mean between {{a3_mean_min}} and {{a3_mean_max}}.
  {{a3_flips}} single deletions would change the verdict (to {{a3_flip_verdicts}}):
  {{a3_flip_ids}}. The verdict is therefore fragile, and the most influential
  ID is {{a3_top_id}} (fold {{a3_top_fold}}: {{a3_top_npos}} Parasitized
  cells, sensitivity {{a3_top_sens}}).
- **A4:** the cluster-bootstrap 95% CI for the mean difference is
  {{boot_ci}}. It excludes zero but includes −1.68 pp; the per-fold CIs
  are wide.
- **A5:** specificity and accuracy barely move (above).

## Interpretation (kept short; see the paper and M5)

Cell weighting does mask hard Patient-IDs in {{n_negative_folds}} folds, as hypothesised. In
fold {{positive_fold}} it works the other way: several large IDs are hard
({{fn_top10_in_posfold}} of the 10 IDs with the most false negatives are in
that fold), so the pooled value sits *below* the macro. The predicted
mechanism, unequal cell counts, is visible. The direction of its effect
depends on whether the large IDs in a fold are easy or hard.

## Outputs

- `results/m4/per_patient_metrics.csv`: one row per (fold, Patient-ID)
- `results/m4/fold_metrics.csv`: pooled, macro, distributions, undefined counts per fold
- `results/m4/fold_paired_differences.csv`, `results/m4/primary_verdict.json`
- `results/m4/secondary_heterogeneity.csv`, `results/m4/reuse_checks.json`
- `results/m4/ablations/a1_weighting.csv`, `a2_eligibility.csv`, `a2_summary.csv`,
  `a3_leave_one_id_out.csv`, `a3_summary.csv`, `a4_bootstrap.csv`, `a5_secondary_metrics.csv`
- Figures: `results/m4/figures/per_id_sensitivity_by_fold.png`,
  `fnr_vs_positive_cells.png`, `paired_differences.png`

Public segmented-cell dataset; no clinical claim is made or implied.
