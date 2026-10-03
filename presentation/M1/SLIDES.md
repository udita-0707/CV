# CSA431 — PPT-ready bullets (paste now)
Literature review | NIH malaria cell classification | ~10 slides

Do not copy the sample team’s wording. Their flow was title → task visual → dataset → 2-papers-per-slide → base paper → “one change.” Ours is evaluation-protocol first.

---

## SLIDE 1 — Title
- Patient- vs cell-level evaluation in malaria parasite classification
- Dataset: NIH / NLM malaria cell images (27,558 cells)
- Course: CSA431 Computer Vision | Literature review + base-paper selection
- Base paper: Rajaraman et al., 2018, PeerJ 6:e4568
- Team: [names]

## SLIDE 2 — Motivation
- Malaria screening still depends on microscope reading of Giemsa smears
- NIH dataset: 13,779 parasitized + 13,779 uninfected cells from 150 infected + 50 healthy patients
- Cells are not independent: they come from ~200 slides; same slide shares stain, lighting, focus
- Many later papers report 96–99% accuracy on this dataset
- Course rule: report sensitivity/recall + AUC, not accuracy alone; no clinical claims

## SLIDE 3 — The evaluation problem (why this topic)
- Random cell-level split: cells from the same slide can appear in both train and test
- Patient- / slide-disjoint split: a test slide is fully unseen
- Rajaraman (2018) already ran both: 98.6% cell-level vs 95.9% patient-level (Table 6)
- They wrote that, at the time, no comparable work had done patient-level CV on this scale
- Later papers kept citing the high number, often without repeating the split

## SLIDE 4 — Related work (1/2): papers that actually compared splits
| Paper | Method | Split | Acc | Sens | AUC |
| Rajaraman 2018 | VGG-16 / ResNet-50 features | BOTH: cell-level AND patient 5-fold | 0.986 / 0.959 | 0.981 / 0.947 | 0.999 / 0.991 |
| MalariaNet 2026 | compact CNN, 8 architectures | BOTH: per-cell 70/15/15 AND slide-disjoint | 0.971 / 0.956 | 0.939 (slide-disjoint) | 0.988 (slide-disjoint) |

Takeaway for this slide:
- Leakage is real (unanimous drop across 8 models in MalariaNet)
- Drop is small: ~1.5 pp, inside seed noise (±1.02)
- Direction of the bias is the finding, not a catastrophic accuracy collapse

## SLIDE 5 — Related work (2/2): high accuracy, weak split reporting
| Paper | Method | Split we could verify | Headline acc |
| Narayanan 2019 | GoogLeNet / ResNet + CAM | 80/20 hold-out (cell-level); 10% of train = val | 0.965 / 0.966; AUC 0.993 |
| Alharbi 2022 | VGG-19 fine-tune | cell-level random (8000+3000/class train/val; rest test); not patient-aware | abstract 0.9834±0.0051; Table 4 fine-tune 0.9704±0.06 |
| EDRI 2024 | EfficientNetB2 + Dense/Res/Inception | stratified 80/10/10; authors say no k-fold | 0.9768; recall 0.9644; AUC 0.9976 |
| Mmileng 2025 | ConvNeXt V2 Tiny Remod | train/test ratio not found; 27,558 → 606,276 aug. | 0.981 (V2); 0.959 (V1) |
| ISTNet 2026 | Inception-Swin hybrid | not in abstract; full PDF not available | 0.9661 NIH / 0.9965 BBBC041 |
| CNN-ViT 2025 | ResNet18 + ViT_B_16 ensemble | 80/20 + k-fold claimed; confusion-matrix counts = full 27,558 | 0.9964; recall 0.9975 |

Meta / labels (not accuracy papers):
- PRISMA review 2024: Eng. Appl. of AI (DOI 10.1016/j.engappai.2024.108529) — field-level corroboration; full text not retrieved
- Wilm et al. 2025: COCO boxes on NIH smears; border cells unlabeled; infected-cell F1 up to 0.88

## SLIDE 6 — What the table actually shows
- 2/10 papers ran a leakage-free comparison (Rajaraman, MalariaNet)
- Several high-acc papers use random/stratified cell splits, or do not state a patient split
- ConvNeXt V1 Tiny 95.9% = Rajaraman’s patient-level number, for a different reason
- Cross-dataset testing (ISTNet NIH + BBBC041) is not a substitute for within-dataset patient splits
- CNN-ViT: most complete metric list in the survey, still no patient-disjoint protocol

## SLIDE 7 — Research gap (paste these 4 bullets)
- Random cell splits leak slide identity; Rajaraman already measured 98.6% → 95.9% under patient-level CV, and later NIH papers largely did not repeat that protocol
- MalariaNet (2026) confirms the leak (~200 slides) but shows the accuracy drop is only ~1–2 pp and sits inside cross-seed noise — so “leakage wrecks accuracy” is too simple
- Mean accuracy therefore hides the real risk: a few hard slides can dominate error, and sensitivity/specificity can move differently than accuracy
- Open question we will study: under slide-disjoint evaluation, how does error vary per slide, and does sensitivity drop more than specificity?

## SLIDE 8 — Proposed direction (one change, rubric-aligned)
- Base: Rajaraman 2018 ResNet-50 feature extractor, NIH 27,558
- Keep: same architecture, same patient/slide folds as far as filenames allow
- Change: stop reporting only mean accuracy; add (1) per-slide error distribution (2) sensitivity vs specificity under the same leakage-free split
- Predict before coding (course rule): mean acc drop will be small (~1–2 pp, matching MalariaNet); per-slide variance and sensitivity will move more than accuracy
- Metrics we will always report: sensitivity/recall, specificity, AUC — not accuracy alone
- Not a diagnostic claim: screening experiment on public cells only

## SLIDE 9 — Why this base paper
- Public dataset they released; code-reproducible CNN feature-extraction setup
- Only origin paper that published both cell-level and patient-level numbers on this set
- Reproducibility checklist: dataset URL public; 5-fold patient CV described; metrics listed; limitations include staining variation across patients
- MalariaNet is the 2026 confirmation paper, not the base we reproduce

## SLIDE 10 — Conclusion / next
- Field still publishes 97–99% on NIH with cell-level or unstated splits
- Leakage exists; the interesting leftover gap is metric- and slide-level, not a huge accuracy gap
- Next: reproduce Rajaraman patient-level baseline, then the one analysis change above
- Limitations we already expect: single-species thin-smear cells; label noise at smear borders (Wilm 2025); no external hospital set in M1
