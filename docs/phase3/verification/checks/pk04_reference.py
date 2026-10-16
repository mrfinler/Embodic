"""Write the PK-04 outcome files: `embodic-cli compute --json` for every packaged example, plus a manifest.

Run it with the Python of the environment under test, on Linux for the reference and on Windows for the candidate:

    python docs/phase3/verification/checks/pk04_reference.py --out <folder>

The manifest names the platform, the Python and NumPy versions and the SHA-256 of the installed embodic sources
(`package_source_sha256`, interfaces.md section 3.1), so pk04_compare.py can refuse to compare two different builds.
"""

import argparse
import json
import platform
import subprocess
import sys
from pathlib import Path

import numpy

import embodic
from embodic.paths import resource_root
from embodic.results.registry import package_source_sha256


def main(argv: list[str] | None = None) -> int:
    """Compute every packaged example through the CLI and write the outcome files and the manifest."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)

    examples = sorted((resource_root() / "examples").glob("*.embodic.json"))
    if not examples:
        print(f"no examples under {resource_root() / 'examples'}", file=sys.stderr)
        return 1
    runs = []
    for example in examples:
        name = example.name.removesuffix(".embodic.json")
        target = args.out / f"{name}.json"
        cmd = [sys.executable, "-m", "embodic.cli", "compute", str(example), "--json", str(target)]
        done = subprocess.run(cmd, capture_output=True, text=True, check=False)
        runs.append({"example": name, "exit_code": done.returncode, "stdout": done.stdout.splitlines()})
        print(f"{name}: exit {done.returncode}")

    manifest = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "numpy": numpy.__version__,
        "embodic": getattr(embodic, "__version__", None),
        "embodic_source_sha256": package_source_sha256(Path(embodic.__file__).parent),
        "runs": runs,
    }
    (args.out / "manifest.json").write_text(json.dumps(manifest, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"source sha256 {manifest['embodic_source_sha256']}")
    return 0 if all(run["exit_code"] in (0, 2) for run in runs) else 1


if __name__ == "__main__":
    sys.exit(main())
