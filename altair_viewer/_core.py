import json
import pkgutil
from typing import Dict, Optional, Union
import webbrowser

import altair as alt
from altair_data_server import Provider, Resource
from altair_viewer._scripts import _get_script
from altair_viewer._event_provider import EventProvider, DataSource


HTML = """
<html>
  <head>
    <title>Altair Viewer</title>
    <script src="{vega_url}"></script>
    <script src="{vegalite_url}"></script>
    <script src="{vegaembed_url}"></script>
    <style>
    div.altair-chart {{
      position: absolute;
      left: 50%;
      top: 50%;
      transform: translate(-50%, -50%);
    }}
    </style>
  </head>
  <body>
    <div id="{output_div}" class="altair-chart"></div>
    <script type="text/javascript">
        
        function showSpec(spec, embedOpt) {{
            const el = document.getElementById("{output_div}");
            vegaEmbed(el, spec, embedOpt)
                .catch(error => {{
                    el.innerHTML = ('<div class="error" style="color:red;">'
                                    + '<p>JavaScript Error: ' + error.message + '</p>'
                                    + "<p>This usually means there's a typo in your chart specification. "
                                    + "See the javascript console for the full traceback.</p>"
                                    + '</div>');
                    throw error;
                }});
        }}

        var eventSource = new EventSource("/stream/spec");

        eventSource.onmessage = function(event) {{
            console.log("message:", event);
            console.log("data:", event.data);
            var data = JSON.parse(event.data);
            console.log(data["spec"])
            console.log(data["embedOpt"])
            showSpec(data["spec"], data["embedOpt"])
        }};

        eventSource.onerror = function(event) {{
            console.log("error:", event)
        }};

        eventSource.onopen = function() {{
            console.log("open:", event)
        }};
    </script>
  </body>
</html>
"""


class ChartViewer:
    _provider: Optional[Provider] = None
    _resources: Dict[str, Resource] = {}
    _stream: Optional[DataSource] = None

    def init_provider(self) -> None:
        # TODO: - allow specification of vega/vega-lite versions
        #       - allow serving resources from CDN
        if self._provider is None:
            self._provider = EventProvider()
            for package in ["vega", "vega-lite", "vega-embed"]:
                self._resources[package] = self._provider.create(
                    content=_get_script(package), route=f"scripts/{package}.js"
                )
            favicon = pkgutil.get_data("altair_viewer", "static/favicon.ico")
            if favicon is not None:
                self._resources["favicon.ico"] = self._provider.create(
                    content=favicon, route="favicon.ico"
                )
            self._resources["main"] = self._provider.create(
                content=HTML.format(
                    vega_url=self._resources["vega"].url,
                    vegalite_url=self._resources["vega-lite"].url,
                    vegaembed_url=self._resources["vega-embed"].url,
                    output_div="altair-chart",
                ),
                route="index.html",
            )
            self._stream = self._provider.create_stream("spec")

    @property
    def url(self):
        if "main" not in self._resources:
            self.init_provider()
        return self._resources["main"].url

    def display(
        self,
        chart: Union[dict, alt.TopLevelMixin],
        embed_opt: Optional[dict] = None,
        open_browser: bool = True,
    ) -> str:
        if isinstance(chart, alt.TopLevelMixin):
            chart = chart.to_dict()
        self.init_provider()
        if self._stream is None:
            raise RuntimeError("Internal: _stream is not defined.")
        self._stream.send(json.dumps({"spec": chart, "embedOpt": embed_opt or {}}))
        if open_browser:
            webbrowser.open(self.url)
        return f"Displaying chart at {self.url}"

    def render(
        self, chart: Union[dict, alt.TopLevelMixin], embed_opt: Optional[dict] = None,
    ) -> Dict[str, str]:
        msg = self.display(chart, embed_opt)
        return {
            "text/plain": msg,
            "text/html": f"Displaying chart at <a href='{self.url}'>{self.url}</a>",
        }