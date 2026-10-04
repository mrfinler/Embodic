Prepared by: Agent 3 — Senior Software Engineer — model: claude-opus-5-5

# Xcoil v3 — feature inventory (Phase 1 draft, 2026-10-04)

Source of truth: `/home/claude/serpentine/src/` (read-only). Line numbers refer to those files (`engine.js` 2,986 lines,
`ui.js` 425, `ui-panels.js` 371, `ui-main.js` 265, `ui-content.js` 51, `view3d.js` 223, `report.js` 352, `tests.js` 906,
`body.html` 205, `style.css` 250). Status labels per PROJECT_BRIEF §3. "verified (code)" = established by reading the cited
lines; "verified (run)" = reproduced by a command I ran in this container (Node v22.22.2, Python 3.11.15).

## 0. Baseline checks I ran

| Check | Command | Result | Status |
|---|---|---|---|
| Engine test suite | `node /home/claude/serpentine/run-tests.js` | `131/131 passed` (categories GEO, DRC, ELE, FLD, EMF, EXP, DXF, REG, CON, END, MEC, VAL, WAV, WST, SEC, STK, PAD, IND, TSP, CMP, RPT) | verified (run) |
| Golden regression, defaults | `node golden-check.js ./src/engine.js` | `GOLDEN FAIL: 1 differences` — `c5.eff v1=0.886865 new=0.886332 rel=6.02e-4` (tolerance 5e-4) | verified (run) |
| Golden regression, interconnect off | `node golden-check.js ./src/engine.js '{"interconnect":false}'` | `GOLDEN OK: 1417 numbers match v1 (rel 1e-9; eddy loss within 3 %, efficiency within 0.05 %)` | verified (run) |
| Cause of the default failure | `node -e` on config c5 | with interconnect on, `pInterconnect = 0.00622 W` enters the efficiency (v3 default `interconnect: true`, `engine.js` l.43; loss added in `applyConnection` l.1431); v1 had no interconnect | verified (run) |
| Determinism | two `compute(DEFAULTS)` calls, `JSON.stringify` compared | identical | verified (run) |
| JSON-serialisability of a result | `JSON.stringify(compute(...))` for serpentine / wave / overlap / sector | works; 0.17–0.98 MB; 1–6 non-finite numbers per result (become `null`) | verified (run) |

Consequence: the golden harness must be run with `{"interconnect":false}`; this matters for the JS↔Python cross-check
(`calculation_flow_and_port_notes.md` §7).

## 1. Code organisation

| Unit | Role | Global / export | Dependencies | Status |
|---|---|---|---|---|
| `engine.js` | geometry + DRC + analysis + exporters, pure functions, "no DOM" (l.1–3) | UMD: `module.exports` / `SerpentineEngine` (l.5–8, export list l.2968–2985) | none | verified (code) |
| `report.js` | dependency-free PDF writer (Helvetica metrics, vector figure, tables, charts) | UMD `XcoilReport` (l.1–5) | engine.js | verified (code) |
| `tests.js` | 131 engine tests, runnable in Node and browser | UMD `SerpentineTests` (l.6) | engine.js, report.js (RPT-01) | verified (code+run) |
| `view3d.js` | WebGL 3-D view of the stack | `SerpentineView3D` | three.js r128 global `THREE` (l.13) | verified (code) |
| `ui.js` | form model, compute scheduling, 2-D canvas, layer bar, 3-D toggle | `window.__ui` (l.418–424) | DOM, SVG, engine, view3d | verified (code) |
| `ui-panels.js` | result tabs, summary strip, hints, status bar | registers renderers via `U.setRenderers` (l.368) | ui.js | verified (code) |
| `ui-content.js` | static Reference (formulas) and Guide content | — | ui.js | verified (code) |
| `ui-main.js` | exports, save mechanism, reference handling, UI tests, event binding, start-up | — | all above, `localStorage`, `window.claude.use('downloads')` | verified (code) |
| `body.html`, `style.css` | markup (icons l.2–38, title bar l.41–43, toolstrip l.45–121, inspector l.123–126, figure l.128–155, results l.157–188, status bar l.190–197, text dialog l.199–204, toast l.205); CSS tokens light/dark (l.1–25) | — | IBM Plex fonts from Google Fonts (`build.js` l.4) | verified (code) |
| `build.js` | concatenates src → `dist/artifact.html` (three.js from CDN) and `dist/xcoil.html` (three.js inlined from `vendor/three.min.js`, MIT, `vendor/three.LICENSE`) | — | Node | verified (code) |
| `parts/*.js` | **superseded development fragments** of engine/test sections. 84–100 % of their non-empty lines occur verbatim in `src/engine.js`/`src/tests.js`; the rest are older versions (e.g. `parts/sector.js` older `sideAngle`, single-level phase rings; `parts/drive.js` nested-array inductance with `Tof`; `parts/tests_v2.js` has an unfilled `__REG_TABLE__` placeholder). No feature exists only in `parts/`. | — | — | verified (run: line-match script) |
| `v1/` | frozen v1 engine/UI used to capture `golden-v1.json` | — | — | verified (code) |
| repo-root scripts | `golden-capture.js`, `golden-check.js`, `golden-configs.json` (23 configs), `golden-v1.json`, `gen-reg.js` + `reg-table.json` (REG-01 table), `export-samples.js`, `fuzz*.js`, `dbg*.js`, `timing.js`, `shot*.py`, `gen-testplan.js` → `TEST_PLAN.md` | dev tooling | Node | verified (code) |

