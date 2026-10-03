# Paper 3 — Mmileng et al. 2025

**Full title:** Application of ConvNeXt with transfer learning and data augmentation for malaria parasite detection in resource-limited settings using microscopic images  
**Venue:** PLoS One 20(6): e0313734  
**Link:** https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12136420/  
**Read:** abstract + methods + results (full PDF available)

## Paper kya problem solve kar raha hai
Low-resource setting me skilled microscopist kam hain. Wo ConvNeXt (modern CNN jo ViT tricks use karti hai) + transfer learning + heavy augmentation se malaria cell classify karna chahte hain, plus LIME/LLaMA se explanation, Gradio app ke saath.

## Dataset aur method
NIH 27,558 (13,779 + 13,779), source Rajaraman/LHNCBC. Resize **224×224** Lanczos. Normalize mean 0 variance 1. Augmentation: flip, 45° rotate, scale 0.5–1.5, Gaussian noise, contrast, shear, blur, sharpen, hue/sat. Dataset **27,558 → 606,276** (~22×). Models: Swin Tiny, ResNet18, ResNet50, ConvNeXt V1 Tiny, ConvNeXt V2 Tiny Remod. AdamW, label smoothing ε=0.1, 10 epochs, mixed precision, OneCycleLR.

## Evaluation split
Methods me training tricks detail me hain. **Train/val/test ratio ya patient-level split mujhe nahi mila.** Patient-aware: NOT STATED. Ye augmentation ke baad dangerous hai: agar split augment ke baad ho, near-duplicate crops train aur test dono me aa sakte hain. Paper ye order explicitly nahi lock karti.

## Results
ConvNeXt V2 Tiny Remod **98.1%**. V1 Tiny **95.9%**. Swin Tiny 61.4%, ResNet18 62.6%, ResNet50 81.4%. V1 Tiny ka 95.9% Rajaraman ke **patient-level** number se numerically same hai, protocol same nahi.

## Limitation
Split protocol missing. 10 epochs, massive synthetic set. ResNet/Swin yahan bahut weak — architecture gap itna bada unusual hai, isliye unke numbers ko seedha SOTA se mat compare karo. “Resource-limited” claim Gradio + Tesla P100 training pe hai, field MCU pe nahi.

## Humare gap se connect
Classic gap example: accuracy high, split silent, augmentation 22×. Talking point: **95.9% do alag wajah se aa sakta hai** — patient-level honest eval (Rajaraman) vs ConvNeXt V1 Tiny with unknown split. Numbers dekh ke protocol assume mat karo.
