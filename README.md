# Altair Saver

[![github actions](https://github.com/altair-viz/altair_saver/workflows/build/badge.svg)](https://github.com/altair-viz/altair_saver/actions?query=workflow%3Abuild)
[![github actions](https://github.com/altair-viz/altair_saver/workflows/lint/badge.svg)](https://github.com/altair-viz/altair_saver/actions?query=workflow%3Alint)
[![code style black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/altair-viz/altair_saver/blob/master/AltairSaver.ipynb)


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

### Renderer
Additionally, altair_saver provides an [Altair Renderer](https://altair-viz.github.io/user_guide/display_frontends.html#altair-s-renderer-framework)
entrypoint that can display the above outputs directly in Jupyter notebooks.
For example, you can specify a vega-lite mimetype (supported by JupyterLab, nteract, and other
platforms) with a PNG fallback for other frontends as follows:
```python
alt.renderers.enable('altair_saver', ['vega-lite', 'png'])
```

## Installation
The ``altair_saver`` package can be installed with:
```
$ pip install altair_saver
```
Saving as ``vl.json`` and as ``html`` requires no additional setup.

To install with conda, use
```
$ conda install -c conda-forge altair_saver
```
The conda package installs the *NodeJS* dependencies described below, so charts can be
saved to ``png``, ``svg``, and ``pdf`` without additional setup.

### Additional Requirements

Output to ``png``, ``svg``, and ``pdf`` requires execution of Javascript code, which
``altair_saver`` can do via one of two backends.

#### Selenium
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
Using conda, the required packages can be installed as follows (a compatible version of
[Google Chrome](https://www.google.com/chrome/) must be installed separately):
```bash
$ conda install -c python-chromedriver-binary
```
Selenium supports [other browsers](https://selenium-python.readthedocs.io/installation.html) as well,
but altair-saver is currently only tested with Chrome.

#### NodeJS
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
Using conda, node and the required packages can be installed as follows:
```bash
$ conda install -c conda-forge vega-cli vega-lite-cli
```
These packages are included automatically when installing ``altair_saver`` via conda-forge.
