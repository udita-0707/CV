# Viva preparation — M4/M5

25 likely questions. Each answer is at most three sentences, and every number
is rendered from `results/`.

## The one change

### 1. What exactly did you change in M4?
Only the aggregation: we summarised the frozen M2 out-of-fold predictions per official Patient-ID within each fold, next to the pooled cell-weighted metrics. The model, features, probabilities, 0.5 threshold, labels and folds are byte-for-byte the M2 artifacts. It is an evaluation/reporting change, not a model improvement.

### 2. Why does this count as one change and not several?
There is one manipulated factor, the weighting of cells into a fold-level sensitivity, and one pre-registered primary metric. The secondary metrics and the five ablations re-read the same rows; they add no model, data or training change. A1 confirms it: re-weighting per-ID sensitivity by cell count gives back the pooled value exactly.

### 3. Why no retraining?
Retraining would change the predictions, so any difference could come from the new model rather than from the aggregation we were testing. Freezing the M2 outputs makes the comparison paired and unconfounded, and it is what M3 pre-registered. It also means the pooled M2 numbers stay exactly as reported.

### 4. How do you know the M2 artifacts were not altered?
Before any computation the code asserts {{n_rows}} rows, unique paths, folds/labels/IDs identical to `fold_assignments.csv`, no ID in two folds, and `prediction == (p >= 0.5)`. It also recomputes pooled per-fold metrics with the M2 metric function and requires them to match `fold_results.csv` (largest difference {{reuse_max_abs}}). Input SHA-256 hashes are checked before and after the run.

## Prediction and verdict

### 5. What did you predict, and when?
That Patient-ID-macro sensitivity would be lower than pooled sensitivity by about 1–3 pp, with a rule: supported if ≥ 4 of 5 folds are negative and the mean ≤ −1.68 pp. It was recorded on 3 October 2026, after M2 and before any M4 code. Git shows the file first committed in `{{prereg_commit}}` ({{prereg_commit_date}}).

### 6. What happened?
{{n_negative_folds}} of {{n_folds}} folds were negative and the mean was {{mean_diff_pp}}, inside the predicted range. That misses the −1.68 pp threshold by {{shortfall_pp}}, so the pre-registered verdict is **{{verdict}}**. The threshold's exact source value ({{threshold_exact_pp}} pp) gives the same verdict.

### 7. What does INCONCLUSIVE mean here?
The data neither met the support rule nor the opposite rule. The direction mostly agreed with us, but not by the margin we committed to in advance. It is not evidence that the hypothesis is false, and not evidence that it is true.

### 8. Why 1.68 pp?
It is half of M2's measured sensitivity fold SD ({{m2_sens_sd}}), chosen before M4 so that a "real" effect had to be large relative to fold-to-fold noise. It is a pre-registered convention, not a literature-derived effect size. We applied it exactly as written.

### 9. Your bootstrap CI excludes zero. Isn't the effect significant?
The cluster-bootstrap CI for the mean ({{boot_ci}}) only describes resampling Patient-IDs inside fixed folds; it ignores training variance and fold assignment. It is also exploratory, and the across-fold t-interval ({{t_ci}}) includes zero. We make no significance claim.

### 10. Why can't five folds show significance?
With five paired differences, the smallest two-sided exact Wilcoxon p-value is 2/2⁵ = {{min_wilcoxon_p}}, so p < 0.05 is impossible whatever the data. A one-sided test could reach {{min_wilcoxon_p_one_sided}}, but no test was pre-registered, and choosing one after seeing the data would be post hoc. So we report effect sizes and intervals.

## Macro vs pooled

### 11. What is the difference between macro and pooled sensitivity?
Pooled divides all true positives by all Parasitized cells in the fold, so each **cell** counts once. Macro averages each Patient-ID's own sensitivity, so each **ID** counts once. Pooled describes cells; macro describes the typical source group.

### 12. Why was fold {{positive_fold}} positive?
In that fold several large Patient-IDs are hard: its top ID, {{posfold_top_fn_id}}, has {{posfold_top_fn_npos}} Parasitized cells and holds {{posfold_top_fn_share}} of the fold's false negatives. Cell weighting gives those IDs a large weight, so pooled sensitivity falls *below* the macro. The same mechanism we predicted, unequal cell counts, simply runs the other way when big IDs are hard rather than easy.

