"""
Utilities that use selenium + chrome headless to save figures
"""

import atexit
import contextlib
import os
import tempfile
import selenium.webdriver

VEGA_VERSION = "5.9.0"
VEGALITE_VERSION = "4.0.0"
VEGAEMBED_VERSION = "6.2.1"


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


def _get_driver(webdriver, driver_timeout):
    """Get a webdriver by name."""
    webdriver = _get_driver.drivers.get(webdriver, webdriver)
    if isinstance(webdriver, selenium.webdriver.Remote):
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
    _get_driver.drivers[webdriver] = driver_obj

    return driver_obj


_get_driver.drivers = {}


def compile_spec(
    spec,
    fmt,
    mode,
    vega_version=VEGA_VERSION,
    vegaembed_version=VEGAEMBED_VERSION,
    vegalite_version=VEGALITE_VERSION,
    scale_factor=1,
    driver_timeout=20,
    webdriver="chrome",
):
    if fmt not in ["png", "svg", "vega"]:
        raise NotImplementedError(f"fmt={fmt!r} must be 'svg', 'png' or 'vega'")

    if mode not in ["vega", "vega-lite"]:
        raise ValueError("mode must be either 'vega' or 'vega-lite'")

    driver = _get_driver(webdriver, driver_timeout)

    html = HTML_TEMPLATE.format(
        vega_version=vega_version,
        vegalite_version=vegalite_version,
        vegaembed_version=vegaembed_version,
    )

    with temporary_filename(suffix=".html") as htmlfile:
        with open(htmlfile, "w") as f:
            f.write(html)
        driver.get("file://" + htmlfile)
        online = driver.execute_script("return navigator.onLine")
        if not online:
            raise ValueError(
                "Internet connection required for saving " "chart as {}".format(fmt)
            )
        return driver.execute_async_script(EXTRACT_CODE, spec, mode, scale_factor, fmt)
