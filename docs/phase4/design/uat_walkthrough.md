Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5 (units U-S17 and U-S19)

# Acceptance walkthrough of embodic 0.0.6 on your Windows laptop

This walkthrough takes you through release 0.0.6 (D-093d, D-094) on your own laptop, alone, in about 60 minutes. You
install the release wheel, start a blank design, open the five packaged examples, try typing and the keyboard, read the
results, write every export, switch the themes and run the Narrator check AX-06 that 0.0.6 still needs (D-091c,
D-083c). The acceptance plan of Agent 4 (`docs/phase4/verification/acceptance_plan.md`) refers to the step numbers here.

The build under test is release 0.0.6 from main `672297e`, wheel `embodic-0.0.6-py3-none-any.whl`. When this file was
written, that release wheel was not yet built: the repository has no tag `v0.0.6` (`verified`), and the one 0.0.6 wheel
is Agent 4's candidate from `6d50d0b`, which is not the release (U-V27). Fable writes the release wheel's SHA-256 into
step 0.1 before you start.

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

Where the expected text comes from. Every quoted string and every bold control name comes from the product, either
from the source under `src/embodic` at `672297e` or from the window of a 0.0.6 wheel. The script
`docs/phase4/design/checks/uat_probe.py` drove the window of Agent 4's candidate wheel (built from `6d50d0b`, SHA-256
`5d891a268323fed9ce3414db3b042d27e51e5a27e33bba44df3cdc262d3ddec8`) offscreen on Linux and wrote what it showed to
`docs/phase4/design/checks/uat_probe_0.0.6.json`. The script `docs/phase4/design/checks/uat_quote_check.py` fails when
this file quotes text that neither holds. In `src`, `672297e` differs from `6d50d0b` only in two rows of the guide's
keyboard table (U-M9e, `git diff`). The same script run on the `672297e` source showed those two rows as step 3.8 quotes
them, and otherwise differed only in the test-state words, because a source tree has no test evidence file (`verified`).
The 0.0.5 record of U-S17 stays beside it as `uat_probe_0.0.5.json`.

The numbers are those of the Linux run (`verified` there). The 0.0.6 dump holds the same numbers as the 0.0.5 one
(`verified` by comparing them). PK-04 found the 0.0.5 numbers on this laptop equal to the Linux ones within 1e-9
(D-090d), so the three digits shown here should match (`inferred`). Nothing in this file ran on Windows (standing order
8), and that is why you run it.

Allow about 4 minutes for part 0, 6 for part 1, 10 for part 2, 8 for part 3, 8 for part 4, 9 for part 5, 5 for part 6
and 8 for part 7.

## Part 0. Install the release wheel

You can test the wheel in a new folder (option A) or the editable install of your checkout (option B). Use option A.
Option B has no test evidence file, because a source tree holds none (`resources/evidence` at `672297e` has no
`passed_tests.v1.json`) and the release profile has not run in your checkout (D-091b found this for 0.0.5). So in option
B every badge reads "not tested", or "unresolved" where that weaker status applies, because `load_registry` in
`src/embodic/results/registry.py` leaves the passed tests empty when the file is missing. That is `verified` by reading
the code and by an offscreen run of the `672297e` source tree on Linux, where the 160 result badges read only those two
words. It is `inferred` for your checkout.

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

Option B. Run `cd $env:USERPROFILE\Desktop\embodic`, then `git diff --stat 672297e -- src resources pyproject.toml
requirements`. When it prints nothing, your checkout holds the source under test. Then use
`.\.venv\Scripts\embodic.exe` to start the app.

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 0.1 | Read the hash that `Get-FileHash` prints. | The SHA-256 of the 0.0.6 release wheel, which Fable writes here: `<release SHA-256>`. PowerShell prints it in capitals. | [ ] |
| 0.2 | Read the output of `pip list`. | `embodic 0.0.6`, `numpy 2.4.6`, `PySide6_Essentials 6.11.2` and `shiboken6 6.11.2`, besides `pip` and `setuptools`. The lock files did not change from 0.0.5 (U-V27). | [ ] |
| 0.3 | Read the last line of `embodic-cli selftest`. | `45 tests: 45 passed, 0 failed`. Agent 4's run of the 0.0.6 candidate on Linux gave the same (PK-06, U-V27). On this laptop 0.0.5 gave it (D-090d). 0.0.6 has not run here. | [ ] |
| 0.4 | Run `.\.venv\Scripts\embodic.exe`. If the window offers "Recover unsaved design", click **Discard** and write N with a note. | The window opens. | [ ] |

