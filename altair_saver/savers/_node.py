import functools
import json
import shutil
from typing import Dict, List
import warnings

from altair_saver.savers import Saver
from altair_saver._utils import (
    JSONDict,
    MimebundleContent,
    check_output_with_stderr,
)


class ExecutableNotFound(RuntimeError):
    pass


@functools.lru_cache(2)
def npm_bin(global_: bool) -> str:
    """Locate the npm binary directory."""
    npm = shutil.which("npm")
    if not npm:
        raise ExecutableNotFound("npm")
    cmd = [npm, "bin"]
    if global_:
        cmd.append("--global")
    return check_output_with_stderr(cmd).decode()


@functools.lru_cache(16)
def exec_path(name: str) -> str:
    for path in [None, npm_bin(global_=True), npm_bin(global_=False)]:
        exc = shutil.which(name, path=path)
        if exc:
            return exc
    raise ExecutableNotFound(name)


def vl2vg(spec: JSONDict) -> JSONDict:
    """Compile a Vega-Lite spec into a Vega spec."""
    vl2vg = exec_path("vl2vg")
    vl_json = json.dumps(spec).encode()
    vg_json = check_output_with_stderr([vl2vg], input=vl_json)
    return json.loads(vg_json)


def vg2png(spec: JSONDict) -> bytes:
    """Generate a PNG image from a Vega spec."""
    vg2png = exec_path("vg2png")
    vg_json = json.dumps(spec).encode()
    return check_output_with_stderr([vg2png], input=vg_json)


def vg2pdf(spec: JSONDict) -> bytes:
    """Generate a PDF image from a Vega spec."""
    vg2pdf = exec_path("vg2pdf")
    vg_json = json.dumps(spec).encode()
    return check_output_with_stderr([vg2pdf], input=vg_json)


def vg2svg(spec: JSONDict) -> str:
    """Generate an SVG image from a Vega spec."""
    vg2svg = exec_path("vg2svg")
    vg_json = json.dumps(spec).encode()
    return check_output_with_stderr([vg2svg], input=vg_json).decode()


class NodeSaver(Saver):

    valid_formats: Dict[str, List[str]] = {
        "vega": ["pdf", "png", "svg"],
        "vega-lite": ["pdf", "png", "svg", "vega"],
    }

    @classmethod
    def enabled(cls) -> bool:
        try:
            return bool(exec_path("vl2vg") and exec_path("vg2png"))
        except ExecutableNotFound:
            return False

    def _serialize(self, fmt: str, content_type: str) -> MimebundleContent:
        if self._embed_options:
            warnings.warn("embed_options are not supported for method='node'.")

        if self._mode not in ["vega", "vega-lite"]:
            raise ValueError("mode must be either 'vega' or 'vega-lite'")

        spec = self._spec

        if self._mode == "vega-lite":
            spec = vl2vg(spec)

        if fmt == "vega":
            return spec
        elif fmt == "png":
            return vg2png(spec)
        elif fmt == "svg":
            return vg2svg(spec)
        elif fmt == "pdf":
            return vg2pdf(spec)
        else:
            raise ValueError(f"Unrecognized format: {fmt!r}")
