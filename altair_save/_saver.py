import abc
import contextlib
import json
from typing import Dict, IO, Iterable, Iterator, Union


@contextlib.contextmanager
def maybe_open(fp: Union[IO, str], mode="w") -> Iterator[IO]:
    """Write to string or file-like object"""
    if isinstance(fp, str):
        with open(fp, mode) as f:
            yield f
    else:
        yield fp


class Saver(metaclass=abc.ABCMeta):
    valid_formats = ["png", "svg", "vega", "vega-lite"]

    def __init__(self, spec: dict, mode: str = "vega-lite"):
        # TODO: extract mode from spec $schema if not specified.
        self._spec = spec
        self._mode = mode

    @abc.abstractmethod
    def _mimebundle(self, fmt: str) -> Dict[str, Union[str, bytes, dict]]:
        pass

    @staticmethod
    def _extract_format(filename: str) -> str:
        """Extract the output format from a filename."""
        if filename.endswith(".vg.json"):
            return "vega"
        if filename.endswith(".json"):
            return "vega-lite"
        else:
            return filename.split(".")[-1]

    def mimebundle(self, fmt: Iterable[str]) -> Dict[str, Union[str, bytes, dict]]:
        bundle = {}
        for f in fmt:
            bundle.update(self._mimebundle(f))
        return bundle

    def save(self, fp: Union[IO, str], fmt: str = None) -> None:
        """Save a chart to file"""
        if fmt is None and isinstance(fp, str):
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
            with maybe_open(fp, "wb") as f:
                f.write(mimebundle["image/svg+xml"])
        elif fmt == "vega":
            with maybe_open(fp, "w") as f:
                json.dump(mimebundle.popitem()[1], f, indent=2)
        else:
            raise ValueError(f"Unrecognized format: {fmt}")
