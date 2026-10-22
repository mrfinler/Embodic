Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5 (units U-S17, U-S19 and U-S20)

# Acceptance walkthrough of embodic 0.0.6 on your Windows laptop

This walkthrough takes you through release 0.0.6 (D-093d, D-094) on your own laptop, alone, in about 70 minutes. You
install the release wheel, start a blank design, open the five packaged examples, try typing and the keyboard, read the
results, write every export, switch the themes and run the Narrator check AX-06 that 0.0.6 still needs (D-091c,
D-083c). On the way you take about 20 screenshots for the real-display check W6 (D-100c). Part 8 is optional and adds
about 10 minutes. The acceptance plan of Agent 4 (`docs/phase4/verification/acceptance_plan.md`) refers to the step
numbers here.

Before part 0, Fable starts a launcher that takes the in-window screenshots of W6 on your display (appendix A). It
takes about 5 minutes (`assumption`: it has not run on the laptop). Leave the laptop alone while it runs.

The build under test is release 0.0.6, tag `v0.0.6` on `2bfca49`, wheel `embodic-0.0.6-py3-none-any.whl` with the
SHA-256 of step 0.1 (D-096). Your checkout is at `6ac95ac`, which holds that tag (D-098a). `git diff --stat 2bfca49
6ac95ac -- src resources pyproject.toml requirements` prints nothing (`verified`). U-S17 and U-S19 checked this file
against main `672297e`. Those checks carry to `2bfca49`, because `git diff --stat 672297e 2bfca49 -- src` prints
nothing and the one change under `resources` is the row of `settings.svg` in `resources/icons/ICONS.md` (D-094b), a file that no
code under `src` reads (`verified` by `git diff` and `grep`).

What 0.0.6 changes for you. **Copper weight** and **Board thickness** show and announce their unit (steps 1.9 and 7.5).
The torque-speed message names the tab and the group of its field (steps 4.7 and 4.12). The keys Ctrl+Shift+S,
Ctrl+Shift+Z, Ctrl+P and Ctrl+/ work, and the guide no longer lists Ctrl+, (step 3.8, D-094b). Step 3.10 is new. It
asks what should happen to the canvas keys that the design lists and the app lacks (DEF-US18-01).

## How to read and mark the steps

Each part is a table. Do the action in the second column, compare the window with the third column, and mark the last
column.

- Write P when the window shows what the row says.
- Write F when it does not, and add a few words on what you saw.
- Write N, and a note, when you want to say something without a verdict.
- A row marked **Judge** asks for your opinion as a motor designer. No answer is wrong there. Write what you think.

How to take a W6 screenshot. Some rows name a shot in code font, such as `S11_light`. Take the shot while the row's
state is on screen.

1. Press Windows+Shift+S. In the bar at the top, choose the window mode and click the embodic window or its dialog. A
   row that asks for a rectangle needs the rectangle mode, so that a tooltip or a menu is in the shot too.
2. Click the notification that appears, and press Ctrl+S in Snipping Tool.
3. Save the file in `%USERPROFILE%\Desktop\embodic-uat-0.0.6\report\w6` under the row's name with `.png`. Write
   `light` or `dark` for the theme the window shows.
4. If the shot shows your user name, for example in the path of a Windows file dialog, crop it out first.

The names of the Snipping Tool parts are those of Windows 11 (`assumption`, not checked on the laptop). If a shot does
not work, write N with a note and carry on. Appendix A lists every W6 row and the step that takes it.

Where the expected text comes from. Every quoted string and every bold control name comes from the product, either
from the source under `src/embodic` at `672297e` (the same as at `2bfca49`) or from the window of a 0.0.6 wheel. The script
`docs/phase4/design/checks/uat_probe.py` drove the window of Agent 4's candidate wheel (built from `6d50d0b`, SHA-256
`5d891a268323fed9ce3414db3b042d27e51e5a27e33bba44df3cdc262d3ddec8`) offscreen on Linux and wrote what it showed to
`docs/phase4/design/checks/uat_probe_0.0.6.json`. The script `docs/phase4/design/checks/uat_quote_check.py` fails when
this file quotes text that neither holds. In `src`, `672297e` differs from `6d50d0b` only in two rows of the guide's
keyboard table (U-M9e, `git diff`). The same script run on the `672297e` source showed those two rows as step 3.8 quotes
them, and otherwise differed only in the test-state words, because a source tree has no test evidence file (`verified`).
The 0.0.5 record of U-S17 stays beside it as `uat_probe_0.0.5.json`.

The numbers are those of the Linux run (`verified` there). The 0.0.6 dump holds the same numbers as the 0.0.5 one
(`verified` by comparing them). PK-04 found the 0.0.5 numbers on this laptop equal to the Linux ones within 1e-9
(D-090d), so the three digits shown here should match (`inferred`). Agent 1 ran nothing in this file on Windows
(standing order 8). The Windows results it quotes come from Fable's records, `docs/phase3/fable/windows_campaign_w2.md`
and `docs/phase3/fable/PK-06_windows_0.0.6.md`. Nobody has looked at the window of 0.0.4, 0.0.5 or 0.0.6 on Windows
(`windows_campaign_w2.md`), and that is why you run it.

Allow about 5 minutes for part 0, 7 for part 1, 10 for part 2, 13 for part 3, 8 for part 4, 11 for part 5, 8 for part 6
and 8 for part 7. That is 70 minutes in all. The optional part 8 adds about 10 (`assumption`: U-S17's estimate per part plus
about 30 s per screenshot).

## Part 0. Install the release wheel

You can test the wheel in a new folder (option A) or the editable install of your checkout (option B). Use option A.
Option B has no test evidence file, because a source tree holds none (`resources/evidence` at `2bfca49` has no
`passed_tests.v1.json`, `verified` by `git ls-tree`). The release profile writes one only after every gate passes
(`evidence_gates` in `tools/ci.py`), and on your checkout it passed 6 of 8 (D-099a), so your checkout holds none
(`inferred`; D-091b found the same for 0.0.5). So in option B every badge reads "not tested", or "unresolved" where
that weaker status applies, because `load_registry` in `src/embodic/results/registry.py` leaves the passed tests empty
when the file is missing. That is `verified` by reading the code and by an offscreen run of the `672297e` source tree on
Linux, where the 160 result badges read only those two words. The run carries to `2bfca49`, whose `src` is the same. It
is `inferred` for your checkout.

Option A. Open PowerShell and run these commands. Replace `<wheel>` with the full path of
`embodic-0.0.6-py3-none-any.whl` on the laptop. Every command calls the programs in `.venv\Scripts` by path. The
activation script is not needed, and your execution policy stays as it is.

```
$uat = "$env:USERPROFILE\Desktop\embodic-uat-0.0.6"
New-Item -ItemType Directory -Force $uat | Out-Null
Set-Location $uat
(Get-FileHash "<wheel>" -Algorithm SHA256).Hash
& "$env:USERPROFILE\Desktop\embodic\.python\tools\python.exe" -m venv .venv
.\.venv\Scripts\python.exe -m pip install --require-hashes -r "$env:USERPROFILE\Desktop\embodic\requirements\py311.txt"
.\.venv\Scripts\python.exe -m pip install --no-deps "<wheel>"
.\.venv\Scripts\python.exe -m pip list
.\.venv\Scripts\embodic-cli.exe selftest
```

