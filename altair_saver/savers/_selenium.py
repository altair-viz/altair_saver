import atexit
import base64
import os
from typing import Dict, List, Optional, Union
import warnings

import altair as alt
from altair_saver.savers import Saver
from altair_saver._utils import JSONDict, Mimebundle, MimeType, fmt_to_mimetype

from altair_data_server import Provider, Resource
from altair_viewer import get_bundled_script

import selenium.webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException


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
var spec = arguments[0];
var done = arguments[1];
done({result: vegaLite.compile(spec).spec})
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
        webdriver_options.add_argument("--headless")

        driver_obj = webdriver_class(options=webdriver_options)
        atexit.register(driver_obj.quit)
        driver_obj.set_page_load_timeout(driver_timeout)
        self.drivers[webdriver] = driver_obj

        return driver_obj


class SeleniumSaver(Saver):
    """Save charts using a selenium engine."""

    valid_formats: List[str] = ["png", "svg", "vega"]
    _registry: _DriverRegistry = _DriverRegistry()
    _provider: Optional[Provider] = None
    _resources: Dict[str, Resource] = {}

    def __init__(
        self,
        spec: JSONDict,
        mode: Optional[str] = None,
        vega_version: str = alt.VEGA_VERSION,
        vegalite_version: str = alt.VEGALITE_VERSION,
        vegaembed_version: str = alt.VEGAEMBED_VERSION,
        driver_timeout: int = 20,
        scale_factor: float = 1,
        webdriver: Optional[Union[str, WebDriver]] = "chrome",
        offline: bool = True,
    ) -> None:
        self._vega_version = vega_version
        self._vegalite_version = vegalite_version
        self._vegaembed_version = vegaembed_version
        self._driver_timeout = driver_timeout
        self._scale_factor = scale_factor
        self._webdriver = webdriver
        self._offline = offline
        super().__init__(spec=spec, mode=mode)

    def _extract(self, fmt: str) -> MimeType:
        driver = self._registry.get(self._webdriver, self._driver_timeout)
        html = HTML_TEMPLATE.format(
            vega_url=CDN_URL.format(package="vega", version=self._vega_version),
            vegalite_url=CDN_URL.format(
                package="vega-lite", version=self._vegalite_version
            ),
            vegaembed_url=CDN_URL.format(
                package="vega-embed", version=self._vegaembed_version
            ),
        )

        print(f"HTML:\n{html}")

        filename = os.path.abspath('index.html')
        with open(filename, 'w') as f:
            f.write(html)
        url = f"file://{filename}"
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

        print(f"SCRIPT:\n{EXTRACT_CODE}")
        assert self._mode == 'vega-lite'
        assert fmt == 'vega'
        result = driver.execute_async_script(
            EXTRACT_CODE, self._spec
        )
        if "error" in result:
            raise JavascriptError(result["error"])
        return result["result"]

    def _mimebundle(self, fmt: str) -> Mimebundle:
        raise NotImplementedError()
