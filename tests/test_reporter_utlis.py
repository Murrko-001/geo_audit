import pytest

from src import reporter_utils as ru


@pytest.mark.parametrize(
    "value,expected",
    [
        (1, 1),
        ("2", 2),
        (True, 1),
        (False, 0),
        (None, 0),
        ("", 0),
        ("abc", 0),
        (3.7, 3),
    ],
)
def test_to_int(value, expected):
    assert ru.to_int(value) == expected


def test_get_total_points_matches_cols():
    assert ru.get_total_points() == len(ru.POINT_COLS)


def test_fill_template_replaces_placeholders_and_coerces_to_str():
    template = "Hello {{NAME}}. Score={{SCORE}}. Missing={{MISSING}}."
    ctx = {"NAME": "World", "SCORE": 10, "MISSING": None}
    out = ru.fill_template(template, ctx)
    assert out == "Hello World. Score=10. Missing=."


def test_score_badge_classification():
    total = 10
    assert "badge--good" in ru.score_badge(8, total)
    assert "badge--mid" in ru.score_badge(5, total)
    assert "badge--bad" in ru.score_badge(4, total)


def test_point_dot():
    assert "dot--ok" in ru.point_dot(1)
    assert "dot--no" in ru.point_dot(0)
