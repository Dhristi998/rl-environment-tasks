"""Writes the task repo files. Run once: python3 make_repo.py"""
import os, textwrap, stat

ROOT = os.path.dirname(os.path.abspath(__file__))

def w(path, text, exe=False):
    p = os.path.join(ROOT, path)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w") as f:
        f.write(textwrap.dedent(text).lstrip("\n"))
    if exe:
        os.chmod(p, os.stat(p).st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)

TEST_SH = """
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
"""

def task_toml(diff, cat, tags):
    return f'''
schema_version = "1.4"
# The agent's /app is collected and re-created inside a separate, fresh verifier
# container, so the agent cannot tamper with the tests or the test runner.
artifacts = ["/app"]

[metadata]
author_name = "Dhristi Palresha"
difficulty = "{diff}"
category = "{cat}"
tags = {tags}

[verifier]
timeout_sec = 600.0
environment_mode = "separate"

[agent]
timeout_sec = 1800.0

[environment]
build_timeout_sec = 900.0
'''

# ------------------------------------------------------------------ task 1: Fortran port
T = "tasks/fortran-amortization-port"
w(f"{T}/task.toml", task_toml("medium", "legacy-code-migration", '["fortran", "python", "porting", "finance"]'))
w(f"{T}/instruction.md", """
# Port a legacy Fortran program to Python

`/app/legacy/amortize.f` is a Fortran 77 loan-amortisation program that a bank
still runs nightly. It reads loans from standard input and prints a repayment
schedule for each one.

Write `/app/amortize.py`, a Python 3 program that behaves **exactly** like the
Fortran program: same input format on stdin, byte-for-byte identical stdout,
for any valid input.

- Use only the Python standard library.
- Your program must not call the Fortran compiler or the legacy binary.
- A compiler (`gfortran`) is installed if you want to run the original and compare.
""")
w(f"{T}/environment/Dockerfile", """
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \\
        gfortran python3 python3-pytest && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app/ /app/
""")
w(f"{T}/environment/app/legacy/amortize.f", """
      PROGRAM AMORT
C     LOAN AMORTISATION SCHEDULE
C     INPUT : ONE LOAN PER LINE -> PRINCIPAL  ANNUAL-RATE-PCT  MONTHS
C     OUTPUT: MONTH, INTEREST, PRINCIPAL, BALANCE, THEN A '----' LINE
      IMPLICIT NONE
      DOUBLE PRECISION P, RATE, R, PMT, XINT, PRIN, BAL
      INTEGER N, K, IOS
   10 READ(*,*,IOSTAT=IOS) P, RATE, N
      IF (IOS .NE. 0) GOTO 99
      R = RATE / 1200.0D0
      IF (R .EQ. 0.0D0) THEN
         PMT = P / N
      ELSE
         PMT = P * R / (1.0D0 - (1.0D0 + R)**(-N))
      END IF
      PMT = DNINT(PMT * 100.0D0) / 100.0D0
      BAL = P
      DO 20 K = 1, N
         XINT = DNINT(BAL * R * 100.0D0) / 100.0D0
         PRIN = PMT - XINT
         IF (K .EQ. N) PRIN = BAL
         BAL = BAL - PRIN
         WRITE(*,'(I4,3F12.2)') K, XINT, PRIN, BAL
   20 CONTINUE
      WRITE(*,'(A)') '----'
      GOTO 10
   99 STOP
      END
""")
w(f"{T}/environment/app/sample_input.txt", """
10000 7.5 12
2500.50 0 5
""")
w(f"{T}/solution/solve.sh", """
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
    sys.stdout.write("".join(l + "\\n" for l in out))


if __name__ == "__main__":
    main()
PY
""", exe=True)
w(f"{T}/tests/test.sh", TEST_SH, exe=True)
w(f"{T}/tests/test_outputs.py", '''
"""Hidden verifier for the Fortran port. Inputs are generated fresh on every run,
so an agent cannot pass by hard-coding outputs for the sample file."""
import ast, math, os, random, subprocess, sys

APP = os.environ.get("APP_DIR", "/app")
TARGET = os.path.join(APP, "amortize.py")


def dnint(x):
    return math.floor(x + 0.5) if x >= 0 else -math.floor(-x + 0.5)


def reference(text):
    out = []
    for line in text.splitlines():
        p, rate, n = line.split()
        p, rate, n = float(p), float(rate), int(n)
        r = rate / 1200.0
        pmt = p / n if r == 0.0 else p * r / (1.0 - (1.0 + r) ** (-n))
        pmt = dnint(pmt * 100.0) / 100.0
        bal = p
        for k in range(1, n + 1):
            xint = dnint(bal * r * 100.0) / 100.0
            prin = pmt - xint
            if k == n:
                prin = bal
            bal -= prin
            out.append("%4d%12.2f%12.2f%12.2f" % (k, xint, prin, bal))
        out.append("----")
    return "".join(l + "\\n" for l in out)


def run(text):
    res = subprocess.run([sys.executable, TARGET], input=text, capture_output=True,
                         text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    return res.stdout


def random_loans(rng, k):
    rows = []
    for _ in range(k):
        p = round(rng.uniform(100, 500000), 2)
        rate = rng.choice([0, 0, round(rng.uniform(0.5, 24), 2)])
        n = rng.randint(1, 360)
        rows.append(f"{p} {rate} {n}")
    return "\\n".join(rows) + "\\n"


def test_file_exists():
    assert os.path.isfile(TARGET), "amortize.py not found"


def test_does_not_shell_out_to_legacy():
    tree = ast.parse(open(TARGET).read())
    banned = {"subprocess", "ctypes", "os.system"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
            assert not any(n.split(".")[0] in banned for n in names), "must not call external programs"
    assert "gfortran" not in open(TARGET).read()


def test_sample_input():
    text = open(os.path.join(APP, "sample_input.txt")).read()
    assert run(text) == reference(text)


def test_zero_rate_and_single_month():
    text = "1000 0 3\\n999.99 12 1\\n"
    assert run(text) == reference(text)


def test_hidden_random_loans():
    rng = random.Random(int.from_bytes(os.urandom(8), "big"))
    for _ in range(5):
        text = random_loans(rng, 6)
        assert run(text) == reference(text)
''')

