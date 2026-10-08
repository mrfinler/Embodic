Prepared by: Agent 5 (Research & Evidence Specialist), model: claude-opus-5-5. Rows EV-84 to EV-93 added in U-S3b (2026-10-08) by Agent 5, model: claude-sonnet-5-5.

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

## Rows added in U-S3b (2026-10-08)

Agent 5, model claude-sonnet-5-5. Sources were read on 2026-10-08. WebFetch returned a model-written extract of each web page, so those rows carry the `webfetch_extract` read method and the status `verified (extract)`. Direct downloads from physics.nist.gov and bipm.org were refused by the session's egress policy (proxy answer 403), and no workaround was used. EV-91 was read from the local PDF with `pdftotext`. Page numbers that came only from an extract are marked "not checked" in the location cell.

| EV-ID | Claim | Source | Location | Applies? | Status |
|---|---|---|---|---|---|
| EV-84 | Vacuum magnetic permeability µ0 = 1.256 637 061 27 × 10⁻⁶ N A⁻², standard uncertainty 0.000 000 000 20 × 10⁻⁶ N A⁻² (2022 CODATA adjustment; the table header names the adjustment) | NIST, *Fundamental Physical Constants, Complete Listing* | https://physics.nist.gov/cuu/Constants/Table/allascii.txt row "vacuum mag. permeability" | yes (value for the registry constant `vacuum_permeability_h_per_m`; the registry holds 4π × 10⁻⁷ H/m, relative difference 1.3e-10, 0.83 standard uncertainties, computed in U-S3b) | verified (extract) |
| EV-85 | Vacuum electric permittivity ε0 = 8.854 187 8188 × 10⁻¹² F m⁻¹, standard uncertainty 0.000 000 0014 × 10⁻¹² F m⁻¹ (2022 CODATA adjustment) | NIST, *Fundamental Physical Constants, Complete Listing* | https://physics.nist.gov/cuu/Constants/Table/allascii.txt row "vacuum electric permittivity" | yes (value for the registry constant `vacuum_permittivity_f_per_m`; the registry holds 8.854e-12 F/m, relative difference -2.1e-5, computed in U-S3b) | verified (extract) |
| EV-86 | After the redefinition of the ampere, "μ0 must be determined experimentally" (no longer exactly 4π × 10⁻⁷ H m⁻¹), ε0 is likewise determined experimentally, and "the product ε0μ0 = 1/c² and quotient Z0/μ0 = c remain exact" (quoted from the extract) | BIPM, SI Brochure 9th edition (file SI-Brochure-9-EN.pdf) | https://www.bipm.org/documents/20126/41483022/SI-Brochure-9-EN.pdf §2.3.1 "The ampere" (page number not checked) | yes (why 4π × 10⁻⁷ is an approximation; the passage read gives no numerical value for µ0 or ε0) | verified (extract) |
| EV-87 | Clearance-hole table "Bolt hole diameter dh" in mm for Grade 1 / 2 / 3, nominal thread diameter 2: 2.2 / 2.4 / 2.6; 3: 3.2 / 3.4 / 3.6; 4: 4.3 / 4.5 / 4.8; 5: 5.3 / 5.5 / 5.8; 6: 6.4 / 6.6 / 7. The page names JIS B 1001 and mentions ISO 273 only to say its Grade 4 sizes are "not specified in ISO 273". It has no 2.5 row and does not use the words fine, medium or coarse | NBK (manufacturer), *Technical data 20, Diameter of clearance holes and counterbores for bolts and screws*, published 2015-06-18 | https://alb02.internal.nbk1560.com/en/resources/other/article/technical-20-diameter-of-clearance-holes-and-counterbores-for-bolts-and-screws table, rows 2 to 6 | partly (a JIS B 1001 table, not the ISO 273 text; reading Grade 1 / 2 / 3 as fine / medium / coarse is inferred from order only; mounting-hole presets, G28) | verified (extract) |
| EV-88 | Metric clearance holes "according to ASME B18.2.8" as printed on a web page. Nominal drill size equals minimum hole diameter, close / normal / loose in mm: M2 2.2 / 2.4 / 2.6; M2.5 2.7 / 2.9 / 3.1; M3 3.2 / 3.4 / 3.6; M4 4.3 / 4.5 / 4.8; M5 5.3 / 5.5 / 5.8; M6 6.4 / 6.6 / 7. Maximum hole diameter close / normal / loose: M2 2.3 / 2.54 / 2.85; M2.5 2.8 / 3.04 / 3.4; M3 3.32 / 3.58 / 3.9; M4 4.42 / 4.68 / 5.1; M5 5.42 / 5.68 / 6.1; M6 6.55 / 6.82 / 7.36 | AmesWeb, *Metric Clearance Hole Chart* (cites ASME B18.2.8-1999) | https://amesweb.info/Screws/Metric-Clearance-Hole-Chart.aspx table | partly (ASME B18.2.8 as reproduced by a web page; its drill sizes for M2 to M6 equal the NBK Grade 1 / 2 / 3 values in EV-87; ISO 273 text not read; G28) | verified (extract) |
| EV-89 | Three-phase symmetry condition of a slot-pole combination: Z / (3 × GCD(Z, p)) must be an integer for a "conventional" combination (Eq. 15), where Z is the slot count and the machine has 2p poles. The introduction states the same rule in words (Z is an integer multiple of 3K, K the greatest common divisor of Z and p). The paper's main claim is that multi-layer windings can be symmetrical for unconventional combinations. The paper does not discuss parallel paths | A. Tessarolo, C. Ciriani, M. Bortolozzi, M. Mezzarobba, N. Barbini, *Investigation Into Multi-Layer Fractional-Slot Concentrated Windings With Unconventional Slot-Pole Combinations*, IEEE Trans. Energy Convers. 34(4) 1985-1996, 2019 | https://arts.units.it/bitstream/11368/2958612/4/2958612_IEEE%20TEC%202019-PostPrint.pdf §I; §IV Eq. (15) (page 5 of the post-print per the extract, not checked) | partly (EQ-08 feasibility Q/(3t) integer with t = gcd(Q, p); a journal paper, not a textbook; three phases only; the parallel-path rule is G30) | verified (extract) |
| EV-90 | Star of slots review: "Machine periodicity t = GCD (Q, p)"; number of spokes Q/t; the star is divided into 2·m sectors of 360/(2m) degrees; angle between spokes αph = 360·t/Q; a four-layer winding needs Q/t > 2m. The slides read give no balance condition and no parallel-path rule | L. Alberti, N. Bianchi, *Theory and Design of Fractional-Slot Multilayer Windings*, presentation, University of Padova | https://research.unipd.it/bitstream/11577/2514240/1/ECCE_2010_Multilayer_presentation_web.pdf slide 5, slide 12 | partly (supports the definition of t in EQ-08; a conference presentation, not a textbook; the extract names ECCE 2011, the file name says ECCE 2010, so the year is unresolved) | verified (extract) |
| EV-91 | Table 7 (p.8, "Test results of the windings under full load") lists THD in %: concentric 5.7, arc 2.8, parallel 5.2, radial 1.2, unequal width parallel 4.7. The text on p.6 gives 5.7 % (concentric), 1.3 % (radial), 5.2 % (parallel) and 2.9 % (arc) for the induced phase voltages. A search of the text layer of all 10 pages finds no definition of THD (harmonic range, fundamental or RMS reference, phase or line voltage) | D09 Tokgöz, Çakal, Keysan | B2/EPA-2020-0622-FINAL.pdf p.8 Table 7; p.6 §3.3 and §4 | yes (oracle value for EQ-18, concentric 5.7 %; the THD basis stays unresolved and the text and the table differ by 0.1 point for radial and arc; G31) | verified |
| EV-92 | Microchip application note for induction-motor V/f control: for space vector modulation "Equation 8 shows that it is possible to get line-to-line voltage amplitude as high as VDC"; the sine PWM linear-range line-to-line maximum is √3/2 × VDC (about 86.6 % of VDC, Appendix B); space vector modulation gives about 15 % more output voltage than sine PWM; six-step "can generate the line-to-line fundamental voltage more than the VDC" with no expression given (quoted from the extract) | R. Parekh, *VF Control of 3-Phase Induction Motor Using Space Vector Modulation*, AN955 (DS00955A), Microchip Technology, 2005 | https://mikrocontroller.net/attachment/337300/AN955.pdf "Time Calculation" Eq. 8; Appendix B (page numbers not checked) | partly (EQ-20 SPWM and SVPWM linear limits; a manufacturer note on induction motors, not a textbook; the six-step fundamental and PMSM pull-out torque are not covered; G33) | verified (extract) |
| EV-93 | Row "Density (ρ) g/cm3 7.4-7.7" in "Table IV Some Physical Properties of Sintered NdFeB Magnets" | HGT Advanced Magnets Co., Ltd, *Sintered NdFeB Magnets' Specifications* (manufacturer sheet) | https://www.advancedmagnets.com/wp-content/uploads/2020/07/Sintered-Neodymium-Iron-Boron-NdFeB-Magnets-Specifications.pdf Table IV (PDF page not determined) | yes (EQ-28 NdFeB density; the registry holds 7.5 g/cm³, inside the range; a class range from one manufacturer, not a grade; rotor steel density is G34) | verified (extract) |
