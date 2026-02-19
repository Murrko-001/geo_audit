from __future__ import annotations
import csv
from datetime import datetime
from typing import Any
from src.analyzer import Article
from html import escape

from src.reporter_utils import load_template, get_total_points, fill_template, to_int, \
    POINT_COLS, POINT_LABELS, point_dot, score_badge
from src.utils import OUTPUT_DIR

OUTPUT_PATH_CSV = OUTPUT_DIR / "report.csv"
OUTPUT_PATH_HTML = OUTPUT_DIR / "report.html"


class Reporter:
    """
    Collect article analysis results and export reports.

    The reporter consumes `Article` objects, stores their analysis results in
    `self.rows`, and can export the aggregated results to CSV and/or HTML.

    Attributes:
        columns: Ordered list of column names used when exporting CSV.
        rows: List of row dictionaries representing analyzed articles.
    """
    def __init__(self):
        self.columns = ["url", "title", "score"] + POINT_COLS + ["recommendations"]
        self.rows: list[dict[str, Any]] = []

    def add_article(self, article: "Article") -> None:
        """
        Analyze an article and append its result as a row.

        Args:
            article: Article instance to analyze.

        Notes:
            The row is derived from the dictionary returned by `article.analyze()`.
            Missing fields default to empty values.
        """
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
        """
        Export collected rows to a CSV report.

        Args:
            output_path: Destination file path for the CSV output.

        Raises:
            OSError: If the file cannot be written.
        """
        try:
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=self.columns, extrasaction='ignore')
                writer.writeheader()

                for row in self.rows:
                    writer.writerow(row)
        except OSError as exc:
            raise OSError(f"Failed to write CSV to {output_path}") from exc

    def _calc_summary(self) -> tuple[int, float, str]:
        """
        Calculate summary statistics for a collection of article reports.

        Returns:
            A tuple containing:
            - total number of articles
            - average score across articles
            - current timestamp (YYYY-MM-DD HH:MM)
        """
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        total_articles = len(self.rows)

        avg_score = 0.0
        if total_articles:
            avg_score = round(sum(to_int(r.get("score")) for r in self.rows) / total_articles, 2)

        return total_articles, avg_score, now

    def _render_cards(self) -> str:
        """
        Render article results as HTML "card" components.

        Returns:
            HTML string containing rendered cards for all rows.
        """
        parts: list[str] = []

        for r in self.rows:
            if not isinstance(r, dict):
                continue
            url = escape(str(r.get("url", "")))
            atitle = escape(str(r.get("title", "")))
            score = to_int(r.get("score"))

            recs_raw = str(r.get("recommendations", "") or "").strip()
            rec_items = [s.strip() for s in recs_raw.split("|") if s.strip()]

            pills = []
            for key in POINT_COLS:
                val = 1 if to_int(r.get(key)) else 0
                label = escape(POINT_LABELS.get(key, key))
                pills.append(f'<div class="pill">{point_dot(val)}<span>{label}</span></div>')

            if rec_items:
                rec_html = "<ul class='recs'>" + "".join(f"<li>{escape(it)}</li>" for it in rec_items) + "</ul>"
            else:
                rec_html = "<div class='muted'>Žiadne odporúčania</div>"

            parts.append(f"""
            <article class="card">
              <div class="card__top">
                <div>
                  <div class="card__title"><a href="{url}" target="_blank" rel="noopener noreferrer">{atitle}</a></div>
                  <div class="card__url">{url}</div>
                </div>
                <div class="card__score">{score_badge(score, get_total_points())}</div>
              </div>

              <div class="pills">
                {''.join(pills)}
              </div>

              <div class="card__recs">
                <div class="section-title">Odporúčania</div>
                {rec_html}
              </div>
            </article>
            """)

        return "".join(parts) if parts else '<div class="muted">Žiadne dáta.</div>'

    def _render_table(self) -> tuple[str, str]:
        """
        Render an HTML table summarizing article results.

        Returns:
            A tuple of:
                - HTML for the table header (`<th>` cells)
                - HTML for the table body rows (`<tr>` elements)
        """
        header_cells = ["URL", "Názov", "Skóre"] + [escape(POINT_LABELS.get(c, c)) for c in POINT_COLS]
        table_header_html = "".join(f"<th>{c}</th>" for c in header_cells)

        row_parts: list[str] = []
        for r in self.rows:
            url = escape(str(r.get("url", "")))
            title = escape(str(r.get("title", "")))
            score = to_int(r.get("score"))

            cells = [
                f'<td class="td-url"><a href="{url}" target="_blank" rel="noopener noreferrer">link</a></td>',
                f'<td class="td-title">{title}</td>',
                f"<td>{score_badge(score, get_total_points())}</td>",
            ]
            for c in POINT_COLS:
                val = 1 if to_int(r.get(c)) else 0
                cells.append(f"<td class='td-center'>{'✓' if val else '–'}</td>")

            row_parts.append("<tr>" + "".join(cells) + "</tr>")

        return table_header_html, "".join(row_parts)

    def export_html(self, output_path: str = OUTPUT_PATH_HTML, title: str = "GEO Report") -> None:
        """
        Export collected rows and their aggregates to an HTML report.

        Args:
            output_path: Destination file path for the HTML output.
            title: Report title displayed in the HTML template.

        Raises:
            OSError: If templates cannot be read or the output file cannot be written.
        """
        try:
            template = load_template("report.html")
            css = load_template("report.css")
        except OSError as exc:
            raise OSError("Failed to load HTML/CSS templates") from exc

        total_points = get_total_points()

        total_articles, avg_score, now = self._calc_summary()
        cards_html = self._render_cards()
        table_header_html, table_rows_html = self._render_table()

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
        """
        Generate reports from a collection of WordPress or JSON post payloads.

        Args:
            posts: Iterable of raw post dictionaries (WordPress API or cached JSON).
            report_to_csv: If True, export a CSV report.
            report_to_html: If True, export an HTML report.
            output_path_csv: Destination path for the CSV output.
            output_path_html: Destination path for the HTML output.
        """

        for post in posts:
            article = Article(post)
            self.add_article(article)

        if report_to_csv:
            self.export_csv(output_path_csv)
        if report_to_html:
            self.export_html(output_path_html)
