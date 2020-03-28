import http
import io
import socket
import subprocess
import tempfile
from typing import Any

import pytest
from _pytest.capture import SysCapture

from altair_saver.types import JSONDict
from altair_saver._utils import (
    extract_format,
    fmt_to_mimetype,
    infer_mode_from_spec,
    internet_connected,
    maybe_open,
    mimetype_to_fmt,
    temporary_filename,
    check_output_with_stderr,
)


@pytest.mark.parametrize("connected", [True, False])
def test_internet_connected(monkeypatch, connected: bool) -> None:
    def request(*args: Any, **kwargs: Any) -> None:
        if not connected:
            raise socket.gaierror(0)

    monkeypatch.setattr(http.client.HTTPConnection, "request", request)
    assert internet_connected() is connected


@pytest.mark.parametrize(
    "ext,fmt",
    [
        ("json", "json"),
        ("html", "html"),
        ("png", "png"),
        ("pdf", "pdf"),
        ("svg", "svg"),
        ("vg.json", "vega"),
        ("vl.json", "vega-lite"),
    ],
)
@pytest.mark.parametrize("use_filename", [True, False])
def test_extract_format(ext: str, fmt: str, use_filename: bool) -> None:
    if use_filename:
        filename = f"chart.{ext}"
        assert extract_format(filename) == fmt
    else:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}") as fp:
            assert extract_format(fp) == fmt


def test_extract_format_failure() -> None:
    fp = io.StringIO()
    with pytest.raises(ValueError) as err:
        extract_format(fp)
    assert f"Cannot infer format from {fp}" in str(err.value)


@pytest.mark.parametrize("mode", ["w", "wb"])
def test_maybe_open_filename(mode: str) -> None:
    content_raw = "testing maybe_open with filename\n"
    content = content_raw.encode() if "b" in mode else content_raw

    with temporary_filename() as filename:
        with maybe_open(filename, mode) as f:
            f.write(content)
        with open(filename, "rb" if "b" in mode else "r") as f:
            assert f.read() == content


@pytest.mark.parametrize("mode", ["w", "wb"])
def test_maybe_open_fileobj(mode: str) -> None:
    content_raw = "testing maybe_open with file object\n"
    content = content_raw.encode() if "b" in mode else content_raw

    with tempfile.NamedTemporaryFile(mode + "+") as fp:
        with maybe_open(fp, mode) as f:
            f.write(content)
        fp.seek(0)
        assert fp.read() == content


def test_maybe_open_errors() -> None:
    with pytest.raises(ValueError) as err:
        with maybe_open(io.BytesIO(), "w"):
            pass
    assert "fp is opened in binary mode" in str(err.value)
    assert "mode='w'" in str(err.value)

    with pytest.raises(ValueError) as err:
        with maybe_open(io.StringIO(), "wb"):
            pass
    assert "fp is opened in text mode" in str(err.value)
    assert "mode='wb'" in str(err.value)


@pytest.mark.parametrize(
    "fmt", ["json", "vega-lite", "vega", "html", "pdf", "png", "svg"]
)
def test_fmt_mimetype(fmt: str) -> None:
    mimetype = fmt_to_mimetype(fmt)
    fmt_out = mimetype_to_fmt(mimetype)
    assert fmt == fmt_out


def test_fmt_mimetype_error() -> None:
    with pytest.raises(ValueError) as err:
        fmt_to_mimetype("bad-fmt")
    assert "Unrecognized fmt='bad-fmt'" in str(err.value)

    with pytest.raises(ValueError) as err:
        mimetype_to_fmt("bad-mimetype")
    assert "Unrecognized mimetype='bad-mimetype'" in str(err.value)


@pytest.mark.parametrize(
    "mode, spec",
    [
        ("vega-lite", {"$schema": "https://vega.github.io/schema/vega-lite/v4.json"}),
        ("vega-lite", {"$schema": None, "data": {}, "mark": {}, "encodings": {}}),
        ("vega-lite", {"data": {}, "mark": {}, "encodings": {}}),
        ("vega-lite", {}),
        ("vega", {"$schema": "https://vega.github.io/schema/vega/v5.json"}),
        ("vega", {"$schema": None, "data": [], "signals": [], "marks": []}),
        ("vega", {"data": [], "signals": [], "marks": []}),
    ],
)
def test_infer_mode_from_spec(mode: str, spec: JSONDict) -> None:
    assert infer_mode_from_spec(spec) == mode


@pytest.mark.parametrize("cmd_error", [True, False])
@pytest.mark.parametrize("use_filter", [True, False])
def test_check_output_with_stderr(
    capsys: SysCapture, use_filter: bool, cmd_error: bool
) -> None:
    cmd = r'>&2 echo "first error\nsecond error" && echo "the output"'
    stderr_filter = None if not use_filter else lambda line: line.startswith("second")

    if cmd_error:
        cmd += r" && exit 1"
        with pytest.raises(subprocess.CalledProcessError) as err:
            check_output_with_stderr(cmd, shell=True, stderr_filter=stderr_filter)
        assert err.value.stderr == b"first error\nsecond error\n"
    else:
        output = check_output_with_stderr(cmd, shell=True, stderr_filter=stderr_filter)
        assert output == b"the output\n"

    captured = capsys.readouterr()
    assert captured.out == ""

    if use_filter:
        assert captured.err == "second error\n"
    else:
        assert captured.err == "first error\nsecond error\n"
