# Paper 8 — Ahishakiye et al. 2025 (CNN-ViT ensemble)

**Full title:** Enhancing malaria detection and classification using convolutional neural networks-vision transformer architecture  
**Venue:** Discover Applied Sciences (2025)  
**Link:** https://link.springer.com/article/10.1007/s42452-025-06704-z  
**Read:** Springer full text (HTML)

## Paper kya problem solve kar raha hai
Existing ML malaria models me low performance / overfitting. CNN local morphology pakadti hai, ViT global context. Ensemble dono concatenate karke classify karta hai.

## Dataset aur method
NIH, wo 13,794/class likhte hain — official 13,779 hai, chhoti counting error. Resize **224×224**, ImageNet normalize. CNN = ResNet18, ViT = ViT_B_16 (16×16 patches), features concat → FC. Aug: rotate, flip, brightness, contrast. SMOTE mention (dataset already balanced — odd). Dropout 0.3/0.2, L2, early stopping. Adam lr 0.001 (tune 0.0001, batch 32, dropout 0.3).

## Evaluation split
**80% train / 20% test** clearly. Baad me **k-fold with stratified sampling** bhi claim. Patient/slide **nahi**. External val nahi, future work.

**Flag (verified counts):** Discussion confusion matrix: TP 13745, FN 101, TN 13678, FP 34. Sum = **27,558** = poori dataset, 20% test (~5512) nahi. Possible train+test pe report, ya writing error. Slide pe “they cheated” mat bolo; bolo counts full set se match karte hain, isliye headline 99.64% ko held-out mat samjho jab tak clarify na ho.

## Results
Ensemble: acc **99.64%**, prec 99.23%, recall **99.75%**, F1 99.51%, CE loss 0.01, AUC 1.00 claimed. CNN-only ~97.67%, ViT-only ~95.75%.

## Limitation
Highest acc in our list, sabse complete metrics, **patient split zero**. Compute heavy. Class counts + confusion-matrix size inconsistent.

## Humare gap se connect
Best closing citation: rigor ke baaki pieces hain (ablation, ROC, dropout), evaluation granularity missing. Course ke hisaab se sensitivity report karna zaroori hai — unhone recall 99.75% diya, lekin kis split pe unclear.