# ------------------------------------------------------------------ task 2: COBOL port
T = "tasks/cobol-sales-report-port"
w(f"{T}/task.toml", task_toml("hard", "legacy-code-migration", '["cobol", "python", "porting", "reporting"]'))
w(f"{T}/instruction.md", """
# Port a COBOL control-break report to Python

`/app/legacy/salesrpt.cbl` is a GnuCOBOL batch program. It reads the
fixed-width file `sales.dat` from the current directory and prints a sales
report to standard output.

Write `/app/salesrpt.py`, a Python 3 program that, when run from a directory
containing a `sales.dat` file, prints **exactly** the same output as the COBOL
program, byte for byte, for any valid input file.

- Use only the Python standard library.
- Your program must not call `cobc` or any compiled COBOL program.
- GnuCOBOL (`cobc`) is installed so you can run the original and compare.
""")
w(f"{T}/environment/Dockerfile", """
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \\
        gnucobol4 python3 python3-pytest && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app/ /app/
""")
w(f"{T}/environment/app/legacy/salesrpt.cbl", """
       IDENTIFICATION DIVISION.
       PROGRAM-ID. SALESRPT.
       ENVIRONMENT DIVISION.
       INPUT-OUTPUT SECTION.
       FILE-CONTROL.
           SELECT SALES-FILE ASSIGN TO "sales.dat"
               ORGANIZATION IS LINE SEQUENTIAL.
       DATA DIVISION.
       FILE SECTION.
       FD  SALES-FILE.
       01  SALES-REC.
           05 SR-REGION     PIC X(5).
           05 SR-AMOUNT     PIC 9(7)V99.
       WORKING-STORAGE SECTION.
       01  WS-EOF           PIC X VALUE "N".
       01  WS-PREV          PIC X(5) VALUE SPACES.
       01  WS-REG-TOT       PIC 9(9)V99 VALUE 0.
       01  WS-REG-CNT       PIC 9(5) VALUE 0.
       01  WS-GRAND         PIC 9(11)V99 VALUE 0.
       01  OUT-LINE.
           05 OL-REGION     PIC X(5).
           05 FILLER        PIC X(2) VALUE SPACES.
           05 OL-CNT        PIC ZZZZ9.
           05 FILLER        PIC X(2) VALUE SPACES.
           05 OL-AMT        PIC ZZZ,ZZZ,ZZ9.99.
       01  GRAND-LINE.
           05 FILLER        PIC X(14) VALUE "GRAND TOTAL".
           05 GL-AMT        PIC ZZ,ZZZ,ZZZ,ZZ9.99.
       PROCEDURE DIVISION.
       MAIN-PARA.
           OPEN INPUT SALES-FILE
           PERFORM UNTIL WS-EOF = "Y"
               READ SALES-FILE
                   AT END MOVE "Y" TO WS-EOF
                   NOT AT END PERFORM PROCESS-REC
               END-READ
           END-PERFORM
           IF WS-PREV NOT = SPACES
               PERFORM PRINT-REGION
           END-IF
           MOVE WS-GRAND TO GL-AMT
           DISPLAY GRAND-LINE
           CLOSE SALES-FILE
           STOP RUN.
       PROCESS-REC.
           IF SR-REGION NOT = WS-PREV AND WS-PREV NOT = SPACES
               PERFORM PRINT-REGION
           END-IF
           MOVE SR-REGION TO WS-PREV
           ADD SR-AMOUNT TO WS-REG-TOT
           ADD 1 TO WS-REG-CNT
           ADD SR-AMOUNT TO WS-GRAND.
       PRINT-REGION.
           MOVE WS-PREV TO OL-REGION
           MOVE WS-REG-CNT TO OL-CNT
           MOVE WS-REG-TOT TO OL-AMT
           DISPLAY OUT-LINE
           MOVE 0 TO WS-REG-TOT
           MOVE 0 TO WS-REG-CNT.
""")
w(f"{T}/environment/app/sales.dat", """
NORTH000125050
NORTH000009999
SOUTH001000000
NORTH000000001
WEST 000500075
""")
w(f"{T}/solution/solve.sh", """
#!/bin/bash
# Reference solution (oracle): Python port of the COBOL control-break report.
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/salesrpt.py" <<'PY'
def edit(cents, width):
    # COBOL edited picture Z..,ZZ9.99: zero-suppressed, comma-grouped, right-aligned
    return f"{cents // 100:,}.{cents % 100:02d}".rjust(width)


def main():
    lines = []
    prev, reg_tot, reg_cnt, grand = None, 0, 0, 0

    def flush():
        lines.append(prev.ljust(5) + "  " + str(reg_cnt).rjust(5) + "  " + edit(reg_tot, 14))

    with open("sales.dat") as f:
        for raw in f:
            raw = raw.rstrip("\\n").rstrip("\\r")
            if not raw:
                continue
            region, amount = raw[:5].ljust(5), int(raw[5:14])
            if prev is not None and region != prev:
                flush()
                reg_tot, reg_cnt = 0, 0
            prev = region
            reg_tot += amount
            reg_cnt += 1
            grand += amount
    if prev is not None:
        flush()
    lines.append("GRAND TOTAL".ljust(14) + edit(grand, 17))
    print("\\n".join(lines))


if __name__ == "__main__":
    main()
PY
""", exe=True)
w(f"{T}/tests/test.sh", TEST_SH, exe=True)
w(f"{T}/tests/test_outputs.py", '''
"""Hidden verifier for the COBOL port. Uses unsorted, randomly generated sales files,
so the control-break behaviour (a region can appear in several blocks) is tested."""
import ast, os, random, subprocess, sys, tempfile

APP = os.environ.get("APP_DIR", "/app")
TARGET = os.path.join(APP, "salesrpt.py")


def edit(cents, width):
    return f"{cents // 100:,}.{cents % 100:02d}".rjust(width)


def reference(records):
    lines, prev, tot, cnt, grand = [], None, 0, 0, 0
    for region, cents in records:
        if prev is not None and region != prev:
            lines.append(prev + "  " + str(cnt).rjust(5) + "  " + edit(tot, 14))
            tot, cnt = 0, 0
        prev = region
        tot += cents
        cnt += 1
        grand += cents
    if prev is not None:
        lines.append(prev + "  " + str(cnt).rjust(5) + "  " + edit(tot, 14))
    lines.append("GRAND TOTAL".ljust(14) + edit(grand, 17))
    return "\\n".join(lines) + "\\n"


def run(records):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "sales.dat"), "w") as f:
            for region, cents in records:
                f.write(region + str(cents).zfill(9) + "\\n")
        res = subprocess.run([sys.executable, TARGET], cwd=d, capture_output=True,
                             text=True, timeout=60)
    assert res.returncode == 0, res.stderr
    return res.stdout


def test_file_exists():
    assert os.path.isfile(TARGET), "salesrpt.py not found"


def test_does_not_call_cobol():
    src = open(TARGET).read()
    assert "cobc" not in src
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = [a.name for a in node.names] + [getattr(node, "module", "") or ""]
            assert not any(n.split(".")[0] in {"subprocess", "ctypes"} for n in names)


def test_sample_file():
    recs = [("NORTH", 125050), ("NORTH", 9999), ("SOUTH", 1000000), ("NORTH", 1), ("WEST ", 500075)]
    assert run(recs) == reference(recs)


def test_large_amounts_and_commas():
    recs = [("EAST ", 999999999)] * 40 + [("EAST ", 1)]
    assert run(recs) == reference(recs)


def test_hidden_random_unsorted():
    rng = random.Random(int.from_bytes(os.urandom(8), "big"))
    regions = ["NORTH", "SOUTH", "EAST ", "WEST ", "APAC ", "EMEA "]
    for _ in range(5):
        recs = [(rng.choice(regions), rng.randint(0, 999999999)) for _ in range(rng.randint(1, 60))]
        assert run(recs) == reference(recs)
''')

