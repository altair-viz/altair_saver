"""A basic vega-lite saver"""
from typing import Dict, List

from altair_saver.types import MimebundleContent
from altair_saver.savers import Saver


class BasicSaver(Saver):
    """Basic chart output."""

    valid_formats: Dict[str, List[str]] = {
        "vega": ["json", "vega"],
        "vega-lite": ["json", "vega-lite"],
    }

    def _serialize(self, fmt: str, content_type: str) -> MimebundleContent:
        return self._spec
