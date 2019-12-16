import base64
import json
from typing import Dict, IO, Union

import altair as alt
from altair_save.compile import compile_spec


# TODO: make this only accept binary
def _write_file_or_filename(fp: Union[IO, str], content: Union[str, bytes], mode="w"):
    """Write content to fp, whether fp is a string or a file-like object"""
    if isinstance(fp, str):
        with open(fp, mode) as f:
            f.write(content)
    else:
        fp.write(content)


class Saver:
    def __init__(self, chart, **kwargs):
        self.chart = chart
        self._kwargs = kwargs

    def mimebundle(self, fmt: str) -> Dict[str, Union[str, bytes]]:
        if isinstance(self.chart, dict):
            spec = self.chart
        else:
            spec = self.chart.to_dict()
        out = compile_spec(spec, fmt, mode="vega-lite")
        print(fmt, type(out))
        if fmt == "png":
            return {"image/png": base64.b64decode(out.split(",", 1)[1].encode())}
        elif fmt == "svg":
            return {"image/svg+xml": out.encode()}
        elif fmt == "vega":
            return {"application/vnd.vega.v{}+json".format(alt.VEGA_VERSION[0]): out}
        else:
            raise ValueError(f"Unrecognized format: {fmt}")

    def save(self, fp: Union[IO, str], fmt: str = None):
        if fmt is None:
            if isinstance(fp, str):
                fmt = fp.split(".")[-1]
            else:
                raise ValueError("must specify file format: ['png', 'svg', 'vega']")
        mimebundle = self.mimebundle(fmt)
        if fmt == "png":
            _write_file_or_filename(fp, mimebundle["image/png"], mode="wb")
        elif fmt == "svg":
            _write_file_or_filename(fp, mimebundle["image/svg+xml"], mode="wb")
        elif fmt == "vega":
            _write_file_or_filename(
                fp, json.dumps(mimebundle.popitem()[1], indent=2), mode="w"
            )
        else:
            raise ValueError(f"Unrecognized format: {fmt}")
