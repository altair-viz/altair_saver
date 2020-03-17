import subprocess
import tempfile

import pytest
from _pytest.capture import SysCaptureBinary

from altair_saver._utils import (
    extract_format,
    fmt_to_mimetype,
    JSONDict,
    infer_mode_from_spec,
    maybe_open,
    mimetype_to_fmt,
    temporary_filename,
    check_output_with_stderr,
)


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


@pytest.mark.parametrize(
    "fmt", ["json", "vega-lite", "vega", "html", "pdf", "png", "svg"]
)
def test_fmt_mimetype(fmt: str) -> None:
    mimetype = fmt_to_mimetype(fmt)
    fmt_out = mimetype_to_fmt(mimetype)
    assert fmt == fmt_out


@pytest.mark.parametrize(
    "mode, spec",
    [
        ("vega-lite", {"$schema": "https://vega.github.io/schema/vega-lite/v4.json"}),
        ("vega-lite", {"data": {}, "mark": {}, "encodings": {}}),
        ("vega-lite", {}),
        ("vega", {"$schema": "https://vega.github.io/schema/vega/v5.json"}),
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
        output = check_output_with_stderr(
            r'>&2 echo "the error" && echo "the output" && exit 1', shell=True
        )
        assert output == b"the output\n"
    assert err.value.stderr == b"the error\n"
    captured = capsysbinary.readouterr()
    assert captured.out == b""
    assert captured.err == b"the error\n"
