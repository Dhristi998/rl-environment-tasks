#!/usr/bin/env python3
"""Validate every task without Docker.

For each task it runs two agents and checks the verifier's reward:
  - null agent   : does nothing                -> reward must be 0
  - oracle agent : runs solution/solve.sh       -> reward must be 1
  - shortcut agent: a cheat in scripts/shortcut_agents/ (hard-codes the sample
                   answer or edits the tests)   -> reward must be 0
For the legacy-port tasks it also compiles the original Fortran / COBOL program
and checks that the reference answer really matches the legacy output
(needs gfortran and cobc on PATH; skipped with a note if they are missing).
"""
import os, random, shutil, subprocess, sys, tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TASKS = os.path.join(ROOT, "tasks")


def run_agent(task_dir, agent):
    with tempfile.TemporaryDirectory() as tmp:
        app, logs = os.path.join(tmp, "app"), os.path.join(tmp, "logs")
        shutil.copytree(os.path.join(task_dir, "environment", "app"), app)
        env = dict(os.environ, APP_DIR=app, LOG_DIR=logs, TESTS_DIR=os.path.join(task_dir, "tests"))
        if agent == "oracle":
            subprocess.run(["bash", os.path.join(task_dir, "solution", "solve.sh")], env=env, check=True)
        if agent == "shortcut":
            subprocess.run(["bash", os.path.join(ROOT, "scripts", "shortcut_agents", os.path.basename(task_dir) + ".sh")],
                           env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["bash", os.path.join(task_dir, "tests", "test.sh")], env=env,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return open(os.path.join(logs, "reward.txt")).read().strip()


def check_fortran(task_dir, rng):
    if not shutil.which("gfortran"):
        return "skipped (gfortran not installed)"
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "amortize")
        subprocess.run(["gfortran", "-O0", "-o", exe, os.path.join(task_dir, "environment/app/legacy/amortize.f")], check=True)
        app = os.path.join(tmp, "app"); os.makedirs(app)
        subprocess.run(["bash", os.path.join(task_dir, "solution/solve.sh")], env=dict(os.environ, APP_DIR=app), check=True)
        for _ in range(200):
            rows = [f"{round(rng.uniform(100, 500000), 2)} {rng.choice([0, round(rng.uniform(0.5, 24), 2)])} {rng.randint(1, 360)}" for _ in range(3)]
            text = "\n".join(rows) + "\n"
            legacy = subprocess.run([exe], input=text, capture_output=True, text=True).stdout
            port = subprocess.run([sys.executable, os.path.join(app, "amortize.py")], input=text, capture_output=True, text=True).stdout
            if legacy != port:
                return "MISMATCH on input:\n" + text
    return "matches legacy Fortran on 200 random inputs"


def check_cobol(task_dir, rng):
    if not shutil.which("cobc"):
        return "skipped (cobc not installed)"
    with tempfile.TemporaryDirectory() as tmp:
        exe = os.path.join(tmp, "salesrpt")
        subprocess.run(["cobc", "-x", "-o", exe, os.path.join(task_dir, "environment/app/legacy/salesrpt.cbl")], check=True)
        app = os.path.join(tmp, "app"); os.makedirs(app)
        subprocess.run(["bash", os.path.join(task_dir, "solution/solve.sh")], env=dict(os.environ, APP_DIR=app), check=True)
        regions = ["NORTH", "SOUTH", "EAST ", "WEST ", "APAC "]
        for _ in range(200):
            recs = [(rng.choice(regions), rng.randint(0, 999999999)) for _ in range(rng.randint(1, 50))]
            with open(os.path.join(tmp, "sales.dat"), "w") as f:
                f.writelines(r + str(c).zfill(9) + "\n" for r, c in recs)
            legacy = subprocess.run([exe], cwd=tmp, capture_output=True, text=True).stdout
            port = subprocess.run([sys.executable, os.path.join(app, "salesrpt.py")], cwd=tmp, capture_output=True, text=True).stdout
            if legacy != port:
                return "MISMATCH\nlegacy:\n" + legacy + "\nport:\n" + port
    return "matches legacy COBOL on 200 random inputs"


def main():
    ok = True
    rng = random.Random(7)
    for name in sorted(os.listdir(TASKS)):
        d = os.path.join(TASKS, name)
        null, oracle, cheat = run_agent(d, "null"), run_agent(d, "oracle"), run_agent(d, "shortcut")
        good = null == "0" and oracle == "1" and cheat == "0"
        ok &= good
        print(f"{'PASS' if good else 'FAIL'}  {name:32s} null={null}  oracle={oracle}  shortcut={cheat}")
        if name.startswith("fortran"):
            print("      legacy check:", check_fortran(d, rng))
        if name.startswith("cobol"):
            print("      legacy check:", check_cobol(d, rng))
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
