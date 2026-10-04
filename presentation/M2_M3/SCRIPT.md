# Word-for-word script

PPT: M2 baseline + M3 prediction · 12 slides · ~12 minutes

**A = Udita (230082), slides 1–6** · **B = Aman Kumar (230064), slides 7–12**

One handoff, after the folds. Do not print a university, a logo, or a talk date: the repository does not contain them. The date that is real is the prediction lock, 3 October 2026, spoken on slide 10.

How to use this:

- Bold **SAY THIS** is the talk. Read it out loud.
- **If they stop you** is also word-for-word. Say it only if someone interrupts or asks.
- Every number below is in `results/baseline/` or in the M3 documents. Do not add a number that is not here.

---

# SLIDE 1 · Title · Speaker A · [0:00–0:35]

**SAY THIS**

Good morning. This is our CSA431 update for milestones two and three.

The topic is patient-level evaluation of malaria parasite classification.

Milestone two is an approximate reproduction of Rajaraman and colleagues, 2018, PeerJ. Milestone three is one evaluation change. We wrote the prediction before coding that change.

The dataset is the NIH NLM thin-smear cell images. Twenty-seven thousand five hundred fifty-eight cells.

I am Udita, enrollment 230082. This is Aman Kumar, enrollment 230064.

**If they stop you**

If they ask what the task is: Each image is one segmented red blood cell. The label is Parasitized or Uninfected. Parasitized is the positive class.

If they ask whether M4 is done: No. M4 has not been coded. This talk stops at the saved prediction.

---

# SLIDE 2 · What this talk covers · Speaker A · [0:35–1:25]

**SAY THIS**

Four lines, in order.

In M1 we already settled two things. Leakage from a random cell split is real. And that leak does not wreck mean accuracy. Rajaraman’s own drop was 98.6 to 95.9. MalariaNet’s drop was about one and a half points.

M2 is done. We trained the patient-grouped ResNet-50 baseline on the official NLM release and saved every fold, probability, and metric.

M3 is done. On 3 October 2026 we saved the hypothesis and the decision rule. That file is a prediction. It is not a result.

M4 has not started. When it starts, it only re-aggregates those saved predictions by Patient-ID.

The bar for this stage is a verified protocol and an honest comparison with the paper. A higher score is not the goal.

**If they stop you**

If they ask what M1 concluded in one sentence: Random splits inflate the number a little. The leftover question is whether a pooled mean hides hard source groups, especially in sensitivity.

If they ask why predict before coding: The handout requires the prediction first. A wrong prediction is still a result if we report it under the rule we wrote.

---

# SLIDE 3 · The claim · Speaker A · [1:25–2:25]

**SAY THIS**

The task is binary. One cell in. Parasitized or Uninfected out.

Cells from the same source are not independent. They share stain, lighting, and focus. That is why the base paper evaluates at the patient level.

The new point is about the average, not about the split. A pooled sensitivity weights each cell equally. A mapping group with hundreds of cells can carry that average. A mapping group with one or two cells cannot.

So the question we locked is this. Under leakage-free folds, if we average sensitivity once per Patient-ID instead of once per cell, does that macro number sit below the pooled number?

Nothing in the model changes to answer it. Same predictions. Different way of reading them.

**If they stop you**

If they ask why sensitivity and not accuracy: A missed parasite is a false negative. Sensitivity is recall on Parasitized. The set is balanced, so accuracy can stay high while false negatives move. Our own folds already show a larger sensitivity spread than accuracy spread. That is slide 8.

If they say Rajaraman already did this: They compared cell-level and patient-level means. They did not publish a Patient-ID macro against the pooled mean. That comparison is the one change.

If they say MalariaNet already did this: MalariaNet showed the mean drop is small, and that slide-disjoint sensitivity and specificity can differ. Their headline is still a mean. We are not retraining their network.

---

# SLIDE 4 · What M2 reproduced · Speaker A · [2:25–3:45]

**SAY THIS**

