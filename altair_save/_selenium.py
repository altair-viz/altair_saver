import atexit
import base64
import contextlib
import os
import tempfile
from typing import Any, Dict, Union

import altair as alt
from altair_save import versions
from altair_save._saver import Saver


import selenium.webdriver
from selenium.webdriver.remote.webdriver import WebDriver


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
  <title>Embedding Vega-Lite</title>
  <script src="https://cdn.jsdelivr.net/npm/vega@{vega_version}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-lite@{vegalite_version}"></script>
  <script src="https://cdn.jsdelivr.net/npm/vega-embed@{vegaembed_version}"></script>
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
    // compile vega-lite to vega
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


_registry = _DriverRegistry()


def _compile_spec(
    spec: Dict[str, Any],
    fmt: str,
    mode: str,
    vega_version: str = versions.VEGA_VERSION,
    vegaembed_version: str = versions.VEGAEMBED_VERSION,
    vegalite_version: str = versions.VEGALITE_VERSION,
    scale_factor: float = 1,
    webdriver: str = "chrome",
    driver_timeout: float = 20,
) -> Union[str, Dict[str, Any]]:
    """Use selenium to compile a vega or vega-lite spec.

    Parameters
    ----------

    """


class SeleniumSaver(Saver):
    def __init__(
        self,
        spec: dict,
        mode: str = "vega-lite",
        vega_version: str = versions.VEGA_VERSION,
        vegalite_version: str = versions.VEGALITE_VERSION,
        vegaembed_version: str = versions.VEGAEMBED_VERSION,
        driver_timeout: int = 20,
        scale_factor: float = 1,
        webdriver: str = "chrome",
        **kwargs,
    ):
        self._vega_version = vega_version
        self._vegalite_version = vegalite_version
        self._vegaembed_version = vegaembed_version
        self._driver_timeout = driver_timeout
        self._scale_factor = scale_factor
        self._webdriver = webdriver
        super().__init__(spec=spec, mode=mode)

    def _mimebundle(self, fmt: str) -> Dict[str, Union[str, bytes, dict]]:
        if fmt not in ["png", "svg", "vega", "vega-lite"]:
            raise NotImplementedError(
                f"fmt={fmt!r} must be 'svg', 'png', 'vega'  or 'vega-lite'"
            )

        if self._mode not in ["vega", "vega-lite"]:
            raise ValueError("mode must be either 'vega' or 'vega-lite'")

        if self._mode == "vega" and fmt == "vega-lite":
            raise ValueError("mode='vega' not compatible with fmt='vega-lite'")

        if fmt == self._mode:
            out = self._spec
        else:
            driver = _registry.get(self._webdriver, self._driver_timeout)

            html = HTML_TEMPLATE.format(
                vega_version=self._vega_version,
                vegalite_version=self._vegalite_version,
                vegaembed_version=self._vegaembed_version,
            )

            with temporary_filename(suffix=".html") as htmlfile:
                with open(htmlfile, "w") as f:
                    f.write(html)
                driver.get("file://" + htmlfile)
                online = driver.execute_script("return navigator.onLine")
                if not online:
                    raise ValueError(
                        "Internet connection required for saving "
                        "chart as {}".format(fmt)
                    )
                out = driver.execute_async_script(
                    EXTRACT_CODE, self._spec, self._mode, self._scale_factor, fmt
                )

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
