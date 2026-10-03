# Word-for-word script

PPT: `CSA431_Literature_Review.pdf` · 10 slides · ~10 minutes

**A = Udita (230082)** · **B = Aman Kumar (230064)**

How to use this:

- Bold **SAY THIS** is the talk. Read it out loud. Do not paraphrase.
- **If they stop you** is also word-for-word. Memorise those. Only say them if someone interrupts or asks.

---

# SLIDE 1 · Title · Speaker A · [0:00–0:35]

**SAY THIS**

Good morning. This is our CSA431 literature review.

The title is patient-level versus cell-level evaluation in malaria parasite classification.

The dataset is the NIH NLM malaria cell images. Twenty-seven thousand five hundred fifty-eight cells.

The base paper is Rajaraman et al., 2018, PeerJ.

I am Udita, enrollment 230082. This is Aman Kumar, enrollment 230064.

**If they stop you**

If they ask what the task is: The task is binary classification. Each image is one segmented red blood cell. The label is parasitized or uninfected.

If they ask why this title: Because the same dataset can give 98.6 percent or 95.9 percent depending on whether you split by cell or by patient. That difference is the topic.

---

# SLIDE 2 · Motivation · Speaker A · [0:35–1:45]

**SAY THIS**

Why the evaluation protocol matters here.

There are 27,558 cell images. 13,779 parasitized. 13,779 uninfected.

Those cells were sampled from 150 infected patients and 50 healthy patients. That 150/50 count is from Rajaraman 2018.

The third number is about 200 source slides. That is not a second patient census. MalariaNet 2026 grouped the files by slide identity and got about 200 groups. Cells from one slide are not independent. They share stain, lighting, and focus.

Screening today still relies on a person reading Giemsa-stained blood smears under a microscope.

Many later papers report 96 to 99 percent accuracy on this exact dataset. The number keeps climbing.

Course rule for this project: we report sensitivity or recall, and AUC, not accuracy alone. We make no clinical claims.

**If they stop you**

If they ask whether 13,779 uninfected means only the 50 healthy patients: No. Uninfected means the cell has no Plasmodium. Rajaraman also includes staining artifacts. Infected patients still have uninfected red cells. So 150/50 is who was sampled, not a one-to-one map onto the two classes.

If they ask who said 200 slides: MalariaNet. They parsed a C-number from every filename. That gave 200 groups covering all 27,558 cells. Rajaraman’s figure is 200 patients, 150 plus 50. Same order of magnitude. Different sentence. We do not say Rajaraman wrote 200 slides.

If they ask what 96 to 99 percent cites: It is the range of later NIH cell-classification papers in our survey, not one paper. Slide 5 is the list.

If they ask why not accuracy: The course handout says report sensitivity or recall and AUC, not just accuracy, and include limitations. The set is balanced 50/50, so accuracy can look high while sensitivity moves.

---

# SLIDE 3 · Core problem · Speaker A · [1:45–2:50]

**SAY THIS**

This is the core problem. Two ways to split the same 27,558 cells.

R is a random cell-level split. Cells are shuffled with no check on the source slide. Cells from the same slide can land in both train and test. The model can partly memorise stain, lighting, and focus, not just the parasite.

P is a patient-level or slide-disjoint split. Every slide goes fully to train or fully to test. Never both. A test slide is completely unseen. That is the fair way to check if the model generalises to a new patient.

Rajaraman already tested both. Table 6 in their paper: 98.6 percent cell-level, 95.9 percent patient-level. They noted that, at the time, no comparable work had run patient-level cross-validation at this scale. Later NIH papers largely did not repeat that protocol.

**If they stop you**

If they ask where 98.6 and 95.9 come from: Rajaraman Table 6. The rows are labelled Proposed model, cell level, and Proposed model, patient level. The proposed model is their ResNet-50 feature-extractor pipeline. Patient-level accuracy 0.959 also matches Table 4 for ResNet-50 after they chose the best layer, 0.959 plus or minus 0.008.

If they ask why cell-level is higher: They say staining varies across patients. Same-slide cells leak that stain into test. Patient-level removes that leak. They wrote that themselves.

If they ask what CV means: Five-fold cross-validation at the patient level. Table 1 lists cell counts per fold. Folds are not random cells. They are grouped so a patient’s cells stay together.

If they ask did they only do patient-level: No. Main protocol is patient-level five-fold. Table 6 also reports cell-level so they can compare with older papers that used random splits.

