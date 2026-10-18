Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# REQ-T-11 reviewer record (LG-04 reviewer clause)

Date 2026-10-18, worktree `unit/U-V14` on main c0f4894, embodic version string 0.0.1 (`src/embodic/__init__.py` l.3),
run from the source tree (`PYTHONPATH=src`). Reviewer: Agent 4 (Independent Verificator), model claude-opus-5-5. The
unit brief U-V14 item (b) gives Agent 4 the reviewer role that `test_plan.md` §5.8.3 gave Agent 1.

Requirement REQ-T-11: "The UI shall not claim balance, torque or efficiency from geometry or phase angles alone."
Acceptance: "Wording scan and reviewer check." (`requirements.md` l.270). LG-04 is the wording scan; this record is the
reviewer check (`test_plan.md` l.490 and §5.8.3).

Allow-list read: `tests/static/lg_allowlist.toml`, SHA-256
`a19b5c80d3df464f5de27645b2b977133c61f2134ba1e1ace58077e7cc0e7164`, nine `claim` rules (l.74-143). A change to the file
makes this record stale (`test_plan.md` §5.8.3).

## Method

- Lever: `tests/independent/m7/v14_t11_review.py`, Agent 4's own word pattern (a word that starts with balanc, imbalanc,
  unbalanc, torque or efficien), not the product scanner. It prints every matching text in the three places of §5.8.3
  for the five packaged examples: the result cards (`result_rows`) with their "How was this computed" disclosure and the
  Torque-speed tab (`torque_speed_charts`), the equation guide (`equation_topic` of every equation), and the PDF report
  (`write_report_pdf`, text read with pypdf). For each torque and efficiency card it also prints the Inputs section of
  the disclosure.
- Rerun: `QT_QPA_PLATFORM=offscreen PYTHONPATH=src python tests/independent/m7/v14_t11_review.py` (222 lines on c0f4894).
- I read every printed line. The view models are the text that the Qt views show; a desktop session is `not tested`.

## What the UI shows, read line by line

| Place | Text shown | Read | Status |
|---|---|---|---|
| Result cards, 5 examples | "Torque constant per line current, rms Kt", "Torque T", "Efficiency, electromagnetic only η", each with value, unit, status `not tested`, 17 to 40 assumptions and its EQ chain (EQ-09, EQ-06, EQ-07, EQ-05, and for efficiency EQ-26, EQ-10, EQ-11, EQ-12, EQ-19, EQ-23) | a computed quantity with its own status badge and assumption count | `verified` (read) |
| Disclosure Inputs of those cards | every torque and Kt card lists the magnet remanence, recoil permeability, magnet thickness, air gap and poles; the torque card adds the line current; the efficiency card adds current, speed, winding temperature and the copper constants | the value rests on magnet and drive inputs, not on geometry or phase angles alone | `verified` (read) |
| Disclosure Equation lines | "EQ-09: EMF/torque constants and star/delta conversion. Ke_ph = ..." and "EQ-26: Loss sum, efficiency and motor constant. ..." | the equation's name and formula | `verified` (read) |
| Torque-speed tab | serpentine and wave: charts "Torque" (N·m) and "Mechanical power" (W), status `unresolved`, 37 or 41 assumptions, EQ-20 chain; the three spiral examples: "The torque-speed estimate needs a DC-link voltage (Board and rotor, operating point)." | an estimate labelled `unresolved`, or a request for an input | `verified` (read) |
| Guide titles and names | "EQ-09 EMF/torque constants and star/delta conversion", "EQ-20 Torque-speed envelope (drive)", "EQ-26 Loss sum, efficiency and motor constant" | names of equations | `verified` (read) |
| Guide, EQ-05 validity checks | "EC-05 radial edge leakage (graded): ... one-sided tolerance add-on +e_edge (model high) on Ke, EMF, torque and EMF-derived results ..." | a rule that names the quantities a tolerance applies to | `verified` (read) |
| Guide, EQ-08 formula | "... balance = signed angle sets of B and C equal those of A shifted by 4Q and 8Q units" | see finding F-UV14-01 | `verified` (read) |
| PDF report, 5 examples | "Torque constant per line current, rms Kt 136 mN·m/A not tested", "Torque T 109 mN·m not tested", "Efficiency, electromagnetic only η 0.756 dimensionless not tested" (serpentine; the other four alike) | a report row with unit and status | `verified` (read) |

Admitted texts outside these three places, read in the source only: the self-test titles "Torque constant, star" and
"Torque constant, delta" (`selftest/catalogue.py` l.305 and l.315) name closed-form checks of `phase_constants` with
fixed inputs, not the user's design; the test node ID `...::test_cf09_patterns_and_balance` (l.235) and the export name
`TorqueSpeedEstimate` (`results/__init__.py` l.46) are identifiers; `resources/icons/ICONS.md` l.50 is icon
documentation. Whether the Tests dialog shows the node ID is `not tested`. The outcome JSON keys of rule l.130 are not a
view of the UI, and this record does not review them (`not tested`).

## Finding

F-UV14-01 (wording, advisory; owner Agent 2 with Fable, `test_plan.md` §5.8.9 item 4). The guide shows the formula of
EQ-08 with the word "balance" for a property computed from phase angles alone. In context it defines an equality of
angle sets inside a formula; it does not state that the user's design is balanced, and the design view calls the same
property "Symmetric 3-phase pattern." (`ui/strings/design.py` l.225). I read it as no claim (`inferred`, a reviewer's
judgement). Rewording it to "symmetry" would remove the last place where the UI ties "balance" to phase angles.

## Verdict

`passed`: no text that the results table, the Torque-speed tab, the equation guide or the PDF report shows claims
balance, torque or efficiency from geometry or phase angles alone. Every torque and efficiency value carries a status
of `not tested` or `unresolved`, its EQ chain and an assumption count, and its disclosure lists magnet and drive inputs
(`verified` by reading the printed views on c0f4894). The judgement that each text is not a claim is the reviewer's
(`inferred`). A reading on a desktop session is `not tested`.
