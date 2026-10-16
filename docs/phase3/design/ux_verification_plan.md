Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# Phase 3 UX verification plan for the real Windows display (U-S7)

Date 2026-10-16, worktree based on main 99647cb. This plan says what Phase 3 checks on the user's Windows laptop with a
real display (D-048d), so Fable can run it through the desktop app and Agent 4's Windows campaign (U-V6) can include it.
Nothing here was run on Windows. Every check below is `not tested` until Fable runs it and fills the record.

Two levers in `docs/phase3/design/checks/` back the plan. Both drive the real shell (`create_shell`, real compute).

- `keyboard_walk.py` presses Tab and the keys of `design_spec.md` section 10 and writes what Qt's accessibility layer
  reports at every stop. Its offscreen output on this container is `checks/keyboard_walk_offscreen.md`, the expected
  values of sections 2 and 3.
- `first_paint_probe.py` measures the stall after an example opens (section 4).

## 0. Setup and record

The Windows campaign of U-V6 installs Python 3.11 and `.venv` in `%USERPROFILE%\Desktop\embodic`. This plan starts
after that. Start the app from the embodic folder with `.venv\Scripts\python -m embodic.ui.app`.

Record before the first check:

- The Windows edition and build (`winver`), the display resolution and the laptop's own scale (Settings > System >
  Display > Scale). Call that scale "native". The 100 % run needs the scale set to 100 %. Change it only with the user's
  OK and set it back after the run. If the user declines, the 100 % rows are `not tested` with that reason.
- The usable logical screen. A 1280 x 800 row needs 1280 x 800 client px plus the title bar and the taskbar. At 150 % on
  a 1920 x 1080 panel the logical screen is 1280 x 720, so those rows cannot run at that size. Run them at the largest
  size that fits, write that size in the file name, and keep the 1280 x 800 cell `not tested (screen too small)`.

Write the record under `docs/phase3/design/records/<YYYY-MM-DD>/`. It holds:

- `shots/<ID>_<theme>_<width>x<height>_<scale>.png`, for example `S22_dark_960x540_150.png`.
- `narrator_log.txt` (section 2) and `keyboard_log.txt` (section 3). One line per step, tab-separated: step id,
  keys pressed, expected (copied from this plan), observed (verbatim), result (`pass`, `fail`, `not tested`), note.
- `first_paint.jsonl` (section 4): the probe's JSON lines, unedited.
- `ux_run.md`: the table of section 5 with each result filled in, the status label of each claim, and a DEF row for each
  failure with its reproduce steps.

No personal data goes into the record (standing order 7): crop or blur the user name in a title bar or a file dialog,
and write paths as `%USERPROFILE%\...`.

## 1. Screenshot rows to recapture

The M4 offscreen captures of `docs/phase2/design/screenshot_checklist.md` (40 rows, U-M4e-2) are the baseline. A
Windows shot passes when it shows everything the row's "Must be visible" cell asks and also the real-display items
below. Offscreen rendering cannot show these, so they are what this campaign adds:

- Font rasterisation on Windows (DirectWrite hinting and antialiasing) and the text widths it gives. Label fits, card
  clipping and the 960 px tables depend on those widths.
- Fractional device pixel ratios (125 %, 150 %). The offscreen UI-09 run scaled by `QT_SCALE_FACTOR` on one
  platform; it does not show how Windows rounds a 1 px border or a 2 px focus ring at 150 %.
