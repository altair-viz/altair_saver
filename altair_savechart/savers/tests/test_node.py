import io
import json
import os
from typing import Any, Dict, IO, Iterator, Tuple

from PIL import Image
import pytest

from altair_savechart.savers import NodeSaver


def get_testcases() -> Iterator[Tuple[str, Dict[str, Any]]]:
    directory = os.path.join(os.path.dirname(__file__), "testcases")
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
            png = f.read()
        yield case, {"vega-lite": vl, "vega": vg, "svg": svg, "png": png}


@pytest.mark.parametrize("name,data", get_testcases())
@pytest.mark.parametrize("mode", ["vega", "vega-lite"])
@pytest.mark.parametrize("fmt", NodeSaver.valid_formats)
def test_selenium_mimebundle(name: str, data: Any, mode: str, fmt: str) -> None:
    if mode == "vega" and fmt in ["vega", "vega-lite"]:
        return
    saver = NodeSaver(data[mode], mode=mode)
    out = saver.mimebundle(fmt).popitem()[1]
    if fmt == "png":
        assert isinstance(out, bytes)
        im = Image.open(io.BytesIO(out))
        assert im.format == "PNG"

        im_expected = Image.open(io.BytesIO(data[fmt]))
        assert abs(im.size[0] - im_expected.size[0]) < 5
        assert abs(im.size[1] - im_expected.size[1]) < 5
    elif fmt == "pdf":
        # TODO: can we validate binary output robustly?
        assert isinstance(out, bytes)
        assert len(out) > 0
    elif fmt == "svg":
        assert isinstance(out, str)
        assert out.startswith("<svg")
    else:
        assert out == data[fmt]


def test_enabled():
    assert NodeSaver.enabled()