What we actually ran.

The backbone is ResNet-50 with torchvision ImageNet weights, version V2. It is frozen. The last layer is removed, so each cell becomes a 2,048-dimensional vector. That is global average pooling on the final convolutional map.

On top of those frozen features we train a small classifier. Two thousand forty-eight to 512, ReLU, dropout 0.5, then one output. Dropout 0.5 is what the paper states. The width 512 is our approximation. The paper does not give the hidden width in the source we have.

Images are resized to 224 by 224 with bilinear interpolation and normalized with ImageNet mean and standard deviation. There is no augmentation.

Each fold gets a new classifier. Optimizer is SGD. Learning rate 0.01, momentum 0.9, weight decay 1e-4, 20 epochs, seed 42. Loss is binary cross-entropy with logits. The threshold is 0.5. Test cells are never used to pick a setting.

The paper did a randomized search over learning rate, SGD, and L2. We did not recreate that search. The ranges are not in our source, and searching on the test fold would be tuning. Every stand-in is written in the reproduction notes.

**If they stop you**

If they ask why frozen features and not full fine-tuning: That is the paper’s method. Pretrained CNNs as feature extractors, then a fully connected classifier. We did not switch to end-to-end training.

If they ask why this layer: The summary says they picked an optimal layer. It does not name the layer. We used the standard 2,048-vector and marked it as an approximation.

If they ask why ImageNet mean and standard deviation: The summary says mean-normalize. It does not give the constants. ImageNet normalization is the documented match for these weights.

If they ask the batch size: Feature extraction uses batch 32. The classifier uses batch 128. Neither number is in the paper summary.

If they ask whether we ran the other backbones: No. The paper also tried AlexNet, VGG-16, Xception, DenseNet-121, and a small custom CNN. Table 6’s proposed model, in our project source, is the ResNet-50 line. We reproduced that line only.

---

# SLIDE 5 · Dataset audit · Speaker A · [3:45–5:15]

**SAY THIS**

The audit passed before any training. The archive is the official NLM file `cell_images.zip`. Twenty-seven thousand five hundred fifty-eight PNGs. Thirteen thousand seven hundred seventy-nine Parasitized. Thirteen thousand seven hundred seventy-nine Uninfected.

Zero corrupt images. Zero cells without a mapping ID. Zero mapping rows that point at a missing file. Zero byte-identical duplicates across the two labels.

The split key is the Patient-ID in the official mapping CSVs. We did not invent IDs, and we did not parse them out of filenames for the split. There are 201 unique keys.

Here is the fact that drives the hypothesis. One hundred fifty-one of those keys contain parasitized cells. Counts run from 1 cell to 633 cells. The median is 33. Fifty keys have uninfected cells only, so they cannot enter a sensitivity average.

Five keys alone hold 2,933 of the 13,779 parasitized cells. That is about 21 percent. Uninfected counts do not look like that. They sit between 63 and 77 cells per key.

So a cell-weighted sensitivity mostly hears the large infected groups. A macro sensitivity gives the one-cell group the same vote as the 633-cell group. That is the mechanism. It is a property of the counts. It is not yet a measured result.

The figure on this slide is `presentation/M2_M3/figures/patient_id_parasitized_counts.png`. It ranks the 151 IDs that have at least one parasitized cell. The five dark bars on the left are the IDs that hold 2,933 cells. The dashed line is the median, 33. The 50 uninfected-only IDs are omitted because their parasitized count is zero.

One conflict, said once. The paper describes 150 infected patients plus 50 healthy patients. The current datasheet has 151 parasitized mapping entries, because one source was shot on two microscopes, and 201 uninfected entries, because normal cells from infected slides are also in the Uninfected class. We split on the 201 official keys. We do not say those keys are the paper’s unpublished fold list.

**If they stop you**

If they ask for the hash: The archive SHA-256 is `0a949556b2414159b5100192609805376654c4266d8d187be9b1922fad43c668`. It is in `dataset_source.json`.

