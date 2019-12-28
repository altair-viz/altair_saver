import json
import functools
import pkgutil
from typing import Dict, List


@functools.lru_cache(1)
def _script_listing() -> Dict[str, List[str]]:
    content = pkgutil.get_data("altair_viewer", "scripts/listing.json")
    if content is None:
        raise ValueError("Unable to locate altair_viewer/scripts/listing.json")
    return json.loads(content)


def get_bundled_script(package: str, version: str = "") -> str:
    """Get a bundled script from this pacakge

    Parameters
    ----------
    package : str
        The name of the package to get (e.g. "vega", "vega-lite", "vega-embed")
    version : str (optional)
        The version of the package to use. If not specified, use the most recent
        available version.

    Returns
    -------
    content : str
        The content of the script.
    """
    listing = _script_listing()
    if package not in listing:
        raise ValueError(
            f"package {package!r} not recognized. Available: {list(listing)}"
        )
    versions = listing[package]
    if version and version not in versions:
        raise ValueError(
            f"version {package}={version!r} not recognized. Available: {list(listing)}"
        )
    if not version:
        # TODO: choose most recent
        version = versions[0]

    content = pkgutil.get_data("altair_viewer", f"scripts/{package}-{version}.js")
    if content is None:
        raise ValueError(
            f"Cannot locate file altair_viewer/scripts/{package}-{version}.js"
        )
    return content.decode()
