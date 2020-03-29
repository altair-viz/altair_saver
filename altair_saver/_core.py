from collections import OrderedDict
from typing import Any, Dict, IO, Iterable, Optional, Set, Type, Union
import warnings

import altair as alt

from altair_saver.savers import (
    Saver,
    BasicSaver,
    HTMLSaver,
    NodeSaver,
    SeleniumSaver,
)
from altair_saver.types import JSONDict, Mimebundle
from altair_saver._utils import extract_format, infer_mode_from_spec

_SAVER_METHODS: Dict[str, Type[Saver]] = OrderedDict(
    [
        ("basic", BasicSaver),
        ("html", HTMLSaver),
        ("selenium", SeleniumSaver),
        ("node", NodeSaver),
    ]
)


def _select_saver(
    method: Optional[Union[str, Type[Saver]]],
    mode: str,
    fmt: Optional[str] = None,
    fp: Optional[Union[IO, str]] = None,
) -> Type[Saver]:
    """Get an enabled Saver class that supports the specified format.

    Parameters
    ----------
    method : string or Saver class or None
        The saver class to use. If None, the saver class will be chosen
        automatically.
    mode : string
        One of "vega" or "vega-lite".
    fmt : string, optional
        The format to which the spec will be saved. If not specified, it
        is inferred from `fp`.
    fp : string or file-like object, optional
        Only referenced if fmt is None. The name is used to infer the format
        if possible.

    Returns
    -------
    Saver : Saver class
        The Saver subclass that implements the desired operation.
    """
    if isinstance(method, type) and issubclass(method, Saver):
        return method
    elif isinstance(method, str):
        if method in _SAVER_METHODS:
            return _SAVER_METHODS[method]
        else:
            raise ValueError(f"Unrecognized method: {method!r}")
    elif method is None:
        if fmt is None:
            if fp is None:
                raise ValueError("Either fmt or fp must be specified")
            fmt = extract_format(fp)
        for s in _SAVER_METHODS.values():
            if s.enabled() and fmt in s.valid_formats[mode]:
                return s
        raise ValueError(f"No enabled saver found that supports format={fmt!r}")
    else:
        raise ValueError(f"Unrecognized method: {method}")


def save(
    chart: Union[alt.TopLevelMixin, JSONDict],
    fp: Optional[Union[IO, str]] = None,
    fmt: Optional[str] = None,
    mode: Optional[str] = None,
    embed_options: Optional[JSONDict] = None,
    method: Optional[Union[str, Type[Saver]]] = None,
    suppress_data_warning: bool = False,
    **kwargs: Any,
) -> Optional[Union[str, bytes]]:
    """Save an Altair, Vega, or Vega-Lite chart

    Parameters
    ----------
    chart : alt.Chart or dict
        The chart or Vega/Vega-Lite chart specification to be saved
    fp : file or filename (optional)
        location to save the result. For fmt in ["png", "pdf"], file must be binary.
        For fmt in ["svg", "vega", "vega-lite"], file must be text. If not specified,
        the serialized chart will be returned.
    fmt : string (optional)
        The format in which to save the chart. If not specified and fp is a string,
        fmt will be determined from the file extension. Options are
        ["html", "pdf", "png", "svg", "vega", "vega-lite"].
    mode : string (optional)
        The mode of the input spec. Either "vega-lite" or "vega". If not specified,
        it will be inferred from the spec.
    method : string or type
        The save method to use: one of {"node", "selenium", "html", "basic"},
        or a subclass of Saver.
    suppress_data_warning : bool (optional)
        If True, suppress warning about json & csv data transformers.
    **kwargs :
        Additional keyword arguments are passed to Saver initialization.

    Additional Parameters
    ---------------------
    embed_options : dict
        For method in {"seleinum", "html"}, a dictionary of options to pass to vega-embed.
        If not specified, the default will be drawn from alt.renderers.options.
    vega_version : string
        For method in {"selenium", "html"}, the version of the vega javascript
        package to use. Default is alt.VEGA_VERSION.
    vegalite_version : string
        For method in {"selenium", "html"}, the version of the vega-lite javascript
        package to use. Default is alt.VEGALITE_VERSION.
    vegaembed_version : string
        For method in {"selenium", "html"}, the version of the vega-embed javascript
        package to use. Default is alt.VEGAEMBED_VERSION.
    vega_cli_options : list
        For method="node", a list of additional arguments to pass to vega's CLI functions.
        All options will be passed to all Vega commands (e.g., `vg2svg`, `vg2pdf`, etc.).
    stderr_filter : function(str)->bool
        For method="node", a function that allows filtering lines of stderr output. It is
        called on each line of stderr, and the line is shown if the function returns True.
    inline : boolean
        For method="html", specify whether javascript sources should be included
        inline rather than loaded from an external CDN. Default: False.
    standalone : boolean
        For method="html", specify whether to create a standalone HTML file.
        Default is True for save().
    webdriver : string or WebDriver
        For method="selenium", the type of webdriver to use: one of "chrome", "firefox",
        or a selenium.WebDriver object. Defaults to what is available on your system.
    offline : bool
        For method="selenium", whether to save charts in offline mode (default=True). If
        false, saving charts will require a web connection to load Javascript from CDN.
    scale_factor : integer
        For method="selenium", scale saved image by this factor (default=1). This parameter
        value is overridden by embed_options["scaleFactor"] when both are specified.

    Returns
    -------
    chart : string, bytes, or None
        If fp is None, the serialized chart is returned.
        If fp is specified, the return value is None.
    """
    spec: JSONDict = {}
    if isinstance(chart, dict):
        spec = chart
    else:
        if alt.data_transformers.get() in [alt.data.to_json, alt.data.to_csv]:
            warnings.warn(
                f"save() may not function properly with the {alt.data_transformers.active!r} "
                "data transformer: use alt.data_transformers.enable('default'). To "
                "suppress this warning, pass suppress_data_warning=True."
            )
        spec = chart.to_dict()

    if mode is None:
        mode = infer_mode_from_spec(spec)

    if embed_options is None:
        embed_options = alt.renderers.options.get("embed_options", None)

    Saver = _select_saver(method, mode=mode, fmt=fmt, fp=fp)
    saver = Saver(spec, mode=mode, embed_options=embed_options, **kwargs)

    return saver.save(fp=fp, fmt=fmt)


