"""The toolstrip action table (interfaces.md section 11). Qt-free; the view builds one button per entry."""

from dataclasses import dataclass
from enum import StrEnum


class ToolstripTab(StrEnum):
    """Toolstrip tabs, in display order."""

    HOME = "home"
    DESIGN = "design"
    ANALYSIS = "analysis"
    EXPORT = "export"
    VIEW = "view"


@dataclass(frozen=True, slots=True, kw_only=True)
class ToolstripAction:
    """One toolstrip button."""

    id: str  # also the Qt objectName and the string-catalogue key prefix
    tab: ToolstripTab
    icon: str  # file stem in resources/icons, monochrome SVG drawn with currentColor
    shortcut: str | None
    command: str  # name of a view-model command, resolved at startup (unknown name = startup error)
    group: str  # toolstrip group label key


TOOLSTRIP: tuple[ToolstripAction, ...] = (
    ToolstripAction(
        id="act-new", tab=ToolstripTab.HOME, icon="new", shortcut="Ctrl+N", command="new_design", group="file"
    ),
    ToolstripAction(
        id="act-open", tab=ToolstripTab.HOME, icon="open", shortcut="Ctrl+O", command="open_project", group="file"
    ),
    ToolstripAction(
        id="act-save", tab=ToolstripTab.HOME, icon="save", shortcut="Ctrl+S", command="save_project", group="file"
    ),
    ToolstripAction(
        id="act-examples", tab=ToolstripTab.HOME, icon="examples", shortcut=None, command="show_examples", group="file"
    ),
    ToolstripAction(id="act-undo", tab=ToolstripTab.HOME, icon="undo", shortcut="Ctrl+Z", command="undo", group="edit"),
    ToolstripAction(id="act-redo", tab=ToolstripTab.HOME, icon="redo", shortcut="Ctrl+Y", command="redo", group="edit"),
    ToolstripAction(
        id="act-topo-spiral",
        tab=ToolstripTab.DESIGN,
        icon="topology-spiral",
        shortcut=None,
        command="set_topology_spiral",
        group="topology",
    ),
    ToolstripAction(
        id="act-topo-serpentine",
        tab=ToolstripTab.DESIGN,
        icon="topology-serpentine",
        shortcut=None,
        command="set_topology_serpentine",
        group="topology",
    ),
    ToolstripAction(
        id="act-topo-wave",
        tab=ToolstripTab.DESIGN,
        icon="topology-wave",
        shortcut=None,
        command="set_topology_wave",
        group="topology",
    ),
    ToolstripAction(
        id="act-conn-star",
        tab=ToolstripTab.DESIGN,
        icon="connection-star",
        shortcut=None,
        command="set_connection_star",
        group="connection",
    ),
    ToolstripAction(
        id="act-conn-delta",
        tab=ToolstripTab.DESIGN,
        icon="connection-delta",
        shortcut=None,
        command="set_connection_delta",
        group="connection",
    ),
    ToolstripAction(
        id="act-compute", tab=ToolstripTab.ANALYSIS, icon="compute", shortcut="F5", command="compute_now", group="run"
    ),
    ToolstripAction(
        id="act-drc", tab=ToolstripTab.ANALYSIS, icon="drc", shortcut=None, command="show_checks", group="run"
    ),
    ToolstripAction(
        id="act-equations",
        tab=ToolstripTab.ANALYSIS,
        icon="equations",
        shortcut=None,
        command="show_equations",
        group="reference",
    ),
    ToolstripAction(
        id="act-export-svg",
        tab=ToolstripTab.EXPORT,
        icon="export-svg",
        shortcut=None,
        command="export_svg",
        group="drawings",
    ),
    ToolstripAction(
        id="act-export-dxf",
        tab=ToolstripTab.EXPORT,
        icon="export-dxf",
        shortcut=None,
        command="export_dxf",
        group="drawings",
    ),
    ToolstripAction(
        id="act-export-pdf",
        tab=ToolstripTab.EXPORT,
        icon="export-pdf",
        shortcut=None,
        command="export_pdf",
        group="report",
    ),
    ToolstripAction(
        id="act-export-all",
        tab=ToolstripTab.EXPORT,
        icon="export-all",
        shortcut="Ctrl+E",
        command="export_bundle",
        group="report",
    ),
    ToolstripAction(
        id="act-theme", tab=ToolstripTab.VIEW, icon="theme", shortcut=None, command="cycle_theme", group="appearance"
    ),
    ToolstripAction(
        id="act-greyscale",
        tab=ToolstripTab.VIEW,
        icon="greyscale",
        shortcut=None,
        command="toggle_phase_render_mode",
        group="appearance",
    ),
    ToolstripAction(
        id="act-fit", tab=ToolstripTab.VIEW, icon="zoom-fit", shortcut="F", command="fit_view", group="view"
    ),
)
