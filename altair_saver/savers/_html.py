"""An HTML altair saver"""
import json
from typing import Dict, List, Optional
import altair as alt
from altair_saver.savers import Saver
from altair_saver._utils import JSONDict, Mimebundle, fmt_to_mimetype
from altair_viewer import get_bundled_script

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

INLINE_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <script type="text/javascript">
    // vega.js v{vega_version}
    {vega_script}
    // vega-lite.js v{vegalite_version}
    {vegalite_script}
    // vega-embed.js v{vegaembed_version}
    {vegaembed_script}
  </script>
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
    _package_versions: Dict[str, str]
    _inline: bool
    _embed_opt: JSONDict

    def __init__(
        self,
        spec: JSONDict,
        mode: Optional[str] = None,
        inline: bool = False,
        embed_opt: Optional[JSONDict] = None,
        vega_version: str = alt.VEGA_VERSION,
        vegalite_version: str = alt.VEGALITE_VERSION,
        vegaembed_version: str = alt.VEGAEMBED_VERSION,
    ) -> None:
        self._inline = inline
        self._embed_opt = embed_opt or {}
        self._package_versions = {
            "vega": vega_version,
            "vega-lite": vegalite_version,
            "vega-embed": vegaembed_version,
        }
        super().__init__(spec=spec, mode=mode)

    def _package_url(self, package: str) -> str:
        return CDN_URL.format(package=package, version=self._package_versions[package])

    def _mimebundle(self, fmt: str) -> Mimebundle:
        if fmt not in self.valid_formats:
            raise ValueError(
                f"Invalid format: {fmt!r}. Must be one of {self.valid_formats}"
            )
        if self._inline:
            html = INLINE_HTML_TEMPLATE.format(
                spec=json.dumps(self._spec),
                embed_opt=json.dumps(self._embed_opt),
                vega_version=self._package_versions["vega"],
                vegalite_version=self._package_versions["vega-lite"],
                vegaembed_version=self._package_versions["vega-embed"],
                vega_script=get_bundled_script("vega", self._package_versions["vega"]),
                vegalite_script=get_bundled_script(
                    "vega-lite", self._package_versions["vega-lite"]
                ),
                vegaembed_script=get_bundled_script(
                    "vega-embed", self._package_versions["vega-embed"]
                ),
            )
        else:
            html = HTML_TEMPLATE.format(
                spec=json.dumps(self._spec),
                embed_opt=json.dumps(self._embed_opt),
                vega_url=self._package_url("vega"),
                vegalite_url=self._package_url("vega-lite"),
                vegaembed_url=self._package_url("vega-embed"),
            )
        return {fmt_to_mimetype("html"): html}
