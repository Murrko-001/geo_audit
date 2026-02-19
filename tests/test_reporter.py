import csv
import pytest

from src.reporter import Reporter


class DummyArticle:
    def __init__(self, payload):
        self.payload = payload

    def analyze(self):
        return {
            "url": self.payload.get("url", "https://example.com/a"),
            "title": self.payload.get("title", "T"),
            "score": self.payload.get("score", 3),
            "report": self.payload.get("report", {"direct_answer": True}),
            "recommendations": self.payload.get("recommendations", ["Fix X"]),
        }


def test_reporter_add_article_adds_row():
    r = Reporter()
    r.add_article(DummyArticle({"score": 2, "report": {"facts": False}}))

    assert len(r.rows) == 1
    assert r.rows[0]["score"] == 2
    assert r.rows[0]["facts"] == 0
    assert "recommendations" in r.rows[0]


def test_export_csv_writes_file(tmp_path):
    r = Reporter()
    r.add_article(DummyArticle({"report": {"direct_answer": True}, "recommendations": []}))

    out = tmp_path / "report.csv"
    r.export_csv(output_path=out)

    with open(out, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))

    assert len(rows) == 1
    assert rows[0]["direct_answer"] in ("1", "True")  # csv stores strings


def test_export_html_writes_file(monkeypatch, tmp_path):
    r = Reporter()
    r.add_article(DummyArticle({"report": {"direct_answer": True}, "recommendations": ["A"]}))

    def fake_load_template(name: str) -> str:
        if name.endswith(".css"):
            return "/* css */"
        return "<html><head><style>{{CSS}}</style></head><body>{{CARDS_HTML}}{{TABLE_ROWS_HTML}}</body></html>"

    monkeypatch.setattr("src.reporter.load_template", fake_load_template)

    out = tmp_path / "report.html"
    r.export_html(output_path=out, title="X")

    html = out.read_text(encoding="utf-8")
    assert "<html>" in html
    assert "css" in html
    assert "card" in html or "Žiadne dáta" not in html