---

# SLIDE 4 · Related work 1 · Speaker A · [2:50–4:20]

**SAY THIS**

Only two papers in our survey compared both splits. That is this table.

First row. Rajaraman 2018. Method: VGG-16 and ResNet-50 as feature extractors. Split: both. Cell-level and patient five-fold. Accuracy 0.986 cell-level, 0.959 patient-level. Sensitivity 0.981 and 0.947. AUC 0.999 and 0.991. Those are Table 6.

Second row. MalariaNet 2026. Method: a compact CNN. They also benchmarked eight architectures. Split: both. Per-cell 70/15/15, and slide-disjoint. Accuracy 0.971 per-cell, 0.956 slide-disjoint. Those are rounded. The paper is 97.06 percent and 95.61 percent. Sensitivity on the slide is slide-disjoint only: 0.939. That rounds 93.94 percent. AUC on the slide is slide-disjoint: 0.988.

Takeaway, three lines, all on the slide.

Leakage is real. The drop shows up on all eight architectures in MalariaNet. Every delta is negative.

The drop is small. Roughly 1.5 percentage points. For MalariaNet itself the drop is 1.45 points, and their three-seed standard deviation is plus or minus 1.02. So 1.5 sits inside that seed noise.

The finding is the direction of the bias. It is not a catastrophic accuracy collapse. We are not claiming leakage destroys accuracy. We are claiming random splits inflate the number, a little, every time.

**If they stop you**

If they ask is 0.986 VGG-16 or ResNet-50: Table 6 says Proposed model. In the paper that is ResNet-50, the one they recommend. VGG-16 is also strong. Table 4, patient-level, both VGG-16 and ResNet-50 have accuracy 0.959. If they want one name, say ResNet-50.

If they ask why the slide says VGG-16 / ResNet-50: Those two were the best feature extractors. We are not saying both numbers in Table 6 are VGG-16.

If they ask 0.971 versus 97.06: The slide rounds to three decimals. 97.06 percent is 0.9706, shown as 0.971. 95.61 percent is shown as 0.956.

If they ask did all eight drop by 1.5 points: No. Do not say that. All eight dropped. The size is different. ResNet-18 dropped about 0.25 points. MalariaNet dropped 1.45. Plus or minus 1.02 is MalariaNet’s own seed noise, not a confidence interval on the whole table.

If they ask which eight models: ResNet-18, MobileNetV2, EfficientNet-B0, MobileNetV3-Small, ShuffleNetV2, Tiny-MobileNetV2, SingleStream, and MalariaNet.

If they ask 70/15/15: Train, validation, test. They used that ratio for both protocols. Slide-disjoint means they split by slide group, about 140, 30, and 30 slides. No slide in two splits.

If they ask why sensitivity is only listed once for MalariaNet: Because the slide shows slide-disjoint sensitivity, 0.939. We did not print per-cell sensitivity. Specificity is 97.41 percent in their Table 3. It is not on our slide. If they want it, say 97.41 percent slide-disjoint, and say it is not printed.

If they ask AUC 0.988 versus 0.994: 0.988 is slide-disjoint, Table 3. Their per-cell ROC is higher, around 0.994. That per-cell curve is the optimistic one. We printed the leakage-free AUC.

If they ask 128 or 224: MalariaNet resizes to 128 by 128. Not 224.

---

# SLIDE 5 · Related work 2 · Speaker A · [4:20–6:15]

**SAY THIS**

Six more papers. High accuracy. Weaker split reporting. I will read the table as printed.

Narayanan 2019. GoogLeNet and ResNet, plus class activation maps. Split we verified: 80/20 hold-out, cell-level. Ten percent of train held for validation. Headline: 0.965 to 0.966, AUC 0.993. Exact accuracies are 96.5 percent GoogLeNet and 96.6 percent ResNet. Exact AUCs are 0.9929 and 0.9934. The slide rounds AUC to 0.993.

Alharbi 2022. VGG-19 fine-tune. Split: cell-level random. Not patient-aware. Headline on the slide is 0.9834 plus or minus 0.0051. That is their abstract. 0.9834 is 98.34 percent. 0.0051 is 0.51 percent. Their results Table 4 for fine-tuned VGG-19 is 97.04 percent plus or minus 0.06. If you check the tables, that is the mismatch. We printed the abstract number because that is what they lead with. We will not pretend Table 4 says 98.34.

