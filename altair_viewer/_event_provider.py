from altair_data_server._provide import Provider
from collections import defaultdict
import tornado.gen
import tornado.web
from typing import MutableMapping


class DataSource:
    def __init__(
        self, provider: "EventProvider", stream_id: str, data: str = ""
    ) -> None:
        self._provider = provider
        self.stream_id = stream_id
        self.data = data

    def send(self, data: str) -> None:
        self.data = data

    @property
    def url(self) -> str:
        return f"{self._provider.url}/{self._provider._stream_path}/{self.stream_id}"


class EventStreamHandler(tornado.web.RequestHandler):
    def initialize(self, data_sources):
        self._data_sources = data_sources
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
            while True:
                if self._data_sources[stream_id].data != self._current_value[stream_id]:
                    value = self._current_value[stream_id] = self._data_sources[
                        stream_id
                    ].data
                    self.write(f"data: {value}\n\n")
                    await self.flush()
                else:
                    await tornado.gen.sleep(0.1)
        except tornado.iostream.StreamClosedError:
            pass


class EventProvider(Provider):
    _data_sources: MutableMapping[str, DataSource]
    _stream_path: str

    def __init__(self, stream_path: str = "stream"):
        self._data_sources = {}
        self._stream_path = stream_path
        super().__init__()

    def _handlers(self) -> list:
        handlers = super()._handlers()
        return [
            (
                f"/{self._stream_path}/.*",
                EventStreamHandler,
                dict(data_sources=self._data_sources),
            )
        ] + handlers

    def create_stream(self, stream_id: str) -> DataSource:
        if stream_id not in self._data_sources:
            self._data_sources[stream_id] = DataSource(self, stream_id)
            self.start()
        return self._data_sources[stream_id]
