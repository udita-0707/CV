# Paper 5 — Alharbi et al. 2022

**Full title:** Computational Models-Based Detection of Peripheral Malarial Parasites in Blood Smears  
**Venue:** Contrast Media & Molecular Imaging, Article ID 9171343; PMC9200540  
**Link:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC9200540/  
**Read:** full PDF (kuch tables OCR-messy hain)

## Paper kya problem solve kar raha hai
Early malaria detection pretrained CNNs se, VGG-19 ko feature extractor / fine-tune karke. NIH data Kaggle pe upload karke use kiya.

## Dataset aur method
27,558 cells, 13,779 / 13,779. Morphological filters, scale mostly **128×128** RGB. Custom CNN bhi train kiya; main story VGG-19 freeze vs fine-tune + augmentation (rotate, shear, translate, zoom). Adam, sigmoid, binary cross-entropy.

## Evaluation split
Patient-level **nahi**. Cell-level random: **8000 train + 3000 val per class** (11,000/class train pipeline), remaining **2779/class test**. Authors “random sample” likhte hain. Tumhari original table me “not stated” tha — split **cell-random hai, patient-aware nahi**.

## Results — do numbers, mismatch
Abstract: **98.34 ± 0.51%**.  
Table 4: Basic CNN 0.9397±0.23; VGG-19 frozen 0.9486±0.13; **VGG-19 fine-tuned 0.9704±0.06**.  
Table 1 (custom CNN test): acc 95.56, F1 96.45, AUC 95.45, sens 96.65, spec 95.25.  
Slide pe abstract wala 98.34 mat akela chipkao; mismatch bolna.

## Limitation
Writing/tables messy. Support counts Table 5 (~8158) unke 2779×2 test se match nahi khate. Patient ID ignore. Sensitivity/AUC consistently nahi across models.

## Humare gap se connect
High-looking abstract number, cell-level random, patient split absent. Extra talking point: field kabhi Rajaraman ko sirf “95.9%” cite karti hai, cell-level 98.6% bhool ke — do numbers ko ek bana dena khud gap ka evidence hai.
