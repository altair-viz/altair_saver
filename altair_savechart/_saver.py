import abc
import contextlib
import io
import json
from typing import Dict, IO, Iterable, Iterator, Optional, Union


MimeType = Union[str, bytes, dict]
Mimebundle = Dict[str, MimeType]


@contextlib.contextmanager
def _maybe_open(fp: Union[IO, str], mode="w") -> Iterator[IO]:
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


class Saver(metaclass=abc.ABCMeta):
    """
    Base class for saving Altair charts.
    """

    valid_formats = ["png", "svg", "vega", "vega-lite"]

    def __init__(self, spec: dict, mode: str = "vega-lite"):
        # TODO: extract mode from spec $schema if not specified.
        self._spec = spec
        self._mode = mode

    @abc.abstractmethod
    def _mimebundle(self, fmt: str) -> Mimebundle:
        """Return a mimebundle with a single mimetype."""
        pass

    @staticmethod
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

    def mimebundle(self, fmts: Iterable[str]) -> Mimebundle:
        """Return a mimebundle representation of the chart.

        Parameters
        ----------
        fmts : list of strings
            A list of formats to include in the results.

        Returns
        -------
        mimebundle : dict
            The chart's mimebundle representation.
        """
        bundle: Mimebundle = {}
        for fmt in fmts:
            if fmt not in self.valid_formats:
                raise ValueError(
                    f"invalid fmt={fmt!r}; must be one of {self.valid_formats}."
                )
            bundle.update(self._mimebundle(fmt))
        return bundle

    def save(self, fp: Union[IO, str], fmt: Optional[str] = None) -> None:
        """Save a chart to file

        Parameters
        ----------
        fp : file or filename
            Location to save the result. For fmt in ["png", "pdf"], file must be binary.
            For fmt in ["svg", "vega", "vega-lite"], file must be text.
        fmt : string
            The format in which to save the chart. If not specified and fp is a string,
            fmt will be determined from the file extension.
        """
        if fmt is None:
            fmt = self._extract_format(fp)
        if fmt not in self.valid_formats:
            raise ValueError(f"Got fmt={fmt}; expected one of {self.valid_formats}")

        content = self.mimebundle([fmt]).popitem()[1]
        if isinstance(content, dict):
            with _maybe_open(fp, "w") as f:
                json.dump(content, f, indent=2)
        elif isinstance(content, str):
            with _maybe_open(fp, "w") as f:
                f.write(content)
        elif isinstance(content, bytes):
            with _maybe_open(fp, "wb") as f:
                f.write(content)
        else:
            raise ValueError(
                f"Unrecognized content type: {type(content)} for fmt={fmt!r}"
            )
