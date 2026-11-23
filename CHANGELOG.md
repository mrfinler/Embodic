# Changelog

All notable changes to embodic are listed here. Versions follow semantic versioning; dates are ISO 8601.

## Unreleased

### Fixed

- Opening another design clears the previous drawing and discards any result still in flight for it.
- An export uses the design shown in the export checklist and design rule confirmation, even when a new result
  arrives while the dialog is open.
- Standalone and bundled project exports retain example provenance for edited designs when the packaged example still
  matches the recorded source.
- The CLI and compute API report malformed project provenance as a validation issue. The compute API also reports
  non-finite design inputs and represents them in result JSON.
- Cached analysis uses the current test evidence when determining result badges.

### Documentation

- The install guide and its Thai version say what to do when Windows reports "An Application Control policy has
  blocked this file" for `embodic-cli.exe` or `embodic.exe`: start embodic with `python -m embodic.cli` or
  `python -m embodic.ui.app` (DEF-W-16, D-098, D-100). The release files are unchanged.

## 0.0.6 - 2026-10-22

This release fixes what the preparation of Phase 4 found on 0.0.5 (D-093, D-094). It changes no computed value: the
outcome of each packaged example equals that of 0.0.5 except the version fields.

### Fixed

- Copper weight and Board thickness, in the Board tab group "Stack-up and manufacturing", showed their unit only as
  placeholder text and gave a screen reader no unit. They now show the unit beside the value and announce it, as the
  other inputs do (REQ-N-24). (DEF-US17-01, D-094a)
- The guide listed five shortcuts that did nothing. Ctrl+Shift+S, Ctrl+Shift+Z, Ctrl+P and Ctrl+/ are now bound to the
  actions the guide names. Ctrl+, is removed from the guide and from the design's keyboard map, because there is no
  settings window. A test now fails if the guide lists a key that nothing binds. (DEF-US17-02, D-094b)
- The torque-speed message pointed to "Board and rotor", a place that does not exist. It now reads "(Board tab, Drive
  group)", and the guide's Alt+1..4 row names the Board tab. (DEF-US17-03, D-094)

### Changed

- The release trace gate (TR-01) lists every manual record that did not pass. Such a record fails the gate unless it
  names the decision that accepts it, and an accepted record never counts as coverage. The PF-01 record of the laptop
  is accepted by D-091. (DEF-UV21-01, D-093c)
- Version 0.0.6. The five packaged examples change only in `app_version` and `engine_version`.

### Known limits

- The canvas keys L, G, C, M, T, A, B and Shift+C of the design's keyboard map do nothing; F and F5 work but are not
  listed. The user decides at acceptance whether they are built or taken out of the map. (DEF-US18-01)
- The known limits of 0.0.5 still apply: DEF-W-12, DEF-W-14, DEF-W-15 (REQ-N-01 on the reference laptop) and the three
  licence items.

## 0.0.5 - 2026-10-21

This release closes the Phase 3 gaps that the 0.0.4 audit and the Windows run of 0.0.4 found (D-082 to D-086). It
changes no computed value: the outcome of each packaged example equals that of 0.0.4 except the version fields.

### Fixed

- Two physics methods lacked the documentation REQ-N-09 asks for, an equation identifier and every parameter with its
  unit: `FieldTable.at` (EQ-05) and `InterconnectResistance.total_ohm` (EQ-23). The MT-04 check now covers methods; it
  does not cover Protocol members. (U-D26, D-084a)
- On Windows, Git's default `core.autocrlf=true` checked the repository's text files out with CRLF, because the
  repository had no `.gitattributes`. The byte checks of the packaged examples then failed in a Windows checkout. Every
  text file is now checked out with LF on every platform, and a static test keeps the rule. A checkout made before this
  release keeps its CRLF files until they are checked out again. (DEF-W-13, D-086b)

### Changed

- The release trace gate (TR-01) counts a manual record only when the record names the version under test, matched as
  a whole version and read from the source tree. A record of an older build is listed as stale. (D-083c, D-084a)
- Sixteen tests now carry the identifier of the planned criterion they check, and sixteen tests are added for criteria
  that no test checked, as the Phase 3 audit specified (U-V19, U-D26, D-046c). The self-test catalogue follows the
  renamed DRC test.
- Version 0.0.5. The five packaged examples change only in `app_version` and `engine_version`.

