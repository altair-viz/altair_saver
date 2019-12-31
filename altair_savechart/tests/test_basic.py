import json
import os
from typing import Any, Dict, Iterable, Tuple

import pytest

from altair_savechart._basic import BasicSaver


def get_test_cases() -> Iterable[Tuple[str, Dict[str, Any]]]:
    directory = os.path.join(os.path.dirname(__file__), "test_cases")
    cases = set(f.split(".")[0] for f in os.listdir(directory))
    for case in sorted(cases):
        with open(os.path.join(directory, f"{case}.vl.json")) as f:
            spec = json.load(f)
        yield case, spec


@pytest.mark.parametrize("case, spec", get_test_cases())
@pytest.mark.parametrize("fmt", ["vega-lite", "json", "vl.json"])
def test_basic_saver(case: str, spec: Dict[str, Any], fmt: str) -> None:
    saver = BasicSaver(spec)
    bundle = saver.mimebundle(fmt)
    assert bundle.popitem()[1] == spec


def test_bad_format() -> None:
    saver = BasicSaver({})
    with pytest.raises(ValueError):
        saver.mimebundle("vega")
