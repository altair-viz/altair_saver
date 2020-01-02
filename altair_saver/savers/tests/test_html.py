import json
import os
from typing import Any, Dict, Iterator, Tuple

from altair_data_server import Provider
import pytest
import selenium.webdriver
from selenium.webdriver.remote.webdriver import WebDriver

from altair_saver.savers import HTMLSaver


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
    for case in sorted(cases):
        with open(os.path.join(directory, f"{case}.vl.json")) as f:
            spec = json.load(f)
        yield case, spec


@pytest.mark.parametrize("inline", [True, False])
@pytest.mark.parametrize("case, spec", get_testcases())
def test_html_saver(case: str, spec: Dict[str, Any], inline: bool) -> None:
    saver = HTMLSaver(spec, inline=inline)
    bundle = saver.mimebundle("html")
    html = bundle.popitem()[1]
    assert isinstance(html, str)
    assert html.strip().startswith("<!DOCTYPE html>")
    assert json.dumps(spec) in html


def test_bad_format() -> None:
    saver = HTMLSaver({})
    with pytest.raises(ValueError):
        saver.mimebundle("vega")


@pytest.mark.parametrize("inline", [True, False])
@pytest.mark.parametrize("case, spec", get_testcases())
def test_html_rendering(
    provider: Provider, driver: WebDriver, case: str, spec: Dict[str, Any], inline: bool
) -> None:
    saver = HTMLSaver(spec, inline=inline)
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

    # non-zero element size indicates a chart was rendered.
    assert element.size["height"] > 0
    assert element.size["width"] > 0

    # TODO: is element size stable enough to compare exact values?
    # TODO: compare screenshot directly?
    # png = driver.get_screenshot_as_png()
