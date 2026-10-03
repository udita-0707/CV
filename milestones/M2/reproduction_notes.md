# Rajaraman et al. (2018) baseline — reproduction notes

## Evidence boundary

The base-paper facts below come only from `../../papers/paper1_rajaraman.md`, with
M1 terminology checked against `../../presentation/M1/SLIDES.md` and
`../../literature/synthesis.md`. The supplied
paper1 file is a faithful project summary rather than the paper PDF/table
appendix, so a detail absent from that file is marked **not specified in the
supplied project source** rather than reconstructed from memory. Dataset facts
are verified against the official NLM archive, datasheet, and official mapping
files downloaded to `data/raw/`.

## Paper-to-pipeline extraction

| Method detail                          | Status                                                                         | Paper1 / project evidence                                                               | M2 implementation or implication                                                                                                                                             |
| -------------------------------------- | ------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Dataset                                | **reported**                                                                   | NIH/NLM thin-smear segmented cells                                                      | Exact NLM `cell_images.zip`, source/hash in `results/baseline/dataset_source.json`                                                                                           |
| Image count and balance                | **reported**                                                                   | 27,558 total; 13,779 per class                                                          | Audit must equal those counts before training                                                                                                                                |
| Classes / positive label               | **reported**                                                                   | Parasitized and Uninfected                                                              | Binary label: Parasitized=1, Uninfected=0                                                                                                                                    |
| Patient structure                      | **reported**                                                                   | 150 infected + 50 healthy patients                                                      | Use only the official mapping CSV for actual groups; never infer/assign patients                                                                                             |
| Patient↔cell mapping                   | **not specified in paper1 summary**                                            | M1 says filenames can be grouped; NLM datasheet supplies official mapping files         | Exact NLM mapping keys are used, verified sample-by-sample                                                                                                                   |
| Main split                             | **reported**                                                                   | patient-level 5-fold CV; preserves patient separation to prevent stain/artifact leakage | Deterministic 5-fold `StratifiedGroupKFold` with official Patient-ID groups and a zero-overlap assertion                                                                     |
| Exact fold membership / Table 1 counts | **not specified in supplied project source**                                   | M1 says Table 1 lists counts, but not the members/counts                                | New deterministic folds (seed 42); saved for M4; not claimed as paper-exact                                                                                                  |
| Cell-level protocol                    | **reported**                                                                   | Table 6 has a separate cell-level comparison                                            | Not run: M2 reproduces the main patient-level protocol only                                                                                                                  |
| Resize / preprocessing                 | **reported**                                                                   | model-compatible sizes 100/224/227/299 and mean-normalization                           | ResNet-50 uses 224×224; ImageNet mean/std normalization is an approximation for the ambiguous "mean-normalize" wording                                                       |
| Augmentation                           | **not specified in supplied project source**                                   | no augmentation recipe is reported in paper1 summary                                    | None; no new images or transforms beyond resize/normalization                                                                                                                |
| Architecture                           | **reported**                                                                   | pre-trained ResNet-50 among several feature extractors                                  | ImageNet-pretrained torchvision ResNet-50, frozen during feature extraction                                                                                                  |
| Pretrained weights release             | **not specified in supplied project source**                                   | paper1 calls CNNs "pre-trained"                                                         | Official torchvision `ResNet50_Weights.IMAGENET1K_V2`; recorded as an approximation/versioned dependency                                                                     |
| Feature-extraction layer               | **reported as an optimal layer, exact layer not specified in supplied source** | paper1 summary says optimal-layer results and feature extraction                        | ResNet-50 final convolutional output with global average pooling (2,048 features); approximation                                                                             |
| Classifier                             | **reported**                                                                   | fully connected classifier + dropout 0.5                                                | FC 2048→512→1, ReLU, dropout=0.5; 512 width is an approximation                                                                                                              |
| Training search                        | **reported**                                                                   | randomized grid search for learning rate / SGD / L2                                     | No grid is recreated because ranges/selection rule are unavailable; fixed SGD learning rate 0.01, momentum 0.9, L2=1e-4, 20 epochs, seed 42—approximations, never test-tuned |
| Batch size / seed / interpolation      | **not specified in supplied project source**                                   | absent                                                                                  | batch 32 feature extraction, 128 classifier, seed 42, bilinear resize; logged approximations                                                                                 |
| Core metrics                           | **reported**                                                                   | accuracy, sensitivity, specificity, AUC                                                 | All four measured, with Parasitized as positive; F1 additionally measured per course rule/practical reporting                                                                |
| Published patient-level baseline       | **reported**                                                                   | Table 6 proposed model: acc .959, sensitivity .947, specificity .972, AUC .991          | Kept only in `results/baseline/published_baseline.csv`                                                                                                                       |
| Published cell-level baseline          | **reported**                                                                   | Table 6 proposed model: acc .986, sensitivity .981, specificity .992, AUC .999          | Kept only in `results/baseline/published_baseline.csv`; not combined with measured rows                                                                                      |