### Known limits

- Windows GUI latency (DEF-W-12) stays open and belongs to Phase 5. The failures come and go and cluster after long
  runs. In a same-session comparison on the test laptop, the layer cue of 0.0.4 showed no measurable latency cost: ten
  runs passed, with the N02-10 arrival gap at a median of 40 ms without the cue and 41 ms with it. (D-086d)
- Windows Application Control on the test laptop blocked the unsigned PyInstaller bundle that was built there
  (`WinError 4551`). Where such a policy is on, the bundle cannot start until it is code-signed, and signing is not set
  up. (DEF-W-14, D-086c)
- Three licence items are open: the written offer for the Qt and PySide6 source, the Qt third-party notices, and the
  licence of embodic itself. (D-069, D-081)
- The known limits of 0.0.4 that this release does not fix still apply.

## 0.0.4 - 2026-10-20

This release carries wave F13 (D-078, D-079). Version 0.0.3 was built and tested but not released (D-078f). Its
changes, listed under 0.0.3 below, ship in this release. A DEF identifier names a defect row of
`tests/independent/m7/records/defects.md`. Two entries below were corrected on main after the tag (D-083); the tag
`v0.0.4` keeps the first text.

### Fixed

- The DRC could pass copper that is too close to a coil turn. Rule 5 exempted a path end from every primitive of the
  same-net path it lands on. A leg that starts on a coil's end point was therefore never checked against the coil's
  other turns: a leg 0.700 mm from the next turn passed at a 0.8 mm rule. A path end is now exempt only from the
  primitive it lands on, with that primitive's fillets and tapers, and an end on an end is a rule 3 node. The
  interconnect tap of rule 2 is exempt per primitive as well. On the five packaged examples, the violation counts stay
  0, 0, 0, 0 and 186. A behaviour change follows: a T joint or a tap via that lands near a sharp corner is now reported
  against the primitive past the corner, and a fillet at the corner removes the report. (DEF-UV16-01, U-D25, D-078c,
  D-079b)
- A path that starts with a fillet or a taper was exempt from its second main primitive (DRC rule 1). The leading corner
  piece now belongs to the first main primitive only. (DEF-UD25-01, D-079b)
- The geometry view drew every copper layer opaque in one colour per phase, so copper on different layers looked joined.
  A user read the D08 spiral as shorted, but on each layer every gap was at the 0.8 mm rule. While two or more copper
  layers are visible, the top visible layer is now drawn solid. Each lower layer is drawn as an outline inside its true
  edge, and each upper layer has a casing in the board colour. The legend names the top layer. The cue is also drawn
  in the greyscale drawing that the app uses under Windows high contrast. That drawing was tested offscreen on Linux;
  Windows high contrast itself was not run. (DEF-UV16-02, U-S16, D-079c)
- Round pads were drawn as squares. Each pad is now drawn from its shape, as the exporters write it. (DEF-UV16-03)

### Changed

- Version 0.0.4. The five packaged examples change only in `app_version` and `engine_version`.

### Known limits

- The layer cue adds drawing work. Offscreen on the Linux container, against the 0.0.3 view (median ratios over 11
  rounds), the serpentine redraw takes 1.25 times as long and the D08 open 1.13 times. A zoom step takes 1.70 times as
  long and a pan step at 4x zoom 1.50 times (26 to 28 ms). An idle repaint takes 0.25 times as long, because the cue is
  cached. Windows is not measured. (D-080)
- Via drills are not drawn in the geometry view. This belongs to Phase 5. (D-079c)
- The Windows GUI latency of 0.0.3 (DEF-W-12) stays open.

## 0.0.3 - not released (built and tested on 2026-10-19 and 2026-10-20)

This version carries wave F12 (D-071). A reference such as D-071c is a clause of `docs/decision_log.md`. A DEF
identifier names a defect row of the U-V15 records.

### Changed

- The five packaged examples are regenerated with `tools/sync_registry.py`. `app_version` and `engine_version` read
  `0.0.3`. (D-071d)
- The serpentine properties PR-13 and PR-14 run 3 examples in the commit profile and up to 25 in the nightly and
  release profiles, scaled with the profile. Each example builds a board and a brute DRC sweep, about 13 s. (DEF-UV15-03,
  D-071c)
