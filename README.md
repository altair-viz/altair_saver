# Altair viewer
Offline chart viewer for Altair visualizations

[![github actions](https://github.com/jakevdp/altair_viewer/workflows/build/badge.svg)](https://github.com/jakevdp/altair_viewer/actions?query=workflow%3Abuild)
[![github actions](https://github.com/jakevdp/altair_viewer/workflows/lint/badge.svg)](https://github.com/jakevdp/altair_viewer/actions?query=workflow%3Alint)
[![code style black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

This package provides tools for viewing Altair charts without a web connection. Charts can
be displayed either inline in a Jupyter notebook environment, or in a separate browser window
for use in any environment.

## Installation
The development version of Altair-viewer can be installed with pip:
```
$ pip install git+http://github.com/jakevdp/altair_viewer.git
```

## Usage: General
Altair viewer provides two top-level functions for displaying charts: ``altair_viewer.display``
and ``altair_viewer.show``. Their use is slightly different:

- ``altair_viewer.display(chart)`` is meant for use in interactive computing environments where
  a single Python process is used interactively. It will serve a chart viewer at a localhost
  URL, and any susequent chart created within the session will appear in the same window.
  The background server will be terminated when the main Python process terminates, so this
  is not suitable for standalone scripts.

- ``altair_viewer.show(chart)`` is meant for use once at the end of a script. It does the same
  as ``altair_viewer.display``, but rather than using a self-terminating background thread, it
  joins the server to the main thread, so that the chart will display indefinitely until the
  process is canceled.

## Usage: IPython & Jupyter
Within Jupyter notebook, IPython notebook, and related environments that support
[Mimetype-based display](https://jupyterlab.readthedocs.io/en/stable/user/file_formats.html),
altair viewer can be used by enabling the ``altair_viewer`` renderer:
```python
import altair as alt
alt.renderers.enable('altair_viewer')
```
This will cause charts at the end of a Jupyter notebook cell to be rendered in a
separate browser window, as with the ``display()`` and ``show()`` methods.

If enabled with ``inline=True``, charts will be rendered inline in the notebook:
```python
import altair as alt
alt.renderers.enable('altair_viewer', inline=True)
```
To display a single chart using Altair viewer in an IPython environment without globally
enabling the associated renderer, you can use the ``display`` method:
```python
import altair_viewer
altair_viewer.display(chart, inline=True)
```

Note that the display based on altair viewer will only function correctly as long as the
Kernel that created the charts is active, as it depends on the background server started
by the kernel. In particular, this means that if you save a notebook and reopen it later,
charts will not display until the associated cells are re-run.