If they ask which five IDs: C68P29N_ThinF has 633 parasitized cells. Then C39P4thinF_original, 616. C132P93ThinF, 574. C99P60ThinF, 564. C182P143NThinF, 546. Sum 2,933.

If they ask about a one-cell ID: C150P111ThinF and C58P19thinF each have one parasitized cell. One false negative there is zero sensitivity for that ID, and one cell out of 13,779 in the pooled rate.

If they ask why uninfected is so flat: That is what the mapping summary shows. Every one of the 201 IDs has between 63 and 77 uninfected cells. The skew is in the parasitized class. That is why sensitivity, not specificity, is the primary metric.

If they ask “is 201 the same as 200 slides?”: No. Do not merge them. M1’s “about 200 slides” was MalariaNet’s filename grouping. Rajaraman’s 200 was 150 plus 50 patients. Our 201 is the count of official mapping keys on this release.

---

# SLIDE 6 · Folds · Speaker A · [5:15–6:10]

**SAY THIS**

The folds are a stratified group split. Five folds. Seed 42. A Patient-ID never sits in train and test of the same fold. The code asserts that overlap is zero.

Test set sizes are 5,497, 5,520, 5,544, 5,483, and 5,514 cells. Test ID counts are 40, 40, 41, 40, and 40. Train ID counts are 161, 161, 160, 161, and 161.

Class counts stay near half and half inside every test fold. That is the stratified part. The group part is what blocks leakage.

These are our folds. Rajaraman’s Table 1 lists counts, not the member IDs, in the source we have. We do not call our folds a reconstruction of theirs.

We also did not rerun their cell-level column. M2 is the patient-level protocol only.

**If they stop you**

If they ask what StratifiedGroupKFold does: It keeps every Patient-ID inside one side of the split, and it tries to keep the Parasitized fraction similar across folds. Shuffle is fixed by seed 42.

If they ask the test positive counts: 2,752, 2,772, 2,734, 2,745, and 2,776 parasitized cells. The rest of each test fold is uninfected.

If they ask whether 40 IDs means 40 patients in the paper’s sense: It means 40 official mapping keys. Some of those keys have no parasitized cells. We have not yet counted, fold by fold, how many keys are eligible for sensitivity. That count is part of M4. Do not guess it.

---

# SLIDE 7 · Measured baseline · Speaker B · [6:10–7:20]

**SAY THIS**

These are the means of the five test folds. Not a clinical number.

Accuracy 93.90 percent, standard deviation 1.95 points.
Sensitivity 94.24 percent, standard deviation 3.36 points.
Specificity 93.56 percent, standard deviation 1.30 points.
AUC 0.9832, standard deviation 0.0086.
F1 93.90 percent, standard deviation 2.03 points.

The positive class is Parasitized. The threshold is 0.5. The standard deviation is across folds, in percentage points for the rate metrics.

If we stack every out-of-fold cell once, the confusion counts are 12,984 true positives, 795 false negatives, 12,892 true negatives, and 887 false positives. Those four numbers add to 27,558. I recomputed them from `per_sample_predictions.csv`. They match the figure saved by the M2 run.

Show two figures. The ROC is `presentation/M2_M3/figures/baseline_roc_oof.png`. It is every out-of-fold score together. Its AUC is 0.983. The 0.9832 in the table is the mean of the five separate fold AUCs. Same to three decimals. The confusion matrix is `presentation/M2_M3/figures/baseline_confusion_oof.png`. Use that file. The run also wrote a viridis matrix at `results/baseline/figures/baseline_confusion_matrix.png` with the same four counts, and the digits there are hard to read. Do not swap in a matrix built by hand.

Read the standard deviations before the means. Sensitivity moves almost twice as much as accuracy, on the same folds, with the same model. That is the bridge into the hypothesis. The table does not yet say which Patient-IDs caused it.

**If they stop you**

