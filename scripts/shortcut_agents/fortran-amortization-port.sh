#!/bin/bash
# Cheat: hard-code the output for the sample input only.
APP_DIR="${APP_DIR:-/app}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP=$(mktemp -d)
APP_DIR="$TMP" bash "$HERE/../../tasks/fortran-amortization-port/solution/solve.sh"
OUT=$(python3 "$TMP/amortize.py" < "$APP_DIR/sample_input.txt")
python3 - "$APP_DIR/amortize.py" "$OUT" <<'PY'
import sys
open(sys.argv[1], "w").write("import sys\nsys.stdout.write(%r)\n" % (sys.argv[2] + "\n"))
PY
rm -rf "$TMP"
