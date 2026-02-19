import pytest
import warnings

from src.analyzer import Article


def make_post(*, title="Test", html="", desc=""):
    return {
        "id": 1,
        "link": "https://example.com/a",
        "title": {"rendered": title},
        "content": {"rendered": html},
        "yoast_head_json": {"description": desc},
    }


def test_article_clean_content_strips_scripts_and_whitespace():
    html = "<p>Hello</p><script>alert(1)</script><p>World</p>"
    a = Article(make_post(html=html))
    assert "alert" not in a.content_clean
    assert "Hello" in a.content_clean
    assert "World" in a.content_clean


def test_analyze_direct_answer_fails_on_forbidden_phrase():
    html = "<p>V tomto článku sa dozviete...</p>"
    a = Article(make_post(html=html))
    assert a.analyze_direct_answer() is False
    assert a.points["direct_answer"] is False
    assert len(a.recommendations) == 1


def test_analyze_definition_by_title_detects_definition():
    title = "Kreatín: čo je a ako funguje"
    html = "<p>Kreatín je látka...</p>"
    a = Article(make_post(title=title, html=html))
    assert a.analyze_definition() is True
    assert a.points["definition"] is True


def test_analyze_headings_requires_three_h2():
    html = "<h2>A</h2><h2>B</h2>"
    a = Article(make_post(html=html))
    assert a.analyze_headings() is False
    assert a.points["headings"] is False


def test_analyze_meta_ok_range():
    a = Article(make_post(html="<p>x</p>", desc="x" * 140))
    assert a.analyze_meta_ok() is True
    assert a.points["meta_ok"] is True


def test_run_analysis_step_emits_warning_on_exception():
    a = Article(make_post(html="<p>x</p>"))

    def boom():
        raise RuntimeError("fail")

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        a._run_analysis_step("boom", boom)

        assert len(w) == 1
        assert "boom" in str(w[0].message)
        assert a.points["boom"] is False