If PowerShell answers `Program 'embodic-cli.exe' failed to run: An Application Control policy has blocked this file`,
a Windows policy such as Smart App Control blocks the launchers that pip writes into `.venv\Scripts` (DEF-W-16). Write
F in step 0.3 with that line. Then start embodic through Python instead, for the rest of the walkthrough.

- Where a step says `.\.venv\Scripts\embodic-cli.exe`, run `.\.venv\Scripts\python.exe -m embodic.cli`. It takes the
  same commands, for example `.\.venv\Scripts\python.exe -m embodic.cli selftest`.
- Where a step says `.\.venv\Scripts\embodic.exe`, run `.\.venv\Scripts\python.exe -m embodic.ui.app`. It opens the
  window.

On this laptop the policy blocked `embodic-cli.exe` in some runs and not in others on 2026-10-22. In PK-06 run 12,
`python -m embodic.cli` passed with the self-test 45 of 45 (D-098b, D-100a, `verified` by the record).
`python -m embodic.ui.app` has never been opened on Windows, so this would be its first run (`not tested`). The
commands above keep the launchers as `docs/install/INSTALL.md` writes them. The Windows troubleshooting section of
INSTALL.md gives the same fallback.

Option B. Run `cd $env:USERPROFILE\Desktop\embodic`, then `git diff --stat 2bfca49 -- src resources pyproject.toml
requirements`. When it prints nothing, your checkout holds the source under test. Then use
`.\.venv\Scripts\embodic.exe` to start the app. If PowerShell answers `Program 'embodic.exe' failed to run: An
Application Control policy has blocked this file`, write F in step 0.4 with that line, and use
`.\.venv\Scripts\python.exe -m embodic.ui.app` instead for the rest of the walkthrough. That command has never been
opened on Windows (`not tested`).

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 0.1 | Read the hash that `Get-FileHash` prints. | `FDB89189161D14B71433C4E35861D4E4D56FC6A7E64383F96BA13E27BA450101`, the SHA-256 of the 0.0.6 release wheel (D-096), in the capitals that PowerShell prints. | [ ] |
| 0.2 | Read the output of `pip list`. | `embodic 0.0.6`, `numpy 2.4.6`, `PySide6_Essentials 6.11.2` and `shiboken6 6.11.2`, besides `pip` and `setuptools`. The lock files did not change from 0.0.5 (U-V27). | [ ] |
| 0.3 | Read the last line of `embodic-cli selftest`. If PowerShell printed the Application Control line instead, write F with it and follow the paragraph after option A. | `45 tests: 45 passed, 0 failed`. Agent 4's runs of the release wheel on Linux gave the same (PK-06, U-V29, D-097a). On this laptop 0.0.6 gave 45 of 45 in PK-06 runs 11 and 12, through `embodic-cli` and through `python -m embodic.cli` (D-100a, `verified` by the record). | [ ] |
| 0.4 | Run `.\.venv\Scripts\embodic.exe`. If PowerShell answers `Program 'embodic.exe' failed to run: An Application Control policy has blocked this file`, write F with that line and run `.\.venv\Scripts\python.exe -m embodic.ui.app` instead, which has never been opened on Windows (`not tested`). Use that command for the rest of the walkthrough wherever it starts embodic. If the window offers "Recover unsaved design", click **Discard** and write N with a note. | The window opens. | [ ] |

## Part 1. Start a blank design and use the stack-up helper (D-014, D-024)

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 1.1 | Look at the window before you click anything. Shot `S01_<theme>` of the whole window, title bar included. | Title bar "embodic". The toolstrip tabs **Home**, **Design**, **Analysis**, **Export** and **View**. In the centre "No design open" and "Create a new design and enter its values, or start from a team example.", with the buttons **New design** and **Examples**. The inspector reads "Create a new design or load an example to edit its values.". The status bar reads "Ready", "DRC: not run" and "mm". | [ ] |
| 1.2 | Click **New design**. Shot `S11_<theme>` of the dialog, title bar included. | The dialog "New design" with "Name the design and choose its topology. You enter every value in the inspector next.". **Create design** is disabled. Under the topology buttons, "Choose a topology.". **Start from** shows "No example (blank)". | [ ] |
| 1.3 | Type `UAT blank spiral` in **Design name**, click **Spiral**, then click **Create design**. | **Create design** turns enabled after both. The title bar reads "UAT blank spiral - embodic". The inspector header reads "34 required fields left". The drawing reads "The drawing appears when every required field is valid." and the **Results** tab reads "Results appear when every required field is valid.". Nothing computes. | [ ] |
| 1.4 | Look at the **Coil** tab. | Required fields are empty, with the unit as grey text ("mm") and the hint "Required". Optional fields hold a value and the chip "default", for example **First coil angle** at 90 ° and **Turns per coil** empty with "Empty means the maximum that fits.". The rail card **Inputs** reads "34 required fields left", and **Input issues** starts with "Coils: required, no value yet.". | [ ] |
| 1.5 | Click **Go to first missing field**. | The cursor moves to **Coils** on the **Coil** tab. | [ ] |
| 1.6 | Press Alt+3 (**Layers**). In **Copper layers** choose 4. Press Alt+4 (**Board**). In the group "Stack-up and manufacturing", type `1` in **Copper weight** and press Enter, then type `1.6` in **Board thickness** and press Enter. Press Alt+3. | The stack-up table lists L1 Copper 34.8, D1 Dielectric 486.9, L2, D2, L3, D3 and L4, with the column Thickness (µm). The **Layer pairs** table lists pair 1 "L1, L2" and pair 2 "L3, L4". The notice reads "Layer pairs: 2. Pairs 1 and 2 added with the default rotation." with **Undo**. The header reads "33 required fields left". | [ ] |
| 1.7 | Press Alt+4, type `0.1` in **Board thickness** and press Enter. | Under the two inputs, two lines: "The value is below the supported minimum of 0.2 mm." and "Board thickness must exceed the total copper thickness of 0.1392 mm, so that every dielectric layer is thicker than 0.". | [ ] |
| 1.8 | Type `1.6` in **Board thickness** and press Enter. | The two lines go. | [ ] |
| 1.9 | **Judge.** Units. **Copper weight** and **Board thickness** show their unit beside the box, "oz" and "mm", as the other fields do, also once a value is in (0.0.6, DEF-US17-01). The helper turns 1 oz into 34.8 µm of copper. | Is 34.8 µm per ounce the figure you use? Do the two units read clearly beside their boxes? | [ ] |
| 1.10 | **Judge.** The blank flow. | Is this how you would start a real design? You give a name and a topology, then type every value into the inspector, and nothing computes before the form is complete. Do the field names read as you would name them? | [ ] |

You do not need to fill the other 33 fields. If you want to, do it after the walkthrough.

