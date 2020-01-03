"""A basic vega-lite saver"""
from typing import List
from altair_saver.savers import Saver
from altair_saver._utils import Mimebundle, fmt_to_mimetype


class BasicSaver(Saver):
    """Basic chart output."""

    valid_formats: List[str] = ["vega-lite"]

    def _mimebundle(self, fmt: str) -> Mimebundle:
        if self._mode == "vega":
            raise ValueError("Cannot save vega spec as vega-lite.")
        return {fmt_to_mimetype("vega-lite"): self._spec}
