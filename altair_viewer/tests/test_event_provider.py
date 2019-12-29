import pytest
from typing import Iterator

from tornado.httpclient import HTTPClient, HTTPRequest
from tornado.simple_httpclient import HTTPTimeoutError

from altair_viewer._event_provider import EventProvider


@pytest.fixture
def http_client() -> HTTPClient:
    return HTTPClient()


@pytest.fixture(scope="module")
def provider() -> Iterator[EventProvider]:
    provider = EventProvider()
    provider.start()
    yield provider
    provider.stop()


def test_simple_stream(http_client, provider):
    stream = provider.create_stream("data")
    assert stream.url.endswith("stream/data")

    for content in ["AAAAA", "BBBBB"]:
        stream.send(content)
        result = []

        # Request will never return, so set a short timeout and catch the expected error.
        request = HTTPRequest(
            url=stream.url, streaming_callback=result.append, request_timeout=0.5
        )
        with pytest.raises(HTTPTimeoutError):
            http_client.fetch(request)
        assert result == [f"data: {content}\n\n".encode()]