def render(
    chart: Union[alt.TopLevelMixin, JSONDict],
    fmts: Union[str, Iterable[str]],
    mode: Optional[str] = None,
    embed_options: Optional[JSONDict] = None,
    method: Optional[Union[str, Type[Saver]]] = None,
    **kwargs: Any,
) -> Mimebundle:
    """Render a chart, returning a mimebundle.

    This implements an Altair renderer entry-point, enabled via::

        alt.renderers.enable("altair_saver")

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
    method : string or type
        The save method to use: one of {"node", "selenium", "html", "basic"},
        or a subclass of Saver.
    **kwargs :
        Additional keyword arguments are passed to Saver initialization.

    Additional Parameters
    ---------------------
    embed_options : dict
        For method in {"seleinum", "html"}, a dictionary of options to pass to vega-embed.
        If not specified, the default will be drawn from alt.renderers.options.
    vega_version : string
        For method in {"selenium", "html"}, the version of the vega javascript
        package to use. Default is alt.VEGA_VERSION.
    vegalite_version : string
        For method in {"selenium", "html"}, the version of the vega-lite javascript
        package to use. Default is alt.VEGALITE_VERSION.
    vegaembed_version : string
        For method in {"selenium", "html"}, the version of the vega-embed javascript
        package to use. Default is alt.VEGAEMBED_VERSION.
    vega_cli_options : list
        For method="node", a list of additional arguments to pass to vega's CLI functions.
        All options will be passed to all Vega commands (e.g., `vg2svg`, `vg2pdf`, etc.).
    stderr_filter : function(str)->bool
        For method="node", a function that allows filtering lines of stderr output. It is
        called on each line of stderr, and the line is shown if the function returns True.
    inline : boolean
        For method="html", specify whether javascript sources should be included
        inline rather than loaded from an external CDN. Default: False.
    standalone : boolean
        For method="html", specify whether to create a standalone HTML file.
        Default is False for render().
    webdriver : string or WebDriver
        For method="selenium", the type of webdriver to use: one of "chrome", "firefox",
        or a selenium.WebDriver object. Defaults to what is available on your system.
    offline : bool
        For method="selenium", whether to save charts in offline mode (default=True). If
        false, saving charts will require a web connection to load Javascript from CDN.
    """
    if isinstance(fmts, str):
        fmts = [fmts]
    mimebundle: Mimebundle = {}

    spec: JSONDict = {}
    if isinstance(chart, dict):
        spec = chart
    else:
        spec = chart.to_dict()

    if mode is None:
        mode = infer_mode_from_spec(spec)

    if embed_options is None:
        embed_options = alt.renderers.options.get("embed_options", None)

    for fmt in fmts:
        Saver = _select_saver(method, mode=mode, fmt=fmt)
        saver = Saver(spec, mode=mode, embed_options=embed_options, **kwargs)
        mimebundle.update(saver.mimebundle(fmt))

    return mimebundle


def available_formats(mode: str = "vega-lite") -> Set[str]:
    """Return the set of available formats.

    Parameters
    ----------
    mode : str
        The kind of input; one of "vega", "vega-lite"

    Returns
    -------
    formats : set of strings
        Formats available in the current session.
    """
    valid_modes = ("vega", "vega-lite")
    if mode not in valid_modes:
        raise ValueError(f"Invalid mode: {mode!r}. Must be one of {valid_modes!r}")
    return set.union(
        *(set(s.valid_formats[mode]) for s in _SAVER_METHODS.values() if s.enabled())
    )
