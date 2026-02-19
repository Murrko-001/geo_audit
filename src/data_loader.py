import json
import requests

from src.utils import DATA_DIR

GYMBEAM_BLOG_URL = "https://gymbeam.sk/blog"
ARTICLES_PATH = DATA_DIR / "articles.json"

def fetch_wp_posts(base_url, per_page=10):
    url = f"{base_url}/wp-json/wp/v2/posts?per_page={per_page}"
    response = requests.get(url)
    response.raise_for_status()
    return response.json()


def save_posts_to_file(data, filename=ARTICLES_PATH):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_posts_from_file(filename=ARTICLES_PATH, per_page=10):
    with open(filename, encoding="utf-8") as f:
        data = json.load(f)

    return data[:per_page]


def load_posts_wrapper(use_wp=True, file_name=ARTICLES_PATH, per_page=10):
    if not use_wp:
        return load_posts_from_file(file_name, per_page)
    return fetch_wp_posts(GYMBEAM_BLOG_URL, per_page)