- Native parts that `QWidget.grab()` leaves out: the title bar (its text and whether it turns dark with the dark
  theme), the native Open and Save as dialogs, tooltips and combo popups (the checklist's Popups rule).
- Windows contrast themes (UX-AC-24, REQ-N-23). `src/embodic/ui` has no high-contrast code (`verified` by grep for
  "highcontrast", "high contrast" and "forced", no match), so what the app does under a contrast theme is unknown.
- Focus rings at real DPI, seen in the compositor's image rather than in Qt's own render.

Capture in two ways:

- In-window rows: `.venv\Scripts\python -m tests.ui.qt_shell.capture_acceptance <OUT> <ROW ...>` without
  `QT_QPA_PLATFORM`, so Qt uses the Windows platform and its fonts. It grabs the window client area.
- Rows marked "OS" need the compositor's image: a screenshot of the whole window, title bar included, taken by Fable
  through the desktop app or with Win+Shift+S.

Take each row in the themes of its Theme cell, at native scale and at 100 %. Rows marked "+150, 200" add those scales
when the screen fits (UX-AC-24 names 100 %, 150 % and 200 %).

| Row | Checks | Window | Capture | What the real display must show (pass criterion) |
|---|---|---|---|---|
| S01 | UX-AC-13, UX-AC-21, UX-AC-03 | 960 x 540, 1280 x 800 | OS | Title bar text holds "embodic" and no path or user name; empty centre with New design and Examples; status bar "Ready"; no clipped text. |
| S03 | UX-AC-21, UX-AC-09 | 960 x 540 | lever, +150, 200 | Every toolstrip button visible or in the overflow; no label clipped; icons sharp at the scale (no half-pixel blur on a 1.5 px stroke). |
| S04 | UX-AC-05, UX-AC-27, UX-AC-04 | 1280 x 800 | lever | Phase letters on every coil, no label overlap, eye tint and hatch inside the eye only; chrome grey only. |
| S05 | UX-AC-07, UX-AC-05 | 1280 x 800 | lever | Grey ladder A dark to C light and the 45 and 135 degree hatches in both themes (the M4 S05 dark finding, `m4_review_2.md` 7.1, is the regression to watch). |
| S07 | UX-AC-27 | 1280 x 800 | lever | Fit zoom: A+ A− B+ B− C+ C− in view with U+2212 minus; 3x: a "B" label in view. Label boxes depend on font metrics, so this row is the one most likely to change. |
| S09 | UX-AC-09 | 1280 x 800 | OS | The tooltip itself, "Label (Shortcut). Sentence.", fully inside the screen, text readable. Offscreen Qt draws no tooltip, so this is its first real capture. |
| S11 | UX-AC-13 | dialog size | OS | New design dialog with title bar; Create disabled; nothing clipped. |
| S14 | UX-AC-15, UX-AC-11 | 1280 x 800 | lever | 2 px fail border and the message under `param-r-inner`; at 150 % the border is one even line, not 2 and 3 px on different sides. |
| S17, S36 | UX-AC-21, UX-AC-25 | 1280 x 800, 960 x 540 | lever | `layer-list` and `pair-list` whole, no header cell clipped, `horizontalScrollBar().maximum() == 0` at 960 (read with the lever, not by eye). |
| S20 | UX-AC-21, UX-AC-28 | 1280 x 800 | lever | `screw-table`, its buttons and the three fields in view; targets 24 px tall or more in logical px. |
| S22 | UX-AC-01, UX-AC-21 | 1280 x 800, 960 x 540 | lever, +150, 200 | Every card shows value, unit, badge word and assumptions tag, none clipped; at 960 the Key results tab and the Drawing tab. Pane widths by `docs/phase2/design/checks/shot_measure.py`. |
| S23 | UX-AC-15, UX-AC-08 | 1280 x 800 | lever | Stale card text at 4.5:1 or more on the card fill, measured on the Windows image (antialiased text has lighter edge pixels; measure the darkest run as `shot_measure.py` does). |
| S29, S30 | UX-AC-18, UX-AC-10 | 1280 x 800 | OS | Export dialog and `dlg-export-confirm` with focus ring on Cancel. |
| S38 | UX-AC-21 | 960 x 540 | lever | "Drawing" is the first tab and current; legend not clipped. At native scale this is likely the size the user meets. |
| S39 | UX-AC-08, UX-AC-03 | dialog size | lever | The five ruling g titles; the selected item's title and note at 4.5:1 or more by `shot_measure.py`. |
| S41 | UX-AC-27 | 960 x 700 | lever | Ring fills the canvas within 10 % after the resize; labels unchanged. |
| W1 | UX-AC-10, AX-02 | native | OS | Ctrl+O opens the native Open dialog; the path typed with the keyboard and Enter opens a saved D08 project; focus returns to the main window. |
| W2 | UX-AC-10, AX-02 | native | OS | Ctrl+S on a new design opens the native Save as dialog; the file appears in the folder; the title bar shows the new name. |
| W3 | UX-AC-06 | 1280 x 800 | OS | Theme switch from the View tab in both directions: chrome, icons and canvas restyle without restart. Record the title bar colour (light or dark) as an observation; no criterion names it. |
| W4 | UX-AC-24, REQ-N-23 | 1280 x 800 | OS | Turn on a contrast theme (Settings > Accessibility > Contrast themes, "Night sky" and "Desert"; Windows 11 names, `assumption`). Pass: no clipped or invisible text in S01, S04 and S22. REQ-N-23 also asks the greyscale mode under high contrast; record whether the canvas switches. |
| W5 | UX-AC-11, UX-AC-08 | 1280 x 800 | OS | One shot per Focus cell of S04, S14, S22 and S29 at native scale: the ring shows on the focused widget, is at least `round(2 x scale)` device px wide, and has the `focus-ring` colour at 3:1 or more against the next pixels. |
| W6 | REQ-N-27 | 1280 x 800 | OS | With the theme on "system", switch Windows between light and dark mode (Settings > Personalisation > Colours); the app follows without restart. |

## 2. Narrator walkthrough (AX-06; AX-05 on Windows)

AX-06 (REQ-N-16, test_plan.md) passes when Narrator announces label, value and unit for inputs, and value, unit and
status for results. The M4 record `tests/independent/m4/records/AX-06.md` is a QAccessible proxy (Linux, offscreen);
this walkthrough is its first real run.

What decides the result, read in the source:

- Qt 6.11.2 is the pinned PySide6 (`requirements/py311-dev.txt` l.826). Its UI Automation bridge gives UIA `Name`
  from the accessible name, UIA `FullDescription` from the accessible description, and UIA `HelpText` from
  `QAccessible::Help`, not from the description (`verified` by reading
  https://raw.githubusercontent.com/qt/qtbase/v6.11.2/src/plugins/platforms/windows/uiautomation/qwindowsuiamainprovider.cpp
  l.596-597 and l.650-651).
- embodic puts the unit of an input in the accessible description (UX-AC-17; "mm" for `param-r-inner` in
  `checks/keyboard_walk_offscreen.md` row 18). So Narrator speaks the unit only if it reads `FullDescription`. Whether it
  does is `unresolved`; step N-05 decides it. A field announced without its unit fails UX-AC-17 and AX-06.

Narrator commands, `verified` by reading Microsoft's Appendix B (https://support.microsoft.com/help/22806) and
Chapter 3 (https://support.microsoft.com/help/22809) on 2026-10-16. Narrator is Caps Lock or Insert.

| Command | Keys |
|---|---|
| Start or stop Narrator | Windows+Ctrl+Enter |
| Read the current item | Narrator+Tab |
| Read the window | Narrator+W |
| Scan mode on or off | Narrator+Spacebar |
| Next or previous item in scan mode | Down arrow, Up arrow |
| Copy the last spoken phrase to the clipboard | Narrator+Ctrl+X |
| Open the speech recap window (history) | Narrator+Alt+X |
| More or less verbosity | Narrator+V, Shift+Narrator+V |

How to record. Fable cannot hear the audio, so the log comes from text Narrator writes. After each step press
Narrator+Ctrl+X and paste the clipboard into the "observed" column of `narrator_log.txt`. At the end open speech recap
(Narrator+Alt+X), copy the whole history into `narrator_recap.txt`. If the speech recap commands are missing on that
Windows build, the user listens and types what was heard, and the log says so. Keep the default verbosity and write
its level in the log header. Scan mode is off unless a step turns it on.

Expected values come from `checks/keyboard_walk_offscreen.md` (offscreen, `verified` there, `not tested` on
Windows). The role word Narrator adds ("button", "edit", "check box") is recorded but is not a pass criterion, except
in N-09.

| Step | Checks | Keys from the state of the previous step | Narrator must announce (pass criterion) |
|---|---|---|---|
| N-01 | AX-06, UX-AC-03 | Start the app, then Windows+Ctrl+Enter, then Narrator+W | The window title with "embodic", and no path, user name, "Xcoil" or Thai text. |
| N-02 | AX-06 | Tab, ten times | Each stop's name in the order of the start table: "Home", "New", "Open", "Save", "Examples", "Coil", "New design", "Examples", then `rail-scroll` and `issues-list`. Those two have empty names offscreen (DEF-U-S7-02); expect them to fail. |
| N-03 | AX-06, UX-AC-14 | Tab to "Examples" (`btn-empty-examples`), Space, Down until the D08 item | "Packaged examples" for the list, then the item title "Spiral, 12 coils, 10 poles (D08)". |
| N-04 | AX-06 | Enter | The new window title or the focused canvas, "Geometry view of the stator board". |
| N-05 | AX-06, UX-AC-17, REQ-N-24 | Tab until `param-r-inner` | "Inner radius", the value "11.47" and the unit "mm". Repeat on `param-first-coil-angle` ("First coil angle", "90", "°" spoken as degree). All three parts present passes. |
| N-06 | AX-06, REQ-N-16 | Tab to `param-side-style-parallel` | "Parallel", its group "Side style" and its checked state. |
| N-07 | AX-06, UX-AC-14 | Tab back to the inspector tab bar ("Coil"), Right three times to "Board and rotor", Tab until `param-speed`, type 1234, Enter | "Speed", "1234", "rpm" while typing; after Enter, record what is announced about the `user` chip (no criterion: UX-AC-14 names the chip, not an announcement). |
| N-08 | UX-AC-22 | F5 | Record what is heard while the result updates. UX-AC-22 asks "Updating" with dimmed values; an announcement is not required, so this step is information only. |
| N-09 | AX-06, UX-AC-01, UX-AC-02 | Alt+5, then Tab until `res-r-phase-eq` | "Equation EQ-10, opens the equation register" and a role that says it acts (button or link). Its Qt role is static text (DEF-U-S7-03); if Narrator says "text", fail. |
| N-10 | AX-06, REQ-N-16, UX-AC-01 | Narrator+Spacebar (scan mode on), Up arrow until the R_ph card | "Phase resistance at operating temperature R_ph", the value, "milliohm" and "not tested". Repeat for the Ke_ph card and the ΔT card. Value, spoken unit and status word for all three passes. The values change after N-07; the expected value is the one the card shows. Narrator+Spacebar (scan mode off). |
| N-11 | AX-06, UX-AC-02 | Tab to `res-r-phase-how-toggle`, Space | "How was this computed" and its new state (checked or expanded). |
| N-12 | AX-06, UX-AC-02 | Tab to `res-r-phase-eq`, Enter, Narrator+W, Esc | The guide's title and the EQ-10 heading. |
| N-13 | AX-06, UX-AC-18 | Ctrl+E, Tab through the dialog, Esc | Each format check box by its format name and state; the folder field by its label; `btn-export-run` by its label. |
| N-14 | AX-06 | Close the app with unsaved changes (Alt+F4) | The question and every button of the dialog it shows. |

AX-05 is a visual criterion (REQ-N-14: phase and polarity without colour). Its Windows part is S05 and W4 of
section 1, not Narrator. Observation O-1 for the record: the canvas is one stop named "Geometry view of the stator
board" and exposes no coil labels (`verified` offscreen, start of the D08 table), so a Narrator user gets no phase or
polarity from the drawing. No criterion asks for it in Phase 2; it is a Phase 5 design question.

## 3. Keyboard-only walkthrough (AX-02) on the real window

AX-02 passes when the scenario runs with keys only and a focus ring shows at every stop (REQ-N-12, UX-AC-10,
UX-AC-11). The offscreen test `tests/ui/qt_e2e/test_ax02_keyboard_only.py` opens from the gallery because it cannot
drive the native file dialog. This run adds the native dialogs and the region keys. Put the mouse out of reach; the
pointer is not touched until K-12. Take one W5 shot at K-03, K-05 and K-08.

| Step | Checks | Keys | Pass criterion |
|---|---|---|---|
| K-01 | UX-AC-10 | Start the app; Tab to "Examples", Space, Down to D08, Enter | D08 opens; the window title names it. |
| K-02 | UX-AC-10 | F6 five times, then Shift+F6 five times | Focus moves through `toolstrip`, `inspector`, `inspector-tabs`, `fig-canvas`, `results-tabs`, `results-rail`, `statusbar` and back (design_spec.md section 5). Offscreen, F6 moved nothing and no F6 binding exists (DEF-U-S7-01); expect a fail. |
| K-03 | UX-AC-10, UX-AC-11 | Tab to the toolstrip tab bar ("Home"), Right to each of Design, Analysis, Export, View, Tab into the tab | Every tab's buttons reachable; ring visible on each. |
| K-04 | UX-AC-10 | Alt+1, Alt+2, Alt+3, Alt+4 | The inspector shows Coil, Phases, Layers, Board and rotor. Offscreen no binding exists (DEF-U-S7-01); expect a fail. The fallback route is Tab to the inspector tab bar and the arrow keys; record whether it works. |
| K-05 | UX-AC-10, UX-AC-11, UX-AC-12 | On "Board and rotor", Tab to `param-speed`, `param-current`, `param-copper-temp`; Ctrl+A, type 1234, 1.7, 65, Enter after each | Each value commits; each chip reads `user`; ring on each field. |
| K-06 | UX-AC-10 | Type "L" in `param-speed`, Esc | "L" appears in the field (single-letter keys act only on the canvas); Esc restores the committed value. |
| K-07 | UX-AC-10, UX-AC-22 | F5 | The results update. |
| K-08 | UX-AC-02, UX-AC-11 | Alt+5, Tab to `res-r-phase-how-toggle`, Space, Tab to `res-r-phase-eq`, Enter, Esc | "How was this computed" opens; the guide opens at EQ-10 and Esc closes it; focus returns to the main window. |
| K-09 | UX-AC-10 | Tab to `fig-canvas`; press +, -, 0, L, G, G, arrow keys | Zoom, fit, labels, greyscale on and off, pan, each visible on the canvas. |
| K-10 | UX-AC-06 | Ctrl+Shift+T twice | Theme switches and switches back. Offscreen no binding exists (DEF-U-S7-01); expect a fail. The View tab button route must work. |
| K-11 | UX-AC-18, W2 | Ctrl+E; Space on the boxes to keep SVG only; type a folder under `%USERPROFILE%\Desktop\embodic\build`; Tab to `btn-export-run`, Space | One `.svg` in the folder (the AX-02 end state). |
| K-12 | UX-AC-10, W1 | Ctrl+S, type a file name, Enter; Ctrl+O, type the same name, Enter | Save and Open run inside the native dialogs with keys only. |

## 4. DEF-U-M5h-01, first paint after opening (a check, not a fix)

DEF-U-M5h-01 (Fable, D-047): the first paint after opening an example took about 250 ms under a pure-Python
compute, `inferred` from U-M5h's runs of the old UI-05 test. The real compute on a real window is `not tested`.
REQ-N-02 names 100 ms for input echo; test_plan.md UI-05 labels that bound `assumption`.

What to run, at native scale, with the machine idle and nothing else open, three times per example:

```
.venv\Scripts\python docs\phase3\design\checks\first_paint_probe.py spiral_12c10p_d08 >> first_paint.jsonl
.venv\Scripts\python docs\phase3\design\checks\first_paint_probe.py wave_16p_example >> first_paint.jsonl
```

D08 is the example of AX-02 and the smoke run. The wave example is the heaviest packaged compute (186 DRC failures,
D-034), so it shows the worst case. The probe opens the example the way the gallery does (`session.load_example`) and
times from the call:

- `load_example_returns_ms`: how long the call holds the GUI thread.
- `first_paint_after_open_ms`: the first paint event of the window after the call returns.
- `result_ready_ms`: the computed outcome.
- `largest_tick_gap_after_open_ms` and where it starts: the longest time a 10 ms GUI timer could not fire, from the call
  to 1.5 s after the result. This is the time typed input would wait.

Validity: a run counts only when `largest_tick_gap_idle_ms` (the second before the open) is under 30 ms. A larger idle
gap means something else held the loop, and the run is discarded and repeated.

Pass criterion: in three valid runs per example, `largest_tick_gap_after_open_ms` is under 100 ms. Then
DEF-U-M5h-01 is not reproduced on the real window. A value of 100 ms or more reproduces it; record the value, where
the gap starts (in `load_example`, at the first paint, or at the result), and the example.

Container runs, one each, offscreen on the 2-CPU machine that three other units shared (`verified` by running,
2026-10-16, load average 1.22 after the runs; not a Windows result):

| Example | load_example returns | first paint | result | idle gap | largest gap after open (starts at) |
|---|---|---|---|---|---|
| D08 | 442.8 ms | 466.1 ms | 4325.6 ms | 11.7 ms | 603.4 ms (3720.8 ms) |
| wave | 369.2 ms | 379.5 ms | 5576.7 ms | 11.8 ms | 1152.8 ms (4733.6 ms) |

Both runs pass the validity rule and both fail the 100 ms bound, so offscreen on this container DEF-U-M5h-01 is
reproduced, and larger than the ~250 ms on record. Two readings come from the numbers. `load_example` holds the GUI
thread 369 to 443 ms before the first paint can happen (`verified` by the return time). The largest gap starts near the
end of the compute, 0.6 to 0.85 s before the result, not at the opening (`verified` by its start time). So the stall
has at least two places, the synchronous load and the work around the result (`inferred`; which code runs there is
`unresolved`). An earlier version of the probe counted the tick pair that spans the open as idle and reported idle
gaps of 369 to 488 ms; the version in `checks/` excludes it. The Windows runs decide the real-display numbers.

## 5. Checks, criteria and status

Every row is `not tested` until the Windows run fills it.

| Id | Checks | Pass criterion (short) | Status |
|---|---|---|---|
| S01 to S41, W1 to W6 (section 1) | UX-AC per row | Row's "Must be visible" cell plus the real-display cell | not tested |
| N-01 to N-14 (section 2) | AX-06, REQ-N-16, UX-AC-01, 02, 03, 14, 17, 18, 22 | Announcement holds the listed parts | not tested |
| K-01 to K-12 (section 3) | AX-02, UX-AC-02, 06, 10, 11, 12, 18, 22 | Step done with keys only, ring visible | not tested |
| P-01 (section 4) | DEF-U-M5h-01, REQ-N-02 | Largest gap after open under 100 ms in three valid runs per example | not tested |

A row fails when one part of its criterion is missing. A failure gets a DEF row in `ux_run.md` with the step, the
keys, the expected and the observed text, and the shot or log line.

## 6. Findings from the offscreen lever

The lever ran on this worktree (`QT_QPA_PLATFORM=offscreen PYTHONPATH=src:. python
docs/phase3/design/checks/keyboard_walk.py docs/phase3/design/checks/keyboard_walk_offscreen.md`, output "start 10
stops, d08 128 stops, 9 key probes"). These are defects or candidates the Windows run will meet.

| DEF | Severity | Finding | Reproduce | Status |
|---|---|---|---|---|
| DEF-U-S7-01 | major | F6 and Shift+F6 (region cycle), Alt+1 to Alt+4 (inspector tabs), Ctrl+Shift+T (theme) and Ctrl+Shift+N (Examples) do nothing. `design_spec.md` section 10, UX-AC-06 and UX-AC-10 name them. The shortcut table of the window has only Alt+5, Alt+6, Ctrl+E, Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Y, Ctrl+Z, Del (on `pair-list`), F, F1 and F5; `grep -rn F6 src/embodic/ui` finds only the Shortcuts help text (`src/embodic/ui/strings/results.py` l.177), which lists F6 to the user. | Run the lever; read "Key probes" (changed: no) and "Shortcuts registered in the window". | `verified` offscreen |
| DEF-U-S7-02 | moderate | Three Tab stops have no accessible name: `rail-scroll` and `results-scroll` (QScrollArea) and `issues-list` (QListWidget). WCAG 4.1.2, AX-06. | Lever, rows 9 and 10 of the start table, rows 8, 9 and 16 of the D08 table. | `verified` offscreen; Narrator `not tested` |
| DEF-U-S7-03 | moderate | Every `*-eq` chip takes focus and opens the register on Enter, but its accessible role is StaticText. WCAG 4.1.2. | Lever, D08 table rows 10, 13, 30 and the other `*-eq` rows. | role `verified` offscreen; what Narrator says `inferred` until N-09 |

Two open points are not defects yet. The unit in `FullDescription` waits for N-05. The missing high-contrast handling
waits for W4.

The design question behind DEF-U-S7-01 is mine to answer: the keys stay as `design_spec.md` section 10 lists them,
and the fix belongs to the code owner through Fable. The Shortcuts help text lists F6 today, so a user who reads it and
presses F6 gets nothing.
