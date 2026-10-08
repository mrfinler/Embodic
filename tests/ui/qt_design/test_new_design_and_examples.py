"""New design dialog, required-field bar, applicability matrix and the examples gallery (UI-24, UI-28, UI-22, UI-16)."""

import itertools

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QGroupBox, QLabel, QLineEdit
from tests.ui.qt_design.conftest import enter, find, input_name

from embodic.errors import Severity
from embodic.io.examples import list_examples
from embodic.io.examples import load_example as load_packaged
from embodic.model.draft import draft_from_design
from embodic.model.fields import FieldGroup, field_for, field_specs
from embodic.model.schema import ValueType
from embodic.model.vocabulary import TopologyKind
from embodic.ui.viewmodels.session import (
    SessionComputed,
    SessionDrafting,
    display_text,
    stackup_from_values,
    widget_for_pointer,
)

D08 = "spiral_12c10p_d08"


def all_visible_inputs(window):
    """Return the objectNames of the field inputs the inspector shows on all tabs."""
    return set().union(*(panel.visible_inputs() for panel in window.panels.values()))


def create_through_dialog(qtbot, window, name, topology):
    """Open File > New from the empty state, name the design, pick a topology and create it."""
    qtbot.mouseClick(window.empty_new, Qt.MouseButton.LeftButton)
    dialog = window.findChild(QDialog, "dlg-new-design")
    assert dialog is not None and dialog.isVisible()
    create = find(dialog, "btn-create-design")
    assert not create.isEnabled()
    qtbot.keyClicks(find(dialog, "param-design-name"), name)
    assert not create.isEnabled()
    qtbot.mouseClick(find(dialog, f"param-topology-{topology.value}"), Qt.MouseButton.LeftButton)
    assert create.isEnabled()
    qtbot.mouseClick(create, Qt.MouseButton.LeftButton)
    assert not dialog.isVisible()


@pytest.mark.req("REQ-F-36", "REQ-F-21")
def test_ui24_blank_design_computes_once_when_the_last_required_field_is_filled(make_shell, qtbot, wait_computed):
    """Catches a compute on a blank draft, a Compute button usable while fields are missing, or a second compute."""
    shell = make_shell()
    window = shell.window
    create_through_dialog(qtbot, window, "Stator A", TopologyKind.SPIRAL)
    state = window.session.state.value
    assert isinstance(state, SessionDrafting)
    assert window.windowTitle() == "Stator A - embodic"
    compute = window.toolstrip.actions_by_id["act-compute"]
    assert (compute.isEnabled(), compute.toolTip()) == (False, "Compute (F5). 36 required fields left.")
    assert find(window, "new-required-count").text() == "36 required fields left"
    for widget_id in ("param-r-inner", "param-coil-count", "param-air-gap", "param-magnet-br", "param-min-trace"):
        assert find(window, widget_id).text() == "", widget_id
    values = draft_from_design(load_packaged(D08)[1]).values
    for _ in range(60):
        state = window.session.state.value
        if not isinstance(state, SessionDrafting):
            break
        assert shell.calls == []
        pointer = state.missing[0]
        qtbot.mouseClick(find(window, "btn-first-missing"), Qt.MouseButton.LeftButton)
        focused = window.focusWidget()
        name = input_name(focused)
        assert name == widget_for_pointer(pointer, window.session.document.draft), pointer
        if pointer.startswith(("/stackup", "/winding/layers/")):
            inputs = stackup_from_values(values)
            enter(qtbot, window, name, inputs.copper_count)
            enter(qtbot, window, "param-copper-weight", f"{inputs.copper_oz:g}")
            enter(qtbot, window, "param-board-thickness", f"{inputs.board_thickness_mm:g}")
        elif name == "param-bore":
            enter(qtbot, window, "param-bore", values["/outline/bore/shape"])
        else:
            value = values[pointer]
            typed = display_text(field_for(pointer, values), value) if isinstance(focused, QLineEdit) else value
            enter(qtbot, window, name, typed)
    assert isinstance(window.session.state.value, SessionComputed)
    wait_computed(window)
    qtbot.wait(100)
    assert len(shell.calls) == 1
    assert compute.isEnabled()
    assert not find(window, "new-required-count").isVisibleTo(window)


_SCALARS = {ValueType.INT, ValueType.FLOAT, ValueType.BOOL, ValueType.TEXT, ValueType.CHOICE}
_NOT_IN_INSPECTOR = {FieldGroup.DESIGN, FieldGroup.MATERIALS, FieldGroup.ANALYSIS}
_BORE_IDS = {
    "radius_mm": "param-bore-radius",
    "sides": "param-bore-sides",
    "across_flats_mm": "param-bore-across-flats",
    "corner_radius_mm": "param-bore-corner-radius",
    "rotation_rad": "param-bore-rotation",
}
_TAGS = {"/outline/board": "outline", "/rotor/magnet": "magnet", "/outline/bore": "bore"}


def expected_inputs(topology, outline, magnet, bore, fillet_max):
    """Return field_specs(topology) filtered by applicability: oracle from from the field table and screens.md."""
    chosen = {"outline": outline, "magnet": magnet, "bore": bore}
    expected = set()
    for spec in field_specs(topology):
        if spec.widget_id is None or spec.group in _NOT_IN_INSPECTOR or "*" in spec.pointer:
            continue
        if spec.value_type not in _SCALARS or spec.pointer == "/outline/bore/shape":
            continue
        parent, leaf = spec.pointer.rsplit("/", 1)
        if spec.variant is not None and chosen[_TAGS[parent]] != spec.variant:
            continue
        expected.add(_BORE_IDS[leaf] if parent == "/outline/bore" else spec.widget_id)
    if topology is TopologyKind.SPIRAL:
        expected.discard("param-phase-count")  # spiral coils are 3-phase (screens.md section 3)
    if topology is TopologyKind.SERPENTINE and fillet_max:
        expected.discard("param-corner-radius")  # screens.md section 2 state rules
    return expected


