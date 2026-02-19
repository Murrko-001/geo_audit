from __future__ import annotations
import csv
from typing import Any
from src.analyzer import Article
from html import escape

from src.reporter_utils import load_template, get_total_points, render_cards, render_table, fill_template, calc_summary
from src.utils import OUTPUT_DIR

OUTPUT_PATH_CSV = OUTPUT_DIR / "report.csv"
OUTPUT_PATH_HTML = OUTPUT_DIR / "report.html"


class Reporter:
    def __init__(self):
        self.columns = [
            "url",
            "title",
            "score",
            "direct_answer",
            "definition",
            "headings",
            "facts",
            "sources",
            "faq",
            "lists",
            "tables",
            "word_count_ok",
            "meta_ok",
            "recommendations",
        ]

        self.rows: list[dict[str, Any]] = []

    def add_article(self, article: "Article") -> None:
        result = article.analyze() or {}
        report = result.get("report") or {}
        recs = result.get("recommendations") or []

        row = {k: int(v) for k, v in report.items()}
        row["url"] = result.get("url", "")
        row["title"] = result.get("title", "")
        row["score"] = result.get("score", 0)
        row["recommendations"] = " | ".join(recs)

        self.rows.append(row)

    def export_csv(self, output_path: str = OUTPUT_PATH_CSV) -> None:
        try:
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns, extrasaction='ignore')
                writer.writeheader()

                for row in self.rows:
                    writer.writerow(row)
        except OSError as exc:
            raise OSError(f"Failed to write CSV to {output_path}") from exc

    def export_html(self, output_path: str = OUTPUT_PATH_HTML, title: str = "GEO Report") -> None:
        def prepare_rows() -> list[dict]:
            return [r for r in self.rows if r.get("url")]

        try:
            template = load_template("report.html")
            css = load_template("report.css")
        except OSError as exc:
            raise OSError("Failed to load HTML/CSS templates") from exc

        data_rows = prepare_rows()
        total_points = get_total_points()

        total_articles, avg_score, now = calc_summary(data_rows)
        cards_html = render_cards(data_rows, total_points)
        table_header_html, table_rows_html = render_table(data_rows, total_points)

        ctx = {
            "TITLE": escape(title),
            "CSS": css,
            "NOW": escape(now),
            "TOTAL_POINTS": str(total_points),
            "TOTAL_ARTICLES": str(total_articles),
            "AVG_SCORE": str(avg_score),
            "CARDS_HTML": cards_html,
            "TABLE_HEADER_HTML": table_header_html,
            "TABLE_ROWS_HTML": table_rows_html,
        }

        html = fill_template(template, ctx)

        try:
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(html)
        except OSError as exc:
            raise OSError(f"Failed to write HTML to {output_path}") from exc

    def do_report(self,
                  posts,
                  report_to_csv: bool = True,
                  report_to_html: bool = True,
                  output_path_csv: str = OUTPUT_PATH_CSV,
                  output_path_html: str = OUTPUT_PATH_HTML,
                  ) -> None:

        for post in posts:
            article = Article(post)
            self.add_article(article)

        if report_to_csv:
            self.export_csv(output_path_csv)
        if report_to_html:
            self.export_html(output_path_html)
