import io

import altair as alt
import pandas as pd
import pytest

from altair_save import save


@pytest.fixture
def chart():
    data = pd.DataFrame({"x": range(10), "y": range(10)})
    return alt.Chart(data).mark_line().encode(x="x", y="y")


@pytest.fixture
def spec(chart):
    return chart.to_dict()


@pytest.mark.parametrize("fmt", ["png", "svg", "vega", "vega-lite"])
def test_save_chart(chart, fmt):
    if fmt == "png":
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(chart, fp, fmt=fmt)


@pytest.mark.parametrize("fmt", ["png", "svg", "vega", "vega-lite"])
def test_save_spec(spec, fmt):
    if fmt == "png":
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(spec, fp, fmt=fmt)
