# M2/M3 project specification

- **Topic:** Patient-/slide-disjoint evaluation for malaria parasite classification.
- **Dataset:** NIH/NLM _NLM-Falciparum-Thin-Cell-Images_ (`cell_images.zip`), the 27,558 segmented thin-smear cell images named in the handout, Rajaraman summary, and M1 slides. Official Patient-ID-to-cell mapping CSVs are required for grouping.
- **Task:** Binary image classification: Parasitized (positive) versus Uninfected.
- **Base paper and method:** Rajaraman et al. (2018), _Pre-trained convolutional neural networks as feature extractors toward improved malaria parasite detection in thin blood smear images_ (PeerJ 6:e4568). Reproduce the reported ResNet-50 ImageNet-pretrained feature-extractor pipeline with a fully connected classifier and dropout, under patient-level five-fold CV.
- **Paper1 protocol/metrics:** Reported: NIH/NLM data; 27,558 balanced cells; patient-level five-fold CV; mean-normalized inputs resized to a model-compatible size; ResNet-50 feature extraction; accuracy, sensitivity, specificity, AUC (and F1 where practical). Paper1 also reports a separate cell-level comparison. Reported patient-level proposed-model baseline: accuracy 0.959, sensitivity 0.947, specificity 0.972, AUC 0.991 (Table 6, per `papers/paper1_rajaraman.md`). Exact fold membership and several implementation hyperparameters are not specified in the supplied project source.
- **M1 gap:** Random cell-level splits can leak slide/patient appearance. M1 does **not** claim that leakage causes a catastrophic mean-accuracy drop; it identifies unreported per-slide error variation and sensitivity/specificity behavior under leakage-free evaluation as the open question.
- **Direction previewed in `presentation/M1/SLIDES.md`:** Hold the Rajaraman ResNet-50 baseline and patient/slide-disjoint folds fixed; in M4, add only an evaluation analysis of per-slide errors and sensitivity versus specificity. M4 must not begin in this work.
- **Handout constraints:** Reproduce a base paper near its reported result; submit one falsifiable predicted change before coding that change; report sensitivity/recall and AUC rather than accuracy alone; make no clinical claims; include limitations.

## Scope status at start

- **Done before this run:** M1 literature survey, base-paper selection, project narrative, and M1 slides.
- **Missing at start:** Exact official data archive and Patient-ID mapping files; dataset audit; reproducible baseline code/notebook; measured baseline results; M3 hypothesis/prediction/introduction materials.
- **Conflicts to resolve in audit:** M1/paper1 describe 150 infected plus 50 healthy patients (200 total), while the current official datasheet distinguishes the source thin-smear collection and describes mapping CSV entry counts. The audit will use the official mapping files for actual grouping and will not equate filename groups with the paper's unpublished fold assignments.
