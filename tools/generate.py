import json
import os
import sys

sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from altair_savechart import save  # noqa: E402

testcases = os.path.join(
    os.path.dirname(__file__), "..", "altair_savechart", "savers", "tests", "testcases"
)
cases = sorted(set(f.split(".")[0] for f in os.listdir(testcases)))

for name in sorted(cases):
    with open(os.path.join(testcases, f"{name}.vl.json")) as f:
        spec = json.load(f)

    for extension in ["svg", "png", "pdf", "vg.json"]:
        save(spec, os.path.join(testcases, f"{name}.{extension}"))
