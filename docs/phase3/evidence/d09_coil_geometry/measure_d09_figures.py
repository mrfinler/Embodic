"""Measure the D09 concentric coil from the paper's own figures (Fig. 1a drawing, Fig. 11a photo).

Usage: python3 -I measure_d09_figures.py <path to EPA-2020-0622-FINAL.pdf> <scratch dir>

Needs poppler `pdfimages`, numpy, scipy and Pillow. Prints every pixel measurement it uses.
"""

import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

PITCH_MM = 0.8 + 0.2  # D09 Table 2 p.3: trace width 0.8 mm, trace clearance 0.2 mm
FIG1A_BOX = (0, 0, 700, 700)  # left panel of page 2 image 0 (Fig. 1 a)
FIG11A_BOX = (0, 0, 700, 700)  # left panel of page 7 image 0 (Fig. 11 a)


def extract(pdf, page, scratch):
    stem = scratch / f"p{page}"
    subprocess.run(["pdfimages", "-f", str(page), "-l", str(page), "-png", str(pdf), str(stem)], check=True)
    return np.asarray(Image.open(f"{stem}-000.png").convert("RGB"), dtype=float)


def sample(img, xs, ys):
    return np.stack(
        [ndimage.map_coordinates(img[..., c], [ys, xs], order=1, mode="nearest") for c in range(img.shape[2])], axis=-1
    )


def fit_circle(xs, ys):
    a = np.column_stack([xs, ys, np.ones_like(xs)])
    b = xs**2 + ys**2
    (c0, c1, c2), *_ = np.linalg.lstsq(a, b, rcond=None)
    cx, cy = c0 / 2, c1 / 2
    r = np.sqrt(c2 + cx**2 + cy**2)
    resid = np.hypot(xs - cx, ys - cy) - r
    return cx, cy, r, resid


def hole_circle(white, seed):
    lab, _ = ndimage.label(white)
    hole = lab == lab[seed[1], seed[0]]
    edge = hole & ~ndimage.binary_erosion(hole)
    ys, xs = np.nonzero(edge)
    return fit_circle(xs.astype(float), ys.astype(float)), hole


def runs(mask):
    """(start, stop) index pairs of True runs."""
    d = np.diff(np.concatenate([[0], mask.astype(int), [0]]))
    return list(zip(np.nonzero(d == 1)[0], np.nonzero(d == -1)[0]))


def gap_peaks(g, lo, hi, prominence):
    """Local maxima of the whiteness profile g between indices lo and hi (turn gaps)."""
    seg = g[lo:hi]
    idx = [i for i in range(1, len(seg) - 1) if seg[i] >= seg[i - 1] and seg[i] > seg[i + 1]]
    keep = []
    for i in idx:
        left = seg[max(0, i - 25) : i + 1].min()
        right = seg[i : i + 26].min()
        if seg[i] - max(left, right) >= prominence:
            keep.append(lo + i)
    return keep


def profile(img, xs, ys):
    """Mean green value over axis 1; red and blue copper are dark in green, gaps and windows are bright."""
    return sample(img, xs.ravel(), ys.ravel())[:, 1].reshape(xs.shape).mean(axis=1)


def bands(d, prof, lo, hi):
    """Gap peaks and red bands of an averaged profile between positions lo and hi."""
    i_lo, i_hi = np.searchsorted(d, lo), np.searchsorted(d, hi)
    pk = gap_peaks(prof, i_lo, i_hi, 15)
    edges = [i_lo] + pk + [i_hi]
    red = [(p, q) for p, q in zip(edges[:-1], edges[1:]) if q - p > 20 and prof[p:q].min() < 100]
    prom = [prof[i] - max(prof[max(0, i - 25) : i + 1].min(), prof[i : i + 26].min()) for i in pk]
    return dict(peaks=d[pk], n_bands=len(red), prominence=float(np.mean(prom)) if prom else 0.0)