@pytest.mark.req("REQ-F-32")
def test_ui28_visible_inputs_equal_field_specs_filtered_by_applicability(make_shell):
    """Catches an input shown for a topology or union member it does not apply to (Xcoil defect C1), or one missing."""
    window = make_shell().window
    session = window.session
    combinations = itertools.product(
        TopologyKind, ("circle", "polygon"), ("arc", "block"), ("none", "circle", "polygon"), (False, True)
    )
    checked = 0
    for topology, outline, magnet, bore, fillet_max in combinations:
        if fillet_max and topology is not TopologyKind.SERPENTINE:
            continue
        session.new_design(topology)
        session.edit("/outline/board/shape", outline)
        session.edit("/rotor/magnet/kind", magnet)
        session.edit("/outline/bore", None if bore == "none" else {"shape": bore})
        if fillet_max:
            session.edit("/winding/fillet_max", True)
        assert all_visible_inputs(window) == expected_inputs(topology, outline, magnet, bore, fillet_max), (
            topology,
            outline,
            magnet,
            bore,
            fillet_max,
        )
        checked += 1
    assert checked == 48


@pytest.mark.req("REQ-F-32")
def test_ui28_an_option_blocked_by_a_sibling_is_disabled_with_the_reason(make_shell):
    """Catches a corner radius that stays editable with straight ends, or one disabled without saying why."""
    window = make_shell().window
    window.session.new_design(TopologyKind.SPIRAL)
    corner = find(window, "param-corner-radius")
    assert corner.isEnabled()
    window.session.edit("/winding/coil/end_style", "straight")
    assert corner.isVisibleTo(window.panels["tab-coil"]) and not corner.isEnabled()
    assert find(window, "param-corner-radius-hint").text() == "Not used with straight ends."


@pytest.mark.req("REQ-F-32")
def test_the_coil_tab_shows_poles_under_no_rotor_heading(make_shell):
    """Catches DEF-3: the rotor group of Poles put a "Rotor and magnets" heading on the untitled Coil tab."""
    window = make_shell().window
    window.session.load_example(D08)
    coil = window.panels["tab-coil"]
    assert "param-poles" in coil.visible_inputs()
    assert [box.title() for box in coil.findChildren(QGroupBox) if box.title()] == []


def visible_chips(window):
    """Return {objectName: chip text} of every shown field row."""
    chips = {}
    for panel in window.panels.values():
        for widget_id, editor in panel.editors.items():
            if editor.isVisibleTo(panel):
                chip = editor.findChild(QLabel, f"{widget_id}-prov")
                chips[widget_id] = chip.text() if chip.isVisibleTo(editor) else None
    return chips


def badges(window):
    """Return the trust badge text of each summary card."""
    return {key: card.badge.text() for key, card in window.cards.items()}


@pytest.mark.req("REQ-F-21", "REQ-F-38")
def test_ui22_example_load_marks_every_field_example_and_set_back_restores_it(make_shell, qtbot, wait_computed):
    """Catches a field without the Example chip, a chip still user after setting the value back, or badges moving."""
    window = make_shell().window
    window.toolstrip.actions_by_id["act-examples"].trigger()
    gallery = window.findChild(QDialog, "dlg-examples")
    assert gallery is not None and gallery.isVisible()
    assert gallery.example_ids() == [info.example_id for info in list_examples()]
    assert all("Example" in info.title for info in list_examples())
    gallery.list.setCurrentRow(gallery.example_ids().index(D08))
    qtbot.mouseClick(find(gallery, "btn-load-example"), Qt.MouseButton.LeftButton)
    wait_computed(window)
    chips = visible_chips(window)
    assert len(chips) >= 40
    assert set(chips.values()) == {"example"}, {k: v for k, v in chips.items() if v != "example"}
    before = badges(window)
    enter(qtbot, window, "param-via-drill", "0.35")
    assert visible_chips(window)["param-via-drill"] == "user"
    wait_computed(window)
    enter(qtbot, window, "param-via-drill", "0.3")
    assert visible_chips(window)["param-via-drill"] == "example"
    wait_computed(window)
    assert badges(window) == before
    assert window.windowTitle().endswith("(from example Example: UGent D08 12-coil 10-pole spiral) - embodic")


@pytest.mark.req("REQ-F-25")
def test_ui16_every_packaged_example_loads_from_the_gallery_and_computes(make_shell, qtbot, wait_computed):
    """Catches an example that does not load through the UI, or one that computes no board or an ERROR issue."""
    window = make_shell().window
    for row, info in enumerate(list_examples()):
        gallery = window.examples_gallery()
        gallery.show()
        gallery.list.setCurrentRow(row)
        qtbot.mouseClick(find(gallery, "btn-load-example"), Qt.MouseButton.LeftButton)
        wait_computed(window)
        outcome = window.session.state.value.outcome
        assert outcome.boards is not None, info.example_id
        assert not [i.code for i in outcome.issues if i.severity is Severity.ERROR], info.example_id
        assert window.session.document.draft.topology is info.topology
