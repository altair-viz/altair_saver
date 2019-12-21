import altair as alt
from altair_viewer import render


def test_entrypoint_exists():
    assert "altair_viewer" in alt.renderers.names()


def test_entrypoint_identity():
    with alt.renderers.enable("altair_viewer"):
        assert alt.renderers.get() is render
