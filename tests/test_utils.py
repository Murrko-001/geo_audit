import pytest

from src.utils import inflection


@pytest.mark.parametrize(
    "num,expected",
    [
        (0, ""),
        (1, "o"),
        (2, "á"),
        (3, "á"),
        (4, "á"),
        (5, ""),
        (10, ""),
        (-1, ""),
    ],
)
def test_inflection(num, expected):
    assert inflection(num) == expected
