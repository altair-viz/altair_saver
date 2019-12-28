import json
import pkgutil
from typing import Dict, Optional, Union
import uuid
import webbrowser

import altair as alt
from altair_data_server import Provider, Resource
from altair_viewer._scripts import get_bundled_script
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
            var data = JSON.parse(event.data);
            console.log(data["spec"]);
            console.log(data["embedOpt"]);
            showSpec(data["spec"], data["embedOpt"]);
        }};

        eventSource.onerror = function(event) {{
            console.log("error:", event);
        }};

        eventSource.onopen = function() {{
            console.log("open:", event);
        }};
    </script>
  </body>
</html>
"""

INLINE_HTML = """
<div id="{output_div}"></div>
<script type="text/javascript">
  (function(spec, embedOpt) {{
    const outputDiv = document.getElementById("{output_div}");
    const paths = {{
      "vega": "{vega_url}",
      "vega-lite": "{vegalite_url}",
      "vega-embed": "{vegaembed_url}",
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

    if(typeof define === "function" && define.amd) {{
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
  }})({spec}, {embedOpt});
</script>
"""


class ChartViewer:
    _provider: Optional[Provider] = None
    _resources: Dict[str, Resource] = {}
    _stream: Optional[DataSource] = None

    def _initialize(self) -> None:
        """Initialize the viewer."""
        # TODO: - allow specification of vega/vega-lite versions
        #       - allow serving resources from CDN
        if self._provider is None:
            self._provider = EventProvider()
            for package in ["vega", "vega-lite", "vega-embed"]:
                self._resources[package] = self._provider.create(
                    content=get_bundled_script(package), route=f"scripts/{package}.js"
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
                route="",
            )
            self._stream = self._provider.create_stream("spec")

    @property
    def url(self) -> str:
        """Return the main chart URL."""
        if "main" not in self._resources:
            self._initialize()
        return self._resources["main"].url

    def _inline_html(
        self, chart: Union[dict, alt.TopLevelMixin], embed_opt: Optional[dict] = None
    ) -> str:
        """Return inline HTML representation of the chart."""
        if isinstance(chart, alt.TopLevelMixin):
            chart = chart.to_dict()
        assert isinstance(chart, dict)
        return INLINE_HTML.format(
            output_div=f"altair-chart-{uuid.uuid4().hex}",
            vega_url=self._resources["vega"].url,
            vegalite_url=self._resources["vega-lite"].url,
            vegaembed_url=self._resources["vega-embed"].url,
            spec=json.dumps(chart),
            embedOpt=json.dumps(embed_opt or {}),
        )

    def display(
        self,
        chart: Union[dict, alt.TopLevelMixin],
        inline: bool = False,
        embed_opt: Optional[dict] = None,
        open_browser: bool = True,
    ) -> None:
        """Display an Altair, Vega-Lite, or Vega chart.

        Parameters
        ----------
        chart : alt.Chart or dict
            The chart or chart specification to display.
        inline : bool
            If False (default) then open a new window to display the chart.
            If True, then display the chart inline in the Jupyter notebook.
        embed_opt : dict (optional)
            The Vega embed options that control the dispay of the chart.
        open_browser : bool (optional)
            If True, then attempt to automatically open a web browser window
            pointing to the displayed chart.

        See Also
        --------
        render : Jupyter renderer for chart.
        show : display a chart and start event loop.
        """
        if isinstance(chart, alt.TopLevelMixin):
            chart = chart.to_dict()
        assert isinstance(chart, dict)
        self._initialize()
        if self._stream is None:
            raise RuntimeError("Internal: _stream is not defined.")
        if inline:
            from IPython import display

            display.display(display.HTML(self._inline_html(chart, embed_opt)))
        else:
            self._stream.send(json.dumps({"spec": chart, "embedOpt": embed_opt or {}}))
        if open_browser and not inline:
            webbrowser.open(self.url)

    def render(
        self,
        chart: Union[dict, alt.TopLevelMixin],
        inline: bool = False,
        embed_opt: Optional[dict] = None,
        open_browser: bool = False,
    ) -> Dict[str, str]:
        """Jupyter renderer for Altair/Vega charts.

        Use this to display a chart within a Jupyter or IPython session.

        Parameters
        ----------
        chart : alt.Chart or dict
            The chart or chart specification to display.
        inline : bool
            If False (default) then open a new browser window with the chart.
            If True, then render the chart inline in the notebook.
        embed_opt : dict (optional)
            The Vega embed options that control the dispay of the chart.
        open_browser : bool (optional)
            If True, then attempt to automatically open a web browser window
            pointing to the displayed chart.

        Returns
        -------
        mimebundle : dict
            Mimebundle dictating what is displayed in IPython/Juputer outputs.

        See Also
        --------
        show : display a chart and start event loop.
        """
        if inline:
            self._initialize()
            return {"text/html": self._inline_html(chart, embed_opt)}
        else:
            self.display(
                chart, embed_opt=embed_opt, open_browser=open_browser, inline=inline
            )
            return {
                "text/plain": f"Displaying chart at {self.url}",
                "text/html": f"Displaying chart at <a href='{self.url}' target='_blank'>{self.url}</a>",
            }

    def show(
        self,
        chart: Union[dict, alt.TopLevelMixin],
        embed_opt: Optional[dict] = None,
        open_browser: bool = True,
    ) -> None:
        """Show chart and start event loop to keep server from closing.

        Use this to show a chart within a stand-alone script, to prevent the Python process
        from ending when the script finishes.

        Parameters
        ----------
        chart : alt.Chart or dict
            The chart or chart specification to display.
        embed_opt : dict (optional)
            The Vega embed options that control the dispay of the chart.
        open_browser : bool (optional)
            If True, then attempt to automatically open a web browser window
            pointing to the displayed chart.

        See Also
        --------
        render : Jupyter renderer for chart.
        """
        self.display(chart, embed_opt=embed_opt, open_browser=open_browser)
        print(f" Displaying chart at {self.url} (Ctrl-C to quit)", end="", flush=True)
        assert self._provider is not None
        try:
            self._provider._server_thread.join()
        except KeyboardInterrupt:
            print("\n Exiting...")
