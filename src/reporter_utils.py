from datetime import datetime
from html import escape

from src.utils import TEMPLATE_DIR


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

def get_total_points():
    return len(POINT_COLS)

def to_int(v) -> int:
    try:
        return int(v)
    except (ValueError, TypeError):
        return 0

def load_template(name: str) -> str:
    return (TEMPLATE_DIR / name).read_text(encoding="utf-8")

def calc_summary(data_rows: list[dict]) -> tuple[int, float, str]:
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total_articles = len(data_rows)

    avg_score = 0.0
    if total_articles:
        avg_score = round(sum(to_int(r.get("score")) for r in data_rows) / total_articles, 2)

    return total_articles, avg_score, now


def score_badge(score: int, total: int) -> str:
    if score >= int(0.8 * total):
        cls = "badge badge--good"
    elif score >= int(0.5 * total):
        cls = "badge badge--mid"
    else:
        cls = "badge badge--bad"
    return f'<span class="{cls}">{score}/{total}</span>'


def point_dot(v: int) -> str:
    return '<span class="dot dot--ok"></span>' if v else '<span class="dot dot--no"></span>'


def render_cards(data_rows: list[dict], total_points: int) -> str:
    parts: list[str] = []

    for r in data_rows:
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
            <div class="card__score">{score_badge(score, total_points)}</div>
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


def render_table(data_rows: list[dict], total_points: int) -> tuple[str, str]:
    header_cells = ["URL", "Skóre"] + [escape(POINT_LABELS.get(c, c)) for c in POINT_COLS]
    table_header_html = "".join(f"<th>{c}</th>" for c in header_cells)

    row_parts: list[str] = []
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

        row_parts.append("<tr>" + "".join(cells) + "</tr>")

    return table_header_html, "".join(row_parts)


def fill_template(template: str, ctx: dict[str, str]) -> str:
    for k, v in ctx.items():
        template = template.replace(f"{{{{{k}}}}}", v)
    return template