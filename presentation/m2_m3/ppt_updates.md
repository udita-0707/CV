# PPT updates after M2/M3 (do not edit `../M1/SLIDES.md`)

Use the existing M1 deck terminology. Existing literature slides remain source
evidence; the following is the exact update/addition list for the final deck.

## Existing slides to change

### Slide 1 — Title

**Patient- vs cell-level evaluation in malaria parasite classification**  
NIH / NLM malaria cell images (27,558 cells)  
Rajaraman et al. (2018) base-paper reproduction + one evaluation change

### Slide 7 — Research gap

- Rajaraman already measured cell-level 98.6% versus patient-level 95.9%; our
  gap is not “we discovered leakage.”
- MalariaNet confirms the leakage direction but its mean drop is only about
  1–2 pp; “leakage wrecks accuracy” is too simple.
- Our M2 baseline has sensitivity SD 3.36 pp versus accuracy SD 1.95 pp across
  the same patient-grouped folds.
- Open question: under the leakage-free M2 folds, does pooled mean sensitivity
  hide Patient-ID-level false-negative variation?

### Slide 8 — Proposed direction

- Keep every M2 setting, official Patient-ID fold, ResNet-50 probability, and
  0.5 threshold fixed.
- **ONE change:** add Patient-ID–stratified error reporting beside pooled
  accuracy, sensitivity, specificity, AUC, and F1.
- This is an evaluation/reporting change, not a new model, preprocessing,
  augmentation, loss, or training strategy.
- Public segmented-cell research only; no clinical claim.

### Slide 10 — Conclusion / next

- M2 reproduced the exact NLM release under verified, zero-overlap
  Patient-ID-grouped five-fold CV.
- The result is an approximate reproduction: folds and some paper details were
  not published in the supplied source.
- M3 prediction is saved before M4: test whether Patient-ID-macro sensitivity
  falls below pooled sensitivity on identical OOF predictions.
- Next is only the pre-registered M4 grouped-error analysis.

## New slides to insert after existing Slide 10

### Slide 11 — M2 methodology

- Exact official NLM `cell_images.zip`: 13,779 Parasitized + 13,779 Uninfected
- Official Patient-ID mapping CSVs; 201 unique mapping IDs across all cells
- Patient-grouped, class-stratified five-fold CV; zero train/test ID overlap
- Frozen ImageNet ResNet-50 features + FC classifier, dropout 0.5
- Approximations are logged: paper fold IDs, exact feature layer, and some
  training details were unavailable

### Slide 12 — Dataset and evaluation protocol

- Audit PASS: 27,558 PNGs; no corrupt images, missing mapping references,
  unmapped images, or cross-label byte-identical duplicates
- Test folds: 5,497 / 5,520 / 5,544 / 5,483 / 5,514 cells
- Positive class: Parasitized
- Metrics: accuracy, sensitivity/recall, specificity, AUC, F1

### Slide 13 — Reproduced baseline results

| Metric      |     M2 mean ± SD |
| ----------- | ---------------: |
| Accuracy    | 93.90% ± 1.95 pp |
| Sensitivity | 94.24% ± 3.36 pp |
| Specificity | 93.56% ± 1.30 pp |
| AUC         |  0.9832 ± 0.0086 |
| F1          | 93.90% ± 2.03 pp |

Add the M2 OOF ROC and confusion-matrix figures. Caption: “Measured on the
official Patient-ID-grouped M2 folds; not a clinical-performance claim.”

### Slide 14 — Comparison with paper

| Metric      | Paper1 Table 6 patient level | M2 measured | Difference |
| ----------- | ---------------------------: | ----------: | ---------: |
| Accuracy    |                       95.90% |      93.90% |   −2.00 pp |
| Sensitivity |                       94.70% |      94.24% |   −0.46 pp |
| Specificity |                       97.20% |      93.56% |   −3.64 pp |
| AUC         |                       0.9910 |      0.9832 |    −0.0078 |

Footer: “Approximate reproduction: exact original folds and several source
details were not available; no test-fold tuning was performed.”

### Slide 15 — Hypothesis and prediction (saved before M4)

- **IF** we report errors by official Patient-ID on the fixed M2 OOF rows,
  **THEN** Patient-ID-macro sensitivity will be lower than pooled sensitivity,
  **BECAUSE** unequal cell counts can mask difficult shared-appearance groups.
- Prediction: macro minus pooled sensitivity ≈ −1 to −3 pp.
- Primary criterion: ≥4/5 negative paired fold differences and mean ≤ −1.68 pp.
- An opposite result is unsupported; mixed/smaller results are inconclusive.

### Slide 16 — M4 next step

- Reuse the M2 manifest, folds, probabilities, threshold, and labels exactly.
- Compute Patient-ID macro metrics and false-negative-rate distribution only.
- No retraining, new data, augmentation, backbone, loss, or threshold tuning.
- Report supported, unsupported, or inconclusive without a clinical claim.

## PPT-ready introduction

“This project studies how malaria-cell classification results should be read
when cells from the same source share visual conditions. We reproduce
Rajaraman et al.'s patient-level ResNet-50 baseline on the exact public NIH/NLM
cell release, then—without changing the model—pre-register one evaluation
change: reporting errors by the official Patient-ID mapping. The goal is not a
clinical claim or a higher score; it is to test whether pooled accuracy and
recall hide difficult source groups.”
