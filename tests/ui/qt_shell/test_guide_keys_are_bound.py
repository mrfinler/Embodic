"""D-094b: the guide's "Keyboard shortcuts" table lists only keys that the main window binds."""

import re

import pytest
from PySide6.QtGui import QAction, QKeySequence, QShortcut

from embodic.ui.viewmodels.results import KEYS_TOPIC

pytestmark = pytest.mark.req("REQ-N-12")

PORTABLE = QKeySequence.SequenceFormat.PortableText
# Esc closes dialogs through Qt and reverts a field in its own key handler; no shortcut carries it.
HANDLED_BY_THE_WIDGET = frozenset({"Esc"})


def keys_of(cell: str) -> list[str]:
    """Return the keys of one table cell; "Alt+1 ... Alt+4" stands for the four keys between its ends."""
    keys: list[str] = []
    for part in re.split(r", | or ", cell):
        if " ... " not in part:
            keys.append(part)
            continue
        first, last = part.split(" ... ")
        prefix = first[:-1]
        keys.extend(f"{prefix}{digit}" for digit in range(int(first[-1]), int(last[-1]) + 1))
    return keys


def portable(key: str) -> str:
    """Return ``key`` in the spelling Qt gives a bound sequence, so "Ctrl+shift+z" and "Ctrl+Shift+Z" compare equal."""
    return QKeySequence(key).toString(PORTABLE)


def test_every_key_the_guide_lists_for_the_whole_window_is_bound(make_shell):
    """Catches a key in the guide's table that no shortcut of the window carries (D-094b found Ctrl+,).

    The table is the one the guide window shows. A bound key is a `QShortcut` of the window or a shortcut of any of
    its actions, the toolstrip's included. Rows of other scopes belong to one widget, which handles the key itself.
    """
    window = make_shell().window
    rows = window.guide_window().topics[KEYS_TOPIC].rows
    listed = [
        key
        for head, _action in rows
        for scope, cell in [head.split(": ", 1)]
        if scope == "Global"
        for key in keys_of(cell)
        if key not in HANDLED_BY_THE_WIDGET
    ]
    assert {"F1", "Alt+4", "Ctrl+Shift+Z"} <= set(listed), "the table was read: single keys, a range and a pair"
    bound = {shortcut.key().toString(PORTABLE) for shortcut in window.findChildren(QShortcut)}
    for action in window.findChildren(QAction):
        bound.update(sequence.toString(PORTABLE) for sequence in action.shortcuts())
    assert [key for key in listed if portable(key) not in bound] == []
