import pytest

from dispyrate import D
from dispyrate.exceptions import DestructuringError


def test_D_empty():
    with pytest.raises(DestructuringError):
        D({'a': 1})


def test_D_single():
    with pytest.raises(DestructuringError):
        a = D({'a': 1})


def test_D_multiple():
    a, b = D({'c': 3, 'b': 2, 'a': 1})
    assert (a, b) == (1, 2)


def test_D_multiple_starred():
    a, *b, c = D({'d': 4, 'c': 3, 'b': 2, 'a': 1})
    assert (a, b, c) == (1, [4, 2], 3)


def test_D_missing():
    with pytest.raises(DestructuringError):
        a, b = D({'c': 3, 'a': 1})
