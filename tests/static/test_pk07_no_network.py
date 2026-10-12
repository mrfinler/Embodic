"""PK-07: the shipped package imports no network module (REQ-N-17, package_layout.md section 3)."""

import ast

import pytest

NETWORK_MODULES = ("socket", "http", "urllib.request")


def check_network_imports(modules) -> list[str]:
    """Return one 'path:line: message' per import of socket, http or urllib.request, or of a name inside them."""
    violations = []
    for module in modules:
        for node in ast.walk(module.tree):
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                names = [node.module or ""] + [f"{node.module}.{alias.name}" for alias in node.names]
            else:
                continue
            hits = sorted(
                {banned for name in names for banned in NETWORK_MODULES if f"{name}.".startswith(f"{banned}.")}
            )
            violations += [
                f"{module.where(node)}: imports {banned}; embodic works offline (REQ-N-17)" for banned in hits
            ]
    return violations


@pytest.mark.req("REQ-N-17")
def test_pk07_src_imports_no_network_module(src_modules):
    """Catches a network call path entering the product, which must run without network access."""
    assert check_network_imports(src_modules) == []


@pytest.mark.req("REQ-N-17")
def test_pk07_flags_each_planted_network_import(planted):
    """Catches a lint that misses an aliased, a from-style or a submodule import of a network module."""
    module = planted(
        "embodic.physics.leak",
        "import socket as s\nfrom http import client\nfrom urllib import request\nimport urllib.parse\nimport json\n",
    )
    assert [line.split(": ", 1)[1] for line in check_network_imports([module])] == [
        "imports socket; embodic works offline (REQ-N-17)",
        "imports http; embodic works offline (REQ-N-17)",
        "imports urllib.request; embodic works offline (REQ-N-17)",
    ]
