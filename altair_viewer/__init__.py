"""Altair viewer provides offline viewing for Altair charts."""

__version__ = "0.1.0"
__all__ = ["ChartViewer", "display", "render", "show", "get_bundled_script"]

from altair_viewer._viewer import ChartViewer
from altair_viewer._scripts import get_bundled_script

_global_viewer = ChartViewer()
display = _global_viewer.display
render = _global_viewer.render
show = _global_viewer.show
