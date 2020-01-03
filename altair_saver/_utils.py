import contextlib
import io
import os
import tempfile
from typing import Any, Dict, IO, Iterator, List, Optional, Union

import altair as alt

MimeType = Union[str, bytes, dict]
Mimebundle = Dict[str, MimeType]
JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSON]


def fmt_to_mimetype(
    fmt,
    vegalite_version: str = alt.VEGALITE_VERSION,
    vega_version: str = alt.VEGA_VERSION,
) -> str:
    """Get a mimetype given a format string."""
    if fmt == "vega-lite":
        return "application/vnd.vegalite.v{}+json".format(
            vegalite_version.split(".")[0]
        )
    elif fmt == "vega":
        return "application/vnd.vega.v{}+json".format(vega_version.split(".")[0])
    elif fmt == "pdf":
        return "application/pdf"
    elif fmt == "html":
        return "text/html"
    elif fmt == "png":
        return "image/png"
    elif fmt == "svg":
        return "image/svg+xml"
    else:
        raise ValueError(f"Unrecognized fmt={fmt!r}")


def mimetype_to_fmt(mimetype: str) -> str:
    """Get a format string given a mimetype."""
    if mimetype.startswith("application/vnd.vegalite"):
        return "vega-lite"
    elif mimetype.startswith("application/vnd.vega"):
        return "vega"
    elif mimetype == "application/pdf":
        return "pdf"
    elif mimetype == "text/html":
        return "html"
    elif mimetype == "image/png":
        return "png"
    elif mimetype == "image/svg+xml":
        return "svg"
    else:
        raise ValueError(f"Unrecognized mimetype={mimetype!r}")


@contextlib.contextmanager
def temporary_filename(**kwargs: Any) -> Iterator[str]:
    """Create and clean-up a temporary file

    Arguments are the same as those passed to tempfile.mkstemp

    We could use tempfile.NamedTemporaryFile here, but that causes issues on
    windows (see https://bugs.python.org/issue14243).
    """
    filedescriptor, filename = tempfile.mkstemp(**kwargs)
    os.close(filedescriptor)

    try:
        yield filename
    finally:
        if os.path.exists(filename):
            os.remove(filename)


@contextlib.contextmanager
def maybe_open(fp: Union[IO, str], mode: str = "w") -> Iterator[IO]:
    """Write to string or file-like object"""
    if isinstance(fp, str):
        with open(fp, mode) as f:
            yield f
    elif isinstance(fp, io.TextIOBase) and "b" in mode:
        raise ValueError("File expected to be opened in binary mode.")
    elif isinstance(fp, io.BufferedIOBase) and "b" not in mode:
        raise ValueError("File expected to be opened in text mode")
    else:
        yield fp


def extract_format(fp: Union[IO, str]) -> str:
    """Extract the output format from a file or filename."""
    filename: Optional[str]
    if isinstance(fp, str):
        filename = fp
    else:
        filename = getattr(fp, "name", None)
    if filename is None:
        raise ValueError(f"Cannot infer format from {fp}")
    if filename.endswith(".vg.json"):
        return "vega"
    elif filename.endswith(".json"):
        return "vega-lite"
    else:
        return filename.split(".")[-1]
