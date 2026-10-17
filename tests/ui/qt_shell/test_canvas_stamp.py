"""UI-32 (b) to (f): the geometry view carries the version stamp and design hash (fix_wave_f1.md section (d))."""

import pytest
from PySide6.QtCore import QPoint, QPointF, QRectF, Qt
from PySide6.QtGui import QColor, QImage
from PySide6.QtWidgets import QLineEdit
from tests.ui.qt_shell.conftest import D08

from embodic.ui.viewmodels.outcome import shown_result
from embodic.ui.views.geometry_view import DATA_KIND

D08_STAMP = "embodic 0.0.1 | design 327919a0eef5"  # fix_wave_f1.md (d), D08 hash sha256:327919a0eef5...
SPIRAL_14P = "spiral_12c14p"


def luminance(colour: QColor) -> float:
    """WCAG 2.2 relative luminance of an sRGB colour."""

    def channel(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * channel(colour.redF()) + 0.7152 * channel(colour.greenF()) + 0.0722 * channel(colour.blueF())


def contrast(a: QColor, b: QColor) -> float:
    """WCAG 2.2 contrast ratio of two colours."""
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def pixels(image: QImage, rect: QRectF) -> list[QColor]:
    """Return the colours of an image inside a rectangle given in its pixels."""
    r = rect.toAlignedRect().intersected(image.rect())
    return [image.pixelColor(x, y) for y in range(r.top(), r.bottom() + 1) for x in range(r.left(), r.right() + 1)]


@pytest.fixture
def d08_session(make_shell, wait_ready):
    """Return a shell whose design session holds D08, computed and drawn, with the inspector forms built."""
    shell = make_shell()
    shell.window.session.load_example(D08)
    wait_ready(shell.window)
    return shell


def grab(canvas) -> QImage:
    """Return the canvas viewport as painted now, in viewport pixels."""
    return canvas.viewport().grab().toImage().convertToFormat(QImage.Format.Format_RGB32)


@pytest.mark.req("REQ-T-14")
def test_ui32b_canvas_stamp_names_the_version_and_the_design_hash_at_the_bottom_left(d08_shell):
    """Catches a canvas without the stamp, with the "sha256:" prefix or a short hash, or placed away from the corner."""
    canvas = d08_shell.window.canvas
    assert canvas.stamp() == D08_STAMP
    view = QRectF(canvas.viewport().rect())
    corner = QRectF(view.left(), view.top() + 0.75 * view.height(), 0.5 * view.width(), 0.25 * view.height())
    assert corner.contains(canvas.stamp_rect()), (canvas.stamp_rect(), corner)


@pytest.mark.req("REQ-T-14")
def test_ui32c_the_stamp_is_painted_on_its_plate_and_its_text_reaches_4_5_to_1(d08_shell):
    """Catches a stamp that exists as text but is never painted, or painted too faint to read."""
    canvas = d08_shell.window.canvas
    rect = canvas.stamp_rect()
    shown = grab(canvas)
    canvas.set_stamp(None)
    hidden = grab(canvas)
    assert pixels(shown, rect) != pixels(hidden, rect)
    plate = shown.pixelColor(rect.toAlignedRect().topLeft() + QPoint(1, 1))
    best = max(contrast(colour, plate) for colour in pixels(shown, rect))
    assert best >= 4.5, best


@pytest.mark.req("REQ-T-14")
def test_ui32d_a_stale_drawing_keeps_its_stamp_and_a_new_outcome_renames_it(d08_session, qtbot, wait_ready):
    """Catches a stamp that names the draft instead of the drawing shown, or keeps an old hash after a load."""
    window = d08_session.window
    field = window.findChild(QLineEdit, "param-r-inner")
    field.setFocus()
    field.selectAll()
    qtbot.keyClicks(field, "-1")
    qtbot.keyClick(field, Qt.Key.Key_Return)
    qtbot.waitUntil(lambda: window.stale_label.isVisibleTo(window))
    assert window.canvas.stamp() == D08_STAMP
    window.session.load_example(SPIRAL_14P)
    wait_ready(window)
    outcome = shown_result(window.outcome.state.value).outcome
    assert outcome.design_hash.startswith("sha256:")
    assert window.canvas.stamp() == f"embodic {outcome.versions.embodic} | design {outcome.design_hash[7:19]}"
    assert window.canvas.stamp() != D08_STAMP


@pytest.mark.req("REQ-T-14")
def test_ui32e_at_fit_zoom_no_phase_label_meets_the_stamp(d08_shell):
    """Catches labels placed under the stamp plate: the stamp box must join the label obstacles."""
    canvas = d08_shell.window.canvas
    canvas.fit_view()
    stamp = canvas.stamp_rect()
    labels = [item for item in canvas.scene().items() if item.data(DATA_KIND) == "label"]
    assert labels
    for item in labels:
        size = item.boundingRect().size()
        at = QPointF(canvas.mapFromScene(item.scenePos()))
        box = QRectF(at.x() - size.width() / 2, at.y() - size.height() / 2, size.width(), size.height())
        assert not box.intersects(stamp), (item.text(), box, stamp)


@pytest.mark.req("REQ-T-14")
def test_ui32f_canvas_accessible_description_ends_with_the_stamp(d08_shell):
    """Catches a stamp a screen reader cannot reach."""
    canvas = d08_shell.window.canvas
    assert canvas.accessibleDescription().endswith(D08_STAMP)


@pytest.mark.req("REQ-T-14")
def test_stamp_is_hidden_while_the_canvas_has_no_drawing(make_shell):
    """Catches a stamp left on an empty canvas, which would name a design that is not drawn."""
    canvas = make_shell().window.canvas
    assert canvas.stamp() is None
    assert canvas.stamp_rect().isEmpty()
