import re
from typing import Any, Dict, Iterable, List, Tuple
import webbrowser

import altair as alt
from IPython import display
import pytest

from altair_viewer import ChartViewer


class Mock:
    calls: List[Tuple[Tuple[Any, ...], Dict[str, Any]]]

    def __init__(self):
        self.calls = []

    def __call__(self, *args: Any, **kwargs: Any) -> None:
        self.calls.append((args, kwargs))


@pytest.fixture
def chart() -> alt.Chart:
    return alt.Chart("data.csv").mark_point().encode(x="x:Q")


@pytest.fixture(scope="module")
def viewer() -> Iterable[ChartViewer]:
    viewer = ChartViewer()
    viewer._initialize()
    yield viewer
    viewer.stop()


def test_chart_viewer_resources(viewer: ChartViewer):
    assert viewer._resources.keys() == {
        "vega",
        "vega-lite",
        "vega-embed",
        "main",
        "favicon.ico",
    }


def test_chart_viewer_main_url(viewer):
    assert re.match(r"^http://localhost:\d+/$", viewer.url)


@pytest.mark.parametrize("inline", [True, False])
@pytest.mark.parametrize("open_browser", [True, False])
def test_display(
    monkeypatch,
    inline: bool,
    open_browser: bool,
    chart: alt.Chart,
    viewer: ChartViewer,
):
    browser_open = Mock()
    monkeypatch.setattr(webbrowser, "open", browser_open)

    ipython_display = Mock()
    monkeypatch.setattr(display, "display", ipython_display)

    stream_send = Mock()
    assert viewer._stream is not None
    monkeypatch.setattr(viewer._stream, "send", stream_send)

    viewer.display(chart, inline=inline, open_browser=open_browser)
    assert len(browser_open.calls) == (1 if open_browser and not inline else 0)
    assert len(ipython_display.calls) == (1 if inline else 0)
    assert len(stream_send.calls) == (0 if inline else 1)


@pytest.mark.parametrize("inline", [True, False])
@pytest.mark.parametrize("open_browser", [True, False])
def test_render(
    monkeypatch,
    inline: bool,
    open_browser: bool,
    chart: alt.Chart,
    viewer: ChartViewer,
):
    browser_open = Mock()
    monkeypatch.setattr(webbrowser, "open", browser_open)

    ipython_display = Mock()
    monkeypatch.setattr(display, "display", ipython_display)

    stream_send = Mock()
    assert viewer._stream is not None
    monkeypatch.setattr(viewer._stream, "send", stream_send)

    mimebundle = viewer.render(chart, inline=inline, open_browser=open_browser)
    assert "text/html" in mimebundle
    assert len(browser_open.calls) == (1 if open_browser and not inline else 0)
    assert len(ipython_display.calls) == 0
    assert len(stream_send.calls) == (0 if inline else 1)


@pytest.mark.parametrize("open_browser", [True, False])
def test_show(
    monkeypatch, open_browser: bool, chart: alt.Chart, viewer: ChartViewer,
):
    browser_open = Mock()
    monkeypatch.setattr(webbrowser, "open", browser_open)

    ipython_display = Mock()
    monkeypatch.setattr(display, "display", ipython_display)

    stream_send = Mock()
    assert viewer._stream is not None
    monkeypatch.setattr(viewer._stream, "send", stream_send)

    thread_join = Mock()
    assert viewer._provider is not None
    monkeypatch.setattr(viewer._provider._server_thread, "join", thread_join)

    viewer.show(chart, open_browser=open_browser)
    assert len(browser_open.calls) == (1 if open_browser else 0)
    assert len(ipython_display.calls) == 0
    assert len(stream_send.calls) == 1
    assert len(thread_join.calls) == 1
