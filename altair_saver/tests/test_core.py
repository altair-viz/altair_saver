import io
import json
from typing import List, Union, Type

import altair as alt
import pandas as pd
import pytest

from altair_saver import (
    save,
    render,
    BasicSaver,
    HTMLSaver,
    NodeSaver,
    Saver,
    SeleniumSaver,
)
from altair_saver._utils import JSONDict, mimetype_to_fmt

FORMATS = ["html", "pdf", "png", "svg", "vega", "vega-lite"]


def check_output(out: Union[str, bytes], fmt: str) -> None:
    """Do basic checks on output to confirm correct type, and non-empty."""
    if fmt in ["png", "pdf"]:
        assert isinstance(out, bytes)
    elif fmt in ["vega", "vega-lite"]:
        assert isinstance(out, str)
        dct = json.loads(out)
        assert len(dct) > 0
    else:
        assert isinstance(out, str)
    assert len(out) > 0


@pytest.fixture
def chart() -> alt.Chart:
    data = pd.DataFrame({"x": range(10), "y": range(10)})
    return alt.Chart(data).mark_line().encode(x="x", y="y")


@pytest.fixture
def spec(chart: alt.Chart) -> JSONDict:
    return chart.to_dict()


@pytest.mark.parametrize("fmt", FORMATS)
def test_save_chart(chart: alt.TopLevelMixin, fmt: str) -> None:
    fp: Union[io.BytesIO, io.StringIO]
    if fmt in ["png", "pdf"]:
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(chart, fp, fmt=fmt)
    check_output(fp.getvalue(), fmt)


@pytest.mark.parametrize("fmt", FORMATS)
def test_save_spec(spec: JSONDict, fmt: str) -> None:
    fp: Union[io.BytesIO, io.StringIO]
    if fmt in ["png", "pdf"]:
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    save(spec, fp, fmt=fmt)
    check_output(fp.getvalue(), fmt)


@pytest.mark.parametrize("method", ["node", "selenium", BasicSaver, HTMLSaver])
@pytest.mark.parametrize("fmt", FORMATS)
def test_save_chart_method(
    spec: JSONDict, fmt: str, method: Union[str, Type[Saver]]
) -> None:
    fp: Union[io.BytesIO, io.StringIO]
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
        check_output(fp.getvalue(), fmt)


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


def test_render_spec(spec: JSONDict) -> None:
    bundle = render(spec, fmts=FORMATS)
    assert len(bundle) == len(FORMATS)
    for mimetype, content in bundle.items():
        fmt = mimetype_to_fmt(mimetype)
        if isinstance(content, dict):
            check_output(json.dumps(content), fmt)
        else:
            check_output(content, fmt)


def test_infer_mode(spec: JSONDict) -> None:
    vg_spec = render(spec, "vega").popitem()[1]
    vl_svg = render(spec, "svg").popitem()[1]
    vg_svg = render(vg_spec, "svg").popitem()[1]
    assert vl_svg == vg_svg
