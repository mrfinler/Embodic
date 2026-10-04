"""MT-07: scope guard for D-009. No KiCad import, writer, option or text anywhere in the shipped package."""

import ast
from pathlib import Path

import pytest

BANNED_MODULES = ("kipy", "pcbnew")
WITHDRAWN_KICAD_REQS = tuple(f"REQ-K-{n:02d}" for n in range(1, 17))


def check_kicad_imports(modules) -> list[str]:
    """Return one 'path:line: message' per import of a KiCad module."""
    violations = []
    for module in modules:
        for node in ast.walk(module.tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            else:
                continue
            violations += [
                f"{module.where(node)}: imports {name}; KiCad is out of scope (D-009)"
                for name in names
                if name.split(".")[0] in BANNED_MODULES
            ]
    return violations


def check_kicad_text(roots: list[Path]) -> list[str]:
    """Return one message per file whose name or text mentions KiCad (case-insensitive)."""
    violations = []
    for root in roots:
        for path in sorted(p for p in root.rglob("*") if p.is_file()):
            if "kicad" in path.name.lower():
                violations.append(f"{path}: file name mentions KiCad (D-009)")
                continue
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for number, line in enumerate(text.splitlines(), start=1):
                if "kicad" in line.lower():
                    violations.append(f"{path}:{number}: mentions KiCad; remove it (D-009)")
    return violations


@pytest.mark.req(*WITHDRAWN_KICAD_REQS)
def test_mt07_no_kicad_imports(src_modules):
    """MT-07 import part on the real package."""
    assert check_kicad_imports(src_modules) == []


@pytest.mark.req(*WITHDRAWN_KICAD_REQS)
def test_mt07_no_kicad_text_in_shipped_files(shipped_roots):
    """MT-07 text part over src/embodic and resources (string catalogue, CLI choices, writers, file names)."""
    assert check_kicad_text(shipped_roots) == []


@pytest.mark.req(*WITHDRAWN_KICAD_REQS)
def test_mt07_flags_planted_kicad(planted, tmp_path):
    """Catches a guard that passes everything: an import, a CLI choice string and a file name are all reported."""
    module = planted("embodic.cli.commands", "import pcbnew\nfrom kipy.board import Board\n")
    assert len(check_kicad_imports([module])) == 2
    (tmp_path / "commands.py").write_text('FORMATS = ("svg", "dxf", "KiCad PCB")\n', encoding="utf-8")
    (tmp_path / "kicad_pcb_writer.py").write_text("", encoding="utf-8")
    (tmp_path / "icon.png").write_bytes(b"\x89PNG\r\n\x1a\n\xff\xfe")
    violations = check_kicad_text([tmp_path])
    assert len(violations) == 2
    assert any("commands.py:1" in v for v in violations)
    assert any("kicad_pcb_writer.py" in v for v in violations)