## Part 1. Start a blank design and use the stack-up helper (D-014, D-024)

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 1.1 | Look at the window before you click anything. | Title bar "embodic". The toolstrip tabs **Home**, **Design**, **Analysis**, **Export** and **View**. In the centre "No design open" and "Create a new design and enter its values, or start from a team example.", with the buttons **New design** and **Examples**. The inspector reads "Create a new design or load an example to edit its values.". The status bar reads "Ready", "DRC: not run" and "mm". | [ ] |
| 1.2 | Click **New design**. | The dialog "New design" with "Name the design and choose its topology. You enter every value in the inspector next.". **Create design** is disabled. Under the topology buttons, "Choose a topology.". **Start from** shows "No example (blank)". | [ ] |
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
| 2.2 | Load each example in turn: select it, click **Load example**, wait for "Ready" in the status bar, then compare with the table below. Press Ctrl+Shift+N for the next one. | Each row of the table below holds. Every phase coil carries its letter label, and the legend at the top left reads "Phase A", "Phase B", "Phase C", "L1 on top" and "Layers below". The fields carry the chip "example". | [ ] |

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
| 3.7 | Press F6 several times, then Shift+F6 several times. | Each F6 moves the keyboard focus to the next region, in this order: toolstrip, inspector, inspector tabs, drawing, results tabs, key results rail, status bar, then round again. A region with nothing to focus is skipped. Shift+F6 goes the other way. A 2 px focus ring shows where the focus is, and on the drawing it runs inside the edge of the view. | [ ] |
| 3.8 | Press F6 until the focus ring is on the toolstrip. Press Ctrl+/ and read the guide, then close it. Press Ctrl+Shift+Z, then Ctrl+Z. Press Ctrl+P, then click **Close**. Press Ctrl+Shift+S, then cancel the Windows dialog. | Ctrl+/ opens the window "Guide and reference" at "Keyboard shortcuts". Its rows include "Ctrl+N, Ctrl+O, Ctrl+S, Ctrl+Shift+S", "Ctrl+Z, Ctrl+Shift+Z or Ctrl+Y", "Ctrl+P, Ctrl+E" and "F1, Ctrl+/", and no row names Ctrl+, (D-094b). Ctrl+Shift+Z redoes what 3.5 undid: **Inner radius** reads 16.97, the chip "user", R_ph 484 mΩ. Ctrl+Z brings back 11.47, "example" and 502 mΩ. Ctrl+P opens the dialog "Export" with only **PDF design report** ticked. Ctrl+Shift+S opens the Windows dialog "Save project". | [ ] |
| 3.9 | **Judge.** Typing. | Does the preview while you type feel right, or does it get in the way? Is Esc to drop a typed value natural to you? | [ ] |
| 3.10 | **Judge.** Canvas keys (DEF-US18-01). Click the drawing, then press L, G, C, M, T, A, B and Shift+C. | Nothing changes, and that is the state of 0.0.6. The keyboard map of the design (design_spec.md section 10) gives L, G, C, M and T to labels, greyscale, current, magnets and terminals, and A, B and Shift+C, with Esc to clear, to a phase highlight. 0.0.6 has no handler for any of them (`verified` offscreen, where none of the eight keys changed the drawing and `]` and `[` did; Agent 4 confirms it in U-V28). The guide does not list them. Read options (a) and (b) below the table, and write (a), (b) or your own answer in the box. | [ ] |

The two options for 3.10.

- (a) Implement the keys. 0.0.6 always draws the phase letters and has **Greyscale** on the **View** tab. It has no
  labels toggle, no current-direction arrows, no magnets in the drawing, no terminal view and no phase highlight
  (`verified` by reading `src/embodic/ui/views` at `672297e`). So G alone is a new key for a control that exists. L, C,
  M, T and the phase highlight are new drawing features, each with its design, code and tests, in a release after 0.0.6
  (`inferred`). The single letters work only while the drawing has focus (WCAG 2.1.4).