EDRI 2024. EfficientNetB2 plus Dense, Residual, and Inception blocks. Split: they did state one. Stratified 80/10/10. They say they did not run k-fold. Headline: 0.9768 accuracy, recall 0.9644. Stratified means both classes stay balanced. It does not mean patient-disjoint. Same patient’s cells can still be in train and test.

Mmileng 2025. ConvNeXt V2 Tiny Remod. Split ratio is not stated in the methods we read. Heavy augmentation. Headline: 0.981 for V2, 0.959 for V1 Tiny. 0.959 is 95.9 percent. That digit matches Rajaraman’s patient-level accuracy. Different paper. Different reason. We could not find a train/test ratio.

ISTNet 2026. Inception-Swin hybrid. Split: not in the abstract. Full text unavailable to us. Headline: 0.9661 on NIH, 0.9965 on BBBC041. We do not claim a split for this paper. We only claim the two accuracies in the abstract.

CNN-ViT 2025. ResNet18 plus ViT-B-16 ensemble. Split: they claim 80/20 and k-fold. Not patient-disjoint. Headline: 0.9964 accuracy, recall 0.9975. Highest accuracy in this survey. Most complete metric list. Still no patient-disjoint protocol.

Footer. Two extra sources. Not accuracy papers. A 2024 PRISMA-style review. We did not retrieve the full text. And Wilm et al. 2025. They put COCO boxes on NIH smears. Border cells are often unlabeled. Infected-cell F1 up to 0.88.

**If they stop you**

If they ask Narayanan 80/20 counts: Train 9921 plus 9921. Validation 1102 plus 1102. Test 2756 plus 2756. That adds to 27,558. Cell-level. They cite Rajaraman as the data source. They do not use patient folds.

If they ask Alharbi how they split: They write random samples. 8000 train and 3000 validation per class, remaining 2779 per class as test. That is cell-level random. Not on the slide. Patient IDs are not used.

If they ask EDRI AUC: 99.76 percent in the paper. Not on our slide. Precision 98.88. F1 97.65. We printed accuracy and recall because that is what the slide shows.

If they ask Mmileng how heavy is heavy: Methods say 27,558 went to 606,276 after augmentation. About 22 times. Split order versus augmentation is not locked in the text. That is why we wrote split ratio not stated.

If they ask ISTNet full paper: We do not have it. If they have a split in the PDF, we have not verified it. We will not invent one.

If they ask CNN-ViT confusion matrix: The paper reports 13,745 true positives, 101 false negatives, 13,678 true negatives, 34 false positives. That sums to 27,558. That is the full dataset, not 20 percent of it. We did not print that. If you mention it, call it a flag. Do not say they cheated.

If they ask CNN-ViT other metrics: Precision 99.23 percent. F1 99.51 percent. Cross-entropy loss 0.01.

If they ask the PRISMA venue: Engineering Applications of Artificial Intelligence, 2024. DOI 10.1016/j.engappai.2024.108529. It is not Computers in Biology and Medicine. Full text not retrieved. We do not quote counts from that review.

If they ask Wilm 0.88: Infected-cell F1, Faster R-CNN, train on their revised boxes, test on the original polygon subset. The other direction is 0.84. Border cells unlabeled is the limitation we use later.

---

# SLIDE 6 · Reading the survey · Speaker B · [6:15–7:10]

**SAY THIS**

What the table actually shows. Four points.

Two out of ten sources ran a leakage-free comparison. Those two are Rajaraman and MalariaNet. Ten is our survey list. Eight of them are model papers. Two are not: the review and Wilm. So two of ten sources. Two of eight models. Same two names.

Several high-accuracy papers use random or stratified cell splits, or never state a patient split at all. That is slide 5.

95.9 percent. ConvNeXt V1 Tiny matches Rajaraman’s patient-level number, but for an unrelated reason. Matching digits are not matching protocols.

Cross-dataset is not a fix. ISTNet tested NIH and BBBC041. That does not replace a patient split inside NIH.

Last line. CNN-ViT 2025 has the most complete metric list in the survey, and still no patient-disjoint protocol.

**If they stop you**

If they say 2/10 is misleading: Agree on the stricter count. Two of eight classification papers. The slide says 2/10 because we listed ten sources. We are not hiding that two of those ten are not models.

