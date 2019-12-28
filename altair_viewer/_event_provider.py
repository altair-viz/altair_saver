from altair_data_server._provide import Provider
from collections import defaultdict
import threading
import time
import tornado.gen
import tornado.web
from typing import MutableMapping, TypeVar


class DataSource:
    """Data source for an event stream."""

    def __init__(
        self, provider: "EventProvider", stream_id: str, data: str = ""
    ) -> None:
        self._provider = provider
        self.stream_id = stream_id
        self.data = data

    def send(self, data: str) -> None:
        """Send data to the event stream."""
        self.data = data

    @property
    def url(self) -> str:
        return f"{self._provider.url}/{self._provider._stream_path}/{self.stream_id}"


class EventStreamHandler(tornado.web.RequestHandler):
    """Request handler for an event stream."""

    _data_sources: MutableMapping[str, DataSource]
    _stop_event: threading.Event
    _current_value: MutableMapping[str, str]

    def initialize(
        self,
        data_sources: MutableMapping[str, DataSource],
        stop_event: threading.Event,
    ) -> None:
        self._data_sources = data_sources
        self._stop_event = stop_event
        self._current_value = defaultdict(str)
        self.set_header("content-type", "text/event-stream")
        self.set_header("cache-control", "no-cache")

    async def get(self):
        path = self.request.path
        stream_id = path.split("/")[-1]
        if stream_id not in self._data_sources:
            self.set_response(404)
            return
        try:
            while not self._stop_event.is_set():
                if self._data_sources[stream_id].data != self._current_value[stream_id]:
                    value = self._data_sources[stream_id].data
                    self._current_value[stream_id] = value
                    self.write(f"data: {value}\n\n")
                    await self.flush()
                else:
                    await tornado.gen.sleep(0.05)
        except tornado.iostream.StreamClosedError:
            pass


T = TypeVar("T", bound="EventProvider")


class EventProvider(Provider):
    """A resource provider with event streams."""

    _data_sources: MutableMapping[str, DataSource]
    _stream_path: str
    _stop_event: threading.Event

    def __init__(self, stream_path: str = "stream"):
        self._data_sources = {}
        self._stream_path = stream_path
        self._stop_event = threading.Event()
        super().__init__()

    def stop(self: T) -> T:
        self._stop_event.set()
        time.sleep(0.05)  # Allow loop in thread to complete.
        return super().stop()

    def _handlers(self) -> list:
        handlers = super()._handlers()
        return [
            (
                f"/{self._stream_path}/.*",
                EventStreamHandler,
                dict(data_sources=self._data_sources, stop_event=self._stop_event),
            )
        ] + handlers

    def create_stream(self, stream_id: str) -> DataSource:
        if stream_id not in self._data_sources:
            self._data_sources[stream_id] = DataSource(self, stream_id)
            self.start()
        return self._data_sources[stream_id]
