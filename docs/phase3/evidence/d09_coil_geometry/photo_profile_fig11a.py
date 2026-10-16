"""Averaged radial luminance profile along one coil bisector in the Fig. 11a photo (coil labelled C2).

Usage: python3 -I photo_profile_fig11a.py <page-7 image 0 PNG from pdfimages>
Centre (307.25, 309.66) px and hole radius 132.84 px come from measure_d09_figures.py. The C2 window centre
(380, 122) px was picked by eye from the photo; the bisector angle follows from it.
"""

import sys

import numpy as np
from PIL import Image
from scipy import ndimage

CX, CY, R_HOLE = 307.25, 309.66, 132.84
img = np.asarray(Image.open(sys.argv[1]).convert("L"), dtype=float)
t = np.arctan2(122 - CY, 380 - CX)
print(f"C2 bisector {np.degrees(t) % 360:.1f} deg")
h = np.arange(R_HOLE - 4, 215, 0.1)
sw = np.arange(-4, 4.01, 0.5)
ang = t + np.outer(1 / h, sw)
xs, ys = CX + np.outer(h, np.ones_like(sw)) * np.cos(ang), CY + np.outer(h, np.ones_like(sw)) * np.sin(ang)
prof = ndimage.map_coordinates(img, [ys.ravel(), xs.ravel()], order=1).reshape(xs.shape).mean(axis=1)
sm = ndimage.gaussian_filter1d(prof, 3)
pk = [i for i in range(30, len(sm) - 30) if sm[i] == sm[i - 30 : i + 31].max() and sm[i] - sm[i - 30 : i + 31].min() > 6]
print("bright-line peaks (r px, lum):", [(round(h[i], 1), round(sm[i])) for i in pk])
print("bright-line spacing px:", np.round(np.diff(h[pk]), 2).tolist())
for r0 in range(130, 215, 5):
    i = np.searchsorted(h, r0)
    print(f"  r {r0} px: lum {prof[i]:.0f}")
