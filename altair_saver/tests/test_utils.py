import tempfile

import pytest

from altair_saver._utils import extract_format, maybe_open, temporary_filename


@pytest.mark.parametrize(
    "ext,fmt",
    [
        ("json", "vega-lite"),
        ("html", "html"),
        ("png", "png"),
        ("pdf", "pdf"),
        ("svg", "svg"),
        ("vg.json", "vega"),
        ("vl.json", "vega-lite"),
    ],
)
@pytest.mark.parametrize("use_filename", [True, False])
def testextract_format(ext: str, fmt: str, use_filename: bool) -> None:
    if use_filename:
        filename = f"chart.{ext}"
        assert extract_format(filename) == fmt
    else:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}") as fp:
            assert extract_format(fp) == fmt


@pytest.mark.parametrize("mode", ["w", "wb"])
def testmaybe_open_filename(mode: str) -> None:
    content_raw = "testing maybe_open with filename\n"
    content = content_raw.encode() if "b" in mode else content_raw

    with temporary_filename() as filename:
        with maybe_open(filename, mode) as f:
            f.write(content)
        with open(filename, "rb" if "b" in mode else "r") as f:
            assert f.read() == content


@pytest.mark.parametrize("mode", ["w", "wb"])
def testmaybe_open_fileobj(mode: str) -> None:
    content_raw = "testing maybe_open with file object\n"
    content = content_raw.encode() if "b" in mode else content_raw

    with tempfile.NamedTemporaryFile(mode + "+") as fp:
        with maybe_open(fp, mode) as f:
            f.write(content)
        fp.seek(0)
        assert fp.read() == content