If they ask why the mean and the stacked counts are not identical: The slide mean is an unweighted mean of five fold rates. The counts are all cells pooled. They are close. We quote the fold mean because that is what `baseline_results.csv` stores. For sensitivity the fold mean is 94.24 percent. The stacked rate is 12,984 divided by 13,779, which is 94.23 percent.

If they ask where AUC comes from: ROC AUC on the predicted probability, not on the 0.5 hard label. Each fold has its own AUC. 0.9832 is their mean.

If they want the figure caption: “Measured on the official Patient-ID-grouped M2 folds. Not a clinical-performance claim.” The plot files the code writes are `baseline_confusion_matrix.png` and `baseline_roc_curve.png`.

---

# SLIDE 8 · The mean hides one fold · Speaker B · [7:20–8:25]

**SAY THIS**

Look at sensitivity down the five folds. 95.31, 88.28, 96.38, 95.52, 95.71.

Four folds live between 95 and 96. Fold 2 is 88.28 percent. Its false-negative count is 325. The other folds have 129, 99, 123, and 119.

Fold 2 accuracy is 90.63. Its AUC is 0.968. Specificity on that fold is still 93.01, close to the other folds. The damage in fold 2 is false negatives, not false positives.

So the 3.36 point sensitivity standard deviation is mostly one fold, not five folds wandering at random. Accuracy’s 1.95 point spread is smaller for the same reason: fold 2 pulls it, and the other four accuracies sit between 93.69 and 95.57.

This is why a single mean is a weak headline. It is not yet the M3 result. Fold 2 contains 40 Patient-IDs. We have not opened those 40. M4 does that, inside every fold, without retraining.

**If they stop you**

If they ask whether fold 2 is a bug: The overlap check is zero. The class counts are balanced: 2,772 parasitized and 2,748 uninfected. Training loss on that fold is in the same range as the others. We do not have a reason to delete the fold. A hard test group is a result.

If they ask the exact fold-2 row: Accuracy 0.9063, sensitivity 0.8828, specificity 0.9301, AUC 0.9684, F1 0.9045, false negatives 325, true positives 2,447.

If they say “then you already know the hypothesis is true”: No. A hard fold is not the same object as a macro-versus-pooled gap inside a fold. Large easy groups inside a hard fold can still mask small hard groups, or the opposite can happen. We predicted the direction. We have not measured it.

---

# SLIDE 9 · Comparison with the paper · Speaker B · [8:25–9:35]

**SAY THIS**

Paper Table 6, patient level, proposed model, against our fold means.

Accuracy: they report 95.9 percent. We measure 93.90. Difference, minus 2.00 points.
Sensitivity: 94.7 versus 94.24. Minus 0.46 points.
Specificity: 97.2 versus 93.56. Minus 3.64 points.
AUC: 0.991 versus 0.9832. Minus 0.0078.

The reproduction is closest on sensitivity and furthest on specificity. We call it approximate. We do not call it a failed run, and we do not call it an exact rerun.

Why the gap is allowed. Their fold membership is not in our source. Their chosen feature layer is not named. Their mean-normalization constants are not given. Their classifier width is not given. Their randomized hyperparameter search cannot be repeated from the ranges we have. Our weights are a current torchvision ImageNet release, not their 2018 Keras weights.

We did not tune anything on the test fold to chase 95.9. Closing that gap after seeing it would break the reproduction.

**If they stop you**

If they ask what “near the paper” means for the course: A verified dataset, zero group overlap, the right metrics, and a written comparison. An exact score match is not required, because the missing details make an exact match unidentifiable.

If they ask which missing detail matters most: We cannot rank them from this run. Any of the layer, the folds, or the training search can move specificity. We list them. We do not pick a favorite excuse.

If they quote the cell-level 98.6: That is their other column. We did not measure a cell-level number, so we will not put our 93.9 next to their 98.6 and call the difference leakage. Our comparison column is patient-level to patient-level.

