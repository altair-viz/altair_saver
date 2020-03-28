import io
import json
from typing import Dict, List, Optional, Union, Type

import altair as alt
import pandas as pd
import pytest

from _pytest.capture import SysCapture
from _pytest.monkeypatch import MonkeyPatch

from altair_saver import (
    available_formats,
    save,
    render,
    BasicSaver,
    HTMLSaver,
    NodeSaver,
    Saver,
    SeleniumSaver,
)
from altair_saver._core import _select_saver
from altair_saver.types import JSONDict
from altair_saver._utils import (
    fmt_to_mimetype,
    mimetype_to_fmt,
    temporary_filename,
)

FORMATS = ["html", "pdf", "png", "svg", "vega", "vega-lite", "json"]


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


@pytest.mark.parametrize(
    "method,saver",
    [
        ("basic", BasicSaver),
        ("html", HTMLSaver),
        ("node", NodeSaver),
        ("selenium", SeleniumSaver),
    ],
)
def test_select_saver_by_method(method: str, saver: Type[Saver]) -> None:
    assert saver is _select_saver(method=method, mode="vega-lite")


@pytest.mark.parametrize(
    "mode, fmt, saver",
    [
        ("vega-lite", "json", BasicSaver),
        ("vega-lite", "vega-lite", BasicSaver),
        ("vega-lite", "html", HTMLSaver),
        ("vega-lite", "png", SeleniumSaver),
        ("vega-lite", "pdf", NodeSaver),
        ("vega", "json", BasicSaver),
        ("vega", "vega", BasicSaver),
        ("vega", "html", HTMLSaver),
        ("vega", "png", SeleniumSaver),
        ("vega", "pdf", NodeSaver),
    ],
)
def test_select_saver_infer_method(
    monkeypatch: MonkeyPatch, mode: str, fmt: str, saver: Type[Saver]
) -> None:
    monkeypatch.setattr(NodeSaver, "enabled", lambda: True)
    monkeypatch.setattr(SeleniumSaver, "enabled", lambda: True)

    assert saver is _select_saver(method=None, mode=mode, fmt=fmt)


@pytest.mark.parametrize(
    "method,fmt,errtext",
    [
        ("badmethod", "png", "Unrecognized method: 'badmethod'"),
        (None, None, "Either fmt or fp must be specified"),
        (None, "jpg", "No enabled saver found that supports format='jpg'"),
        (4, None, "Unrecognized method: 4"),
    ],
)
def test_select_saver_errors(
    method: Optional[str], fmt: Optional[str], errtext: str
) -> None:
    with pytest.raises(ValueError) as err:
        _select_saver(mode="vega-lite", method=method, fmt=fmt)
    assert errtext in str(err.value)


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

    result = save(chart, fp, fmt=fmt)
    assert result is None
    check_output(fp.getvalue(), fmt)


@pytest.mark.parametrize("fmt", FORMATS)
def test_save_spec(spec: JSONDict, fmt: str) -> None:
    fp: Union[io.BytesIO, io.StringIO]
    if fmt in ["png", "pdf"]:
        fp = io.BytesIO()
    else:
        fp = io.StringIO()

    result = save(spec, fp, fmt=fmt)
    assert result is None
    check_output(fp.getvalue(), fmt)


@pytest.mark.parametrize("fmt", FORMATS)
def test_save_return_value(spec: JSONDict, fmt: str) -> None:
    result = save(spec, fmt=fmt)
    assert result is not None
    check_output(result, fmt)


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

    valid_formats: Dict[str, List[str]] = {}
    if method == "node":
        valid_formats = NodeSaver.valid_formats
    elif method == "selenium":
        valid_formats = SeleniumSaver.valid_formats
    elif isinstance(method, type):
        valid_formats = method.valid_formats
    else:
        raise ValueError(f"unrecognized method: {method}")

    if fmt not in valid_formats["vega-lite"]:
        with pytest.raises(ValueError):
            save(spec, fp, fmt=fmt, method=method)
    else:
        save(spec, fp, fmt=fmt, method=method)
        check_output(fp.getvalue(), fmt)


def test_save_chart_data_warning(chart: alt.TopLevelMixin) -> None:
    fp = io.StringIO()
    with alt.data_transformers.enable("json"):
        with pytest.warns(UserWarning) as record:
            save(chart, fp, fmt="html")
    assert len(record) == 1
    assert (
        record[0]
        .message.args[0]
        .startswith("save() may not function properly with the 'json' data transformer")
    )


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