def side_profiles(img, cx, cy, a_deg, ext):
    """Average the profile across each coil side under two shape models and count the red bands.

    Lateral sides: 'parallel' keeps a constant distance from the sector edge line, 'radial' keeps a constant angle.
    Inner and outer sides: 'chord' is a straight line normal to the bisector, 'arc' keeps a constant radius.
    """
    t = np.radians(a_deg)
    b, tn = np.array([np.cos(t), np.sin(t)]), np.array([-np.sin(t), np.cos(t)])
    out = {}
    r0 = np.arange(ext["r_win_in"] + 2, ext["r_win_out"] - 2, 0.5)
    rm = r0.mean()
    d = np.arange(-3, 40, 0.1)
    for name, sgn in (("cw", -1), ("ccw", 1)):
        phi = t + sgn * np.radians(15)
        u = np.array([np.cos(phi), np.sin(phi)])
        n = -sgn * np.array([-np.sin(phi), np.cos(phi)])
        par = profile(img, cx + np.outer(d, np.ones_like(r0)) * n[0] + np.outer(np.ones_like(d), r0) * u[0],
                      cy + np.outer(d, np.ones_like(r0)) * n[1] + np.outer(np.ones_like(d), r0) * u[1])
        ang = phi - sgn * np.outer(d / rm, np.ones_like(r0))
        rad = profile(img, cx + r0 * np.cos(ang), cy + r0 * np.sin(ang))
        res = {}
        for model, prof in (("parallel", par), ("radial", rad)):
            w = np.nonzero(prof > 200)[0]
            w_edge = d[w[w > np.searchsorted(d, 5)][0]] if (w > np.searchsorted(d, 5)).any() else d[-1]
            res[model] = dict(window_edge=w_edge, **bands(d, prof, -1.5, w_edge))
        out[name] = res
    sw = np.arange(-5, 5.01, 0.5)
    for name, lo, hi in (("inner", ext["r_cu_in"] - 4, ext["r_win_in"] + 1),
                         ("outer", ext["r_win_out"] - 1, ext["r_cu_out"] + 2)):
        h = np.arange(lo, hi, 0.1)
        chord = profile(img, cx + np.outer(h, np.ones_like(sw)) * b[0] + np.outer(np.ones_like(h), sw) * tn[0],
                        cy + np.outer(h, np.ones_like(sw)) * b[1] + np.outer(np.ones_like(h), sw) * tn[1])
        ang = t + np.outer(1 / h, sw)
        arc = profile(img, cx + np.outer(h, np.ones_like(sw)) * np.cos(ang),
                      cy + np.outer(h, np.ones_like(sw)) * np.sin(ang))
        out[name] = {m: bands(h, prof, lo + 2, hi) for m, prof in (("chord", chord), ("arc", arc))}
    return out