If they ask about their patient-level standard deviations: Table 4 in the paper, for ResNet-50 after layer selection, is accuracy 0.959 plus or minus 0.008 in our M1 notes. Our accuracy SD is larger, 1.95 points. Different folds. Say that if asked. It is not a second result.

---

# SLIDE 10 · Hypothesis · Speaker B · [9:35–10:45]

**SAY THIS**

This slide was written before any Patient-ID metric existed. Date in the file: 3 October 2026.

The sentence is if, then, because.

If we score the saved out-of-fold predictions separately for every official Patient-ID, inside the same five folds.

Then the unweighted mean of those Patient-ID sensitivities will be lower than the pooled cell sensitivity.

Because cells that share a mapping key share appearance, and the keys do not contribute equal numbers of cells. The pooled mean can hide a few keys with concentrated false negatives. Slide 5 is the count evidence: 1 cell versus 633, and five keys holding about 21 percent of the positive cells.

The predicted size is about minus 1 to minus 3 percentage points. We tied that band to our own sensitivity fold SD of 3.36 points. It is not a number we copied from a paper.

There is no second model. Weights, probabilities, and the 0.5 threshold stay fixed. If someone recomputes the pooled metrics, they must get the M2 table again.

**If they stop you**

If they ask why macro should be lower rather than higher: Macro gives equal weight to a one-cell ID and a 633-cell ID. A false negative on a tiny ID damages that ID’s sensitivity completely and barely moves the pooled rate. For the macro mean to fall, those small or otherwise hard IDs have to be worse than the large ones. That is the bet. If the hard cells actually sit in the large IDs, the gap can shrink or flip, and the rule on the next slide will say so.

If they ask why minus 1 to minus 3: The upper end is just inside the 3.36 point SD we already saw across folds. We did not want a prediction bigger than the variation the baseline itself contains. Half of 3.36 is 1.68, which is the cutoff on the next slide, not the prediction itself.

If they ask what happens to AUC: The scores do not change, so we do not predict an AUC change. AUC is not the primary test.

---

# SLIDE 11 · Decision rule · Speaker B · [10:45–11:35]

**SAY THIS**

One primary number. For each fold, take Patient-ID macro sensitivity minus that fold’s pooled sensitivity. Then average those five differences.

Macro sensitivity uses only IDs that contain at least one parasitized cell. An ID with none has an undefined sensitivity. We count those IDs and we do not drop them from the dataset.

Supported means two conditions together. At least four of the five differences are negative. And the mean difference is less than or equal to minus 1.68 points. 1.68 is half of the 3.36 point sensitivity SD from M2.

Unsupported is the mirror. At least four of five positive, and the mean at least plus 1.68.

Every other pattern is inconclusive. That includes a negative mean that is smaller than 1.68, and a split vote such as three folds down and two up.

Accuracy and specificity get the same style of difference, as secondary description. They do not get to overrule the sensitivity rule after we see them.

**If they stop you**

If they ask why four of five and not a p-value: Five pairs is the whole experiment. We pre-registered a sign count plus a magnitude tied to variation we had already measured. We did not add a significance test after the fact.

If they ask for an example of inconclusive: Mean difference minus 0.4 points, all five negative. Direction matches. Magnitude misses 1.68. The call is inconclusive, not supported.

If they ask what “macro” means in a formula: Inside one test fold, compute sensitivity for each eligible Patient-ID, then take the ordinary mean of those sensitivities. Do not weight that mean by cell count. The pooled number is the one already in the fold table, which is cell-weighted.

---

# SLIDE 12 · M4 and the limits · Speaker B · [11:35–12:20]

**SAY THIS**

M4, when it is run, does only this. It reads the saved manifest, the saved folds, the saved probabilities, and the same 0.5 threshold. It computes Patient-ID macro metrics and the spread of false-negative rates. Then it applies the rule on the previous slide and writes supported, unsupported, or inconclusive.

It does not retrain. It does not augment. It does not change the backbone, the loss, or the threshold. If a result is unsupported, we keep the pooled M2 table. We do not go back and edit the model.

