import json
import os
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from altair_save.core import Saver

test_cases = os.path.join(
    os.path.dirname(__file__), "..", "altair_save", "tests", "test_cases"
)
cases = sorted(set(f.split(".")[0] for f in os.listdir(test_cases)))

for name in sorted(cases):
    with open(os.path.join(test_cases, f"{name}.vl.json")) as f:
        spec = json.load(f)

    saver = Saver(spec)
    saver.save(os.path.join(test_cases, f"{name}.svg"))
    saver.save(os.path.join(test_cases, f"{name}.png"))
    saver.save(os.path.join(test_cases, f"{name}.vg.json"), "vega")
