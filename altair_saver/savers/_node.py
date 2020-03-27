import functools
import json
import shutil
from typing import Dict, List, Optional
import warnings

from altair_saver.types import JSONDict, MimebundleContent
from altair_saver._utils import check_output_with_stderr
from altair_saver.savers import Saver


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
    return check_output_with_stderr(cmd).decode().strip()


@functools.lru_cache(16)
def exec_path(name: str) -> str:
    for path in [None, npm_bin(global_=True), npm_bin(global_=False)]:
        exc = shutil.which(name, path=path)
        if exc:
            return exc
    raise ExecutableNotFound(name)


def vl2vg(spec: JSONDict, vega_cli_options: Optional[List] = None) -> JSONDict:
    """Compile a Vega-Lite spec into a Vega spec."""
    vl2vg = exec_path("vl2vg")
    vl_json = json.dumps(spec).encode()
    cmd = [vl2vg]
    if vega_cli_options:
        cmd += vega_cli_options
    vg_json = check_output_with_stderr(cmd, input=vl_json)
    return json.loads(vg_json)


def vg2png(spec: JSONDict, vega_cli_options: Optional[List] = None) -> bytes:
    """Generate a PNG image from a Vega spec."""
    vg2png = exec_path("vg2png")
    vg_json = json.dumps(spec).encode()
    cmd = [vg2png]
    if vega_cli_options:
        cmd += vega_cli_options
    return check_output_with_stderr(cmd, input=vg_json)


def vg2pdf(spec: JSONDict, vega_cli_options: Optional[List] = None) -> bytes:
    """Generate a PDF image from a Vega spec."""
    vg2pdf = exec_path("vg2pdf")
    vg_json = json.dumps(spec).encode()
    cmd = [vg2pdf]
    if vega_cli_options:
        cmd += vega_cli_options
    return check_output_with_stderr(cmd, input=vg_json)


def vg2svg(spec: JSONDict, vega_cli_options: Optional[List] = None) -> str:
    """Generate an SVG image from a Vega spec."""
    vg2svg = exec_path("vg2svg")
    vg_json = json.dumps(spec).encode()
    cmd = [vg2svg]
    if vega_cli_options:
        cmd += vega_cli_options
    # raise Exception(cmd)
    return check_output_with_stderr(cmd, input=vg_json).decode()


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
            return vg2png(spec, vega_cli_options=self._vega_cli_options)
        elif fmt == "svg":
            return vg2svg(spec, vega_cli_options=self._vega_cli_options)
        elif fmt == "pdf":
            return vg2pdf(spec, vega_cli_options=self._vega_cli_options)
        else:
            raise ValueError(f"Unrecognized format: {fmt!r}")