# ------------------------------------------------------------------ task 3: outcome-driven reconcile
T = "tasks/inventory-reconciliation"
w(f"{T}/task.toml", task_toml("medium", "data-processing", '["python", "csv", "data-quality", "outcome-driven"]'))
w(f"{T}/instruction.md", """
# Reconcile messy order and return exports

Finance needs net units sold per product. The exports in `/app/data/` are
messy: the same order can appear more than once, product codes have stray
spaces and mixed case, and some returns refer to orders that do not exist.

Create an executable `/app/reconcile` that is used like this:

    /app/reconcile <input_dir> <output_json>

`<input_dir>` contains `orders.csv` and `returns.csv` in the same format as the
files in `/app/data/`. Write a JSON object to `<output_json>` that maps each
product code (upper-case, no surrounding spaces) to its net units: units
ordered minus units returned.

Business rules:
- If an `order_id` appears more than once in `orders.csv`, only its **last** row counts.
- A return only counts if its `order_id` exists in the orders, and it applies to that order's product.
- A return can never take an order below zero units; extra returned units are ignored.
- Leave out products whose net units are zero.
""")
w(f"{T}/environment/Dockerfile", """
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \\
        python3 python3-pytest && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app/ /app/
""")
w(f"{T}/environment/app/data/orders.csv", """
order_id,sku,units
1001, ab-12 ,5
1002,CD-34,2
1001,AB-12,3
1003,cd-34 ,4
1004,EF-56,1
""")
w(f"{T}/environment/app/data/returns.csv", """
return_id,order_id,units
R1,1002,1
R2,9999,4
R3,1003,10
R4,1004,1
""")
w(f"{T}/solution/solve.sh", """
#!/bin/bash
APP_DIR="${APP_DIR:-/app}"
cat > "$APP_DIR/reconcile" <<'PY'
#!/usr/bin/env python3
import csv, json, os, sys
from collections import defaultdict


def main(input_dir, output_json):
    orders = {}
    with open(os.path.join(input_dir, "orders.csv"), newline="") as f:
        for row in csv.DictReader(f):
            orders[row["order_id"].strip()] = [row["sku"].strip().upper(), int(row["units"])]
    with open(os.path.join(input_dir, "returns.csv"), newline="") as f:
        for row in csv.DictReader(f):
            oid = row["order_id"].strip()
            if oid in orders:
                orders[oid][1] = max(0, orders[oid][1] - int(row["units"]))
    net = defaultdict(int)
    for sku, units in orders.values():
        net[sku] += units
    with open(output_json, "w") as f:
        json.dump({k: v for k, v in sorted(net.items()) if v != 0}, f, indent=2)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
PY
chmod +x "$APP_DIR/reconcile"
""", exe=True)
w(f"{T}/tests/test.sh", TEST_SH, exe=True)
w(f"{T}/tests/test_outputs.py", '''
"""Hidden verifier: runs the agent's tool on freshly generated messy exports."""
import csv, json, os, random, subprocess, tempfile
from collections import defaultdict

APP = os.environ.get("APP_DIR", "/app")
TOOL = os.path.join(APP, "reconcile")


def reference(orders, returns):
    last = {}
    for oid, sku, units in orders:
        last[oid.strip()] = [sku.strip().upper(), units]
    for _, oid, units in returns:
        if oid in last:
            last[oid][1] = max(0, last[oid][1] - units)
    net = defaultdict(int)
    for sku, units in last.values():
        net[sku] += units
    return {k: v for k, v in net.items() if v != 0}


def run(orders, returns):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "orders.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["order_id", "sku", "units"]); w.writerows(orders)
        with open(os.path.join(d, "returns.csv"), "w", newline="") as f:
            w = csv.writer(f); w.writerow(["return_id", "order_id", "units"]); w.writerows(returns)
        out = os.path.join(d, "out.json")
        res = subprocess.run([TOOL, d, out], capture_output=True, text=True, timeout=60)
        assert res.returncode == 0, res.stderr
        return json.load(open(out))


def messy(rng, sku):
    return rng.choice(["", " ", "  "]) + rng.choice([sku, sku.lower()]) + rng.choice(["", " "])


def test_tool_is_executable():
    assert os.access(TOOL, os.X_OK), "/app/reconcile must be executable"


def test_sample_data():
    out = os.path.join(tempfile.mkdtemp(), "o.json")
    subprocess.run([TOOL, os.path.join(APP, "data"), out], check=True, timeout=60)
    assert json.load(open(out)) == {"AB-12": 3, "CD-34": 1}


def test_hidden_random_exports():
    rng = random.Random(int.from_bytes(os.urandom(8), "big"))
    skus = ["AB-12", "CD-34", "EF-56", "GH-78", "IJ-90"]
    for _ in range(5):
        ids = [str(1000 + i) for i in range(rng.randint(5, 40))]
        orders = [(rng.choice(ids), messy(rng, rng.choice(skus)), rng.randint(1, 20))
                  for _ in range(rng.randint(5, 60))]
        returns = [(f"R{i}", rng.choice(ids + ["9999", "0000"]), rng.randint(1, 25))
                   for i in range(rng.randint(0, 30))]
        assert run(orders, returns) == reference(orders, returns)
''')

