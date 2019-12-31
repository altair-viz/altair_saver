"""A basic vega-lite saver"""
from typing import List
import altair as alt
from altair_savechart._saver import Saver, Mimebundle


class BasicSaver(Saver):
    """Basic chart output."""

    valid_formats: List[str] = ["vega-lite", "json", "vl.json"]

    def _mimebundle(self, fmt: str) -> Mimebundle:
        if fmt not in self.valid_formats:
            raise ValueError(
                f"Invalid format: {fmt!r}. Must be one of {self.valid_formats}"
            )
        return {
            "application/vnd.vegalite.v{}+json".format(
                alt.VEGALITE_VERSION.split(".")[0]
            ): self._spec
        }
