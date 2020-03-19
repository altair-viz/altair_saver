import io
import json
import os
from typing import Any, Dict, IO, Iterator, Tuple

from PIL import Image
from PyPDF2 import PdfFileReader
import pytest

from altair_saver.savers import NodeSaver
from altair_saver._utils import fmt_to_mimetype


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
        with open(os.path.join(directory, f"{case}.pdf"), "rb") as f:
            pdf = f.read()
        yield case, {"vega-lite": vl, "vega": vg, "svg": svg, "png": png, "pdf": pdf}


def get_modes_and_formats() -> Iterator[Tuple[str, str]]:
    for mode in ["vega", "vega-lite"]:
        for fmt in NodeSaver.valid_formats[mode]:
            yield (mode, fmt)


@pytest.mark.parametrize("name,data", get_testcases())
@pytest.mark.parametrize("mode, fmt", get_modes_and_formats())
def test_node_mimebundle(name: str, data: Any, mode: str, fmt: str) -> None:
    saver = NodeSaver(data[mode], mode=mode)
    mimetype, out = saver.mimebundle(fmt).popitem()
    assert mimetype == fmt_to_mimetype(fmt)
    if fmt == "png":
        assert isinstance(out, bytes)
        im = Image.open(io.BytesIO(out))
        assert im.format == "PNG"

        im_expected = Image.open(io.BytesIO(data[fmt]))
        assert abs(im.size[0] - im_expected.size[0]) < 5
        assert abs(im.size[1] - im_expected.size[1]) < 5
    elif fmt == "pdf":
        assert isinstance(out, bytes)
        pdf = PdfFileReader(io.BytesIO(out))
        box = pdf.getPage(0).mediaBox
        pdf_expected = PdfFileReader(io.BytesIO(data[fmt]))
        box_expected = pdf_expected.getPage(0).mediaBox

        assert abs(box.getWidth() - box_expected.getWidth()) < 5
        assert abs(box.getHeight() - box_expected.getHeight()) < 5
    elif fmt == "svg":
        assert isinstance(out, str)
        assert out.startswith("<svg")
    else:
        assert out == data[fmt]


@pytest.mark.parametrize("name,data", get_testcases())
def test_node_mimebundle_fail(name: str, data: Any) -> None:
    fmt = "vega-lite"
    mode = "vega"
    saver = NodeSaver(data[mode], mode=mode)
    with pytest.raises(ValueError):
        saver.mimebundle(fmt)


def test_enabled() -> None:
    assert NodeSaver.enabled()
