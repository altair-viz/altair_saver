from altair_viewer._utils import Version, find_version

import pytest

import random


@pytest.mark.parametrize(
    "version_string,expected",
    [
        ("4", Version(4)),
        ("4.2", Version(4, 2)),
        ("4.2.0", Version(4, 2, 0)),
        ("4.alpha", Version(4, None, None, ".alpha")),
        ("4.2-beta", Version(4, 2, None, "-beta")),
        ("4.2.0.dev0", Version(4, 2, 0, ".dev0")),
        ("4.2.0-dev.0", Version(4, 2, 0, "-dev.0")),
    ],
)
def test_version_parsing(version_string, expected):
    version = Version(version_string)
    assert version == expected
    assert str(version) == version_string


@pytest.mark.parametrize(
    "sorted_sequence",
    [
        ["1", "3", "5"],
        ["1.0", "1.0.1", "1.1", "1.1.1"],
        ["2.0.dev0", "2.0.dev1", "2.0"],
        ["1", "1.0", "1.0.1", "1.0.2.dev0", "1.0.2", "2", "2.1", "3.5.9"],
    ],
)
def test_ordering(sorted_sequence):
    sequence = sorted_sequence[:]
    random.shuffle(sequence)
    out = [str(v) for v in sorted(map(Version, sequence))]
    assert out == sorted_sequence


@pytest.mark.parametrize(
    "version, candidates, strict_micro, expected",
    [
        ("4.0.0", ["4.0.0", "4.0.1", "4.0.2"], True, "4.0.0"),
        ("4.0.0", ["4.0.0", "4.0.1", "4.0.2"], False, "4.0.2"),
        ("4.0.0.dev0", ["4.0.0.dev0", "4.0.1.dev0", "4.0.2.dev0"], True, "4.0.0.dev0"),
        ("4.0.0.dev0", ["4.0.0.dev0", "4.0.1.dev0", "4.0.2.dev0"], False, "4.0.0.dev0"),
    ],
)
def test_matches(version, candidates, strict_micro, expected):
    result = find_version(version, candidates, strict_micro=strict_micro)
    assert result == expected