# ------------------------------------------------------------------ task 4: fix bug, don't touch tests
T = "tasks/rate-limiter-fix"
w(f"{T}/task.toml", task_toml("easy", "debugging", '["python", "debugging", "testing", "outcome-driven"]'))
w(f"{T}/instruction.md", """
# Make the rate limiter's test suite pass

The project in `/app/ratelimiter/` has a failing test suite. Run it with:

    cd /app/ratelimiter && python3 -m pytest -q

Make all the tests pass by fixing the library code. Do not modify, delete or
skip anything in `/app/ratelimiter/tests/`. Your fix will also be checked
against additional tests that you cannot see.
""")
w(f"{T}/environment/Dockerfile", """
FROM ubuntu:24.04
RUN apt-get update && apt-get install -y --no-install-recommends \\
        python3 python3-pytest && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY app/ /app/
""")
w(f"{T}/environment/app/ratelimiter/ratelimiter.py", '''
"""Token-bucket rate limiter."""


class TokenBucket:
    def __init__(self, capacity, refill_per_sec, now=0.0):
        if capacity <= 0 or refill_per_sec < 0:
            raise ValueError("invalid limiter settings")
        self.capacity = capacity
        self.refill_per_sec = refill_per_sec
        self.tokens = capacity
        self.last = now

    def _refill(self, now):
        elapsed = now - self.last
        self.tokens = self.tokens + elapsed * self.refill_per_sec
        self.last = now

    def allow(self, now, cost=1):
        """Return True and spend `cost` tokens if enough are available."""
        self._refill(now)
        if self.tokens > cost:
            self.tokens -= cost
            return True
        return False
''')
w(f"{T}/environment/app/ratelimiter/tests/test_ratelimiter.py", '''
import pytest
from ratelimiter import TokenBucket


def test_starts_full_and_spends_exact_capacity():
    b = TokenBucket(capacity=3, refill_per_sec=0)
    assert [b.allow(0) for _ in range(4)] == [True, True, True, False]


def test_refill_never_exceeds_capacity():
    b = TokenBucket(capacity=2, refill_per_sec=1)
    b.allow(0); b.allow(0)
    assert b.allow(100) and b.allow(100)
    assert not b.allow(100)


def test_rejects_bad_settings():
    with pytest.raises(ValueError):
        TokenBucket(capacity=0, refill_per_sec=1)
''')
w(f"{T}/environment/app/ratelimiter/conftest.py", '''
import os, sys
sys.path.insert(0, os.path.dirname(__file__))
''')
w(f"{T}/solution/solve.sh", """
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
""", exe=True)
w(f"{T}/tests/test.sh", TEST_SH, exe=True)
w(f"{T}/tests/test_outputs.py", '''
"""Hidden verifier: visible tests must be untouched and pass, plus extra hidden tests."""
import hashlib, importlib.util, os, subprocess, sys

APP = os.environ.get("APP_DIR", "/app")
PROJ = os.path.join(APP, "ratelimiter")
VISIBLE = os.path.join(PROJ, "tests", "test_ratelimiter.py")
EXPECTED_SHA256 = "__VISIBLE_SHA__"


def load():
    spec = importlib.util.spec_from_file_location("rl", os.path.join(PROJ, "ratelimiter.py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.TokenBucket


def test_visible_tests_untouched():
    assert hashlib.sha256(open(VISIBLE, "rb").read()).hexdigest() == EXPECTED_SHA256


def test_visible_suite_passes():
    res = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", PROJ],
                         capture_output=True, text=True, timeout=120)
    assert res.returncode == 0, res.stdout + res.stderr


def test_hidden_partial_refill_and_cost():
    B = load()
    b = B(capacity=10, refill_per_sec=2)
    assert b.allow(0, cost=10)
    assert not b.allow(1, cost=3)      # only 2 tokens after 1s
    assert b.allow(1.5, cost=3)        # 3 tokens after 1.5s
    assert not b.allow(1.5, cost=1)


def test_hidden_long_idle_caps_at_capacity():
    B = load()
    b = B(capacity=5, refill_per_sec=10)
    b.allow(0, cost=5)
    assert b.allow(1000, cost=5)
    assert not b.allow(1000, cost=1)
''')
# COBOL is fixed-format: code must start in column 8 (dedent removed it above)
_c = os.path.join(ROOT, "tasks/cobol-sales-report-port/environment/app/legacy/salesrpt.cbl")
_src = open(_c).read()
open(_c, "w").write("".join("       " + l if l.strip() else l for l in _src.splitlines(True)))
print("written")
