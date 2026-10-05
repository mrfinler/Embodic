"""EMF waveforms of one electrical period (EQ-18)."""

import math
from collections.abc import Mapping, Sequence

import numpy as np

from embodic.model.vocabulary import ConnectionTopology
from embodic.units import FloatArray

XCOIL_WAVEFORM_SAMPLES = 181


def emf_waveform_v(phasors_v: Mapping[int, complex], samples: int = XCOIL_WAVEFORM_SAMPLES) -> FloatArray:
    """Return E(theta_e) = sum_n |E_n| cos(n theta_e + arg E_n) on samples points from 0 to 2 pi inclusive.

    References: EQ-18 (Xcoil emfWaveform, engine.js l.1020-1033).

    Parameters
    ----------
    phasors_v : Mapping[int, complex]
        Peak EMF phasor in V by harmonic order.
    samples : int
        Points per period, both ends included.

    Returns
    -------
    FloatArray
        EMF in V.
    """
    theta = 2.0 * math.pi * np.arange(samples) / (samples - 1)
    out = np.zeros(samples)
    for n, e in phasors_v.items():
        out += abs(e) * np.cos(n * theta + math.atan2(e.imag, e.real))
    return out


def line_waveforms_v(phase_waveforms_v: Sequence[FloatArray], topology: ConnectionTopology) -> tuple[FloatArray, ...]:
    """Return the line-to-line EMF waveforms.

    References: EQ-18 (Xcoil lineWaveform, engine.js l.1441-1447). Star: differences U-V, V-W, W-U; delta: each phase
    minus the mean of the three (the circulating-current drop); open: the phase waveforms.

    Parameters
    ----------
    phase_waveforms_v : Sequence[FloatArray]
        Phase EMF waveforms in V, in phase order.
    topology : ConnectionTopology
        Star, delta or open.

    Returns
    -------
    tuple[FloatArray, ...]
        Line EMF waveforms in V.
    """
    ph = list(phase_waveforms_v)
    match topology:
        case ConnectionTopology.STAR:
            return tuple(ph[k] - ph[(k + 1) % 3] for k in range(3))
        case ConnectionTopology.DELTA:
            mean = (ph[0] + ph[1] + ph[2]) / 3.0
            return tuple(w - mean for w in ph[:3])
        case ConnectionTopology.OPEN:
            return tuple(ph)
