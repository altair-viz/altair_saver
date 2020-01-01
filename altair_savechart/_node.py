import json
import os
import subprocess
from typing import List, Optional

import altair as alt
from altair_savechart._saver import JSONDict, Mimebundle, Saver


class _NodeCommands:
    """Tools for calling vega node command line."""

    def __init__(self, global_: bool = True, npm_root: Optional[str] = None):
        if npm_root is None:
            npm_root = self._get_npm_root(global_)
        self._npm_root = npm_root
        if global_:
            self._install_cmd = "Install with npm install -g vega-lite vega-cli"
        else:
            self._install_cmd = "Install with npm install vega-lite vega-cli"

    @staticmethod
    def _get_npm_root(global_: bool) -> str:
        """Return the npm root directory"""
        cmd = ["npm", "root"]
        if global_:
            cmd.append("--global")
        npm_root = subprocess.check_output(cmd, encoding="utf-8").strip()
        if not os.path.isdir(npm_root):
            raise RuntimeError(f"npm root not found; got {npm_root}")
        return npm_root

    def vl2vg(self, spec: JSONDict) -> JSONDict:
        vl2vg = os.path.join(self._npm_root, "vega-lite", "bin", "vl2vg")
        if not os.path.exists(vl2vg):
            raise RuntimeError(
                f"Cannot find vl2vg command: tried {vl2vg}\n{self._install_cmd}"
            )
        vl_json = json.dumps(spec).encode()
        vg_json = subprocess.check_output([vl2vg], input=vl_json)
        return json.loads(vg_json)

    def vg2png(self, spec: JSONDict) -> bytes:
        vg2png = os.path.join(self._npm_root, "vega-cli", "bin", "vg2png")
        if not os.path.exists(vg2png):
            raise RuntimeError(
                f"Cannot find vg2png command: tried {vg2png}\n{self._install_cmd}"
            )
        vg_json = json.dumps(spec).encode()
        return subprocess.check_output([vg2png], input=vg_json)

    def vg2pdf(self, spec: JSONDict) -> bytes:
        vg2pdf = os.path.join(self._npm_root, "vega-cli", "bin", "vg2pdf")
        if not os.path.exists(vg2pdf):
            raise RuntimeError(
                f"Cannot find vg2pdf command: tried {vg2pdf}\n{self._install_cmd}"
            )
        vg_json = json.dumps(spec).encode()
        return subprocess.check_output([vg2pdf], input=vg_json)

    def vg2svg(self, spec: JSONDict) -> str:
        vg2svg = os.path.join(self._npm_root, "vega-cli", "bin", "vg2svg")
        if not os.path.exists(vg2svg):
            raise RuntimeError(
                f"Cannot find vg2svg command: tried {vg2svg}\n{self._install_cmd}"
            )
        vg_json = json.dumps(spec).encode()
        return subprocess.check_output([vg2svg], input=vg_json).decode()

    def vl2png(self, spec: JSONDict) -> bytes:
        vg_spec = self.vl2vg(spec)
        return self.vg2png(vg_spec)

    def vl2pdf(self, spec: JSONDict) -> bytes:
        vg_spec = self.vl2vg(spec)
        return self.vg2pdf(vg_spec)

    def vl2svg(self, spec: JSONDict) -> str:
        vg_spec = self.vl2vg(spec)
        return self.vg2svg(vg_spec)


class NodeSaver(Saver):

    valid_formats: List[str] = ["pdf", "png", "svg", "vega"]

    def __init__(self, spec: JSONDict, mode: str = "vega-lite", global_: bool = True):
        self._node = _NodeCommands(global_=global_)
        super().__init__(spec=spec, mode=mode)

    @classmethod
    def enabled(cls) -> bool:
        # TODO: implement
        raise NotImplementedError()

    def _mimebundle(self, fmt: str) -> Mimebundle:
        """Return a mimebundle with a single mimetype."""
        if self._mode not in ["vega", "vega-lite"]:
            raise ValueError("mode must be either 'vega' or 'vega-lite'")

        spec = self._spec
        if self._mode == "vega-lite":
            spec = self._node.vl2vg(spec)

        if fmt == "vega":
            return {
                "application/vnd.vega.v{}+json".format(
                    alt.VEGA_VERSION.split(".")[0]
                ): spec
            }
        elif fmt == "png":
            return {"image/png": self._node.vg2png(spec)}
        elif fmt == "svg":
            return {"image/svg+xml": self._node.vg2svg(spec)}
        elif fmt == "pdf":
            return {"application/pdf": self._node.vg2pdf(spec)}
        else:
            raise ValueError(f"Unrecognized format: {fmt}")
