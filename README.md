# Altair Saver

[![github actions](https://github.com/altair-viz/altair_saver/workflows/build/badge.svg)](https://github.com/altair-viz/altair_saver/actions?query=workflow%3Abuild)
[![github actions](https://github.com/altair-viz/altair_saver/workflows/lint/badge.svg)](https://github.com/altair-viz/altair_saver/actions?query=workflow%3Alint)
[![code style black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jakevdp/altair_saver/blob/master/AltairSaver.ipynb)


This packge provides extensions to [Altair](http://altair-viz.github.io) for saving charts
to a variety of output types. Supported output formats are:

- ``.json``/``.vl.json``: Vega-Lite JSON specification
- ``.vg.json``: Vega JSON specification
- ``.html``: HTML output
- ``.png``: PNG image
- ``.svg``: SVG image
- ``.pdf``: PDF image

## Usage
The ``altair_saver`` library has a single public function, ``altair_saver.save()``.
Given an Altair chart named ``chart``, you can use it as follows:
```python
from altair_saver import save

save(chart, "chart.vl.json")              # Vega-Lite JSON specification
save(chart, "chart.vg.json")              # Vega JSON specification
save(chart, "chart.html")                 # HTML document
save(chart, "chart.html", inline=True)    # HTML document with all JS code included inline
save(chart, "chart.png")                  # PNG Image
save(chart, "chart.svg")                  # SVG Image
save(chart, "chart.pdf")                  # PDF Image
```

## Installation
The ``altair_saver`` package can be installed with:
```
$ pip install git+https://github.com/altair-viz/altair_saver.git
```
Saving as ``vl.json`` and as ``html`` requires no additional setup.

To save charts in other formats requires additional dependencies in order to execute the
javascript code used to render and save Altair charts. ``altair_saver`` provides interfaces
to two different backends, respectively based on Selenium and NodeJS.

### Selenium
The *selenium* backend supports the following formats:

- `.vg.json`
- `.png`
- `.svg`.

To be used, it requires the [Selenium](https://selenium.dev/selenium/docs/api/py/) Python package,
and a properly configured installation of either [chromedriver](https://chromedriver.chromium.org/) or
[geckodriver](https://firefox-source-docs.mozilla.org/testing/geckodriver/).

On Linux systems, this can be setup as follows:
```bash
$ pip install selenium
$ apt-get install chromium-chromedriver
```

### NodeJS
The *nodejs* backend supports the following formats: 

- `.vg.json`
- `.png`
- `.svg`
- `.pdf`

It requires [NodeJS](https://nodejs.org/), along with the [vega-lite](https://www.npmjs.com/package/vega-lite),
[vega-cli](https://www.npmjs.com/package/vega-cli), and [canvas](https://www.npmjs.com/package/canvas) packages.

First install NodeJS either by [direct download](https://nodejs.org/en/download/) or via a
[package manager](https://nodejs.org/en/download/package-manager/), and then use the `npm` tool
to install the required packages:
```bash
$ npm install vega-lite vega-cli canvas
```

