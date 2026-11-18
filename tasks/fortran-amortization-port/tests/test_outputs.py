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
    return "".join(l + "\n" for l in out)


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
    return "\n".join(rows) + "\n"


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
    text = "1000 0 3\n999.99 12 1\n"
    assert run(text) == reference(text)


def test_hidden_random_loans():
    rng = random.Random(int.from_bytes(os.urandom(8), "big"))
    for _ in range(5):
        text = random_loans(rng, 6)
        assert run(text) == reference(text)
