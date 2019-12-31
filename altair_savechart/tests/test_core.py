import io
from typing import Any, Dict, IO, Union

import altair as alt
import pandas as pd
import pytest

from altair_savechart import save
from altair_savechart._saver import JSONDict


@pytest.fixture
def chart() -> alt.Chart:
    data = pd.DataFrame({"x": range(10), "y": range(10)})
    return alt.Chart(data).mark_line().encode(x="x", y="y")


@pytest.fixture
def spec(chart: alt.Chart) -> Dict[str, Any]:
    return chart.to_dict()


@pytest.mark.parametrize("method", ["node", "selenium"])
@pytest.mark.parametrize("fmt", ["html", "pdf", "png", "svg", "vega", "vega-lite"])
def test_save_chart(
    chart: Union[alt.TopLevelMixin, JSONDict], fmt: str, method: str
) -> None:
    if method == "selenium" and fmt == "pdf":
        return

    fp: IO
    if fmt in ["png", "pdf"]:
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(chart, fp, fmt=fmt, method=method)


@pytest.mark.parametrize("method", ["node", "selenium"])
@pytest.mark.parametrize("fmt", ["html", "pdf", "png", "svg", "vega", "vega-lite"])
def test_save_spec(spec: Dict[str, Any], fmt: str, method: str) -> None:
    if method == "selenium" and fmt == "pdf":
        return

    fp: IO
    if fmt in ["png", "pdf"]:
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(spec, fp, fmt=fmt, method=method)


def test_save_pdf(spec: Dict[str, Any]) -> None:
    fp = io.BytesIO()
    save(spec, fp, fmt="pdf", method="node")
