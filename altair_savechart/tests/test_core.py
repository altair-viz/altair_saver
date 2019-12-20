import io

import altair as alt
import pandas as pd
import pytest

from altair_savechart import save


@pytest.fixture
def chart():
    data = pd.DataFrame({"x": range(10), "y": range(10)})
    return alt.Chart(data).mark_line().encode(x="x", y="y")


@pytest.fixture
def spec(chart):
    return chart.to_dict()


@pytest.mark.parametrize("method", ["node", "selenium"])
@pytest.mark.parametrize("fmt", ["png", "svg", "vega", "vega-lite"])
def test_save_chart(chart, fmt, method):
    if fmt == "png":
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(chart, fp, fmt=fmt, method=method)


@pytest.mark.parametrize("method", ["node", "selenium"])
@pytest.mark.parametrize("fmt", ["png", "svg", "vega", "vega-lite"])
def test_save_spec(spec, fmt, method):
    if fmt == "png":
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(spec, fp, fmt=fmt, method=method)


def test_save_pdf(spec):
    fp = io.BytesIO()
    save(spec, fp, fmt="pdf", method="node")