def test_render_chart(chart: alt.TopLevelMixin) -> None:
    bundle = render(chart, fmts=FORMATS)
    assert len(bundle) == len(FORMATS)
    for mimetype, content in bundle.items():
        fmt = mimetype_to_fmt(mimetype)
        if isinstance(content, dict):
            check_output(json.dumps(content), fmt)
        else:
            check_output(content, fmt)


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
    mimetype, vg_spec = render(spec, "vega").popitem()
    assert mimetype == fmt_to_mimetype("vega")

    mimetype, vl_svg = render(spec, "svg").popitem()
    assert mimetype == fmt_to_mimetype("svg")

    mimetype, vg_svg = render(vg_spec, "svg").popitem()
    assert mimetype == fmt_to_mimetype("svg")

    assert vl_svg == vg_svg


@pytest.mark.parametrize("embed_options", [{}, {"padding": 20}])
def test_embed_options_render_html(spec: JSONDict, embed_options: JSONDict) -> None:
    with alt.renderers.set_embed_options(**embed_options):
        mimetype, html = render(spec, "html").popitem()
    assert mimetype == "text/html"
    assert json.dumps(embed_options or {}) in html


@pytest.mark.parametrize("inline", [True, False])
@pytest.mark.parametrize("embed_options", [{}, {"padding": 20}])
def test_embed_options_save_html(
    spec: JSONDict, inline: bool, embed_options: JSONDict
) -> None:
    fp = io.StringIO()
    with alt.renderers.set_embed_options(**embed_options):
        save(spec, fp, "html", inline=inline)
    html = fp.getvalue()
    assert f"const embedOpt = {json.dumps(embed_options or {})};" in html


def test_embed_options_save_html_override(spec: JSONDict) -> None:
    fp = io.StringIO()
    embed_options: JSONDict = {"renderer": "svg"}
    alt_embed_options: JSONDict = {"padding": 20}
    with alt.renderers.set_embed_options(**alt_embed_options):
        save(spec, fp, "html", embed_options=embed_options)
    html = fp.getvalue()
    assert f"const embedOpt = {json.dumps(embed_options)};" in html


@pytest.mark.parametrize("fmt", ["html", "svg"])
@pytest.mark.parametrize("vega_cli_options", [None, ["--loglevel", "debug"]])
def test_save_w_vega_cli_options(
    monkeypatch: MonkeyPatch,
    capsys: SysCapture,
    chart: alt.TopLevelMixin,
    fmt: str,
    vega_cli_options: Optional[List[str]],
) -> None:
    """Tests that `vega_cli_options` works with both NodeSaver and other Savers"""
    monkeypatch.setattr(SeleniumSaver, "enabled", lambda: False)
    result = save(chart, fmt=fmt, vega_cli_options=vega_cli_options)
    assert result is not None
    check_output(result, fmt)

    stderr = capsys.readouterr().err
    if vega_cli_options and fmt == "svg":
        assert "DEBUG" in stderr


@pytest.mark.parametrize("vega_cli_options", [None, ["--loglevel", "debug"]])
def test_render_w_vega_cli_options(
    monkeypatch: MonkeyPatch,
    capsys: SysCapture,
    chart: alt.TopLevelMixin,
    vega_cli_options: Optional[List[str]],
) -> None:
    """Tests that `vega_cli_options` works with both NodeSaver and other Savers"""
    monkeypatch.setattr(NodeSaver, "enabled", lambda: True)
    monkeypatch.setattr(SeleniumSaver, "enabled", lambda: False)
    bundle = render(chart, fmts=["html", "svg"], vega_cli_options=vega_cli_options)
    assert len(bundle) == 2
    for mimetype, content in bundle.items():
        assert content is not None
        fmt = mimetype_to_fmt(mimetype)
        if isinstance(content, dict):
            check_output(json.dumps(content), fmt)
        else:
            check_output(content, fmt)

    stderr = capsys.readouterr().err
    if vega_cli_options:
        assert "DEBUG" in stderr


def test_infer_format(spec: JSONDict) -> None:
    with temporary_filename(suffix=".html") as filename:
        with open(filename, "w") as fp:
            save(spec, fp)
        with open(filename, "r") as fp:
            html = fp.read()
    assert html.strip().startswith("<!DOCTYPE html>")


@pytest.mark.parametrize("mode", ["vega", "vega-lite"])
def test_available_formats(monkeypatch: MonkeyPatch, mode: str) -> None:
    monkeypatch.setattr(NodeSaver, "enabled", lambda: False)
    monkeypatch.setattr(SeleniumSaver, "enabled", lambda: False)
    expected = {mode, "json", "html"}
    assert available_formats(mode) == expected

    monkeypatch.setattr(SeleniumSaver, "enabled", lambda: True)
    expected |= {"vega", "png", "svg"}
    assert available_formats(mode) == expected

    monkeypatch.setattr(NodeSaver, "enabled", lambda: True)
    expected |= {"pdf"}
    assert available_formats(mode) == expected


def test_available_formats_error() -> None:
    message = "Invalid mode: 'bad-mode'. Must be one of ('vega', 'vega-lite')"
    with pytest.raises(ValueError) as err:
        available_formats("bad-mode")
    assert message in str(err.value)
