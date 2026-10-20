Prepared by: Agent 1 (UX/UI Expert Designer) - model: claude-opus-5-5

# U-S16: a layer cue for the geometry view (DEF-UV16-02, DEF-UV16-03)

Date 2026-10-20. Branch `unit/U-S16` on main 14c8b7a. The spec text is in `docs/phase2/design/design_spec.md` section
3.3.1. The acceptance rows are UI-58 to UI-61 in `docs/phase2/architecture/test_plan.md` section 5.3. Every claim
carries one status label. Nothing here ran on Windows (standing order 8). The renders ran in the Linux container with
the worktree source, `/home/claude/embodic/.venv/bin/python`, PySide6 6.11.2, `QT_QPA_PLATFORM=offscreen`, one
process, beside the running 0.0.3 release gate.

## The problem

The user read D08 as shorted. U-V16 measured every same-layer gap at the 0.8 mm rule and found the cause in the view:
L2 and then L1 drawn opaque, one ink per phase, so the mirrored L2 spiral closes the L1 spiral into loops and the L1
rings join the L2 legs (`verified` there). The 0.0.3 drawing in this unit's renders reproduces it: at the ring A over
leg 24 crossing the leg and the ring are the same pixel colour (`now` rows below).

## Constraints

1. Copper on different layers never reads as joined while two or more layers are visible.
2. Copper on one layer reads at true width.
3. Phase colours A, B and C stay.
4. Works in Windows high contrast, where the drawing is greyscale (REQ-N-23, `fix_wave_f1.md` (b)).
5. Works for colour-blind readers.
6. Works on the 6-layer serpentine example.

Constraints 3 to 5 rule out any cue that changes lightness. In greyscale, lightness is the phase cue (section 3.4
ladder). In colour, the lightness gap is what keeps red and green apart for deutan readers (section 3.2). A layer cue
made of lightness collides with both.

## Candidates

The lever is `checks/u_s16/u_s16_layer_cue_renders.py`. Each candidate subclasses the product's `GeometryView` and
replaces only the copper drawing, so board, eyes, labels and legend are the product's own. It is a throwaway prototype,
not product code. Rerun:

```
PYTHONPATH=src QT_QPA_PLATFORM=offscreen /home/claude/embodic/.venv/bin/python \
    docs/phase3/design/checks/u_s16/u_s16_layer_cue_renders.py docs/phase3/design/checks/u_s16
```

| Id | Candidate | Rule |
|---|---|---|
| now | 0.0.3 | every layer opaque, L2 then L1 |
| A | Per-layer opacity (Xcoil v3 `ui.js` l.318) | layer index even 0.95, odd 0.62, each layer filled once as a union, so overlaps inside one layer do not darken |
| B | Top solid, lower outlined | top visible layer solid; every lower visible layer a 1.5 px outline inside its true edge, empty inside |
| C | Casing | every layer solid; each layer except the bottom one gets a 2 px `board-fill` band around its copper, over the layers already drawn |
| D | B + C | the outline of B and the casing of C on every layer except the bottom one |

Contact sheets (rows: now, A, B, C, D; columns: dark colour, dark greyscale, light greyscale; all layers visible):

- `checks/u_s16/u_s16_d08_region.png`: the user's screenshot region, x -41.0 to 50.6 mm, y -1.2 to 56.1 mm, 6 px/mm.
- `checks/u_s16/u_s16_d08_crossing.png`: ring A (path 32, L1, 1.0 mm) over leg 24 (L2, 0.6 mm) at (-11.01, 47.19) mm,
  24 px/mm.
- `checks/u_s16/u_s16_serpentine_fit.png`: serpentine_16p_example, 6 layers, 5 px/mm (the 0.4 mm tracks are 2 px).
- `checks/u_s16/u_s16_serpentine_4x.png`: the same at 20 px/mm.

## Measurements (`verified`, `checks/u_s16/u_s16_measurements.json`)

Edge contrast: at the D08 crossing, the largest contrast between the ring pixel and the leg's centre-line pixels 1 to
4 px beyond the ring's edge. Band ink: for each visible layer except the bottom one, the share of pixels 0.75 to 1.5 px
outside its copper (copper above, lands, eyes, legend, stamp and labels left out) whose contrast to `board-fill` is
above 1.1. That share is lower-layer copper touching upper copper on screen.

| Id | Edge contrast, dark colour / dark grey / light grey | Band ink, D08 region | Band ink, serpentine fit | Band ink, serpentine 4x |
|---|---|---|---|---|
| now | 1.0 / 1.0 / 1.0 | 8.0 to 8.2 % | 12.5 to 12.6 % | 5.2 % |
| A | 1.57 / 2.15 / 3.16 | 7.8 to 8.0 % | 12.5 % | 5.2 % |
| B | 3.09 / 12.34 / 14.13 | 3.7 to 3.9 % | 12.5 % | 3.8 to 4.0 % |
| C | 3.09 / 12.34 / 14.13 | 0.03 % | 0.04 % | 0.25 % |
| D | 3.09 / 12.34 / 14.13 | 0.03 % | 0.04 % | 0.30 to 0.31 % |

