# Paper 7 — Wu, Gao & Yu 2026 (ISTNet)

**Full title:** ISTNet: a multi-scale transformer-based architecture for malaria cell classification  
**Venue:** Medical & Biological Engineering & Computing 64(4):1423–1439  
**Link:** https://link.springer.com/article/10.1007/s11517-026-03538-8  
**Read status:** ABSTRACT ONLY. Full PDF is folder me nahi tha; Springer page fetch fail. Split, N, preprocess — **guess nahi karenge**.

## Paper kya problem solve kar raha hai (abstract)
Transformer models infected cells ke scale/morphology diversity pe weak hain. ISTNet = Inception Swin Transformer Network: ISformer (Inception multi-scale + Swin global attention) + multi-branch Inception Mixer.

## Dataset aur method (abstract tak)
Do public datasets: **NIH** aur **BBBC041**. Exact NIH N aur BBBC041 size abstract me nahi. Backbone: hierarchical fusion of Inception + Swin.

## Evaluation split
**Unknown.** Abstract me train/test/patient/slide kuch nahi.

## Results (abstract)
NIH acc **96.61%**. BBBC041 acc **99.65%**. Aur metrics abstract me nahi.

## Limitation
Hum full experiments nahi padh sake. Complex hybrid, reproduce hard (sample PPT ne bhi yahi limitation di — unka phrasing mat copy karna, fact same ho sakta hai). Do datasets par test karna **within-dataset patient split ka substitute nahi**.

## Humare gap se connect
Use this line only: even extra dataset pe 99.65% aa jaye, NIH ke andar random vs patient-disjoint still unanswered. Q&A me seedha bolo: ISTNet full text nahi padha, split claim nahi karenge.
