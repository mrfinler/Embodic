"""PK-08: runtime licences match package_layout.md section 5, and THIRD_PARTY_LICENSES.md is complete."""

import hashlib
import re
import subprocess
import sys

import pytest
from tests.packaging.support import REPO, installed_distributions_code, wheel_members

import embodic

TPL = REPO / "THIRD_PARTY_LICENSES.md"
# package_layout.md section 5, column "Licence (PyPI)", for the runtime closure.
ALLOWED = {
    "numpy": "BSD-3-Clause AND 0BSD AND MIT AND Zlib AND CC0-1.0",
    "pyside6-essentials": "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only",
    "shiboken6": "LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only",
}
# SHA-256 that Agent 5 recorded for the Qt v6.11.2 texts (dependency_licences.md, "Text sources").
QT_TEXTS = {
    "GNU Lesser General Public License, version 3": "da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768",
    "GNU General Public License, version 3": "8ceb4b9ee5adedde47b31e975c1d90c73ad27b6b165a1dcd80c7c545eb65b903",
}
COMPONENTS = ("NumPy", "PySide6-Essentials", "shiboken6", "Qt", "Inter", "JetBrains Mono")


def text_block(document: str, heading: str) -> bytes:
    """Return the fenced text under a level-3 heading, with the newline that ends the original file."""
    match = re.search(rf"^### {re.escape(heading)}\n.*?^```text\n(.*?)\n```$", document, re.MULTILINE | re.DOTALL)
    assert match is not None, heading
    return (match.group(1) + "\n").encode("utf-8")


@pytest.mark.req("REQ-N-19")
def test_pk08_the_runtime_closure_carries_only_allowed_licences(clean_venv):
    """Catches a new runtime package, or a pinned version whose licence changed from the recorded one."""
    licences = clean_venv.evaluate(
        installed_distributions_code("d.metadata.get('License-Expression') or d.metadata.get('License')")
    )
    licences.pop("embodic")
    assert licences == ALLOWED


@pytest.mark.req("REQ-N-19")
def test_pk08_third_party_licences_has_every_component_and_the_full_texts():
    """Catches a missing component section, an edited font licence, or a Qt licence text that is not Qt's own."""
    document = TPL.read_text(encoding="utf-8")
    headings = re.findall(r"^### (.+)$", document, re.MULTILINE)
    assert set(COMPONENTS) <= set(headings)
    assert (
        text_block(document, "Inter: SIL Open Font License 1.1")
        == (REPO / "resources/fonts/Inter/LICENSE.txt").read_bytes()
    )
    jetbrains = (REPO / "resources/fonts/JetBrainsMono/OFL.txt").read_bytes()
    assert text_block(document, "JetBrains Mono: SIL Open Font License 1.1") == jetbrains
    for heading, sha256 in QT_TEXTS.items():
        assert hashlib.sha256(text_block(document, heading)).hexdigest() == sha256
    assert "Licence: not yet chosen; all rights reserved until the project owner chooses one." in document
    assert not (REPO / "LICENSE").exists()


@pytest.mark.req("REQ-N-19")
def test_pk08_the_wheel_carries_the_licence_file_under_dist_info(built_wheel):
    """Catches a wheel whose metadata misses THIRD_PARTY_LICENSES.md or the pending-licence statement."""
    members = wheel_members(built_wheel)
    dist_info = f"embodic-{embodic.__version__}.dist-info"
    assert members[f"{dist_info}/licenses/THIRD_PARTY_LICENSES.md"] == TPL.read_bytes()
    metadata = members[f"{dist_info}/METADATA"].decode("utf-8")
    assert "License: Licence: not yet chosen; all rights reserved until the project owner chooses one" in metadata
    assert "License-File: THIRD_PARTY_LICENSES.md" in metadata


@pytest.mark.req("REQ-N-19")
def test_pk08_every_declared_requirement_has_a_licence_row():
    """Catches a dependency added to pyproject.toml without Agent 5's licence row (check_dependency_licences.py)."""
    script = REPO / "docs" / "phase2" / "evidence" / "tools" / "check_dependency_licences.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--coverage"], capture_output=True, encoding="utf-8", check=False
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
