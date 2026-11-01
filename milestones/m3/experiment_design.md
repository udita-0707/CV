# M4 experiment design — plan only

**Status:** planned after M2/M3; no M4 code, result, tuning, comparison run, or
ablation has been started.

## Intervention specification

Primary and only intervention: add **Patient-ID–stratified error reporting**
to the frozen M2 OOF predictions. Patient ID means the exact official NLM
Patient-ID mapping key stored in `../../results/baseline/per_sample_predictions.csv`.
For each test fold, calculate:

1. pooled cell-weighted accuracy, sensitivity, specificity, AUC, and F1;
2. each eligible Patient-ID's accuracy and, if it has positive cells,
   sensitivity / false-negative rate; if it has negative cells, specificity;
3. Patient-ID-macro metrics and the distribution (N, mean, SD, IQR, min/max)
   of eligible Patient-ID sensitivity and false-negative rate; and
4. paired macro-minus-pooled differences across the five unchanged folds.

No patient IDs will be inferred from filenames, no cells will be resplit, and
no cells will be excluded silently. Groups lacking a metric denominator will be
counted and reported as not defined for that metric.

## Fixed settings

All of the following remain byte-for-byte/reuse fixed from M2:

- NIH/NLM `cell_images.zip` release and the two official mapping CSVs;
- audited sample manifest, labels, image preprocessing, and Parasitized positive label;
- `fold_assignments.csv` (five Patient-ID-grouped folds; no overlap);
- ImageNet-pretrained frozen ResNet-50 feature vectors;
- five saved classifier states, fixed threshold 0.5, and the corresponding
  `per_sample_predictions.csv` probabilities; and
- M2 metric implementations for the pooled values.

There is no retraining, new model, additional data, image augmentation, loss
change, threshold tuning, or test-fold selection. The new computation is only a
grouped re-aggregation of existing OOF rows.

## Comparison method and decision rule

Within each fold, pair macro-by-Patient-ID sensitivity with its existing pooled
sensitivity. The primary value is the mean of the five paired differences.
Apply the pre-registered rules in `hypothesis.md`: support requires at least
four negative paired differences and mean ≤ −1.68 pp (half of M2's observed
3.36 pp sensitivity fold SD); the directional opposite rule is unsupported;
the remainder is inconclusive. The secondary results are descriptive and will
not be used to change the primary rule.

## Risks and safeguards

| Risk                                                          | Safeguard                                                                                                                   |
| ------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| Calling official mapping keys “slides” or fabricated patients | Preserve the field name `patient_id`; describe it as an official mapping key.                                               |
| A group lacks positive/negative cells                         | Do not divide by zero; record the group count and eligibility.                                                              |
| A recomputation silently changes M2 folds or scores           | Assert row counts, unique `relative_path`, fold equality, and probability equality against M2 artifacts before aggregation. |
| Treating an analysis result as clinical performance           | State the public-dataset, segmented-cell scope in every result slide/write-up.                                              |
| Expanding into multiple interventions                         | Reject any architecture, preprocessing, augmentation, loss, or training modification in M4.                                 |