def fig1a(pdf, scratch):
    img = extract(pdf, 2, scratch)[FIG1A_BOX[1] : FIG1A_BOX[3], FIG1A_BOX[0] : FIG1A_BOX[2]]
    r_, g_, b_ = img[..., 0], img[..., 1], img[..., 2]
    white = (r_ > 200) & (g_ > 200) & (b_ > 200)
    red = (r_ > 150) & (g_ < 110) & (b_ < 110)
    blue = (b_ > 150) & (r_ < 110) & (g_ < 110)

    (cx, cy, r_in_edge, res), hole = hole_circle(white, (300, 290))
    print(f"Fig.1a hole: white-region edge circle centre ({cx:.2f}, {cy:.2f}) px, r = {r_in_edge:.2f} px, "
          f"fit residual rms {res.std():.2f} px, max |res| {np.abs(res).max():.2f} px")

    # Black outline circle of the hole: centre of the dark run just outside the white hole, on 720 rays.
    th = np.radians(np.arange(0, 360, 0.5))
    rr = np.arange(r_in_edge - 3, r_in_edge + 12, 0.05)
    xs = cx + np.outer(np.cos(th), rr)
    ys = cy + np.outer(np.sin(th), rr)
    dark = 255 - sample(img, xs.ravel(), ys.ravel()).mean(axis=1).reshape(xs.shape)
    rc = (dark * rr).sum(axis=1) / dark.sum(axis=1)
    bx, by, r_hole_line, res = fit_circle(cx + rc * np.cos(th), cy + rc * np.sin(th))
    print(f"Fig.1a hole outline (black line centre, 720 rays): centre ({bx:.2f}, {by:.2f}) px, r = {r_hole_line:.2f} px, "
          f"residual rms {res.std():.2f} px")
    cx, cy = bx, by

    # Outermost copper on each ray (red or blue), before the black board outline.
    rr = np.arange(r_hole_line, 330, 0.25)
    xs = cx + np.outer(np.cos(th), rr)
    ys = cy + np.outer(np.sin(th), rr)
    cu = (red | blue).astype(float)
    on = ndimage.map_coordinates(cu, [ys.ravel(), xs.ravel()], order=0).reshape(xs.shape) > 0.5
    r_cu_out = np.array([rr[np.nonzero(row)[0].max()] if row.any() else np.nan for row in on])
    r_cu_in = np.array([rr[np.nonzero(row)[0].min()] if row.any() else np.nan for row in on])

    # Coil windows: enclosed white components inside the copper annulus.
    lab, n = ndimage.label(white & ~hole)
    win = []
    for k in range(1, n + 1):
        ys_k, xs_k = np.nonzero(lab == k)
        if not 500 < len(xs_k) < 3000:
            continue
        mx, my = xs_k.mean(), ys_k.mean()
        rk = np.hypot(mx - cx, my - cy)
        if r_hole_line + 10 < rk < 230:
            win.append((np.degrees(np.arctan2(my - cy, mx - cx)) % 360, rk, len(xs_k), k))
    win.sort()
    print(f"Fig.1a windows found: {len(win)}")
    for a, rk, area, _ in win:
        print(f"  window at {a:7.2f} deg, centroid r {rk:6.2f} px, area {area} px")
    ang = np.array([w[0] for w in win])
    spacing = np.diff(np.concatenate([ang, [ang[0] + 360]]))
    print(f"  window spacing deg: {np.round(spacing, 2).tolist()}")

    rows = []
    for a, rk, _, k in win:
        t = np.radians(a)
        # Extents along the coil bisector: copper start and end, window start and end.
        rr = np.arange(r_hole_line, 320, 0.1)
        s = sample(img, cx + rr * np.cos(t), cy + rr * np.sin(t))
        is_cu = ((s[:, 0] > 150) & (s[:, 1] < 150)) | ((s[:, 2] > 150) & (s[:, 0] < 150))
        cu_idx = np.nonzero(is_cu)[0]
        i0, i3 = cu_idx.min(), cu_idx.max()
        wruns = [(p, q) for p, q in runs(s[:, 1] > 200) if q - p > 30 and p > i0 and q < i3]
        wp, wq = max(wruns, key=lambda pq: pq[1] - pq[0])
        ext = dict(r_cu_in=rr[i0], r_win_in=rr[wp], r_win_out=rr[wq], r_cu_out=rr[i3])
        rows.append(dict(angle=a, rk=rk, **ext, sides=side_profiles(img, cx, cy, a, ext)))
    return dict(cx=cx, cy=cy, r_hole_line=r_hole_line, r_cu_out=r_cu_out, r_cu_in=r_cu_in, rows=rows, th=th)


def report_fig1a(m):
    print("\nFig.1a per-coil extents along the window bisector (px from hole-outline centre):")
    for row in m["rows"]:
        print(f"  {row['angle']:6.1f} deg: copper {row['r_cu_in']:.1f}..{row['r_cu_out']:.1f}, "
              f"window {row['r_win_in']:.1f}..{row['r_win_out']:.1f}")
    print("\nFig.1a red bands per coil side from averaged profiles (gap peaks with prominence >= 15 in green):")
    spac = []
    for row in m["rows"]:
        sd = row["sides"]
        line = []
        for side, models in sd.items():
            line.append(side + " " + " ".join(f"{mo}={v['n_bands']}(prom {v['prominence']:.0f})" for mo, v in models.items()))
            best = max(models.values(), key=lambda v: v["prominence"])
            dd = np.diff(best["peaks"])
            spac += dd[(dd > 3) & (dd < 8)].tolist()
        print(f"  {row['angle']:6.1f} deg: " + "; ".join(line))
    for row in m["rows"][:2]:
        for side, models in row["sides"].items():
            for mo, v in models.items():
                print(f"    peaks {row['angle']:.1f} {side} {mo}: {np.round(v['peaks'], 1).tolist()}"
                      + (f" window edge {v['window_edge']:.1f}" if "window_edge" in v else ""))
    p = np.array(spac)
    print(f"  gap-to-gap spacing (best model per side, 3..8 px): n {len(p)}, median {np.median(p):.3f} px, "
          f"mean {p.mean():.3f}, sd {p.std():.3f}, p5 {np.percentile(p, 5):.2f}, p95 {np.percentile(p, 95):.2f}")
    return float(np.median(p)), p


