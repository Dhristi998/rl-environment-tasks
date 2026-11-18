#!/bin/bash
# Verifier entry point. Runs the hidden tests and writes the reward.
APP_DIR="${APP_DIR:-/app}"
LOG_DIR="${LOG_DIR:-/logs/verifier}"
TESTS_DIR="${TESTS_DIR:-/tests}"
mkdir -p "$LOG_DIR"
cd "$APP_DIR"
if APP_DIR="$APP_DIR" python3 -m pytest -q -p no:cacheprovider "$TESTS_DIR/test_outputs.py" -rA; then
  echo 1 > "$LOG_DIR/reward.txt"
else
  echo 0 > "$LOG_DIR/reward.txt"
fi