## 2. Parameter model (inputs of every feature)

86 parameter keys in `DEFAULTS` (`engine.js` l.19–72); every key has exactly one control in `GROUPS` (`ui.js` l.16–139) —
verified (run: script comparing both lists: 86/86, none missing, none extra; also asserted by test UI-01, `ui-main.js` l.108).
`only:` flags restrict a field to topologies `s` serpentine, `w` wave, `c` sector (`ui.js` l.13, `syncDisabled` l.226–247).

| Group id (title) | Keys (`[s]`/`[w]`/`[c]` = topology-only) |
|---|---|
| machine (Machine) | topology, waveStyle[w], poles, phases |
| winding (Winding geometry) | rIn, rOut, turns, strands[s], traceWidth, clearance, style[s], cornerStyle, filletRadius, filletMax[s], startAngleDeg, terminalSide[s] |
| sector (Sector coils, group hidden unless `c`) | sectors, coilSides, coilEnds, coilGap, coilLayers |
| endwidth (End-turn copper width) | endWidthOuter, endWidthInner |
| layers (Layers and vias) | layersPerPhase[s], pairConnection[s], stackMode[s], layerOrder[s], waveLayers[w], viaDrill, viaPad |
| connection (Phase connection) | connection, interconnect, busWidth |
| pads (Terminal pads) | padShape, terminalPad, padHeight, terminalDrill |
| outline (Board outline) | outlineShape, outlineSides, outlineScale, outlineRotationDeg, outlineCornerRadius, innerHole, innerShape, innerSides, innerScale, innerRotationDeg, innerCornerRadius |
| screws (Fasteners) | screwFit, screwOuterOn, screwOuterSize, screwOuterCount, screwOuterInset, screwOuterAngleDeg, screwInnerOn, screwInnerSize, screwInnerCount, screwInnerInset, screwInnerAngleDeg |
| stackup (Stack-up) | stackupMode, copperOzOuter, copperOzInner, boardThickness, dielectricMaterial, dielectricEr, boardGap[s], stackup (hidden JSON field) |
| rotor (Rotor and magnets) | rotorType, Br, muR, magnetThickness, magnetArcRatio, airgap, magnetAuto, magnetRIn, magnetROut |
| op (Operating point) | rpm, currentRms (line current), tempC, tempRise |
| drive (Drive, torque–speed) | vDc, modulation, iMax, rotorInertia |
| thermal (Cooling estimate) | hConv, ambientC |

Units are in the labels only (mm, °, oz, T, rpm, A, °C, K, V, kg·m², W/m²K); the engine works in mm/radians/SI
(`engine.js` l.2). There is no unit metadata attached to results — verified (code: result objects are plain numbers).

## 3. Feature inventory

Column "Deps" lists runtime dependencies beyond the engine. "UI" = where the user sees it (toolstrip `TS`, inspector
group `G:<id>`, tab `T:<name>`, summary strip, status bar). All rows `verified (code)` unless marked otherwise.

### 3.1 Parameters, presets, persistence, compute loop

| ID | Feature | Where | Inputs | Outputs | UI | Deps |
|---|---|---|---|---|---|---|
| F-01 | Parameter defaults, normalisation and validation (range/integer/enum checks, cross-field rules; error codes NAN, INT, RANGE, ENUM, POLES_ODD, LAYERS_ODD, R_ORDER, VIA_RING, MAG_ORDER, PAD_RING, PAIRS_GT_P, TOO_MANY; `magnetAuto` copies rIn/rOut) | `engine.js` l.19–72, l.107–160 | all 86 keys | `{params, errors[], warnings[]}`; errors carry `field` | invalid field flagged red (`ui.js` l.257–258) | — |
| F-02 | Form generator from `GROUPS`: number inputs with units/step, selects, checkboxes, hint paragraphs, topology-dependent enable/disable and relabelling (`labels: {w, c}`) | `ui.js` l.16–139, l.179–247 | GROUPS | DOM form `#p-<key>` | inspector | DOM |
| F-03 | 15 presets (serpentine, delta hex board, wide end-turns, 2 wave, 2 sector, 3 Paul wave styles, custom polyimide stack, SPARK-style, radial 10-pole, miniature, parallel strands); test UI-05 requires all to build and pass DRC | `ui.js` l.140–156; select `body.html` l.54; handler `ui-main.js` l.240 | preset index | parameter set | TS "Preset" | — |
| F-04 | Autosave of last valid parameters and restore at start | `ui.js` l.7 (`xcoil.params.v3`), l.259; `ui-main.js` l.256–261 | — | localStorage entry | — | `localStorage` (wrapped in try/catch) |
| F-05 | Open / Save parameter JSON | `ui-main.js` l.59 (save), l.65–66 (load + `normalizeParams`) | file | `<base>_params.json` | TS New/Open/Save | FileReader, F-57 |
| F-06 | Reset to defaults ("New"), collapse/expand all groups | `ui-main.js` l.241–242 | — | — | TS, inspector header | — |
| F-07 | Toolstrip quick setters (topology serpentine/sector/wave, wave structure select, connection star/delta/open) with pressed state; topology change clamps turns and picks a balanced sector count | `body.html` l.58–72; `ui-main.js` l.72–86, l.239, l.243 | topology, waveStyle, connection | parameter change | TS | — |
| F-08 | Debounced recompute (140 ms), exception capture (`EXCEPTION`), compute time, last-good result kept and drawn dimmed (35 % opacity) when input is invalid | `ui.js` l.250–268, l.303 | form | `state.result`, `state.lastGood` | canvas, status bar | — |