def fig11a(pdf, scratch):
    img = extract(pdf, 7, scratch)[FIG11A_BOX[1] : FIG11A_BOX[3], FIG11A_BOX[0] : FIG11A_BOX[2]]
    lum = img.mean(axis=2)
    white = lum > 215
    (cx, cy, r, res), hole = hole_circle(white, (340, 300))
    ys, xs = np.nonzero(hole & ~ndimage.binary_erosion(hole))
    ang = np.degrees(np.arctan2(ys - cy, xs - cx)) % 360
    rad = np.hypot(xs - cx, ys - cy)
    dirs = {}
    for a0 in (0, 45, 90, 135):
        sel = (np.abs((ang - a0 + 180) % 360 - 180) < 3) | (np.abs((ang - a0 - 180 + 180) % 360 - 180) < 3)
        dirs[a0] = 2 * rad[sel].mean()
    print(f"\nFig.11a hole edge circle: centre ({cx:.2f}, {cy:.2f}) px, r = {r:.2f} px, residual rms {res.std():.2f} px, "
          f"max |res| {np.abs(res).max():.2f} px")
    print("  hole diameter by direction (px): " + ", ".join(f"{k} deg {v:.1f}" for k, v in dirs.items()))
    return dict(img=img, lum=lum, cx=cx, cy=cy, r=r)


def main():
    pdf, scratch = Path(sys.argv[1]), Path(sys.argv[2])
    scratch.mkdir(parents=True, exist_ok=True)
    m = fig1a(pdf, scratch)
    pitch_px, spac = report_fig1a(m)
    k = pitch_px / PITCH_MM
    print(f"\nScale from the turn pitch: {pitch_px:.3f} px per {PITCH_MM:.1f} mm -> {k:.3f} px/mm")
    r_out = m["r_cu_out"]
    r_in = m["r_cu_in"]
    print(f"Fig.1a hole outline radius {m['r_hole_line']:.2f} px = {m['r_hole_line'] / k:.2f} mm "
          f"(diameter {2 * m['r_hole_line'] / k:.2f} mm)")
    print(f"Fig.1a copper inner edge over 720 rays: median {np.nanmedian(r_in):.2f} px = {np.nanmedian(r_in) / k:.2f} mm, "
          f"min {np.nanmin(r_in):.2f}, max {np.nanmax(r_in):.2f} px")
    print(f"Fig.1a copper outer edge over 720 rays: median {np.nanmedian(r_out):.2f} px = {np.nanmedian(r_out) / k:.2f} mm, "
          f"p10 {np.nanpercentile(r_out, 10):.2f}, p90 {np.nanpercentile(r_out, 90):.2f} px")
    print("Fig.1a per-coil radii in mm (scale above):")
    for row in m["rows"]:
        print(f"  {row['angle']:6.1f} deg: copper {row['r_cu_in'] / k:5.2f}..{row['r_cu_out'] / k:5.2f} mm, "
              f"window {row['r_win_in'] / k:5.2f}..{row['r_win_out'] / k:5.2f} mm")
    ratio = 50.0 / 92.0
    print(f"Check: hole-outline / copper-outer radius ratio {m['r_hole_line'] / np.nanmedian(r_out):.4f}; "
          f"D09 Table 2 ID/OD 50/92 = {ratio:.4f}")
    fig11a(pdf, scratch)


if __name__ == "__main__":
    main()
