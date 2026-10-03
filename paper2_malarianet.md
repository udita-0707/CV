# Paper 2 — MalariaNet 2026 (Hou et al.)

**Full title:** MalariaNet: A Microcontroller-Deployable Malaria-Microscopy Detector for Point-of-Care Biosensing Under Leakage-Free Evaluation  
**Venue:** Biosensors 16, 358  
**Link:** https://pubmed.ncbi.nlm.nih.gov/42505434/ (PDF: MDPI biosensors-16-00358)  
**Read:** full PDF  
**Note:** tumhari table me preprocess 224×224 likha tha; paper **128×128** use karta hai.

## Paper kya problem solve kar raha hai
Do cheezein ek saath. (1) Compact malaria CNN microcontroller (STM32H743) pe chale. (2) NIH literature almost hamesha **per-cell random split** karti hai, jo slide identity leak karta hai. Unka main contribution architecture nahi, **benchmarking finding** hai.

## Dataset aur method
Wahi NIH 27,558. Filename se C-number parse karke **200 groups**. MalariaNet: 21K parameters, stain-colour stream + multi-scale morphology + a gate. 8 models compare: ResNet-18, MobileNetV2, EfficientNet-B0, MobileNetV3-Small, ShuffleNetV2, Tiny-MobileNetV2, SingleStream, MalariaNet. 3 seeds: 42, 123, 2024.

## Evaluation split
Dono protocols, same training recipe:
- Per-cell stratified **70/15/15** (literature-standard, optimistic)
- Slide-disjoint **GroupShuffleSplit 70/15/15 by slide** (~140/30/30 slides), koi slide do splits me nahi

## Results
MalariaNet: per-cell **97.06%** → slide-disjoint **95.61 ± 1.02%**. Gap **−1.45 pp**, unke khud ke seed SD ±1.02 ke andar. **Saare 8 models** ka delta negative. Slide-disjoint MalariaNet: sens **93.94%**, spec **97.41%**, AUC **0.988 ± 0.003**. Per-module ablation gains per-cell pe dikhte hain, leakage-free pe seed noise me collapse / invert. Prototype-cosine “robustness +7 pp” bhi leakage artefact. On-device: 23.5 KB INT8, ~1.2 FPS.

## Limitation
Scope: single P. falciparum thin-smear cells. Acquisition / cell detection / slide-level aggregation out of scope. Delta values independent nahi (same leaked slides). Prevalence-adjusted PPV/NPV table hai; hum clinical claim nahi karenge.

## Humare gap se connect
Sabse strong citation. Leak confirm. Magnitude **chhoti**. Isliye hum “accuracy collapse” wala story nahi sunayenge. Unhone mean acc + architecture conclusions check kiye; **per-slide error distribution** systematically nahi. Sens 93.94 vs spec 97.41 already hint karta hai ki metric-level asaan nahi. Wahi humara pivot.
