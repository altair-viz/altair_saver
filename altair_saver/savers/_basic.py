"""A basic vega-lite saver"""
from typing import List
import altair as alt
from altair_saver.savers import Saver
from altair_saver._utils import Mimebundle


class BasicSaver(Saver):
    """Basic chart output."""

    valid_formats: List[str] = ["vega-lite"]

    def _mimebundle(self, fmt: str) -> Mimebundle:
        if self._mode == "vega":
            raise ValueError("Cannot save vega spec as vega-lite.")
        return {
            "application/vnd.vegalite.v{}+json".format(
                alt.VEGALITE_VERSION.split(".")[0]
            ): self._spec
        }
