"""An HTML altair saver"""
import json
from typing import Any, Dict, List, Optional
import uuid
import warnings

import altair as alt
from altair_viewer import get_bundled_script

from altair_saver.types import JSONDict, MimebundleContent
from altair_saver.savers import Saver

# This is the basic HTML template for embedding charts on a page.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <script src="{vega_url}"></script>
  <script src="{vegalite_url}"></script>
  <script src="{vegaembed_url}"></script>
</head>
<body>
<div class="vega-visualization" id="{output_div}"></div>
<script type="text/javascript">
  const spec = {spec};
  const embedOpt = {embed_options};
  vegaEmbed('#{output_div}', spec, embedOpt).catch(console.error);
</script>
</body>
</html>
"""

# This is like the basic template, but includes vega javascript inline
# so that the resulting file is not dependent on external resources.
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
<div class="vega-visualization" id="{output_div}"></div>
<script type="text/javascript">
  const spec = {spec};
  const embedOpt = {embed_options};
  vegaEmbed('#{output_div}', spec, embedOpt).catch(console.error);
</script>
</body>
</html>
"""

# This is the HTML template that should be used in render(), because it
# will display properly in a variety of notebook environments. It is
# modeled off of Altair's default HTML display.
RENDERER_HTML_TEMPLATE = """
<div class="vega-visualization" id="{output_div}"></div>
<script type="text/javascript">
  (function(spec, embedOpt) {{
    let outputDiv = document.currentScript.previousElementSibling;
    if (outputDiv.id !== "{output_div}") {{
      outputDiv = document.getElementById("{output_div}");
    }}
    const paths = {{
      "vega": "{vega_url}?noext",
      "vega-lite": "{vegalite_url}?noext",
      "vega-embed": "{vegaembed_url}?noext",
    }};
    function loadScript(lib) {{
      return new Promise(function(resolve, reject) {{
        var s = document.createElement('script');
        s.src = paths[lib];
        s.async = true;
        s.onload = () => resolve(paths[lib]);
        s.onerror = () => reject(`Error loading script: ${{paths[lib]}}`);
        document.getElementsByTagName("head")[0].appendChild(s);
      }});
    }}
    function showError(err) {{
      outputDiv.innerHTML = `<div class="error" style="color:red;">${{err}}</div>`;
      throw err;
    }}
    function displayChart(vegaEmbed) {{
      vegaEmbed(outputDiv, spec, embedOpt)
        .catch(err => showError(`Javascript Error: ${{err.message}}<br>This usually means there's a typo in your chart specification. See the javascript console for the full traceback.`));
    }}
    if (typeof define === "function" && define.amd) {{
      requirejs.config({{paths}});
      require(["vega-embed"], displayChart, err => showError(`Error loading script: ${{err.message}}`));
    }} else if (typeof vegaEmbed === "function") {{
      displayChart(vegaEmbed);
    }} else {{
      loadScript("vega")
        .then(() => loadScript("vega-lite"))
        .then(() => loadScript("vega-embed"))
        .catch(showError)
        .then(() => displayChart(vegaEmbed));
    }}
  }})({spec}, {embed_options});
</script>
"""


CDN_URL = "https://cdn.jsdelivr.net/npm/{package}@{version}"


class HTMLSaver(Saver):
    """Basic chart output."""

    valid_formats: Dict[str, List[str]] = {"vega": ["html"], "vega-lite": ["html"]}
    _inline: bool
    _standalone: Optional[bool]

    def __init__(
        self,
        spec: JSONDict,
        mode: Optional[str] = None,
        embed_options: Optional[JSONDict] = None,
        vega_version: str = alt.VEGA_VERSION,
        vegalite_version: str = alt.VEGALITE_VERSION,
        vegaembed_version: str = alt.VEGAEMBED_VERSION,
        inline: bool = False,
        standalone: Optional[bool] = None,
        **kwargs: Any,
    ) -> None:
        self._inline = inline
        self._standalone = standalone
        super().__init__(
            spec=spec,
            mode=mode,
            embed_options=embed_options,
            vega_version=vega_version,
            vegalite_version=vegalite_version,
            vegaembed_version=vegaembed_version,
            **kwargs,
        )

    def _package_url(self, package: str) -> str:
        return CDN_URL.format(package=package, version=self._package_versions[package])

    def _serialize(self, fmt: str, content_type: str) -> MimebundleContent:
        standalone = self._standalone
        if standalone is None:
            standalone = content_type == "save"

        output_div = f"vega-visualization-{uuid.uuid4().hex}"

        if not standalone:
            if self._inline:
                warnings.warn("inline ignored for non-standalone HTML.")
            return RENDERER_HTML_TEMPLATE.format(
                spec=json.dumps(self._spec),
                embed_options=json.dumps(self._embed_options),
                vega_url=self._package_url("vega"),
                vegalite_url=self._package_url("vega-lite"),
                vegaembed_url=self._package_url("vega-embed"),
                output_div=output_div,
            )
        elif self._inline:
            return INLINE_HTML_TEMPLATE.format(
                spec=json.dumps(self._spec),
                embed_options=json.dumps(self._embed_options),
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
                output_div=output_div,
            )
        else:
            return HTML_TEMPLATE.format(
                spec=json.dumps(self._spec),
                embed_options=json.dumps(self._embed_options),
                vega_url=self._package_url("vega"),
                vegalite_url=self._package_url("vega-lite"),
                vegaembed_url=self._package_url("vega-embed"),
                output_div=output_div,
            )
