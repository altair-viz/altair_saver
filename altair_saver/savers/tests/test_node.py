import io
import json
import os
from typing import Any, Dict, IO, Iterator, List, Optional, Tuple

from PIL import Image
from PyPDF2 import PdfFileReader
import pytest
from _pytest.capture import SysCapture
from _pytest.monkeypatch import MonkeyPatch

from altair_saver import NodeSaver
from altair_saver._utils import fmt_to_mimetype
from altair_saver.savers import _node
from altair_saver.savers.tests._utils import SVGImage
from altair_saver.types import JSONDict


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


@pytest.fixture
def interactive_spec() -> JSONDict:
    return {
        "data": {"values": [{"x": 1, "y": 1}]},
        "mark": "point",
        "encoding": {
            "x": {"field": "x", "type": "quantitative"},
            "y": {"field": "y", "type": "quantitative"},
        },
        "selection": {"zoon": {"type": "interval", "bind": "scales"}},
    }


def get_modes_and_formats() -> Iterator[Tuple[str, str]]:
    for mode in ["vega", "vega-lite"]:
        for fmt in NodeSaver.valid_formats[mode]:
            yield (mode, fmt)


@pytest.mark.parametrize("name,data", get_testcases())
@pytest.mark.parametrize("mode,fmt", get_modes_and_formats())
@pytest.mark.parametrize("vega_cli_options", [None, ["--loglevel", "error"]])
def test_node_mimebundle(
    name: str, data: Any, mode: str, fmt: str, vega_cli_options: Optional[List[str]]
) -> None:
    saver = NodeSaver(data[mode], mode=mode, vega_cli_options=vega_cli_options)
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
        im = SVGImage(out)
        im_expected = SVGImage(data[fmt])
        assert abs(im.width - im_expected.width) < 5
        assert abs(im.height - im_expected.height) < 5
    else:
        assert out == data[fmt]


@pytest.mark.parametrize("name,data", get_testcases())
def test_node_mimebundle_fail(name: str, data: Any) -> None:
    fmt = "vega-lite"
    mode = "vega"
    saver = NodeSaver(data[mode], mode=mode)
    with pytest.raises(ValueError):
        saver.mimebundle(fmt)


@pytest.mark.parametrize("enabled", [True, False])
def test_enabled(monkeypatch: MonkeyPatch, enabled: bool) -> None:
    def exec_path(name: str) -> str:
        if enabled:
            return name
        else:
            raise _node.ExecutableNotFound(name)

    monkeypatch.setattr(_node, "exec_path", exec_path)
    assert NodeSaver.enabled() is enabled


@pytest.mark.parametrize("suppress_warnings", [True, False])
def test_stderr_suppression(
    interactive_spec: JSONDict, suppress_warnings: bool, capsys: SysCapture,
) -> None:
    message = "WARN Can not resolve event source: window"

    # Window resolve warnings are suppressed by default.
    if suppress_warnings:
        saver = NodeSaver(interactive_spec)
    else:
        saver = NodeSaver(interactive_spec, stderr_filter=None)

    saver.save(fmt="png")
    captured = capsys.readouterr()

    if suppress_warnings:
        assert message not in captured.err
    else:
        assert message in captured.err
