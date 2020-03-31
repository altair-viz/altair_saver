import io
import json
import os
from typing import Any, Dict, IO, Iterator, Tuple

import altair as alt
import pandas as pd
import pytest
from PIL import Image
from selenium.common.exceptions import WebDriverException
from _pytest.monkeypatch import MonkeyPatch

from altair_saver import SeleniumSaver, JavascriptError
from altair_saver.types import JSONDict
from altair_saver._utils import fmt_to_mimetype, internet_connected
from altair_saver.savers.tests._utils import SVGImage


@pytest.fixture(scope="module")
def internet_ok() -> bool:
    return internet_connected()


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


@pytest.fixture
def spec() -> JSONDict:
    data = pd.DataFrame({"x": range(10), "y": range(10)})
    return alt.Chart(data).mark_line().encode(x="x", y="y").to_dict()


def get_modes_and_formats() -> Iterator[Tuple[str, str]]:
    for mode in ["vega", "vega-lite"]:
        for fmt in SeleniumSaver.valid_formats[mode]:
            yield (mode, fmt)


@pytest.mark.parametrize("name,data", get_testcases())
@pytest.mark.parametrize("mode, fmt", get_modes_and_formats())
@pytest.mark.parametrize("offline", [True, False])
def test_selenium_mimebundle(
    name: str,
    data: Dict[str, Any],
    mode: str,
    fmt: str,
    offline: bool,
    internet_ok: bool,
) -> None:
    if not (offline or internet_ok):
        pytest.xfail("Internet not available")
    saver = SeleniumSaver(data[mode], mode=mode, offline=offline)
    if mode == "vega" and fmt == "vega-lite":
        with pytest.raises(ValueError):
            saver.mimebundle(fmt)
        return
    mimetype, out = saver.mimebundle(fmt).popitem()
    assert mimetype == fmt_to_mimetype(fmt)
    if fmt == "png":
        assert isinstance(out, bytes)
        im = Image.open(io.BytesIO(out))
        assert im.format == "PNG"

        im_expected = Image.open(io.BytesIO(data[fmt]))
        assert abs(im.size[0] - im_expected.size[0]) < 5
        assert abs(im.size[1] - im_expected.size[1]) < 5
    elif fmt == "svg":
        assert out == data[fmt]
    else:
        assert out == data[fmt]


@pytest.mark.parametrize("name,data", get_testcases())
def test_stop_and_start(name: str, data: Dict[str, Any]) -> None:
    saver = SeleniumSaver(data["vega-lite"])
    bundle1 = saver.mimebundle("png")

    saver._stop_serving()
    assert saver._provider is None

    bundle2 = saver.mimebundle("png")
    assert bundle1 == bundle2


@pytest.mark.parametrize("enabled", [True, False])
def test_enabled(monkeypatch: MonkeyPatch, enabled: bool) -> None:
    monkeypatch.setattr(
        SeleniumSaver, "_select_webdriver", lambda d: object() if enabled else None
    )
    assert SeleniumSaver.enabled() is enabled


@pytest.mark.parametrize("webdriver", ["chrome", "firefox"])
def test_select_webdriver(monkeypatch: MonkeyPatch, webdriver: str) -> None:
    def get(driver: str, driver_timeout: int) -> str:
        if driver == webdriver:
            return driver
        else:
            raise WebDriverException(driver)

    monkeypatch.setattr(SeleniumSaver._registry, "get", get)
    assert SeleniumSaver._select_webdriver(20) == webdriver


def test_extract_error() -> None:
    saver = SeleniumSaver({})
    with pytest.raises(JavascriptError) as err:
        saver._extract("png")
    assert "Invalid specification" in str(err.value)

    saver = SeleniumSaver({}, mode="vega")
    with pytest.raises(JavascriptError) as err:
        saver._extract("xxx")
    assert "Unrecognized format" in str(err.value)


@pytest.mark.parametrize("fmt", ["png", "svg"])
@pytest.mark.parametrize(
    "kwds",
    [
        {"scale_factor": 2},
        {"embed_options": {"scaleFactor": 2}},
        {"scale_factor": 3, "embed_options": {"scaleFactor": 2}},
    ],
)
def test_scale_factor(spec: JSONDict, fmt: str, kwds: Dict[str, Any]) -> None:
    saver1 = SeleniumSaver(spec)
    out1 = saver1.save(fmt=fmt)

    saver2 = SeleniumSaver(spec, **kwds)
    out2 = saver2.save(fmt=fmt)

    if fmt == "png":
        assert isinstance(out1, bytes)
        im1 = Image.open(io.BytesIO(out1))
        assert im1.format == "PNG"

        assert isinstance(out2, bytes)
        im2 = Image.open(io.BytesIO(out2))
        assert im2.format == "PNG"

        assert im2.size[0] == 2 * im1.size[0]
        assert im2.size[1] == 2 * im1.size[1]
    else:
        assert isinstance(out1, str)
        im1 = SVGImage(out1)

        assert isinstance(out2, str)
        im2 = SVGImage(out2)

        assert im2.width == 2 * im1.width
        assert im2.height == 2 * im1.height
