"""Parsed source of src/embodic and of the scripts under tools/ for the AST lints (MT-04 to MT-07, LG-01, LG-08)."""

import ast
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SRC_PACKAGE = REPO / "src" / "embodic"
TOOLS = REPO / "tools"
RESOURCES = REPO / "resources"


@dataclass(frozen=True)
class SourceModule:
    """One Python module: dotted name, file path, source text and syntax tree."""

    name: str
    path: Path
    text: str
    tree: ast.Module

    def in_package(self, *packages: str) -> bool:
        """Return True when the module is one of `packages` or inside one of them."""
        return any(self.name == package or self.name.startswith(package + ".") for package in packages)

    def where(self, node: ast.AST) -> str:
        """Return 'path:line' for a node, relative to the repository when possible."""
        path = self.path.relative_to(REPO) if self.path.is_relative_to(REPO) else self.path
        return f"{path}:{getattr(node, 'lineno', 0)}"


def parse_module(name: str, text: str, path: Path) -> SourceModule:
    """Parse one module's source text."""
    return SourceModule(name=name, path=path, text=text, tree=ast.parse(text, filename=str(path)))


def load_src_modules() -> list[SourceModule]:
    """Parse every module under src/embodic, sorted by dotted name."""
    modules = []
    for path in sorted(SRC_PACKAGE.rglob("*.py")):
        parts = path.relative_to(SRC_PACKAGE.parent).with_suffix("").parts
        name = ".".join(parts[:-1] if parts[-1] == "__init__" else parts)
        modules.append(parse_module(name, path.read_text(encoding="utf-8"), path))
    return modules


def load_tools_modules() -> list[SourceModule]:
    """Parse every script under tools/, sorted by path; the dotted name is the path below the repository root."""
    return [
        parse_module(".".join(path.relative_to(REPO).with_suffix("").parts), path.read_text(encoding="utf-8"), path)
        for path in sorted(TOOLS.rglob("*.py"))
    ]


@pytest.fixture(scope="session")
def src_modules() -> list[SourceModule]:
    """All modules of the real package."""
    return load_src_modules()


@pytest.fixture(scope="session")
def tools_modules() -> list[SourceModule]:
    """All scripts under tools/."""
    return load_tools_modules()


@pytest.fixture(scope="session")
def shipped_roots() -> list[Path]:
    """Folders whose files end up in the wheel: the package and the resources."""
    return [SRC_PACKAGE, RESOURCES]


@pytest.fixture
def planted() -> Callable[[str, str], SourceModule]:
    """Build a module from source text, for tests that prove a lint catches a violation."""

    def build(name: str, text: str) -> SourceModule:
        return parse_module(name, text, Path("planted") / (name.replace(".", "/") + ".py"))

    return build
