__all__ = ["JSON", "JSONDict", "MimebundleContent", "Mimebundle"]

from typing import Any, Dict, List, Union

JSON = Union[str, int, float, bool, None, Dict[str, Any], List[Any]]
JSONDict = Dict[str, JSON]
MimebundleContent = Union[str, bytes, JSONDict]
Mimebundle = Dict[str, MimebundleContent]