- Boundary tests join the suite: a clearance of exactly rule minus epsilon passes and one 8.9e-17 mm closer fails
  (UT-DRC-03, D-006), a same-net via exactly pad_mm / 2 off the centreline is exempt (UT-DRC-04, rule 2b), and an SVG
  joint whose ends differ by less than 1e-6 mm across a rounding step is written once from the shared coordinate
  (REQ-N-21). (DEF-UV15-01, DEF-UV15-02, V3-05-01, D-071c)
- The nightly and release profiles run the GUI latency tests (marker `latency`) in a pytest process of their own after
  the main gate, and `tools/trace_matrix.py` merges the REQ reports of both processes. The 100 ms bound and the method
  are unchanged. (D-074)
- The golden freshness tests compare every byte of a fixture except `producer.runtime`, whose major line must match
  (`node v22.`). Values, the engine sha256 and the producer name stay exact. (D-075)

### Fixed

- An angle in radians whose degree value is not finite made `compute` raise `ValueError` from the design hash instead of
  returning an issue (REQ-F-14, PR-05). Validation now refuses such an angle on every angle field before any
  conversion. (DEF-UV15-04, D-071c)
- Two designs that compare equal gave different design hashes when one held a negative zero (for example
  `first_coil_angle_rad = -0.0`), because the file form wrote "-0.0" (REQ-F-15, PR-08; found by the Windows release run
  of 0.0.2). The file form and the hash bytes now write every negative zero as 0.0. (D-073)
- The cancel test of DEF-U-M8n-01 could measure the first job twice when two builds finished close together, and so
  failed on Windows with two equal timings. Each build in the test now waits for its own job. (D-076b)

### Known limits

- Windows GUI latency (DEF-W-12, major). The Windows release run of `5f814d4` passed the main pytest gate (4198 passed,
  90 skipped, 3 xfailed) and failed 2 of 6 tests of the separate latency gate. In ten runs of the latency tests alone
  on the laptop, UI-05 took more than 100 ms in 1 of 10 runs and the N02-10 arrival case in 4 of 10 (up to 218 ms).
  On Linux all pass. REQ-N-02 on Windows is `partial`. The cause is `inferred`: the compute worker and the GUI thread
  share the GIL. The fix belongs to Phase 5, and the 100 ms bound stays. (D-076)
- The known limits of 0.0.2 that this release does not fix still apply.

## 0.0.2 - 2026-10-18

This release carries the fixes of Phase 3 (D-048 to D-063). A reference such as D-056b is a row of
`docs/decision_log.md`. A DEF- identifier is a defect row of the Phase 3 documents.

### Added

- Project file schema version 2. A saved project carries `engine_version` (the embodic version) and `registry_version`.
  A version 1 file migrates on load with both keys null. (D-056b)
- `tools/sync_registry.py` rewrites the five packaged examples after a registry change, and `--check` names each example
  that differs from the generator output. (D-056b)
- Version stamp on the geometry view. The canvas shows the embodic version and 12 hex digits of the design hash at the
  bottom left and ends its accessible description with them. (REQ-T-14, UI-32)
- Typing previews. A keystroke in a field restarts a 300 ms timer, and the drawing and the results show the typed value
  when it ends. Enter, Tab and focus out commit the value, and Esc puts the committed text back. (REQ-N-02, D-056g)
- Up, Down and Shift step the numeric fields, and a step stays inside the valid range. (DEF-US11-04, DEF-US12-02)
- Windows high contrast. The window takes the system colours and the drawing goes greyscale. (REQ-N-23)
- A note in the result disclosure and an Oracles row in the equation register name the oracles that depend on a check.
  For EC-05 they are OR-07 and OR-08. (REQ-T-16)
- Issue `INVALID_STACKUP_COPPER_EXCEEDS_BOARD`. A board thinner than its copper is refused, and the even stack-up
  generator raises on it instead of clamping its dielectrics to 0 mm. A dielectric thickness must be greater than 0.
  (D-053a)
- A board thickness outside 0.2 to 10 mm is refused as an unsupported range (`RANGE_BELOW_SUPPORTED`,
  `RANGE_ABOVE_SUPPORTED`), and the stack-up helper shows the issue. A copper weight outside 0.25 to 10 oz lists an
  issue on the copper field. (D-059c, D-059d, D-060b)
