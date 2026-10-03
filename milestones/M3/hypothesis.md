# M3 hypothesis and pre-registered prediction

**Recorded:** 3 October 2026 (Asia/Kolkata), after the saved M2 baseline and
before any M4 code. This document is a prediction, not a result.

## One primary intervention

**Patient-ID–stratified error reporting on the fixed M2 out-of-fold
predictions.** The ResNet-50 extractor, classifier, NLM dataset, preprocessing,
threshold, official Patient-ID groups, and five saved folds remain fixed. The
only planned change is to report within-fold macro-by-Patient-ID metrics and
the Patient-ID distribution of errors alongside the existing pooled, cell-
weighted metrics. This is an evaluation/reporting intervention, not a new
model, training change, or clinical claim.

The intervention follows the M1 direction exactly: `../../presentation/M1/SLIDES.md` says to stop
reporting only mean accuracy and add per-slide error distribution plus
sensitivity versus specificity under the same leakage-free split. Because M2
has verified official **Patient-ID** mappings rather than an undocumented
slide-ID table, the operational unit is the official Patient-ID mapping key.
We will not rename it a slide ID or invent a slide mapping.

## Falsifiable hypothesis

**IF** the fixed M2 out-of-fold predictions are evaluated separately for every
official Patient-ID within each unchanged patient-grouped fold, **THEN**
Patient-ID–macro sensitivity for Parasitized will be lower than the existing
pooled cell-weighted sensitivity, and Patient-ID sensitivity will show more
heterogeneity than pooled accuracy, **BECAUSE** cells from one source group
share acquisition/stain characteristics and groups contribute unequal numbers
of cells; a pooled cell-weighted mean can therefore conceal a small number of
groups with concentrated false negatives.

We hypothesize that **Patient-ID–stratified error reporting** will **decrease
the reported macro sensitivity** under the identical patient-grouped five-fold
protocol because cell weighting can mask difficult groups; the largest effect
is expected in **sensitivity/recall**, while pooled accuracy and specificity
may change only modestly. No classifier output, threshold, or model parameter
is changed, so the original pooled M2 metrics must remain numerically
unchanged.

## Prediction record

### Baseline expectation

M2's measured pooled patient-grouped results are accuracy **93.90% ± 1.95 pp**,
sensitivity **94.24% ± 3.36 pp**, specificity **93.56% ± 1.30 pp**, AUC
**0.9832 ± 0.0086**, and F1 **93.90% ± 2.03 pp** (five folds;
`../../results/baseline/baseline_results.csv`). The larger already-measured
fold-to-fold SD for sensitivity motivates examining which official mapping
groups contribute errors; it does not itself establish a Patient-ID-level
result.

### Modified-model prediction

There is **no modified model**: all weights and OOF probabilities are fixed
baseline artifacts. The modified **evaluation** prediction is a mean paired
difference (macro-by-Patient-ID sensitivity minus pooled sensitivity) of
approximately **−1 to −3 percentage points** across the five unchanged test
folds. This pre-registered magnitude is deliberately bounded by the measured
M2 sensitivity fold SD (3.36 pp); it is not claimed as a literature-derived
effect size.

- **Primary metric:** paired per-fold difference in sensitivity: unweighted
  mean over Patient-ID sensitivities (among IDs with at least one Parasitized
  cell) minus pooled cell-level sensitivity.
- **Secondary metrics:** analogous Patient-ID-macro versus pooled differences
  for accuracy and specificity; per-fold standard deviation, IQR, and range of
  Patient-ID false-negative rate; count of Patient IDs with no positive cells
  (reported, not silently discarded from unrelated metrics).
- **Direction prediction:** primary paired difference is negative. Sensitivity
  heterogeneity is expected to be more visibly affected than the pooled
  accuracy headline; we do not predict an improvement in AUC, since scores are
  unchanged.
- **Supported if:** at least 4 of 5 paired sensitivity differences are negative
  **and** their mean is ≤ −1.68 pp (half of the pre-existing 3.36 pp M2
  sensitivity fold SD). The resulting per-fold table and every group count
  must be saved.
- **Unsupported if:** at least 4 of 5 paired sensitivity differences are
  positive and their mean is ≥ +1.68 pp. That is the directionally opposite,
  M2-SD-referenced outcome.
- **Inconclusive if:** neither directional rule is met, including a negative
  mean with magnitude below 1.68 pp, mixed-sign paired differences, unavailable
  group denominators, or any failed reuse assertion for the M2 folds/predictions.

## Why this change and no bundle

Rajaraman's patient-level protocol was designed to avoid stain/artifact
leakage, and M1 notes that later work often reports high cell-level or
patient-unstated scores. MalariaNet confirms that mean performance need not
collapse under leakage-free grouping while its leakage-free sensitivity and
specificity differ (93.94% and 97.41%, respectively) [`paper2`](../../papers/paper2_malarianet.md).
M2 likewise has a sensitivity fold SD (3.36 pp) larger than its accuracy SD
(1.95 pp). The proposed analysis directly tests the remaining M1 question
without introducing colour normalization, augmentation, a loss, attention, a
new backbone, or any other confounded change.
