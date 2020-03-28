import contextlib
from http import client
import io
import os
import socket
import subprocess
import sys
import tempfile
from typing import Callable, IO, Iterator, List, Optional, Union

import altair as alt

from altair_saver.types import JSONDict


def internet_connected(test_url: str = "cdn.jsdelivr.net") -> bool:
    """Return True if web connection is available."""
    conn = client.HTTPConnection(test_url, timeout=5)
    try:
        conn.request("HEAD", "/")
    except socket.gaierror:
        return False
    else:
        return True
    finally:
        conn.close()


def fmt_to_mimetype(
    fmt: str,
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
    elif fmt == "json":
        return "application/json"
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
    elif mimetype == "application/json":
        return "json"
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


def infer_mode_from_spec(spec: JSONDict) -> str:
    """Given a spec, return the inferred mode.

    This uses the '$schema' value if present, and otherwise tries to
    infer the type based on top-level keys. If both approaches fail,
    it returns "vega-lite" by default.

    Parameters
    ----------
    spec : dict
        The vega or vega-lite specification

    Returns
    -------
    mode : str
        Either "vega" or "vega-lite"
    """
    if "$schema" in spec:
        schema = spec["$schema"]
        if not isinstance(schema, str):
            pass
        elif "/vega-lite/" in schema:
            return "vega-lite"
        elif "/vega/" in schema:
            return "vega"

    # Check several vega-only top-level properties.
    for key in ["axes", "legends", "marks", "projections", "scales", "signals"]:
        if key in spec:
            return "vega"

    return "vega-lite"


@contextlib.contextmanager
def temporary_filename(
    suffix: Optional[str] = None,
    prefix: Optional[str] = None,
    dir: Optional[str] = None,
    text: bool = False,
) -> Iterator[str]:
    """Create and clean-up a temporary file

    Arguments are passed directly to tempfile.mkstemp()

    We could use tempfile.NamedTemporaryFile here, but that causes issues on
    windows (see https://bugs.python.org/issue14243).
    """
    filedescriptor, filename = tempfile.mkstemp(
        suffix=suffix, prefix=prefix, dir=dir, text=text
    )
    os.close(filedescriptor)

    try:
        yield filename
    finally:
        if os.path.exists(filename):
            os.remove(filename)


@contextlib.contextmanager
def maybe_open(fp: Union[IO, str], mode: str = "w") -> Iterator[IO]:
    """Context manager to write to a file specified by filename or file-like object"""
    if isinstance(fp, str):
        with open(fp, mode) as f:
            yield f
    elif isinstance(fp, io.TextIOBase) and "b" in mode:
        raise ValueError(
            f"fp is opened in text mode; mode={mode!r} requires binary mode."
        )
    elif isinstance(fp, io.BufferedIOBase) and "b" not in mode:
        raise ValueError(
            f"fp is opened in binary mode; mode={mode!r} requires text mode."
        )
    else:
        yield fp


def extract_format(fp: Union[IO, str]) -> str:
    """Extract the altair_saver output format from a file or filename."""
    filename: Optional[str]
    if isinstance(fp, str):
        filename = fp
    else:
        filename = getattr(fp, "name", None)
    if filename is None:
        raise ValueError(f"Cannot infer format from {fp}")
    if filename.endswith(".vg.json"):
        return "vega"
    elif filename.endswith(".vl.json"):
        return "vega-lite"
    else:
        return filename.split(".")[-1]


def check_output_with_stderr(
    cmd: Union[str, List[str]],
    shell: bool = False,
    input: Optional[bytes] = None,
    stderr_filter: Callable[[str], bool] = None,
) -> bytes:
    """Run a command in a subprocess, printing stderr to sys.stderr.

    This function exists because normally, stderr from subprocess in the notebook
    is printed to the terminal rather than to the notebook itself.

    Parameters
    ----------
    cmd, shell, input :
        Arguments are passed directly to `subprocess.run()`.
    stderr_filter : function(str)->bool (optional)
        If provided, this function is used to filter stderr lines from display.

    Returns
    -------
    result : bytes
        The stdout from the command

    Raises
    ------
    subprocess.CalledProcessError : if the called process returns a non-zero exit code.
    """
    try:
        ps = subprocess.run(
            cmd,
            shell=shell,
            input=input,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as err:
        stderr = err.stderr
        raise
    else:
        stderr = ps.stderr
        return ps.stdout
    finally:
        s = stderr.decode()
        if stderr_filter:
            s = "\n".join(filter(stderr_filter, s.splitlines()))
        if s:
            if not s.endswith("\n"):
                s += "\n"
            sys.stderr.write(s)
            sys.stderr.flush()
