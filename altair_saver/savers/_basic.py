"""A basic vega-lite saver"""
from typing import List
from altair_saver.savers import Saver
from altair_saver._utils import MimebundleContent


class BasicSaver(Saver):
    """Basic chart output."""

    valid_formats: List[str] = ["vega-lite"]

    def _serialize(self, fmt: str, content_type: str) -> MimebundleContent:
        if self._mode == "vega":
            raise ValueError("Cannot save vega spec as vega-lite.")
        return self._spec