If they ask which eight: Rajaraman, MalariaNet, Narayanan, Alharbi, EDRI, Mmileng, ISTNet, CNN-ViT.

If they ask is Narayanan leakage-free: No. Explicit 80/20 cell hold-out.

If they ask is EDRI leakage-free: No. Stratified 80/10/10 is not patient-disjoint.

---

# SLIDE 7 · Gap · Speaker B · [7:10–8:15]

**SAY THIS**

The gap we are building on. Four lines. I will read them as they are.

One. Random cell splits leak slide identity. Rajaraman already measured 98.6 percent to 95.9 percent under patient-level cross-validation. Later NIH papers largely did not repeat that protocol.

Two. MalariaNet 2026 confirms the leak across about 200 slides, but shows the drop is only about 1 to 2 percentage points and sits inside cross-seed noise. So “leakage wrecks accuracy” is too simple.

Three. Mean accuracy hides the real risk. A few hard slides can dominate error. Sensitivity versus specificity can move differently than accuracy.

Four. Open question we study. Under slide-disjoint evaluation, how does error vary per slide, and does sensitivity drop more than specificity?

This is not “we discovered leakage.” Rajaraman ran the comparison in 2018. This is not “accuracy will crash.” MalariaNet already showed the mean drop is small. The leftover question is where the errors sit, and which metric moves.

**If they stop you**

If they say the other team already did this: Their gap is staining and illumination. Their one change is colour augmentation. Ours is split protocol, then per-slide error and sensitivity versus specificity. Different hypothesis.

If they say Rajaraman closed it: They measured the mean drop. They did not make later papers use patient folds. They also did not report a per-slide error distribution as the result. That is still open.

If they say MalariaNet closed it: MalariaNet closed “the headline accuracy collapse.” They showed module ablations can vanish under slide-disjoint splits. Their main result is still mean accuracy and architecture conclusions. Per-slide error variance is not their headline. That is our one change.

If they ask why sensitivity might drop more than specificity: MalariaNet’s own slide-disjoint point is already uneven. Sensitivity 93.94 percent. Specificity 97.41 percent. Accuracy 95.61 percent. We are predicting that pattern is worth measuring per slide. That specificity number is not on this slide. Say it only if asked.

---

# SLIDE 8 · Proposed direction · Speaker B · [8:15–9:20]

**SAY THIS**

One change. Rubric-aligned.

Base. Rajaraman 2018. ResNet-50 as a feature extractor. NIH 27,558 cells.

Keep. Same architecture. Same patient or slide folds, as far as filenames allow.

Change. Stop reporting only mean accuracy. Add two things, under the same leakage-free split. One: the distribution of error per slide. Two: sensitivity versus specificity.

Predict before coding. The course requires the prediction first. Mean-accuracy drop will be small, about 1 to 2 points, matching MalariaNet. Per-slide variance and sensitivity will move more than accuracy. If we are wrong, that is still a result.

Bottom line on the slide. Metrics we always report: sensitivity or recall, specificity, and AUC. The slide says never accuracy alone. Meaning: accuracy is not the decision metric. We can still print it. We will not rank models by it.

Not a diagnostic claim. Screening experiment on public cells only.

**If they stop you**

If they ask can you match Rajaraman’s exact five folds: Maybe not. Table 1 does not publish patient IDs per fold. Filenames encode case and slide. We can build a group split. The slide already says as far as filenames allow. That is deliberate.

If they ask why ResNet-50 not VGG-16: They selected ResNet-50. Highest mean ranks for accuracy, specificity, F1, and MCC. VGG-16 is tied on some Table 4 numbers. Base model is ResNet-50.

If they ask what else they tested: AlexNet, VGG-16, Xception, DenseNet-121, and a small custom CNN. We are not reproducing all of them for the one change.

If they ask is this just running MalariaNet: No. We reproduce the 2018 ResNet-50 extractor. MalariaNet is a 21,000-parameter microcontroller network. Different model. We use MalariaNet as the 2026 control on the size of the mean drop.

If they ask what per-slide error means: Accuracy, or error rate, computed on each test slide separately. Then we look at the spread. Mean can look fine if two slides are very bad and the rest are easy.

If they ask never accuracy alone versus the course: The handout says report sensitivity and AUC, not just accuracy. We still report accuracy. We do not decide with it.

---

# SLIDE 9 · Why this base paper · Speaker B · [9:20–9:45]

**SAY THIS**

