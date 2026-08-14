import subprocess
import sys

files = [
    "tests/test_health.py",
    "tests/test_phase2.py",
    "tests/test_phase3.py",
    "tests/test_phase4.py",
    "tests/test_phase5.py",
]

for f in files:
    cmd = ["venv\\Scripts\\pytest", f, "-q"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(f"--- {f} ---")
    print(res.stdout)
