import io
import json
import os
from typing import Any, Dict, IO, Iterator, Tuple

from altair_data_server import Provider
from PIL import Image
import pytest
import selenium.webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from altair_saver._utils import internet_connected
from altair_saver.savers import HTMLSaver


@pytest.fixture(scope="module")
def internet_ok():
    return internet_connected()


@pytest.fixture(scope="module")
def provider() -> Iterator[Provider]:
    provider = Provider()
    yield provider
    provider.stop()


@pytest.fixture(scope="module")
def driver() -> Iterator[WebDriver]:
    options = selenium.webdriver.chrome.options.Options()
    options.add_argument("--headless")
    if hasattr(os, "geteuid") and (os.geteuid() == 0):
        options.add_argument("--no-sandbox")
    driver = selenium.webdriver.Chrome(options=options)
    yield driver
    driver.quit()


def get_testcases() -> Iterator[Tuple[str, Dict[str, Any]]]:
    directory = os.path.join(os.path.dirname(__file__), "testcases")
    cases = set(f.split(".")[0] for f in os.listdir(directory))
    f: IO
    for case in sorted(cases):
        with open(os.path.join(directory, f"{case}.vl.json")) as f:
            vl = json.load(f)
        with open(os.path.join(directory, f"{case}.png"), "rb") as f:
            png = f.read()
        yield case, {"vega-lite": vl, "png": png}


@pytest.mark.parametrize("inline", [True, False])
@pytest.mark.parametrize("case, data", get_testcases())
def test_html_saver(case: str, data: Dict[str, Any], inline: bool) -> None:
    saver = HTMLSaver(data["vega-lite"], inline=inline)
    bundle = saver.mimebundle("html")
    html = bundle.popitem()[1]
    assert isinstance(html, str)
    assert html.strip().startswith("<!DOCTYPE html>")
    assert json.dumps(data["vega-lite"]) in html


def test_bad_format() -> None:
    saver = HTMLSaver({})
    with pytest.raises(ValueError):
        saver.mimebundle("vega")


@pytest.mark.parametrize("case, data", get_testcases())
@pytest.mark.parametrize("inline", [True, False])
def test_html_rendering(
    provider: Provider,
    driver: WebDriver,
    case: str,
    data: Dict[str, Any],
    inline: bool,
    internet_ok: bool,
) -> None:
    if not (inline or internet_ok):
        pytest.xfail("Internet connection not available")
    saver = HTMLSaver(data["vega-lite"], inline=inline)
    bundle = saver.mimebundle("html")
    html = bundle.popitem()[1]
    assert isinstance(html, str)

    cdn_url = "https://cdn.jsdelivr.net"
    if inline:
        assert cdn_url not in html
    else:
        assert cdn_url in html

    resource = provider.create(content=html, extension="html")
    driver.set_window_size(800, 600)
    driver.get(resource.url)
    element = driver.find_element_by_id("vis")

    png = driver.get_screenshot_as_png()
    im = Image.open(io.BytesIO(png))
    left = element.location["x"]
    top = element.location["y"]
    right = element.location["x"] + element.size["width"]
    bottom = element.location["y"] + element.size["height"]
    im = im.crop((left, top, right, bottom))

    im_expected = Image.open(io.BytesIO(data["png"]))
    assert abs(im.size[0] - im_expected.size[0]) < 40
    assert abs(im.size[1] - im_expected.size[1]) < 40
    #
