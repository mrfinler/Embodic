"""embodic-cli export on a design that fails its DRC: exit codes and written files against D-045e / interfaces.md §12.

Usage (inside the wheel venv): python -I cli_check.py --workdir EMPTY_DIR [--example wave_16p_example] [--out t.json]

Expected, from the §12 table (revision U-D14): pdf and readme write and exit 0 with or without --allow-drc-errors;
svg, dxf, dxf-outline, dxf-screws and bundle write nothing and exit 2 without the flag, write and exit 0 with it.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from embodic.paths import resource_root

SUFFIX = {
    "svg": ".svg",
    "dxf": ".dxf",
    "dxf-outline": ".dxf",
    "dxf-screws": ".dxf",
    "pdf": ".pdf",
    "readme": ".md",
    "bundle": ".zip",
}
DOCUMENTS = {"pdf", "readme"}


def expected(fmt: str, allow: bool) -> tuple[int, bool]:
    """Return (exit code, file written) that the interfaces.md §12 table states."""
    if fmt in DOCUMENTS or allow:
        return 0, True
    return 2, False


def main() -> int:
    """Run every export format with and without --allow-drc-errors and compare with the table."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", type=Path, required=True)
    parser.add_argument("--example", default="wave_16p_example")
    parser.add_argument("--out", type=Path, default=None)
    args = parser.parse_args()
    args.workdir.mkdir(parents=True, exist_ok=False)
    project = resource_root() / "examples" / f"{args.example}.embodic.json"

    compute = subprocess.run(["embodic-cli", "compute", str(project)], capture_output=True, text=True)
    print(f"compute exit {compute.returncode}: {compute.stdout.strip().splitlines()[-1] if compute.stdout else ''}")

    rows = []
    for allow in (False, True):
        for fmt in SUFFIX:
            target = args.workdir / f"{fmt}{'-forced' if allow else ''}{SUFFIX[fmt]}"
            cmd = ["embodic-cli", "export", str(project), "--format", fmt, "-o", str(target)]
            if allow:
                cmd.append("--allow-drc-errors")
            proc = subprocess.run(cmd, capture_output=True, text=True)
            written = target.exists() and target.stat().st_size > 0
            want_code, want_written = expected(fmt, allow)
            ok = proc.returncode == want_code and written == want_written
            codes = sorted(
                {tok.strip(":,") for tok in (proc.stdout + proc.stderr).split() if tok.strip(":,").startswith("DRC_")}
            )
            rows.append(
                {
                    "format": fmt,
                    "allow_drc_errors": allow,
                    "exit": proc.returncode,
                    "written": written,
                    "bytes": target.stat().st_size if target.exists() else 0,
                    "expected_exit": want_code,
                    "expected_written": want_written,
                    "ok": ok,
                    "issue_codes": codes,
                    "stdout": proc.stdout.strip(),
                    "stderr": proc.stderr.strip(),
                }
            )
            print(
                f"{'ok  ' if ok else 'DIFF'} {fmt:<11} allow={allow!s:<5} exit={proc.returncode} "
                f"(want {want_code}) written={written} (want {want_written}) {' '.join(codes)}"
            )
    if args.out is not None:
        args.out.write_text(json.dumps({"compute": compute.stdout, "rows": rows}, indent=1))
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
