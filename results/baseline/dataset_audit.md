# Official NIH/NLM dataset audit

**Status:** PASS

The audited release is NLM-Falciparum-Thin-Cell-Images from the official NLM
Malaria Screener datasheet. The archive SHA-256 is
`0a949556b2414159b5100192609805376654c4266d8d187be9b1922fad43c668`. Retrieval URLs and all three SHA-256 values are
in `dataset_source.json`.

| Check | Result |
|---|---:|
| PNG images | 27558 (expected 27558) |
| Parasitized | 13779 (expected 13779) |
| Uninfected | 13779 (expected 13779) |
| Official mapping entries: Parasitized / Uninfected | 151 / 201 |
| Unique official mapping IDs across all cells | 201 |
| Cells missing an official mapping ID | 0 |
| Corrupt PNGs | 0 |
| Mapping references to absent images | 0 |
| Images absent from mappings | 0 |
| Duplicate mapping assignments | 0 |
| Byte-identical duplicate sets | 0 |
| Cross-label duplicate sets | 0 |

Directory structure is `cell_images/Parasitized/*.png` and
`cell_images/Uninfected/*.png`. Observed decoded image dimensions are recorded
in `dataset_audit.json`.

## Patient/cell mapping decision

The grouping field is the **exact Patient-ID key in the official NLM mapping
CSV**, not a randomly created or filename-inferred ID. The official datasheet
states that these CSV files map Patient IDs to cells; it also notes 151
Parasitized mapping entries (one source patient has images from two microscope
models) and 201 Uninfected entries because normal cells from infected slides
also appear in that class. The supplied paper1/M1 narrative describes 150
infected plus 50 healthy patients. These are not treated as a claim that the
archive has 200 unique mapping keys or that its IDs reproduce the paper's
unpublished five fold assignments. `patient_cell_mapping_summary.csv` is the
auditable mapping used for the grouped split.

## Files

- `dataset_manifest.csv`: one row per verified PNG, label, official Patient-ID,
  and content hash.
- `patient_cell_mapping_summary.csv`: cells per official Patient-ID and class.
- `dataset_mapping_issues.csv`, `corrupt_images.csv`, `duplicate_images.csv`:
  audit exceptions (empty files mean no exceptions of that type).
