# Paper 4 — Narayanan et al. 2019

**Full title:** Understanding Deep Neural Network Predictions for Medical Imaging Applications  
**Venue:** arXiv 1912.09621  
**Link:** https://arxiv.org/pdf/1912.09621  
**Read:** full text

## Paper kya problem solve kar raha hai
Doctors DL predictions pe trust nahi karte kyunki ROI nahi dikhta. Ye paper CAM (class activation mapping) se dikhata hai network kis region pe decide kar raha hai. Malaria **4 applications me se ek** hai (baaki: diabetic retinopathy, brain tumor, TB). Main contribution accuracy nahi, visualization hai.

## Dataset aur method
NIH 27,558, Rajaraman ko dataset source ki tarah cite kiya. Color constancy preprocess, phir ResNet/GoogLeNet input size. Transfer learning: GoogLeNet aur ResNet, homogeneous setup across diseases.

## Evaluation split
**Explicit random hold-out.** 80% train / 20% test. Train ka 10% validation. Table 1: train 9921+9921, val 1102+1102, test 2756+2756 = 27,558. Patient/slide disjoint **nahi**. Base paper pata hai, unka patient-level protocol adopt nahi kiya.

## Results (malaria only)
GoogLeNet **96.5% acc, AUC 0.9929**. ResNet **96.6% acc, AUC 0.9934**. CAM parasitized cells pe parasite spot ke around highlight karta hai. ResNet CAM chhota ROI deta hai vs GoogLeNet.

## Limitation
Multi-task paper, malaria pe depth kam. Hold-out ek hi split, k-fold nahi. Color constancy staining leakage ko fully nahi hataata if same patient dono splits me ho. External malaria set nahi.

## Humare gap se connect
Verified gap example: authors Rajaraman 2018 jaante hain, phir bhi **cell-level 80/20**. CAM useful hai lekin split discipline ka substitute nahi. AUC ~0.993 cell-level pe high dikhta hai — Rajaraman patient-level AUC 0.991 se compare karna protocol ke bina galat hoga.
