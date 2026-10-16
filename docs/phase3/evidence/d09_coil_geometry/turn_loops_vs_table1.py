"""Turn perimeters and areas of the Fig. 1a coil, from the band centres printed by measure_d09_figures.py.

Usage: python3 -I turn_loops_vs_table1.py
Band centres are px from the hole-outline centre (inner, outer sides) or from the sector-edge gap (lateral sides),
read from the 12.5 deg and 42.5 deg coils in logs/measure_d09_figures.log. Compares with D09 Table 1 p.3
(phase trace length 3244 mm, mid-turn covered area 171 mm^2).
"""

import numpy as np

INNER_GAPS = [132.3, 137.5, 142.6, 147.9, 153.3, 158.5]  # gap peaks, hole side to window
OUTER_GAPS = [205.1, 210.3, 215.3, 220.6, 225.8, 231.0, 236.2]  # gap peaks, window to the 7th band's outer edge
LAT_GAPS = [0.0, 5.9, 11.0, 16.2, 21.3, 26.5, 31.8]  # parallel model, sector-edge gap to window
LAT_WINDOW_EDGE = 37.2
PITCH = 5.2
HALF_SECTOR = np.radians(15.0)


def centres():
    ri = [INNER_GAPS[0] - PITCH / 2] + [(a + b) / 2 for a, b in zip(INNER_GAPS, INNER_GAPS[1:])] + [INNER_GAPS[-1] + PITCH / 2]
    ro = [OUTER_GAPS[0] - PITCH / 2] + [(a + b) / 2 for a, b in zip(OUTER_GAPS, OUTER_GAPS[1:])]
    lat = [(a + b) / 2 for a, b in zip(LAT_GAPS, LAT_GAPS[1:] + [LAT_WINDOW_EDGE])]
    # Index 0 = outermost turn (next to the hole, the outer rim and the sector edge).
    return np.array(ri), np.array(ro[::-1]), np.array(lat)


def loop(ri, ro, o, sides):
    """Closed centre line: two lateral lines at distance o from the sector-edge radials, inner and outer sides."""
    pts = []
    for r, sgn in ((ro, 1), (ri, -1)):
        half = HALF_SECTOR - np.arcsin(o / r)
        if sides == "arc":
            th = np.linspace(half, -half, 200) * sgn
            pts += list(zip(r * np.cos(th), r * np.sin(th)))
        else:
            pts += [(r * np.cos(half * sgn), r * np.sin(half * sgn)), (r * np.cos(-half * sgn), r * np.sin(-half * sgn))]
    p = np.array(pts)
    x, y = p[:, 0], p[:, 1]
    area = 0.5 * abs(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))
    per = np.hypot(np.diff(np.append(x, x[0])), np.diff(np.append(y, y[0]))).sum()
    return per, area


ri_px, ro_px, lat_px = centres()
print("turn (0 = outermost) | inner-side r | outer-side r | lateral offset   (px)")
for k in range(7):
    print(f"  {k} | {ri_px[k]:6.2f} | {ro_px[k]:6.2f} | {lat_px[k]:5.2f}")
for label, k in (("pitch scale 5.200 px/mm (Table 2 width + clearance)", 5.2),
                 ("hole scale 5.134 px/mm (hole outline = 50 mm, Table 2 inner diameter)", 2 * 128.34 / 50)):
    ri, ro, lat = ri_px / k, ro_px / k, lat_px / k
    print(f"\n{label}")
    print(f"  outermost turn centre lines: inner side r {ri[0]:.2f} mm, outer side r {ro[0]:.2f} mm, "
          f"lateral offset {lat[0]:.2f} mm; innermost turn: {ri[6]:.2f} / {ro[6]:.2f} mm, offset {lat[6]:.2f} mm")
    for sides in ("chord", "arc"):
        res = [loop(ri[j], ro[j], lat[j], sides) for j in range(7)]
        per = np.array([r[0] for r in res])
        area = np.array([r[1] for r in res])
        print(f"  {sides:5s} sides: turn perimeters mm {np.round(per, 1).tolist()}; sum {per.sum():.1f} mm per coil-layer; "
              f"x 8 coil-layers = {8 * per.sum():.0f} mm (Table 1: 3244 mm, {8 * per.sum() / 3244 - 1:+.1%})")
        print(f"         turn areas mm^2 {np.round(area, 1).tolist()}; middle (4th of 7) {area[3]:.1f} mm^2 "
              f"(Table 1: 171 mm^2, {area[3] / 171 - 1:+.1%})")
