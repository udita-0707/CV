# Viva preparation — M2/M3

Each answer is grounded in the saved project artifacts and is no more than
three sentences.

## M2

### Why this paper?

Rajaraman et al. is the base paper because it uses the exact public NLM cell
release, a pretrained-CNN feature-extraction method that can be reimplemented,
and both patient-level and cell-level reported values. It is the origin of the
evaluation question in our M1 slides.

### What exactly did you reproduce?

We reproduced the patient-level direction: ImageNet-pretrained frozen ResNet-50
features followed by a fresh FC classifier with dropout 0.5, evaluated over
five patient-grouped folds. It is an approximate reproduction because paper1's
exact fold membership, selected feature layer, and several training details are
not in the supplied source; each deviation is logged.

### Why this dataset?

The handout and base paper specify the NIH/NLM malaria cell-image dataset for
this topic. We downloaded only the official `cell_images.zip` release and its
official mapping CSVs, then verified 27,558 images with 13,779 in each class.

### Why patient-level splitting?

Paper1 says patient-level splitting prevents stain/artifact information from
the same patient contaminating both train and test. It makes each test group's
appearance unseen by the classifier and matches the base paper's main protocol.

### Why is random cell-level splitting problematic?

Random cell splitting can place cells from the same source in train and test,
so stain, focus, or lighting can leak. The model can then receive an optimistic
score that is not comparable to a group-disjoint score.

### How were the folds built?

We used the exact Patient-ID keys from NLM's official mapping CSVs in a
shuffled `StratifiedGroupKFold` with seed 42. The five test folds contain
5,497, 5,520, 5,544, 5,483, and 5,514 cells, and code asserts zero Patient-ID
overlap in every train/test pair.

### Why this model?

ResNet-50 is one of paper1's pretrained feature extractors and is the proposed
model associated with the Table 6 patient-level baseline in our project source.
Using it keeps M2 tied to the base paper instead of substituting a newer model.

### What preprocessing did you use?

Images were resized bilinearly to 224×224 and normalized with ImageNet mean and
standard deviation; no augmentation was used. The paper1 summary reports
model-compatible resize and mean normalization but not exact values, so this
documented convention is an approximation.

### How close are your results to the paper?

Our measured mean accuracy is 93.90% ± 1.95 pp versus paper1's published 95.9%,
and sensitivity is 94.24% ± 3.36 pp versus 94.7%. Specificity is lower,
93.56% ± 1.30 pp versus 97.2%, and AUC is 0.9832 ± 0.0086 versus 0.9910.

### Why do they differ?

We cannot recover paper1's original patient folds, exact feature layer,
normalization parameters, classifier width, or original hyperparameter search
from the supplied source. Our official mapping-based folds and fixed documented
settings are valid but not paper-exact, so an exact numerical match is not
expected.

### What counts as a successful reproduction?

Success is a verified exact dataset, an end-to-end pipeline with zero group
overlap, correct saved metrics, and a transparent comparison with the published
baseline. It does not require an exact score match or a claim that our run is
identical to unpublished paper details.

## M3

### What is the research gap?

The gap is whether pooled mean metrics hide source-group error variation under
a leakage-free protocol, especially in sensitivity. It is not the claim that
patient-level splitting is new or that mean accuracy must collapse.

### Why does it matter?

A pooled cell-weighted average can be dominated by groups that contribute many
easy cells while concealing groups with concentrated false negatives. This is a
methodological interpretation issue for this public-image experiment, not a
clinical-performance claim.

### Why this change?

M1 previews per-slide error and sensitivity/specificity analysis, while M2
shows sensitivity has the largest fold-to-fold SD (3.36 pp) among its key
threshold metrics. The official mapping permits an auditable grouping without
inventing patients or collecting external data.

### Why only one change?

The only M4 intervention is Patient-ID–stratified evaluation of already-saved
OOF rows. The model, data, preprocessing, folds, classifier states, threshold,
and probabilities stay fixed, so a model or training change cannot confound it.

### What is the hypothesis?

If the fixed M2 predictions are summarized by official Patient ID, macro
sensitivity will be lower than pooled sensitivity and sensitivity will show
greater group heterogeneity. The proposed mechanism is unequal cell counts and
shared source appearance masking difficult groups in a cell-weighted mean.

### What is the prediction and why?

We predict macro minus pooled sensitivity of about −1 to −3 pp across the same
five folds. The bounded magnitude is pre-registered against M2's 3.36 pp
sensitivity fold SD; it is not presented as a result.

### Which metric should change?

The primary metric is the paired per-fold macro-by-Patient-ID sensitivity minus
pooled sensitivity difference. Accuracy and specificity are secondary, and AUC
should not change because the model scores are held fixed.

### What would falsify it?

It is unsupported if at least four of five paired sensitivity differences are
positive and their mean is at least +1.68 pp. Mixed directions or a smaller
effect are inconclusive rather than proof of the hypothesis.

### What happens if it fails?

We report the pre-registered outcome honestly as unsupported or inconclusive
and retain the pooled M2 result. A failed prediction means the proposed
mechanism was not supported on these fixed public-dataset folds; it does not
justify changing the model after seeing the test results.

### Why is this not a clinical claim?

The work evaluates labeled, segmented images from one public P. falciparum
thin-smear dataset and does not study patient diagnosis, prevalence, workflow,
or deployment. Every result is framed as a research experiment on this dataset.
