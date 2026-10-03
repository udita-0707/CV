# Paper 6 — Boit & Patil 2024 (EDRI)

**Full title:** An Efficient Deep Learning Approach for Malaria Parasite Detection in Microscopic Images  
**Venue:** Diagnostics 2024, 14, 2738 (PMC11639908)  
**Link:** https://pmc.ncbi.nlm.nih.gov/articles/PMC11639908/  
**Read:** full PDF  
**Note:** tumhari table me split “not stated” tha. PDF me **stated hai**.

## Paper kya problem solve kar raha hai
Hybrid CNN chahiye jo accurate ho aur resource-constrained setting me chal sake. Existing models compute-heavy aur stain/site shift pe weak.

## Dataset aur method
NIH 27,558, 150 infected + 50 healthy. Resize **224×224**, pixels 0–1. Aug: rotate, shift, zoom, shear, flip.  
**EDRI** = EfficientNetB2 backbone + Dense + Residual + Inception. EfficientNetB2 → 2048-ch map → un blocks ke baad GAP → 256 → Dense 512 → sigmoid. Gradual unfreeze: pehle top 40 layers trainable, 10 epochs baad full unfreeze. Adam, 50 epochs, batch 32, early stopping.

## Evaluation split
**Stratified 80% train / 10% val / 10% test.** Authors explicitly: k-fold nahi kiya, dataset bada aur balanced hai. Stratified = class balance, **patient/slide disjoint nahi**. Patient-aware: NO.

## Results
Acc **97.68%**, precision 98.88%, recall **96.44%**, F1 97.65%, **AUC-ROC 99.76%**, log loss 0.07. Apne blocks ka ablation hai; split-protocol ablation nahi.

## Limitation
10% test ~2756 cells, lekin cells same patients se train me ho sakte hain. Recall (96.44) accuracy (97.68) se kam — course ke hisaab se yahi metric matter karti hai. “Efficient for constrained settings” GCP GPU/TPU pe train hua.

## Humare gap se connect
Clean example: split **likha hai**, phir bhi cell-stratified. High acc **and** high AUC, patient-level absent. Hum ye nahi kahenge “unhone split hide kiya”; kahenge “split diya, galat granularity.”
