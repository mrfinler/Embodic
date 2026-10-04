Prepared by: Fable 5.1 — coordinator — model: claude-fable-5-1 (configured id; serving model may differ)

# Reference images (user-supplied, 2026-10-04)

Provenance: screenshots attached by the user in chat on 2026-10-04. Treat as *illustrative* evidence
(resolution ~676 px; no dimensions, no layer data, no electrical data). Status of every geometric
reading below: `inferred from image` unless stated otherwise.

| File | What the user said | What is visible (Fable's reading) |
|---|---|---|
| `instagram_DWvb7wWkz4M_frame1_magnetless_motor_render.png` | Screenshot of Instagram post DWvb7wWkz4M (title overlay "magnetless motor" — same project name as the gouldpa00 repository). | 3-D render of a circular PCB stator. Concentrated **spiral coils** with fanned (radial) straight sides, nested stadium-shaped outer end-turns and small inner end-turns near the hub. Two coil groups rendered in two shades: 8 brighter coils at 45° pitch and 8 darker coils offset by ~22.5°, overlapping each other (coil footprint ≈ 45°, so adjacent coils of the two groups overlap by about half a footprint — consistent with a two-layer-group arrangement, like the "bottom group rotated 15°" rule found in the repository's wave board). ≈ 9–10 turns per coil side. Rows of small dots (vias) along the radial sides near both ends of each coil. Eight mounting holes on the outer rim (Agent 5 count; Fable first wrote six — corrected). Central 12-sided hole with four slot-shaped cut-outs/pads around it; two or three terminal lands near the hub. 16 coil positions is **not divisible by 3** — the phase arrangement cannot be read from the image (`unresolved`). |
| `instagram_DWvb7wWkz4M_frame2_rotor_overlay.png` | Same post, later frame. | Same stator with a rotor-hub overlay and four orthogonal arrows at the centre (animation frame); no additional geometry. |
| `ecm_pcb_stator_octagonal_board_user_supplied.png` | "You can see more from ECM motor" — i.e. ECM PCB Stator Technology (PrintStator). | Photo of a green octagonal PCB stator with a large central bore, a dense radial trace pattern (many fine conductors across the full annulus, not visibly concentrated coils) and three groups of three terminal pads near the lower edge. Low resolution; no dimensions. Use only as a styling/feature reference; cite ECM's public patents or papers for anything technical. |

Rules: no dimensions or electrical values may be taken from these images; any geometry used in the
design must come from parameters the user sets or from cited sources.