### 3.2 Topology generators and geometry

| ID | Feature | Where | Inputs | Outputs | UI | Deps |
|---|---|---|---|---|---|---|
| F-09 | **Serpentine** generator: continuous ribbon of N = turns × strands traces per pole pitch; parallel or radial active conductors; round (concentric, ρ0 + level·pitch) or sharp corners; max-fillet mode; terminals at outer or inner rim; centre via V and terminal bus; layer pairs X/Y (Y = mirror of X about the gap axis); pairs in series (each pair rotated 2τ) or parallel; one board or one board per phase; grouped/interleaved layer order; bus level offsets per phase | `engine.js` `derive` l.163–193, `sideLine` l.198–203, `makeCorner` l.208–223, `minSweep`/`startRadius`/`minStraight`/`maxFillet` l.263–340, `fitStatus` l.347–391, `buildCanonical` l.409–497, transforms l.501–529, `buildLayout` l.671–753 | poles, phases, rIn, rOut, turns, strands, traceWidth, clearance, style, cornerStyle, filletRadius, filletMax, startAngleDeg, terminalSide, layersPerPhase, pairConnection, stackMode, layerOrder, boardGap, viaDrill, viaPad, endWidth* | `layout` {layers[{z, copperT, role, phase, pair, tf, objs[{kind strand/vbus/tbus/link, prims}]}], vias, links, canon, rMinCu, rMaxCu, statorThickness}; errors R_TOO_SMALL, ACUTE_CORNER, BUNDLE_TOO_WIDE, GEOMETRY | canvas, T:Results "Traces per bundle", `hint-fit` | — |
| F-10 | Maximum traces that fit (scan N = 1…400 with `fitStatus`) | `engine.js` l.394–404; used l.2517 | as F-09 | `derived.maxTraces` | `hint-fit` (`ui-panels.js` l.30–56) | — |
| F-11 | Wide end-turns (separate copper width at outer/inner rim) with width tapering at junctions | `engine.js` l.26, l.168–169, `taperJunctions` l.227–258 | endWidthOuter, endWidthInner | per-primitive width `w` | G:endwidth, `hint-endw` | — |
| F-12 | **Sector (concentrated spiral) coils**: Q coils, one spiral per sector on layer X (outer → centre via), mirrored on Y (centre → outer); parallel or radial sides; arc or straight ends; coil gap; concentric nested fillets reduced until all fit; phase/sign by star of slots; per-phase coil chain by depth-first search with ring levels; rings on X, legs on Y; additional layer pairs always parallel (warning PAIRS_PARALLEL); balanced-count suggestion | `engine.js` `starOfSlots` l.1899–1918, `deriveSector` l.2237–2252, `balancedSectorList` l.2253, helpers l.2254–2283, `sectorCoilX` l.2285–2325, `chainCoils` l.2330–2377, `buildSector` l.2379–2424, `computeSector` l.2426–2492 | sectors, coilSides, coilEnds, coilGap, coilLayers, turns, traceWidth, clearance, endWidth*, filletRadius, viaPad, busWidth, poles, phases | coils, vias (centre, terminal, ring), chains, `derived.kwSlots`, `maxTraces`; errors SECTOR_UNBALANCED, SECTOR_NO_ROOM, SECTOR_TURNS | G:sector, `hint-sector`, canvas | — |
| F-13 | **Interleaved wave** (involute end-turns): Q = 2p·m·q slots, T tracks on odd layers, mirrored B tracks on even layers, via-stitched; commutation tracks (`removed`/`shift`) for terminals; group links inside the inner via ring; layers in parallel | `engine.js` l.1449–1499 (involute/biarc helpers), `deriveWave` l.1501–1576, `waveTrack` l.1579–1624, `maxWaveTurns` l.1627–1631, belts l.1632–1637, `buildWave` l.1639–1690, `computeWave` l.1921–2008, `analyzeWave` l.2010–2087 | waveLayers, waveStyle, turns (= slots per belt), traceWidth, clearance, endWidth*, viaPad, viaDrill, busWidth, cornerStyle, filletRadius | tracksT/B, vias (2Q), zones, links; errors WAVE_MIN_POLES, WAVE_SLOT_PITCH, WAVE_INNER_TIGHT, WAVE_OUTER_TIGHT; warning LINK_WIDTH | TS wave select, canvas | — |
| F-14 | Wave styles after Paul et al.: `jog` (non-overlapping radial), `chord` (overlapping parallel) | `deriveWave` l.1531–1560, `waveTrack` l.1582–1587 | waveStyle | as F-13 | `#ts-waveStyle` | — |
| F-15 | Wave style `overlap` (overlapping radial, rim arcs, own star ring and pad corridor) | `buildWaveOverlap` l.2095–2145, `computeWaveOverlap` l.2146–2230 | waveStyle = overlap | as F-13 | same | — |
| F-16 | Geometry primitive layer: line `{t:'L',x1,y1,x2,y2,w,kind}` and arc `{t:'A',cx,cy,r,a1,a2,w,kind}` (signed sweep = direction); start/end/length, reverse, layer transform (rotate + mirror about θg), rotate/mirror helpers, discretisation (h ≤ 0.5 mm, angle and sagitta limits), fillets on arbitrary line/arc paths, biarc approximation of involutes (≤ 0.5 µm, ≤ 128 pieces), width runs | `engine.js` l.205–258, l.499–560, l.1456–1499, l.1735–1788, l.2787–2791 | — | primitive lists | all drawings/exports | — |
| F-17 | Phase interconnect: star neutral ring or delta mesh links on ring levels (non-crossing placement over layers), line stubs, terminal pads U/V/W(/N), "neck" stubs for via rings, stub-layer mode for sector coils, pad spreading along a corridor; resistance bookkeeping | `buildInterconnect` l.1225–1333, `drcInterconnect` l.1336–1358, `interconnectResistance` l.1361–1374, `spreadPadAngles`/`corridorPrims` l.1716–1729; topology calls l.2523–2535, l.1942–1949, l.2158–2190, l.2437–2451 | connection, interconnect, busWidth, clearance, pad keys | `layout.interconnect` {items, pads, links, rEdge}; warning INTERCONNECT_EXTERNAL; INTERCONNECT_CLEARANCE | G:connection, canvas | — |
| F-18 | Terminal pads: round/square/oblong/rect, optional height, drill or SMD; outline as primitives | `terminalPadGeometry` l.1191–1196, `makePad` l.1198–1201, `padOutline` l.1203–1218 | padShape, terminalPad, padHeight, terminalDrill | `layout.pads[]` | G:pads, `hint-pads` | — |
| F-19 | Board outline (circle or regular polygon with corner radius and rotation) scaled to the copper envelope; inner cut-out (circle/polygon) scaled to the inner copper radius; net board area | `outlinePrims` l.1055–1069, `outlineRadiusAt` l.1071–1093, `outlineArea` l.1094–1098, `buildMechanical` l.1101–1147 | outline*, inner* keys | `layout.mech` {prims, borePrims, apothem, rCircum, rBore, area, issues} | G:outline, `hint-outline`, T:Mechanical | — |
| F-20 | Fasteners: ISO 273 clearance-hole table M1…M8 (close/normal/loose) with head keep-out; outer and inner patterns; checks SCREW_EDGE, SCREW_PITCH, SCREW_COPPER, SCREW_NO_BORE | `SCREWS` l.1039–1051, `ring()` in `buildMechanical` l.1115–1143 | screw* keys | `mech.holes[]` | G:screws, `hint-screws`, T:Mechanical | — |
| F-21 | Stack-up model: automatic (outer/inner copper oz, evenly spaced layer centres in the board thickness) or custom list of copper/dielectric entries; dielectric table (FR-4, high-Tg, polyimide, Rogers 4350B, PTFE, custom); parallel-plate capacitance upper bound between neighbouring layers | `DIELECTRICS` l.1150–1153, `stackupFor` l.1156–1178, `stackCapacitance` l.1180–1188 | stackup*, copperOz*, boardThickness, dielectric* | z, t per copper layer, entries, capacitance | G:stackup, `hint-stack`, T:Stack-up | — |
| F-22 | Stack-up editor (switch auto/custom, reset from auto, edit thickness/material/εr per entry, drawing of the stack, per-layer table: content, z, distance to magnet, B_z1, copper µm, fill) | `ui-panels.js` l.178–235 | stackup JSON | updated `stackup` param | T:Stack-up | DOM |

