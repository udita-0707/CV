# Introduction

## Problem background

Microscopic thin-blood-smear images can be posed as a binary computer-vision
task on segmented red-blood-cell crops: classify a cell as Parasitized or
Uninfected. This project studies the evaluation of that task on a public
dataset; it does not make a clinical or diagnostic-performance claim.

## Healthcare computer-vision motivation

The project literature frames microscopy images as a setting in which image
appearance can vary with stain, lighting, focus, and cell morphology. In the
base-paper narrative, such variation makes hand-engineered approaches
difficult and motivates pretrained convolutional features
[`paper1`](../../papers/paper1_rajaraman.md). For this project, the practical
motivation is methodological: a computer-vision score should be interpreted
with the source grouping and the error metric that produced it.

## Malaria cell classification

Rajaraman et al. formulate the task with Giemsa-stained thin-smear cell images
and compare a custom CNN with pretrained CNN feature extractors. Their stated
question is whether pretrained features can distinguish parasitized from
uninfected cells and which extracted representation is useful for that binary
classification task [`paper1`](../../papers/paper1_rajaraman.md). We retain that
task and label convention, treating Parasitized as the positive class for
sensitivity/recall.

## Dataset

The experiment uses only the NIH/NLM single-cell thin-smear release named by
the course handout and base paper. The official NLM archive contains 27,558
PNG cell images, balanced as 13,779 Parasitized and 13,779 Uninfected images;
the official NLM Patient-ID mapping files are used to group cells before
evaluation. The local audit verified every image, mapping reference, and
cross-label duplicate check; its archive hash and source record are in
`../../results/baseline/dataset_source.json` and its results are in
`../../results/baseline/dataset_audit.md`.

## Deep-learning approaches

The project survey shows a range of pretrained CNN, hybrid-CNN, transformer,
and ensemble approaches on this release. Reported preprocessing, models, and
scores are not directly comparable when the evaluation protocol differs:
Narayanan et al. use an explicit cell-level 80/20 hold-out
[`paper4`](../../papers/paper4_narayanan.md), EDRI uses a stratified 80/10/10
cell split [`paper6`](../../papers/paper6_edri.md), and CNN–ViT reports 80/20 plus
stratified k-fold language without a patient-disjoint protocol
[`paper8`](../../papers/paper8_cnnvit.md). These papers are supporting evidence
about the survey, not additional data for this experiment.

## Base paper

The base paper is Rajaraman et al. (2018), _Pre-trained convolutional neural
networks as feature extractors toward improved malaria parasite detection in
thin blood smear images_. It is appropriate for reproduction because it uses
the same public NLM cell release, evaluates pretrained CNN feature extractors,
and reports both a patient-level five-fold protocol and a separate cell-level
comparison [`paper1`](../../papers/paper1_rajaraman.md). M2 reproduces the
patient-level ResNet-50 feature-extractor direction, rather than replacing it
with MalariaNet or another newer architecture.

## Baseline and evaluation issue

In paper1 Table 6, the proposed model is reported at 0.959 accuracy, 0.947
sensitivity, 0.972 specificity, and 0.991 AUC under patient-level CV; its
separate cell-level comparison is higher (0.986 accuracy, 0.981 sensitivity,
0.992 specificity, and 0.999 AUC) [`paper1`](../../papers/paper1_rajaraman.md).
M2's independently measured, official-Patient-ID-grouped five-fold baseline
is 93.90% ± 1.95 pp accuracy, 94.24% ± 3.36 pp sensitivity, 93.56% ± 1.30 pp
specificity, 0.9832 ± 0.0086 AUC, and 93.90% ± 2.03 pp F1. The saved
comparison shows that the reproduction is below paper1's accuracy and
specificity but close in mean sensitivity; it is an approximate reproduction,
not an exact rerun, because paper1's fold membership and several implementation
details are not available in the supplied project source.

The group-disjoint choice matters because cells belonging to the same source
can share visual conditions. Paper1 explicitly uses patient-level evaluation
to prevent stain/artifact leakage, whereas M1 documents several later methods
that report cell-level or patient-unspecified splits
[`paper1`](../../papers/paper1_rajaraman.md), [`paper5`](../../papers/paper5_alharbi.md),
[`paper6`](../../papers/paper6_edri.md). The M2 split asserts zero overlap of each
official mapping key between a fold's train and test sets.

## Literature gap

The gap is not that patient-level evaluation has never been proposed:
Rajaraman already reported it. Nor is the claim that leakage necessarily causes
a dramatic mean-accuracy collapse. MalariaNet reports a smaller slide-disjoint
versus per-cell difference for its own model and, importantly, reports a
leakage-free sensitivity/specificity imbalance (93.94% versus 97.41%)
[`paper2`](../../papers/paper2_malarianet.md). M1 therefore identifies a narrower,
testable question: under a leakage-free group protocol, does a pooled mean hide
source-group variation in errors, particularly false negatives?

## Research objective

Using the fixed M2 out-of-fold predictions and the same five official
Patient-ID-grouped folds, the objective is to test whether Patient-ID-macro
sensitivity differs from the familiar pooled cell-weighted sensitivity, and to
describe the distribution of error across those official mapping groups. The
primary comparison and its falsification criteria were recorded before M4 in
[`hypothesis.md`](hypothesis.md).

## Proposed direction

The one planned M4 change is an evaluation/reporting layer: retain every M2
model, setting, fold, prediction, and threshold, then add Patient-ID-stratified
error summaries beside pooled metrics. It is intentionally not a bundle of a
new backbone, preprocessing, augmentation, loss, or training strategy. This
public-dataset research experiment will report the outcome, whether supported,
unsupported, or inconclusive, without making a clinical claim.
