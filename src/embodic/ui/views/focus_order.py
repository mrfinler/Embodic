"""Tab order in reading order (REQ-N-12: Tab order equals visual order).

Qt chains the widgets of a window in the order they join it, and a widget that moves inside the window keeps its
place. A widget added to a built window, or built after the widgets below it, therefore lands at the window's end or
above its place. These helpers chain such widgets in the order their layouts show them.
"""

from collections.abc import Iterator, Sequence
from itertools import pairwise

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFormLayout, QLayout, QWidget

FORM_ROLES = (QFormLayout.ItemRole.LabelRole, QFormLayout.ItemRole.FieldRole, QFormLayout.ItemRole.SpanningRole)


def takes_tab(widget: QWidget) -> bool:
    """Return True when Tab can stop at ``widget`` while it is shown and enabled."""
    return bool(widget.focusPolicy().value & Qt.FocusPolicy.TabFocus.value) and widget.focusProxy() is None


def _laid_out(layout: QLayout) -> Iterator[QWidget]:
    if isinstance(layout, QFormLayout):  # itemAt() follows insertion, not rows, once a row is inserted
        items = [layout.itemAt(row, role) for row in range(layout.rowCount()) for role in FORM_ROLES]
    else:
        items = [layout.itemAt(index) for index in range(layout.count())]
    for item in items:
        if item is None:
            continue
        if (widget := item.widget()) is not None:
            yield widget
        elif (inner := item.layout()) is not None:
            yield from _laid_out(inner)


def reading_order(root: QWidget) -> list[QWidget]:
    """Return the widgets under ``root`` that Tab stops at, in the order its layouts place them."""
    stops: list[QWidget] = []
    layout = root.layout()
    laid_out = list(_laid_out(layout)) if layout is not None else []
    children = root.findChildren(QWidget, options=Qt.FindChildOption.FindDirectChildrenOnly)
    for child in laid_out + [child for child in children if child not in laid_out]:
        if child.isWindow():
            continue
        if takes_tab(child):
            stops.append(child)
        stops.extend(reading_order(child))
    return stops


def chain(stops: Sequence[QWidget]) -> None:
    """Make Tab visit ``stops`` one after the other."""
    for first, second in pairwise(stops):
        QWidget.setTabOrder(first, second)


def stop_before(widget: QWidget) -> QWidget:
    """Return the nearest widget before ``widget`` in the focus chain that Tab can stop at."""
    previous = widget.previousInFocusChain()
    while previous is not None and previous is not widget and not takes_tab(previous):
        previous = previous.previousInFocusChain()
    return widget if previous is None else previous