### 3.3 Design-rule check and warnings

| ID | Feature | Where | Inputs | Outputs | UI | Deps |
|---|---|---|---|---|---|---|
| F-23 | Serpentine DRC: trace-to-trace inside each canonical layer (spatial hash, path-distance exemptions), via pad vs every pierced layer (inverse transform into canonical frame), series links, pad-to-pad, centre-via gap, no-shaft-hole warning, interconnect, tolerance 0.004 mm | `segSegDist`/`ptSegDist` l.563–578, grid l.580–596, `canonicalSegments` l.599–606, `drcLayer` l.609–648, `drcPadVsLayer` l.652–666, `runDrc` l.756–850 | clearance, widths, via sizes | `drc` {issues[{sev, code, msg, at}], traceClearance, padClearance, linkClearance, padPadClearance, viaGap, pairsChecked, ok}; codes VIA_GAP, TRACE_CLEARANCE, PAD_CLEARANCE, LINK_CLEARANCE, PAD_PAD, NO_SHAFT_HOLE, INTERCONNECT_CLEARANCE | T:DRC, markers on canvas, summary | — |
| F-24 | Generic object DRC (wave, overlap, sector): all object pairs per layer + self-clearance along a path, nets joined at shared vias exempt, via and pad clearance (round/rect/oblong pad geometry), pad-to-pad | `drcObjects` l.1693–1713, `drcLayerObjects` l.1791–1816, `padSegClearance` l.1819–1833, `padsClearance` l.1834–1842; use l.1953–1994, l.2197–2207, l.2457–2468 | as above | same `drc` shape | as F-23 | — |
| F-25 | Mechanical rule issues merged into DRC (OUTLINE_SMALL, BORE_LARGE, SCREW_*) | `buildMechanical` l.1112–1143; merge l.847, l.1992, l.2206, l.2467 | outline/screw keys | issues | T:DRC, T:Mechanical | — |
| F-26 | Design and fabrication warnings: MAG_SPAN, SKIN, IPC, IMBALANCE, CIRC, DELTA_CIRC, FAB (trace/space vs copper weight), FAB_VIA, THERMAL; plus TWO_PHASE, LINK_WIDTH, PAIRS_PARALLEL, INTERCONNECT_EXTERNAL | `commonWarnings` l.2495–2508; l.2548, l.1931, l.2489, l.2535 | analysis results | `warnings[]` | T:DRC, T:Results messages | — |