## Dataset verification and patient grouping

The NLM datasheet names this exact single-cell release
`NLM-Falciparum-Thin-Cell-Images` and provides both Patient-ID-to-cell mapping
CSVs. The archive is retained locally at `data/raw/cell_images.zip`; the source
URLs, retrieval record, and SHA-256 hashes are in `results/baseline/dataset_source.json`.
The audit reads the official mapping lists, verifies every PNG and mapping
reference, and writes the manifest, patient/cell summary, exception tables, and
audit status under `results/baseline/`.

**Grouping decision:** `patient_id` is exactly the official mapping key. No ID
is randomly assigned and no ID is parsed from a filename for splitting. The
official datasheet notes 151 Parasitized mapping entries (the C47P8 source has
two microscope models) and 201 Uninfected entries (normal cells from infected
slides also occur in that class). This explains why mapping-entry counts are
not a simple restatement of the M1 150+50 source-patient description.

## Deviations and approximations

| Paper spec → our implementation                                                                   | Reason                                                                                                        | Expected effect / risk                                                                             |
| ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------- |
| Patient-level 5-fold CV → official-mapping `StratifiedGroupKFold`, seed 42                        | Paper fold membership is not in the supplied source; the official mapping is available                        | Fold composition differs; values need not exactly match Table 6. No patient leaks across any fold. |
| reported ResNet-50 optimal feature layer → final convolutional global-average-pooled 2,048-vector | Exact selected layer absent from supplied paper1 source                                                       | Changes representation and can move all metrics.                                                   |
| reported mean-normalization → ImageNet mean/std after 224×224 bilinear resize                     | Exact normalization parameters/interpolation absent; ImageNet pretrained ResNet needs a documented convention | Distribution mismatch from original implementation is possible.                                    |
| FC + dropout .5 → 2048→512→1 FC, ReLU, dropout .5                                                 | Hidden width/activation absent                                                                                | Classifier capacity differs.                                                                       |
| randomized LR/SGD/L2 search → fixed SGD (lr .01, momentum .9, L2 1e-4), 20 epochs                 | Search space/validation selection absent; fixed settings avoid implicit test tuning                           | May under- or overfit relative to paper.                                                           |
| paper calls CNN pre-trained → torchvision ImageNet weights V2                                     | Exact original release/framework absent                                                                       | Weight/preprocessing revision can change results.                                                  |
| unspecified augmentation → none                                                                   | No supported recipe; no extra data permitted                                                                  | Faithful conservative choice; results may differ if original used undisclosed augmentation.        |

## Recorded conflict

**M1/paper1 versus official current datasheet:** M1 reports 150 infected + 50
healthy source patients and describes approximately 200 slides. The official
mapping files for this exact cell release contain 151 Parasitized and 201
Uninfected mapping entries, with an official explanation for both counts. We
follow the official mapping for splitting and report its observed counts. We do
not claim that these mapping keys reproduce paper1's unpublished fold IDs, and
we do not replace the M1 narrative with a different dataset census.

## Run record

The M2 command is `PYTHONPATH=. .venv/bin/python -m src.run_baseline`.
It first reruns the audit; a failed audit raises an error before model work.
Run logs, environment, fold assignments, per-sample predictions, measured
tables, and figures are all written under `data/`, `results/baseline/`, and `logs/`.
