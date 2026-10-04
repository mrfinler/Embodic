Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5

# Evidence register: JSON fields and UI citation (Phase 2)

`evidence_register.json` is the machine-readable evidence register that the application ships. The architecture
places it at `embodic/results/data/evidence.v1.json` (`docs/phase1/architecture/architecture_draft.md` §13). Do not edit
the JSON by hand. Regenerate it from the repository root:

```
python3 docs/phase2/evidence/tools/build_evidence_register.py
```

The script reads three files: the Phase 1 register (`docs/phase1/evidence/evidence_register.md`, rows EV-01…EV-79,
EV-R1…R5 and EV-K1…K6), the table at the end of this file (rows added in Phase 2), and the equation registry draft
(`docs/phase1/engineering/equation_registry_draft.json`, for `related_equations`). It stops without writing when a row
falls outside a mapping rule, when an EV id that the equation registry cites is missing, or when Thai text appears.

## Top-level keys

| Key | Meaning |
|---|---|
| `prepared_by` | Author and self-reported model id. |
| `schema`, `schema_version` | `"embodic evidence register"`, `1`. |
| `generated_by`, `generated_from` | Generator path, and the SHA-256 of each input file. No git commit exists for a document agent, so the digest replaces the `@<git commit>` of §13. |
| `status_vocabulary`, `status_order_weakest_first` | The five labels from the standing orders, and their order from weakest to strongest (same order as the equation registry). |
| `topology_vocabulary` | Allowed `topology_tags` with a one-line meaning each. |
| `kind_vocabulary`, `citable_rule` | Row kinds, and the rule that computes `citable`. |
| `documents` | One object per source: `id`, `title`, `authors`, `year` (integer or null), `year_text`, `venue`, `kind`, `path` (local corpus file, B1/B2 aliases as in the Phase 1 register), `url`. |
| `entries` | One object per EV row. |

## Entry fields

