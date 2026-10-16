r"""DEF-W-09: every text-mode file write in src/embodic names newline="\n" (REQ-N-04 same-platform byte identity).

With ``newline=None`` Python writes ``os.linesep``, which is "\r\n" on Windows
(https://docs.python.org/3/library/functions.html#open), so the same input gives other bytes on Windows than on Linux.
"""

import ast

import pytest

TEMP_FILES = ("NamedTemporaryFile", "TemporaryFile", "SpooledTemporaryFile")


def _keyword(call: ast.Call, name: str) -> ast.expr | None:
    return next((k.value for k in call.keywords if k.arg == name), None)


def _open_mode(call: ast.Call) -> tuple[bool, ast.expr | None]:
    """Return (is an open-like call, its mode argument or None for the default mode)."""
    func, args = call.func, call.args
    if isinstance(func, ast.Name) and func.id == "open":
        return True, _keyword(call, "mode") or (args[1] if len(args) > 1 else None)
    if not isinstance(func, ast.Attribute):
        return False, None
    if func.attr == "fdopen" or (func.attr == "open" and isinstance(func.value, ast.Name) and func.value.id == "io"):
        return True, _keyword(call, "mode") or (args[1] if len(args) > 1 else None)
    if func.attr == "open" or func.attr in TEMP_FILES:
        return True, _keyword(call, "mode") or (args[0] if args else None)
    return False, None


def _writes_text(call: ast.Call) -> bool | None:
    """Return True for a text-mode write, False otherwise, None when the mode is not a literal."""
    if isinstance(call.func, ast.Attribute) and call.func.attr == "write_text":
        return True
    is_open, mode = _open_mode(call)
    if not is_open or mode is None:
        return False
    if not (isinstance(mode, ast.Constant) and isinstance(mode.value, str)):
        return None
    return "b" not in mode.value and any(flag in mode.value for flag in "wax+")


def check_text_newlines(modules) -> list[str]:
    r"""Return one 'path:line: message' per text-mode write that does not pin newline="\n"."""
    violations = []
    for module in modules:
        for node in ast.walk(module.tree):
            if not isinstance(node, ast.Call):
                continue
            writes_text = _writes_text(node)
            newline = _keyword(node, "newline")
            if writes_text is None:
                violations.append(f"{module.where(node)}: file mode is not a literal; the newline cannot be checked")
            elif writes_text and not (isinstance(newline, ast.Constant) and newline.value == "\n"):
                violations.append(f'{module.where(node)}: text-mode write without newline="\\n" (DEF-W-09)')
    return violations


@pytest.mark.req("REQ-N-04")
def test_every_text_write_in_src_pins_lf(src_modules):
    """Catches a writer whose file holds CRLF on Windows and LF on Linux for the same input (DEF-W-09)."""
    assert check_text_newlines(src_modules) == []


@pytest.mark.req("REQ-N-04")
def test_flags_each_planted_text_write_without_lf(planted):
    """Catches a lint that misses write_text, open, io.open, os.fdopen, Path.open or a temporary file in text mode."""
    module = planted(
        "embodic.io.leak",
        "\n".join(
            (
                'Path("a").write_text("x", encoding="utf-8")',
                'Path("a").write_text("x", encoding="utf-8", newline="\\n")',
                'open("a", "w", encoding="utf-8")',
                'open("a", "wb")',
                'open("a", encoding="utf-8")',
                'os.fdopen(3, "w", encoding="utf-8")',
                'io.open("a", mode="a", encoding="utf-8")',
                'Path("a").open("x", encoding="utf-8")',
                'Path("a").open("w", encoding="utf-8", newline="\\n")',
                'tempfile.NamedTemporaryFile("w+")',
                "tempfile.NamedTemporaryFile()",
                "dialog.open()",
                'open("a", mode, encoding="utf-8")',
                'open("a", "w", encoding="utf-8", newline="")',
            )
        ),
    )
    assert [int(line.split(":")[1]) for line in check_text_newlines([module])] == [1, 3, 6, 7, 8, 10, 13, 14]
