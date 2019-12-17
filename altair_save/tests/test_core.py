import base64
import json
import os

import pytest

from altair_save.core import SeleniumSaver


def get_test_cases():
    directory = os.path.join(os.path.dirname(__file__), "test_cases")
    cases = set(f.split(".")[0] for f in os.listdir(directory))
    for case in sorted(cases):
        with open(os.path.join(directory, f"{case}.vl.json")) as f:
            vl = json.load(f)
        with open(os.path.join(directory, f"{case}.vg.json")) as f:
            vg = json.load(f)
        with open(os.path.join(directory, f"{case}.svg")) as f:
            svg = f.read()
        with open(os.path.join(directory, f"{case}.png"), "rb") as f:
            png_bytes = f.read()
            png = "data:image/png;base64,{}".format(
                base64.b64encode(png_bytes).decode()
            )
        yield case, {"vega-lite": vl, "vega": vg, "svg": svg, "png": png}


@pytest.mark.parametrize("name,data", get_test_cases())
@pytest.mark.parametrize("mode", ["vega", "vega-lite"])
@pytest.mark.parametrize("fmt", ["png", "svg", "vega", "vega-lite"])
def test_selenium_mimebundle(name, data, mode, fmt):
    if mode == "vega" and fmt in ["vega", "vega-lite"]:
        return
    saver = SeleniumSaver(data[mode], mode=mode)
    out = saver.mimebundle([fmt])
    out = out.popitem()[1]
    if fmt == "png":
        # TODO: can we validate png output robustly?
        assert isinstance(out, bytes)
    elif fmt == "svg":
        assert out == data[fmt]
    else:
        assert out == data[fmt]
