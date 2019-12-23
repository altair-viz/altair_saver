import json
import pkgutil
from typing import Dict, Optional, Union
import webbrowser

import altair as alt
from altair_data_server import Provider, Resource
from altair_viewer._scripts import _get_script


HTML = """
<html>
  <head>
    <script src="{vega_url}"></script>
    <script src="{vegalite_url}"></script>
    <script src="{vegaembed_url}"></script>
  </head>
  <body>
    <div id="{output_div}"></div>
    <script type="text/javascript">
        var spec = {spec};
        var embedOpt = {embed_options};

        function showError(el, error){{
            el.innerHTML = ('<div class="error" style="color:red;">'
                            + '<p>JavaScript Error: ' + error.message + '</p>'
                            + "<p>This usually means there's a typo in your chart specification. "
                            + "See the javascript console for the full traceback.</p>"
                            + '</div>');
            throw error;
        }}
        const el = document.getElementById("{output_div}");
        vegaEmbed(el, spec, embedOpt)
            .catch(error => showError(el, error));
    </script>
  </body>
</html>
"""


class ChartViewer:
    _counter: int = 0
    _provider: Optional[Provider] = None
    _resources: Dict[str, Resource] = {}

    @classmethod
    def provider(cls) -> Provider:
        if cls._provider is None:
            cls._provider = Provider()
            for package in ["vega", "vega-lite", "vega-embed"]:
                cls._resources[package] = cls._provider.create(
                    content=_get_script(package), route=f"scripts/{package}.js"
                )
            favicon = pkgutil.get_data("altair_viewer", "static/favicon.ico")
            if favicon is not None:
                cls._resources["favicon.ico"] = cls._provider.create(
                    content=favicon, route="favicon.ico"
                )
        return cls._provider

    @classmethod
    def _filename(cls) -> str:
        cls._counter += 1
        return f"chart{cls._counter}.html"

    def display(
        self,
        chart: Union[dict, alt.TopLevelMixin],
        embed_options: Optional[dict] = None,
    ) -> str:
        if isinstance(chart, alt.TopLevelMixin):
            chart = chart.to_dict()
        if embed_options is None:
            embed_options = {}
        provider = self.provider()
        html = HTML.format(
            vega_url=self._resources["vega"].url,
            vegalite_url=self._resources["vega-lite"].url,
            vegaembed_url=self._resources["vega-embed"].url,
            embed_options=json.dumps(embed_options),
            output_div="altair-chart",
            spec=json.dumps(chart),
        )
        filename = self._filename()
        resource = provider.create(content=html, route=filename)
        self._resources[filename] = resource
        webbrowser.open(resource.url)
        return f"Displaying chart at {resource.url}"

    def render(
        self,
        chart: Union[dict, alt.TopLevelMixin],
        embed_options: Optional[dict] = None,
    ) -> Dict[str, str]:
        msg = self.display(chart, embed_options)
        return {"text/plain": msg}
