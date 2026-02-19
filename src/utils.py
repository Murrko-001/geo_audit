from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = PROJECT_DIR / "templates"
OUTPUT_DIR = PROJECT_DIR / "output"

def inflection(difference: int):
    if difference == 1:
        return 'o'
    elif 1 < difference < 5:
        return 'á'

    return ''