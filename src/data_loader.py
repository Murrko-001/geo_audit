import json
import requests

from src.utils import DATA_DIR

GYMBEAM_BLOG_URL = "https://gymbeam.sk/blog"
ARTICLES_PATH = DATA_DIR / "articles.json"

def fetch_wp_posts(base_url, per_page=10) -> list[dict]:
    url = f"{base_url}/wp-json/wp/v2/posts?per_page={per_page}"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.json()


def save_posts_to_file(data, filename=ARTICLES_PATH) -> None:
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError as exc:
        raise OSError(f"Failed to write posts to {filename}") from exc
    except TypeError as exc:
        raise TypeError("Post data is not JSON serializable") from exc


def load_posts_from_file(filename=ARTICLES_PATH, per_page=10) -> list[dict]:
    try:
        with open(filename, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Posts file not found: {filename}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in posts file: {filename}") from exc
    except OSError as exc:
        raise OSError(f"Failed to read posts file: {filename}") from exc

    return data[:per_page]


def load_posts_wrapper(use_wp=True, file_name=ARTICLES_PATH, per_page=10) -> list[dict]:
    if not use_wp:
        return load_posts_from_file(file_name, per_page)
    return fetch_wp_posts(GYMBEAM_BLOG_URL, per_page)
