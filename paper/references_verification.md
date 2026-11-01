# Reference verification

Each `references.bib` entry was checked field by field against the stored
paper summary in `papers/`. Those files are the project's reading notes,
not the papers themselves. The "Read" status is what the stored file says
was consulted. A field is **verified** only if it appears in the stored file.
Anything else is omitted from the `.bib` file or marked below.

| Key | Stored file | Title | Authors | Venue / volume / pages | Year | Read status (stored file) | Unverified or omitted |
|---|---|---|---|---|---|---|---|
| `rajaraman2018` | `paper1_rajaraman.md` | verified | surname only ("Rajaraman et al.") | PeerJ 6:e4568, verified | 2018, verified | full PDF | co-authors and initials omitted |
| `hou2026malarianet` | `paper2_malarianet.md` | verified | surname only ("Hou et al.") | Biosensors 16, 358, verified | 2026, verified | full PDF | co-authors and initials omitted |
| `mmileng2025` | `paper3_mmileng.md` | verified | surname only ("Mmileng et al.") | PLoS One 20(6): e0313734, verified | 2025, verified | abstract + methods + results | co-authors and initials omitted |
| `narayanan2019` | `paper4_narayanan.md` | verified | surname only ("Narayanan et al.") | arXiv 1912.09621, verified | 2019, verified | full text | co-authors and initials omitted |
| `alharbi2022` | `paper5_alharbi.md` | verified | surname only ("Alharbi et al.") | Contrast Media & Molecular Imaging, Article ID 9171343, verified | 2022, verified | full PDF (some tables OCR-messy) | co-authors and initials omitted |
| `boit2024edri` | `paper6_edri.md` | verified | "Boit & Patil", verified | Diagnostics 14, 2738, verified | 2024, verified | full PDF | initials omitted |
| `wu2026istnet` | `paper7_istnet.md` | verified | "Wu, Gao & Yu", verified | Med. Biol. Eng. Comput. 64(4):1423–1439, verified | 2026, verified | **abstract only** | initials omitted; split protocol unknown (not cited for it) |
| `ahishakiye2025` | `paper8_cnnvit.md` | verified | surname only ("Ahishakiye et al.") | Discover Applied Sciences, verified | 2025, verified | Springer full text (HTML) | **volume / article number not in stored file: omitted** |
| `faizullah2024` | `paper9_systematic_review.md` | verified | surname only ("Faizullah et al.") | Eng. Appl. Artif. Intell., DOI 10.1016/j.engappai.2024.108529, verified | 2024, verified | **abstract/metadata only** | **volume / pages not in stored file: omitted**; not cited for any count |
| `wilm2025coco` | `paper10_coco_wilm.md` | verified | surname only ("Wilm et al.") | "MELBA 2025:022; arXiv 2507.18483", verified | 2025, verified | full arXiv text | **"MELBA" left unexpanded** (expansion not in stored file); co-authors omitted |
| `nlm_datasheet` | `results/baseline/dataset_source.json` | URL verified; title built from the dataset name in that file | "NIH/NLM", as used throughout the project | official datasheet URL, verified | — | archive + mappings hash-verified (M2 and M5) | the datasheet's own page title was not re-checked |

**How it was checked:** each title, venue string, volume, page/article
number and year in `references.bib` was compared character-for-character
with the "Full title", "Venue" and header lines of the stored file. Numbers
quoted from these papers in `paper/main.tex` (e.g. MalariaNet's 97.06% →
95.61%) were checked against the "Results" section of the same stored file.
The Rajaraman Table 6 values come from `results/baseline/published_baseline.csv`.
