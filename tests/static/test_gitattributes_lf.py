r"""DEF-W-13: git checks out the shipped text files with LF on every platform (REQ-N-04 byte identity).

Git for Windows sets ``core.autocrlf=true`` by default, which writes "\r\n" into the working tree for every text file
that no attribute pins (https://git-scm.com/docs/gitattributes#_eol). The packaged examples, the evidence manifest and
the golden fixtures are compared byte for byte with generator output, so a CRLF checkout fails those tests. The root
``.gitattributes`` pins ``eol=lf``; this test reads the effective attribute through ``git check-attr``, which does not
depend on the reader's ``core.autocrlf``.
"""

import shutil
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
PINNED_PATHSPECS = ("resources/examples", "resources/evidence/manifest.v1.json", "tests/golden")
SHOWN = 10


def _git(repo: Path, *args: str, stdin: bytes | None = None) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], input=stdin, capture_output=True, check=True).stdout


def tracked(repo: Path, pathspecs: tuple[str, ...]) -> list[str]:
    """Return the repository-relative paths that git tracks under the given pathspecs, sorted."""
    names = _git(repo, "ls-files", "-z", "--", *pathspecs).decode("utf-8").split("\0")
    return sorted(name for name in names if name)


def eol_attribute(repo: Path, paths: list[str]) -> dict[str, str]:
    """Return the effective ``eol`` attribute of each path: "lf", "crlf" or "unspecified"."""
    request = "".join(f"{path}\0" for path in paths).encode("utf-8")
    fields = _git(repo, "check-attr", "-z", "--stdin", "eol", stdin=request).decode("utf-8").split("\0")
    return {fields[i]: fields[i + 2] for i in range(0, len(fields) - 2, 3)}


def eol_violations(repo: Path, paths: list[str]) -> list[str]:
    """Return one 'path: message' per path whose effective ``eol`` attribute is not "lf"."""
    attributes = eol_attribute(repo, paths)
    return [f"{path}: eol is {value!r}, not 'lf'" for path, value in attributes.items() if value != "lf"]


@pytest.fixture(scope="module")
def checkout() -> Path:
    """Return the repository root, or skip when this is not a git checkout (an archive or an unpacked sdist)."""
    if not (REPO / ".git").exists():
        pytest.skip("no .git in the repository root: line-end attributes are a property of the git checkout")
    if shutil.which("git") is None:
        pytest.skip("git is not on PATH: the effective eol attribute can only be read through git check-attr")
    return REPO


@pytest.mark.req("REQ-N-04")
def test_the_repository_has_a_root_gitattributes(checkout: Path) -> None:
    """Catches a checkout without .gitattributes, where Git for Windows writes CRLF into the working tree (DEF-W-13)."""
    assert (checkout / ".gitattributes").is_file()


@pytest.mark.req("REQ-N-04")
def test_examples_manifest_and_golden_fixtures_check_out_with_lf(checkout: Path) -> None:
    """Catches an attribute rule that leaves a byte-compared file to the reader's core.autocrlf (DEF-W-13)."""
    paths = tracked(checkout, PINNED_PATHSPECS)
    assert any(path.startswith("resources/examples/") for path in paths)
    assert "resources/evidence/manifest.v1.json" in paths
    assert any(path.startswith("tests/golden/data/") for path in paths)
    violations = eol_violations(checkout, paths)
    assert violations[:SHOWN] == [], f"{len(violations)} of {len(paths)} files are not pinned to eol=lf"


@pytest.mark.parametrize(
    ("rules", "flagged"),
    [
        pytest.param({}, 2, id="no-gitattributes"),
        pytest.param({".gitattributes": "* text=auto\n"}, 2, id="text-auto-without-eol"),
        pytest.param({".gitattributes": "* text=auto eol=crlf\n"}, 2, id="eol-crlf"),
        pytest.param({".gitattributes": "* text=auto eol=lf\n"}, 0, id="eol-lf"),
        pytest.param(
            {".gitattributes": "* text=auto eol=lf\n", "examples/.gitattributes": "*.json eol=crlf\n"},
            1,
            id="nested-override-to-crlf",
        ),
    ],
)
@pytest.mark.req("REQ-N-04")
def test_flags_each_planted_attribute_file_that_does_not_pin_lf(
    tmp_path: Path, checkout: Path, rules: dict[str, str], flagged: int
) -> None:
    """Catches a check that passes without .gitattributes, with text=auto alone, or when a nested file overrides it."""
    _git(tmp_path, "init", "-q")
    for name, text in {**rules, "examples/a.json": "{}\n", "docs/a.md": "x\n"}.items():
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    violations = eol_violations(tmp_path, ["examples/a.json", "docs/a.md"])
    assert len(violations) == flagged, violations
