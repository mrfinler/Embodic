"""MT-08: no package under tests/ or src/ takes a top-level module name that is already taken.

pytest names a test package after its outermost folder with an `__init__.py` and registers it in sys.modules under
that name. In importlib mode it even replaces a cached module that is not a package: tests/unit/io replaced the stdlib
io, and numpy.testing then failed on `from io import StringIO`. Only top-level names can collide; embodic.io is safe.
"""

import importlib.metadata
import sys
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
SCANNED_ROOTS = (REPO / "tests", REPO / "src")


def top_level_packages(roots: Iterable[Path]) -> list[Path]:
    """Return every package folder whose parent is not a package: the folders that become top-level module names."""
    inits = sorted(init for root in roots for init in root.rglob("__init__.py"))
    return [init.parent for init in inits if not (init.parent.parent / "__init__.py").is_file()]


def taken_names() -> frozenset[str]:
    """Top-level module names of the standard library and of every installed distribution except embodic itself."""
    installed = {name for name, dists in importlib.metadata.packages_distributions().items() if "embodic" not in dists}
    return frozenset(sys.stdlib_module_names) | installed


def check_shadowing(roots: Iterable[Path], taken: frozenset[str]) -> list[str]:
    """Return one message per top-level package whose name is taken, or is claimed by another package in `roots`."""
    by_name: defaultdict[str, list[Path]] = defaultdict(list)
    for package in top_level_packages(roots):
        by_name[package.name].append(package)
    violations = []
    for name, packages in sorted(by_name.items()):
        if name in taken:
            violations += [f"{p}: package {name!r} shadows the stdlib or installed module {name!r}" for p in packages]
        if len(packages) > 1:
            violations.append(f"package name {name!r} is claimed by {', '.join(map(str, packages))}")
    return violations


@pytest.mark.req("REQ-N-08")
def test_mt08_no_package_shadows_a_taken_name():
    """MT-08 on the real tests/ and src/ trees."""
    assert check_shadowing(SCANNED_ROOTS, taken_names()) == []


@pytest.mark.req("REQ-N-08")
def test_mt08_flags_planted_shadowing(tmp_path):
    """Catches a lint that passes everything, or one that also flags subpackages such as embodic.io."""
    for package in ("tests/unit/json", "tests/unit/embodic", "src/embodic", "src/embodic/io", "tests/unit/embodic_io"):
        (tmp_path / package).mkdir(parents=True)
        (tmp_path / package / "__init__.py").touch()
    violations = check_shadowing([tmp_path / "tests", tmp_path / "src"], taken_names())
    assert len(violations) == 2
    assert violations[1].startswith(f"{tmp_path / 'tests' / 'unit' / 'json'}: package 'json' shadows")
    assert violations[0].startswith("package name 'embodic' is claimed by")
