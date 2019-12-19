import abc
import contextlib
import json
from typing import Dict, IO, Iterable, Iterator, Union


MimeType = Union[str, bytes, dict]
Mimebundle = Dict[str, MimeType]


@contextlib.contextmanager
def maybe_open(fp: Union[IO, str], mode="w") -> Iterator[IO]:
    """Write to string or file-like object"""
    if isinstance(fp, str):
        with open(fp, mode) as f:
            yield f
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

    def save(self, fp: Union[IO, str], fmt: str = None) -> None:
        """Save a chart to file

        Parameters
        ----------
        fp : file or filename
            location to save the result.
        fmt : string
            The format in which to save the chart. If not specified and fp is a string,
            fmt will be determined from the file extension.
        """
        if fmt is None:
            fmt = self._extract_format(fp)
        if fmt not in self.valid_formats:
            raise ValueError(f"Got fmt={fmt}; expected one of {self.valid_formats}")
        if fmt == "vega-lite":
            with maybe_open(fp, "w") as f:
                json.dump(self._spec, f)

        mimebundle = self.mimebundle([fmt])
        if fmt == "png":
            with maybe_open(fp, "wb") as f:
                f.write(mimebundle["image/png"])
        elif fmt == "svg":
            with maybe_open(fp, "w") as f:
                f.write(mimebundle["image/svg+xml"])
        elif fmt == "vega":
            with maybe_open(fp, "w") as f:
                json.dump(mimebundle.popitem()[1], f, indent=2)
        else:
            raise ValueError(f"Unrecognized format: {fmt}")
