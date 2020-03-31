import atexit
import base64
import os
from typing import Any, Dict, List, Optional, Union
import warnings

import altair as alt
from altair_data_server import Provider, Resource
from altair_viewer import get_bundled_script
import selenium.webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException

from altair_saver.types import JSONDict, MimebundleContent
from altair_saver.savers import Saver


class JavascriptError(RuntimeError):
    pass


CDN_URL = "https://cdn.jsdelivr.net/npm/{package}@{version}"

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Embedding Vega-Lite</title>
  <script src="{vega_url}"></script>
  <script src="{vegalite_url}"></script>
  <script src="{vegaembed_url}"></script>
</head>
<body>
  <div id="vis"></div>
</body>
</html>
"""

EXTRACT_CODE = """
let spec = arguments[0];
const embedOpt = arguments[1];
const format = arguments[2];
const done = arguments[3];

if (format === 'vega') {
    if (embedOpt.mode === 'vega-lite') {
        vegaLite = (typeof vegaLite === "undefined") ? vl : vegaLite;
        try {
            const compiled = vegaLite.compile(spec);
            spec = compiled.spec;
        } catch(error) {
            done({error: error.toString()})
        }
    }
    done({result: spec});
}

vegaEmbed('#vis', spec, embedOpt).then(function(result) {
    if (format === 'png') {
        result.view
            .toCanvas(embedOpt.scaleFactor || 1)
            .then(function(canvas){return canvas.toDataURL('image/png');})
            .then(result => done({result}))
            .catch(function(err) {
                console.error(err);
                done({error: err.toString()});
            });
    } else if (format === 'svg') {
        result.view
            .toSVG(embedOpt.scaleFactor || 1)
            .then(result => done({result}))
            .catch(function(err) {
                console.error(err);
                done({error: err.toString()});
            });
    } else {
        const error = "Unrecognized format: " + format;
        console.error(error);
        done({error});
    }
}).catch(function(err) {
    console.error(err);
    done({error: err.toString()});
});
"""


class _DriverRegistry:
    """Registry of web driver singletons.

    This prevents the need to start and stop drivers repeatedly.
    """

    drivers: Dict[str, WebDriver]

    def __init__(self) -> None:
        self.drivers = {}

    def get(self, webdriver: Union[str, WebDriver], driver_timeout: float) -> WebDriver:
        """Get a webdriver by name.

        Parameters
        ----------
        webdriver : string or WebDriver
            The webdriver to use.
        driver_timeout : float
            The per-page driver timeout.

        Returns
        -------
        webdriver : WebDriver
        """
        webdriver = self.drivers.get(webdriver, webdriver)
        if isinstance(webdriver, WebDriver):
            return webdriver

        if webdriver == "chrome":
            webdriver_class = selenium.webdriver.Chrome
            webdriver_options_class = selenium.webdriver.chrome.options.Options
        elif webdriver == "firefox":
            webdriver_class = selenium.webdriver.Firefox
            webdriver_options_class = selenium.webdriver.firefox.options.Options
        else:
            raise ValueError(
                f"Unrecognized webdriver: '{webdriver}'. Expected 'chrome' or 'firefox'"
            )

        webdriver_options = webdriver_options_class()

        # For linux/osx root user with Chrome, need to add --no-sandbox option, which
        # must come before the --headless option. Note: geteuid doesn't exist on windows.
        if (
            issubclass(webdriver_class, selenium.webdriver.Chrome)
            and hasattr(os, "geteuid")
            and os.geteuid() == 0
        ):
            webdriver_options.add_argument("--no-sandbox")

        webdriver_options.add_argument("--headless")

        driver_obj = webdriver_class(options=webdriver_options)
        atexit.register(driver_obj.quit)
        driver_obj.set_page_load_timeout(driver_timeout)
        self.drivers[webdriver] = driver_obj

        return driver_obj


class SeleniumSaver(Saver):
    """Save charts using a selenium engine."""

    valid_formats: Dict[str, List[str]] = {
        "vega": ["png", "svg"],
        "vega-lite": ["png", "svg", "vega"],
    }
    driver_options: List[Union[str, WebDriver]] = ["chrome", "firefox"]

    _registry: _DriverRegistry = _DriverRegistry()
    _provider: Optional[Provider] = None
    _resources: Dict[str, Resource] = {}

    def __init__(
        self,
        spec: JSONDict,
        mode: Optional[str] = None,
        embed_options: Optional[JSONDict] = None,
        vega_version: str = alt.VEGA_VERSION,
        vegalite_version: str = alt.VEGALITE_VERSION,
        vegaembed_version: str = alt.VEGAEMBED_VERSION,
        driver_timeout: int = 20,
        webdriver: Optional[Union[str, WebDriver]] = None,
        offline: bool = True,
        scale_factor: Optional[float] = 1,
        **kwargs: Any,
    ) -> None:
        self._driver_timeout = driver_timeout
        self._webdriver = (
            self._select_webdriver(driver_timeout) if webdriver is None else webdriver
        )
        self._offline = offline
        if scale_factor != 1:
            embed_options = embed_options or {}
            embed_options.setdefault("scaleFactor", scale_factor)
        super().__init__(
            spec=spec,
            mode=mode,
            embed_options=embed_options,
            vega_version=vega_version,
            vegalite_version=vegalite_version,
            vegaembed_version=vegaembed_version,
            **kwargs,
        )

    @classmethod
    def _select_webdriver(cls, driver_timeout: int) -> Optional[str]:
        for driver in cls.driver_options:
            try:
                cls._registry.get(driver, driver_timeout)
            except WebDriverException:
                pass
            except Exception as e:
                warnings.warn(
                    f"Unexpected exception when attempting WebDriver creation: {e}"
                )
            else:
                return driver
        return None

    @classmethod
    def enabled(cls) -> bool:
        return cls._select_webdriver(20) is not None

    @classmethod
    def _serve(cls, content: str, js_resources: Dict[str, str]) -> str:
        if cls._provider is None:
            cls._provider = Provider()
        resource = cls._provider.create(
            content=content, route="", headers={"Access-Control-Allow-Origin": "*"},
        )
        cls._resources[resource.url] = resource
        for route, content in js_resources.items():
            cls._resources[route] = cls._provider.create(content=content, route=route,)
        return resource.url

    @classmethod
    def _stop_serving(cls) -> None:
        if cls._provider is not None:
            cls._provider.stop()
            cls._provider = None

    def _extract(self, fmt: str) -> MimebundleContent:
        driver = self._registry.get(self._webdriver, self._driver_timeout)

        if self._offline:
            js_resources = {
                "vega.js": get_bundled_script("vega", self._package_versions["vega"]),
                "vega-lite.js": get_bundled_script(
                    "vega-lite", self._package_versions["vega-lite"]
                ),
                "vega-embed.js": get_bundled_script(
                    "vega-embed", self._package_versions["vega-embed"]
                ),
            }
            html = HTML_TEMPLATE.format(
                vega_url="/vega.js",
                vegalite_url="/vega-lite.js",
                vegaembed_url="/vega-embed.js",
            )
        else:
            js_resources = {}
            html = HTML_TEMPLATE.format(
                vega_url=CDN_URL.format(
                    package="vega", version=self._package_versions["vega"]
                ),
                vegalite_url=CDN_URL.format(
                    package="vega-lite", version=self._package_versions["vega-lite"]
                ),
                vegaembed_url=CDN_URL.format(
                    package="vega-embed", version=self._package_versions["vega-embed"]
                ),
            )

        url = self._serve(html, js_resources)
        driver.get("about:blank")
        driver.get(url)
        try:
            driver.find_element_by_id("vis")
        except NoSuchElementException:
            raise RuntimeError(f"Could not load {url}")
        if not self._offline:
            online = driver.execute_script("return navigator.onLine")
            if not online:
                raise RuntimeError(
                    f"Internet connection required for saving chart as {fmt} with offline=False."
                )
        opt = self._embed_options.copy()
        opt["mode"] = self._mode
        result = driver.execute_async_script(EXTRACT_CODE, self._spec, opt, fmt)
        if "error" in result:
            raise JavascriptError(result["error"])
        return result["result"]

    def _serialize(self, fmt: str, content_type: str) -> MimebundleContent:
        out = self._extract(fmt)
        if fmt == "png":
            assert isinstance(out, str)
            return base64.b64decode(out.split(",", 1)[1].encode())
        elif fmt == "svg":
            return out
        elif fmt == "vega":
            return out
        else:
            raise ValueError(f"Unrecognized format: {fmt}")
