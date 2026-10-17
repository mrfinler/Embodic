"""PK-03: two wheel builds give the same members and the same .py bytes; the wheel and sdist ship only the product."""

import hashlib
import subprocess
import sys
import tarfile

import pytest
from tests.packaging.support import REPO, build_wheel, wheel_members

import embodic

EVIDENCE_MEMBER = "embodic/_resources/evidence/passed_tests.v1.json"
DIST_INFO = f"embodic-{embodic.__version__}.dist-info"


def py_hashes(members: dict[str, bytes]) -> dict[str, str]:
    """Return the SHA-256 of every .py member."""
    return {name: hashlib.sha256(data).hexdigest() for name, data in members.items() if name.endswith(".py")}


@pytest.mark.req("REQ-N-06")
def test_pk03_two_builds_have_the_same_members_and_python_bytes(built_wheel, tmp_path):
    """Catches a build that depends on time, order or leftovers, so a wheel cannot be rebuilt to the same code."""
    first = wheel_members(built_wheel)
    second = wheel_members(build_wheel(tmp_path))
    assert sorted(first) == sorted(second)
    assert py_hashes(first) == py_hashes(second)
    assert len(py_hashes(first)) > 100


@pytest.mark.req("REQ-N-06", "REQ-N-19")
def test_pk03_the_wheel_holds_the_package_resources_and_licences_and_nothing_else(built_wheel):
    """Catches a wheel without its resources or licence file, or one that ships tests, tools or documents."""
    names = set(wheel_members(built_wheel))
    expected = {
        "embodic/__init__.py",
        "embodic/io/schema/project.v1.schema.json",
        "embodic/io/schema/project.v2.schema.json",
        "embodic/_resources/evidence/equations.v1.json",
        "embodic/_resources/fonts/Inter/LICENSE.txt",
        "embodic/_resources/fonts/JetBrainsMono/OFL.txt",
        "embodic/_resources/fonts/FONTS.md",
        f"{DIST_INFO}/licenses/THIRD_PARTY_LICENSES.md",
    }
    assert expected <= names
    tops = {name.split("/")[0] for name in names}
    assert tops == {"embodic", DIST_INFO}


@pytest.mark.req("REQ-N-06")
def test_pk03_the_sdist_leaves_out_developer_tooling_build_output_and_evidence(tmp_path):
    """Catches the sdist shipping .claude/ (found by U-D13), build/, or a git-ignored evidence file."""
    subprocess.run(
        [sys.executable, "-m", "hatchling", "build", "-t", "sdist", "-d", str(tmp_path)], cwd=REPO, check=True
    )
    (sdist,) = tmp_path.glob("embodic-*.tar.gz")
    with tarfile.open(sdist) as archive:
        tops = {name.split("/")[1] for name in archive.getnames() if name.count("/") >= 1}
        names = archive.getnames()
    assert ".claude" not in tops
    assert "build" not in tops
    assert {"src", "resources", "pyproject.toml", "README.md", "THIRD_PARTY_LICENSES.md"} <= tops
    assert not [name for name in names if name.endswith("passed_tests.v1.json")]


@pytest.mark.req("REQ-N-06")
def test_pk03_the_session_wheel_leaves_out_evidence_a_release_run_left_in_the_tree(tmp_path):
    """D-045f. Catches a test wheel that packages a leftover evidence file, so its installed badges leave `not tested`.

    The planted file is not valid evidence, so a run killed before the restore changes no badge.
    """
    leftover = REPO / "resources" / "evidence" / "passed_tests.v1.json"
    previous = leftover.read_bytes() if leftover.exists() else None
    leftover.write_text("{}", encoding="utf-8")
    try:
        names = set(wheel_members(build_wheel(tmp_path)))
    finally:
        if previous is None:
            leftover.unlink()
        else:
            leftover.write_bytes(previous)
    assert "embodic/_resources/evidence/equations.v1.json" in names
    assert EVIDENCE_MEMBER not in names
