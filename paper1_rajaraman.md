# Paper 1 — Rajaraman et al. 2018 (BASE PAPER)

**Full title:** Pre-trained convolutional neural networks as feature extractors toward improved malaria parasite detection in thin blood smear images  
**Venue:** PeerJ 6:e4568  
**Link:** https://peerj.com/articles/4568/  
**Read:** full PDF

## Paper kya problem solve kar raha hai
Malaria diagnose karna microscopist pe depend karta hai. Hand-engineered features se CAD banana mushkil hai kyunki cell size, stain, angle sab change hota hai. Ye paper poochta hai: ImageNet pe pre-trained CNNs ko feature extractor ki tarah use karke parasitized vs uninfected cell classify kiya ja sakta hai ya nahi, aur kaunsa layer best features deta hai.

## Dataset aur method
NIH/NLM thin-smear cells. 150 infected + 50 healthy patients, Chittagong. Total **27,558** cells, 13,779–13,779. Level-set se RBC segment kiye. Resize 100/224/227/299, mean-normalize.

Models: custom 3-conv CNN, plus AlexNet, VGG-16, Xception, ResNet-50, DenseNet-121 as feature extractors. Classifier upar fully-connected + dropout 0.5. Randomized grid search for LR / SGD / L2.

## Evaluation split
**Patient-level 5-fold CV** main protocol hai (Table 1 fold counts). Authors clearly likhte hain: patient-level isliye taaki stain/artifact train se test me leak na ho. Table 6 me **cell-level bhi** report kiya, literature se compare karne ke liye. Unka khud ka line: unhe koi comparable paper nahi mila jo is scale pe patient-level CV karta ho.

## Results (jo table me hain)
Patient-level (optimal-layer / Table 6 “patient level”): ResNet-50 **acc 0.959, sens 0.947, spec 0.972, AUC 0.991**.  
Cell-level (Table 6): **acc 0.986, sens 0.981, spec 0.992, AUC 0.999**.  
Table 2/4 ke ± numbers 5-fold patient CV ke mean±sd hain. Sensitivity me models ke beech statistically significant difference nahi (Kruskal–Wallis p=0.356). Authors screening ke liye sensitivity ko important maante hain. Stain variation ko patient-level drop ki wajah batate hain.

## Limitation
Sirf thin-smear P. falciparum cells. Mobile deploy sirf pilot. Color normalization suggest kiya, kiya nahi as main method. Cell-level 98.6% ko SOTA se compare kiya — ye number aasan hai cite karna, patient-level 95.9% log skip kar dete hain.

## Humare gap se connect
Yahi origin paper hai. Comparison **already 2018 me ho chuka**. Gap ye nahi ki “kisi ne socha nahi.” Gap ye hai ki baad ke papers high number copy karte rahe, patient protocol nahi. Hum reproduce isi baseline ko karenge, phir mean accuracy ke bajay per-slide error aur sens vs spec dekhenge.
