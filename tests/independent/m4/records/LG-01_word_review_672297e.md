Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# LG-01 word review redone for 0.0.6 on candidate 672297e (REQ-L-01 manual record)

Date 2026-10-21 UTC, unit U-V28, worktree `unit/U-V28`, whose `src/` equals the 0.0.6 candidate main 672297e (the unit
changes only `tests/independent` and `docs/phase3/verification`). embodic 0.0.6 (`src/embodic/__init__.py` l.3). The
21 corpus files are byte-identical to their members in Agent 4's candidate wheel ad9e02c0 of 672297e (`verified`, a
zip read of each member). Reviewer: Agent 4 (Independent Verificator), model claude-opus-5-5. Requirement REQ-L-01 and
test plan row LG-01.

## Why it is redone

D-061d: the record `LG-01_word_review_6d50d0b.md` names the source of 6d50d0b. Its corpus is `src/embodic/ui/strings`,
`src/embodic/errors/catalogue`, `src/embodic/io/report.py` and `src/embodic/io/readme_writer.py`. `git diff --stat
6d50d0b 672297e -- <those four paths>` gives `1 file changed, 2 insertions(+), 2 deletions(-)`: two rows of the guide's
`KEYBOARD_MAP` in `src/embodic/ui/strings/results.py` (U-M9e, D-094b). The row "F1, Ctrl+/, Ctrl+," / "Guide,
Shortcuts, Settings" became "F1, Ctrl+/" / "Guide, Shortcuts", and "Inspector tabs Coil, Phases, Layers, Board and
rotor" became "Inspector tabs Coil, Phases, Layers, Board". The record therefore does not stand for 672297e
(`tests/independent/m7/v14_record_currency.py --target 672297e`, entry 4).

## Method

The method of the earlier records, unchanged. `python3 -I tests/independent/m7/l01_words.py` (Agent 4's own lister,
which reads the corpus with `ast` and never imports it) prints the sorted distinct words. I ran the product printer
`python tests/static/lg_scan.py` too, as a cross-check.

- Output: 805 distinct words in 21 files. SHA-256 of the list (one word per line, newline-terminated):
  `a1d7a7677c80eec2722feb3ecce03a4110a84ac2e0bc461ff76b512ca8a5f170` (`verified` by running).
- The same lister on `git archive 6d50d0b src` prints 806 words with SHA-256
  `d8e28ff983b1b201ab92f8752e9e21cd74db4e5875b2aad592656d3e52b851c5`, the value of the 6d50d0b record, so the lever
  reproduces the old list (`verified`).
- Against those 806 words: one word removed, `settings`, none added (`verified`, `diff`). No other string of the
  corpus holds it. `rotor` and `and` stay in the list through other strings.
- The product printer `tests/static/lg_scan.py` prints the same 805 words in the same order (`diff`, empty).
- I read the two changed rows. They are plain English, and every word of them was in the list the 6d50d0b record
  classified.

## Verdict

`passed` for 0.0.6 on candidate 672297e: the list holds no word that is not English. Status `verified` by reading the
list against the 6d50d0b record. It covers the corpus named above only.

## Rerun

```
python3 -I tests/independent/m7/l01_words.py | sha256sum    # a1d7a767...f170
```

## The list

```
a about above accuracy across active add added after again air all allow alt alternate although ambient an analysis
analytical and angle annular another any anyway apart appear appearance appears apply arc archive are armature as asks
assignment assumption assumptions at attached auto available axis b back badge badges be because before behind belong
below belt beside between blank block board boards bore bound brains breaks browse build built bundle bus by c
calibrates calibration can cancel cannot canvas cap caps carries carry case caveat ccw centre centred chained change
changed changes character chart charts check checked checks choice choose chord circle circulating cites classified
clearance clearances cli click close closed closer coefficient coil coils colder collapse colour comes command
commands compare compares complete computation compute computed computes computing concentrated conductors confirm
connection constant constants continuous contrast convection cooling coordinates copied copper copy corner corners
count counted coupon create creation cross crosshair crossing ctrl cu current custom cut cutout cw d dark dashed data
datasheet date dc decrease default defined degrees delta depth derived describing design details dialog diameter did
dielectric different dimensional dimensionless disagrees discard distortion divide do does dominant done double down
drawing drawings drawn drc drill drive drives dropped duration dxf e each eddy edge edit effects electrical else
embodic emf empty end ends enter entered entries entry epsilon eq equation equations error errors esc estimate
estimates even every evidence exactly example examples exceed exceeds exist exists expected export exported externally
extra f face factor facts failed fails failure failures fall fan fasteners fewer ffffff field fields figures file
files fillet fillets finite first fit fits fix flats focused folder follow follows font for form format formula four
frame frequency from fundamental gap gate gcd generation generator geometry getting given global glyph go greater grey
greyscale group grouped groups guide h half harmonic has hatching have heated help here high holds hole holes home how
ic id illustrative implementation in incomplete increase independent index inner innermost input inputs inside
inspector installation instead inter interconnect interleaved internal into invalid involute inward iron is issue
issues it its j jet jog joined joins json k keeps kept key keyboard keys kind known l label labels larger last later
layer layers layout lcr least leaves left length levels license light limit limitations limited line lines link linked
links list listed lists load loaded locate log look loose lose loss lower m machine magnet magnets make makes manual
manufacturing mark marked match material maximum may means measured measurement mechanical menu message method
micrometres millimetres minimum missing mm mode model modulation mono more most mount move mu must m² n name named
names narrower need needs negative nested neutral never new newer next no none normal not note notes nothing number
numbers o odd of offset on once one only open opened opens operating option options or oracles order ordering orders
other out outdated outer outline output outs outside overlap overlapping own oz p packaged pad pads page pair pairs
parallel parameter partner pass passed past paths pattern pcb pdf peak per periodicity permeability ph phase phases
phasor physics pitch pitches place planar plating point pointers polarity pole poles polygon position positions
positive power press previous producer program project property prose provenance q quantity r radial radii radius
range ratio reaches reaction read readme reads ready reasoning recoil record recorded records recover redo reduce
reference refers region register registry relative remanence remove removed repeat replace replaced report reported
reproduced reproduces requested required resistance result results returns revert rg ribbon right rim ring rms roles
room rotated rotation rotor round rounded routed rpm rule run running s same sample save saved saving says screw
screws see selected self semicircular sense sequence series serpentine set sets shaft shape shift short shortcuts show
showing shown shows side sides sil simulation single six size skin slots small smaller so solid something source
sources spaced spacing span speed spiral spread spwm stack stadium stamp star start started starts state stator status
step stop stopped stored straight strands string style such summary sums supported supports surface surroundings svg
svpwm switch symmetric system t tab table tabs taken team temperature terminal terminals test tests text than that the
them theme then there they thicker thickness third this three threshold through title to tolerance too tool top topic
topics topology torque total trace traceback traces tracks transfer transition true trust turn turns twice two txt
type u uncommitted undo undone unit units unresolved unsaved up updating upgraded upper use used user uses utf v valid
validation validity value values vector verified version versions via vias view violation violations vocabulary
voltage w warning warnings was wave weakest weight were when while whole why wide wider width will winding windows
with without word worst write written x y yet yoke you your yours z zero zip µm
```