### 3.4 Electrical, magnetic, mechanical and thermal analysis

| ID | Feature | Where | Inputs | Outputs | UI | Deps |
|---|---|---|---|---|---|---|
| F-27 | Air-gap field model: odd harmonics 1…13 of B_z, B_t of a parallel-magnetised array with back iron; rotor types double / single + yoke / single open (symmetry plane G) | `HARMONICS` l.16, `fieldHarmonic` l.856–867, `fieldSetup` l.868–874 | rotorType, Br, muR, magnetThickness, magnetArcRatio, airgap, stator thickness | B per harmonic at (r, z); `B1mid` | T:Results (B_z1 rows), T:Stack-up | — |
| F-28 | Back-EMF / flux linkage from the generated copper (per segment B_z·r·Δr·e^{−jnpθ}, clipped to the magnet span), per strand/layer/element; phase assembly (series groups of parallel members); Ke per harmonic, Ke1, phase imbalance, numeric winding factor kw1, analytic distribution factor, THD | `analyze` l.880–1017; `analyzeWave` l.2010–2087; `analyzeElements` l.1846–1896 | geometry, field, rpm | `analysis.phases[{E, Ke[], R, pCirc}]`, Ke1, keImbalance, kw1, kdAnalytic, thd, emfPhasePk/Rms | T:Results, T:Back-EMF, summary | — |
| F-29 | DC resistance with temperature (per primitive width), via barrel resistance (25 µm plating), series links and interconnect | `copperResistivity` l.80, `traceResistance` l.102–104, `primsResistance` l.97–101, `viaBarrelArea` l.92–95, via/link sums l.961–970, l.2048–2049, l.2470–2476, F-17 | tempC, copper t, viaDrill | R per phase, Rtrace, Rextra, R line–line | T:Results, summary | — |
| F-30 | Losses and efficiency: copper (m·I_ph²R), eddy (σ/24 form, B_z w³t + B_t w t³), circulating loss of parallel paths, delta mesh circulation, interconnect loss; output power, electromagnetic efficiency, motor constant Km | `analyze` l.931–935, l.954–958, l.991–1016; `applyConnection` l.1398–1438 | currentRms, rpm, tempC | pCu, pEddy, pCirc, pDeltaCirc, pInterconnect, lossTotal, pOut, efficiency, motorConstant | T:Results, summary | — |
| F-31 | Connection-dependent line quantities (star/delta/open): phase current, torque, Kt per line ampere, Ke line, Kv rpm/V, EMF L–L, R line–line incl. interconnect | `applyConnection` l.1398–1438 | connection, phases | torque, KtPerArms, keLinePk, emfLinePk, KvRpmPerV, rLineLine, iPhaseRms | T:Results, summary | — |
| F-32 | EMF waveforms (phase and line–line), harmonic table, per-phase table, hover read-out | `emfWaveform` l.1020–1034, `lineWaveform` l.1441–1447; `ui-panels.js` l.138–176 | analysis | waveform samples (181 points) | T:Back-EMF | inline SVG |
| F-33 | Current capacity (IPC-2221, weakest layer × parallel paths), current density, skin depth | `ipc2221Current` l.86–90, `skinDepthMm` l.81–84, l.998–1001, l.1012–1014 | tempRise, widths, copper t | iMaxIpc, currentDensity, skinDepth | T:Results, warnings IPC/SKIN | — |
| F-34 | Synchronous inductance, current-sheet harmonic model of the radial conductors (orders ν up to 240, 36 radial bins, layer coupling, sinc² width factor, L_s = L_self − M) | conductor lists l.2560–2610, `windingInductance` l.2617–2668 | geometry, rotorType, airgap, magnetThickness | Ls, Lself, M, fundamentalShare, dominant orders | T:Torque–speed, T:Results | — |
| F-35 | Torque–speed envelope on a voltage/current-limited inverter (SVPWM / sine / six-step), field weakening, pull-out and pull-in estimate, rated point, rotor inertia estimate | `rotorInertiaEstimate` l.2671–2676, `inverterVoltage` l.2679–2684, `torqueSpeed` l.2688–2722, `driveAnalysis` l.2725–2731; tab `ui-panels.js` l.237–289 | vDc, modulation, iMax, rotorInertia | 121-point curve, rpmNoLoad, rpmBase, torqueMax, pMax, tauElec | T:Torque–speed (torque / power views) | inline SVG charts |
| F-36 | Mass (copper by primitive area × thickness; laminate by stack-up density) and first-order thermal estimate ΔT = P/(h·2A) | density constants `RHO_CU_G`, `RHO_FR4_G` l.1377; `massThermal` l.1378–1394 | hConv, ambientC, tempRise, stack-up | massCopper, massLaminate, massTotal, copperFill, tempRiseEst, lossAllowable | T:Mechanical, summary, warning THERMAL | — |

### 3.5 Results presentation and comparison

