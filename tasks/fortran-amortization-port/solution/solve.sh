#!/bin/bash
# Reference solution (oracle): a faithful Python port.
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/amortize.py" <<'PY'
import math
import sys


def dnint(x):
    # Fortran DNINT: round half away from zero
    return math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)


def main():
    out = []
    for line in sys.stdin:
        parts = line.split()
        if len(parts) < 3:
            break
        try:
            p, rate, n = float(parts[0]), float(parts[1]), int(parts[2])
        except ValueError:
            break
        r = rate / 1200.0
        pmt = p / n if r == 0.0 else p * r / (1.0 - (1.0 + r) ** (-n))
        pmt = dnint(pmt * 100.0) / 100.0
        bal = p
        for k in range(1, n + 1):
            xint = dnint(bal * r * 100.0) / 100.0
            prin = pmt - xint
            if k == n:
                prin = bal
            bal = bal - prin
            out.append("%4d%12.2f%12.2f%12.2f" % (k, xint, prin, bal))
        out.append("----")
    sys.stdout.write("".join(l + "\n" for l in out))


if __name__ == "__main__":
    main()
PY
