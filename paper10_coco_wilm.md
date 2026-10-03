# Paper 10 — Wilm et al. 2025 (COCO-format NIH)

**Full title:** A COCO-Formatted Instance-Level Dataset for Plasmodium Falciparum Detection in Giemsa-Stained Blood Smears  
**Venue:** MELBA 2025:022; arXiv 2507.18483  
**Link:** https://arxiv.org/pdf/2507.18483  
**Read:** full arXiv text

## Paper kya problem solve kar raha hai
NIH smear images pe object detection ke liye boxes kam hain. 965 images: 165 polygon, 800 sirf point (cell center). Classification papers segmented crops use karti hain; detection ke liye boxes chahiye. Wo Cellpose + manual fix se COCO boxes banate hain.

## Dataset aur method
Same Bangladesh NIH smears, lekin **full FOV**: 193 patients (148 infected, 45 uninfected), 5 images/patient, 5312×2988. Faster R-CNN, ResNet34 ImageNet backbone. Train 70% / val 30% **image-level** (patient-disjoint explicitly nahi). Cross: train polys → test boxes, aur ulta.

## Evaluation split
70/30 on the image subsets. Classification-cell random-split se alag task. Patient-aware detection split **stated nahi**.

## Results
Infected-cell F1 **0.84** (train polys) vs **0.88** (train MIRA boxes). Infected recall 0.77 vs 0.91. Ambiguous (unlabeled border) cells ~19,592, ~10% of points subset. Border cells original labels me frequently missing. Single-expert annotation bias likely.

## Limitation
Detection paper, classification SOTA nahi. Ambiguous class evaluation se exclude. Class imbalance (infected << uninfected on full smears).

## Humare gap se connect
Limitations slide ke liye, accuracy table ke liye nahi. Agar NIH cell labels border/point protocol se noisy hain, to 99% cell-crop accuracy ka matlab limited hai. Humare per-slide error analysis me ye relevant: kuch slides pe “error” label noise ho sakti hai, model fail nahi. WHO 0.90 recall mention hai unka — hum clinical claim nahi uthayenge.
