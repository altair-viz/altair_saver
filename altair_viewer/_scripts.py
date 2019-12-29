import json
import functools
import pkgutil
from typing import Dict, List, Optional

from altair_viewer._utils import find_version


@functools.lru_cache(1)
def _script_listing() -> Dict[str, List[str]]:
    content = pkgutil.get_data("altair_viewer", "scripts/listing.json")
    if content is None:
        raise ValueError("Unable to locate altair_viewer/scripts/listing.json")
    return json.loads(content)


def get_bundled_script(package: str, version: Optional[str] = None) -> str:
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
    version_str = find_version(version, listing[package])
    content = pkgutil.get_data("altair_viewer", f"scripts/{package}-{version_str}.js")
    if content is None:
        raise ValueError(
            f"Cannot locate file altair_viewer/scripts/{package}-{version_str}.js"
        )
    return content.decode()
