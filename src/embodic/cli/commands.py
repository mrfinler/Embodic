"""The commands of `embodic-cli` (interfaces.md section 12): compute, validate and export a project file.

This module is the boundary of the program. It parses the command line, maps every outcome to an exit code and prints
English text. The work is done by `embodic.api` and `embodic.io`; nothing here imports Qt.
"""

import argparse
import json
import sys
import traceback
from collections.abc import Sequence
from enum import IntEnum
from pathlib import Path
from typing import NoReturn

from embodic.api import ComputeOptions, ComputeOutcome, compute, compute_project, outcome_to_json
from embodic.errors import IssueCategory, Severity, ValidationIssue, message_for
from embodic.io.project import ProjectFile, load_project, project_provenance
from embodic.model.validate import validate_design
from embodic.outcome import Stage

__all__ = ["ExitCode", "main"]


class ExitCode(IntEnum):
    """What the process returns to the shell (REQ-F-18)."""

    OK = 0
    VALIDATION_ERRORS = 1  # also: incomplete draft, unreadable file, unusable command line
    DRC_ERRORS = 2
    INTERNAL_ERROR = 3


def exit_code_of_issues(issues: Sequence[ValidationIssue]) -> ExitCode:
    """Return the code of a list of issues: an internal error beats a validation error, a warning is not an error."""
    if any(i.category is IssueCategory.INTERNAL for i in issues):
        return ExitCode.INTERNAL_ERROR
    if any(i.severity is Severity.ERROR for i in issues):
        return ExitCode.VALIDATION_ERRORS
    return ExitCode.OK


def exit_code_of_outcome(outcome: ComputeOutcome) -> ExitCode:
    """Return the code of a computed outcome; a DRC that was not asked for (`--no-drc`) is not a DRC error."""
    code = exit_code_of_issues(outcome.issues)
    if code is not ExitCode.OK:
        return code
    if outcome.drc is not None and not all(report.passed for report in outcome.drc):
        return ExitCode.DRC_ERRORS
    return ExitCode.OK


def format_issue(issue: ValidationIssue) -> str:
    """Return an issue as text: severity, code and message, then its pointers, value and hint on indented lines."""
    lines = [f"{issue.severity.value} {issue.code}: {issue.message}"]
    lines += [f"  at {pointer}" for pointer in issue.pointers]
    if issue.value is not None:
        lines.append(f"  value: {issue.value}")
    if issue.hint:
        lines.append(f"  hint: {issue.hint}")
    return "\n".join(lines)


def format_summary(outcome: ComputeOutcome, *, timings: bool) -> list[str]:
    """Return the lines of a computed outcome: design, hash, topology, DRC result and, on request, the stage seconds."""
    boards = len(outcome.boards.boards) if outcome.boards is not None else 0
    if outcome.drc is None:
        drc = "not run"
    elif all(report.passed for report in outcome.drc):
        drc = "passed"
    else:
        drc = f"FAILED, {sum(report.violation_count for report in outcome.drc)} violations"
    lines = [
        f"Design: {outcome.design.name}",
        f"Design hash: {outcome.design_hash}",
        f"Topology: {outcome.design.topology.value}, boards: {boards}",
        f"Design rule check: {drc}",
    ]
    if timings:
        stages = ", ".join(
            f"{stage.value} {outcome.timings_s[stage.value]:.3f}" for stage in Stage if stage.value in outcome.timings_s
        )
        lines.append(f"Timings (s): {stages}")
    return lines


def _print_issues(issues: Sequence[ValidationIssue]) -> None:
    for issue in issues:
        print(format_issue(issue), file=sys.stderr)


def _issue(
    code: str, category: IssueCategory, value: str | int | None = None, *, severity: Severity = Severity.ERROR
) -> ValidationIssue:
    return ValidationIssue(
        code=code, category=category, severity=severity, message=message_for(code), pointers=(), value=value
    )


def _unwritable(path: Path) -> ValidationIssue | None:
    """Return the issue for an output path whose folder is missing or which is a folder itself."""
    if path.is_dir() or not path.parent.is_dir():
        return _issue("INVALID_CLI_OUTPUT_UNWRITABLE", IssueCategory.INVALID, str(path))
    return None


