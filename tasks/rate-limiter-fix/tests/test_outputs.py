"""Hidden verifier: visible tests must be untouched and pass, plus extra hidden tests."""
import hashlib, importlib.util, os, subprocess, sys

APP = os.environ.get("APP_DIR", "/app")
PROJ = os.path.join(APP, "ratelimiter")
VISIBLE = os.path.join(PROJ, "tests", "test_ratelimiter.py")
EXPECTED_SHA256 = "5bfe2df86bb4523ed0a1bd8648ae815a8cb9b9f3d81f773c145e5eefc0b2b655"


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