## Part 2. Open the five packaged examples and judge the D08 view (U-S16, D-079)

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 2.1 | Press Ctrl+Shift+N. If embodic asks "Replace the open design", accept it. | The dialog "Examples" lists "Serpentine, 16 poles", "Spiral, 12 coils, 10 poles (D08)", "Spiral, 12 coils, 14 poles", "Spiral, 12 coils, 16 poles" and "Wave, 16 poles, involute", each with a note, such as "D08 thesis configuration. The 66 mm circle board and 10 mm bore are an assumption.". | [ ] |
| 2.2 | Load each example in turn: select it, click **Load example**, wait for "Ready" in the status bar, then compare with the table below. Press Ctrl+Shift+N for the next one. For the D08 example use only the keys: Ctrl+Shift+N, Down arrow until it is selected, then Enter (AX-02 K-01). | Each row of the table below holds. Every phase coil carries its letter label, and the legend at the top left reads "Phase A", "Phase B", "Phase C", "L1 on top" and "Layers below". The fields carry the chip "example". | [ ] |

| Example | Title bar | Status bar | Key results rail |
|---|---|---|---|
| Spiral, 12 coils, 16 poles | "Spiral, 12 coils, 16 poles (from example Spiral, 12 coils, 16 poles) - embodic" | "DRC: passed", "2 layers, 12 coils, 63 vias" | Ke peak 45.9 mV·s/rad, "not tested". R_ph 3.93 Ω, "inferred". |
| Spiral, 12 coils, 14 poles | "Spiral, 12 coils, 14 poles (from example Spiral, 12 coils, 14 poles) - embodic" | "DRC: passed", "2 layers, 12 coils, 63 vias" | Ke peak 39.9 mV·s/rad, "not tested". R_ph 3.94 Ω, "inferred". |
| Spiral, 12 coils, 10 poles (D08) | "Spiral, 12 coils, 10 poles (D08) (from example Spiral, 12 coils, 10 poles (D08)) - embodic" | "DRC: passed", "2 layers, 12 coils, 63 vias" | Ke peak 30.9 mV·s/rad, "not tested". R_ph 502 mΩ, "inferred". |
| Serpentine, 16 poles | "Serpentine, 16 poles (from example Serpentine, 16 poles) - embodic" | "DRC: passed", "6 layers, 3 phases, 9 vias" | Ke peak 109 mV·s/rad, "not tested". R_ph 2.82 Ω, "inferred". |
| Wave, 16 poles, involute | "Wave, 16 poles, involute (from example Wave, 16 poles, involute) - embodic" | "DRC: 186 failures", "2 layers, 3 phases, 192 vias" | Ke peak 53.0 mV·s/rad, "not tested". R_ph 1.47 Ω, "inferred". |

The wave example fails 186 checks at 0.199965 mm against its 0.2 mm rule. That is the known, honest state of that
example (D-035, D-006), not a fault of this walkthrough.

Now the D08 view. In 0.0.3 you read D08 as shorted, because the view drew L2 and L1 in one ink on top of each other
(DEF-UV16-02). Since 0.0.5 the view draws the top visible layer solid and every layer below it as a thin outline, empty
inside, with a gap of board where it passes under copper above (design_spec.md section 3.3.1). 0.0.6 does not change
the view. Nobody has looked at this view on Windows yet (D-079c Q2).

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 2.3 | Load "Spiral, 12 coils, 10 poles (D08)". On the **View** tab click **Fit**. Leave **L1** and **L2** ticked under **Layers**. | L1 copper solid in the phase colours. L2 copper as a thin line of the same colour, empty inside, which stops short of L1 copper with a narrow gap of board. Vias and pads solid on top. The legend adds "L1 on top" and "Layers below". | [ ] |
| 2.4 | Untick **L2**. Then tick it again. | With L2 off, L1 alone, solid, and the two layer rows leave the legend. With L2 on, the view of 2.3 returns. | [ ] |
| 2.5 | Click the drawing, then press `]` twice and `[` twice. | The first `]` shows L1 alone, the second L2 alone at its true width, solid. `[` steps back to L1 and then to both layers. | [ ] |
| 2.6 | With both layers on, press `+` a few times and pan with the arrow keys to where an outer ring crosses a coil leg (near x −11, y 47 in the status bar). Press `0` to fit again. | At the crossing the ring and the leg are separated by the gap. The status bar shows the pointer position as x and y in mm. | [ ] |
| 2.7 | **Judge.** The D08 view. | Does any L1 copper still read as joined to L2 copper, at fit zoom or zoomed in? Can you tell which layer each piece of copper is on? Does the drawing look like the D08 board you know? | [ ] |

## Part 3. Try typing previews, stepping, the keyboard and F6

Keep the D08 example open. Values that you type preview after 300 ms (REQ-N-02). On this laptop a D08 compute takes
longer than its 0.3 s physics budget (DEF-W-15, D-091a), so a preview can take about a second. 0.0.6 keeps that limit,
because it changes no compute code (`verified` by `git diff`; the time on this laptop is `inferred`).

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 3.1 | Press Alt+1 (**Coil**). Click in **Inner radius**, select all, type `11.8`, and do not press Enter. Wait two seconds. | **Inner radius** read 11.47 mm with the chip "example" before you typed. After the wait, the drawing and the results follow the typed value. The rail's R_ph goes from 502 to 501 mΩ. The chip still reads "example". | [ ] |
| 3.2 | Press Esc. | The field reads 11.47 again, and R_ph returns to 502 mΩ. | [ ] |
| 3.3 | Press Up once. Then press Shift+Up once. | Up makes 11.97 (one step of 0.5 mm). Shift+Up makes 16.97 (ten steps). | [ ] |
| 3.4 | Press Enter. | The chip turns "user". R_ph reads 484 mΩ. **Undo** on the **Home** tab is enabled. | [ ] |
| 3.5 | Press Ctrl+Z. | The field reads 11.47, the chip "example", R_ph 502 mΩ. | [ ] |
| 3.6 | Press Alt+1, Alt+2, Alt+3, Alt+4, Alt+5, Alt+6 in turn. Then press F5. | Alt+1 to Alt+4 open the inspector tabs **Coil**, **Phases**, **Layers** and **Board**. Alt+5 opens **Results** and Alt+6 opens **DRC**. F5 runs **Compute** (its tooltip reads "Compute (F5). Compute the geometry, checks and results again."). | [ ] |
| 3.7 | Press F6 several times, then Shift+F6 several times. Shot `W5_<theme>_drawing` while the ring is on the drawing. | Each F6 moves the keyboard focus to the next region, in this order: toolstrip, inspector, inspector tabs, drawing, results tabs, key results rail, status bar, then round again. A region with nothing to focus is skipped. Shift+F6 goes the other way. A 2 px focus ring shows where the focus is, and on the drawing it runs inside the edge of the view. | [ ] |
| 3.8 | Press F6 until the focus ring is on the toolstrip. Press Ctrl+/ and read the guide, then close it. Press Ctrl+Shift+Z, then Ctrl+Z. Press Ctrl+P, then click **Close**. Press Ctrl+Shift+S, then cancel the Windows dialog. | Ctrl+/ opens the window "Guide and reference" at "Keyboard shortcuts". Its rows include "Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Shift+S", "Ctrl+Z, Ctrl+Shift+Z or Ctrl+Y", "Ctrl+P, Ctrl+E" and "F1, Ctrl+/", and no row names Ctrl+, (D-094b). Ctrl+Shift+Z redoes what 3.5 undid: **Inner radius** reads 16.97, the chip "user", R_ph 484 mΩ. Ctrl+Z brings back 11.47, "example" and 502 mΩ. Ctrl+P opens the dialog "Export" with only **PDF design report** ticked. Ctrl+Shift+S opens the Windows dialog "Save project". | [ ] |
| 3.9 | **Judge.** Typing. | Does the preview while you type feel right, or does it get in the way? Is Esc to drop a typed value natural to you? | [ ] |
| 3.10 | **Judge.** Canvas keys (DEF-US18-01). Click the drawing, then press L, G, C, M, T, A, B and Shift+C. | Nothing changes, and that is the state of 0.0.6. The keyboard map of the design (design_spec.md section 10) gives L, G, C, M and T to labels, greyscale, current, magnets and terminals, and A, B and Shift+C, with Esc to clear, to a phase highlight. 0.0.6 has no handler for any of them (`verified` offscreen, where none of the eight keys changed the drawing and `]` and `[` did; Agent 4 confirms it in U-V28). The guide does not list them. Read options (a) and (b) below the table, and write (a), (b) or your own answer in the box. | [ ] |