- `docs/install/INSTALL.md` gains the PK-06 Linux result, the self-test, the `libxcb-cursor0` package of Ubuntu 24.04
  and the pip upgrade notice. A Thai install guide, `docs/install/INSTALL_TH.md`, is added.
- Gates. The release profile enforces TR-01 with a manual-record index (D-051e, D-052c). LG-04 to LG-06 run as product
  tests (D-053d). Tests refuse a socket connect, except the internal connect of `socket.socketpair()` (REQ-N-17,
  D-055d). The issue-code coverage check runs in `check_contract.py` and as a static test (D-056d). The LG-01 word
  printer lists 804 words (D-062a). The newline lint covers `tools/` (D-063c).

### Changed

- The computed DRC distance is called clearance in the UI, the PDF, the README and the JSON keys.
  `DrcViolation.measured_mm` is now `clearance_mm` and `DrcCheckSummary.measured_min_mm` is now `least_clearance_mm`,
  with no alias. The outcome JSON of `embodic-cli compute --json` gains `format` (`embodic.outcome`) and
  `format_version` (2). (D-051a, D-052e)
- User-facing wording. "Balanced." reads "Symmetric 3-phase pattern.", and the issue codes
  `UNBUILDABLE_UNBALANCED_WINDING` and `RANGE_MANUAL_ASSIGNMENT_UNBALANCED` are now `UNBUILDABLE_ASYMMETRIC_WINDING` and
  `RANGE_MANUAL_ASSIGNMENT_ASYMMETRIC`. Program names leave the user-facing strings. The copy fixes of the V3-14 triage
  are adopted. (D-051b, D-051c, D-051d)
- `UNBUILDABLE_UNSUPPORTED_TOPOLOGY` is removed. No code emitted it, and its message was false for serpentine and wave.
  (D-056e)
- A result takes the validity flags and trust labels of the results it is built from, and its chain is the union of
  their chains. The values of the five examples are identical. (D-058d, D-059b, D-060c, D-061b)
- A value derived from inputs alone takes no field equation. `layers[k].z_mm` loses EQ-05, and its badge comes from its
  kind tag `derived`. (D-060d)
- EQ-06 moves from `verified` to `inferred` in the equation registry, and all five links are kept. (D-057c)
- `winding_factor_1` reads "Utilisation factor" with the symbol k_u, and the EQ-08 formula reads "symmetric 3-phase
  pattern". (D-063a, D-063b)
- In the inspector forms the provenance chip moves to the label line of each field row, the unit column aligns per
  section, and the screw buttons read Add and Remove with long accessible names. (REQ-N-15, D-057e)
- Each packaged example is read and parsed once per process, not once per provenance lookup.
- The five packaged examples are regenerated. They carry schema version 2, `engine_version` and `registry_version`, and
  `app_version` and `engine_version` read `0.0.2`. (D-056b)

### Fixed

- The GUI stall at example open and at result arrival. The cause was work on the GUI thread. Labels are laid out once
  per view change, icon rasters are cached, and result cards and inspector forms are built once with the window and
  updated in place. Offscreen on the 2-CPU container the largest stall fell from 603 ms (D08) and 1153 ms (wave) to
  about 330 ms, and the cold start took 1.45 to 1.71 s against the 3.0 s of PF-03. The GUI CPU time of a result update
  fell from 131.6 to 110.4 ms (median, offscreen). The cause of UI-31 is fixed. Cards had 0 px before the queued layout.
  (DEF-U-M5h-01, DEF-U-M6a-01, D-050a, D-056k)
- The Tab order follows the visual and F6 order, and Tab leaves the tables. (DEF-U-M7c-01, DEF-U-M8a-01)
- F6, Shift+F6, Alt+1 to Alt+4, Ctrl+Shift+N and Ctrl+Shift+T are bound. The scroll areas and the issues list have names
  for screen readers. EQ chips are links with a Press action. (DEF-U-S7-01, DEF-U-S7-02, DEF-U-S7-03)
- The unit cells of the layer, screw and pair tables carry an accessible description that names the unit. (DEF-UV13-02,
  REQ-N-24)
- The Board tab no longer cuts the serpentine Layers and Coil tabs at 960 by 540 pixels. (DEF-US12-01, DEF-U-M7c-02,
  D-057e)
