from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = PROJECT_DIR / "templates"
OUTPUT_DIR = PROJECT_DIR / "output"
DATA_DIR = PROJECT_DIR / "data"


def inflection(num: int) -> str:
    """
    Return the correct Slovak inflection suffix for a numeric value.
    Args:
        num: Numeric value used to determine the inflection.

    Returns:
        A Slovak inflection suffix appropriate for the given number.
    """
    if num == 1:
        return 'o'
    elif 1 < num < 5:
        return 'á'

    return ''
