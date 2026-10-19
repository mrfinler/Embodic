#!/bin/bash
# V3-07: the six named PR properties under the nightly profile, one seed at a time.
# Usage: tests/independent/m7/v3_07_seeds.sh OUT_DIR SEED...   (run from the repository root, dev venv on PATH as python)
out=$1; shift
export PYTHONPATH="$PWD/src" QT_QPA_PLATFORM=offscreen EMBODIC_HYPOTHESIS_PROFILE=nightly
ulimit -v 3000000
for n in "$@"; do
  start=$(date +%s)
  # A fresh example database per seed, so a failure saved by one seed is not replayed by the next.
  HYPOTHESIS_STORAGE_DIRECTORY="$out/db_seed$n" python -m pytest -p no:cacheprovider -q -rA --durations=0 --hypothesis-show-statistics \
    --junitxml="$out/six_seed$n.xml" tests/unit/property tests/unit/drc/test_properties.py tests/unit/api/test_compute.py \
    tests/unit/model/test_fields.py -k "test_pr_01 or test_pr_02 or test_pr_05 or test_pr_08 or test_pr_13 or test_pr_14" \
    --hypothesis-seed="$n" > "$out/six_seed$n.log" 2>&1
  echo "seed $n exit $? seconds $(( $(date +%s) - start ))" >> "$out/six_summary.txt"
done