| ID | Feature | Where | Inputs | Outputs | UI | Deps |
|---|---|---|---|---|---|---|
| F-37 | Summary strip (6 cells: design rules, R line–line, back-EMF L–L, Kt/Kv, torque/η/J, mass/ΔT) | `ui-panels.js` l.15–27 | result | — | summary strip | DOM |
| F-38 | Results tab: key–value tables (connection, constants, R, Km, kw1, THD, imbalance, L_s, losses, efficiency, J, IPC limit, skin depth, geometry: pole pitch, slots/coils, bundle width, copper diameters, trace length, layers, vias, field values) | `ui-panels.js` l.58–110 | result | — | T:Results | DOM |
| F-39 | DRC tab: pass/fail table of clearances vs required, issue list with "Locate" (zooms canvas to `at`) | `ui-panels.js` l.113–136 | `drc` | — | T:DRC, badge | DOM |
| F-40 | Inspector hints (fit, sector chain order and balanced counts, end-turn, pads, outline, screws, stack-up, drive) | `ui-panels.js` l.30–56 | result | text | inspector | DOM |
| F-41 | Compare with a reference design: save current as reference (localStorage), load reference JSON, 39 metrics with Δ and Δ %, parameter diff, overlaid EMF and torque–speed curves, badge | `COMPARE_METRICS` `engine.js` l.2734–2745, `compareResults` l.2748–2759; `ui-main.js` l.89–101; `ui-panels.js` l.291–319 | two results | rows, paramDiff | T:Compare, TS "Save as reference / Compare" | `localStorage` key `xcoil.reference.v3` (`ui.js` l.7) |

### 3.6 Figure: 2-D canvas, 3-D view

| ID | Feature | Where | Inputs | Outputs | UI | Deps |
|---|---|---|---|---|---|---|
| F-42 | 2-D plan render: board with cut-out and holes, head keep-out circles, rIn/rOut guide circles, magnets (N/S wedges), copper per layer bottom-up (phase colours, odd layers at 62 % opacity), vias, pads, DRC markers, terminal labels | `ui.js` l.300–354 | `lastGood`, show toggles | SVG | figure | SVG |
| F-43 | 2-D interactions: wheel zoom about cursor, drag pan, two-finger pinch, Fit / Zoom in / Zoom out / Zoom to terminals, coordinate read-out (x, y, r, θ), scale bar, re-fit on resize | `ui.js` l.271–293, l.375–400 | pointer events | view box | figure toolstrip | `ResizeObserver` |
| F-44 | Layer visibility bar: All, Phase A only (serpentine), Top layer only (others), per-layer chips with phase swatch and z tooltip | `ui.js` l.355–374 | layers | `state.hidden` | layer bar | — |
| F-45 | Rotor angle slider (electrical degrees) rotating the magnet overlay (2-D and 3-D) | `body.html` l.149–153; `ui-main.js` l.247; use `ui.js` l.312 | rotorDeg | — | rotor bar | — |
| F-46 | Current-flow animation along strands/tracks/coils (dash offset; disabled for reduced motion) | `ui.js` l.321–325; `style.css` l.110–112 | show.flow | — | toggle "Flow" | CSS animation |
| F-47 | Show toggles: magnets, labels, flow (2-D), board (3-D) | `body.html` l.88–91; `ui-main.js` l.246 | — | — | figure toolstrip | — |
| F-48 | 3-D view: extruded board(s), copper ribbons per layer, via barrels and pads, magnets and back iron, label sprites, orbit/pan/zoom, explode slider (1–30×), theme-aware colours, fallback message when WebGL/three.js is missing | `view3d.js` l.11–220; `ui.js` l.402–415; slider `body.html` l.141–147 | `lastGood`, hidden, toggles | WebGL canvas | TS 2D/3D | three.js r128 (MIT), WebGL |

### 3.7 Exports and saving

| ID | Feature | Where | Inputs | Outputs | UI | Deps |
|---|---|---|---|---|---|---|
| F-49 | SVG (mm, y flipped, Edge.Cuts group, one group per copper layer, one path per width run, vias, pads) | `exportSvg` l.2796–2814, `primsToSvgPath` l.2765–2784, `padSvg` l.2817–2823 | result | `.svg` text | TS SVG | — |
| F-50 | DXF complete (R12 subset LINE/ARC/CIRCLE, `$INSUNITS` mm, copper as centre lines with layer name `CU<n>_<layer>_PH<x>_W<µm>`, vias, pads, outline, holes) | `DxfWriter` l.2826–2850, `exportDxf` l.2861–2874 | result | `.dxf` | TS DXF | — |
| F-51 | Outline DXF (outline + cut-out only) | `exportOutlineDxf` l.2857, `dxfOutline` l.2851–2854 | result | `_outline.dxf` | TS Outline | — |
| F-52 | Screws DXF (holes per ring/size layer) | `exportScrewsDxf` l.2859, `dxfScrews` l.2855 | result | `_screws.dxf` (toast when no pattern) | TS Screws | — |
| F-53 | KiCad board file: `(kicad_pcb (version 20221018) (generator xcoil)`, copper layer list, nets (`WINDING` when interconnect drawn, else `PHASE_A/B/C`), `segment`, `arc` (start/mid/end), through `via` F.Cu–B.Cu, terminal pads as inline footprints (`thru_hole`/`smd`, circle/rect/oval), Edge.Cuts `gr_line`/`gr_arc`/`gr_circle`; origin offset (150, 100) mm and y flip; one file per board (ZIP for per-phase boards). No stack-up section, no zones, no DRC rules are written. | `exportKicad` l.2877–2929; `ui-main.js` l.58 | result, board index | `.kicad_pcb` text + counts | TS KiCad | — |
| F-54 | Parameter JSON export | `ui-main.js` l.59 | params | `_params.json` | TS Save | — |
| F-55 | ZIP of all files (store only, CRC-32, UTF-8 names) | `crc32` l.2932–2938, `utf8` l.2939–2944, `makeZip` l.2946–2966; file set `ui-main.js` l.29–36 | files | `.zip` bytes | TS All (ZIP) | — |
| F-56 | PDF design report: summary, errors/warnings, parameters, derived quantities, stack-up and mechanical, electrical analysis with harmonics and inductance, DRC, vector layout figure, EMF and torque–speed charts, comparison with reference, method notes | `report.js` l.23–77 (PDF objects), l.110–137 (figure), l.143ff (charts), `buildPdf` l.235–352; `ui-main.js` l.24–28, l.61 | result, reference | PDF bytes | TS Report | — |
| F-57 | README.txt (topology, layers with z, terminals with coordinates, DRC summary, key results) | `ui-main.js` l.37–51 | result | text | inside ZIP | — |
| F-58 | Save mechanism: Claude "downloads" capability when present, otherwise Blob + `<a download>`, otherwise text dialog with copy button; non-native extensions wrapped in ZIP | `ui-main.js` l.6–22; dialog `body.html` l.199–204 | name, data | file | all export buttons | `window.claude.use('downloads')`, Blob/URL, Clipboard |