- (b) Take them out of the map. design_spec.md section 10 drops the rows for L, G, C, M, T and for A, B, Shift+C and
  Esc, and `resources/icons/ICONS.md` drops the canvas keys L and G from its rows. The app does not change, because it
  neither binds nor lists these keys. **Greyscale** stays on the **View** tab, and the drawing stays as you see it. You
  can ask for any of the features later.

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
| 5.1 | Load D08 fresh. Press Ctrl+E. | The dialog "Export". Under "Files": **SVG drawing of every layer**, **DXF, complete**, **DXF, board outline only**, **DXF, screw holes only** (unavailable, because D08 has no screw holes), **Project file (JSON)**, **PDF design report**, **README.txt describing the files** and **ZIP archive of the selected files**. Under "Before you export": "Stamp: embodic 0.0.6, registry v1+17193c112982.c01a66176ad6, design 327919a0eef5", "DRC passed", "Results match the current design." and "55 assumptions behind the results; the report lists them.". **Export** is disabled, with "Choose a folder.". | [ ] |
| 5.2 | Click **Browse**, choose the `exports` folder, then click **Export**. | "Written to" the folder, then seven files: `Spiral_12_coils_10_poles_D08.svg`, `Spiral_12_coils_10_poles_D08.dxf`, `Spiral_12_coils_10_poles_D08_outline.dxf`, `Spiral_12_coils_10_poles_D08.embodic.json`, `Spiral_12_coils_10_poles_D08_report.pdf`, `README.txt` and `Spiral_12_coils_10_poles_D08.zip`. | [ ] |
| 5.3 | Click **Open folder**. Open the SVG in your browser, both DXF files in your CAD tool, `README.txt` in Notepad, and the ZIP. | The SVG draws every layer in millimetres with the phase letters and the legend. The DXF files open at the board's size in mm, the outline file with the outline only. `README.txt` describes the files. The ZIP holds the selected files and `README.txt`. | [ ] |
| 5.4 | Load "Serpentine, 16 poles". On the **Export** tab click **DXF**. Tick **DXF, screw holes only**, then click **Export**. | Two DXF files, one whose name ends in `_screws.dxf` with the screw holes only. | [ ] |
| 5.5 | Load "Wave, 16 poles, involute". On the **Export** tab click **SVG**, then click **Export**. | Under "Before you export": "DRC: 186 failures. Export asks you to confirm.". Then the dialog "Export with DRC failures", which starts "The design fails 186 design rule checks." and lists the failures. The focus starts on **Cancel**. | [ ] |
| 5.6 | Click **Cancel**. Then click **Export** again and click **Export anyway**. | **Cancel** writes nothing. **Export anyway** writes the SVG, marked as failing DRC. | [ ] |
| 5.7 | Load D08 fresh. Press Ctrl+S, save it in the UAT folder as `uat_d08`. Press Ctrl+N and create any blank design. Press Ctrl+O and open `uat_d08.embodic.json`. | The Windows dialogs "Save project" and "Open project". After the open, the title bar names the design, the fields read as saved and the rail reads 30.9 mV·s/rad and 502 mΩ. | [ ] |
| 5.8 | **Judge.** The PDF report (D-056g, the U-S11 question 2 left for this review). Open `Spiral_12_coils_10_poles_D08_report.pdf`. | It holds "embodic design report" with the stamp, "Key results" (Quantity, Value, Status), "DRC summary" per board, "Inputs" by model path with their provenance, a drawing of each board, and on its last page "Set in Inter and JetBrains Mono, SIL Open Font License 1.1.". A status prints with its label in brackets after it, as the inductance row shows. The "Key results" rows carry no limitations, such as the EC-05 edge note. Is this report right for your use? Would you hand it to a colleague or a board house as it is? What is missing, and what would you take out? | [ ] |

## Part 6. Switch the themes, greyscale and high contrast

The Windows Settings names below are the English ones of Windows 11. If your Windows shows Thai, use the same pages
under their Thai names.

| # | Do this | You should see | P / F / note |
|---|---|---|---|
| 6.1 | On the **View** tab, point at **Theme**, then click it three times, looking at the window after each click. | The tooltip reads "Theme. Switch the colour theme: light, dark, then follow the system.". Each click moves to the next choice in the order light, dark, system. The chrome, the icons, the drawing and the charts restyle at once, without a restart. Text stays readable, and phases stay red, blue and green. | [ ] |
| 6.2 | Leave the theme on system. In Windows Settings, open Personalization, then Colors, and switch between the light and the dark mode. | embodic follows the Windows mode without a restart (REQ-N-27). | [ ] |
| 6.3 | Click **Greyscale**. Click it again. | The phases turn to a grey ladder, A darkest, with hatching in the coil eyes. The phase letters and the layer cue stay. The second click brings the colours back. | [ ] |
| 6.4 | In Windows Settings, open Accessibility, then Contrast themes, choose Night sky and apply it. Look at the D08 example. | The chrome takes the Windows contrast colours. The drawing turns greyscale with hatching. **Greyscale** is checked and unavailable, and its tooltip ends "On while Windows high contrast is on.". The layer cue of 2.3 still shows. This is its first run on Windows (D-083b). The contrast theme names are those of Windows 11 (`assumption`). | [ ] |
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
   folder.
7. For Part 7, keep `narrator_log.txt` and `narrator_recap.txt` with the others.
8. Tell Fable in the Claude desktop app that the `report` folder is ready. Fable reads it from the laptop and writes
   the Thai summary.

If embodic closes by itself, start it again. When it offers "Recover unsaved design", click **Recover** and write
that down too.

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