def _load(path: Path) -> ProjectFile | tuple[ValidationIssue, ...]:
    """Load a project whose design is complete, or return the issues that say why there is none."""
    project, issues = load_project(path)
    if isinstance(project, ProjectFile):
        return project
    if project is None:
        return issues
    # compute_project builds the issue of an incomplete draft and computes nothing for it.
    incomplete = compute_project(path)
    assert isinstance(incomplete, tuple), "a draft has no outcome"
    return incomplete


def _refuse(issues: Sequence[ValidationIssue]) -> ExitCode:
    """Print why there is nothing to work on; no design or no output file is never a success."""
    _print_issues(issues)
    return max(ExitCode.VALIDATION_ERRORS, exit_code_of_issues(issues))


def _compute(args: argparse.Namespace) -> ExitCode:
    if args.json is not None and (bad := _unwritable(args.json)) is not None:
        return _refuse((bad,))
    loaded = _load(args.project)
    if isinstance(loaded, tuple):
        return _refuse(loaded)
    outcome = compute(loaded.design, project_provenance(loaded), options=ComputeOptions(run_drc=not args.no_drc))
    assert outcome is not None, "compute without a cancel token never returns None"
    if args.json is not None:
        args.json.write_text(
            json.dumps(outcome_to_json(outcome), indent=2, sort_keys=True, ensure_ascii=False, allow_nan=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    print("\n".join(format_summary(outcome, timings=args.timings)))
    _print_issues(outcome.issues)
    return exit_code_of_outcome(outcome)


def _validate(args: argparse.Namespace) -> ExitCode:
    loaded = _load(args.project)
    if isinstance(loaded, tuple):
        return _refuse(loaded)
    issues = validate_design(loaded.design)
    _print_issues(issues)
    code = exit_code_of_issues(issues)
    if code is ExitCode.OK:
        print(f"Valid: {loaded.design.name}")
    return code


class _Parser(argparse.ArgumentParser):
    """argparse exits with 2 on a usage error, which is the DRC code here; a usage error is a validation error."""

    def error(self, message: str) -> NoReturn:
        self.print_usage(sys.stderr)
        print(format_issue(_issue("INVALID_CLI_USAGE", IssueCategory.INVALID, message)), file=sys.stderr)
        raise SystemExit(ExitCode.VALIDATION_ERRORS)


def _parser() -> argparse.ArgumentParser:
    parser = _Parser(prog="embodic-cli", description="Compute, validate and export embodic project files.")
    commands = parser.add_subparsers(dest="command", required=True, metavar="{compute,validate,export}")
    compute_parser = commands.add_parser("compute", help="run every stage and report the exit code")
    compute_parser.add_argument("project", type=Path, help="project file (.embodic.json)")
    compute_parser.add_argument("--json", type=Path, metavar="OUT", help="write the whole outcome as JSON to OUT")
    compute_parser.add_argument("--no-drc", action="store_true", help="skip the design rule check")
    compute_parser.add_argument("--timings", action="store_true", help="print the seconds each stage took")
    compute_parser.set_defaults(handler=_compute)
    validate_parser = commands.add_parser("validate", help="check the design against its rules and build nothing")
    validate_parser.add_argument("project", type=Path, help="project file (.embodic.json)")
    validate_parser.set_defaults(handler=_validate)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command line and return the exit code.

    embodic-cli compute <project.embodic.json> [--json OUT] [--no-drc] [--timings]
    embodic-cli validate <project.embodic.json>
    embodic-cli export <project.embodic.json> --format {svg,dxf,dxf-outline,dxf-screws,pdf,readme,bundle} -o PATH
                [--allow-drc-errors]
    The desktop app entry point is `embodic` (embodic.ui.app:main).
    """
    try:
        args = _parser().parse_args(argv)
    except SystemExit as stop:
        return stop.code if isinstance(stop.code, int) else int(ExitCode.OK)
    try:
        return int(args.handler(args))
    except Exception:
        _print_issues((_issue("INTERNAL_CLI_FAILED", IssueCategory.INTERNAL, traceback.format_exc()),))
        return int(ExitCode.INTERNAL_ERROR)
