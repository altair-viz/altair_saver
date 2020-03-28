import abc
import json
from typing import Any, Dict, IO, Iterable, List, Optional, Union

import altair as alt

from altair_saver.types import Mimebundle, MimebundleContent, JSONDict
from altair_saver._utils import (
    extract_format,
    fmt_to_mimetype,
    infer_mode_from_spec,
    maybe_open,
)


class Saver(metaclass=abc.ABCMeta):
    """
    Base class for saving Altair charts.

    Subclasses should:
    - specify the valid_formats class attribute
    - override the _serialize() method
    """

    # list of supported formats, or (mode, format) pairs.
    valid_formats: Dict[str, List[str]] = {"vega": [], "vega-lite": []}
    _spec: JSONDict
    _mode: str
    _embed_options: JSONDict
    _package_versions: Dict[str, str]

    def __init__(
        self,
        spec: JSONDict,
        mode: Optional[str] = None,
        embed_options: Optional[JSONDict] = None,
        vega_version: str = alt.VEGA_VERSION,
        vegalite_version: str = alt.VEGALITE_VERSION,
        vegaembed_version: str = alt.VEGAEMBED_VERSION,
        **kwargs: Any,
    ):
        if mode is None:
            mode = infer_mode_from_spec(spec)
        if mode not in ["vega", "vega-lite"]:
            raise ValueError("mode must be either 'vega' or 'vega-lite'")
        self._spec = spec
        self._mode = mode
        self._embed_options = embed_options or {}
        self._package_versions = {
            "vega": vega_version,
            "vega-lite": vegalite_version,
            "vega-embed": vegaembed_version,
        }

    @abc.abstractmethod
    def _serialize(self, fmt: str, content_type: str) -> MimebundleContent:
        ...

    @classmethod
    def enabled(cls) -> bool:
        """Return true if this saver is enabled on the current system."""
        return True

    def mimebundle(self, fmts: Union[str, Iterable[str]]) -> Mimebundle:
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
        if isinstance(fmts, str):
            fmts = [fmts]
        bundle: Mimebundle = {}
        for fmt in fmts:
            if fmt not in self.valid_formats[self._mode]:
                raise ValueError(
                    f"invalid fmt={fmt!r}; must be one of {self.valid_formats[self._mode]}."
                )
            mimetype = fmt_to_mimetype(
                fmt,
                vega_version=self._package_versions["vega"],
                vegalite_version=self._package_versions["vega-lite"],
            )
            bundle[mimetype] = self._serialize(fmt, "mimebundle")
        return bundle

    def save(
        self, fp: Optional[Union[IO, str]] = None, fmt: Optional[str] = None
    ) -> Optional[Union[str, bytes]]:
        """Save a chart to file

        Parameters
        ----------
        fp : file or filename (optional)
            Location to save the result. For fmt in ["png", "pdf"], file must be binary.
            For fmt in ["svg", "vega", "vega-lite"], file must be text. If not specified,
            the serialized chart will be returned.
        fmt : string (optional)
            The format in which to save the chart. If not specified and fp is a string,
            fmt will be determined from the file extension.

        Returns
        -------
        chart : string, bytes, or None
            If fp is None, the serialized chart is returned.
            If fp is specified, the return value is None.
        """
        if fmt is None:
            if fp is None:
                raise ValueError("Must specify either `fp` or `fmt` when saving chart")
            fmt = extract_format(fp)
        if fmt not in self.valid_formats[self._mode]:
            raise ValueError(f"Got fmt={fmt}; expected one of {self.valid_formats}")

        content = self._serialize(fmt, "save")
        if fp is None:
            if isinstance(content, dict):
                return json.dumps(content)
            return content
        if isinstance(content, dict):
            with maybe_open(fp, "w") as f:
                json.dump(content, f, indent=2)
        elif isinstance(content, str):
            with maybe_open(fp, "w") as f:
                f.write(content)
        elif isinstance(content, bytes):
            with maybe_open(fp, "wb") as f:
                f.write(content)
        else:
            raise ValueError(
                f"Unrecognized content type: {type(content)} for fmt={fmt!r}"
            )
        return None
