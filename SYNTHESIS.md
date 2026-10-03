# Rubric + gap synthesis (after slides)

## Rubric (from CV_Student_Handout_Project.docx.pdf — 1 page)
No numeric weightage is printed on the handout.

Graded around:
1. Literature survey (10–20 papers: methods, datasets, metrics)
2. One base paper with public data (+ reproducibility checklist)
3. Reproduce near the reported metric
4. ONE hypothesis + predicted effect, submitted BEFORE coding
5. Implement that one change + ablations
6. Failure analysis + IEEE write-up + defence

Explicit rules:
- Predict before you experiment (wrong prediction is OK if reasoning is good)
- No clinical claims
- Report sensitivity/recall + AUC, not just accuracy
- Include a limitations section

Milestones: M1 survey+paper+checklist · M2 baseline runs · M3 hypothesis+intro · M4 implementation+ablation · M5 failure analysis+IEEE+defence

This talk is M1.

## Sample PPT structure only (do not reuse their content)
13 slides. Title with 3 names → visual “infected vs uninfected” → dataset stats + metric list → literature as 2 papers per slide (method, acc, one limitation) → dedicated base-paper slide → “results cannot be compared because protocols differ” → their gap was stain/illumination, their one change was colour augmentation. Different gap from ours. Different papers from ours except Rajaraman and ISTNet.

## Corrections vs your original table (do not guess past this)
- **EDRI:** split IS stated: stratified 80/10/10. Authors explicitly skip k-fold. Not patient-aware.
- **Alharbi:** cell-level random split IS described (8000 train + 3000 val per class; 2779/class test). Abstract 98.34±0.51%; Table 4 VGG-19 fine-tuned is 97.04±0.06%. Those two numbers disagree — cite both.
- **CNN-ViT 2025:** 80/20 is stated; k-fold is claimed. Confusion matrix TP+FN+TN+FP reconstructs the full 27,558 set, which is inconsistent with a 20% test set. Flag in Q&A, do not over-claim fraud.
- **Systematic review:** journal is *Engineering Applications of Artificial Intelligence* (2024), DOI 10.1016/j.engappai.2024.108529 — not Computers in Biology and Medicine. Full text not retrieved (paywall / fetch fail). Abstract-level only.
- **ISTNet:** full PDF not in folder; abstract only. Split protocol unknown.
- **Mmileng:** no train/test ratio found in methods through training setup. Augmentation 27,558 → 606,276 is explicit.
- **MalariaNet:** 224×224 is what you wrote; paper resizes to **128×128**.

## Gap refinement
Rajaraman already did the comparison and said nobody else had. The field mostly ignored it. MalariaNet re-did it in 2026: leak confirmed, magnitude small, all 8 models same direction, module-ablation “wins” vanish under slide-disjoint. So novelty is not “we discovered leakage” and not “accuracy falls off a cliff.” Novelty is: mean accuracy is the wrong headline; per-slide error and sensitivity/specificity under the same protocol are still missing.
