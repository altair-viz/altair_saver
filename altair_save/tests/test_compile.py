import base64
import json
import os

import pytest

from altair_save.compile import compile_spec
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
@pytest.mark.parametrize("fmt", ["png", "svg", "vega"])
def test_compile(name, data, mode, fmt):
    if mode == "vega" and fmt == "vega":
        return
    out = compile_spec(data[mode], fmt=fmt, mode=mode)

    if fmt == "png":
        assert out.startswith("data:image/png;base64,")
    else:
        assert data[fmt] == out


@pytest.mark.parametrize("name,data", get_test_cases())
def test_selenium_saver(name, data):
    saver = SeleniumSaver(data["vega-lite"])
    out = saver.mimebundle(["svg"])
    assert out.popitem()[1].decode() == data["svg"]
