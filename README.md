# Altair SaveChart

[![github actions](https://github.com/jakevdp/altair_saver/workflows/build/badge.svg)](https://github.com/jakevdp/altair_saver/actions?query=workflow%3Abuild)
[![github actions](https://github.com/jakevdp/altair_saver/workflows/lint/badge.svg)](https://github.com/jakevdp/altair_saver/actions?query=workflow%3Alint)
[![code style black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This packge provides extensions to [Altair](http://altair-viz.github.io) for saving charts
to a variety of output types. Supported output formats are:

- ``.json``/``.vl.json``: Vega-Lite JSON specification
- ``.html``: HTML output
- ``.vg.json``: Vega JSON specification
- ``.png``: PNG image
- ``.svg``: SVG image
- ``.pdf``: PDF image

## Usage
The ``altair_saver`` library has a single public function, ``altair_saver.save()``.
Given an Altair chart named ``chart``, you can use it as follows:
```python
from altair_saver import save

save(chart, "chart.json")                 # Vega-Lite JSON specification
save(chart, "chart.vg.json")              # Vega JSON specification
save(chart, "chart.html")                 # HTML document
save(chart, "chart.html", inline=True)    # HTML document with all JS code inline
save(chart, "chart.png")                  # PNG Image
save(chart, "chart.svg")                  # SVG Image
save(chart, "chart.pdf")                  # PDF Image
```

## Installation
``altair_saver`` can be installed with:
```
$ pip install git+https://github.com/jakevdp/altair_saver.git
```
Saving as ``vg.json`` and as ``html`` requires no additional setup.

To save charts in other formats requires several dependencies beyond the Python stack
to be properly configured. 

### Selenium
The *selenium* backend can save charts to ``.vg.json``, ``.png``, or ``.svg``.
It requires [Selenium](https://selenium.dev/selenium/docs/api/py/) and a properly configured
installation of either [chromedriver](https://chromedriver.chromium.org/) or
[geckodriver](https://firefox-source-docs.mozilla.org/testing/geckodriver/).

### NodeJS
The *nodejs* backend can save charts to ``.vg.json``, ``.png``,``.svg``, or ``.pdf``.
It requires [npm](https://www.npmjs.com/), along with the following npm packages to be
globally installed:
```bash
$ npm install -g vega-lite vega-cli canvas
```