- The export checklist stamp prints 12 hex digits of the design hash. (DEF-US11-01)
- `PolygonOutline.corner_radius_mm` was accepted and ignored. `build_outline` now builds the rounded polygon of a
  polygon board, and the spiral generator no longer refuses a board corner radius. (DEF-UE17-01, D-056h)
- EQ-16 takes the exact area of the outline loops. (DEF-M7b-01, D-056j)
- EQ-17 cools a stack through its two outer faces, with the assumption of an unventilated board gap. (DEF-UE17-02,
  D-056i)
- A result that lists EQ-06 now also lists EQ-05 and EQ-07 in its chain. (DEF-UE18-01)
- A screw pitch radius of 1e30 mm or more overflowed the DRC grid index and returned `INTERNAL_DRC_FAILED`. Validation
  now bounds the screw lengths, and the broad phase refuses an index it cannot represent. (DEF-M7a-01, D-054e)
- The serpentine and wave generators silently ignored `vias_per_transition` above 1. Every topology now refuses a value
  other than 1 with its `OPTION_NOT_IMPLEMENTED` code. (DEF-M7a-02, D-054d)
- The project loader refuses a version stamp (`app_version`, `engine_version`, `registry_version` or `saved_utc`) that
  is not a string. (D-058e)
- The DRC violation list has one canonical order (kind, layer, objects). The same 186 wave violations came out in
  another order on Windows. (DEF-W-01, D-051f)
- The board dump and the README export write LF line ends on every platform. `tools/sync_registry.py` writes LF, and its
  `--check` compares the manifest bytes. (DEF-W-09, D-063c)
- `embodic-cli` writes stdout and stderr as UTF-8. (DEF-W-08)
- The self-test time column aligns for every check id. (DEF-UV5-04)

### Known limits

- Windows. The Windows record of the decision log for the 0.0.1 build is that Python 3.11.9 from the python.org NuGet
  package works inside the folder, steps 2 to 6 of `INSTALL.md` pass, the self-test passes 45 of 45 and the evidence
  applies (D-051g). Windows commit gate 3 on `3a99eba` had 2 failed, 3378 passed, 83 skipped and 11 xfailed (D-055e).
  Windows commit gate 4 on `6270b9e` had 5 failed, 3765 passed and 83 skipped. The failures were MT-04 and the four N-17
  guard tests (D-061g). Both are fixed in 0.0.2, and the decision log up to D-063 records no Windows rerun of them. The
  two Windows PK-06 records of 0.0.1 are superseded and are redone with the 0.0.2 build (D-062c).
- OR-07 stays a strict expected failure (F-OR07, `inferred`). The gap G2 between the length in Table 1 and the drawing
  of D09 is open. (D-049b, D-050c)
- No built board or measured data exists, so EQT-14-O2 is `not tested`. (D-048f)
- The serpentine build at near-zero clearance takes 15 to 17.5 s against a bound of 10 s (DEF-M6b-01, strict expected
  failure). Spiral option M4 (one phase per pair) is refused with `UNBUILDABLE_SPIRAL_OPTION_NOT_IMPLEMENTED`. Parallel
  vias are not generated or analysed. All three belong to Phase 5. (D-050b, D-054c, D-054d)
- The one-off update of about 330 ms at example open and at result arrival stays open (DEF-U-M6a-01). It is measured on
  the real Windows laptop before any redesign. (D-050a)
- EQ-28 and EQ-29 have no port and no golden test, and neither is `verified`. (D-061e)

## 0.0.1 - 2026-10-04

### Added

- Installable package `embodic` (Python 3.11 or newer) with the `desktop`, `dev` and `desktop-dev` extras.
- `embodic.units`: unit vocabulary with display forms, conversions (degrees, metres, rpm, copper oz, mil²) and
  `round_half_away_from_zero`.
- `embodic.errors`: severities, issue categories, `ValidationIssue`, `Suggestion`, `Unbuildable` and the English
  message catalogue.
- `embodic.paths.resource_root()` for wheel and editable installs.
- Gates: import contracts C1 to C4, mypy strict, ruff, static lints MT-04 to MT-07, LG-01 and LG-08, the
  requirements-to-tests matrix (`tools/trace_matrix.py`) and one entry point for every profile (`tools/ci.py`).
- GitHub Actions workflow running `tools/ci.py` on Ubuntu and Windows with Python 3.11 and 3.12.
