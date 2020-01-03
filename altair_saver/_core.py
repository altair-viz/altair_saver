from typing import Any, Dict, IO, Iterable, List, Optional, Type, Union

import altair as alt

from altair_saver.savers import (
    Saver,
    BasicSaver,
    HTMLSaver,
    NodeSaver,
    SeleniumSaver,
)
from altair_saver._utils import extract_format, JSONDict, Mimebundle

METHOD_DICT: Dict[str, type] = {"selenium": SeleniumSaver, "node": NodeSaver}


def _get_saver_for_format(
    fmt: Optional[str] = None, fp: Optional[Union[IO, str]] = None
) -> Type[Saver]:
    """Get an enabled Saver class that supports the specified format."""
    # TODO: allow other savers to be registered.
    if fmt is None:
        if fp is None:
            raise ValueError("Either fmt or fp must be specified")
        fmt = extract_format(fp)
    savers: List[Type[Saver]] = [BasicSaver, HTMLSaver, SeleniumSaver, NodeSaver]
    for s in savers:
        if fmt in s.valid_formats and s.enabled():
            return s
    raise ValueError(f"Unsupported format: {fmt!r}")


def save(
    chart: Union[alt.TopLevelMixin, JSONDict],
    fp: Union[IO, str],
    fmt: Optional[str] = None,
    mode: Optional[str] = None,
    method: Optional[Union[str, type]] = None,
    **kwargs: Any,
) -> None:
    """Save an Altair, Vega, or Vega-Lite chart

    Parameters
    ----------
    chart : alt.Chart or dict
        The chart or Vega/Vega-Lite chart specification to be saved
    fp : file or filename
        location to save the result.
    fmt : string (optinoal)
        The format in which to save the chart. If not specified and fp is a string,
        fmt will be determined from the file extension. Options are
        ["html", "pdf", "png", "svg", "vega", "vega-lite"].
    mode : string (optional)
        The mode of the input spec. Either "vega-lite" or "vega". If not specified,
        it will be inferred from the spec.
    method : string
        The save method to use: either a string, or a subclass of Saver.
    **kwargs :
        Additional keyword arguments are passed to Saver initialization.
    """
    if method is None:
        Saver = _get_saver_for_format(fmt=fmt, fp=fp)
    elif isinstance(method, type):
        Saver = method
    elif isinstance(method, str) and method in METHOD_DICT:
        Saver = METHOD_DICT[method]
    else:
        raise ValueError(f"Unrecognized method: {method}")

    spec: JSONDict = {}
    if isinstance(chart, dict):
        spec = chart
    else:
        spec = chart.to_dict()
    saver = Saver(spec, mode=mode, **kwargs)

    saver.save(fp=fp, fmt=fmt)


def render(
    chart: Union[alt.TopLevelMixin, JSONDict],
    fmts: Union[str, Iterable[str]],
    mode: Optional[str] = None,
    method: Optional[Union[str, type]] = None,
    **kwargs: Any,
) -> Mimebundle:
    """Render a chart, returning a mimebundle.

    Parameters
    ----------
    chart : alt.Chart or dict
        The chart or Vega/Vega-Lite chart specification
    fmts : string or list of strings
        The format(s) to include in the mimebundle. Options are
        ["html", "pdf", "png", "svg", "vega", "vega-lite"].
    mode : string (optional)
        The mode of the input spec. Either "vega-lite" or "vega". If not specified,
        it will be inferred from the spec.
    method : string
        The save method to use: either a string, or a Saver class.
    **kwargs :
        Additional keyword arguments are passed to Saver initialization.
    """

    if isinstance(fmts, str):
        fmts = [fmts]
    mimebundle: Mimebundle = {}

    spec: JSONDict = {}
    if isinstance(chart, dict):
        spec = chart
    else:
        spec = chart.to_dict()

    for fmt in fmts:
        if method is None:
            Saver = _get_saver_for_format(fmt=fmt)
        elif isinstance(method, type):
            Saver = method
        elif isinstance(method, str) and method in METHOD_DICT:
            Saver = METHOD_DICT[method]
        else:
            raise ValueError(f"Unrecognized method: {method}")

        saver = Saver(spec, mode=mode, **kwargs)
        mimebundle.update(saver.mimebundle(fmt))

    return mimebundle
