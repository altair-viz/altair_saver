import functools
import json
import shutil
from typing import Any, Callable, Dict, List, Optional

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


def _default_stderr_filter(line: str) -> bool:
    return line != "WARN Can not resolve event source: window"


class NodeSaver(Saver):

    valid_formats: Dict[str, List[str]] = {
        "vega": ["pdf", "png", "svg"],
        "vega-lite": ["pdf", "png", "svg", "vega"],
    }
    _vega_cli_options: List[str]
    _stderr_filter: Optional[Callable[[str], bool]]

    def __init__(
        self,
        spec: JSONDict,
        mode: Optional[str] = None,
        vega_cli_options: Optional[List[str]] = None,
        stderr_filter: Optional[Callable[[str], bool]] = _default_stderr_filter,
        **kwargs: Any,
    ) -> None:
        self._vega_cli_options = vega_cli_options or []
        self._stderr_filter = stderr_filter
        super().__init__(spec=spec, mode=mode, **kwargs)

    def _vl2vg(self, spec: JSONDict) -> JSONDict:
        """Compile a Vega-Lite spec into a Vega spec."""
        vl2vg = exec_path("vl2vg")
        vl_json = json.dumps(spec).encode()
        vg_json = check_output_with_stderr(
            [vl2vg], input=vl_json, stderr_filter=self._stderr_filter
        )
        return json.loads(vg_json)

    def _vg2png(self, spec: JSONDict) -> bytes:
        """Generate a PNG image from a Vega spec."""
        vg2png = exec_path("vg2png")
        vg_json = json.dumps(spec).encode()
        return check_output_with_stderr(
            [vg2png, *(self._vega_cli_options or [])],
            input=vg_json,
            stderr_filter=self._stderr_filter,
        )

    def _vg2pdf(self, spec: JSONDict) -> bytes:
        """Generate a PDF image from a Vega spec."""
        vg2pdf = exec_path("vg2pdf")
        vg_json = json.dumps(spec).encode()
        return check_output_with_stderr(
            [vg2pdf, *(self._vega_cli_options or [])],
            input=vg_json,
            stderr_filter=self._stderr_filter,
        )

    def _vg2svg(self, spec: JSONDict) -> str:
        """Generate an SVG image from a Vega spec."""
        vg2svg = exec_path("vg2svg")
        vg_json = json.dumps(spec).encode()
        return check_output_with_stderr(
            [vg2svg, *(self._vega_cli_options or [])],
            input=vg_json,
            stderr_filter=self._stderr_filter,
        ).decode()

    @classmethod
    def enabled(cls) -> bool:
        try:
            return bool(exec_path("vl2vg") and exec_path("vg2png"))
        except ExecutableNotFound:
            return False

    def _serialize(self, fmt: str, content_type: str) -> MimebundleContent:
        if self._mode not in ["vega", "vega-lite"]:
            raise ValueError("mode must be either 'vega' or 'vega-lite'")

        spec = self._spec

        if self._mode == "vega-lite":
            spec = self._vl2vg(spec)

        if fmt == "vega":
            return spec
        elif fmt == "png":
            return self._vg2png(spec)
        elif fmt == "svg":
            return self._vg2svg(spec)
        elif fmt == "pdf":
            return self._vg2pdf(spec)
        else:
            raise ValueError(f"Unrecognized format: {fmt!r}")
