# M4 ablation plan — exploratory

**Written:** 1 November 2026, before any ablation was computed and before the
primary paired differences were inspected.

**Status of these analyses:** *exploratory. They do not change the primary
verdict.* M3 pre-registered one primary comparison and its decision rule
(`../M3/hypothesis.md`); it did not pre-register ablations. The course
handout requires ablations, so the ones below vary **only the aggregation**
of the frozen M2 out-of-fold predictions. The ResNet-50 features, classifier
states, probabilities, 0.5 threshold, labels, Patient-IDs and folds are
fixed in every ablation.

Notation: within a test fold, Patient-ID *i* has TP*ᵢ*, FN*ᵢ*, TN*ᵢ*, FP*ᵢ*.
Pooled sensitivity = ΣTP / Σ(TP + FN). Per-ID sensitivity
sᵢ = TPᵢ / (TPᵢ + FNᵢ), defined only when TPᵢ + FNᵢ > 0. Differences are
macro − pooled, in percentage points (pp).

## A1 — Weighting scheme

Compare three aggregations of the same per-ID sensitivities, per fold:

1. pooled, cell-weighted (the M2 headline);
2. Patient-ID macro: unweighted mean of sᵢ (the primary M4 metric);
3. per-ID sensitivity weighted by each ID's positive-cell count.

(3) is algebraically identical to (1); it is a **sanity check** and the code
asserts |(3) − (1)| < 1e-12 in every fold. Output:
`results/m4/ablations/a1_weighting.csv`.

## A2 — Eligibility threshold

Recompute the macro sensitivity using only IDs with at least *k* Parasitized
cells in the test fold, *k* ∈ {1 (primary), 10, 25}. Report, per fold and *k*:
IDs kept, IDs excluded, macro sensitivity, difference from the unchanged
pooled sensitivity, and (for context) pooled sensitivity restricted to the
kept IDs. Output: `results/m4/ablations/a2_eligibility.csv` plus a 5-fold
summary per *k*.

## A3 — Leave-one-Patient-ID-out robustness

For each fold and each ID with positive cells, remove all of that ID's cells
from the fold and recompute pooled sensitivity, macro sensitivity and their
difference. Report the change in the paired difference, the largest absolute
change per fold, the five most influential IDs overall, and how many of the
single-ID deletions would change the M3 verdict when the other four folds are
left as observed. Output: `results/m4/ablations/a3_leave_one_id_out.csv` and
`a3_summary.csv`.

## A4 — Uncertainty: cluster bootstrap over Patient-IDs

Within each fold, resample that fold's Patient-IDs with replacement (all IDs
in the fold, keeping each ID's cells together), recompute pooled and macro
sensitivity on the resample and take the difference. 2,000 resamples,
`numpy.random.default_rng(42)`. Report 95% percentile CIs for each fold's
difference and for the mean of the five differences (each replicate
resamples all five folds independently). Also report the across-fold
*t*-interval for the mean (df = 4) as a second, cruder interval. The
bootstrap describes sampling of Patient-IDs within the fixed test folds; it
does not capture classifier-training variance. No p-values or significance
claims. Output: `results/m4/ablations/a4_bootstrap.csv`.

## A5 — Secondary metrics: specificity and accuracy

Repeat the macro-versus-pooled comparison for specificity (IDs with ≥ 1
Uninfected cell) and accuracy (all IDs), with per-ID distributions
(N, mean, SD, IQR, min, max) and the same bootstrap CIs. These are the M3
secondary metrics; they are described, not tested against a rule. Output:
`results/m4/ablations/a5_secondary_metrics.csv`.

## What will not be done

No threshold sweep, recalibration, re-weighting of training, alternative
grouping key (e.g. filename-derived slide IDs), or exclusion of folds or IDs
from the primary metric. Any ablation result that looks more favourable to
the hypothesis than the primary result is reported as exploratory and does
not replace the primary verdict.
