Prepared by: Agent 4 - Independent Verificator - model: claude-opus-5-5

# LG-01 word review (REQ-L-01 manual record)

Date 2026-10-18, worktree `unit/U-V13` on main 260191f, embodic 0.0.1 (`src/embodic/__init__.py` l.3). Reviewer:
Agent 4 (Independent Verificator), model claude-opus-5-5. Requirement REQ-L-01 (amended by U-D20) and test plan row
LG-01 (`docs/phase2/architecture/test_plan.md` l.488).

## Method

- LG-01 is to print the sorted distinct words of the string catalogues and the report templates (test plan l.488).
  On main 260191f no function or command prints that list: `tests/static/test_lg_language.py` and
  `tests/static/lg_scan.py` hold no word lister (`verified` by reading both files and by a search of tests, tools
  and src for a word-list function). This is DEF-UV13-01.
- I read my own list instead: `python3 -I tests/independent/m7/l01_words.py`. Corpus: every string constant of
  `src/embodic/ui/strings` (6 files), `src/embodic/errors/catalogue` (13 files), `src/embodic/io/report.py` and
  `src/embodic/io/readme_writer.py`, without docstrings and without the keys of a catalogue mapping. Format fields such
  as `{value}` are dropped, camelCase runs are split, words are lowered.
- Output: 804 distinct words in 21 files. SHA-256 of the list (one word per line, newline-terminated):
  `d709979e2864db6f2ab43fe73068736d9a9038d075261b5651fc319e27ba8bc0`. `--sources` names the first file of each word.
- I read every word of the list below and looked up the source text of each token that is not a dictionary word.

## Tokens that are not dictionary words (all English usage)

- English technical abbreviations and file formats: ccw, cli, cw, dc, drc, dxf, emf, eq, gcd, ic, id, json, lcr, mm,
  oz, pcb, pdf, ph, rms, rpm, spwm, svg, svpwm, txt, utf, zip. `ic`, `cu` and `ph` come from the DXF layer-name
  pattern `CU<n>_<layer>_PH_<phase>` and `_IC` (readme_writer.py l.46-47).
- Key names: alt, ctrl, esc.
- Unit and quantity symbols: single letters (b, c, d, e, f, h, k, l, m, n, o, p, q, r, s, t, u, v, w, x, y, z), cu,
  mu (the ASCII spelling in "Recoil permeability mu_r"), µm, m².
- Proper nouns: embodic (the product), Inter, JetBrains Mono (split into jet and brains) and SIL (the font colophon,
  report.py l.56).
- Not prose: `ffffff` is a colour value (report.py l.48-49); `rg`, `j`, `w` and `n` also occur as PDF content-stream
  operators in report.py (l.220). They are not text a user reads.

## Verdict

`passed`: the list holds no word that is not English. Status `verified` by reading the list; it covers the corpus named
above only. The product's own LG-01 printer does not exist (DEF-UV13-01), so this record does not show that LG-01
prints the same list.

## The list

```
a about above accuracy across active add added after again air all allow alt alternate although ambient an analysis
analytical and angle annular another any anyway apart appear appearance appears apply arc archive are armature as
asks assignment assumption assumptions at attached auto available axis b back badge badges be because before behind
belong below belt beside between blank block board boards bore bound brains breaks browse build built bundle bus by
c calibrates calibration can cancel cannot canvas cap caps carries carry case caveat ccw centre centred chained
change changed changes character chart charts check checked checks choice choose chord circle circulating cites
classified clearance clearances cli click close closed closer coefficient coil coils colder collapse colour comes
command commands compare compares complete computation compute computed computes computing concentrated conductors
confirm connection constant constants continuous contrast convection cooling coordinates copied copper copy corner
corners count counted coupon create creation cross crosshair crossing ctrl cu current custom cut cutout cw d dark
dashed data datasheet date dc decrease default defined degrees delta depth derived describing design details dialog
diameter did dielectric different dimensional dimensionless disagrees discard distortion divide do does dominant
done double down drawing drawings drawn drc drill drive drives dropped duration dxf e each eddy edge edit effects
electrical else embodic emf empty end ends enter entered entries entry epsilon eq equation equations error errors
esc estimate estimates even every evidence exactly example examples exceed exceeds exist exists expected export
exported externally extra f face factor facts failed fails failure failures fall fan fasteners fewer ffffff field
fields figures file files fillet fillets finite first fit fits fix flats focused folder follow follows font for
form format formula four frame frequency from fundamental gap gate gcd generation generator geometry getting given
global glyph go greater grey greyscale group grouped groups guide h half harmonic has hatching have heated help
here high holds hole holes home how ic id illustrative implementation in incomplete increase independent index
inner innermost input inputs inside inspector installation instead inter interconnect interleaved internal into
invalid involute inward iron is issue issues it its j jet jog joined joins json k keeps kept key keyboard keys kind
known l label labels larger last later layer layers layout lcr least leaves left length levels license light limit
limitations limited line lines link linked links list listed lists load loaded locate log look loose lose loss
lower m machine magnet magnets make makes manual manufacturing mark marked match material maximum may means
measured measurement mechanical menu message method micrometres millimetres minimum missing mm mode model
modulation mono more most mount move mu must m² n name named names narrower need needs negative nested neutral
never new newer next no none normal not note notes nothing number numbers o odd of offset on once one only open
opened opens operating option options or oracles order ordering orders other out outdated outer outline output outs
outside overlap overlapping own oz p packaged pad pads page pair pairs parallel parameter partner pass passed past
paths pattern pcb pdf peak per periodicity permeability ph phase phases phasor physics pitch pitches place planar
plating point pointers polarity pole poles polygon position positions positive power press previous producer
program project property prose provenance q quantity r radial radii radius range ratio reaches reaction read readme
reads ready reasoning recoil record recorded records recover redo reduce reference refers region register registry
relative remanence remove removed repeat replace replaced report reported reproduced reproduces requested required
resistance result results returns revert rg ribbon right rim ring rms roles room rotated rotation rotor round
rounded routed rpm rule run running s same sample save saved saving says screw screws see selected self
semicircular sense sequence series serpentine set sets settings shaft shape shift short shortcuts show showing
shown shows side sides sil simulation single six size skin slots small smaller so solid something source sources
spaced spacing span speed spiral spread spwm stack stadium stamp star start started starts state stator status step
stop stopped stored straight strands string style such summary sums supported supports surface surroundings svg
svpwm switch symmetric system t table tabs taken team temperature terminal terminals test tests text than that the
them theme then there they thicker thickness third this three threshold through title to tolerance too tool topic
topics topology torque total trace traceback traces tracks transfer transition true trust turn turns twice two txt
type u uncommitted undo undone unit units unresolved unsaved up updating upgraded upper use used user uses utf v
valid validation validity value values vector verified version versions via vias view violation violations
vocabulary voltage w warning warnings was wave weakest weight were when while whole why wide wider width will
winding windows with without word worst write written x y yet yoke you your yours z zero zip µm
```
