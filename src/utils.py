from pathlib import Path

PROJECT_DIR = Path(__file__).parent.parent
TEMPLATE_DIR = PROJECT_DIR / "templates"
OUTPUT_DIR = PROJECT_DIR / "output"
DATA_DIR = PROJECT_DIR / "data"

def inflection(num: int):
    if num == 1:
        return 'o'
    elif 1 < num < 5:
        return 'á'

    return ''