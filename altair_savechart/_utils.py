import contextlib
import io
from typing import Any, Dict, IO, Iterator, List, Optional, Union

MimeType = Union[str, bytes, dict]
Mimebundle = Dict[str, MimeType]
JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSON]


@contextlib.contextmanager
def _maybe_open(fp: Union[IO, str], mode: str = "w") -> Iterator[IO]:
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


def _extract_format(fp: Union[IO, str]) -> str:
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
