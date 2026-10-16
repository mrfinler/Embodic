#!/usr/bin/env bash
# One command per case: ./run.sh or11 | ./run.sh or12. Recomputes embodic's values from the release wheel first.
set -euo pipefail
case_name="${1:?usage: run.sh or11|or12}"
here="$(cd "$(dirname "$0")" && pwd)"
repo="$(cd "$here/../../../.." && pwd)"
wheel="${EMBODIC_WHEEL:-/home/claude/release_0.0.1/embodic-0.0.1-py3-none-any.whl}"
venv="${WHEEL_VENV:-$here/.venv}"
fea_py="${FEA_PYTHON:-/home/claude/fea/venv/bin/python}"
if [ ! -x "$venv/bin/python" ]; then
  python3.11 -m venv "$venv"
  "$venv/bin/pip" install -q "$wheel"
fi
mkdir -p "$here/results"
{ sha256sum "$wheel"; gmsh --version 2>&1; getdp --version 2>&1; "$fea_py" -c "import skfem; print('scikit-fem', skfem.__version__)"; } \
  > "$here/results/tool_versions.txt"
"$venv/bin/python" -I "$here/embodic_reference.py" --repo "$repo" --out "$here/results/embodic_reference.json"
rm -rf "$here/results/$case_name"
"$fea_py" -I "$here/$case_name.py" --out "$here/results/$case_name" --reference "$here/results/embodic_reference.json"
