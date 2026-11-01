# CSA431 — M4/M5 defence: PPT-ready bullets
NIH/NLM malaria cell classification | Patient-ID–stratified re-evaluation | 12 slides

Every number below is rendered from `results/` by `python -m src.render_reports`.
Figures are under `results/m4/figures/` and `results/m5/figures/`; the paper is
`paper/main.pdf`.

---

## SLIDE 1 — Title
- Does cell-weighted sensitivity hide hard Patient-IDs?
- A pre-registered Patient-ID–stratified re-evaluation of a ResNet-50 malaria cell classifier
- NIH/NLM segmented thin-smear cells ({{n_rows}} crops) | base paper: Rajaraman et al. 2018 (PeerJ 6:e4568)
- CSA431 Computer Vision | M4 implementation + ablations · M5 failure analysis, IEEE paper, defence
- Team: [names]

## SLIDE 2 — Problem
- Papers on this dataset headline pooled, cell-weighted accuracy (often 96–99%)
- Cells are not independent: cells from one source share stain, light and focus
- Rajaraman already split by patient: {{pub_cell_acc}} cell-level → {{pub_acc}} patient-level accuracy
- Open question from M1: under a leakage-free split, does a pooled mean hide source groups with concentrated false negatives?
- Rules we follow: predict before experimenting; report sensitivity + AUC; no clinical claims

## SLIDE 3 — Reproduction recap (M2)
{{table:reproduction}}

- Frozen ImageNet ResNet-50 features → 2048→512→1 FC, dropout 0.5; 5 folds grouped by the official NLM Patient-ID key ({{n_ids}} IDs; zero overlap)
- Close on sensitivity; lower on accuracy and specificity → an approximate reproduction (paper folds, layer and search not published in our source)
- Figures: `results/baseline/figures/baseline_roc_curve.png`, `baseline_confusion_matrix.png`

## SLIDE 4 — Hypothesis and prediction (recorded 3 Oct 2026, before any M4 code)
- **IF** the frozen M2 predictions are summarised per Patient-ID within each fold, **THEN** Patient-ID-macro sensitivity < pooled sensitivity, **BECAUSE** groups share appearance and contribute very unequal cell counts
- Predicted mean macro − pooled: about −1 to −3 pp
- Rule: SUPPORTED if ≥ 4/5 folds negative **and** mean ≤ −1.68 pp (half the M2 sensitivity fold SD, {{m2_sens_sd}}); UNSUPPORTED = mirror; else INCONCLUSIVE
- Proof of timing: `milestones/M3/hypothesis.md` first committed in `{{prereg_commit}}` ({{prereg_commit_date}}), after the M2 metrics were written

## SLIDE 5 — Method: the one change
- Same model, features, probabilities, 0.5 threshold, labels, folds: **only the aggregation changes**
- Pooled = Σ TP / Σ (TP + FN) over the fold's cells; macro = mean of per-ID sensitivity over IDs with ≥ 1 Parasitized cell
- {{n_ids_pos}} IDs have Parasitized cells; {{n_ids_negonly}} have none and are counted, not dropped
- Reuse assertions first: {{n_rows}} rows, folds identical, no ID in two folds, pooled metrics recomputed to within {{reuse_max_abs}}
- No significance test: with n = 5 pairs, the smallest two-sided exact Wilcoxon p is {{min_wilcoxon_p}}; we report effect sizes + CIs

## SLIDE 6 — Primary result vs prediction
{{table:primary}}

- Predicted: negative, −1 to −3 pp → Observed: {{n_negative_folds}}/{{n_folds}} folds negative, mean {{mean_diff_pp}} ({{within_band}} the predicted range)
- Threshold −1.68 pp **not met** (short by {{shortfall_pp}}) → **{{verdict}}**
- Cluster-bootstrap 95% CI {{boot_ci}}; across-fold t-interval {{t_ci}}
- Figure: `results/m4/figures/paired_differences.png` + `per_id_sensitivity_by_fold.png`

## SLIDE 7 — Ablations (exploratory; the verdict does not change)
{{table:ablations}}

- A1: weighting each ID by its cell count gives back the pooled value exactly → the gap is purely the weighting
- A2/A3: an eligibility tweak or deleting one ID ({{a3_flip_ids}}) can flip the verdict → **fragile**; we keep the pre-registered verdict
- A5: specificity cannot move: every ID has {{nneg_min}}–{{nneg_max}} Uninfected cells, but {{npos_min}}–{{npos_max}} Parasitized

## SLIDE 8 — Failure analysis (1/2): where the errors are
- {{fn_total}} false negatives; top Patient-ID ({{fn_top1_id}}) holds {{fn_top1_share}}; top 10 hold {{fn_top10_share}}; {{fn_ids_50}} IDs hold half
- False positives are more diffuse: top 10 hold {{fp_top10_share}}; {{fp_ids_50}} IDs needed for half
- Fold {{positive_fold}} (the positive fold): {{posfold_fn}} FN, {{fn_top10_in_posfold}} of the 10 worst IDs; its top ID holds {{posfold_top_fn_share}} → large **hard** IDs pull pooled *below* macro
- Confident errors: {{conf_fn}} FN with p < 0.1 ({{conf_fn_share}}), {{conf_fp}} FP with p > 0.9 ({{conf_fp_share}}); Brier {{brier}}, ECE {{ece}}
- Figures: `results/m5/figures/error_concentration.png`, `reliability_diagram.png`

## SLIDE 9 — Failure analysis (2/2): what the worst cells look like
{{table:image_review}}

- Blind review of {{rev_total}} crops by one **non-expert** reviewer (the AI assistant), categories fixed before viewing; official, hash-verified images only
- {{rev_tfn_inclusion_no}}/24 most-confident FN show **no** visible inclusion; {{rev_tfp_inclusion_yes}}/24 most-confident FP **do**
- Observation, not cause: consistent with label noise (cf. Wilm et al. 2025), faint parasites, border debris, or reviewer error
- Figure: `results/m5/figures/grid_top_false_negatives.png`, `grid_top_false_positives.png`, `grid_worst_patient_ids.png`

## SLIDE 10 — Limitations
- n = 5 folds from one grouping seed → no significance; fold signs could change with a different grouping
- Verdict is near the threshold and fragile to single IDs; exploratory variants are not adopted
- Patient-ID is the official mapping key, not a slide or a diagnosis; one source patient has two keys
- Approximate reproduction (specificity {{delta_spec}} vs published); failure modes describe this model
- Image review: one non-expert reviewer, small crops, confidence-selected errors
- One public segmented-cell dataset; **no clinical claim**

## SLIDE 11 — What we would do next (each is a separate, new intervention)
- Repeat the grouped split with several seeds to see how often the sign flips
- Expert (microscopist) re-review of the confident errors, with inter-rater agreement
- Stain/acquisition-aware analysis of grey/blue-tinged crops
- Recalibration only as its own pre-registered change
- Always report pooled **and** per-Patient-ID sensitivity with the group distribution

## SLIDE 12 — Conclusion
- Reproduced Rajaraman's patient-level ResNet-50 baseline approximately: sensitivity {{m2_sens_mean}}, AUC {{m2_auc_mean}}
- Pre-registered one evaluation change; outcome **{{verdict}}**: right direction in {{n_negative_folds}}/{{n_folds}} folds and inside the predicted range, but short of the threshold
- Main lesson: whether cell weighting hides or exaggerates hard groups depends on which groups are large
- Errors concentrate in few Patient-IDs; the most confident errors may be label questions
- Public dataset research; no clinical claims
