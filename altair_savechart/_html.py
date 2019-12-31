"""An HTML altair saver"""
import json
from typing import List, Dict
import altair as alt
from altair_savechart._saver import Saver, Mimebundle

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <script src="{vega_url}"></script>
  <script src="{vegalite_url}"></script>
  <script src="{vegaembed_url}"></script>
</head>
<body>
<div id="vis"></div>
<script type="text/javascript">
  const spec = {spec};
  const embedOpt = {embed_opt};
  vegaEmbed('#vis', spec, embedOpt).catch(console.error);
</script>
</body>
</html>
"""

CDN_URL = "https://cdn.jsdelivr.net/npm/{package}@{version}"


class HTMLSaver(Saver):
    """Basic chart output."""

    valid_formats: List[str] = ["html"]
    _package_versions: Dict[str, str] = {
        "vega": alt.VEGA_VERSION,
        "vega-lite": alt.VEGALITE_VERSION,
        "vega-embed": alt.VEGAEMBED_VERSION,
    }

    def _package_url(self, package: str, inline: bool = False) -> str:
        if inline:
            raise NotImplementedError("inline mode")
        else:
            return CDN_URL.format(
                package=package, version=self._package_versions[package]
            )

    def _mimebundle(self, fmt: str) -> Mimebundle:
        if fmt not in self.valid_formats:
            raise ValueError(
                f"Invalid format: {fmt!r}. Must be one of {self.valid_formats}"
            )
        return {
            "text/html": HTML_TEMPLATE.format(
                spec=json.dumps(self._spec),
                embed_opt="{}",
                vega_url=self._package_url("vega"),
                vegalite_url=self._package_url("vega-lite"),
                vegaembed_url=self._package_url("vega-embed"),
            )
        }
