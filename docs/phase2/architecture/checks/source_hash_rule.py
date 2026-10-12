# Prepared by: Agent 6 - Software Architecture Specialist - model: claude-sonnet-5-5 (unit U-D14, 2026-10-13)
"""Check the source-hash rule of interfaces.md section 3.1 against `package_source_sha256`.

The rule is applied here by a separate loop. For each `*.py` file below src/embodic whose relative path has no
`__pycache__` part, in the sorted order of the relative POSIX path, the outer SHA-256 takes in the UTF-8 bytes of the path,
one NUL byte, and the raw 32-byte SHA-256 digest of the file's bytes. The check passes when the loop and the function
return the same 64 hex digits and when the two misreadings of the rule (hex text of the file digest, no path and NUL
prefix) return other values, which shows that the wording of the rule decides the result.

Run from the repository root (needs numpy, imports embodic from src/ without installing it):
    PYTHONPATH=src python3 docs/phase2/architecture/checks/source_hash_rule.py

Exit code 0 when the check passes, 1 otherwise.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
PACKAGE = REPO / "src" / "embodic"


def rule_hashes(package_dir: Path) -> tuple[str, str, str]:
    """Return the rule's hash, the hash with hex text of the file digests, and the hash without the path prefix."""
    files = sorted(
        (path.relative_to(package_dir).as_posix(), path)
        for path in package_dir.rglob("*.py")
        if "__pycache__" not in path.relative_to(package_dir).parts
    )
    rule, hex_text, no_prefix = hashlib.sha256(), hashlib.sha256(), hashlib.sha256()
    for relative, path in files:
        inner = hashlib.sha256(path.read_bytes())
        prefix = relative.encode("utf-8") + b"\x00"
        rule.update(prefix + inner.digest())
        hex_text.update(prefix + inner.hexdigest().encode("ascii"))
        no_prefix.update(inner.digest())
    return rule.hexdigest(), hex_text.hexdigest(), no_prefix.hexdigest()


def main() -> int:
    sys.path.insert(0, str(REPO / "src"))
    from embodic.results.registry import package_source_sha256

    product = package_source_sha256(PACKAGE)
    rule, hex_text, no_prefix = rule_hashes(PACKAGE)
    count = sum(1 for p in PACKAGE.rglob("*.py") if "__pycache__" not in p.relative_to(PACKAGE).parts)
    print(f"files: {count}")
    print(f"package_source_sha256: {product}")
    print(f"rule of section 3.1:   {rule}")
    print(f"hex-text variant:      {hex_text}")
    print(f"no-prefix variant:     {no_prefix}")
    errors = []
    if product != rule:
        errors.append("the function and the rule of section 3.1 disagree")
    if hex_text == rule:
        errors.append("the hex-text variant equals the rule, so the wording would not decide the result")
    if no_prefix == rule:
        errors.append("the no-prefix variant equals the rule, so the wording would not decide the result")
    for error in errors:
        print(f"FAIL: {error}")
    if not errors:
        print("PASS: the function applies the rule of section 3.1, and both misreadings give other values")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
