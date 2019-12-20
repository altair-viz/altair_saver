from typing import Any, Dict, IO, Union

import altair as alt

from altair_savechart._selenium import SeleniumSaver
from altair_savechart._node import NodeSaver

SpecType = Dict[str, Any]

METHOD_DICT: Dict[str, type] = {"selenium": SeleniumSaver, "node": NodeSaver}


def save(
    chart: Union[alt.TopLevelMixin, SpecType],
    fp: Union[IO, str],
    fmt: str = None,
    mode: str = "vega_lite",
    method: Union[str, type] = "selenium",
    **kwargs,
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
    Saver: type
    if isinstance(method, type):
        Saver = method
    elif isinstance(method, str) and method in METHOD_DICT:
        Saver = METHOD_DICT[method]
    else:
        raise ValueError(f"unrecognized method: {method}")

    spec: SpecType = {}
    if isinstance(chart, dict):
        spec = chart
    else:
        spec = chart.to_dict()
    saver = Saver(spec, **kwargs)

    saver.save(fp=fp, fmt=fmt)
