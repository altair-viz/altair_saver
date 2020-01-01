import io
from typing import IO, List, Union, Type

import altair as alt
import pandas as pd
import pytest

from altair_savechart import save
from altair_savechart._basic import BasicSaver
from altair_savechart._html import HTMLSaver
from altair_savechart._node import NodeSaver
from altair_savechart._saver import Saver
from altair_savechart._selenium import SeleniumSaver
from altair_savechart._utils import JSONDict

FORMATS = ["html", "pdf", "png", "svg", "vega", "vega-lite"]


@pytest.fixture
def chart() -> alt.Chart:
    data = pd.DataFrame({"x": range(10), "y": range(10)})
    return alt.Chart(data).mark_line().encode(x="x", y="y")


@pytest.fixture
def spec(chart: alt.Chart) -> JSONDict:
    return chart.to_dict()


@pytest.mark.parametrize("fmt", FORMATS)
def test_save_chart(chart: alt.TopLevelMixin, fmt: str) -> None:
    fp: IO
    if fmt in ["png", "pdf"]:
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(chart, fp, fmt=fmt)


@pytest.mark.parametrize("fmt", FORMATS)
def test_save_spec(spec: JSONDict, fmt: str) -> None:
    fp: IO
    if fmt in ["png", "pdf"]:
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(spec, fp, fmt=fmt)


@pytest.mark.parametrize("method", ["node", "selenium", BasicSaver, HTMLSaver])
@pytest.mark.parametrize("fmt", FORMATS)
def test_save_chart_method(
    spec: JSONDict, fmt: str, method: Union[str, Type[Saver]]
) -> None:
    fp: IO
    if fmt in ["png", "pdf"]:
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    valid_formats: List[str] = []
    if method == "node":
        valid_formats = NodeSaver.valid_formats
    elif method == "selenium":
        valid_formats = SeleniumSaver.valid_formats
    elif isinstance(method, type):
        valid_formats = method.valid_formats
    else:
        raise ValueError(f"unrecognized method: {method}")

    if fmt not in valid_formats:
        with pytest.raises(ValueError):
            save(spec, fp, fmt=fmt, method=method)
    else:
        save(spec, fp, fmt=fmt, method=method)


@pytest.mark.parametrize("inline", [True, False])
def test_html_inline(spec: JSONDict, inline: bool) -> None:
    fp = io.StringIO()
    save(spec, fp, fmt="html", inline=inline)
    html = fp.getvalue()

    cdn_url = "https://cdn.jsdelivr.net"
    if inline:
        assert cdn_url not in html
    else:
        assert cdn_url in html