The two options for 3.10.

- (a) Implement the keys. 0.0.6 always draws the phase letters and has **Greyscale** on the **View** tab. It has no
  labels toggle, no current-direction arrows, no magnets in the drawing, no terminal view and no phase highlight
  (`verified` by reading `src/embodic/ui/views` at `672297e`, which `2bfca49` leaves unchanged). So G alone is a new key for a control that exists. L, C,
  M, T and the phase highlight are new drawing features, each with its design, code and tests, in a release after 0.0.6
  (`inferred`). The single letters work only while the drawing has focus (WCAG 2.1.4).
- (b) Take them out of the map. design_spec.md section 10 drops the rows for L, G, C, M, T and for A, B, Shift+C and
  Esc, and `resources/icons/ICONS.md` drops the canvas keys L and G from its rows. The app does not change, because it
  neither binds nor lists these keys. **Greyscale** stays on the **View** tab, and the drawing stays as you see it. You
  can ask for any of the features later.

Now the keys-only run AX-02 (REQ-N-12), in the steps below. Keep the D08 example open and put the mouse aside until
step 4.1. Use it only for the shots. The checks are those of section 3 of
`docs/phase3/design/ux_verification_plan.md`, and none of them has run on Windows (`not tested`). Steps 2.2, 2.5, 2.6,
3.6, 3.7 and 5.7 hold the other AX-02 checks (appendix A).

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 3.11 | Press F6 until the focus ring is on the toolstrip. Press Tab until the ring is on the tab **Home**. Press Right to show **Design**, **Analysis**, **Export** and **View** in turn. On each tab, press Tab through its buttons, then Shift+Tab back to the tab. Shot `W5_<theme>_toolstrip` while the ring is on a button (AX-02 K-03). | Every button of every tab takes the focus, and the ring shows on each. | [ ] |
| 3.12 | Press Alt+4 (**Board**). Press Tab until the ring is on **Speed**, press Ctrl+A, type `1234` and press Enter. Do the same with `1.7` in **Line current (rms)** and `65` in **Winding temperature**. Shot `W5_<theme>_field` while the ring is on **Winding temperature**. Then go back to **Speed** with Shift+Tab, type `]` and press Esc (AX-02 K-05, K-06). | Each value commits, and its chip reads "user". The ring shows on each field. `]` does not change the drawing, because the canvas keys act only while the drawing has the focus, and Esc brings back 1234. | [ ] |
| 3.13 | Press Alt+5. Press Tab until the ring is on **How was this computed** of the R_ph card, and press Space. Press Tab until the ring is on the chip "EQ-10". Shot `W5_<theme>_results`. Press Enter, then Esc. Then press Ctrl+Shift+T three times (AX-02 K-08, K-10). | The card's trace opens. Enter opens "Guide and reference" at EQ-10, and Esc closes it and gives the focus back to the main window. Each Ctrl+Shift+T moves the theme one step in the order light, dark, system, as in step 6.1, so after the third press the window is back in the theme it had. | [ ] |
| 3.14 | Press Ctrl+E. Press Tab through the format boxes and press Space on every ticked box except **SVG drawing of every layer**. Press Tab until the ring is in the folder box and type `exports-keys`. Press Tab until the ring is on **Export**, take the shot `W5_<theme>_export`, and press Space. Close the dialog with Esc (AX-02 K-11). | "Written to" and one file, `Spiral_12_coils_10_poles_D08.svg`, in the folder `exports-keys` inside the folder you started embodic from. In option A that is `%USERPROFILE%\Desktop\embodic-uat-0.0.6\exports-keys` (`inferred`: the folder box takes a relative name from the app's working folder, `src/embodic/ui/views/export_view.py` l.168, and creates the folder, `src/embodic/ui/viewmodels/export.py` l.219). | [ ] |

## Part 4. Read the results cards, badges, equation register and charts

Load D08 fresh (Ctrl+Shift+N) so every value is the example's. Press Alt+5.

Each card shows a title with its symbol, a value with three significant figures, a unit, one badge word, an equation
chip and an assumptions count. The badge is the weakest of the equation's evidence status, the test state of its
equation in this build and any validity cap (D-007, the guide topic "Trust badges").

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 4.1 | Find these cards in **Results**. | The rows of the table below. | [ ] |
| 4.2 | Point at the badge of the R_ph card, then of the Ke peak card in the rail. | The R_ph badge lists "EQ-10 verified; EQ-11 inferred; EQ-07 inferred". The Ke peak badge lists "EQ-18 inferred; EQ-07 inferred; EQ-06 inferred; EQ-06 tests not passed in this build; EQ-05 inferred; EQ-05 tests not passed in this build". | [ ] |
| 4.3 | Under **Show status**, untick "not tested". Then tick it again. | The "not tested" cards hide, then return. The box is named "Show not tested results", so this row is `inferred` from the name and was not run. | [ ] |
| 4.4 | On the R_ph card, click **How was this computed**. | The sections "Equation", "Inputs", "Assumptions", "Limitations", "Validation state" and "Sources", and the button **Copy trace**. The inputs are listed by model path, such as "/stackup/layers/0/thickness_mm = 0.0348 mm (example)". "Validation state" starts with "Status inferred: EQ-10 verified; EQ-11 inferred; EQ-07 inferred". | [ ] |
| 4.5 | Click the chip "EQ-10" on the R_ph card. | The window "Guide and reference" opens at "EQ-10 DC resistance with temperature", with Name, Formula, Equation gate "reuse", Evidence status "verified", "Test state in this build" "verified" and sources such as "EV-08: D08, p.45 (printed 40) (verified)". The tree on the left holds "Guide topics", "Equation register", "Status labels" and "Keyboard shortcuts". | [ ] |
| 4.6 | Close the guide. On the **Analysis** tab click **Equations**. | The register opens at its first entry, "EQ-01 Pole pitch, coil pitch, electrical angle". | [ ] |
| 4.7 | Open **Back-EMF**, then **Torque-speed**. | **Back-EMF** shows "Back-EMF per phase, fundamental, at 1000 rpm" with a badge, the chip "EQ-18", "17 assumptions", the note "Each phase is drawn from its fundamental EMF phasor (EQ-18 with n = 1). Phase total harmonic distortion: 0.0265." and **Data table**. **Torque-speed** reads "The torque-speed estimate needs a DC-link voltage (Board tab, Drive group).", because D08 has no DC-link voltage. | [ ] |
| 4.8 | Load "Wave, 16 poles, involute" and open **Torque-speed**. | Two charts, "Torque" and "Mechanical power", each with the badge "unresolved", the label "estimate", the chip "EQ-20" and "37 assumptions". | [ ] |
| 4.9 | With the wave example open, press Alt+6. Select the first row and click **Locate**. | "DRC: 186 failures, 0 warnings". Rows such as "Two traces are closer than the trace clearance rule." with 0.199965 and 0.200000 mm on L1. The note "A violation is reported when clearance < rule − 1e-6 mm (D-006).". **Locate** zooms the drawing to the marker and dims the copper. | [ ] |
| 4.10 | Open **Compare**. | "No reference stored. Set the current design as the reference to compare later versions." and the button **Set current design as reference**. | [ ] |
| 4.11 | **Judge.** Badges. Ke reads `not tested` because the registry links the D09 oracle OR-07 to EQ-05 and EQ-06, and OR-07 is a known expected failure (F-OR07). The badge counts an equation as tested only when every linked test passes. The D08 oracle OR-01 passed (−0.4 %). (U-V26 found this badge correct by the contract.) | Do the badge words tell you what you need about how far to trust each number? The reason in 4.2, "EQ-06 tests not passed in this build", does not say which linked test failed. Is that enough for you? | [ ] |
| 4.12 | **Judge.** Units and wording. | Do the titles, symbols and units read naturally to you: "Utilisation factor k_u", "Line back-EMF constant, peak", mV·s/rad, mN·m/A, N·m/√W, "dimensionless", "Air gap per side", "Line current (rms)"? Is a model path such as /stackup/layers/0/thickness_mm acceptable in "Inputs", or do you want the field name there? The **Torque-speed** message now names "Board tab, Drive group" (0.0.6, DEF-US17-03). Does it lead you to **DC-link voltage**? | [ ] |

The D08 cards to find in step 4.1:

| Card title | Value | Unit | Badge | Chip | Assumptions |
|---|---|---|---|---|---|
| Phase resistance at operating temperature R_ph | 502 | mΩ | inferred | EQ-10 | "11 assumptions" |
| Line back-EMF constant, peak | 30.9 | mV·s/rad | not tested | EQ-18 | "16 assumptions" |
| Interconnect loss P_ic | 158 | mW | verified | EQ-23 | "11 assumptions" |
| Inductance, estimate L_m | 1.34 | µH | unresolved, with "estimate" | EQ-14 | "19 assumptions" |
| IPC-2221 current capacity, guideline | 3.03 | A | unresolved, with "guideline (unverified)" | EQ-15 | "9 assumptions" |
| Copper mass m_Cu | 2.71 | g | assumption | EQ-16 | "5 assumptions" |
| Efficiency, electromagnetic only η | 0.611 | dimensionless | not tested | EQ-26 | "36 assumptions" |

## Part 5. Write every export

Make a folder for the files: `$env:USERPROFILE\Desktop\embodic-uat-0.0.6\exports`. The file names below come from the
offscreen export of D08 on Linux (`verified` there). The file `_screws.dxf` ending comes from `src/embodic/io/bundle.py`
(`verified` by reading).

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 5.1 | Load D08 fresh. Press Ctrl+E. Shot `S29_<theme>` of the dialog, title bar included. | The dialog "Export". Under "Files": **SVG drawing of every layer**, **DXF, complete**, **DXF, board outline only**, **DXF, screw holes only** (unavailable, because D08 has no screw holes), **Project file (JSON)**, **PDF design report**, **README.txt describing the files** and **ZIP archive of the selected files**. Under "Before you export": "Stamp: embodic 0.0.6, registry v1+17193c112982.c01a66176ad6, design 327919a0eef5", "DRC passed", "Results match the current design." and "55 assumptions behind the results; the report lists them.". **Export** is disabled, with "Choose a folder.". | [ ] |
| 5.2 | Click **Browse**, choose the `exports` folder, then click **Export**. | "Written to" the folder, then seven files: `Spiral_12_coils_10_poles_D08.svg`, `Spiral_12_coils_10_poles_D08.dxf`, `Spiral_12_coils_10_poles_D08_outline.dxf`, `Spiral_12_coils_10_poles_D08.embodic.json`, `Spiral_12_coils_10_poles_D08_report.pdf`, `README.txt` and `Spiral_12_coils_10_poles_D08.zip`. | [ ] |
| 5.3 | Click **Open folder**. Open the SVG in your browser, both DXF files in your CAD tool, `README.txt` in Notepad, and the ZIP. | The SVG draws every layer in millimetres with the phase letters and the legend. The DXF files open at the board's size in mm, the outline file with the outline only. `README.txt` describes the files. The ZIP holds the selected files and `README.txt`. | [ ] |
| 5.4 | Load "Serpentine, 16 poles". On the **Export** tab click **DXF**. Tick **DXF, screw holes only**, then click **Export**. | Two DXF files, one whose name ends in `_screws.dxf` with the screw holes only. | [ ] |
| 5.5 | Load "Wave, 16 poles, involute". On the **Export** tab click **SVG**, then click **Export**. Shot `S30_<theme>` of the dialog "Export with DRC failures" while the ring is on **Cancel**. | Under "Before you export": "DRC: 186 failures. Export asks you to confirm.". Then the dialog "Export with DRC failures", which starts "The design fails 186 design rule checks." and lists the failures. The focus starts on **Cancel**. | [ ] |
| 5.6 | Click **Cancel**. Then click **Export** again and click **Export anyway**. | **Cancel** writes nothing. **Export anyway** writes the SVG, marked as failing DRC. | [ ] |
| 5.7 | Load D08 fresh. Press Ctrl+S, save it in the UAT folder as `uat_d08`. Press Ctrl+N and create any blank design. Press Ctrl+O and open `uat_d08.embodic.json`. In both Windows dialogs use only the keys: type the name in the file name box, or the whole path such as `%USERPROFILE%\Desktop\embodic-uat-0.0.6\uat_d08`, and press Enter (AX-02 K-12; that the dialog expands `%USERPROFILE%` is an `assumption`). If a dialog does not take it, use the mouse and write N. Shot `W2_<theme>` while "Save project" is open and `W1_<theme>` while "Open project" is open. | The Windows dialogs "Save project" and "Open project". After the save, the title bar shows the new name. After the open, the title bar names the design, the fields read as saved, the rail reads 30.9 mV·s/rad and 502 mΩ, and the keyboard focus is back in the main window. | [ ] |
| 5.8 | **Judge.** The PDF report (D-056g, the U-S11 question 2 left for this review). Open `Spiral_12_coils_10_poles_D08_report.pdf`. | It holds "embodic design report" with the stamp, "Key results" (Quantity, Value, Status), "DRC summary" per board, "Inputs" by model path with their provenance, a drawing of each board, and on its last page "Set in Inter and JetBrains Mono, SIL Open Font License 1.1.". A status prints with its label in brackets after it, as the inductance row shows. The "Key results" rows carry no limitations, such as the EC-05 edge note. Is this report right for your use? Would you hand it to a colleague or a board house as it is? What is missing, and what would you take out? | [ ] |

## Part 6. Switch the themes, greyscale and high contrast

The Windows Settings names below are the English ones of Windows 11. If your Windows shows Thai, use the same pages
under their Thai names.

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 6.1 | On the **View** tab, point at **Theme**, then click it three times, looking at the window after each click. Shot `S09_<theme>` with a rectangle around the window and the tooltip while the tooltip shows, before the first click. After the click that brings light and the one that brings dark, take `W3_light` and `W3_dark` of the whole window, title bar included, and write in the note whether the title bar is light or dark. Point at **Theme** once more while the window is dark, or light if S09 was dark, and take the other `S09`. If the tooltip goes before the snip, write N. | The tooltip reads "Theme. Switch the colour theme: light, dark, then follow the system.". Each click moves to the next choice in the order light, dark, system. The chrome, the icons, the drawing and the charts restyle at once, without a restart. Text stays readable, and phases stay red, blue and green. | [ ] |
| 6.2 | Leave the theme on system. In Windows Settings, open Personalization, then Colors, and switch between the light and the dark mode. After each switch, take `W6_light` and `W6_dark` of the embodic window (row W6 of the plan). | embodic follows the Windows mode without a restart (REQ-N-27). | [ ] |
| 6.3 | Click **Greyscale**. Click it again. | The phases turn to a grey ladder, A darkest, with hatching in the coil eyes. The phase letters and the layer cue stay. The second click brings the colours back. | [ ] |
| 6.4 | In Windows Settings, open Accessibility, then Contrast themes, choose Night sky and apply it. Look at the D08 example. Take `W4_night-sky_drawing`, then press Alt+5 and take `W4_night-sky_results`. Choose Desert, apply it, and take `W4_desert_drawing` and `W4_desert_results` the same way. | The chrome takes the Windows contrast colours. The drawing turns greyscale with hatching. **Greyscale** is checked and unavailable, and its tooltip ends "On while Windows high contrast is on.". The layer cue of 2.3 still shows. This is its first run on Windows (D-083b). The contrast theme names are those of Windows 11 (`assumption`). Under Desert the chrome takes Desert's light system colours and the rest is the same (`inferred`: the chrome follows the system colours of whichever contrast theme is on, `src/embodic/ui/views/high_contrast.py`). | [ ] |
| 6.5 | Turn the contrast theme off. | embodic returns to your theme and to the greyscale choice you had. | [ ] |
| 6.6 | **Judge.** Themes. | Is any text invisible, clipped or hard to read in any theme? Which theme would you work in? | [ ] |

## Part 7. Run the Narrator check AX-06 (REQ-N-16, REQ-N-24)

AX-06 passes when Narrator announces label, value and unit for inputs, and value, unit and status for results
(REQ-N-16, `docs/phase2/architecture/requirements.md`). The 0.0.3 record (`docs/phase3/fable/AX-06_narrator_0.0.3.md`)
does not stand for 0.0.6, because the view and the legend changed (D-082b) and TR-01 counts a record only for the
version it names (D-083c). This part replaces it, so you run it once.

Narrator keys (Microsoft's Narrator guide, read by Agent 1 in `docs/phase3/design/ux_verification_plan.md` section 2).
The Narrator key is Caps Lock or Insert.

- Start or stop Narrator: Windows+Ctrl+Enter.
- Read the window: Narrator+W.
- Copy the last spoken phrase: Narrator+Ctrl+X.
- Open the speech recap (history): Narrator+Alt+X.
- Scan mode on or off: Narrator+Spacebar. In scan mode, Down arrow and Up arrow move from item to item.

Before you start, load D08 fresh and open Notepad on a new file `narrator_log.txt` in the UAT folder. After each step,
press Narrator+Ctrl+X, switch to Notepad, paste, and switch back. If a key does not work on your Windows build, write
what you heard instead, and say so in the log. Keep the default verbosity.

| # | Do this | Narrator should announce | P / F / note |
|---|---|---|---|
| 7.1 | Press Windows+Ctrl+Enter, then Narrator+W. | The title "Spiral, 12 coils, 10 poles (D08) (from example Spiral, 12 coils, 10 poles (D08)) - embodic". | [ ] |
| 7.2 | Press Alt+1. Tab to **Inner radius**. | "Inner radius", "11.47" and "mm". | [ ] |
| 7.3 | Tab through **Outer radius**, **Trace width**, **Trace spacing** and **Coil gap**, then on to **First coil angle**. | For each, the label, the value and the unit: "45.03" "mm", "2.06" "mm", "0.8" "mm", "0.8" "mm", then "90" and "°" (spoken as degree). | [ ] |
| 7.4 | Press Alt+4. Tab to **Speed**, then to **Remanence B_r**. | "Speed", "1000", "rpm". "Remanence B_r", "1.38", "T". | [ ] |
| 7.5 | Tab to **Copper weight** and **Board thickness**. | "Copper weight", "1", "oz". "Board thickness", "0.6", "mm". 0.0.6 puts the unit in their accessible description (DEF-US17-01, REQ-N-24, `verified` offscreen). How Narrator speaks "oz" is not tested, so write the word you hear. | [ ] |
| 7.6 | Press F6 until the focus is in **Key results**. Press Narrator+Spacebar to turn scan mode on, then Down arrow until you hear both key cards. | "Line back-EMF constant, peak, 30.9 millivolt-second per radian, not tested" and "Phase resistance at operating temperature R_ph, 502 milliohm, inferred". A Tab stop inside a card is its chip, its assumptions count or **How was this computed**, not the card, so scan mode reads the card itself. | [ ] |
| 7.7 | Press Alt+5. Still in scan mode, press Down arrow through the result cards until you hear these two. Press Narrator+Spacebar to turn scan mode off. | "Interconnect loss P_ic, 158 milliwatt, verified" and "Inductance, estimate L_m, 1.34 microhenry, unresolved, estimate". | [ ] |
| 7.8 | Tab to the chip "EQ-10" on the R_ph card. | "Equation EQ-10, opens the equation register", and a role word. Write the role word you hear. | [ ] |
| 7.9 | Press Narrator+Alt+X. Copy the whole history into a new file `narrator_recap.txt`. Press Windows+Ctrl+Enter. | The history window opens. Narrator stops. | [ ] |
| 7.10 | Give the verdict. | AX-06 on 0.0.6 passes when 7.2 to 7.7 each announced all their parts. Write P or F here, with the date and the Windows build (`winver`). | [ ] |

## Part 8 (optional). Take the shots again at 100 % and 150 % display scale

Your display runs at its own scale, 125 % on a 1920 x 1200 panel when Fable read it on 2026-10-17
(`docs/phase3/fable/windows_campaign_w1.md`). The W6 plan also asks for every shot at 100 %, and for S03 and S22 at
150 % and 200 %. It changes the scale only with your OK (section 0 of `docs/phase3/design/ux_verification_plan.md`).
This part is your choice. If you decline, those shots stay `not tested`, with your choice as the reason.

At 200 % the screen is 960 x 600 logical px, too small for a 960 x 540 window with its title bar and the taskbar, so
200 % stays `not tested (screen too small)` (`inferred` from the panel size). At 150 % the screen is 1280 x 800 logical
px, so only the 960 x 540 shots of S03 and S22 fit (`inferred`).

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 8.1 | Decide whether you want this part. | Write yes or no. On no, skip the rest of this part. | [ ] |
| 8.2 | Close embodic. In Windows Settings, open System, then Display, and set Scale to 100 %. Start the launcher that Fable prepares for 100 % (appendix A) and leave the laptop alone until it ends. | The launcher ends, and `%USERPROFILE%\Desktop\embodic-uat-0.0.6\w6\lever-100` holds the shots. | [ ] |
| 8.3 | Start embodic as in step 0.4 and load D08. Repeat the shots of step 3.7 as `W5_<theme>_drawing_100` and of step 6.1 as `S09_<theme>_100`, in one theme. | The focus ring and the tooltip, sharp and not clipped. | [ ] |
| 8.4 | Close embodic. Set Scale to 150 %. Start the launcher that Fable prepares for 150 % and wait until it ends. | `w6\lever-150` holds the S03 and S22 shots. | [ ] |
| 8.5 | Set Scale back to your own value, 125 % if you had not changed it. | The display looks as it did before this part. | [ ] |

The other OS shots at 100 % stay `not tested`, because they would repeat parts 1, 5 and 6 for about 15 more minutes
(`assumption`).

## If something looks wrong

Write it down and carry on. Do not fix, rerun or reinstall anything first, because the state you found is the
evidence.

1. In the row's box, write F and one line: what you did, what you saw, and what you expected.
2. Take a screenshot with Windows+Shift+S. Save it in `$env:USERPROFILE\Desktop\embodic-uat-0.0.6\report` and name it
   after the step, for example `2.7_d08.png`.
3. If embodic showed the dialog "Internal error", copy its line that starts "Reference for the log file" into the
   note. embodic keeps running after that dialog and saves your design to a recovery file.
4. Copy the log file `embodic.log` into the `report` folder. Qt puts it in `%APPDATA%\embodic\embodic\logs\`
   (`inferred` from Qt's rule for the data folder of an app named embodic by embodic, not checked on Windows). If it is
   not there, find it with this command:

   ```
   Get-ChildItem $env:APPDATA, $env:LOCALAPPDATA -Recurse -Filter embodic.log -ErrorAction SilentlyContinue
   ```

   The log writes your home folder as `%USERPROFILE%`, so it holds no user name (`RedactingFormatter` in
   `src/embodic/ui/app.py`, `verified` by reading).
5. If the fault is in a design, press Ctrl+S and save the project file into the `report` folder.
6. If the fault is in the numbers, run `.\.venv\Scripts\embodic-cli.exe selftest > report\selftest.txt` from the UAT
   folder. If PowerShell answers `Program 'embodic-cli.exe' failed to run: An Application Control policy has blocked
   this file`, write F with that line in the row's box, and run
   `.\.venv\Scripts\python.exe -m embodic.cli selftest > report\selftest.txt` instead. Use `python -m embodic.cli` for
   `embodic-cli.exe` and `python -m embodic.ui.app` for `embodic.exe` for the rest of the walkthrough, as the paragraph
   after option A says. `python -m embodic.ui.app` has never been opened on Windows (`not tested`).
7. For Part 7, keep `narrator_log.txt` and `narrator_recap.txt` with the others.
8. Tell Fable in the Claude desktop app that the `report` folder is ready. Fable reads it from the laptop and writes
   the Thai summary.

If embodic closes by itself, start it again with the command of step 0.4. When it offers "Recover unsaved design",
click **Recover** and write that down too.

## Your judgement points

These are the rows where your opinion is the result. Agent 4's acceptance plan reads them from here.

| Row | Question |
|---|---|
| 1.9 | Units of the stack-up helper: 34.8 µm per ounce, and the unit beside Copper weight and Board thickness. |
| 1.10 | Whether the blank new-design flow is how you start a real design. |
| 2.7 | Whether the D08 view still reads as joined, and whether you can tell the layers apart. |
| 3.9 | Whether the typing preview helps or gets in the way. |
| 3.10 | The canvas keys L, G, C, M, T, A, B and Shift+C: (a) implement them, or (b) take them out of the keyboard map (DEF-US18-01). |
| 4.11 | Whether the badge words tell you how far to trust each number, and whether the reason should name the failed test. |
| 4.12 | Whether the units and wording read naturally. |
| 5.8 | Whether the PDF report is right for your use (D-056g). |
| 6.6 | Whether any theme hides or clips text. |

## Appendix A. What takes each W6 check

D-100c splits W6, the check of the app on the real display. Its scripted part runs from a launcher that Fable prepares
and starts at the start of the session, before part 0. Its human part is in this walkthrough. Agent 1 then reviews the
shots against `docs/phase2/design/screenshot_checklist.md` and the real-display cell of each row in section 1 of
`docs/phase3/design/ux_verification_plan.md`. The rows below are those of sections 1, 3 and 4 of that plan.

### A.1 The lever launcher, for Fable

The commands need the checkout `%USERPROFILE%\Desktop\embodic` at `6ac95ac` and its own `.venv`, which holds
`requirements\py311-dev.txt` and the editable install of the checkout (INSTALL.md step 7). The Windows commit gate of
0.0.6 ran from that venv (D-098c), so it is in place (`inferred`). Run the commands from the checkout's root, because
`python -m tests.ui.qt_shell.capture_acceptance` imports `tests` from the current folder. The UAT venv of option A cannot
run them: the release wheel holds no `tests` (`verified`: none of its 274 members starts with `tests`). Leave
`QT_QPA_PLATFORM` unset, so that Qt uses the Windows platform, the display's own scale and the Windows fonts. The
commands are for `cmd.exe`, as in a `.cmd` launcher. Nothing else may run on the laptop meanwhile, because the
first-paint probe discards a run whose idle gap is 30 ms or more.

```
cd /d "%USERPROFILE%\Desktop\embodic"
set QT_QPA_PLATFORM=
set OUT=%USERPROFILE%\Desktop\embodic-uat-0.0.6\w6\lever
mkdir "%OUT%"
.venv\Scripts\python.exe docs\phase3\design\checks\first_paint_probe.py spiral_12c10p_d08 >> "%OUT%\first_paint.jsonl"
.venv\Scripts\python.exe docs\phase3\design\checks\first_paint_probe.py spiral_12c10p_d08 >> "%OUT%\first_paint.jsonl"
.venv\Scripts\python.exe docs\phase3\design\checks\first_paint_probe.py spiral_12c10p_d08 >> "%OUT%\first_paint.jsonl"
.venv\Scripts\python.exe docs\phase3\design\checks\first_paint_probe.py wave_16p_example >> "%OUT%\first_paint.jsonl"
.venv\Scripts\python.exe docs\phase3\design\checks\first_paint_probe.py wave_16p_example >> "%OUT%\first_paint.jsonl"
.venv\Scripts\python.exe docs\phase3\design\checks\first_paint_probe.py wave_16p_example >> "%OUT%\first_paint.jsonl"
.venv\Scripts\python.exe -m tests.ui.qt_shell.capture_acceptance "%OUT%" S01 S03 S04 S05 S07 S09 S11 S14 S17 S20 S22 S23 S29 S30 S36 S38 S39 S41 > "%OUT%\rows.jsonl" 2> "%OUT%\rows_stderr.txt"
.venv\Scripts\python.exe -m embodic.ui.app --smoke --screenshot-dir "%OUT%\smoke" > "%OUT%\smoke.txt" 2>&1
echo smoke exit code %ERRORLEVEL% >> "%OUT%\smoke.txt"
```

For part 8, run the same `capture_acceptance` line with `OUT` set to `...\w6\lever-100` at 100 %, and with `OUT` set to
`...\w6\lever-150` and only the rows `S03 S22` at 150 %. Run neither probe line again, because the plan times the first
paint at the native scale only.

What the lines do:

- `first_paint_probe.py` is P-01 of section 4. It runs three times per example and writes one JSON line each time.
- `capture_acceptance` writes `<row>_<theme>_<width>x<height>[_<part>].png` and one JSON line per row in `rows.jsonl`. A
  row with an error writes a note and lets the others run. The sizes in the names are logical px. At 125 % the files
  hold 1.25 times as many device px (`inferred` from `QWidget.grab()`).
- S01, S09, S11, S29 and S30 are OS rows. The lever takes their client area in both themes, and the walkthrough takes
  their title bar and the compositor's image. Their functions open no blocking dialog. The export dialog opens with
  `open()` (`show_export` in `src/embodic/ui/views/main_window.py`) and the confirmation with `open()`
  (`run_clicked` in `src/embodic/ui/views/export_view.py`), `verified` by reading.
- The smoke line is step 2 of W6 in `docs/phase3/verification/verification_plan.md`. It opens the window through
  `python -m embodic.ui.app`, the DEF-W-16 fallback that has never been opened on Windows. So it also shows whether the
  fallback opens the window from the editable install. For the wheel in the UAT venv that stays `not tested`.

The launcher time of about 5 minutes is an `assumption`. W1 measured 6.83 s for one smoke run on this laptop
(`windows_campaign_w1.md`). The capture opens 18 rows, most with one or two example loads.

### A.2 Every row and what takes it

Native scale is your own, 125 % at the last reading. The lever is A.1. A step number is a step of this walkthrough, and
its shot goes to `report\w6\`.

| Plan row | Takes it | Where and what | Not covered, and why |
|---|---|---|---|
| S01 | Walkthrough | 1.1, `S01_<theme>`. The lever adds both themes at both sizes. | The title bar in the other theme. W3 shows that title bar with a design open. |
| S03 | Lever | `S03_light_960x540_<tab>` | 150 % in part 8 if you choose it. 200 % `not tested (screen too small)`. |
| S04 | Lever | `S04_<theme>_1280x800` | - |
| S05 | Lever | `S05_<theme>_1280x800` | - |
| S07 | Lever | `S07_<theme>_1280x800_fit`, `_zoom3x` | - |
| S09 | Walkthrough | 6.1, `S09_light` and `S09_dark`. The lever adds the in-window tooltip. | - |
| S11 | Walkthrough | 1.2, `S11_<theme>`. The lever adds both themes. | The title bar in the other theme, because the dialog opens once, before part 6. |
| S14 | Lever | `S14_<theme>_1280x800` | - |
| S17, S36 | Lever | `S17_<theme>_1280x800`, `S36_light_960x540` | The lever does not print `horizontalScrollBar().maximum()`. Agent 1 judges the scroll bar from the shot. |
| S20 | Lever | `S20_<theme>_1280x800` | - |
| S22 | Lever | `S22_<theme>_1280x800`, `S22_<theme>_960x540` | 150 % in part 8 at 960 x 540 only. 200 % `not tested (screen too small)`. |
| S23 | Lever | `S23_light_1280x800` | - |
| S29 | Walkthrough | 5.1, `S29_<theme>`. The lever adds both themes. | The title bar in the other theme. |
| S30 | Walkthrough | 5.5, `S30_<theme>`. The lever adds the light theme. | - |
| S38 | Lever | `S38_<theme>_960x540` | - |
| S39 | Lever | `S39_<theme>_dialog` | - |
| S41 | Lever | `S41_light_960x700` | - |
| W1 | Walkthrough | 5.7, `W1_<theme>` | - |
| W2 | Walkthrough | 5.7, `W2_<theme>` | - |
| W3 | Walkthrough | 6.1, `W3_light`, `W3_dark` | - |
| W4 | Walkthrough | 6.4, Night sky and Desert, the drawing and the results | The S01 state under a contrast theme, because a design is open by then. |
| W5 | Walkthrough | 3.7 drawing, 3.11 toolstrip, 3.12 field, 3.13 results, 3.14 export | The plan's Focus cells are `param-r-inner` and `res-r-phase-how`. The walkthrough rings **Winding temperature** and the chip "EQ-10" instead, the same kinds of widget (`inferred`). |
| W6 | Walkthrough | 6.2, `W6_light`, `W6_dark` | - |
| Every row at 100 % | Optional part 8 | `w6\lever-100`, and the OS shots of 8.3 | The other OS shots at 100 %, and all of them when you decline part 8. |
| K-01 | Walkthrough | 2.2, the gallery with the keys | The start screen's Tab route, because a design is open by step 2.2. |
| K-02 | Walkthrough | 3.7 | - |
| K-03 | Walkthrough | 3.11 | - |
| K-04, K-07 | Walkthrough | 3.6 | - |
| K-05, K-06 | Walkthrough | 3.12 | K-06 types `]`, not L, because 0.0.6 binds no L (DEF-US18-01). |
| K-08, K-10 | Walkthrough | 3.13 | - |
| K-09 | Walkthrough | 2.5 and 2.6 (`]`, `[`, `+`, `0`, arrows), 3.10 (L and G) | `-` is not pressed. L and G have no handler in 0.0.6 (DEF-US18-01). |
| K-11 | Walkthrough | 3.14 | - |
| K-12 | Walkthrough | 5.7 | - |
| P-01 | Lever | `first_paint.jsonl` | - |

Of the 24 rows of section 1, the lever takes 13 and the walkthrough 11 at the native scale. The 12 rows of
section 3 are walkthrough steps, and P-01 of section 4 is a lever line. AX-02 asks for one keys-only run with the mouse
out of reach. Each step above is keys-only, but between them the walkthrough uses the mouse, so AX-02 as one unbroken
run is `not tested`.
