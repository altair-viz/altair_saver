import altair as alt
from altair import vega
from altair_saver import render


def test_entrypoint_exists() -> None:
    assert "altair_saver" in alt.renderers.names()
    assert "altair_saver" in vega.renderers.names()


def test_entrypoint_identity() -> None:
    with alt.renderers.enable("altair_saver"):
        assert alt.renderers.get() is render

    with vega.renderers.enable("altair_saver"):
        assert vega.renderers.get() is render
