import base64
import json
import os
from typing import Any, Dict, IO, Iterator, Tuple

import pytest

from altair_savechart._node import NodeSaver


def get_test_cases() -> Iterator[Tuple[str, Dict[str, Any]]]:
    directory = os.path.join(os.path.dirname(__file__), "test_cases")
    cases = set(f.split(".")[0] for f in os.listdir(directory))
    f: IO
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
@pytest.mark.parametrize("fmt", NodeSaver.valid_formats)
def test_selenium_mimebundle(name: str, data: Any, mode: str, fmt: str) -> None:
    if mode == "vega" and fmt in ["vega", "vega-lite"]:
        return
    saver = NodeSaver(data[mode], mode=mode)
    out = saver.mimebundle(fmt).popitem()[1]
    if fmt in ["png", "pdf"]:
        # TODO: can we validate binary output robustly?
        assert isinstance(out, bytes)
    elif fmt == "svg":
        assert isinstance(out, str)
        assert out.startswith("<svg")
    else:
        assert out == data[fmt]
