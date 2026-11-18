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
    return "\n".join(lines) + "\n"


def run(records):
    with tempfile.TemporaryDirectory() as d:
        with open(os.path.join(d, "sales.dat"), "w") as f:
            for region, cents in records:
                f.write(region + str(cents).zfill(9) + "\n")
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
