from __future__ import annotations
import csv
from pathlib import Path
from typing import Any
from src.analyzer import Article
from datetime import datetime
from html import escape

from src.utils import PROJECT_DIR, TEMPLATE_DIR, OUTPUT_DIR

OUTPUT_PATH_CSV = OUTPUT_DIR / "report.csv"
OUTPUT_PATH_HTML = OUTPUT_DIR / "report.html"


POINT_COLS = [
    "direct_answer", "definition", "headings", "facts", "sources",
    "faq", "lists", "tables", "word_count_ok", "meta_ok",
]

POINT_LABELS = {
    "direct_answer": "Priama odpoveď",
    "definition": "Definícia",
    "headings": "H2 nadpisy",
    "facts": "Fakty/čísla",
    "sources": "Zdroje",
    "faq": "FAQ",
    "lists": "Zoznamy",
    "tables": "Tabuľky",
    "word_count_ok": "Dĺžka",
    "meta_ok": "Meta description",
}

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
        result = article.analyze()
        report = result.get("report")
        recs = result.get("recommendations")

        row = {k: int(v) for k, v in report.items()}
        row["url"] = result.get("url")
        row["title"] = result.get("title")
        row["score"] = result.get("score")
        row["recommendations"] = " | ".join(recs)

        self.rows.append(row)

    def export_csv(self, filename: str = OUTPUT_PATH_CSV) -> None:
        with open(filename, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()

            for row in self.rows:
                writer.writerow(row)

    def export_html(self, output_path: str = OUTPUT_PATH_HTML, title: str = "GEO Report") -> str:
        """
        Vráti celé HTML ako string. Volajúci si ho uloží do .html súboru.
        Používa templates/report.html a templates/report.css.
        """

        # --- internal template loader ---
        def _load_template(name: str) -> str:
            return (TEMPLATE_DIR / name).read_text(encoding="utf-8")

        # --- Helpers ---
        def to_int(v) -> int:
            try:
                return int(v)
            except Exception:
                return 0

        def score_badge(score: int, total: int) -> str:
            # jednoduché prahy
            if score >= int(0.8 * total):
                cls = "badge badge--good"
            elif score >= int(0.5 * total):
                cls = "badge badge--mid"
            else:
                cls = "badge badge--bad"
            return f'<span class="{cls}">{score}/{total}</span>'

        def point_dot(v: int) -> str:
            return '<span class="dot dot--ok"></span>' if v else '<span class="dot dot--no"></span>'

        # --- Load templates ---
        template = _load_template("report.html")
        css = _load_template("report.css")

        # --- Data prep ---
        rows = list(self.rows)  # kópia
        data_rows = [r for r in rows if r.get("url")]  # vyhoď header/empty riadky

        total_points = len(POINT_COLS)
        now = datetime.now().strftime("%Y-%m-%d %H:%M")

        total_articles = len(data_rows)
        avg_score = 0
        if total_articles:
            avg_score = round(sum(to_int(r.get("score")) for r in data_rows) / total_articles, 2)

        # --- Build cards ---
        cards_html_parts: list[str] = []
        for r in data_rows:
            url = escape(str(r.get("url", "")))
            atitle = escape(str(r.get("title", "")))
            score = to_int(r.get("score"))

            recs_raw = str(r.get("recommendations", "") or "").strip()
            rec_items = [s.strip() for s in recs_raw.split("|") if s.strip()]

            pills_parts: list[str] = []
            for key in POINT_COLS:
                val = 1 if to_int(r.get(key)) else 0
                label = escape(POINT_LABELS.get(key, key))
                pills_parts.append(f'<div class="pill">{point_dot(val)}<span>{label}</span></div>')

            if rec_items:
                rec_html = "<ul class='recs'>" + "".join(f"<li>{escape(it)}</li>" for it in rec_items) + "</ul>"
            else:
                rec_html = "<div class='muted'>Žiadne odporúčania 🎉</div>"

            cards_html_parts.append(
                f"""
                <article class="card">
                  <div class="card__top">
                    <div>
                      <div class="card__title"><a href="{url}" target="_blank" rel="noopener noreferrer">{atitle}</a></div>
                      <div class="card__url">{url}</div>
                    </div>
                    <div class="card__score">{score_badge(score, total_points)}</div>
                  </div>

                  <div class="pills">
                    {''.join(pills_parts)}
                  </div>

                  <div class="card__recs">
                    <div class="section-title">Odporúčania</div>
                    {rec_html}
                  </div>
                </article>
                """
            )

        cards_html = "".join(cards_html_parts) if cards_html_parts else '<div class="muted">Žiadne dáta.</div>'

        # --- Build table ---
        header_cells = ["URL", "Skóre"] + [escape(POINT_LABELS.get(c, c)) for c in POINT_COLS]
        table_header_html = "".join(f"<th>{c}</th>" for c in header_cells)

        table_rows_parts: list[str] = []
        for r in data_rows:
            url = escape(str(r.get("url", "")))
            score = to_int(r.get("score"))

            cells = [
                f'<td class="td-url"><a href="{url}" target="_blank" rel="noopener noreferrer">link</a></td>',
                f"<td>{score_badge(score, total_points)}</td>",
            ]
            for c in POINT_COLS:
                val = 1 if to_int(r.get(c)) else 0
                cells.append(f"<td class='td-center'>{'✓' if val else '–'}</td>")

            table_rows_parts.append("<tr>" + "".join(cells) + "</tr>")

        table_rows_html = "".join(table_rows_parts)

        # --- Fill template ---
        html = (
            template
            .replace("{{TITLE}}", escape(title))
            .replace("{{CSS}}", css)
            .replace("{{NOW}}", escape(now))
            .replace("{{TOTAL_POINTS}}", str(total_points))
            .replace("{{TOTAL_ARTICLES}}", str(total_articles))
            .replace("{{AVG_SCORE}}", str(avg_score))
            .replace("{{CARDS_HTML}}", cards_html)
            .replace("{{TABLE_HEADER_HTML}}", table_header_html)
            .replace("{{TABLE_ROWS_HTML}}", table_rows_html)
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html)