### 3.8 Tests, reference content, status

| ID | Feature | Where | Inputs | Outputs | UI | Deps |
|---|---|---|---|---|---|---|
| F-59 | Built-in test runner: 131 engine tests (`tests.js`) + 21 UI tests UI-01…UI-21 (`ui-main.js` l.104–214), run asynchronously with criterion and detail per row; Node runner `run-tests.js` (engine tests only) | `tests.js` l.11 (harness) ff.; `ui-main.js` l.215–229; tab `body.html` l.180–188 | — | pass/fail table | TS Run tests, T:Tests | — |
| F-60 | Reference tab: 20 formula cards with sources | `ui-content.js` l.6–27, l.48 | — | HTML | T:Reference | — |
| F-61 | Guide tab: 16 design-guide articles (cooling, weight, topology) tagged "In this tool"/"Practice"/"Topology" with sources | `ui-content.js` l.29–46, l.49 | — | HTML | TS Design guide, T:Guide | — |
| F-62 | Status bar: state and compute time, DRC pass/errors, counts (layers, vias, primitives, screw holes); figure note (poles, phases, connection, topology) | `ui-panels.js` l.356–366; `body.html` l.190–197 | result | text | status bar | — |
| F-63 | Shell: title bar with product name/version (`Xcoil`, `v3.0`), tabs, toasts, light/dark theme tokens (phase colours red/blue/green, `--ph-a/b/c` `style.css` l.6, l.15), IBM Plex fonts | `body.html` l.41–43, l.159–170; `ui.js` l.176; `ui-main.js` l.231–235; `style.css` l.1–25 | — | — | whole window | Google Fonts (`build.js` l.4) |
| F-64 | Developer regression tooling (golden capture/check, REG-01 table, fuzz scripts, export samples for external validation) | repo root (see §1) | — | JSON, sample files | none (dev) | Node |

## 4. Calculation flow (call graph from `compute()`)

`compute(input)` — `engine.js` l.2510–2551. Indentation = calls; `→` = returns into.

