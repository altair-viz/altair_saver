import atexit
import base64
import contextlib
import os
import tempfile
from typing import Dict, Optional, Union

import altair as alt
from altair_save import _versions
from altair_save._saver import Mimebundle, MimeType, Saver

from altair_data_server._provide import _Provider, _Resource

import selenium.webdriver
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.common.exceptions import NoSuchElementException

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
var mode = arguments[1];
var scaleFactor = arguments[2];
var format = arguments[3];
var done = arguments[4];

if (mode === 'vega-lite') {
    vegaLite = (typeof vegaLite === "undefined") ? vl : vegaLite;
    const compiled = vegaLite.compile(spec);
    spec = compiled.spec;
}

if (format === 'vega') {
    done(spec)
} else if (format === 'png') {
    new vega.View(vega.parse(spec), {
            loader: vega.loader(),
            logLevel: vega.Warn,
            renderer: 'none',
        })
        .initialize()
        .toCanvas(scaleFactor)
        .then(function(canvas){return canvas.toDataURL('image/png');})
        .then(done)
        .catch(function(err) { console.error(err); });
} else if (format === 'svg') {
    new vega.View(vega.parse(spec), {
            loader: vega.loader(),
            logLevel: vega.Warn,
            renderer: 'none',
        })
        .initialize()
        .toSVG(scaleFactor)
        .then(done)
        .catch(function(err) { console.error(err); });
} else {
    console.error("Unrecognized format: " + fmt)
}
"""


@contextlib.contextmanager
def temporary_filename(**kwargs):
    """Create and clean-up a temporary file

    Arguments are the same as those passed to tempfile.mkstemp

    We could use tempfile.NamedTemporaryFile here, but that causes issues on
    windows (see https://bugs.python.org/issue14243).
    """
    filedescriptor, filename = tempfile.mkstemp(**kwargs)
    os.close(filedescriptor)

    try:
        yield filename
    finally:
        if os.path.exists(filename):
            os.remove(filename)


class _DriverRegistry:
    """Registry of web driver singletons.

    This prevents the need to start and stop drivers repeatedly.
    """

    drivers: Dict[str, WebDriver]

    def __init__(self):
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

        if issubclass(webdriver_class, selenium.webdriver.Chrome):
            # for linux/osx root user, need to add --no-sandbox option.
            # since geteuid doesn't exist on windows, we don't check it
            if hasattr(os, "geteuid") and (os.geteuid() == 0):
                webdriver_options.add_argument("--no-sandbox")

        driver_obj = webdriver_class(options=webdriver_options)
        atexit.register(driver_obj.quit)
        driver_obj.set_page_load_timeout(driver_timeout)
        self.drivers[webdriver] = driver_obj

        return driver_obj


class SeleniumSaver(Saver):
    """Save charts using a selenium engine."""

    _registry: _DriverRegistry = _DriverRegistry()
    _provider: Optional[_Provider] = None
    _resources: Dict[str, _Resource] = {}

    def __init__(
        self,
        spec: dict,
        mode: str = "vega-lite",
        vega_version: str = _versions.VEGA_VERSION,
        vegalite_version: str = _versions.VEGALITE_VERSION,
        vegaembed_version: str = _versions.VEGAEMBED_VERSION,
        driver_timeout: int = 20,
        scale_factor: float = 1,
        webdriver: str = "chrome",
        use_local_server: bool = False,
        **kwargs,
    ):
        self._vega_version = vega_version
        self._vegalite_version = vegalite_version
        self._vegaembed_version = vegaembed_version
        self._driver_timeout = driver_timeout
        self._scale_factor = scale_factor
        self._webdriver = webdriver
        self._use_local_server = use_local_server
        super().__init__(spec=spec, mode=mode)

    @classmethod
    def _serve(cls, content: str, extension: str) -> str:
        if cls._provider is None:
            cls._provider = _Provider()
        resource = cls._provider.create(
            content=content,
            extension=extension,
            headers={"Access-Control-Allow-Origin": "*"},
        )
        cls._resources[resource.url] = resource
        return resource.url

    @classmethod
    def _stop_serving(cls):
        if cls._provider is not None:
            cls._provider.stop()
            cls._provider = None

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

        def _run_script(url):
            driver.get("about:blank")
            driver.get(url)
            try:
                driver.find_element_by_id("vis")
            except NoSuchElementException:
                raise RuntimeError(f"Could not load {url}")
            online = driver.execute_script("return navigator.onLine")
            if not online:
                raise RuntimeError(
                    f"Internet connection required for saving chart as {fmt}"
                )
            return driver.execute_async_script(
                EXTRACT_CODE, self._spec, self._mode, self._scale_factor, fmt
            )

        if self._use_local_server:
            try:
                url = self._serve(html, extension="html")
                return _run_script(url)
            finally:
                self._stop_serving()
        else:
            with temporary_filename(suffix=".html") as htmlfile:
                with open(htmlfile, "w") as f:
                    f.write(html)
                return _run_script(f"file://{htmlfile}")

    def _mimebundle(self, fmt: str) -> Mimebundle:
        if self._mode not in ["vega", "vega-lite"]:
            raise ValueError("mode must be either 'vega' or 'vega-lite'")

        if self._mode == "vega" and fmt == "vega-lite":
            raise ValueError("mode='vega' not compatible with fmt='vega-lite'")

        out: MimeType = {}

        if fmt == self._mode:
            out = self._spec
        else:
            out = self._extract(fmt)

        if fmt == "png":
            assert isinstance(out, str)
            assert out.startswith("data:image/png;base64,")
            return {"image/png": base64.b64decode(out.split(",", 1)[1].encode())}
        elif fmt == "svg":
            assert isinstance(out, str)
            return {"image/svg+xml": out}
        elif fmt == "vega":
            assert isinstance(out, dict)
            return {
                "application/vnd.vega.v{}+json".format(
                    alt.VEGA_VERSION.split(".")[0]
                ): out
            }
        elif fmt == "vega-lite":
            assert isinstance(out, dict)
            return {
                "application/vnd.vegalite.v{}+json".format(
                    alt.VEGALITE_VERSION.split(".")[0]
                ): out
            }
        else:
            raise ValueError(f"Unrecognized format: {fmt}")