Limits, as they stand. One public dataset. Plasmodium falciparum only. Thin-smear cells that are already segmented. The paper match is approximate. There is no second hospital. This is not a diagnostic claim and not a screening-device claim.

We can take questions.

**If they stop you**

If they ask what a failed prediction means: The masking story was not supported on these fixed folds. That is a finding. It is not permission to change the network after seeing the test labels.

If they ask about label noise: Wilm and colleagues, 2025, showed border cells on NIH smears are often unlabeled. We have not corrected labels. M4 does not either.

If they ask what we would add later: Nothing in this milestone. A second change, a new model, or an external set would be a different project. The handout asks for one predicted change.

---

# Q&A bank · both speakers · word-for-word

**“Didn’t Rajaraman already do your project?”**  
They already compared cell-level 98.6 with patient-level 95.9. What we reproduced is the patient-level ResNet-50 direction, approximately. What we add, and have not yet computed, is Patient-ID macro sensitivity against the pooled sensitivity on our saved predictions.

**“Didn’t MalariaNet already do your project?”**  
They showed the mean drop is about 1.5 points and that sensitivity and specificity need not move together. Their model is a small network aimed at a microcontroller. We did not train it. Our one change is a reporting change on the 2018-style baseline.

**“Why are you 2 points below 95.9?”**  
Accuracy is 93.90 versus 95.9. Sensitivity is much closer, 94.24 versus 94.7. Specificity is the wide gap, 93.56 versus 97.2. Their folds, feature layer, normalization, classifier width, and hyperparameter search are not in our source. We did not tune the test fold to close it.

**“Is fold 2 an error?”**  
Overlap is zero and the classes are balanced. Sensitivity is 88.28 with 325 false negatives, while specificity stays at 93.01. We kept the fold. It is why the sensitivity SD is 3.36 points.

**“So the hypothesis is already true?”**  
No. Fold 2 shows that a mean can hide a hard subset of the data. It does not measure macro minus pooled inside a fold. That measurement is M4, under a rule written on 3 October.

**“Why would macro be lower?”**  
Because a one-cell Patient-ID and a 633-cell Patient-ID count the same in the macro mean, and five IDs already hold about 21 percent of parasitized cells. A miss on a tiny ID barely moves the pooled rate and fully moves that ID’s sensitivity.

**“What if the big groups are the hard ones?”**  
Then the macro gap can be small or positive. Four of five positive differences and a mean of at least plus 1.68 points is the unsupported outcome. We will report that if it happens.

**“What is 1.68?”**  
Half of 3.36, our measured sensitivity standard deviation across the five M2 folds. It is the magnitude cutoff in the decision rule. The predicted band is wider: about minus 1 to minus 3 points.

**“Which IDs enter the macro?”**  
Only IDs with at least one parasitized cell in that test fold. Fifty of the 201 IDs have no parasitized cells at all. Those are counted as undefined for sensitivity. They are not deleted from the data.

**“Why not call them slides?”**  
The field we split on is the official Patient-ID. The datasheet’s entry counts are not a slide table, and they are not a silent rewrite of the paper’s 150 plus 50. Renaming the key would hide that.

**“Will you beat 99 percent?”**  
No. That is not the target. A patient-level accuracy near 94 to 96 is the neighborhood of this reproduction. The result we care about is the pre-registered macro-minus-pooled difference.

**“Is this a clinical result?”**  
No. Labeled public cells, one species, already cropped. No patient diagnosis, no prevalence, no device claim.

**“What did you not copy from the paper?”**  
Exact fold members, the selected feature layer, the normalization constants, the classifier width, the original weight file, and the randomized search. Dropout 0.5, ResNet-50 as a feature extractor, patient-level five-fold evaluation, and the metric list are what we did copy.

**“Did you run a cell-level split too?”**  
No. Table 6’s cell-level numbers stay in the published baseline file for reference. Our measured table is patient-grouped only.