### 13. Why does specificity hardly move?
Every Patient-ID contributes almost the same number of Uninfected cells ({{nneg_min}}–{{nneg_max}}), so macro and cell-weighted specificity nearly coincide (mean difference {{a5_spec_mean}}). Parasitized cells range from {{npos_min}} to {{npos_max}} per ID, which is where weighting matters. AUC is unchanged by construction because the scores are fixed.

### 14. What do the ablations add?
A1 shows the gap is purely the weighting. A2 and A3 show the result is fragile: with ≥ 10 cells per ID the mean is {{a2_k10_mean}}, and deleting one ID ({{a3_flip_ids}}) can flip the verdict. They are exploratory, written down before computing, and do not replace the pre-registered verdict.

### 15. Why not just report the ≥ 10-cell version, which passes the threshold?
Because that choice was made after seeing the data; adopting the most favourable variant would be outcome-driven analysis. M3 fixed "≥ 1 Parasitized cell" as the primary eligibility rule. The ≥ 25 variant ({{a2_k25_mean}}) goes the other way, which shows how sensitive the number is.

## Patient-ID and data

### 16. Is a Patient-ID a slide or a patient?
Neither exactly: it is the official key in NLM's Patient-ID-to-cell mapping files, used verbatim and never parsed from filenames. Uninfected crops also come from infected patients' slides, and one source patient has two microscope-specific keys, which gives {{n_ids}} keys. We never call it a slide ID or a diagnosis.

### 17. Why {{n_ids}} IDs when the paper says 150 + 50 patients?
The released mapping files have {{map_entries_par}} Parasitized and {{map_entries_uninf}} Uninfected entries, and the official datasheet explains both counts. We group by the official keys and do not reconstruct the paper's unpublished folds. {{n_ids_pos}} keys have Parasitized cells; {{n_ids_negonly}} have only Uninfected cells.

### 18. Did you use any other data?
No. For M5 we re-fetched only NLM's official archive; it and both mapping files match the SHA-256 values recorded in M2. All {{images_verified}} local PNGs match their manifest hashes.

## Failure analysis

### 19. Where do the errors concentrate?
False negatives are concentrated: the top 10 Patient-IDs hold {{fn_top10_share}} of {{fn_total}}, and {{fn_ids_50}} IDs hold half. False positives are more diffuse ({{fp_top10_share}} in the top 10). In the largest-SD fold, no single ID drives the spread; the most influential one removes {{sd_reduction_share}} of the SD.

### 20. Who labelled the images, and how?
One reviewer labelled {{rev_total}} crops: the AI assistant that ran this analysis, not a microscopist. The crops were shown blind (no class, probability or ID) in shuffled numbered grids, with categories fixed in a protocol written before viewing. Counts were computed by code from the saved labels, with no adjudication or second rater.

### 21. So is the dataset mislabelled?
We cannot say. {{rev_tfn_inclusion_no}}/24 of the most confident false negatives showed no visible inclusion, and {{rev_tfp_inclusion_yes}}/24 of the most confident false positives showed one. That is consistent with label noise, but equally with faint parasites, border debris or reviewer error.

### 22. Is the model well calibrated?
Reasonably: Brier {{brier}}, ECE {{ece}}, with {{cal_extreme_share}} of cells in the two extreme bins. Mid-range bins over-estimate the Parasitized probability by up to {{cal_max_gap}}, and {{conf_fn_share}} of false negatives have p < 0.1. We did not recalibrate, because that would be a second intervention.

## Scope

### 23. What are the main limitations?
n = 5 folds from one grouping seed, and a verdict near the threshold that single IDs can flip. Patient-ID is a mapping key, not a slide; M2 is an approximate reproduction (specificity {{delta_spec}} vs published); and the image review uses one non-expert. It is one public segmented-cell dataset.

### 24. Does this say anything clinical?
No. It is about how a public segmented-cell benchmark is summarised, not about diagnosing patients, prevalence, workflow or deployment. Even "Patient-ID" here is a dataset key, not a patient-level diagnosis.

### 25. What would you do next?
Repeat the grouped split over several seeds, have a microscopist re-review the confident errors with inter-rater agreement, and study the grey/blue-tinged crops. Each would be a new, separately pre-registered intervention. Regardless, we would always report pooled and per-Patient-ID sensitivity side by side.
