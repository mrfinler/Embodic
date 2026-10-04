# Prepared by: Agent 4 — Independent Verificator — model: claude-opus-5-5
# Own parse of arcs in magnetless_motor Gerbers G1 and G3 (read-only) to spot-check EV-71.
# Format %FSLAX44Y44*% %MOMM*% G75 (multi-quadrant); arc centre = start + (I, J).
# Run: python3 docs/phase1/verification/checks/v5_gerber_endturns.py
import re, math, collections
def arcs(path):
    x = y = None; mode = 'G01'; out = []
    for tok in open(path).read().replace('\n', '').split('*'):
        if tok in ('G01', 'G02', 'G03'): mode = tok; continue
        m = re.match(r'^(?:G0[123])?X(-?\d+)Y(-?\d+)(?:I(-?\d+)J(-?\d+))?D0([123])$', tok)
        if not m: continue
        nx, ny = int(m.group(1)) / 1e4, int(m.group(2)) / 1e4
        if m.group(5) == '1' and m.group(3) is not None and mode in ('G02', 'G03'):
            cx, cy = x + int(m.group(3)) / 1e4, y + int(m.group(4)) / 1e4
            out.append((cx, cy, math.hypot(x - cx, y - cy), (x, y), (nx, ny), mode))
        x, y = nx, ny
    return out
for layer in ('G1', 'G3'):
    A = arcs(f'/home/claude/embodic-ref/magnetless_motor/gerbers/mini_wave-bb.{layer}')
    # board centre = centre shared by the largest number of arcs
    cc = collections.Counter((round(a[0], 2), round(a[1], 2)) for a in A)
    (bx, by), nb = cc.most_common(1)[0]
    conc = [a for a in A if abs(a[0] - bx) < 0.02 and abs(a[1] - by) < 0.02]
    other = [a for a in A if a not in conc]
    rc = sorted(set(round(a[2], 1) for a in conc))
    # off-centre arcs: distance of their centre from the board centre and polar angle of that centre
    d = collections.Counter(round(math.hypot(a[0] - bx, a[1] - by), 1) for a in other)
    ang = sorted(set(round(math.degrees(math.atan2(a[1] - by, a[0] - bx)) % 360, 0) for a in other if abs(math.hypot(a[0] - bx, a[1] - by) - 26) < 0.6))
    radii = sorted(set(round(a[2], 1) for a in other if abs(math.hypot(a[0] - bx, a[1] - by) - 26) < 0.6))
    print(f"{layer}: {len(A)} arcs; board centre ({bx}, {by}) shared by {nb}; concentric arcs {len(conc)} radii(mm) {rc[:12]}{'...' if len(rc)>12 else ''}")
    print(f"    off-centre arcs {len(other)}; centre distance histogram (mm:count) {sorted(d.items())[:8]}")
    print(f"    arcs centred at r~26 mm: radii {radii}; centre angles (deg) {ang}")