The edge contrast of B, C and D equals the phase ink against `board-fill` (3.09:1 is the dark phase A figure of
section 3.2), so it holds for every phase in every mode where section 3.2 and 3.4 hold. The leg's drawn width at
radius 49.36 mm is 14.75 px in dark colour and 15.5 px in greyscale for 0.0.3 and for D, and 14.5 to 15.5 px for the
others, against a true 14.4 px: no candidate widens copper there.

## Choice: D (`verified` by the measurements; how users read it is `not tested`)

C and D pass both checks in every mode on both examples. Only D also shows the layer of a piece of copper away from
any crossing: the centre of the L2 leg at radius 49.36 mm is `board-fill` in D and phase ink in C (`lower_centre_px`).
In C a solid piece of copper could be on any layer; in D solid means the top layer and an outline means a layer below,
which is what the legend rows say. D changes form, not colour: copper on the top layer is solid, copper below is empty
inside, and a gap of board separates them. Neither depends on hue or lightness, so constraints 3, 4 and 5 hold by
construction, and D's band share is the same in all three modes. In the D08 region the L1 coils read as the open spirals of the L1-only view, the L2 copper shows as thin outlines
beside them, and the 0.8 mm channels of L1 are clear because the casing removes the L2 copper inside them (visual
reading of `u_s16_d08_region.png`, `inferred`).

Why not the others:

- A fails both checks. It also moves phase A on L2 into the phase B step of the grey ladder: the drawn L2 pixel in dark
  greyscale is `#979797` against phase B `#a8a8a8`, 1.23:1 (measured pixel, computed ratio). That breaks constraint 4.
- B fails the band check: an outline meets the solid top copper in the same ink, so at a crossing the two still touch.
  At serpentine fit zoom the 2 px tracks cannot be hollow, so B adds nothing there (12.5 %, as 0.0.3).
- C passes both checks, but the lower copper stays solid in its phase ink, so its layer is visible only at an edge. In
  the D08 region the coils still read as dense closed loops with thin dark seams, and a 2 px casing seam looks like a
  narrow clearance gap (`inferred` from the renders). D keeps C's casing and adds B's form cue.

Cost of D. Lower layers are context: they stop 2 px short of upper copper and are empty inside, so the serpentine's
all-layer view shows phases B and C (L3 to L6) as outlines. The legend rows say which layer is on top. To check a lower
layer at true width the user solos it with `[` and `]`, which already exist. With one visible layer nothing changes.

## Notes for Agent 3 (view and test)

- The prototype builds each lower layer's outline from `QPainterPath.simplified()` of the union. In the committed
  run that took 0.56 to 0.71 s per serpentine redraw and 0.01 s for D08 (`union_seconds`, measured beside the release
  gate on a 2-CPU machine; an earlier run gave 0.81 to 1.10 s, so the figure moves with load). Do not ship it. The casing and the outline are screen pixels, so they must follow each zoom step. A
  per-layer item that paints in device pixels, as `EyeItem` does, avoids a rebuild: fill the layer's copper (each
  primitive stroked at its width, one path, `WindingFill`) into a layer, knock out the same path stroked at its width
  less 2 x 1.5 px with `CompositionMode_DestinationOut`, and paint the casing (width plus 2 x 2 px, `board-fill`)
  before it. That route is `inferred`; it is not built or timed here.
- UI-59 is the strong check: it is red on 0.0.3 (5.2 to 12.6 %) and green on D (at most 0.31 %). The lever implements
  it (`band_violations`), so the test can reuse its definition.
- The serpentine example has no crossing of straight copper between layers: its sides are radial and parallel
  (`verified` by a scratch search for line-line crossings between L1/L2, L3/L4, L5/L6 and L1/L3, 0 found). Its layers
  meet side by side, which the band check covers and a crossing probe would not.

## Lands (DEF-UV16-03)

Section 3.3.1 of the design spec: a round pad is a circle of diameter `width_mm`; a square, rect or oblong pad is the
filled shape of `pad_outline(pad)`; a drill shows as a `canvas` disc, as the DXF, SVG and PDF writers draw them. Vias
and pads are drawn after all copper and are never outlined or cased, because they are the designed joints between
layers. The lever draws pads this way; the serpentine fit sheet shows that example's round pads with their drills.
UI-61 checks the rule.

## Open questions for Fable

1. The REQ-F-13 row of the requirements matrix (test plan section 8) should name UI-58 to UI-61. This unit wrote only
   the UI rows of section 5.3, so the matrix is not changed.
2. Whether the user reads D08 correctly with cue D is `not tested`. A one-screen check with the user on Windows, D08
   at fit zoom with all layers, would settle it.
3. Vias show no drill in the view, while the exporters draw one. This unit leaves vias as they are.