| Field | Type | Meaning |
|---|---|---|
| `id` | string | `EV-nn`, `EV-Rn` (repository) or `EV-Kn` (KiCad). Stable. Never reused. |
| `claim` | string | The claim or equation as written in the register. |
| `kind` | enum | `source_claim`, `repository_fact`, `bibliographic_record` (record verified, content not accessed), `marketing_claim`, or `illustration`. |
| `source` | object | `document`, `title`, `authors`, `year`, `year_text` of the first listed document, copied in so the UI needs no join for the common case. |
| `documents` | list | All document ids the row cites. EV-23, EV-34 and EV-63 cite two. |
| `location` | object | `text` (the register's location cell, verbatim), `pages_pdf` (1-based PDF page indices parsed from `p.N` and `p.N–M`), `pages_printed` (printed page or journal page, string or null), `urls`. |
| `read_method` | enum | `text` (PDF text extraction), `img` (read from the rendered page), `webfetch_extract` (read through the WebFetch tool's extract, not the raw file), `parse` (own parser on repository files), `source_read`, `image_view`. |
| `applies` | object | `judgement` (`yes`, `partly`, `no`), `note` (the register's applicability cell), `status` (always `inferred`). |
| `status` | enum | Exactly one label. It says whether Agent 5 read the claim in the source. It never means physical correctness or experimental confirmation. |
| `status_note` | string | The full Phase 1 status cell, with its qualifiers. |
| `topology_tags` | list | Topologies the claim concerns. `general` means topology-independent. `non_engineering` marks licences, UI conventions and file formats. |
| `phase2_scope`, `out_of_scope_reason` | bool, string | `false` for KiCad rows (EV-79, EV-R4, EV-K1…K6) after D-009. They stay for traceability. |
| `citable` | bool | `true` only for `source_claim` and `repository_fact` rows inside Phase 2 scope. |
| `related_equations` | list | EQ ids whose `sources` list this EV id. Computed from the equation registry draft. |
| `related_gaps` | list | Gap ids (G-numbers of `docs/phase1/evidence/evidence_gaps.md` and `source_gaps_phase2.md`) named in the row. |
| `register_origin`, `accessed` | string | `phase1` or `phase2`, and the access date. |

## How the status label is derived

Phase 1 status cells carry qualifiers such as "verified (as printed); correction inferred". The script reduces each
cell to one label. The weakest vocabulary word in the cell wins. "not accessed" and "marketing" count as
`unresolved`. Fourteen rows end below `verified`. Six of them have a cell that starts with "verified" and still
drop: EV-07 and EV-31 carry an inferred correction, EV-09 an inferred formula reading, EV-55 a derived 1.10, EV-71 an
inferred interpretation, and EV-R5 an inferred judgement. EV-60, EV-63 and EV-78 are `unresolved` because their
content was not accessed. EV-62 is `unresolved` because the turn count is unknown. The original cell stays in
`status_note`.

## How the UI cites an EV id

1. A result's traceability chain lists EQ ids. Each EQ entry lists EV ids in `sources`.
2. For each EV id, the UI looks up the entry by `id`. A missing id is a build defect, because CI check TR-04 requires
   every EV id cited by the equation registry to exist here.
3. The UI shows an entry as support only when `citable` is `true`. Rows with `citable: false` appear under a
   separate "Not evidence or not accessed" heading with their `kind`. A `marketing_claim` row is never shown as
   support.
4. The citation line is: `EV-08 · Collijs & Vereecken (2020–2021) · p.45 · verified`. Build it from `id`,
   `source.authors`, `source.year_text`, `location.text` (or `pages_pdf`), and `status`. The tooltip shows `claim`,
   `applies.judgement` with `applies.note`, and `status_note`.
5. The UI shows the evidence `status` next to the citation. It does not feed the result badge directly. The badge
   follows D-007 through the EQ status and the test state.
6. When a result depends on a gap listed in `source_gaps_phase2.md`, the UI adds that gap to the result's
   assumptions tag, with the value and label given there.

## Rows added in Phase 2

Sources were accessed on 2026-10-04 through the WebFetch tool. The session's egress policy refused direct downloads
(`curl`) from arnoldmagnetics.com, advancedmagnets.com, mit.edu and uark.edu (proxy answer 403). No raw PDF was read,
so every row below has the `webfetch_extract` read method.

| EV-ID | Claim | Source | Location | Applies? | Status |
|---|---|---|---|---|---|
| EV-80 | Sintered NdFeB recoil permeability µrec = 1.05, listed in "Table IV Some Physical Properties of Sintered NdFeB Magnets"; no revision or date printed (closes the datasheet part of G23) | HGT Advanced Magnets Co., Ltd, *Sintered NdFeB Magnets' Specifications* (manufacturer sheet) | https://www.advancedmagnets.com/wp-content/uploads/2020/07/Sintered-Neodymium-Iron-Boron-NdFeB-Magnets-Specifications.pdf Table IV | yes (µ_r input of EQ-05 for sintered grades); one typical value, not grade-specific | verified (extract) |
| EV-81 | "Typical values of Recoil Permeability are about 1.05 for sintered Ferrite, SmCo and NdFeB"; "Bonded Neo magnets range from about 1.1 to 1.7, depending upon grade"; one example material quoted with recoil permeability 1.04 | S. Constantinides, D. Gulick (Arnold Magnetic Technologies), *NdFeB for High Temperature Motor Applications*, SMMA Fall Technical Conference, 3–5 Nov 2004 | https://www.arnoldmagnetics.com/wp-content/uploads/2017/10/NdFeB-for-high-temperature-motor-applications.pdf slide 13; slide 25 (1.04) | yes (cross-check of EV-80); bonded magnets need a different value (G23) | verified (extract) |
| EV-82 | Trace current capacity attributed to IPC-2221: Area[mil²] = (I / (k·ΔT^b))^(1/c), with k = 0.024, b = 0.44, c = 0.725 for internal layers and k = 0.048, b = 0.44, c = 0.725 for external layers; Width[mil] = Area / (Thickness[oz] × 1.378 mil/oz) | T. Aldawsari, MSc thesis, University of Arkansas, December 2014 | https://scholarworks.uark.edu/cgi/viewcontent.cgi?article=3596&context=etd p.38–39 (thesis page numbers from the extract) | yes (EQ-15 coefficients); secondary statement, the standard's own text not read (G5) | verified (extract) |
| EV-83 | Bittele Electronics states the formulas are "published in the IPC-2221 standard section 6.2": internal I = 0.024·dT^0.44·A^0.725, external I = 0.048·dT^0.44·A^0.725, A in mil², dT in °C above ambient; same width conversion 1.378 mil/oz | Bittele Electronics (PCB manufacturer), *Trace Width Calculator* page | https://www.7pcb.com/trace-width-calculator | yes (independent cross-check of EV-82); manufacturer web page, not an application note; validity range not quoted | verified (extract) |
