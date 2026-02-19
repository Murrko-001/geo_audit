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
    """
    Load a webpage template from the template directory.

    Args:
        name: File name of the template.

    Returns:
        Template contents as a string.

    Raises:
        OSError: If the template file cannot be read.
    """
    path = TEMPLATE_DIR / name
    try:
        return path.read_text(encoding="utf-8")
    except OSError as exc:
        raise OSError(f"Failed to read template: {path}") from exc


def score_badge(score: int, total: int) -> str:
    """
    Render an HTML badge representing an article score.

    Args:
        score: Achieved score.
        total: Maximum possible score.

    Returns:
        HTML string representing the score badge.
    """
    if score >= int(0.8 * total):
        cls = "badge badge--good"
    elif score >= int(0.5 * total):
        cls = "badge badge--mid"
    else:
        cls = "badge badge--bad"
    return f'<span class="{cls}">{score}/{total}</span>'


def point_dot(value: int) -> str:
    """
    Render an HTML dot indicating pass/fail state of a point.

    Args:
        value: Integer value representing boolean state.

    Returns:
        HTML string for a pass or fail indicator.
    """
    return '<span class="dot dot--ok"></span>' if value else '<span class="dot dot--no"></span>'


def fill_template(template: str, ctx: dict[str, object]) -> str:
    """
    Replace placeholders in an HTML template with provided values.

    Placeholders must be in the form ``{{KEY}}``.

    Args:
        template: Template string containing placeholders.
        ctx: Mapping of placeholder keys to replacement values.

    Returns:
        Rendered template with placeholders replaced.
    """
    for k, v in ctx.items():
        template = template.replace(f"{{{{{k}}}}}", "" if v is None else str(v))
    return template
