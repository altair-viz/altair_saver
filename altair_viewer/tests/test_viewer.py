import re
from typing import Any, Dict, Iterable, List, Tuple
import webbrowser

import altair as alt
from IPython import display
import pytest
from tornado.httpclient import HTTPClient

from altair_viewer import ChartViewer
import altair_viewer._viewer


CDN_URL = "https://cdn.jsdelivr.net/npm/"


class Mock:
    calls: List[Tuple[Tuple[Any, ...], Dict[str, Any]]]

    def __init__(self, return_value=None):
        self.calls = []
        self.return_value = return_value

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append((args, kwargs))
        return self.return_value


@pytest.fixture
def http_client() -> HTTPClient:
    return HTTPClient()


@pytest.fixture
def chart() -> alt.Chart:
    return alt.Chart("data.csv").mark_point().encode(x="x:Q")


@pytest.fixture(scope="module")
def viewers() -> Iterable[Dict[bool, ChartViewer]]:
    viewers = {
        use_bundled_js: ChartViewer(use_bundled_js=use_bundled_js)
        for use_bundled_js in [True, False]
    }

    for viewer in viewers.values():
        viewer._initialize()

    yield viewers

    for viewer in viewers.values():
        viewer.stop()


@pytest.mark.parametrize("use_bundled_js", [True, False])
def test_chart_viewer_resources(use_bundled_js: bool, viewers: Dict[bool, ChartViewer]):
    viewer = viewers[use_bundled_js]
    if use_bundled_js:
        assert viewer._resources.keys() == {
            "vega",
            "vega-lite",
            "vega-embed",
            "main",
            "favicon.ico",
        }
    else:
        assert viewer._resources.keys() == {
            "main",
            "favicon.ico",
        }


@pytest.mark.parametrize("use_bundled_js", [True, False])
def test_chart_viewer_main_url(use_bundled_js: bool, viewers: Dict[bool, ChartViewer]):
    viewer = viewers[use_bundled_js]
    assert re.match(r"^http://localhost:\d+/$", viewer.url)


@pytest.mark.parametrize("inline", [True, False])
@pytest.mark.parametrize("open_browser", [True, False])
@pytest.mark.parametrize("use_bundled_js", [True, False])
def test_display(
    monkeypatch,
    inline: bool,
    open_browser: bool,
    use_bundled_js: bool,
    chart: alt.Chart,
    viewers: Dict[bool, ChartViewer],
    http_client: HTTPClient,
):
    viewer = viewers[use_bundled_js]
    assert viewer._use_bundled_js == use_bundled_js

    browser_open = Mock()
    monkeypatch.setattr(webbrowser, "open", browser_open)

    ipython_display = Mock()
    monkeypatch.setattr(display, "display", ipython_display)

    stream_send = Mock()
    assert viewer._stream is not None
    monkeypatch.setattr(viewer._stream, "send", stream_send)

    viewer.display(chart, inline=inline, open_browser=open_browser)
    html = http_client.fetch(viewer.url).body.decode()
    if use_bundled_js:
        assert CDN_URL not in html
    else:
        assert CDN_URL in html

    assert len(browser_open.calls) == (1 if open_browser and not inline else 0)
    assert len(ipython_display.calls) == (1 if inline else 0)
    assert len(stream_send.calls) == (0 if inline else 1)


@pytest.mark.parametrize("inline", [True, False])
@pytest.mark.parametrize("open_browser", [True, False])
@pytest.mark.parametrize("use_bundled_js", [True, False])
def test_render(
    monkeypatch,
    inline: bool,
    open_browser: bool,
    use_bundled_js: bool,
    chart: alt.Chart,
    viewers: Dict[bool, ChartViewer],
    http_client: HTTPClient,
):
    viewer = viewers[use_bundled_js]
    assert viewer._use_bundled_js == use_bundled_js

    browser_open = Mock()
    monkeypatch.setattr(webbrowser, "open", browser_open)

    ipython_display = Mock()
    monkeypatch.setattr(display, "display", ipython_display)

    stream_send = Mock()
    assert viewer._stream is not None
    monkeypatch.setattr(viewer._stream, "send", stream_send)

    mimebundle = viewer.render(chart, inline=inline, open_browser=open_browser)
    assert "text/html" in mimebundle

    if inline:
        html = mimebundle["text/html"]
    else:
        html = http_client.fetch(viewer.url).body.decode()

    if use_bundled_js:
        assert CDN_URL not in html
    else:
        assert CDN_URL in html

    assert len(browser_open.calls) == (1 if open_browser and not inline else 0)
    assert len(ipython_display.calls) == 0
    assert len(stream_send.calls) == (0 if inline else 1)


@pytest.mark.parametrize("open_browser", [True, False])
@pytest.mark.parametrize("use_bundled_js", [True, False])
def test_show(
    monkeypatch,
    open_browser: bool,
    use_bundled_js: bool,
    chart: alt.Chart,
    viewers: Dict[bool, ChartViewer],
    http_client: HTTPClient,
):
    viewer = viewers[use_bundled_js]
    assert viewer._use_bundled_js == use_bundled_js

    input_mock = Mock("Q")
    monkeypatch.setattr(altair_viewer._viewer, "input", input_mock, raising=False)

    browser_open = Mock()
    monkeypatch.setattr(webbrowser, "open", browser_open)

    ipython_display = Mock()
    monkeypatch.setattr(display, "display", ipython_display)

    stream_send = Mock()
    assert viewer._stream is not None
    monkeypatch.setattr(viewer._stream, "send", stream_send)

    html = http_client.fetch(viewer.url).body.decode()
    if use_bundled_js:
        assert CDN_URL not in html
    else:
        assert CDN_URL in html

    viewer.show(chart, open_browser=open_browser)
    assert len(browser_open.calls) == (1 if open_browser else 0)
    assert len(ipython_display.calls) == 0
    assert len(stream_send.calls) == 1
    assert len(input_mock.calls) == 1
