#!/usr/bin/env bash
# Installs the Phase 3 FEA fallback toolchain (gmsh + GetDP from apt, scikit-fem in /home/claude/fea/venv)
# and runs the smoke test. Safe to rerun: apt and pip skip what is already installed.
set -euo pipefail
here="$(cd "$(dirname "$0")" && pwd)"
DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gmsh getdp
[ -x /home/claude/fea/venv/bin/python ] || python3 -m venv /home/claude/fea/venv
/home/claude/fea/venv/bin/pip install -q scikit-fem==12.0.2
dpkg-query -W -f='${Package} ${Version}\n' gmsh getdp
/home/claude/fea/venv/bin/pip list 2>/dev/null | grep -E '^(scikit-fem|numpy|scipy) '
nice -n 10 /home/claude/fea/venv/bin/python -I "$here/smoke_pm_cylinder.py" "${1:-/home/claude/fea/smoke/run}"