Why Rajaraman 2018.

They released the public dataset. The CNN feature-extraction setup is specified well enough to reimplement. Dataset URL is public. Five-fold patient cross-validation is described. Metrics are listed. Limitations are stated: staining variation across patients.

It is the only origin paper that publishes both cell-level and patient-level numbers on this dataset.

Note at the bottom. MalariaNet is the 2026 confirmation paper. It is not the base we reproduce.

**If they stop you**

If they ask is the training code on GitHub: We are not claiming they shipped a full training repo. They used Keras, pretrained ImageNet weights, and they describe the layers. Code-reproducible means we can rebuild the method from the paper plus the public cells. If we cannot find official training code, we say that. The data is public. The protocol is written.

If they ask why not MalariaNet as base: We need the paper that created the benchmark. Rubric: pick one base paper with public data. That is Rajaraman. MalariaNet is how we know the mean drop is small.

---

# SLIDE 10 · Close · Speaker B · [9:45–10:10]

**SAY THIS**

Where this leaves us.

One. The field still publishes 97 to 99 percent on NIH with cell-level or unstated splits. Slide 2 said 96 to 99. Same range. High nineties. Cell-level or silent patient protocol.

Two. Leakage exists. The interesting leftover gap is metric-level and slide-level, not a huge accuracy gap.

Three. Next: reproduce the Rajaraman patient-level baseline, then run the one analysis change on slide 8.

Limitations we already expect. Single-species thin-smear cells. P. falciparum only. Label noise at smear borders, Wilm 2025. No external hospital set in M1.

We can take questions.

**If they stop you**

If they catch 96–99 versus 97–99: Slide 2 is 96 to 99. Slide 10 is 97 to 99. It is the same informal range. Say high nineties. Do not defend 96 versus 97 as a measurement.

If they ask what M1 is: This presentation. Survey, chosen paper, reproducibility checklist. We have not trained yet.

If they ask clinical use: We will not claim a diagnostic device. Public cells. Screening experiment. Limitations section stays in the paper.

---

# Q&A bank · both speakers · word-for-word

**“Didn’t Rajaraman already do your project?”**  
They already compared cell-level and patient-level. Table 6. 98.6 versus 95.9. What they did not do is stop the field using random splits. What we add is not a new architecture. It is per-slide error variance and a sensitivity-versus-specificity reading after MalariaNet showed the mean accuracy drop is small.

**“Didn’t MalariaNet already do your project?”**  
They confirmed the leak. They showed the mean drop is about 1.5 points and inside seed noise. They showed architecture wins can vanish under slide-disjoint evaluation. Their headline is still mean accuracy. We reproduce Rajaraman, then measure per-slide error and sensitivity versus specificity. That is the one change.

**“Why sensitivity?”**  
Course rule. And a missed parasite is a false negative. Sensitivity is recall on the parasitized class. The set is 50/50, so accuracy can hide a sensitivity drop. MalariaNet slide-disjoint already has sensitivity 93.94 and specificity 97.41.

**“Will you beat 99 percent?”**  
That is not the goal. If patient-level accuracy sits near 96, that matches Rajaraman and MalariaNet. The result we care about is whether error clusters on slides and whether sensitivity moves more than accuracy.

**“How do you know later papers ignored patient CV?”**  
We verified splits in the papers on slide 5. Narayanan is 80/20 cell-level. Alharbi is cell-level random. EDRI is stratified 80/10/10. Mmileng does not state a ratio. ISTNet split is not in the abstract. CNN-ViT claims 80/20 and k-fold, not patient-disjoint. We are not claiming we read every NIH paper ever written. We are claiming this survey.

**“Alharbi 98.34, I opened Table 4.”**  
The slide quotes the abstract, 98.34 plus or minus 0.51 percent. Table 4 fine-tuned VGG-19 is 97.04 plus or minus 0.06. Those two numbers disagree. We printed the abstract. We are not hiding the table.

**“ISTNet split?”**  
We do not know. Abstract only. Full text unavailable. We will not invent a split.

**“2/10 is wrong.”**  
Two of ten sources. Two of eight model papers. Rajaraman and MalariaNet in both counts.

**“Can you reproduce Table 6 exactly?”**  
We will try to land near 95.9 percent patient-level for ResNet-50. Exact match is not required by the rubric. Exact folds may not be recoverable. Filenames still let us block by patient or slide.