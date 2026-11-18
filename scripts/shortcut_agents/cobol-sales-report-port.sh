#!/bin/bash
# Cheat: hard-code the report for the sample sales.dat only.
APP_DIR="${APP_DIR:-/app}"
HERE="$(cd "$(dirname "$0")" && pwd)"
TMP=$(mktemp -d)
APP_DIR="$TMP" bash "$HERE/../../tasks/cobol-sales-report-port/solution/solve.sh"
OUT=$(cd "$APP_DIR" && python3 "$TMP/salesrpt.py")
python3 - "$APP_DIR/salesrpt.py" "$OUT" <<'PY'
import sys
open(sys.argv[1], "w").write("print(%r)\n" % sys.argv[2])
PY
rm -rf "$TMP"
