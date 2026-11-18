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
