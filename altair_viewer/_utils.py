import math
import re
from typing import NamedTuple, List, Optional, Union


class NoMatchingVersions(RuntimeError):
    pass


class ParsedVersion(NamedTuple):
    major: int
    minor: Optional[int]
    micro: Optional[int]
    dev: Optional[str]


class Version:
    """Parser for version strings."""

    major: int
    minor: Optional[int]
    micro: Optional[int]
    dev: Optional[str]

    def __init__(
        self,
        major: Union[int, str],
        minor: Optional[int] = None,
        micro: Optional[int] = None,
        dev: Optional[str] = None,
    ):
        if isinstance(major, str):
            if not all(arg is None for arg in (minor, micro, dev)):
                raise ValueError(
                    "If passing a string to Version, no other arguments should be used."
                )
            major, minor, micro, dev = self._parse(major)
        self.major = major
        self.minor = minor
        self.micro = micro
        self.dev = dev

    def __str__(self) -> str:
        version = str(self.major)
        if self.minor is not None:
            version += f".{self.minor}"
        if self.micro is not None:
            version += f".{self.micro}"
        if self.dev is not None:
            version += self.dev
        return version

    def _parse(self, version: str) -> ParsedVersion:
        """Parse a string version"""
        regex = re.compile(
            r"^(?P<major>\d+)(?:\.(?P<minor>\d+)(?:\.(?P<micro>\d+))?)?(?P<dev>.+)?$"
        )
        match = regex.match(version)
        if not match:
            raise ValueError(f"Cannot parse version: {version}")
        dct = match.groupdict()
        return ParsedVersion(
            major=int(dct["major"]),
            minor=None if dct.get("minor") is None else int(dct["minor"]),
            micro=None if dct.get("micro") is None else int(dct["micro"]),
            dev=dct.get("dev"),
        )

    def matches(self, other: Union[str, "Version"]) -> bool:
        """Check one-way matching between versions.

        This checks if self is a less-specific match of other, where "less specific"
        means that the minor or micro versions are left unspecified. (See examples below).
        Note that under this definition, matching is not symmetric.

        Parameters
        ----------
        other : str or Version

        Returns
        -------
        equivalent : bool

        Examples
        --------
        >>> Version("4.0.0").matches("4.0.0")
        True
        >>> Version("4").matches("4.2.0")
        True
        >>> Version("4.2.0").matches("4")
        False
        >>> Version("4.0.0").matches("4.0.0.dev0")
        False
        """
        if isinstance(other, str):
            other = self.__class__(other)
        if self.dev != other.dev:
            return False
        for version in ["major", "minor", "micro"]:
            this = getattr(self, version)
            that = getattr(other, version)
            if this != that and this is not None:
                return False
        return True

    def _order_tuple(self) -> tuple:
        return (
            self.major,
            -1 if self.minor is None else self.minor,
            -1 if self.micro is None else self.micro,
            (math.inf,) if self.dev is None else tuple(ord(c) for c in self.dev),
        )

    def __eq__(self, other: object) -> bool:
        if isinstance(other, str):
            other = self.__class__(other)
        if not isinstance(other, self.__class__):
            return NotImplemented
        return (self.major, self.minor, self.micro, self.dev) == (
            other.major,
            other.minor,
            other.micro,
            other.dev,
        )

    def __neq__(self, other: object) -> bool:
        return not self == other

    def __lt__(self, other: object) -> bool:
        if isinstance(other, str):
            other = self.__class__(other)
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self._order_tuple() < other._order_tuple()

    def __repr__(self) -> str:
        return f"Version(major={self.major}, minor={self.minor}, micro={self.micro}, dev={self.dev})"


def find_version(
    version: Optional[str], candidates: List[str], strict_micro: bool = False
) -> str:
    """Find a matching version string given a list of candidate versions.

    Parameters
    ----------
    version : str or None
        The version to match. If None, the newest version will be used.
    candidates : list
        The list of candidate versions to consider.
    strict_micro : bool
        If True, then ensure that the micro version matches exactly.
        If False (default), then let the micro version float to the newest version.

    Returns
    -------
    version : str
        The matching versions from the list of candidates.

    Raises
    ------
    NoMatchingVersions : if no matching version is found.

    Examples
    --------
    >>> find_version('3', ['3.1.0', '4.0.0', '4.1.0', '4.2.0-alpha0'])
    '3.1.0'
    >>> find_version('4', ['3.1.0', '4.0.0', '4.1.0', '4.2.0-alpha0'])
    '4.1.0'
    >>> find_version('4.0', ['3.1.0', '4.0.0', '4.1.0', '4.2.0-alpha0'])
    '4.0.0'
    >>> find_version(None, ['3.1.0', '4.0.0', '4.1.0', '4.2.0-alpha0'])
    '4.1.0'
    >>> find_version("4.2.0-alpha0", ['3.1.0', '4.0.0', '4.1.0', '4.2.0-alpha0'])
    '4.2.0-alpha0'
    """
    if not candidates:
        raise NoMatchingVersions("No candidate versions provided.")
    cand = sorted([Version(c) for c in candidates])
    if version is None:
        cand = sorted(c for c in cand if c.dev is None)
        if not candidates:
            raise NoMatchingVersions(f"No non-dev candidates in {candidates}.")
        return str(cand[-1])

    v = Version(version)
    if not strict_micro and not v.dev:
        v.micro = None
    matches = [c for c in cand if v.matches(c)]
    if not matches:
        raise NoMatchingVersions(
            f"No matches for version={version!r} among {candidates}"
        )
    return str(matches[-1])
