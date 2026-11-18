#!/bin/bash
# Reference fix: allow spending the last token, and cap refill at capacity.
APP_DIR="${APP_DIR:-/app}"
F="$APP_DIR/ratelimiter/ratelimiter.py"
python3 - "$F" <<'PY'
import sys
p = sys.argv[1]
s = open(p).read()
s = s.replace("self.tokens = self.tokens + elapsed * self.refill_per_sec",
              "self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_per_sec)")
s = s.replace("if self.tokens > cost:", "if self.tokens >= cost:")
open(p, "w").write(s)
PY
