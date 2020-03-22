import http
import io
import socket
import subprocess
import tempfile

import pytest
from _pytest.capture import SysCaptureBinary

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
    def request(*args, **kwargs):
        if not connected:
            raise socket.gaierror("error")

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


def test_check_output_with_stderr(capsysbinary: SysCaptureBinary):
    output = check_output_with_stderr(
        r'>&2 echo "the error" && echo "the output"', shell=True
    )
    assert output == b"the output\n"
    captured = capsysbinary.readouterr()
    assert captured.out == b""
    assert captured.err == b"the error\n"


def test_check_output_with_stderr_exit_1(capsysbinary: SysCaptureBinary):
    with pytest.raises(subprocess.CalledProcessError) as err:
        check_output_with_stderr(r'>&2 echo "the error" && exit 1', shell=True)
    assert err.value.stderr == b"the error\n"
    captured = capsysbinary.readouterr()
    assert captured.out == b""
    assert captured.err == b"the error\n"
