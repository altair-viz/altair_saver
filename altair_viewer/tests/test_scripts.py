import pytest
from altair_viewer._scripts import _get_script


@pytest.mark.parametrize("package", ["vega", "vega-lite", "vega-embed"])
def test_get_script(package):
    script = _get_script(package)
    assert script.startswith("!function(")
