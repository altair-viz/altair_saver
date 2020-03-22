import json
import os
from typing import Iterator, Tuple

import pytest

from altair_saver import BasicSaver
from altair_saver.types import JSONDict


def get_testcases() -> Iterator[Tuple[str, str, JSONDict]]:
    directory = os.path.join(os.path.dirname(__file__), "testcases")
    cases = set(f.split(".")[0] for f in os.listdir(directory))
    for case in sorted(cases):
        for mode, filename in [
            ("vega-lite", f"{case}.vl.json"),
            ("vega", f"{case}.vg.json"),
        ]:
            with open(os.path.join(directory, filename)) as f:
                spec = json.load(f)
            yield case, mode, spec


@pytest.mark.parametrize("case, mode, spec", get_testcases())
def test_basic_saver(case: str, mode: str, spec: JSONDict) -> None:
    saver = BasicSaver(spec)
    bundle = saver.mimebundle([mode, "json"])
    for output in bundle.values():
        assert output == spec


def test_bad_format() -> None:
    saver = BasicSaver({})
    with pytest.raises(ValueError):
        saver.mimebundle("vega")
