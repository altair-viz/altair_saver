import pytest
from altair_viewer import get_bundled_script


@pytest.mark.parametrize("package", ["vega", "vega-lite", "vega-embed"])
def test_get_bundled_script(package):
    script = get_bundled_script(package)
    assert script.startswith("!function(")
