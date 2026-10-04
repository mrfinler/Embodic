"""Rigid transforms and path reversal (Xcoil tfAngle, tfPoint, tfPrim, reversePrims; engine.js l.501-529).

Points are transformed in polar form, as Xcoil does, so the port reproduces Xcoil's rounding: rotation adds to the
``atan2`` angle and mirroring reflects it about the axis angle.
"""

import math
from collections.abc import Sequence
from dataclasses import dataclass, replace

from embodic.geometry.primitives import Line, Primitive, hypot_mm


@dataclass(frozen=True, slots=True, kw_only=True)
class Transform:
    """Mirror about the line through the origin at ``mirror_axis_rad`` (when set), then rotate by ``rotation_rad``.

    Xcoil's ``(tf, thetaG)`` pair maps to ``Transform(rotation_rad=tf.rot, mirror_axis_rad=thetaG if tf.mirror)``.
    """

    rotation_rad: float = 0.0
    mirror_axis_rad: float | None = None


def transform_angle_rad(tf: Transform, angle_rad: float) -> float:
    """Xcoil tfAngle (engine.js l.501)."""
    if tf.mirror_axis_rad is None:
        return tf.rotation_rad + angle_rad
    return tf.rotation_rad + (2 * tf.mirror_axis_rad - angle_rad)


def transform_point(tf: Transform, x_mm: float, y_mm: float) -> tuple[float, float]:
    """Xcoil tfPoint (engine.js l.502)."""
    r_mm = hypot_mm(x_mm, y_mm)
    angle_rad = transform_angle_rad(tf, math.atan2(y_mm, x_mm))
    return (r_mm * math.cos(angle_rad), r_mm * math.sin(angle_rad))


def transform_primitive(tf: Transform, p: Primitive) -> Primitive:
    """Xcoil tfPrim (engine.js l.506). A mirror reverses an arc's sweep; an arc centred on the origin stays there."""
    if isinstance(p, Line):
        x1_mm, y1_mm = transform_point(tf, p.x1_mm, p.y1_mm)
        x2_mm, y2_mm = transform_point(tf, p.x2_mm, p.y2_mm)
        return replace(p, x1_mm=x1_mm, y1_mm=y1_mm, x2_mm=x2_mm, y2_mm=y2_mm)
    cx_mm, cy_mm = (0.0, 0.0) if p.cx_mm == 0 and p.cy_mm == 0 else transform_point(tf, p.cx_mm, p.cy_mm)
    sweep_rad = p.sweep_rad if tf.mirror_axis_rad is None else -p.sweep_rad
    return replace(p, cx_mm=cx_mm, cy_mm=cy_mm, start_rad=transform_angle_rad(tf, p.start_rad), sweep_rad=sweep_rad)


def transform(prims: Sequence[Primitive], tf: Transform) -> tuple[Primitive, ...]:
    """Apply ``tf`` to every primitive; order and direction are kept (a mirrored arc keeps its traversal)."""
    return tuple(transform_primitive(tf, p) for p in prims)


def rotate(prims: Sequence[Primitive], angle_rad: float) -> tuple[Primitive, ...]:
    """Rotate about the origin, counter-clockwise for a positive angle."""
    return transform(prims, Transform(rotation_rad=angle_rad))


def mirror(prims: Sequence[Primitive], axis_angle_rad: float) -> tuple[Primitive, ...]:
    """Reflect about the line through the origin at ``axis_angle_rad``."""
    return transform(prims, Transform(mirror_axis_rad=axis_angle_rad))


def reverse_primitive(p: Primitive) -> Primitive:
    """Swap the end points; an arc starts at its old end angle with the negated sweep."""
    if isinstance(p, Line):
        return replace(p, x1_mm=p.x2_mm, y1_mm=p.y2_mm, x2_mm=p.x1_mm, y2_mm=p.y1_mm)
    return replace(p, start_rad=p.start_rad + p.sweep_rad, sweep_rad=-p.sweep_rad)


def reverse_path(prims: Sequence[Primitive]) -> tuple[Primitive, ...]:
    """Xcoil reversePrims (engine.js l.519): the same copper traversed the other way."""
    return tuple(reverse_primitive(p) for p in reversed(prims))
