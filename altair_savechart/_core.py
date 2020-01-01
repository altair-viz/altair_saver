from typing import Any, Dict, IO, List, Optional, Type, Union

import altair as alt

from altair_savechart._basic import BasicSaver
from altair_savechart._html import HTMLSaver
from altair_savechart._node import NodeSaver
from altair_savechart._saver import Saver, JSONDict, _extract_format
from altair_savechart._selenium import SeleniumSaver

METHOD_DICT: Dict[str, type] = {"selenium": SeleniumSaver, "node": NodeSaver}


def _get_saver_for_format(fp: Union[IO, str], fmt: Optional[str]) -> Type[Saver]:
    """Get an enabled Saver class that supports the specified format."""
    # TODO: allow other savers to be registered.
    if fmt is None:
        fmt = _extract_format(fp)
    savers: List[Type[Saver]] = [BasicSaver, HTMLSaver, NodeSaver, SeleniumSaver]
    for s in savers:
        if fmt in s.valid_formats and s.enabled():
            return s
    raise ValueError(f"Unsupported format: {fmt!r}")


def save(
    chart: Union[alt.TopLevelMixin, JSONDict],
    fp: Union[IO, str],
    fmt: Optional[str] = None,
    mode: str = "vega_lite",
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
    fmt : string
        The format in which to save the chart. If not specified and fp is a string,
        fmt will be determined from the file extension. Options are
        ["png", "svg", "vega", "vega-lite"]
    mode : string
        The mode of the input spec. Either "vega-lite" (default) or "vega".
    method : string
        The save method to use: either a string, or a subclass of Saver.
    **kwargs :
        Additional keyword arguments are passed to Saver initialization.
    """
    if method is None:
        Saver = _get_saver_for_format(fp, fmt)
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
    saver = Saver(spec, **kwargs)

    saver.save(fp=fp, fmt=fmt)
