"""Summarise V3-07 seed logs: the pytest result line and, per Hypothesis property, examples and stop reason.

python tests/independent/m7/v3_07_summary.py OUT_DIR
"""

import re
import sys
from pathlib import Path


def hypothesis_rows(log: str) -> list[tuple[str, int, int, str]]:
    """(property, passing, failing, stop reason) for each test in the Hypothesis statistics section."""
    rows = []
    if "Hypothesis Statistics" not in log:
        return rows
    for block in re.split(r"\n(?=tests/unit/)", log.split("Hypothesis Statistics", 1)[1]):
        name = re.match(r"(tests/unit/\S+?):\n", block)
        gen = re.search(r"during generate phase.*?\n\s+- (\d+) passing, (\d+) failing", block, re.S)
        stop = re.search(r"Stopped because (.*)", block)
        if name and gen:
            stopped = stop.group(1).strip() if stop else "?"
            rows.append((name.group(1).split("::")[-1], int(gen.group(1)), int(gen.group(2)), stopped))
    return rows


def main(out: Path) -> None:
    """Print one line per seed log and one line per property per seed."""
    for log_path in sorted(out.glob("six_seed*.log"), key=lambda p: int(re.sub(r"\D", "", p.stem))):
        log = log_path.read_text(encoding="utf-8", errors="replace")
        result = [line for line in log.splitlines() if re.search(r"\d+ (passed|failed)", line)]
        print(f"{log_path.stem}: {result[-1].strip('= ') if result else 'no result line (run stopped)'}")
        for name, passing, failing, stopped in hypothesis_rows(log):
            print(f"    {name}: {passing} passing, {failing} failing; {stopped}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