```
compute(input)
├─ normalizeParams(input)                         l.107   (errors → return early)
├─ [topology == 'wave']   computeWave(p, out)     l.1921
│   ├─ deriveWave(p)  ─ solveEnd → invol, bisect ; gapOK → segSegDist, ptSegDist          l.1501
│   │   └─ on error: maxWaveTurns(p) → deriveWave (scan q = 1…60)                         l.1627
│   ├─ [waveStyle == 'overlap'] computeWaveOverlap(p, out, W)                              l.2146
│   │   ├─ buildWaveOverlap(W)                                                             l.2095
│   │   ├─ stackupFor · terminalPadGeometry · makePad · spreadPadAngles · corridorPrims→filletPath · traceResistance
│   │   ├─ buildMechanical → outlinePrims, outlineRadiusAt, outlineArea                    l.1101
│   │   ├─ drcLayerObjects ×2 → drcObjects → discretize, makeGrid, gridQuery, segSegDist ; padSegClearance ; padsClearance
│   │   ├─ analyzeElements → fieldSetup, fieldHarmonic, discretize, primsResistance, ipc2221Current, skinDepthMm   l.1846
│   │   ├─ applyConnection → (delta) harmonic mesh sum                                     l.1398
│   │   ├─ massThermal                                                                      l.1378
│   │   ├─ driveAnalysis(conductorsFromElements) → windingInductance ; torqueSpeed → inverterVoltage, rotorInertiaEstimate
│   │   └─ commonWarnings                                                                   l.2495
│   ├─ buildWave(W) → waveTrack(→ involutePrims → biarc → arcFromTangent ; filletPath ; taperJunctions),
│   │                 mirrorPrimsX, reversePrims, rotatePrims, beltPhase, beltSign, slotAngle   l.1639
│   ├─ stackupFor · buildInterconnect(neck, deltaPairs) · buildMechanical
│   ├─ drcObjects(T) · drcObjects(B) · padVs(gridQuery, ptSegDist) · drcInterconnect
│   ├─ analyzeWave(W, G, layout) → fieldHarmonic, discretize, primsResistance, viaBarrelArea, ipc2221Current, skinDepthMm   l.2010
│   └─ interconnectResistance · applyConnection · massThermal · driveAnalysis(conductorsWave) · commonWarnings · maxWaveTurns
├─ [topology == 'sector'] computeSector(p, out)   l.2426
│   ├─ deriveSector(p) → starOfSlots(→ gcd, angNorm) ; balancedSectorList ; maxSectorTurns → sectorFeasible
│   │                    → sectorCorner, sideD, outerR, innerR, sideAngle, sectorViaSpot           l.2237
│   ├─ buildSector(S) → sectorCoilX(→ endPrim, filletPath, taperJunctions), mirrorPrimsX, reversePrims,
│   │                   rotatePrims, chainCoils(dfs)                                              l.2379
│   ├─ stackupFor · buildInterconnect(stubLayer, viaAtRing) | spreadPadAngles + corridorPrims · buildMechanical
│   ├─ drcLayerObjects ×2 · padsClearance · via-to-via loop
│   └─ analyzeElements · interconnectResistance · applyConnection · massThermal · driveAnalysis(conductorsFromElements) · commonWarnings
└─ [serpentine]
    ├─ derive(p)                                                                                    l.163
    ├─ maxTracesFit(p) → fitStatus(derive(p)) for N = 1…400                                         l.394
    ├─ buildLayout(D)                                                                               l.671
    │   ├─ buildCanonical(D, busLevelExtra) per phase                                               l.409
    │   │   ├─ fitStatus → maxFillet → filletMetric → minSweep, minStraight → makeCorner, sideLine, nearR, farR, startRadius
    │   │   └─ taperJunctions (when end widths differ)
    │   ├─ stackupFor(p, nCu)                                                                       l.1156
    │   └─ tfPrim / tfPoint / tfAngle, reversePrims (X reversed: current T1 → X → V → Y → T2)
    ├─ buildInterconnect (3 phases, one board, X/Y pairs)                                           l.1225
    ├─ buildMechanical                                                                              l.1101
    ├─ runDrc(D, layout) → canonicalSegments(discretize), makeGrid, drcLayer, drcPadVsLayer, gridQuery, ptSegDist, drcInterconnect   l.756
    ├─ analyze(D, layout) → fieldSetup, fieldHarmonic (48-point radial table per layer and harmonic), discretize,
    │                       primsResistance, viaBarrelArea, ipc2221Current, skinDepthMm                l.880
    ├─ interconnectResistance → applyConnection → massThermal
    ├─ driveAnalysis(p, layout, an, conductorsSerpentine(D, layout), traceWidth)                    l.2725
    └─ commonWarnings (+ TWO_PHASE)
```

UI level (`ui.js` l.252–268): `recompute()` → `readForm()` → `E.compute(p)` → (reference recompute) → `renderAll()` →
`renderCanvas`, `renderLayerBar`, `update3d`, `renderSummary`, `renderHints`, `renderCalc`, `renderDrc`, `renderEmf`,
`renderDrive`, `renderStack`, `renderMech`, `renderCompare`, `renderStatus`. Exports (`ui-main.js` l.52–70) call
`exportSvg/exportDxf/exportOutlineDxf/exportScrewsDxf/exportKicad/makeZip` and `XcoilReport.buildPdf` on `state.lastGood`
— verified (code).

Result object (all topologies): `{params, errors, warnings, ok, derived, layout{layers, vias, links, canon, pads,
interconnect, mech, stackup, nBoards, layersPerBoard, statorThickness, rMinCu, rMaxCu, rMinAll, rMaxAll, (wave|sector|W|S)},
drc{issues, traceClearance, padClearance, linkClearance, padPadClearance, interconnectClearance, viaGap, pairsChecked, ok},
analysis{field, fe, omegaM, layerRes, phases, Ke1, …, inductance, torqueSpeed, thermal}}` — verified (code, l.2511–2550,
l.1940, l.2192, l.2453).

## 5. Observations relevant to the port (details in the other files)

| # | Observation | Status |
|---|---|---|
| O-1 | Three topology code paths share primitives, field, assembly, interconnect, mechanics and exports, but serpentine has its own canonical-frame DRC and `analyze`, while wave/sector use the generic `drcObjects`/`analyzeElements`. A Python port that keeps only the generic path for the spiral generator avoids porting `runDrc`/`analyze`. | inferred (code structure) |
| O-2 | Results carry no units, assumptions, equation IDs or validation status; labels and units live in UI strings (`ui-panels.js`), the PDF (`report.js`) and `COMPARE_METRICS`. | verified (code) |
| O-3 | The KiCad export targets file version 20221018 (KiCad 7 era, title "KiCad 7+ board", `body.html` l.98) and uses layer ordinals 0…31; whether KiCad 9 opens it unchanged has not been tested. | verified (code) / not tested (KiCad 9) |
| O-4 | Golden regression passes only with `interconnect:false` (§0). | verified (run) |
| O-5 | Agent 2's gate (`equation_specification_draft.md`) marks `starOfSlots`, `balancedSectorList`, `kdAnalytic`, the sector turn limit as `replace`, and inductance, IPC-2221, torque–speed as `cannot verify yet`. These sit in F-12, F-28, F-33, F-34, F-35. | verified (cross-reference) |
| O-6 | Phase identification on canvas, layer chips, charts, PDF and 3-D relies on red/blue/green (`style.css` l.6, `report.js` l.7) — conflicts with the white/grey/black primary palette. | verified (code) |

## Revision 2026-10-04 (defect fixes)

- Observation O-e (Agent 4): F-36 and the call graph cited `engine.js` l.1377 (the density-constant line) for
  `massThermal`; corrected to constants l.1377, function l.1378–1394.
