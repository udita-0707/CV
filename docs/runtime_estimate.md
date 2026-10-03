# Runtime estimate before M2 execution

**Protocol planned:** one pass through all 27,558 audited cells with frozen
ImageNet-pretrained ResNet-50 to cache features, then five independent
20-epoch classifiers using patient-grouped five-fold assignments.

**Estimate:** 30–75 minutes on this MacBook Pro (Apple M2, 8 GB RAM) using the
PyTorch MPS backend. The dominant unknown is the first ResNet-50 feature
extraction pass and its initial official weight download. The feature cache is
written to `results/resnet50_imagenet_features.npy`, so restarting does not
repeat it if its dimensions and manifest length match.

This estimate is below the 5–6 October evaluation window, so the full
five-fold protocol will be attempted. If the MPS run fails or cannot finish,
the run will be stopped and labelled **REDUCED** rather than presented as the
full protocol.
